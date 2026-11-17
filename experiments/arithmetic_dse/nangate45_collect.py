"""Isolated two-thread N3 worker, strict ns-aware ownership labels.

The live ASAP7 policy, modules, admission and scheduler are never edited.
Both platforms use the same RTL and the same exclusive logical owner reader.
"""
import argparse
from collections import Counter
import csv
from contextlib import ExitStack
import inspect
import math
import os
from pathlib import Path
import shutil
import sys
from types import FunctionType, SimpleNamespace
from unittest.mock import patch

from . import backend,budget,platform_probe,workload_nine_runtime as runtime
from . import nangate45_samples as campaign
from .nangate45_samples import ROOT,read,write,sha
from . import model_fast_sdc_v3 as sdc
from . import model_logical_ownership_v2 as ownership, model_logical_labels_v1 as labels
from . import operator_ownership_replay_v1 as replay
from . import model_mapped_contract as mapped, wide_operator_samples as wide
from . import reduction_wide_sampling as reduction
from .model_reference_labels import liberty
from .model_qualification_labels import with_timing_arcs
from .model_m2_mux_collection import render_cts
from .nangate45_cec import verify_proof
from .platforms import profile,verify_wire_readback
from .processes import run_command

ORFS=Path('/home/zyrv/OpenROAD-flow-scripts');SUFFIX=Path('nangate45/arithmetic_probe/base')
ASSETS=Path(__file__).with_name('reference_assets')


def g_layout(query):return reduction.geometry(query)
def g_geometry(query):return reduction.geometry_contract(query)


def g_mapped(design,query,pins):
    text=inspect.getsource(mapped.mapped_contract).replace(
        'from .model_sampling_v2 import geometry_contract','from .nangate45_collect import g_geometry as geometry_contract').replace(
        'from .model_context_samples import layout','from .nangate45_collect import g_layout as layout')
    ns=dict(mapped.mapped_contract.__globals__);exec(compile(text,__file__,'exec'),ns)
    return ns['mapped_contract'](design,query,pins)


def verify_admission(args,p,rtl,ledger):
    a=campaign.verify(args.admission.parent)
    t=next(t for t in a['tasks'] if t['id']==args.task_id)
    expected=dict(platform=p['platform'],profile_sha256=p['profile_sha256'],rtl=str(rtl),rtl_sha256=sha(rtl),
                  period_ps=args.period_ps,abc_target_ps=args.abc_target_ps,stage=args.stage,threads=args.threads,
                  memory_limit_MiB=args.memory_limit_mib,top=args.top)
    frozen=dict(platform=a['platform'],profile_sha256=a['profile_sha256'],rtl=t['rtl'],rtl_sha256=t['rtl_sha256'],
                period_ps=t['period_ps'],abc_target_ps=t['period_ps'],stage='synth',threads=2,memory_limit_MiB=4096,top='ModelBundle')
    if expected!=frozen or args.admission_id!=a['id'] or args.period_role!='resource_trial' or args.resume_synth_from or args.io_delay_max_ps is not None:
        raise ValueError('task differs from frozen collection')
    ledger.check_job_admission()
    previous=[e for e in read(ledger.path)['entries'] if e.get('admission_id')==a['id']]
    if any(e.get('task_id')==t['id'] for e in previous):raise ValueError('attempt already charged; no retry')
    return sha(args.admission)


