"""Two exact serial pilot measurements; immutable physical inputs, no retries.

Keeps the preregistered joint tests locked.  All EDA and report commands are
charged to the common Ledger.  Label analysis has its own successor identity;
collecting a physical snapshot never grants S/G or formal-D qualification.
"""
import argparse
from datetime import datetime,timezone
import os
from pathlib import Path
import re
import shutil
from types import FunctionType,SimpleNamespace

from .model_fast_preflight import read,write,sha
from .budget import Ledger,POLICY,usage
from . import backend,model_fast_sdc_v3 as sdc
from .platforms import profile,verify_wire_readback
from .operator_condition_model import query
from .stage7_physical_prepare import compose
from . import stage67_mapped_state_v1 as mapped

ROOT=Path(__file__).resolve().parents[2]
ORFS=Path('/home/zyrv/OpenROAD-flow-scripts')
SUFFIX=Path('asap7/arithmetic_probe/base')


def admit(root,preparation,software,model,binding):
    if (root/'admission.json').exists():raise ValueError('preserve existing admission')
    data=read(software/'manifest.json')
    if data['status']!='passed_stage_export' or data['model_sha256']!=sha(model) or data['S_binding_sha256']!=sha(binding):raise ValueError('real joint software/model identity mismatch')
    manifest=read(preparation/'structures.json');source=read(preparation/'sources/serial/request.json');export=read(software/'serial/export.json')
    tasks=[];model_value=read(model)
    for row in manifest['rows']:
        if row['source']!='serial':continue
        if row['role']!='combination_validation':raise ValueError('pilot may not consume locked joint source')
        v=next(v for v in export['variants'] if v['id']==row['placement'])
        target=next(t for t in v['targets'] if t['target_ps']==1500)
        prices=[dict(node=q['trace']['node'],**query(model_value,q['descriptor'])) for q in target['queries']]
        baseline=compose(export,v,target,prices)
        if baseline['status']!='diagnostic_covered':raise ValueError('pilot has an uncovered node/S dependency')
        original=preparation/row['rtl'];text=original.read_text();matches=re.findall(r'\bmodule\s+(Stage7_\w+)\s*\(',text)
        if len(matches)!=1 or sha(original)!=row['rtl_sha256']:raise ValueError('prepared physical RTL changed')
        directory=root/'inputs'/row['placement'];directory.mkdir(parents=True)
        rtl=directory/'input.sv';rtl.write_text(text.replace('module '+matches[0]+'(','module ModelBundle('))
        contract=preparation/row['endpoint_contract'];shutil.copy2(contract,directory/'endpoints.json')
        write(directory/'source.json',source);write(directory/'export.json',export)
        write(directory/'baseline.json',dict(model_sha256=sha(model),S_binding_sha256=sha(binding),variant=v['id'],target_ps=1500,
            prices=prices,zero_G=baseline,placement_selected_before_prices=True,full_D_ready=False))
        tasks.append(dict(id='serial-'+row['placement']+'-T1500',source='serial',placement=row['placement'],source_role='combination_validation',
            period_ps=1500,rtl=str(rtl),rtl_sha256=sha(rtl),prepared_rtl_sha256=row['rtl_sha256'],top_rename_only=True,
            endpoint_contract=str(directory/'endpoints.json'),endpoint_sha256=sha(directory/'endpoints.json'),input_directory=str(directory)))
    if len(tasks)!=2:raise ValueError('pilot must contain exactly two predeclared serial placements')
    later=dict(synth=688,grt=688,walltime_s=86400,CPU_time_s=172800,storage_bytes=30*1024**3)
    used=usage(read(Ledger().path)['entries']);limits=read(POLICY)['resources'];wall=2*(300+1200+12*120)
    if (used['synth']+2+later['synth']>limits['max_synthesis_calls'] or used['grt']+2+later['grt']>limits['max_global_route_calls'] or
        used['walltime_s']+wall+later['walltime_s']>limits['max_global_walltime_h']*3600 or
        used['CPU_time_s']+wall*4+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600 or shutil.disk_usage(root).free<later['storage_bytes']+2*1024**3):raise ValueError('pilot and later work not funded')
    from .operator_collection import measurement_sources
    names=set(measurement_sources())|{str(Path(__file__).relative_to(ROOT)),str(Path(mapped.__file__).relative_to(ROOT))}
    hashes={}
    for name in sorted(names):
        dest=root/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest);hashes[name]=sha(dest)
    write(root/'admission.json',dict(version='stage67-two-serial-pilot-v1',id=root.name+'-serial-pilot',tasks=tasks,
        model=dict(path=str(model),sha256=sha(model)),S_binding=dict(path=str(binding),sha256=sha(binding)),
        preparation=dict(path=str(preparation),protocol_sha256=sha(preparation/'protocol.json')),software_manifest_sha256=sha(software/'manifest.json'),
        sources=hashes,synth_max=2,grt_max=2,support_max=32,synth_timeout_s=300,grt_timeout_s=1200,
        automatic_retries=0,parallel_jobs=1,threads=4,memory_limit_MiB=8192,later_work_reserved=later,
        scope='combination-validation pilot, S reuse and zero-G diagnosis; no independent-test unlock',full_D_ready=False))
    write(root/'progress.json',dict(phase='admitted',completed=[],errors=[],active=None))
    print('STAGE67_SERIAL_PILOT_ADMITTED exact_requests=2 T=1500 locked_tests=0',flush=True)


