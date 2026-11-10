"""Six prospective S reuse validations with existing Ledger/CEC, no refitting."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shutil
import time
from types import FunctionType,SimpleNamespace

from .model_fast_preflight import read,write,sha
from .conditional_boundary_binding import ROOT,SUFFIX,strict_data_wires
from .budget import Ledger,POLICY,usage,BudgetExceeded


def admit(folder,proof_path):
    from .operator_collection import measurement_sources
    proposal=read(folder/'proposal.json');proof=read(proof_path)
    if proof['status']!='passed' or proof['proposal_sha256']!=sha(folder/'proposal.json') or proof['binding_sha256']!=proposal['frozen_candidate_sha256'] or proof['old_independent_labels_read']:raise ValueError('new state-bank software proof mismatch')
    if sha(folder/'binding-candidate.json')!=proposal['frozen_candidate_sha256'] or sha(folder/'reused-S.json')!=proposal['S_sha256']:raise ValueError('frozen reuse parameters changed')
    for name,h in proposal['source_sha256'].items():
        if sha(ROOT/name)!=h:raise ValueError('frozen proposal producer changed '+name)
    state=read(Ledger().path);u=usage(state['entries']);limits=read(POLICY)['resources'];later=proposal['later_work_reserved'];wall=6*(300+1200+2*120)
    if (u['synth']+6+later['synth']>limits['max_synthesis_calls'] or u['grt']+6+later['grt']>limits['max_global_route_calls'] or u['walltime_s']+wall+later['walltime_s']>limits['max_global_walltime_h']*3600 or u['CPU_time_s']+wall*4+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600 or shutil.disk_usage(folder).free<later['storage_bytes']+6*512*1024**2):raise ValueError('limited S validation and reserved later work not funded')
    names=set(measurement_sources())|{str(Path(__file__).relative_to(ROOT)),'experiments/arithmetic_dse/conditional_boundary_binding.py','experiments/arithmetic_dse/conditional_boundary_binding_v2.py','regression/arithmetic_state_boundary.py',
        'experiments/arithmetic_dse/model_general_state_labels.py','experiments/arithmetic_dse/model_general_state_samples.py','experiments/arithmetic_dse/model_general_state_samples_v2.py','experiments/arithmetic_dse/reference_assets/snapshot.tcl'}
    freeze=folder/'measurement-source';freeze.mkdir();hashes={}
    for name in sorted(names):
        dest=freeze/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest);hashes[name]=sha(dest)
    admission=dict(version='conditional-S-validation-admission-v1',id=folder.name+'-S6',tasks=proposal['tasks'],sources=hashes,
        software_proof_path=str(proof_path),software_proof_sha256=sha(proof_path),proposal_sha256=sha(folder/'proposal.json'),candidate_sha256=proposal['frozen_candidate_sha256'],
        S_sha256=proposal['S_sha256'],source_role='binding_validation',automatic_retries=0,max_synth=6,max_grt=6,parallel_jobs=1,later_work_reserved=later,
        independent_labels_read=False,S_coefficients_may_change=False,full_D_ready=False)
    write(folder/'admission.json',admission);write(folder/'validation-progress.json',dict(phase='admitted',completed=[],errors=[],active=None))
    print('S6_VALIDATION_ADMITTED; immutable S/shared candidate; 6 synth/grt maximum; one slot',flush=True)


class ValidationLedger(Ledger):
    def __init__(self,folder,task):super().__init__();self.folder=folder;self.task=task
    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a=read(self.folder/'admission.json')
        if self.task not in a['tasks'] or stage not in (None,'synth','grt') or threads!=4:raise ValueError('unregistered S validation leaf')
        for name,h in a['sources'].items():
            if sha(ROOT/name)!=h or sha(self.folder/'measurement-source'/name)!=h:raise ValueError('S measurement producer changed '+name)
        if sha(self.folder/'binding-candidate.json')!=a['candidate_sha256'] or sha(self.folder/'reused-S.json')!=a['S_sha256'] or sha(self.task['rtl'])!=self.task['rtl_sha256']:raise ValueError('S validation frozen source/parameters changed')
        state=read(self.path);total=usage(state['entries']);limits=read(POLICY)['resources'];later=a['later_work_reserved']
        if stage and any(e.get('admission_id')==a['id'] and e.get('task_id')==self.task['id'] and e['stage']==stage for e in state['entries']):raise ValueError('no repeated physical S validation stage')
        if (total['walltime_s']+timeout_s+later['walltime_s']>limits['max_global_walltime_h']*3600 or total['CPU_time_s']+timeout_s*4+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600 or shutil.disk_usage(self.folder).free<later['storage_bytes']+1024**3):raise ValueError('S leaf would consume later-work reserve')
        return super().reserve(stage,timeout_s,threads,purpose,command,output,context={**(context or {}),'target_platform':'asap7','admission_id':a['id'],'task_id':self.task['id'],'admission_sha256':sha(self.folder/'admission.json'),'model_version':'frozen-S-reuse-validation-v1'})


def point(folder,task):
    from . import backend
    from . import model_fast_sdc_v3 as sdc
    from .platforms import profile,verify_wire_readback
    from .model_reference_labels import liberty
    from .model_qualification_labels import with_timing_arcs
    from .model_general_state_labels import partition,labels,render_requests
    from .model_m2_mux_collection import render_cts
    from .model_m2_live_cec_v3 import verify_proof
    from .processes import run_command
    a=read(folder/'admission.json');out=folder/'runs'/task['id'];ledger=ValidationLedger(folder,task);ctx=dict(target_platform='asap7',admission_id=a['id'],task_id=task['id'])
    if out.exists():raise ValueError('S point already attempted; preserve failure, no automatic retries')
    env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',YOSYS_MAX_THREADS='4',QT_QPA_PLATFORM='offscreen',VULSIM_REFERENCE_REQUESTS=str(out/'requests.tcl'))
    namespace=dict(backend._evaluate.__globals__);namespace.update(rtl_ports=sdc.rtl_ports,verify_sdc=sdc.verify_sdc,SDC_CONTRACT_VERSION=sdc.VERSION,os=SimpleNamespace(environ=env))
    evaluate=FunctionType(backend._evaluate.__code__,namespace,closure=backend._evaluate.__closure__)
    with ledger.job(ctx):
        args=SimpleNamespace(out=out,platform='asap7',threads=4,stage='synth',memory_limit_mib=8192,period_ps=task['period_ps'],period_role='resource_trial',abc_target_ps=task['abc_target_ps'],io_delay_max_ps=None,budget_purpose='characterization',admission_id=a['id'],task_id=task['id'],sample_contract=None,admission=None,resume_synth_from=None,orfs=Path('/home/zyrv/OpenROAD-flow-scripts'),rtl=Path(task['rtl']),top='ModelBundle',synth_timeout_s=300,route_timeout_s=1200,selection_freeze=None)
        evaluate(args,ledger);m=read(out/'manifest.json')
        if m['status']!='completed':raise ValueError('S synthesis failed '+str(m.get('failure_reason')))
        base=next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'));m.update(status='running',data_role='binding_validation',S_reuse_admission_sha256=sha(folder/'admission.json'),sdc_contracts={})
        def save():write(out/'manifest.json',m)
        def execute(command,name,timeout,stage=None):
            reservation=ledger.reserve(stage,timeout,4,'conditional_S_validation',command,out/name,context=ctx);record=run_command(command,out,name,timeout,env,8192,cpu_limit_s=reservation['CPU_time_s']);ledger.finish(reservation,record);m['commands'].append(dict(record,budget_reservation_id=reservation['id']));save()
            if record['exit_code']:raise ValueError('S '+name+' failed')
        try:
            spec=read(task['contract'])['spec'];shutil.copy2(task['contract'],out/'general-state-contract.json');(out/'requests.tcl').write_text(render_requests())
            wrapper=out/'live-cec.py';wrapper.write_text('import sys\nsys.path.insert(0,'+repr(str(ROOT))+')\nfrom experiments.arithmetic_dse.model_m2_live_cec_v3 import main\nmain()\n')
            request=out/'live-cec-request.json';write(request,dict(libraries=m['libraries'],admission_sha256=sha(folder/'admission.json'),collection_plan_sha256=sha(folder/'admission.json')))
            cts=out/'flow-scripts/cts.tcl';cts.unlink();cts.write_text(render_cts((args.orfs/'flow/scripts/cts.tcl').read_text(),wrapper,request,out/'logs'/SUFFIX/'structural_cec'))
            snapshot=out/'S-snapshot.tcl';text=(backend.ASSETS/'snapshot.tcl').read_text()
            text=text.replace('source [file join [file dirname [info script]] rc_readback.tcl]','source {'+str(backend.ASSETS/'rc_readback.tcl')+'}')
            text=text.replace('source [file join [file dirname [info script]] model_labels.tcl]','source {'+str(ROOT/'experiments/arithmetic_dse/reference_assets/snapshot.tcl')+'}')
            snapshot.write_text(text);pins=with_timing_arcs(liberty(m['libraries'],read(out/'liberty_cells.json')['cells']),m['libraries']);write(out/'liberty-pins.json',pins)
            cells=read(out/'liberty_cells.json')['cells'];m['metrics']=[];save()
            for stage,stem in [('synth','1_synth'),('grt','5_1_grt')]:
                if stage=='grt':execute(base+['grt'],'grt',1200,'grt')
                execute(base+['run','RUN_SCRIPT='+str(snapshot),'RUN_LOG_NAME_STEM=S_'+stage,'VULSIM_EVAL_STAGE='+stage,'VULSIM_EVAL_DB='+stem+'.odb','VULSIM_EVAL_SDC='+stem+'.sdc'],'S-'+stage+'-snapshot',120)
                reports=out/'reports'/SUFFIX;prefix=reports/('vulsim_'+stage);g=backend.stage_metrics(reports,stage,cells,task['period_ps'],selected=profile('asap7'))
                ownership,instances,_=partition(prefix,pins,profile('asap7'),spec);write(out/('S-'+stage+'-ownership.json'),ownership)
                if abs(ownership['total_area_um2']-g['cell_area_um2'])>1e-6:raise ValueError('S area ownership does not conserve')
                paths=labels(prefix,task['period_ps'],g['raw_report_units']['time']['to_ps'],pins,instances)
                wires=[v for path in paths if path['kind']=='register' for v in strict_data_wires(out,stage,path)]
                g.update(owner_area_um2=ownership['owner_area_um2'],owner_FF_bits=ownership['owner_FF_bits'],boundary_paths=paths,wire_increment_max_ps=max(wires,default=0),strict_actual_Liberty_arcs_and_wire_nets_checked=True)
                g['wire_RC_readback']=verify_wire_readback(Path(str(prefix)+'_layer_rc.tsv'),profile('asap7'));m['sdc_contracts'][stage]=sdc.verify_sdc((out/'results'/SUFFIX/(stem+'.sdc')).read_text(),profile('asap7'),task['period_ps'],sdc.rtl_ports((out/'input.sv').read_text(),'ModelBundle'),serialization_stage=stage)
                native=read(out/'logs'/SUFFIX/(stem+'.json'))[('synth' if stage=='synth' else 'globalroute')+'__design__instance__area__stdcell'];g['orfs_area_crosscheck']=backend.verify_orfs_area(g['cell_area_um2'],native)
                if not g['timing_coverage_complete']:raise ValueError('S unconstrained timing paths')
                m['metrics'].append(g);save()
            verify_proof(out/'logs'/SUFFIX/'structural_cec/proof.json',out/'results'/SUFFIX/'4_before_rsz_lec.v',out/'results'/SUFFIX/'4_after_rsz_lec.v');m['status']='completed';write(out/'metrics.json',m['metrics'])
        except Exception as error:m.update(status='failed',failure_reason=str(error))
        finally:m['finished_at']=datetime.now(timezone.utc).isoformat();m['evidence_sha256']={str(p.relative_to(out)):sha(p) for sub in ('reports','results','logs') for p in (out/sub).rglob('*') if p.is_file()};save()
        if m['status']!='completed':raise ValueError(task['id']+': '+m.get('failure_reason','unknown'))
        print('S_REUSE_POINT_COMPLETE '+task['id'],flush=True)


def run(folder):
    a=read(folder/'admission.json');p=read(folder/'validation-progress.json')
    for task in a['tasks']:
        if task['id'] in p['completed']:continue
        if p['errors']:raise ValueError('S validation stopped on error; diagnosis required')
        p.update(phase='running',active=task['id']);write(folder/'validation-progress.json',p)
        try:
            while True:
                try:point(folder,task);break
                except BudgetExceeded as e:
                    if 'slots occupied' not in str(e):raise
                    time.sleep(5)
            p['completed'].append(task['id'])
        except Exception as error:p['errors'].append(dict(task=task['id'],error=str(error)));p.update(phase='stopped_on_error',active=None);write(folder/'validation-progress.json',p);raise
        p.update(phase='point_settled',active=None);write(folder/'validation-progress.json',p)
    p['phase']='validation_complete';write(folder/'validation-progress.json',p)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('admit','run'));p.add_argument('--folder',type=Path,required=True);p.add_argument('--proof',type=Path);a=p.parse_args()
    if a.action=='admit':admit(a.folder.resolve(),a.proof.resolve())
    else:run(a.folder.resolve())
