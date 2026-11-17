"""Serial, accounted N5 physical readout using disjoint actual cell/path owners."""
from contextlib import ExitStack
from copy import deepcopy
import csv
import math
import os
from pathlib import Path
from types import FunctionType, SimpleNamespace
from unittest.mock import patch

from .nangate45_samples import ROOT,read,write,sha
from . import nangate45_pipeline_samples as campaign
from . import backend,budget,platform_probe,workload_nine_runtime as runtime
from . import model_fast_sdc_v3 as sdc
from . import stage67_physical_probe_v1 as physical
from . import stage67_physical_readout_v2 as readout
from . import stage67_mapped_state_v3 as mapped
from . import stage67_analyze_v1 as analyze
from .model_reference_labels import liberty
from .model_qualification_labels import with_timing_arcs
from .model_m2_mux_collection import render_cts
from .nangate45_cec import verify_proof
from .platforms import profile,verify_wire_readback
from .processes import run_command

ORFS=Path('/home/zyrv/OpenROAD-flow-scripts')
SUFFIX=Path('nangate45/arithmetic_probe/base')


class PipelineLedger(runtime.NineLedger):
    def __init__(self,root,task):super().__init__();self.root=root;self.task=task
    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a=campaign.verify(self.root)
        if threads!=2 or stage not in (None,'synth','grt'):raise ValueError('N56 leaf resources')
        entries=[e for e in read(self.path)['entries'] if e.get('admission_id')==a['id']]
        own=[e for e in entries if e.get('task_id')==self.task['id']]
        k=stage or 'support'
        if sum((e['stage'] or 'support')==k for e in entries)>=a['call_caps'][k]:raise ValueError('N56 batch call cap')
        if stage and any(e['stage']==stage for e in own):raise ValueError('N56 physical retry prohibited')
        if not stage and sum(e['stage'] is None for e in own)>=12:raise ValueError('N56 support cap')
        if timeout_s>a[{None:'support_timeout_s','synth':'synth_timeout_s','grt':'grt_timeout_s'}[stage]]:raise ValueError('N56 timeout envelope')
        return super().reserve(stage,timeout_s,threads,purpose,command,output,context={**(context or {}),
            'target_platform':'nangate45','admission_id':a['id'],'task_id':self.task['id'],
            'admission_sha256':sha(self.root/'admission.json'),'model_version':campaign.VERSION})


def admission_check(args,p,rtl,ledger):
    a=campaign.verify(args.admission.parent);t=next(t for t in a['tasks'] if t['id']==args.task_id)
    s=next(s for s in a['sources'] if s['id']==t['source'])
    if (p['platform']!='nangate45' or str(rtl)!=s['rtl'] or args.period_ps!=t['period_ps'] or
        args.abc_target_ps!=t['period_ps'] or args.threads!=2 or args.memory_limit_mib!=4096 or
        args.top!='ModelBundle' or args.stage!='synth' or args.admission_id!=a['id']):raise ValueError('N56 physical admission mismatch')
    ledger.check_job_admission()
    return sha(args.admission)


def mapped_state(design,pins,contract,source,rtl):
    result=mapped.verify(design,pins,contract,source,rtl)
    for w in result['words']:
        if w['owner']=='input_service' and not w['valid']:w['reset']=0
    return result


