"""Finite not-training physical diagnosis for new fast sampling interfaces.

Each physical leaf is bound to an explicit source/clock/admission and the shared
ledger. This does not launch the training cohort or qualify an operator model.
"""
import argparse
import copy
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
from datetime import datetime,timezone
import fcntl
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace,FunctionType

from .budget import Ledger,POLICY,usage
from .model_fast_preflight import read,write,sha
from . import model_fast_measurement as measurement
from . import sdc_storage_v3
from . import model_fast_sdc

ROOT=Path(__file__).resolve().parents[2]
CONFIG=Path(__file__).with_name('configs')/'model_fast_probe_v1.json'
ORFS=Path('/home/zyrv/OpenROAD-flow-scripts')
SUFFIX=Path('asap7/arithmetic_probe/base')
ASSET=Path(__file__).with_name('reference_assets')/'snapshot.tcl'
SEED=ROOT/'build/step7-reference-20261106/collection-v3/runs/add_u64/manifest.json'


def save_progress(folder,value):
    with tempfile.NamedTemporaryFile('w',dir=folder,delete=False,prefix='.fast-progress-') as f:
        json.dump(value,f,indent=2);f.write('\n');name=f.name
    os.replace(name,folder/'progress.json')


def prepare(folder,proof_path,parent=None):
    from .platforms import profile
    from .model_reference_labels import liberty
    from .model_m2_evaluate import measurement_identity
    cfg=read(CONFIG);proof=read(proof_path);seed=read(SEED);selected=profile('asap7')
    if (proof['status']!='passed' or proof['protocol_sha256']!=sha(CONFIG) or proof['reader_status']!='passed'
            or len(proof['negative_checks'])<7 or proof['source_role']!='not_training' or proof['PPA_calls']):
        raise ValueError('complete measurement software and reader proof required')
    for name,h in proof['producer_sha256'].items():
        if sha(ROOT/name)!=h:raise ValueError('measurement software producer changed')
    for asset in [*seed['tools'].values(),*seed['libraries']]:
        if sha(asset['path'])!=asset['sha256']:raise ValueError('registered physical tool/library changed')
    cells=read(SEED.parent/'liberty_cells.json')['cells'];pins=liberty(seed['libraries'],cells)
    old_pins=ROOT/'build/step7-reference-20261106/preflight-v4/software/liberty-pin-classes.json'
    if pins!=read(old_pins) or sha(old_pins)!=proof['Liberty_pin_table_sha256']:
        raise ValueError('actual Liberty FF/pin/function table differs from software fixture')
    count=len(cfg['probes'])*len(cfg['SDC_ps']);wall=count*cfg['resources']['per_task_walltime_envelope_s']+cfg['resources']['support_walltime_envelope_s']
    ledger=Ledger()
    with ledger._transaction() as state:
        ledger._live_jobs(state);u=usage(state['entries'])
    limits=read(POLICY)['resources'];later=cfg['later_work_reserved']
    if (u['synth']+count+later['synth']>limits['max_synthesis_calls']
            or u['grt']+count+later['grt']>limits['max_global_route_calls']
            or u['walltime_s']+wall+later['walltime_s']>limits['max_global_walltime_h']*3600
            or u['CPU_time_s']+4*wall+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600
            or shutil.disk_usage(folder.parent).free<count*cfg['resources']['storage_per_task_bytes']+later['storage_bytes']):
        raise ValueError('finite measurement probes and explicitly reserved later work not funded')
    lineage=None;inherited={}
    if parent:
        old=read(parent/'admission.json');progress=read(parent/'progress.json')
        if progress['phase']!='stopped_on_error' or progress['active'] or len(progress['errors'])!=1:
            raise ValueError('one settled metadata-only predecessor stop required')
        for name,h in old['sources'].items():
            if sha(parent/'source'/name)!=h:raise ValueError('predecessor frozen producer changed')
        records=[(name,True) for name in progress['completed']]+[(e['task_id'],False) for e in progress['errors']]
        for name,completed in records:
            previous_task=next(t for t in old['tasks'] if t['id']==name)
            path=Path(previous_task['inherit_completed']['directory']) if previous_task.get('inherit_completed') else parent/'runs'/name
            before=read(path/'manifest.json')
            if not completed:
                alias=(before.get('failure_stage')=='fast-synth-snapshot' and 'reference boundary missing: data0' in (path/'fast-synth-snapshot.log').read_text())
                scalar=before.get('failure_reason')=='SDC IO coverage mismatch (includes reset/valid/data)'
                if before['status']!='failed' or not (alias or scalar):raise ValueError('not a registered nonphysical metadata failure')
                if not any(c['log'].endswith('/synth.log') and c['exit_code']==0 for c in before['commands']) or any(c['log'].endswith('/grt.log') for c in before['commands']):
                    raise ValueError('exact successful pre-grt synthesis checkpoint required')
            elif before['status']!='completed':raise ValueError('invalid completed predecessor point')
            entries={e['id']:e for e in read(Ledger().path)['entries']}
            for command in before['commands']:
                e=entries[command['budget_reservation_id']]
                if e['command']!=command['command'] or e['status']!=('failed' if command['exit_code'] else 'completed') or e.get('admission_sha256')!=sha(parent/'admission.json'):
                    raise ValueError('predecessor paid leaf ancestry differs')
            for relative,h in before.get('evidence_sha256',{}).items():
                if sha(path/relative)!=h:raise ValueError('predecessor synthesis evidence changed')
            files={str(p.relative_to(path)):sha(p) for p in [path/'input.sv',path/'logs'/SUFFIX/'1_synth.json',*(path/'results'/SUFFIX).iterdir()] if p.is_file()}
            inherited[name]=dict(directory=str(path),manifest_sha256=sha(path/'manifest.json'),
                parent_admission_sha256=sha(parent/'admission.json'),completed=completed,files_sha256=files)
        lineage=dict(admission=str(parent/'admission.json'),admission_sha256=sha(parent/'admission.json'),
            progress_sha256=sha(parent/'progress.json'),reason='declared register/port alias reader successor; RTL/SDC/ABC unchanged; no re-synthesis')
    folder.mkdir(parents=True,exist_ok=False);tasks=[]
    for row in cfg['probes']:
        spec=row['spec'];d=folder/'sources'/row['id'];d.mkdir(parents=True);rtl=d/'input.sv';rtl.write_text(measurement.source(spec))
        if sha(rtl)!=proof['RTL_sources'][row['id']]:raise ValueError('physical source differs from software preflight')
        contract=d/'contract.json';write(contract,dict(version=measurement.VERSION,spec=spec,source_role='not_training',model_fit_allowed=False,
            geometry=proof['generic_geometry'][row['id']],protocol_sha256=sha(CONFIG)))
        for i,t in enumerate(cfg['SDC_ps']):
            task=dict(id=row['id']+'-t'+str(i),source_group=row['id'],
            period_ps=t,abc_target_ps=cfg['ABC_ps'],platform='asap7',profile_sha256=selected['profile_sha256'],
            spec=spec,geometry=proof['generic_geometry'][row['id']],rtl=str(rtl),rtl_sha256=sha(rtl),
            contract=str(contract),contract_sha256=sha(contract),source_role='not_training')
            if task['id'] in inherited:
                previous=next(x for x in old['tasks'] if x['id']==task['id'])
                if any(task[k]!=previous[k] for k in ('period_ps','abc_target_ps','rtl_sha256','contract_sha256','geometry')):
                    raise ValueError('synthesis continuation changed semantic/physical task')
                task['inherit_completed' if inherited[task['id']]['completed'] else 'inherit_synth']=inherited[task['id']]
            tasks.append(task)
    paths=[Path(__file__),Path(measurement.__file__),Path(measurement.samples.__file__),CONFIG,POLICY,ASSET,Path(sdc_storage_v3.__file__),Path(model_fast_sdc.__file__)]
    for name in ('backend.py','platforms.py','processes.py','budget.py','sdc.py','model_collection.py','model_samples.py',
                 'model_reference_labels.py','model_reference_labels_v2.py','model_m2_mux_collection.py','model_m2_collection.py',
                 'model_m2_live_cec_v3.py','model_m2_cec.py','model_m2_aig.py','model_m2_state.py','model_m2_evaluate.py'):
        paths.append(Path(__file__).with_name(name))
    paths += sorted(p for p in Path(__file__).with_name('backend').iterdir() if p.is_file())
    paths += [ROOT/name for name in proof['producer_sha256']]
    sources={}
    for p in paths:
        name=str(p.relative_to(ROOT));target=folder/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target);sources[name]=sha(p)
    shutil.copy2(proof_path,folder/'software-proof.json');write(folder/'liberty-pins.json',pins)
    write(folder/'admission.json',dict(version='arithmetic-fast-measurement-admission-v1',id=folder.name,tasks=tasks,
        sources=sources,protocol_sha256=sha(CONFIG),policy_sha256=sha(POLICY),
        software_proof_sha256=sha(folder/'software-proof.json'),pin_table_sha256=sha(folder/'liberty-pins.json'),
        physical_tools=seed['tools'],libraries=seed['libraries'],measurement_static_identity_sha256=measurement_identity(seed),
        capacity_first=cfg['capacity_first'],model_fit_allowed=False,independent_test_allowed=False,automatic_retries=0,
        reader_version=getattr(measurement,'READER_VERSION',measurement.VERSION),predecessor=lineage,
        source_role='not_training',resource_plan=dict(tasks=count,synth=count,grt=count,walltime_s=wall,CPU_time_s=4*wall,
            storage_bytes=count*cfg['resources']['storage_per_task_bytes'],later_work_reserved=later),full_D_ready=False))
    save_progress(folder,dict(phase='admitted',completed=[],active=[],waiting=[t['id'] for t in tasks],errors=[],capacity_qualified=False))
    print(json.dumps(dict(status='admitted',tasks=count,walltime_envelope_s=wall,source_role='not_training',model_fit_allowed=False)),flush=True)