class PilotLedger(Ledger):
    def __init__(self,root,task):super().__init__();self.root=root;self.task=task
    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a=read(self.root/'admission.json')
        if self.task not in a['tasks'] or stage not in (None,'synth','grt') or threads!=4:raise ValueError('unregistered pilot leaf')
        for name,h in a['sources'].items():
            if sha(ROOT/name)!=h or sha(self.root/'source'/name)!=h:raise ValueError('pilot physical producer drift '+name)
        for name in ('model','S_binding'):
            if sha(a[name]['path'])!=a[name]['sha256']:raise ValueError('pilot frozen baseline changed')
        if sha(self.task['rtl'])!=self.task['rtl_sha256']:raise ValueError('pilot RTL drift')
        entries=[e for e in read(self.path)['entries'] if e.get('admission_sha256')==sha(self.root/'admission.json')]
        if stage and (timeout_s>a[stage+'_timeout_s'] or any(e['stage']==stage and e.get('task_id')==self.task['id'] for e in entries)):raise ValueError('physical pilot retries prohibited')
        if stage is None and (timeout_s>120 or sum(e['stage'] is None for e in entries)>=a['support_max']):raise ValueError('pilot report budget exceeded')
        return super().reserve(stage,timeout_s,threads,purpose,command,output,context={**(context or {}),
            'target_platform':'asap7','admission_id':a['id'],'task_id':self.task['id'],'admission_sha256':sha(self.root/'admission.json')})