def report(out,source,task,pins,execute,base):
    contract=read(source['endpoint_contract']);state=read(out/'mapped-state.json')
    with patch.object(physical,'SUFFIX',SUFFIX):owners=readout.certificate(out,out,'grt',contract)
    requests=readout.requests(state,owners)
    expected={r['cell'].replace('\\','') for w in state['words'] for r in w['rows'] if 'cell' in r}
    actual={n for n,m in owners['instances'].items() if owners['liberty'][m]['sequential']}
    if actual!=expected:raise ValueError('CTS changed storage inventory')
    folder=out/'readout';folder.mkdir()
    write(folder/'ownership.json',owners);write(folder/'requests.json',requests);write(folder/'mapped-state.json',state)
    constants={n:v for q in requests.values() for n,v in q.get('constant_to_ports',{}).items()}
    template=(ROOT/'experiments/arithmetic_dse/reference_assets/stage7_readout_v1.tcl').read_text()
    template=template.replace('set targets [s7_pins [dict get $q to_pins]]','set targets [s7_pins [dict get $q to_pins]]\n        if {[dict exists $q to_ports]} {foreach name [dict get $q to_ports] {set p [get_ports [list $name]];if {[llength $p]!=1 || [get_full_name [lindex $p 0]] ne $name} {error "missing output port"};lappend targets [lindex $p 0]}}')
    template=template.replace('[dict get $q class]','[expr {[dict exists $q path_class] ? [dict get $q path_class] : [dict get $q class]}]')
    template=template.replace('[get_property $point arrival]','[expr {1000.0 * [get_property $point arrival]}]')
    template=template.replace('[get_property $path slack]','[expr {1000.0 * [get_property $path slack]}]')
    # Convert native STA ns to ps before serializing path points and slacks.
    adapted=folder/'reader.tcl';adapted.write_text(template)
    o=read(Path(source['folder'])/'owners.json');v=read(Path(source['folder'])/'view.json')
    stages={'node_'+str(r['node']):v['placement'][r['node']] for r in o['operators']}
    stages.update({'node_'+str(r['root']):v['placement'][r['root']] for r in o['G_regions']})
    tcl=readout.tcl;prefix=folder/'timing';script=folder/'load.tcl'
    checks=''
    for n,val in constants.items():
        checks+='set p [get_ports [list '+tcl(n)+']]\nif {[sta::pin_sim_logic_value [sta::get_port_pin [lindex $p 0]]] ne '+tcl(val)+'} {error "constant output differs"}\n'
    script.write_text('source $::env(SCRIPTS_DIR)/load.tcl\nload_design 5_1_grt.odb 5_1_grt.sdc\nset_propagated_clock [all_clocks]\nestimate_parasitics -global_routing\n'+checks+
        'set stage7_prefix '+tcl(prefix)+'\nset stage67_owners '+tcl(owners['owners'])+'\nset stage67_masters '+tcl(owners['instances'])+
        '\nset stage67_node_stages '+tcl(stages)+'\nset stage7_requests '+tcl(requests)+'\nset stage67_readout_script '+tcl(adapted)+
        '\nsource '+tcl(ROOT/'experiments/arithmetic_dse/reference_assets/stage67_context_v1.tcl')+'\n')
    execute(base+['run','RUN_SCRIPT='+str(script),'RUN_LOG_NAME_STEM=n56_readout','VULSIM_EVAL_DB=5_1_grt.odb','VULSIM_EVAL_SDC=5_1_grt.sdc'],'readout')
    result=analyze.parse_stage(folder)
    result.update(target_ps=task['period_ps'],source=source['id'],source_group=source['source_group'],role=task['role'],
        profile_sha256=profile('nangate45')['profile_sha256'],platform='nangate45',stage='grt',
        ownership_sha256=sha(folder/'ownership.json'),mapped_state_sha256=sha(out/'mapped-state.json'))
    write(out/'pipeline-labels.json',result)
    return result