def verify(folder):
    a=read(folder/'admission.json');cfg=read(CONFIG)
    if (a['version']!='arithmetic-fast-measurement-admission-v1' or a['protocol_sha256']!=sha(CONFIG)
            or a['policy_sha256']!=sha(POLICY) or a['model_fit_allowed'] or a['independent_test_allowed']
            or a['source_role']!='not_training' or a['automatic_retries']):raise ValueError('measurement admission scope changed')
    for name,h in a['sources'].items():
        if sha(ROOT/name)!=h or sha(folder/'source'/name)!=h:raise ValueError('measurement producer changed: '+name)
    for asset in [*a['physical_tools'].values(),*a['libraries']]:
        if sha(asset['path'])!=asset['sha256']:raise ValueError('measurement tool/library changed')
    if sha(folder/'software-proof.json')!=a['software_proof_sha256'] or sha(folder/'liberty-pins.json')!=a['pin_table_sha256']:raise ValueError('measurement software/pin proof changed')
    if a.get('predecessor'):
        ref=a['predecessor'];parent=Path(ref['admission']).parent
        if sha(ref['admission'])!=ref['admission_sha256'] or sha(parent/'progress.json')!=ref['progress_sha256']:raise ValueError('measurement predecessor changed')
    for task in a['tasks']:
        if task.get('inherit_synth') or task.get('inherit_completed'):
            ref=task.get('inherit_synth') or task['inherit_completed']
            if sha(Path(ref['directory'])/'manifest.json')!=ref['manifest_sha256']:raise ValueError('saved synthesis checkpoint identity changed')
            if any(sha(Path(ref['directory'])/name)!=h for name,h in ref.get('files_sha256',{}).items()):raise ValueError('preserved physical checkpoint changed')
    expected=[(p['id']+'-t'+str(i),p['spec'],t) for p in cfg['probes'] for i,t in enumerate(cfg['SDC_ps'])]
    if len(a['tasks'])!=len(expected):raise ValueError('incomplete probe task list')
    for task,(name,spec,t) in zip(a['tasks'],expected,strict=True):
        if (task['id']!=name or task['spec']!=spec or task['period_ps']!=t or task['abc_target_ps']!=cfg['ABC_ps']
                or sha(task['rtl'])!=task['rtl_sha256'] or sha(task['contract'])!=task['contract_sha256']
                or task['source_role']!='not_training'):raise ValueError('measurement task source/clock/role changed')
    return a


