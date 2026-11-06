"""Preregistered ASAP7 reference cohort; pilot gate, shared ledger, no fitting."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
from datetime import datetime,timezone
import fcntl
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace

from .budget import Ledger,POLICY,usage
from .model_collection import sha,write
from .model_reference_samples import spec,source,render_requests

ROOT=Path(__file__).resolve().parents[2]
CONFIG=Path(__file__).with_name('configs')/'model_asap7_m2_reference_v1.json'
ASSET=Path(__file__).with_name('reference_assets')/'snapshot.tcl'
ORFS=Path('/home/zyrv/OpenROAD-flow-scripts')
SUFFIX=Path('asap7/arithmetic_probe/base')


def read(path):return json.loads(Path(path).read_text())
def exclusive(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')

def progress_write(folder,value):
    with tempfile.NamedTemporaryFile('w',dir=folder,delete=False,prefix='.reference-progress-') as f:
        json.dump(value,f,indent=2);f.write('\n');name=f.name
    os.replace(name,folder/'progress.json')


def prepare(folder,software,readers):
    from .platforms import profile
    from .model_m2_evaluate import measurement_identity
    cfg=read(CONFIG);proof=read(software);guards=read(readers)
    if (proof['status']!='passed' or guards['status']!='passed' or proof['protocol_sha256']!=sha(CONFIG)
        or len(guards['negative_checks'])!=9 or not proof['native_and_unconditional_external_captures_separate']):
        raise ValueError('complete reference software and reader proof required')
    for name,h in {**proof['producer_sha256'],**guards['producer_sha256']}.items():
        if sha(ROOT/name)!=h:raise ValueError('reference preflight producer changed: '+name)
    if guards['Liberty_pin_table_sha256']!=sha(software.parent/'liberty-pin-classes.json'):raise ValueError('reference Liberty pin table changed')
    if sha(proof['environment_manifest'])!=proof['environment_manifest_sha256'] or sha(proof['atom_path'])!=proof['atom_sha256']:
        raise ValueError('reference physical environment or atom changed')
    parent=read(proof['environment_manifest']);p=profile('asap7')
    for asset in [*parent['libraries'],*parent['tools'].values()]:
        if sha(asset['path'])!=asset['sha256']:raise ValueError('reference tool/library changed')
    resources=read(POLICY)['resources'];u=usage(read(Ledger().path)['entries']);later=cfg['later_work_reserved']
    count=len(cfg['labels']);wall=count*cfg['resources']['per_task_walltime_envelope_s']+cfg['support_walltime_envelope_s']
    if (u['synth']+count+later['synth']>resources['max_synthesis_calls']
        or u['grt']+count+later['grt']>resources['max_global_route_calls']
        or u['walltime_s']+wall+later['walltime_s']>resources['max_global_walltime_h']*3600
        or u['CPU_time_s']+4*wall+later['CPU_time_s']>resources['max_tool_CPU_time_h']*3600
        or shutil.disk_usage(folder.parent).free<count*cfg['resources']['storage_per_task_bytes']+later['storage_bytes']):
        raise ValueError('reference cohort and later work not funded')
    folder.mkdir(parents=True,exist_ok=False);atom=Path(proof['atom_path']).read_text();tasks=[]
    for key in cfg['labels']:
        s=spec(key);d=folder/'sources'/key;d.mkdir(parents=True);rtl=d/'input.sv';rtl.write_text(source(s,atom))
        if sha(rtl)!=proof['RTL_sources'][key]:raise ValueError('reference RTL differs from software proof')
        contract=d/'contract.json';exclusive(contract,{'version':'reference-shell-contract-v1','spec':s,'protocol_sha256':sha(CONFIG),
            'source_role':'microbenchmark_reference_only','model_fit_allowed':False,'native_capture_mode':'previous_launch_valid','external_capture_mode':'unconditional'})
        tasks.append({'id':key,'platform':'asap7','top':'ModelBundle','period_ps':cfg['SDC_ps'],'abc_target_ps':cfg['ABC_ps'],
            'rtl':str(rtl.resolve()),'rtl_sha256':sha(rtl),'contract':str(contract.resolve()),'contract_sha256':sha(contract),
            'profile_sha256':p['profile_sha256'],'data_role':'microbenchmark_reference_only'})
    names=['model_reference_collection.py','model_reference_samples.py','model_reference_labels.py','reference.py',
        'backend.py','platforms.py','processes.py','budget.py','sdc.py','model_collection.py','model_samples.py',
        'model_m2_mux_collection.py','model_m2_evaluate.py','model_m2_live_cec_v3.py','model_m2_cec.py','model_m2_aig.py','model_m2_state.py']
    paths=[Path(__file__).with_name(n) for n in names]+[CONFIG,POLICY,ASSET]
    paths+=sorted(x for x in Path(__file__).with_name('backend').iterdir() if x.is_file())
    paths+=[ROOT/name for name in proof['producer_sha256']]+[ROOT/name for name in guards['producer_sha256']]
    hashes={}
    for path in paths:
        name=str(path.relative_to(ROOT));dst=folder/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst);hashes[name]=sha(path)
    shutil.copy2(software,folder/'software-proof.json');shutil.copy2(readers,folder/'reader-proof.json')
    exclusive(folder/'admission.json',{'version':'asap7-reference-admission-v1','id':folder.name,'tasks':tasks,
        'sources':hashes,'protocol_sha256':sha(CONFIG),'policy_sha256':sha(POLICY),
        'software_proof_path':str(software),'software_proof_sha256':sha(software),'reader_proof_path':str(readers),'reader_proof_sha256':sha(readers),
        'physical_tools':parent['tools'],'libraries':parent['libraries'],'Liberty_pin_table':str(software.parent/'liberty-pin-classes.json'),
        'Liberty_pin_table_sha256':sha(software.parent/'liberty-pin-classes.json'),
        'measurement_static_identity_sha256':measurement_identity(parent),'capacity_pilots':cfg['capacity_pilots'],
        'resource_plan':{'tasks':count,'synth_calls':count,'grt_calls':count,'walltime_envelope_s':wall,'CPU_envelope_s':4*wall,
            'storage_bytes':count*cfg['resources']['storage_per_task_bytes'],'later_work_reserved':later},
        'native_and_unconditional_external_capture_separate':True,'model_fit_allowed':False,
        'formal_PPA_read':False,'automatic_retries':0,'numeric_target_freeze_automatic':False})
    progress_write(folder,{'phase':'admitted','active':[],'completed':[],'waiting':cfg['labels'],'errors':[],'capacity_qualified':False})
    print(json.dumps({'status':'reference_cohort_admitted','tasks':count,'capacity_pilots':cfg['capacity_pilots'],
        'walltime_envelope_s':wall,'CPU_envelope_s':4*wall,'model_fit_allowed':False}),flush=True)


def verify(folder):
    from .platforms import profile
    a=read(folder/'admission.json');cfg=read(CONFIG)
    if (a['version']!='asap7-reference-admission-v1' or a['protocol_sha256']!=sha(CONFIG) or a['policy_sha256']!=sha(POLICY)
        or a['model_fit_allowed'] or a['numeric_target_freeze_automatic'] or [t['id'] for t in a['tasks']]!=cfg['labels']):
        raise ValueError('reference admission scope changed')
    for name,h in a['sources'].items():
        if sha(ROOT/name)!=h or sha(folder/'source'/name)!=h:raise ValueError('reference producer changed: '+name)
    for path,key in [(a['software_proof_path'],'software_proof_sha256'),(a['reader_proof_path'],'reader_proof_sha256'),(a['Liberty_pin_table'],'Liberty_pin_table_sha256')]:
        if sha(path)!=a[key]:raise ValueError('reference preflight changed')
    for t in a['tasks']:
        if sha(t['rtl'])!=t['rtl_sha256'] or sha(t['contract'])!=t['contract_sha256'] or t['period_ps']!=cfg['SDC_ps'] or t['abc_target_ps']!=1500:
            raise ValueError('reference task changed')
        if profile('asap7')['profile_sha256']!=t['profile_sha256']:raise ValueError('reference platform profile changed')
    return a


class ReferenceLedger(Ledger):
    def __init__(self,folder,task):super().__init__();self.folder=folder;self.task=task
    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a=verify(self.folder)
        if threads!=4 or self.task not in a['tasks']:raise ValueError('unregistered reference leaf')
        if self.task['id'] not in a['capacity_pilots']:
            proof=read(self.folder/'capacity-proof.json')
            if proof['status']!='passed' or proof['admission_sha256']!=sha(self.folder/'admission.json') or {r['id'] for r in proof['runs']}!=set(a['capacity_pilots']):
                raise ValueError('reference capacity gate not satisfied')
            for row in proof['runs']:
                path=self.folder/'runs'/row['id']/'manifest.json'
                if sha(path)!=row['manifest_sha256'] or read(path)['status']!='completed':raise ValueError('reference capacity pilot changed')
        return super().reserve(stage,timeout_s,threads,purpose,command,output,context={**(context or {}),
            'target_platform':'asap7','admission_id':a['id'],'task_id':self.task['id'],
            'admission_sha256':sha(self.folder/'admission.json'),'model_version':'asap7-reference-cohort-v1'})


def run_task(folder,t):
    from .backend import _evaluate,stage_metrics,verify_orfs_area
    from .model_m2_mux_collection import render_cts
    from .model_m2_live_cec_v3 import verify_proof
    from .model_m2_evaluate import measurement_identity
    from .platforms import profile,verify_wire_readback
    from .processes import run_command
    from .sdc import verify_sdc,rtl_ports
    from .model_reference_labels import partition,labels
    a=verify(folder);cfg=read(CONFIG);out=folder/'runs'/t['id'];ledger=ReferenceLedger(folder,t)
    context={'target_platform':'asap7','admission_id':a['id'],'task_id':t['id']}
    env=os.environ.copy();env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',YOSYS_MAX_THREADS='4',
        PYTHONDONTWRITEBYTECODE='1',QT_QPA_PLATFORM='offscreen',VULSIM_REFERENCE_REQUESTS=str(out/'reference-requests.tcl'))
    with ledger.job(context):
        args=SimpleNamespace(out=out,platform='asap7',threads=4,stage='synth',memory_limit_mib=8192,
            period_ps=t['period_ps'],period_role='resource_trial',abc_target_ps=1500,io_delay_max_ps=None,
            budget_purpose='characterization',admission_id=a['id'],task_id=t['id'],sample_contract=None,
            admission=None,resume_synth_from=None,orfs=ORFS,rtl=Path(t['rtl']),top='ModelBundle',
            synth_timeout_s=300,route_timeout_s=1200,selection_freeze=None)
        _evaluate(args,ledger);m=read(out/'manifest.json')
        if m['status']!='completed':raise RuntimeError('reference synthesis failed: '+str(m.get('failure_reason')))
        base=next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'))
        m.update(status='running',stages_requested='grt',reference_admission_sha256=sha(folder/'admission.json'),data_role='microbenchmark_reference_only')
        def save():write(out/'manifest.json',m)
        def execute(cmd,name,timeout,stage=None):
            m['active_stage']=name;r=ledger.reserve(stage,timeout,4,'reference_calibration',cmd,out/name,context=context)
            m['active_reservation']=r['id'];save();c=run_command(cmd,out,name,timeout,env,8192,cpu_limit_s=r['CPU_time_s']);ledger.finish(r,c)
            c['budget_reservation_id']=r['id'];m['commands'].append(c);save()
            if c['exit_code']:raise RuntimeError(name+' failed; timeout='+str(c['timed_out']))
        try:
            s=spec(t['id']);shutil.copy2(t['contract'],out/'reference-contract.json');(out/'reference-requests.tcl').write_text(render_requests(s))
            snapshot=out/'reference-snapshot.tcl';original=(ROOT/'experiments/arithmetic_dse/backend/snapshot.tcl').read_text()
            original=original.replace('source [file join [file dirname [info script]] rc_readback.tcl]','source {'+str(ROOT/'experiments/arithmetic_dse/backend/rc_readback.tcl')+'}')
            original=original.replace('source [file join [file dirname [info script]] model_labels.tcl]','source {'+str(ASSET)+'}')
            snapshot.write_text(original)
            wrapper=out/'live-cec.py';wrapper.write_text('import sys\nsys.path.insert(0,'+repr(str(ROOT))+')\nfrom experiments.arithmetic_dse.model_m2_live_cec_v3 import main\nmain()\n')
            request=out/'live-cec-request.json';write(request,{'libraries':m['libraries'],'admission_sha256':sha(folder/'admission.json'),'collection_plan_sha256':sha(folder/'admission.json')})
            cts=out/'flow-scripts/cts.tcl';cts.unlink();cts.write_text(render_cts((ORFS/'flow/scripts/cts.tcl').read_text(),wrapper,request,out/'logs'/SUFFIX/'structural_cec'))
            m['files_sha256'].update({str(p):sha(p) for p in [snapshot,wrapper,request,cts,out/'reference-requests.tcl',out/'reference-contract.json',ASSET]})
            if measurement_identity(m)!=a['measurement_static_identity_sha256']:raise ValueError('reference physical identity differs')
            for asset in [*m['tools'].values(),*m['libraries']]:
                if sha(asset['path'])!=asset['sha256']:raise ValueError('reference tool or library changed')
            pin_cells=read(a['Liberty_pin_table']);p=profile('asap7');basic_cells=read(out/'liberty_cells.json')['cells'];m['metrics']=[]
            for stage in ('synth','grt'):
                if stage=='grt':execute(base+['grt'],'grt',1200,'grt')
                stem={'synth':'1_synth','grt':'5_1_grt'}[stage]
                execute(base+['run','RUN_SCRIPT='+str(snapshot),'RUN_LOG_NAME_STEM=reference_'+stage,
                    'VULSIM_EVAL_STAGE='+stage,'VULSIM_EVAL_DB='+stem+'.odb','VULSIM_EVAL_SDC='+stem+'.sdc'],'reference-'+stage+'-snapshot',120)
                reports=out/'reports'/SUFFIX;g=stage_metrics(reports,stage,basic_cells,t['period_ps'],selected=p);prefix=reports/('vulsim_'+stage)
                ownership,instances,_=partition(prefix,pin_cells,p,expected={name:s[name+'_bits'] for name in ('input_service','native_state','external_state')})
                write(out/('reference-'+stage+'-ownership.json'),ownership)
                if not abs(g['cell_area_um2']-ownership['total_area_um2'])<=1e-6:raise ValueError('reference exhaustive area sum differs')
                g['reference_paths']=labels(prefix,s,t['period_ps'],g['raw_report_units']['time']['to_ps'],pin_cells,instances)
                g['reference_owner_area_um2']=ownership['owner_area_um2'];g['reference_owner_FF_bits']=ownership['owner_FF_bits']
                g['reference_ownership_sha256']=sha(out/('reference-'+stage+'-ownership.json'))
                rc=verify_wire_readback(Path(str(prefix)+'_layer_rc.tsv'),p)
                if rc is not None:g['wire_RC_readback']=rc
                m['sdc_contracts'][stage]=verify_sdc((out/'results'/SUFFIX/(stem+'.sdc')).read_text(),p,t['period_ps'],rtl_ports((out/'input.sv').read_text(),'ModelBundle'))
                native=read(out/'logs'/SUFFIX/(stem+'.json'))[('synth' if stage=='synth' else 'globalroute')+'__design__instance__area__stdcell']
                g['orfs_area_crosscheck']=verify_orfs_area(g['cell_area_um2'],native)
                if not g['timing_coverage_complete']:raise ValueError('reference unconstrained paths')
                m['metrics'].append(g);save()
            verify_proof(out/'logs'/SUFFIX/'structural_cec/proof.json',out/'results'/SUFFIX/'4_before_rsz_lec.v',out/'results'/SUFFIX/'4_after_rsz_lec.v')
            m['status']='completed';write(out/'metrics.json',m['metrics'])
        except Exception as error:m.update(status='failed',failure_stage=m.get('active_stage','reference_preflight'),failure_reason=str(error))
        finally:
            m['finished_at']=datetime.now(timezone.utc).isoformat();m['evidence_sha256']={str(path.relative_to(out)):sha(path) for name in ('logs','reports','results') for path in (out/name).rglob('*') if path.is_file()};save()
        print(json.dumps({'task':t['id'],'status':m['status'],'reason':m.get('failure_reason')}),flush=True)
        if m['status']!='completed':raise RuntimeError(t['id']+': '+m['failure_reason'])
    return t['id']


def run(folder):
    a=verify(folder);indexed={t['id']:t for t in a['tasks']}
    with (folder/'advance.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if any((folder/'runs'/key).exists() for key in indexed):raise ValueError('preserve reference attempts; explicit continuation required')
        waiting=list(indexed);active={};completed=[];errors=[];capacity=False
        with ThreadPoolExecutor(max_workers=4) as pool:
            while waiting or active:
                if not capacity and set(a['capacity_pilots'])<=set(completed):
                    rows=[]
                    for key in a['capacity_pilots']:
                        path=folder/'runs'/key/'manifest.json';m=read(path)
                        rows.append({'id':key,'manifest_sha256':sha(path),'peak_RSS_MiB':max(c['sampled_process_tree_peak_rss_KiB'] for c in m['commands'])/1024})
                    exclusive(folder/'capacity-proof.json',{'status':'passed','admission_sha256':sha(folder/'admission.json'),'scope':read(CONFIG)['capacity_scope'],'runs':rows});capacity=True
                while waiting and len(active)<4 and not errors:
                    ready=next((key for key in waiting if capacity or key in a['capacity_pilots']),None)
                    if ready is None:break
                    waiting.remove(ready);active[pool.submit(run_task,folder,indexed[ready])]=ready
                progress_write(folder,{'phase':'reference_collecting','active':list(active.values()),'completed':completed,'waiting':waiting,'errors':errors,'capacity_qualified':capacity})
                if not active:break
                done,_=wait(active,timeout=1,return_when=FIRST_COMPLETED)
                for future in done:
                    key=active.pop(future)
                    try:completed.append(future.result())
                    except Exception as error:errors.append({'task_id':key,'reason':str(error)})
        progress_write(folder,{'phase':'stopped_on_error' if errors else 'reference_collection_complete','active':[],
            'completed':completed,'waiting':waiting,'errors':errors,'capacity_qualified':capacity})
        if errors:raise RuntimeError(str(errors))


def status(folder):
    a=read(folder/'admission.json');progress=read(folder/'progress.json');counts=Counter()
    print(datetime.now().astimezone().isoformat(timespec='seconds'));print('参考采集：'+progress['phase'])
    for t in a['tasks']:
        path=folder/'runs'/t['id']/'manifest.json';m=read(path) if path.exists() else {};counts[m.get('status','not_started')]+=1
        if m.get('status')=='running':print('任务：',t['id'],'阶段：',m.get('active_stage'))
    print(f'完成{counts["completed"]}/{len(a["tasks"])}；{dict(counts)}；容量准入：{progress["capacity_qualified"]}')
    print('最多4任务×4线程／8GiB；参考角色，不拟合、不启动独立模型测试、不自动冻结目标。');print('错误：',progress['errors'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','verify','run','status'));p.add_argument('--folder',type=Path,required=True)
    p.add_argument('--software-proof',type=Path);p.add_argument('--reader-proof',type=Path);a=p.parse_args();folder=a.folder.resolve()
    if a.action=='prepare':prepare(folder,a.software_proof.resolve(),a.reader_proof.resolve())
    elif a.action=='run':run(folder)
    elif a.action=='status':status(folder)
    else:verify(folder);print('reference admission verified')