def point(root,task):
    a=campaign.verify(root);source=next(s for s in a['sources'] if s['id']==task['source']);out=root/'runs'/task['id']
    if out.exists():raise ValueError('retain previous attempt; no implicit rerun')
    ledger=PipelineLedger(root,task);ctx=dict(target_platform='nangate45',admission_id=a['id'],task_id=task['id'])
    env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',YOSYS_MAX_THREADS='2',PYTHONDONTWRITEBYTECODE='1',QT_QPA_PLATFORM='offscreen')
    namespace=dict(backend._evaluate.__globals__);namespace.update(rtl_ports=sdc.rtl_ports,verify_sdc=sdc.verify_sdc,SDC_CONTRACT_VERSION=sdc.VERSION)
    evaluate=FunctionType(backend._evaluate.__code__,namespace)
    with ledger.job(ctx),ExitStack() as stack:
        stack.enter_context(patch.object(backend,'POLICY',runtime.POLICY));stack.enter_context(patch.object(platform_probe,'verify_admission',admission_check))
        args=SimpleNamespace(out=out,platform='nangate45',threads=2,stage='synth',memory_limit_mib=4096,
            period_ps=task['period_ps'],period_role='resource_trial',abc_target_ps=task['period_ps'],io_delay_max_ps=None,
            budget_purpose='characterization',admission_id=a['id'],task_id=task['id'],sample_contract=None,
            admission=root/'admission.json',resume_synth_from=None,orfs=ORFS,rtl=Path(source['rtl']),top='ModelBundle',
            synth_timeout_s=300,route_timeout_s=1200,selection_freeze=None)
        if evaluate(args,ledger):raise ValueError('N56 synth failed')
        m=read(out/'manifest.json');base=next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'))
        side=max(60,math.ceil(math.sqrt(m['metrics'][0]['cell_area_um2']/.4)))
        base+=['CORE_UTILIZATION=','DIE_AREA=0 0 '+str(side+10)+' '+str(side+10),'CORE_AREA=5 5 '+str(side+5)+' '+str(side+5)]
        commands=[]
        def execute(cmd,name,timeout=120,stage=None):
            r=ledger.reserve(stage,timeout,2,'nangate45_offline_pipeline',cmd,out/name,context=ctx)
            record=run_command(cmd,out,name,timeout,env,4096,cpu_limit_s=r['CPU_time_s']);ledger.finish(r,record)
            commands.append(dict(**record,budget_reservation_id=r['id']));write(out/'pipeline-commands.json',commands)
            if record['exit_code']:raise ValueError('N56 leaf failed: '+record['log'])
        cells=read(out/'liberty_cells.json')['cells'];pins=with_timing_arcs(liberty(m['libraries'],cells),m['libraries']);write(out/'liberty-pins.json',pins)
        script=out/'mapped.ys';script.write_text('\n'.join(['read_liberty -lib '+l['path'] for l in m['libraries']]+[
            'read_verilog '+str(out/'results'/SUFFIX/'1_2_yosys.v'),'hierarchy -top ModelBundle','write_json '+str(out/'mapped.json')])+'\n')
        execute([m['tools']['yosys']['path'],'-s',str(script)],'mapped-json')
        state=mapped_state(read(out/'mapped.json'),pins,read(source['endpoint_contract']),read(Path(source['folder'])/'source.json'),Path(source['rtl']).read_text())
        write(out/'mapped-state.json',state)
        wrapper_path=out/'live-cec.py';wrapper_path.write_text('import sys\nsys.path.insert(0,'+repr(str(ROOT))+')\nfrom experiments.arithmetic_dse.nangate45_cec import main\nmain()\n')
        req=out/'live-cec-request.json';write(req,dict(libraries=m['libraries'],admission_sha256=sha(root/'admission.json'),collection_plan_sha256=sha(root/'admission.json'),
            sequential_clock_pins={n:v['clock_pins'] for n,v in pins.items() if v['sequential']}))
        cts=out/'flow-scripts/cts.tcl';cts.unlink();cts.write_text(render_cts((ORFS/'flow/scripts/cts.tcl').read_text(),wrapper_path,req,out/'logs'/SUFFIX/'structural_cec'))
        execute(base+['grt'],'grt',1200,'grt')
        execute(base+['run','RUN_SCRIPT='+str(backend.ASSETS/'snapshot.tcl'),'RUN_LOG_NAME_STEM=n56_grt','VULSIM_EVAL_STAGE=grt',
            'VULSIM_EVAL_DB=5_1_grt.odb','VULSIM_EVAL_SDC=5_1_grt.sdc'],'snapshot')
        prefix=out/'census-grt';script=out/'census.tcl';script.write_text('source $::env(SCRIPTS_DIR)/load.tcl\nload_design 5_1_grt.odb 5_1_grt.sdc\nset ownership_prefix {'+str(prefix)+'}\nsource {'+str(ROOT/'experiments/arithmetic_dse/reference_assets/ownership_census_v1.tcl')+'}\n')
        execute(base+['run','RUN_SCRIPT='+str(script),'RUN_LOG_NAME_STEM=n56_census','VULSIM_EVAL_DB=5_1_grt.odb','VULSIM_EVAL_SDC=5_1_grt.sdc'],'census')
        p=profile('nangate45');metrics=backend.stage_metrics(out/'reports'/SUFFIX,'grt',cells,task['period_ps'],selected=p)
        metrics['stored_SDC']=sdc.verify_sdc((out/'results'/SUFFIX/'5_1_grt.sdc').read_text(),p,task['period_ps'],sdc.rtl_ports(Path(source['rtl']).read_text(),'ModelBundle'),serialization_stage='grt')
        metrics['wire_RC']=verify_wire_readback(out/'reports'/SUFFIX/'vulsim_grt_layer_rc.tsv',p)
        verify_proof(out/'logs'/SUFFIX/'structural_cec/proof.json',out/'results'/SUFFIX/'4_before_rsz_lec.v',out/'results'/SUFFIX/'4_after_rsz_lec.v')
        labels=report(out,source,task,pins,execute,base)
        if not math.isclose(labels['total_area_um2'],metrics['cell_area_um2'],abs_tol=1e-5):raise ValueError('N56 total area conservation')
        labels.update(whole_shell_metrics=metrics,CTS_CEC_sha256=sha(out/'logs'/SUFFIX/'structural_cec/proof.json'))
        write(out/'pipeline-labels.json',labels)
        write(out/'pipeline-status.json',dict(status='completed',label_sha256=sha(out/'pipeline-labels.json')))
    print('N56 COMPLETE '+task['id'],flush=True)