class FastLedger(Ledger):
    def __init__(self,folder,task):super().__init__();self.folder=folder;self.task=task
    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a=verify(self.folder);cfg=read(CONFIG)
        if self.task not in a['tasks'] or threads!=4 or stage not in (None,'synth','grt'):
            raise ValueError('unregistered measurement task/role/threads/stage')
        if stage:
            limit=cfg['resources']['synth_timeout_s' if stage=='synth' else 'grt_timeout_s']
            prior=[e for e in read(self.path)['entries'] if e.get('admission_id')==a['id'] and e.get('task_id')==self.task['id'] and e['stage']==stage]
            if timeout_s>limit or prior or self.task.get('inherit_completed') or (stage=='synth' and self.task.get('inherit_synth')):raise ValueError('measurement timeout/call cap or no-retry guard')
        if self.task['id'] not in a['capacity_first']:
            proof=read(self.folder/'capacity-proof.json')
            if proof['status']!='passed' or proof['admission_sha256']!=sha(self.folder/'admission.json'):raise ValueError('finite-cohort capacity gate not met')
            for row in proof['runs']:
                if sha(Path(row['directory'])/'manifest.json')!=row['manifest_sha256']:raise ValueError('capacity point changed')
        return super().reserve(stage,timeout_s,threads,purpose,command,output,context={**(context or {}),
            'target_platform':'asap7','admission_id':a['id'],'task_id':self.task['id'],
            'admission_sha256':sha(self.folder/'admission.json'),'model_version':measurement.VERSION})