def point(root,task):
    from .model_reference_labels import liberty
    from .model_qualification_labels import with_timing_arcs
    from .model_m2_mux_collection import render_cts
    from .model_m2_live_cec_v3 import verify_proof
    from .processes import run_command
    a=read(root/'admission.json');out=root/'runs'/task['id'];ledger=PilotLedger(root,task)
    ctx=dict(target_platform='asap7',admission_id=a['id'],task_id=task['id'])
    env=os.environ.copy();env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',YOSYS_MAX_THREADS='4',PYTHONDONTWRITEBYTECODE='1',QT_QPA_PLATFORM='offscreen')
    namespace=dict(backend._evaluate.__globals__);namespace.update(rtl_ports=sdc.rtl_ports,verify_sdc=sdc.verify_sdc,SDC_CONTRACT_VERSION=sdc.VERSION)
    evaluate=FunctionType(backend._evaluate.__code__,namespace,closure=backend._evaluate.__closure__)
    with ledger.job(ctx):
        args=SimpleNamespace(out=out,platform='asap7',threads=4,stage='synth',memory_limit_mib=8192,period_ps=1500,period_role='resource_trial',abc_target_ps=1500,io_delay_max_ps=None,
            budget_purpose='characterization',admission_id=a['id'],task_id=task['id'],sample_contract=None,admission=None,resume_synth_from=None,orfs=ORFS,
            rtl=Path(task['rtl']),top='ModelBundle',synth_timeout_s=300,route_timeout_s=1200,selection_freeze=None)
        if evaluate(args,ledger):raise ValueError('pilot synth failed')
        manifest=read(out/'manifest.json');base=next(c['command'][:-1] for c in manifest['commands'] if c['log'].endswith('/synth.log'));commands=[]
        def execute(command,name,timeout=120,stage=None):
            r=ledger.reserve(stage,timeout,4,'stage67_physical_pilot',command,out/name,context=ctx)
            record=run_command(command,out,name,timeout,env,8192,cpu_limit_s=r['CPU_time_s']);ledger.finish(r,record)
            commands.append(dict(**record,budget_reservation_id=r['id']));write(out/'pilot-commands.json',commands)
            if record['exit_code']:raise ValueError('pilot leaf failed '+record['log'])
        cells=read(out/'liberty_cells.json')['cells'];pins=with_timing_arcs(liberty(manifest['libraries'],cells),manifest['libraries']);write(out/'liberty-pins.json',pins)
        script=out/'mapped.ys';script.write_text('\n'.join(['read_liberty -lib '+l['path'] for l in manifest['libraries']]+[
            'read_verilog '+str(out/'results'/SUFFIX/'1_2_yosys.v'),'hierarchy -top ModelBundle','write_json '+str(out/'mapped.json')])+'\n')
        execute([manifest['tools']['yosys']['path'],'-s',str(script)],'mapped-json')
        contract=mapped.verify(read(out/'mapped.json'),pins,read(task['endpoint_contract']),read(Path(task['input_directory'])/'source.json'))
        write(out/'mapped-state.json',contract)
        wrapper=out/'live-cec.py';wrapper.write_text('import sys\nsys.path.insert(0,'+repr(str(ROOT))+')\nfrom experiments.arithmetic_dse.model_m2_live_cec_v3 import main\nmain()\n')
        request=out/'live-cec-request.json';write(request,dict(libraries=manifest['libraries'],admission_sha256=sha(root/'admission.json'),collection_plan_sha256=sha(root/'admission.json')))
        cts=out/'flow-scripts/cts.tcl';cts.unlink();cts.write_text(render_cts((ORFS/'flow/scripts/cts.tcl').read_text(),wrapper,request,out/'logs'/SUFFIX/'structural_cec'))
        metrics=[]
        for stage,stem in (('synth','1_synth'),('grt','5_1_grt')):
            if stage=='grt':execute(base+['grt'],'grt',1200,'grt')
            execute(base+['run','RUN_SCRIPT='+str(backend.ASSETS/'snapshot.tcl'),'RUN_LOG_NAME_STEM=pilot_'+stage,
                'VULSIM_EVAL_STAGE='+stage,'VULSIM_EVAL_DB='+stem+'.odb','VULSIM_EVAL_SDC='+stem+'.sdc'],'pilot-'+stage+'-snapshot')
            census=out/('census-'+stage+'.tcl');prefix=out/('census-'+stage)
            census.write_text('source $::env(SCRIPTS_DIR)/load.tcl\nload_design $::env(VULSIM_EVAL_DB) $::env(VULSIM_EVAL_SDC)\nset ownership_prefix {'+str(prefix)+'}\nsource {'+str(ROOT/'experiments/arithmetic_dse/reference_assets/ownership_census_v1.tcl')+'}\n')
            execute(base+['run','RUN_SCRIPT='+str(census),'RUN_LOG_NAME_STEM=census_'+stage,'VULSIM_EVAL_DB='+stem+'.odb','VULSIM_EVAL_SDC='+stem+'.sdc'],'census-'+stage)
            g=backend.stage_metrics(out/'reports'/SUFFIX,stage,cells,1500,selected=profile('asap7'))
            g['wire_RC_readback']=verify_wire_readback(out/'reports'/SUFFIX/('vulsim_'+stage+'_layer_rc.tsv'),profile('asap7'))
            g['stored_SDC']=sdc.verify_sdc((out/'results'/SUFFIX/(stem+'.sdc')).read_text(),profile('asap7'),1500,sdc.rtl_ports((out/'input.sv').read_text(),'ModelBundle'),serialization_stage=stage)
            native=read(out/'logs'/SUFFIX/(stem+'.json'))[('synth' if stage=='synth' else 'globalroute')+'__design__instance__area__stdcell'];backend.verify_orfs_area(g['cell_area_um2'],native)
            metrics.append(g);write(out/'pilot-metrics.json',metrics)
        verify_proof(out/'logs'/SUFFIX/'structural_cec/proof.json',out/'results'/SUFFIX/'4_before_rsz_lec.v',out/'results'/SUFFIX/'4_after_rsz_lec.v')
        write(out/'pilot-status.json',dict(status='physical_snapshots_collected',mapped_state_FF_census=True,CEC=True,
            source_role=task['source_role'],timing_qualification='pending_report_analysis',S_G_qualified=False,full_D_ready=False))
    print('STAGE67_PHYSICAL_PILOT_COMPLETE '+task['id'],flush=True)


def run(root):
    a=read(root/'admission.json');progress=read(root/'progress.json')
    if progress['errors']:raise ValueError('pilot stopped; diagnose preserved snapshot before successor')
    for task in a['tasks']:
        if task['id'] in progress['completed']:continue
        if (root/'runs'/task['id']).exists():raise ValueError('prior physical attempt exists; no automatic retry')
        progress.update(phase='running',active=task['id']);write(root/'progress.json',progress)
        try:point(root,task)
        except Exception as error:
            progress['errors'].append(dict(task=task['id'],reason=str(error)));progress.update(phase='stopped_on_error',active=None);write(root/'progress.json',progress);raise
        progress['completed'].append(task['id']);progress.update(phase='point_settled',active=None);write(root/'progress.json',progress)
    progress['phase']='physical_pilot_complete';write(root/'progress.json',progress)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('admit','run'));parser.add_argument('--root',type=Path,required=True)
    for name in ('preparation','software','model','binding'):parser.add_argument('--'+name,type=Path)
    args=parser.parse_args()
    if args.action=='admit':admit(args.root.resolve(),args.preparation.resolve(),args.software.resolve(),args.model.resolve(),args.binding.resolve())
    else:run(args.root.resolve())