class CollectionLedger(runtime.NineLedger):
    def __init__(self,root,task):super().__init__();self.root=root;self.task=task
    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a=campaign.verify(self.root)
        if threads!=2 or stage not in (None,'synth','grt'):raise ValueError('unregistered leaf resource')
        old=[e for e in read(self.path)['entries'] if e.get('admission_id')==a['id']]
        own=[e for e in old if e.get('task_id')==self.task['id']]
        key=stage or 'support';cap=a['call_caps'][key]
        if sum((e['stage'] or 'support')==key for e in old)>=cap:raise ValueError('campaign call cap')
        if stage and any(e['stage']==stage for e in own):raise ValueError('physical stage already attempted')
        if not stage and sum(e['stage'] is None for e in own)>=10:raise ValueError('support cap')
        if timeout_s>a[{'synth':'synth_timeout_s','grt':'grt_timeout_s',None:'support_timeout_s'}[stage]]:raise ValueError('leaf timeout cap')
        return super().reserve(stage,timeout_s,threads,purpose,command,output,context={**(context or {}),
            'target_platform':'nangate45','admission_id':a['id'],'task_id':self.task['id'],
            'admission_sha256':sha(self.root/'admission.json'),'model_version':campaign.VERSION})


def logical_collect(out,base,target,pins,nodes,banks,execute,scale):
    d=out/'logical-v2-grt';d.mkdir(exist_ok=False);task=dict(stage='grt',folder=str(out))
    def command(script,tag):return base+['run','RUN_SCRIPT='+str(script),'RUN_LOG_NAME_STEM='+tag,
        'VULSIM_EVAL_DB=5_1_grt.odb','VULSIM_EVAL_SDC=5_1_grt.sdc','VULSIM_EVAL_STAGE=grt']
    script=d/'census.tcl';prefix=d/'census'
    script.write_text(replay.load_script(task)+'set ownership_prefix {'+str(prefix)+'}\nsource {'+str(ASSETS/'ownership_census_v1.tcl')+'}\n')
    execute(command(script,'logical_v2_census'),'logical-v2-grt-census')
    packet=dict(origin='physical_snapshot',period_ps=target,time_to_ps=scale,
        instances=dict(line.split('\t') for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines()),liberty=pins,
        connections={r['instance']+'/'+r['pin']:dict(direction=r['direction'],net=r['net']) for r in replay.table(Path(str(prefix)+'_connections.tsv'))},
        clock_nets=[r['net'] for r in replay.table(Path(str(prefix)+'_clock_nets.tsv'))],nodes={},pin_logic={},data_requests={},data_paths={})
    ports={r['port']:dict(direction=r['direction'],net=r['net']) for r in replay.table(Path(str(prefix)+'_ports.tsv'))}
    normalized=ownership.normalize(packet,nodes,banks);certificate=ownership.resolve(normalized,nodes,ports)
    write(d/'ownership-certificate.json',certificate);write(d/'top-ports.json',ports)
    if not certificate['complete']:raise ValueError('logical ownership unresolved')
    def tcl(v):
        if any(x in v for x in '{}\n\r'):raise ValueError('unsafe Tcl spelling')
        return '{'+v+'}'
    members={n:o for n,o in certificate['owners'].items() if o in nodes}
    setup='set context_logical_owners {'+' '.join(tcl(n)+' '+tcl(o) for n,o in members.items())+'}\n'
    setup+='set context_logical_masters {'+' '.join(tcl(n)+' '+tcl(normalized['instances'][n]) for n in members)+'}\n'
    script=d/'read-context.tcl';prefix=d/'context'
    script.write_text(replay.load_script(task)+'source {'+str(out/'query-contract.tcl')+'}\n'+setup+
        'set context_prefix {'+str(prefix)+'}\nsource {'+str(ASSETS/'context_readout_logical_v2.tcl')+'}\n')
    execute(command(script,'logical_v2_context'),'logical-v2-grt-readout')
    return labels.read_snapshot(prefix,target,scale,pins,nodes,banks,top_ports=ports,ownership_certificate=certificate)