def seed_synth(out,task):
    ref=task['inherit_synth'];previous=Path(ref['directory']);old=read(previous/'manifest.json')
    if sha(previous/'manifest.json')!=ref['manifest_sha256']:raise ValueError('inherited synthesis manifest changed')
    if any(sha(previous/name)!=h for name,h in ref.get('files_sha256',{}).items()):raise ValueError('saved synthesis files changed')
    out.mkdir(parents=True,exist_ok=False)
    for p in previous.iterdir():
        if p.is_file() and p.name!='manifest.json' and not p.name.endswith(('.log','.command.json','.resources.txt')):shutil.copy2(p,out/p.name)
    for name in ('source','flow-scripts'):shutil.copytree(previous/name,out/name,symlinks=True)
    results=out/'results'/SUFFIX;results.mkdir(parents=True)
    for p in (previous/'results'/SUFFIX).iterdir():
        if p.is_file():shutil.copy2(p,results/p.name)
    logs=out/'logs'/SUFFIX;logs.mkdir(parents=True);shutil.copy2(previous/'logs'/SUFFIX/'1_synth.json',logs/'1_synth.json')
    config=out/'config.mk';config.write_text(config.read_text().replace(str(previous),str(out)))
    base=next(c['command'][:-1] for c in old['commands'] if c['log'].endswith('/synth.log'))
    base=[x.replace(str(previous),str(out)) for x in base if not x.startswith('--assume-old=')]
    base+=['--assume-old='+str(p) for p in (config,out/'input.sv',*results.glob('1*')) if p.is_file()]
    guard=out/'resume-synthesis-lock.mk'
    guarded=[str(results/'1_1_yosys_canonicalize.rtlil'),str(results/'1_2_yosys.v'),'do-yosys','do-yosys-canonicalize']
    guard.write_text('\n'.join(name+':\n\t$(error paid synthesis checkpoint must not be rebuilt)' for name in guarded)+'\n')
    base+=['--file='+str(guard)]
    result=copy.deepcopy(old);result.update(status='completed',commands=[],metrics=[],continuation_base_command=base,
        checkpoint_reuse=dict(mode='exact_paid_synth_ODB_SDC_netlist_and_native_JSON',**ref,new_Yosys_ABC_calls=0,
            synthesis_guard=str(guard),synthesis_guard_sha256=sha(guard),
            copied_files_sha256={p.name:sha(p) for p in results.iterdir() if p.is_file()}))
    for k in ('failure_reason','failure_stage','finished_at','evidence_sha256','active_reservation'):result.pop(k,None)
    write(out/'manifest.json',result)


def run_task(folder,t):
    from . import backend
    from .platforms import profile,verify_wire_readback
    from .model_m2_mux_collection import render_cts
    from .model_m2_live_cec_v3 import verify_proof
    from .model_m2_evaluate import measurement_identity
    from .model_fast_sdc import rtl_ports
    from .processes import run_command
    a=verify(folder);cfg=read(CONFIG);out=folder/'runs'/t['id'];ledger=FastLedger(folder,t)
    ctx=dict(target_platform='asap7',admission_id=a['id'],task_id=t['id'])
    env=os.environ.copy();env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',YOSYS_MAX_THREADS='4',PYTHONDONTWRITEBYTECODE='1',QT_QPA_PLATFORM='offscreen')
    # Local function namespace: no global SDC or process-environment mutation in parallel workers.
    namespace=dict(backend._evaluate.__globals__);namespace.update(verify_sdc=model_fast_sdc.verify_sdc,rtl_ports=model_fast_sdc.rtl_ports,SDC_CONTRACT_VERSION=model_fast_sdc.VERSION,
        os=SimpleNamespace(environ=env))
    evaluate=FunctionType(backend._evaluate.__code__,namespace,closure=backend._evaluate.__closure__)
    with ledger.job(ctx):
        args=SimpleNamespace(out=out,platform='asap7',threads=4,stage='synth',memory_limit_mib=8192,
            period_ps=t['period_ps'],period_role='resource_trial',abc_target_ps=1500,io_delay_max_ps=None,
            budget_purpose='characterization',admission_id=a['id'],task_id=t['id'],sample_contract=None,
            admission=None,resume_synth_from=None,orfs=ORFS,rtl=Path(t['rtl']),top='ModelBundle',synth_timeout_s=300,route_timeout_s=1200,selection_freeze=None)
        if t.get('inherit_synth'):seed_synth(out,t)
        else:evaluate(args,ledger)
        manifest=out/'manifest.json';m=read(manifest)
        if m['status']!='completed':raise RuntimeError(t['id']+' synth failed: '+str(m.get('failure_reason')))
        base=m.get('continuation_base_command') or next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'))
        m.update(status='running',stages_requested='grt',fast_measurement_admission_sha256=sha(folder/'admission.json'),
            admission_id=a['id'],task_id=t['id'],budget_job_id=ledger.job_id,
            fast_measurement_sources=a['sources'],data_role='not_training',model_fit_allowed=False,
            SDC_execution_adapter=model_fast_sdc.VERSION,SDC_adapter_scope='this_worker_function_namespace_only')
        def save():write(manifest,m)
        def execute(cmd,name,timeout,stage=None):
            m['active_stage']=name;r=ledger.reserve(stage,timeout,4,'fast_measurement_diagnosis',cmd,out/name,context=ctx);m['active_reservation']=r['id'];save()
            record=run_command(cmd,out,name,timeout,env,8192,cpu_limit_s=r['CPU_time_s']);ledger.finish(r,record)
            m['commands'].append({**record,'budget_reservation_id':r['id']});save()
            if record['exit_code']:raise RuntimeError(name+' failed; see '+record['log'])
        try:
            shutil.copy2(t['contract'],out/'fast-contract.json');requests=out/'requests.tcl';requests.write_text(measurement.render_requests(t['spec']));env['VULSIM_REFERENCE_REQUESTS']=str(requests)
            snapshot=out/'fast-snapshot.tcl';text=(ROOT/'experiments/arithmetic_dse/backend/snapshot.tcl').read_text()
            for marker,replacement in [('source [file join [file dirname [info script]] rc_readback.tcl]','source {'+str(ROOT/'experiments/arithmetic_dse/backend/rc_readback.tcl')+'}'),
                ('source [file join [file dirname [info script]] model_labels.tcl]','source {'+str(ASSET)+'}')]:
                if text.count(marker)!=1:raise ValueError('unsupported pure-report snapshot insertion point')
                text=text.replace(marker,replacement)
            snapshot.write_text(text)
            wrapper=out/'live-cec.py';wrapper.write_text('import sys\nsys.path.insert(0,'+repr(str(ROOT))+')\nfrom experiments.arithmetic_dse.model_m2_live_cec_v3 import main\nmain()\n')
            request=out/'live-cec-request.json';write(request,dict(libraries=m['libraries'],admission_sha256=sha(folder/'admission.json'),collection_plan_sha256=sha(folder/'admission.json')))
            cts=out/'flow-scripts/cts.tcl';cts.unlink();cts.write_text(render_cts((ORFS/'flow/scripts/cts.tcl').read_text(),wrapper,request,out/'logs'/SUFFIX/'structural_cec'))
            m['files_sha256'].update({str(p):sha(p) for p in (snapshot,wrapper,request,cts,requests,ASSET,out/'fast-contract.json')})
            if measurement_identity(m)!=a['measurement_static_identity_sha256']:raise ValueError('probe physical execution identity differs from pinned profile')
            selected=profile('asap7');cells=read(out/'liberty_cells.json')['cells'];pins=read(folder/'liberty-pins.json');m['metrics']=[]
            for stage,stem in (('synth','1_synth'),('grt','5_1_grt')):
                if stage=='grt':
                    if t.get('inherit_synth'):
                        reuse=m['checkpoint_reuse']
                        if sha(reuse['synthesis_guard'])!=reuse['synthesis_guard_sha256']:raise ValueError('paid-synthesis guard changed')
                        if any(sha(out/'results'/SUFFIX/name)!=h for name,h in reuse['copied_files_sha256'].items()):raise ValueError('copied synthesis artifact changed')
                    execute(base+['grt'],'grt',1200,'grt')
                    if t.get('inherit_synth') and (out/'logs'/SUFFIX/'1_2_yosys.log').exists():raise ValueError('unexpected repeated Yosys log in inherited run')
                execute(base+['run','RUN_SCRIPT='+str(snapshot),'RUN_LOG_NAME_STEM=fast_'+stage,'VULSIM_EVAL_STAGE='+stage,
                    'VULSIM_EVAL_DB='+stem+'.odb','VULSIM_EVAL_SDC='+stem+'.sdc'],'fast-'+stage+'-snapshot',120)
                prefix=out/'reports'/SUFFIX/('vulsim_'+stage);g=backend.stage_metrics(out/'reports'/SUFFIX,stage,cells,t['period_ps'],selected=selected)
                observed=measurement.observations(prefix,t['spec'],t['period_ps'],g['raw_report_units']['time']['to_ps'],pins,selected,t['geometry'])
                write(out/('fast-'+stage+'-observations.json'),observed)
                if abs(g['cell_area_um2']-observed['ownership']['total_area_um2'])>1e-6:raise ValueError('fast measurement area partition incomplete')
                g.update(fast_measurement=observed,observation_sha256=sha(out/('fast-'+stage+'-observations.json')))
                rc=verify_wire_readback(Path(str(prefix)+'_layer_rc.tsv'),selected)
                if rc is not None:g['wire_RC_readback']=rc
                m['sdc_contracts'][stage]=sdc_storage_v3.verify_sdc((out/'results'/SUFFIX/(stem+'.sdc')).read_text(),selected,t['period_ps'],rtl_ports((out/'input.sv').read_text(),'ModelBundle'))
                native=read(out/'logs'/SUFFIX/(stem+'.json'))[('synth' if stage=='synth' else 'globalroute')+'__design__instance__area__stdcell'];g['orfs_area_crosscheck']=backend.verify_orfs_area(g['cell_area_um2'],native)
                if not g['timing_coverage_complete']:raise ValueError('fast measurement timing coverage incomplete')
                m['metrics'].append(g);save()
            verify_proof(out/'logs'/SUFFIX/'structural_cec/proof.json',out/'results'/SUFFIX/'4_before_rsz_lec.v',out/'results'/SUFFIX/'4_after_rsz_lec.v')
            m['status']='completed';write(out/'metrics.json',m['metrics'])
        except Exception as error:m.update(status='failed',failure_stage=m.get('active_stage','fast-readers'),failure_reason=str(error))
        finally:
            m['finished_at']=datetime.now(timezone.utc).isoformat();m['evidence_sha256']={str(p.relative_to(out)):sha(p) for name in ('reports','logs','results') for p in (out/name).rglob('*') if p.is_file()};save()
        if m['status']!='completed':raise RuntimeError(t['id']+': '+str(m.get('failure_reason')))
    print(json.dumps(dict(task=t['id'],status='completed',source_role='not_training')),flush=True);return t['id']