def task_run(root,t):
    a=campaign.verify(root);out=root/'runs'/t['id'];source=next(s for s in a['sources'] if s['id']==t['source'])
    available=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))//1024
    if available<a['minimum_available_MiB']:raise budget.BudgetExceeded('retain 8GiB beyond 4GiB sampling cap')
    ledger=CollectionLedger(root,t);ctx=dict(target_platform='nangate45',admission_id=a['id'],task_id=t['id'])
    env=os.environ.copy();env.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',YOSYS_MAX_THREADS='2',PYTHONDONTWRITEBYTECODE='1',QT_QPA_PLATFORM='offscreen')
    with ledger.job(ctx),ExitStack() as stack:
        stack.enter_context(patch.object(backend,'POLICY',runtime.POLICY))
        stack.enter_context(patch.object(platform_probe,'verify_admission',verify_admission))
        ns=dict(backend._evaluate.__globals__);ns.update(rtl_ports=sdc.rtl_ports,verify_sdc=sdc.verify_sdc,SDC_CONTRACT_VERSION=sdc.VERSION)
        evaluate=FunctionType(backend._evaluate.__code__,ns)
        args=SimpleNamespace(out=out,platform='nangate45',threads=2,stage='synth',memory_limit_mib=4096,
            period_ps=t['period_ps'],period_role='resource_trial',abc_target_ps=t['period_ps'],io_delay_max_ps=None,
            budget_purpose='characterization',admission_id=a['id'],task_id=t['id'],sample_contract=None,
            admission=root/'admission.json',resume_synth_from=None,orfs=ORFS,rtl=Path(t['rtl']),top='ModelBundle',
            synth_timeout_s=300,route_timeout_s=1200,selection_freeze=None)
        if t.get('inherit_synth'):
            origin=Path(t['inherit_synth']['directory'])
            for name,h in t['inherit_synth']['files'].items():
                if sha(origin/name)!=h:raise ValueError('retained PDN predecessor changed')
            def ignore(directory,names):
                # Only the paid synthesis checkpoint can be inherited. In
                # particular, never inherit the failed undersized floorplan.
                prefixes=('grt.','collection-','logical-v2-','live-cec','structural_cec') if t.get('inherit_grt') else ('5_','6_','grt.','collection-','logical-v2-','live-cec','structural_cec') if t.get('inherit_post_repair') else ('2_','3_','4_','5_','6_','grt.','collection-','logical-v2-','live-cec')
                return [n for n in names if n.startswith(prefixes)]
            shutil.copytree(origin,out,symlinks=True,ignore=ignore)
            # Rebase copied text only. The original source, mapped netlist and
            # database remain byte identical, and the original failure stays.
            for path in out.rglob('*'):
                if path.is_file() and not path.is_symlink() and path.suffix in ('.json','.mk','.tcl','.py','.ys'):
                    text=path.read_text();path.write_text(text.replace(str(origin),str(out)))
            write(out/'synth-inheritance.json',t['inherit_synth'])
        elif evaluate(args,ledger):raise ValueError('synthesis failed')
        m=read(out/'manifest.json');base=next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'));commands=[]
        side=max(60,math.ceil(math.sqrt(m['metrics'][0]['cell_area_um2']/.4)))
        base+=['CORE_UTILIZATION=','DIE_AREA=0 0 '+str(side+10)+' '+str(side+10),
               'CORE_AREA=5 5 '+str(side+5)+' '+str(side+5)]
        write(out/'sampling-floorplan.json',dict(policy=a['sampling_layout_overrides'],core_side_um=side,
              command_overrides=base[-3:],synthesis_area_um2=m['metrics'][0]['cell_area_um2']))
        def execute(cmd,name,timeout=120,stage=None):
            r=ledger.reserve(stage,timeout,2,'nangate45_offline_operator_collection',cmd,out/name,context=ctx)
            record=run_command(cmd,out,name,timeout,env,4096,cpu_limit_s=r['CPU_time_s'])
            ledger.finish(r,record);commands.append(dict(**record,budget_reservation_id=r['id']));write(out/'collection-commands.json',commands)
            if record['exit_code']:raise ValueError('collection leaf failed: '+str(record['log']))
        libs=read(out/'liberty_cells.json')['cells'];pins=with_timing_arcs(liberty(m['libraries'],libs),m['libraries'])
        write(out/'liberty-pins.json',pins)
        script=out/'mapped.ys';mapped_v=out/'results'/SUFFIX/'1_2_yosys.v'
        script.write_text('\n'.join(['read_liberty -lib '+p['path'] for p in m['libraries']]+['read_verilog '+str(mapped_v),'hierarchy -top ModelBundle','write_json '+str(out/'mapped.json')])+'\n')
        execute([m['tools']['yosys']['path'],'-s',str(script)],'mapped-json')
        design=read(out/'mapped.json');f=source['query'] if t['family']=='G' else source['local_context']
        contract=g_mapped(design,f,pins) if t['family']=='G' else wide.mapped_contract(design,f,pins)
        port=reduction.mapped_port_contract(design,f,pins) if t['family']=='G' else wide.operator_port_contract(design,f,pins)
        write(out/'mapped-contract.json',contract);write(out/'operator-port-contract.json',port)
        execute(base+['run','RUN_SCRIPT='+str(ASSETS/'boundary_census.tcl'),'RUN_LOG_NAME_STEM=bank_census',
                      'VULSIM_EVAL_DB=1_synth.odb','VULSIM_EVAL_SDC=1_synth.sdc'],'mapped-census')
        connections=list(csv.DictReader((out/'reports'/SUFFIX/'boundary_connections.tsv').read_text().splitlines(),delimiter='\t'))
        setup,nodes,banks=wide.render_query_contract(contract,connections,f)
        (out/'query-contract.tcl').write_text(setup);write(out/'query-contract.json',dict(nodes=nodes,banks=banks))
        wrapper=out/'live-cec.py';wrapper.write_text('import sys\nsys.path.insert(0,'+repr(str(ROOT))+')\nfrom experiments.arithmetic_dse.nangate45_cec import main\nmain()\n')
        request=out/'live-cec-request.json';write(request,dict(libraries=m['libraries'],admission_sha256=sha(root/'admission.json'),collection_plan_sha256=sha(root/'admission.json'),
            sequential_clock_pins={n:v['clock_pins'] for n,v in pins.items() if v['sequential']}))
        cts=out/'flow-scripts/cts.tcl';cts.unlink();cts.write_text(render_cts((ORFS/'flow/scripts/cts.tcl').read_text(),wrapper,request,out/'logs'/SUFFIX/'structural_cec'))
        if t.get('inherit_post_repair'):
            # Continue exactly after repair and before its failed negative
            # clock witness; do not rerun CTS or timing optimization.
            original=(ORFS/'flow/scripts/cts.tcl').read_text()
            marker='  set result [catch { log_cmd detailed_placement } msg]'
            tail=original[original.index(marker):]
            tail=tail.replace('\n}\n\nreport_metrics 4 "cts final"','\n\nreport_metrics 4 "cts final"',1)
            cts.write_text('utl::set_metrics_stage "cts__{}"\nsource $::env(SCRIPTS_DIR)/load.tcl\nerase_non_stage_variables cts\n'
                'load_design 4_1_post_repair_pre_lec.odb 4_1_post_repair_pre_lec.sdc\nset_propagated_clock [all_clocks]\nestimate_parasitics -placement\n'
                f'exec {{{sys.executable}}} -B {{{wrapper}}} --request {{{request}}} --before $::env(RESULTS_DIR)/4_before_rsz_lec.v --after $::env(RESULTS_DIR)/4_after_rsz_lec.v --out {{{out/"logs"/SUFFIX/"structural_cec"}}}\n'+tail)
        if not t.get('inherit_grt'):execute(base+['grt'],'grt',1200,'grt')
        execute(base+['run','RUN_SCRIPT='+str(backend.ASSETS/'snapshot.tcl'),'RUN_LOG_NAME_STEM=qual_grt',
                      'VULSIM_EVAL_STAGE=grt','VULSIM_EVAL_DB=5_1_grt.odb','VULSIM_EVAL_SDC=5_1_grt.sdc'],'qual-grt-snapshot')
        reports=out/'reports'/SUFFIX;p=profile('nangate45');g=backend.stage_metrics(reports,'grt',libs,t['period_ps'],selected=p)
        for line in Path(str(reports/'vulsim_grt')+'_cells.tsv').read_text().splitlines():
            name,count,area,filler,kind=line.split('\t')
            if name not in pins:pins[name]=dict(sequential=False,buffer_or_inverter=False,physical_only=True,data_pins=[],pins={},area_um2=0 if filler=='1' else float(area))
            elif filler=='1' or kind in p['physical_master_types']:
                if any(v['direction'] in ('input','output') for v in pins[name]['pins'].values()):raise ValueError('physical-only cell has signal pins')
                pins[name]=dict(pins[name],physical_only=True,area_um2=0. if filler=='1' else float(area))
        result=logical_collect(out,base,t['period_ps'],pins,nodes,banks,execute,g['raw_report_units']['time']['to_ps'])
        if abs(result['total_cell_area_um2']-g['cell_area_um2'])>1e-5:raise ValueError('exclusive area conservation failed')
        native=read(out/'logs'/SUFFIX/'5_1_grt.json')['globalroute__design__instance__area__stdcell']
        backend.verify_orfs_area(g['cell_area_um2'],native)
        sdc_check=sdc.verify_sdc((out/'results'/SUFFIX/'5_1_grt.sdc').read_text(),p,t['period_ps'],sdc.rtl_ports((out/'input.sv').read_text(),'ModelBundle'),serialization_stage='grt')
        rc=verify_wire_readback(Path(str(reports/'vulsim_grt')+'_layer_rc.tsv'),p)
        proof_root=Path(t['inherited_CEC_root']) if t.get('inherit_grt') else out
        proof=proof_root/'logs'/SUFFIX/'structural_cec/proof.json'
        verify_proof(proof,proof_root/'results'/SUFFIX/'4_before_rsz_lec.v',proof_root/'results'/SUFFIX/'4_after_rsz_lec.v')
        result.update(stage='grt',source=t['source'],source_role=t['role'],target_platform='nangate45',profile_sha256=p['profile_sha256'],
                      physical_training_label_eligible=True,CTS_CEC_path=str(proof),CTS_CEC_sha256=sha(proof),metrics=g,stored_SDC_check=sdc_check,wire_RC_check=rc,
                      admission_sha256=sha(root/'admission.json'),rtl_sha256=sha(out/'input.sv'),sampling_layout_overrides=a['sampling_layout_overrides'])
        write(out/'grt-labels.json',result)
        write(out/'collection-status.json',dict(status='completed',source_role=t['role'],label_sha256=sha(out/'grt-labels.json')))
    print(t['id']+' COMPLETE '+t['role'],flush=True)


def run(root,role=None,task=None):
    root=Path(root).resolve();a=campaign.verify(root);progress=read(root/'progress.json')
    if progress['errors']:raise ValueError('campaign stopped; preserve error, diagnose before continuation')
    try:
        for t in a['tasks']:
            if (role and t['role']!=role) or (task and t['id']!=task) or t['id'] in progress['completed']:continue
            if t['role']=='test' and not (root/'frozen-model.json').exists():raise ValueError('freeze model before opening test backend labels')
            if (root/'runs'/t['id']).exists():raise ValueError('retained earlier attempt, no automatic retry')
            task_run(root,t);progress['completed'].append(t['id']);progress['phase']='collecting';write(root/'progress.json',progress)
        progress['phase']='complete' if len(progress['completed'])==len(a['tasks']) else 'partial';write(root/'progress.json',progress)
    except Exception as e:
        progress['phase']='stopped_on_error';progress['errors'].append(dict(task=t['id'],error=str(e)));write(root/'progress.json',progress);raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--role',choices=('train','validation','test'));p.add_argument('--task');a=p.parse_args();run(a.root,a.role,a.task)