def run(folder):
    a=verify(folder);tasks={t['id']:t for t in a['tasks']}
    with (folder/'advance.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if any((folder/'runs'/key).exists() for key in tasks):raise ValueError('preserve attempts; explicit successor required')
        done=[name for name,t in tasks.items() if t.get('inherit_completed')]
        waiting=[name for name in tasks if name not in done];active={};errors=[];capacity=False
        with ThreadPoolExecutor(max_workers=4) as pool:
            while waiting or active:
                if not capacity and set(a['capacity_first'])<=set(done):
                    rows=[]
                    for k in a['capacity_first']:
                        directory=Path(tasks[k]['inherit_completed']['directory']) if tasks[k].get('inherit_completed') else folder/'runs'/k
                        rows.append(dict(task_id=k,directory=str(directory),manifest_sha256=sha(directory/'manifest.json')))
                    write(folder/'capacity-proof.json',dict(status='passed',admission_sha256=sha(folder/'admission.json'),scope='this finite diagnostic cohort only',runs=rows));capacity=True
                while waiting and len(active)<(4 if capacity else 1) and not errors:
                    name=next((k for k in a['capacity_first'] if k in waiting),None) if not capacity else waiting[0]
                    if name is None:break
                    waiting.remove(name);active[pool.submit(run_task,folder,tasks[name])]=name
                save_progress(folder,dict(phase='running',completed=done,active=list(active.values()),waiting=waiting,errors=errors,capacity_qualified=capacity))
                if not active:break
                finished,_=wait(active,return_when=FIRST_COMPLETED)
                for future in finished:
                    name=active.pop(future)
                    try:future.result();done.append(name)
                    except Exception as error:errors.append(dict(task_id=name,reason=str(error)))
        phase='stopped_on_error' if errors else 'diagnostic_collection_complete'
        save_progress(folder,dict(phase=phase,completed=done,active=[],waiting=waiting,errors=errors,capacity_qualified=capacity,
            automatic_fit_or_training=False,source_role='not_training'))
        print(json.dumps(dict(phase=phase,completed=len(done),errors=errors)),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','run','status','verify'));p.add_argument('--folder',type=Path,required=True);p.add_argument('--proof',type=Path);p.add_argument('--parent',type=Path);a=p.parse_args();folder=a.folder.resolve()
    if a.action=='prepare':
        if not a.proof:p.error('--proof required')
        prepare(folder,a.proof.resolve(),a.parent.resolve() if a.parent else None)
    elif a.action=='run':run(folder)
    elif a.action=='status':print(json.dumps(read(folder/'progress.json'),indent=2))
    else:verify(folder);print('finite fast measurement admission verified')


if __name__=='__main__':main()
