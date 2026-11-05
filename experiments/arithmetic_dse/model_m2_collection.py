"""Frozen four-thread prerequisite collection for the nine-case ASAP7 delivery."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
from datetime import datetime,timezone
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from .budget import Ledger,POLICY,usage
from .model_collection import sha,write
from .model_m2_samples import source
from .model_target_features import clock_request
from .platforms import profile

ROOT=Path(__file__).resolve().parents[2]
CONFIG=Path(__file__).with_name('configs')/'model_asap7_m2_primitives_v1.json'
RECOVERY=Path(__file__).with_name('configs')/'model_asap7_m2_timeout_recovery_v1.json'
RESUMPTION=Path(__file__).with_name('configs')/'model_asap7_m2_original_grid_resume_v1.json'
CONTINUATION=Path(__file__).with_name('configs')/'model_asap7_m2_phase_resume_v1.json'
PURPOSE='arithmetic_m2_model_collection'
SUFFIX=Path('asap7/arithmetic_probe/base')


def read(path):return json.loads(Path(path).read_text())
def run_directory(folder,t):return Path(t['inherited_run']['directory']) if t.get('inherited_run') else folder/'runs'/t['id']
def exclusive(path,value):
    if Path(path).exists():raise ValueError('preserve prior artifact: '+str(path))
    Path(path).parent.mkdir(parents=True,exist_ok=True);write(Path(path),value)


def sources():
    names=['model_m2_collection.py','model_m2_samples.py','model_m2_advance.py','model_collection.py','model_features.py',
           'model_samples.py','model_target_features.py','backend.py','platform_probe.py','budget.py',
           'processes.py','platforms.py','sdc.py','characterization.py','model_target_collection.py','model_mul_interval_fit.py','model_m2_phase_resume.py']
    return [Path(__file__).with_name(n) for n in names]+[CONFIG,RECOVERY,RESUMPTION,CONTINUATION,POLICY,ROOT/'rtlzz/testv2/arithmetic_m2_atom_export.cpp']+sorted(p for p in Path(__file__).with_name('backend').iterdir() if p.is_file())


def ancestor_plans(path):
    """Verify the original plans and producer snapshots without using live code."""
    result={}
    while path:
        path=Path(path).resolve();h=sha(path)
        if h in result:raise ValueError('cyclic M2 predecessor chain')
        p=read(path);result[h]=(path,p)
        for name,expected in p['sources'].items():
            if sha(Path(p['source_snapshot'])/name)!=expected:raise ValueError('changed predecessor producer snapshot')
        parent=p.get('predecessor')
        if parent and sha(parent['path'])!=parent['sha256']:raise ValueError('changed predecessor plan')
        path=parent['path'] if parent else None
    return result


def recovery_spec(predecessor,tasks,resume_original=False):
    contract=RESUMPTION if resume_original else RECOVERY
    cfg=read(contract);prior=read(predecessor);old_by_id={t['id']:t for t in prior['tasks']}
    if prior['id']!=cfg['parent_plan_id'] or cfg['route_timeout_s']!=3600 or cfg['attempts_per_failed_task']!=1:
        raise ValueError('unregistered M2 timeout recovery')
    attempts=[]
    for tid in cfg['failed_task_ids']:
        old=old_by_id[tid];d=run_directory(predecessor.parent,old);mp=d/'manifest.json';m=read(mp)
        grt=[c for c in m['commands'] if Path(c['log']).name=='grt.log']
        lec=d/'logs'/SUFFIX/'4_rsz_lec_check.log'
        interrupted=(len(grt)==1 and grt[0].get('cancelled_signal')==15 and not grt[0]['timed_out'])
        eligible=interrupted if resume_original else (len(grt)==1 and grt[0]['timed_out'])
        if (m['status']!='failed' or not eligible or grt[0]['memory_limit_exceeded']
                or grt[0]['cleanup']['remaining_live_pids'] or 'Starting solver' not in lec.read_text()
                or any(s in lec.read_text() for s in ('Circuits are IDENTICAL','Found difference'))):
            raise ValueError('M2 recovery requires the registered timeout or explicit cancellation evidence')
        attempts.append({'task_id':tid,'directory':str(d.resolve()),'manifest_sha256':sha(mp),
                         'lec_log_sha256':sha(lec),'previous_route_timeout_s':3600 if resume_original else 1200})
        if resume_original:
            audit=predecessor.parent/'obsolete-clock-cancellation-v1.json';record=read(audit)
            if record['job']['task_id']!=tid or record['job']['admission_id']!=m['admission_id']:
                raise ValueError('cancellation identity differs from registered resumption')
            attempts[-1]['cancellation_audit']={'path':str(audit.resolve()),'sha256':sha(audit)}
    expected={t['id'] for t in tasks if t['split'] in ('train','validation') and t['family']=='divrem'
              and t['width']==32 and t['period_ps'] in (4500,1500)}
    if set(cfg['extended_task_ids'])!=expected or not set(cfg['failed_task_ids'])<=expected:
        raise ValueError('M2 timeout extension must name only the six fitting DivRem32 tight targets')
    for t in tasks:
        old=old_by_id[t['id']]
        for key in ('rtl_sha256','sample_contract_sha256','split','period_ps','abc_target_ps','profile_sha256','mapping_source_task'):
            if t[key]!=old[key]:raise ValueError('M2 recovery changed measurement identity: '+key)
        if t['id'] in expected:t['route_timeout_s']=cfg['route_timeout_s']
    result={'path':str(contract.resolve()),'sha256':sha(contract),'failed_attempts':attempts,
            'priority_task_ids':cfg['failed_task_ids'],'reason':cfg['reason']}
    if resume_original:result['priority_wave_limit']=cfg['priority_wave_limit']
    return result


def prepare(folder,atom,predecessor=None,timeout_recovery=False,resume_original=False,phase_continuation=False):
    if sum((timeout_recovery,resume_original,phase_continuation))>1:raise ValueError('choose one explicit recovery contract')
    cfg=read(CONFIG);p=profile('asap7');folder.mkdir(parents=True,exist_ok=False)
    tasks=[];seen={};native=Path(atom).read_text()
    if 'module AtomicFp(' not in native and 'module AtomicFp (' not in native:raise ValueError('native binary32 atom required')
    shutil.copy2(atom,folder/'AtomicFp.sv')
    for split,banks in cfg['split_capture_banks'].items():
        for fanout in banks:
            for family,f in cfg['families'].items():
                for width in f['widths']:
                    group=f'{split}-F{fanout}-{family}-w{width}'
                    d=folder/'sources'/group;d.mkdir(parents=True)
                    text,labels=source(family,width,fanout,cfg,native)
                    (d/'input.sv').write_text(text)
                    exclusive(d/'contract.json',{'version':'arithmetic-model-labels-v1','split':split,'source_group':group,
                                                'protocol_sha256':sha(CONFIG),'labels':labels})
                    ins=sum(sum(l['input_widths']) for l in labels);caps=sum(l['capture_width']*fanout for l in labels)
                    if ins>cfg['resource_limits']['max_input_bits'] or caps>cfg['resource_limits']['max_capture_bits']:
                        raise ValueError('bundle exceeds preregistered capacity')
                    h=sha(d/'input.sv')
                    if h in seen and seen[h]!=split:raise ValueError('source crosses partitions')
                    seen[h]=split
                    targets=sorted({clock_request(v)['requested_period_ps'] for v in f['SDC_ps']},reverse=True)
                    for i,period in enumerate(targets):
                        tasks.append({'id':group+f'-t{i}','source_group':group,'split':split,'family':family,'width':width,
                                      'capture_fanout':fanout,'platform':'asap7','profile_sha256':p['profile_sha256'],
                                      'top':'ModelBundle','stage':'grt','period_ps':period,'abc_target_ps':1500,
                                      'rtl':str((d/'input.sv').resolve()),'rtl_sha256':h,
                                      'sample_contract':str((d/'contract.json').resolve()),'sample_contract_sha256':sha(d/'contract.json'),
                                      'samples':len(labels),'input_bits':ins,'capture_bits':caps,
                                      'mapping_source_task':group+'-t0' if i else None,
                                      'reference_role':'training_primitive_reference' if split=='train' and fanout==1 and i==0 else None})
    blocked=set()
    for old in [ROOT/'build/step7-target-load-20261103/asap7-parallel-v1/plan.json',
                ROOT/'build/step7-models-20261102/native-interval-asap7-v4/admission.json']:
        if old.exists():blocked.update(t['rtl_sha256'] for t in read(old)['tasks'] if t['split']=='test')
    if any(t['rtl_sha256'] in blocked for t in tasks):raise ValueError('consumed independent source reused')
    lineage=None
    if predecessor:
        ancestry=ancestor_plans(predecessor);prior=read(predecessor);old_by_id={t['id']:t for t in prior['tasks']};inherited=[]
        prior_waves={read(f)['id']:(f,read(f)) for f in (predecessor.parent/'waves').glob('*.json') if not f.name.endswith('.outcome.json')}
        for t in tasks:
            old=old_by_id[t['id']];d=run_directory(predecessor.parent,old);mp=d/'manifest.json'
            if not mp.exists() or read(mp)['status']!='completed':continue
            m=read(mp)
            if t['rtl_sha256']!=old['rtl_sha256'] or t['sample_contract_sha256']!=old['sample_contract_sha256']:
                raise ValueError('completed predecessor changed; cannot silently replace or repeat')
            if old.get('inherited_run'):
                origin=old['inherited_run'];wp=Path(origin['wave_path']);w=read(wp)
                if sha(mp)!=origin['manifest_sha256'] or sha(wp)!=origin['wave_sha256']:raise ValueError('changed inherited predecessor measurement')
            else:wp,w=prior_waves[m['admission_id']]
            if w['plan_sha256'] not in ancestry or sha(w['plan_path'])!=w['plan_sha256'] or t['id'] not in w['task_ids']:
                raise ValueError('unbound predecessor task')
            t['inherited_run']={'directory':str(d.resolve()),'manifest_sha256':sha(mp),'wave_path':str(wp.resolve()),'wave_sha256':sha(wp)}
            inherited.append(t['id'])
        lineage={'path':str(predecessor.resolve()),'sha256':sha(predecessor),'inherited_tasks':inherited,
                 'reason':'explicit successor; successful measurement identities preserved; failed attempts retained'}
    if (timeout_recovery or resume_original or phase_continuation) and not predecessor:raise ValueError('timeout recovery requires predecessor')
    if phase_continuation:
        from .model_m2_phase_resume import spec
        recovery=spec(predecessor,tasks)
    else:recovery=recovery_spec(predecessor,tasks,resume_original) if (timeout_recovery or resume_original) else None
    hashes={}
    for path in sources():
        name=path.relative_to(ROOT);saved=folder/'source'/name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,saved)
        hashes[str(name)]=sha(saved)
    exclusive(folder/'plan.json',{'version':'asap7-m2-primitives-plan-v1','id':folder.name,'purpose':PURPOSE,
                                  'protocol_sha256':sha(CONFIG),'policy_sha256':sha(POLICY),'sources':hashes,
                                  'source_snapshot':str((folder/'source').resolve()),'tasks':tasks,
                                  'native_fp_sha256':sha(atom),'blocked_old_test_source_hashes':sorted(blocked),
                                  'automatic_retries':0,'test_read_after_fit_only':True,'formal_36_PPA_authorized':False,'predecessor':lineage,
                                  'timeout_recovery':recovery})
    print(json.dumps({'tasks':len(tasks),'by_split':dict(Counter(t['split'] for t in tasks)),
                      'samples_by_split':{s:sum(t['samples'] for t in tasks if t['split']==s) for s in cfg['split_capture_banks']},
                      'inherited_tasks':lineage['inherited_tasks'] if lineage else []}))


def verify_plan(path):
    p=read(path)
    if p['purpose']!=PURPOSE or p['protocol_sha256']!=sha(CONFIG) or p['policy_sha256']!=sha(POLICY):raise ValueError('changed M2 protocol/policy')
    for name,h in p['sources'].items():
        if sha(ROOT/name)!=h or sha(Path(p['source_snapshot'])/name)!=h:raise ValueError('changed M2 collection producer: '+name)
    if p.get('predecessor') and sha(p['predecessor']['path'])!=p['predecessor']['sha256']:raise ValueError('changed predecessor plan')
    if p.get('timeout_recovery'):
        recovery=p['timeout_recovery']
        contract=Path(recovery['path'])
        if contract not in (RECOVERY.resolve(),RESUMPTION.resolve(),CONTINUATION.resolve()) or recovery['sha256']!=sha(contract):raise ValueError('changed M2 recovery contract')
        tasks=[dict(t) for t in p['tasks']]
        if contract==CONTINUATION.resolve():
            from .model_m2_phase_resume import spec
            expected=spec(Path(p['predecessor']['path']),tasks)
        else:expected=recovery_spec(Path(p['predecessor']['path']),tasks,contract==RESUMPTION.resolve())
        if expected!=recovery or tasks!=p['tasks']:
            raise ValueError('changed M2 recovery evidence/resources')
        allowed=set(read(contract)['extended_task_ids'])
        if any(t.get('route_timeout_s',1200)!=1200 for t in p['tasks'] if t['id'] not in allowed):
            raise ValueError('unregistered M2 resource exception')
        if contract!=CONTINUATION.resolve() and any(t.get('phase_resume') for t in p['tasks']):raise ValueError('unregistered phase-resume task')
    elif any(t.get('route_timeout_s',1200)!=1200 or t.get('phase_resume') for t in p['tasks']):raise ValueError('unregistered M2 resource exception')
    return p


def funding(count,folder,task_ids=None):
    cfg=read(CONFIG);u=usage(read(Ledger().path)['entries']);limits=read(POLICY)['resources'];later=cfg['later_work_reserved']
    extra=0
    if task_ids:
        p=read(folder/'plan.json');extra=sum(t.get('route_timeout_s',1200)-1200+(read(CONTINUATION)['lec_timeout_s'] if t.get('phase_resume') else 0) for t in p['tasks'] if t['id'] in task_ids)
    wall=count*1800+1800+extra;cpu=wall*cfg['resource_limits']['threads']
    for stage,key in [('synth','max_synthesis_calls'),('grt','max_global_route_calls')]:
        if u[stage]+count+later[stage]>limits[key]:raise ValueError('M2 wave/future calls not funded')
    if u['walltime_s']+wall+later['walltime_s']>limits['max_global_walltime_h']*3600 or u['CPU_time_s']+cpu+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600:
        raise ValueError('M2 wave/future time not funded')
    if shutil.disk_usage(folder).free<count*cfg['resource_limits']['storage_per_task_bytes']+10*1024**3:raise ValueError('M2 storage reserve not funded')
    return {'starting_usage':u,'leaf_walltime_s':wall,'CPU_envelope_s':cpu,'future_reserve':later}


def admit(folder,mode,out,limit=24):
    path=(folder/'plan.json').resolve();p=verify_plan(path);cfg=read(CONFIG)
    if mode=='test':raise ValueError('independent M2 tests are preregistered but locked until validated frozen fitting selection')
    rolling=(p.get('timeout_recovery') or {}).get('rolling_fitting',False)
    maximum=read(CONTINUATION)['max_fitting_tasks'] if rolling and mode=='fitting' else cfg['resource_limits']['max_tasks_per_wave']
    if mode not in ('pilots','train','validation',*(['fitting'] if rolling else [])) or not 1<=limit<=maximum:raise ValueError('invalid M2 wave')
    ids=set(cfg['capacity_pilots']) if mode=='pilots' else {t['id'] for t in p['tasks'] if t['split'] in (('train','validation') if mode=='fitting' else (mode,))}
    if mode!='pilots':
        proof=read(folder/'capacity-proof.json')
        if proof['plan_sha256']!=sha(path) or proof['status']!='passed':raise ValueError('capacity proof missing/changed')
    todo=[]
    for t in p['tasks']:
        if t['id'] not in ids:continue
        d=run_directory(folder,t)
        if d.exists():
            if not (d/'manifest.json').exists() or read(d/'manifest.json')['status']!='completed':raise ValueError('failed/incomplete M2 task: '+t['id'])
        else:todo.append(t)
    if not todo:raise ValueError('acquisition phase already complete')
    priority=p.get('timeout_recovery',{}).get('priority_task_ids',[]) if p.get('timeout_recovery') else []
    todo.sort(key=lambda t:0 if t['id'] in priority else 1)
    chosen=todo[:limit]
    exclusive(out,{'version':'asap7-m2-primitives-wave-v1','id':p['id']+'-wave-'+out.stem,'purpose':PURPOSE,
                   'plan_path':str(path),'plan_sha256':sha(path),'protocol_sha256':sha(CONFIG),'policy_sha256':sha(POLICY),
                   'mode':mode,'task_ids':[t['id'] for t in chosen],'funding':funding(len(chosen),folder,{t['id'] for t in chosen}),'automatic_retries':0,
                   'call_caps':{'synth':len(chosen),'grt':len(chosen),'final':0}})
    print(json.dumps({'wave':str(out),'tasks':len(chosen),'remaining':len(todo)-len(chosen)}))


def task(args):
    if not args.admission:raise ValueError('frozen M2 wave required')
    a=read(args.admission)
    if a.get('purpose')!=PURPOSE or a['id']!=args.admission_id or sha(a['plan_path'])!=a['plan_sha256']:raise ValueError('M2 wave identity mismatch')
    p=verify_plan(a['plan_path']);matches=[t for t in p['tasks'] if t['id']==args.task_id]
    if len(matches)!=1 or args.task_id not in a['task_ids'] or a['automatic_retries']!=0:raise ValueError('unadmitted M2 task')
    t=matches[0];cfg=read(CONFIG);folder=Path(a['plan_path']).parent
    if t.get('inherited_run'):raise ValueError('inherited M2 measurement must not be relaunched')
    if t['split']=='test':raise ValueError('independent M2 test remains locked')
    if a['mode']=='fitting' and not (p.get('timeout_recovery') or {}).get('rolling_fitting'):raise ValueError('unregistered rolling acquisition')
    allowed=set(cfg['capacity_pilots']) if a['mode']=='pilots' else {x['id'] for x in p['tasks'] if x['split'] in (('train','validation') if a['mode']=='fitting' else (a['mode'],))}
    if t['id'] not in allowed:raise ValueError('M2 phase mismatch')
    if a['mode']!='pilots':
        proof=read(folder/'capacity-proof.json')
        if proof['plan_sha256']!=sha(folder/'plan.json') or proof['status']!='passed':raise ValueError('capacity not qualified')
    source=run_directory(folder,next(x for x in p['tasks'] if x['id']==t['mapping_source_task'])) if t['mapping_source_task'] else None
    if t.get('phase_resume'):source=Path(t['phase_resume']['directory'])
    if (args.platform!='asap7' or args.top!=t['top'] or args.stage!='grt' or args.period_ps!=t['period_ps'] or args.abc_target_ps!=1500
            or args.threads!=4 or args.memory_limit_mib!=8192 or args.synth_timeout_s!=300 or args.route_timeout_s!=t.get('route_timeout_s',1200)
            or args.budget_purpose!='characterization' or args.period_role!='resource_trial' or args.io_delay_max_ps is not None
            or sha(args.rtl)!=t['rtl_sha256'] or not args.sample_contract or sha(args.sample_contract)!=t['sample_contract_sha256']
            or (args.resume_synth_from.resolve() if args.resume_synth_from else None)!=(source.resolve() if source else None)
            or args.out.resolve()!=folder.resolve()/'runs'/t['id']):raise ValueError('actual request differs from frozen M2 task')
    return a,p,t


def verify_admission(args,p,rtl,ledger):
    a,plan,t=task(args)
    if p['profile_sha256']!=t['profile_sha256']:raise ValueError('changed M2 platform')
    ledger.check_job_admission();entries=read(ledger.path)['entries']
    if any(e.get('task_id')==t['id'] and e.get('admission_id','').startswith(plan['id']+'-wave-') for e in entries):raise ValueError('previous M2 attempt exists')
    funding(len(a['task_ids']),Path(a['plan_path']).parent,set(a['task_ids']))
    return sha(args.admission)


def seed_mapped(args,out,results,environment,command,tools):
    a,p,t=task(args);d=args.resume_synth_from;m=read(d/'manifest.json')
    if (m['status']!='completed' or m['threads_per_tool']!=4 or m['abc_target_ps']!=1500 or m['io_delay_max_ps'] is not None
            or sha(d/'input.sv')!=t['rtl_sha256'] or sha(d/'sample-contract.json')!=t['sample_contract_sha256']
            or m['platform_profile']['profile_sha256']!=t['profile_sha256']):raise ValueError('M2 mapping identity mismatch')
    for name in ('LIB_FILES','TECH_LEF','SC_LEF','CORNER','ASAP7_USE_VT','LIB_MODEL','TC_TEMPERATURE','ABC_DRIVER_CELL','ABC_LOAD_IN_FF','YOSYS_MAX_THREADS'):
        if environment.get(name)!=m['effective_environment'].get(name):raise ValueError('M2 mapped environment changed: '+name)
    for name,tool in tools.items():
        if tool['sha256']!=m['tools'][name]['sha256']:raise ValueError('M2 mapped executable changed')
    for lib in m['libraries']:
        if sha(lib['path'])!=lib['sha256']:raise ValueError('M2 mapped library changed')
    for name,h in m['files_sha256'].items():
        path=Path(name)
        if path.is_relative_to(args.orfs.resolve()) or path.is_relative_to(Path(__file__).parent/'backend'):
            if sha(path)!=h:raise ValueError('M2 physical asset changed')
    old=d/'results'/SUFFIX/'1_2_yosys.v'
    if sha(old)!=m['evidence_sha256'][str(old.relative_to(d))]:raise ValueError('M2 mapped netlist changed')
    results.mkdir(parents=True,exist_ok=True)
    if any(results.iterdir()):raise ValueError('M2 fresh physical directory required')
    copied=results/old.name;shutil.copy2(old,copied);command.append('--assume-old='+str(copied))
    return {'mode':'same_mapping_fresh_SDC_IO_and_physical_chain','source_run':str(d.resolve()),
            'source_manifest_sha256':sha(d/'manifest.json'),'source_netlist_sha256':sha(old),
            'old_ODB_or_SDC_copied':False,'old_SDC_ps':m['period_ps'],'new_SDC_ps':args.period_ps,'Yosys_ABC_reexecuted':False}


def run_task(folder,wave,a,t):
    d=folder/'runs'/t['id'];d.parent.mkdir(exist_ok=True)
    command=[sys.executable,'-B','-m','experiments.arithmetic_dse.backend','--platform','asap7','--admission',str(wave.resolve()),
             '--admission-id',a['id'],'--task-id',t['id'],'--rtl',t['rtl'],'--top',t['top'],'--out',str(d),
             '--period-ps',str(t['period_ps']),'--abc-target-ps','1500','--threads','4','--stage','grt','--budget-purpose','characterization',
             '--sample-contract',t['sample_contract']]
    if t.get('route_timeout_s',1200)!=1200:command+=['--route-timeout-s',str(t['route_timeout_s'])]
    if t['mapping_source_task']:
        plan=read(a['plan_path']);original=next(x for x in plan['tasks'] if x['id']==t['mapping_source_task'])
        command+=['--resume-synth-from',t['phase_resume']['directory'] if t.get('phase_resume') else str(run_directory(folder,original))]
    print('START',t['id'],flush=True)
    with (folder/(t['id']+'.driver.log')).open('x') as log:result=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    m=read(d/'manifest.json') if (d/'manifest.json').exists() else {'status':'failed_before_manifest'}
    print('DONE',t['id'],m['status'],m.get('failure_reason'),flush=True)
    if result.returncode or m['status']!='completed':raise RuntimeError('M2 task failed: '+t['id'])
    return {'task_id':t['id'],'manifest_sha256':sha(d/'manifest.json')}


def run(wave):
    a=read(wave);p=verify_plan(a['plan_path']);folder=Path(a['plan_path']).parent;indexed={t['id']:t for t in p['tasks']}
    with (folder/'collection.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('M2 collection already running')
        todo=[];outcomes=[]
        for tid in a['task_ids']:
            d=run_directory(folder,indexed[tid])
            if d.exists():
                if not (d/'manifest.json').exists() or read(d/'manifest.json')['status']!='completed':raise ValueError('prior M2 failure blocks wave')
            else:todo.append(tid)
        def launch(tid):return run_task(folder,wave,a,indexed[tid])
        def done(result):outcomes.append(result);write(wave.with_suffix('.outcome.json'),outcomes)
        from .model_target_collection import _schedule
        _schedule(todo,indexed,folder,4,launch,done)


def extract_rows(folder,ids):
    from .model_mul_interval_fit import verify_measurement
    from .model_samples import verify_capture_banks
    from .model_features import features
    p=verify_plan(folder/'plan.json');ledger={e['id']:e for e in read(Ledger().path)['entries']};rows=[];runs=[]
    waves={read(f)['id']:(f,read(f)) for f in (folder/'waves').glob('*.json') if not f.name.endswith('.outcome.json')}
    for t in p['tasks']:
        if t['id'] not in ids:continue
        if t['split']=='test':raise ValueError('independent M2 test labels remain locked')
        d=run_directory(folder,t);m=read(d/'manifest.json')
        if m['status']!='completed' or m['threads_per_tool']!=4:raise ValueError('incomplete M2 result')
        if t.get('phase_resume'):
            from .model_m2_phase_resume import validate_replayed_pair
            reuse=m.get('checkpoint_reuse',{});proof=Path(reuse['proof_path'])
            if (reuse.get('source_manifest_sha256')!=t['phase_resume']['manifest_sha256']
                    or not proof.is_relative_to(d.resolve()) or sha(proof)!=reuse['proof_sha256']
                    or m['files_sha256'].get(str(proof))!=sha(proof)):
                raise ValueError('changed phase continuation proof binding')
            validate_replayed_pair(proof,d/'results'/SUFFIX/'4_before_rsz_lec.v',d/'results'/SUFFIX/'4_after_rsz_lec.v')
            if read(proof)['reservation_id'] not in {c['budget_reservation_id'] for c in m['commands']}:
                raise ValueError('phase continuation proof was not paid by this task')
        if t.get('inherited_run'):
            origin=t['inherited_run'];wp=Path(origin['wave_path']);w=read(wp)
            if (sha(d/'manifest.json')!=origin['manifest_sha256'] or sha(wp)!=origin['wave_sha256']
                    or w['plan_sha256'] not in ancestor_plans(p['predecessor']['path'])
                    or sha(w['plan_path'])!=w['plan_sha256']):raise ValueError('changed inherited M2 measurement')
        else:
            wp,w=waves[m['admission_id']]
            if w['plan_sha256']!=sha(folder/'plan.json'):raise ValueError('M2 measured plan mismatch')
        if t['id'] not in w['task_ids']:raise ValueError('M2 measured wave mismatch')
        for c in m['commands']:
            e=ledger[c['budget_reservation_id']]
            if e['status']!='completed' or e.get('admission_sha256')!=sha(wp) or e.get('task_id')!=t['id']:raise ValueError('M2 measurement not paid/bound')
        cells=read(d/'liberty_cells.json')['cells'];specs=read(d/'sample-contract.json')['labels']
        verify_measurement(d,m,t,{'id':m['admission_id']},cells)
        for stage in m['metrics']:
            prefix=d/'reports'/SUFFIX/('vulsim_'+stage['stage']);banks=verify_capture_banks(prefix,d/'sample-contract.json',cells)
            if banks!=stage.get('model_capture_banks',{}):raise ValueError('M2 bank structure changed')
            instances=[v.split('\t')[:2] for v in Path(str(prefix)+'_instances.tsv').read_text().splitlines()]
            labels={v['id']:v for v in stage['model_labels']}
            for spec in specs:
                core=sum(cells[master]['area_um2'] for name,master in instances if master in cells and not cells[master]['sequential'] and name.startswith(spec['arithmetic_scope']))
                if core<=0:raise ValueError('M2 primitive missing positive core area')
                label=labels[spec['id']]
                rows.append({'id':t['id']+'/'+spec['id']+'/'+stage['stage'],'task_id':t['id'],'split':t['split'],'family':t['family'],
                             'stage':stage['stage'],'operation':spec['operation'],'rtl_operation':spec['rtl_operation'],'spec':spec,
                             'features':features(spec['lhs_width'],spec['rhs_width'],spec['result_width'],spec['fanout'],1500,t['period_ps']),
                             'delay_ps':label['data_delay_ps'],'comb_area_um2':core,'period_ps':t['period_ps'],
                             'observed_H_ps':t['period_ps']-label['data_delay_ps']-label['slack_ps'],
                             'path_slack_ps':label['slack_ps'],'whole_setup_slack_ps':stage['setup_worst_slack_ps'],
                             'whole_hold_slack_ps':stage['hold_worst_slack_ps'],'manifest_sha256':sha(d/'manifest.json'),
                             'source_sha256':t['rtl_sha256'],'bank_counts':banks.get(spec['id']), 'reference_role':t['reference_role']})
        runs.append({'task_id':t['id'],'manifest_sha256':sha(d/'manifest.json'),
                     'peak_RSS_MiB':max(c['sampled_process_tree_peak_rss_KiB'] for c in m['commands'])/1024,
                     'grt_walltime_s':next(c['walltime_s'] for c in m['commands'] if c['log'].endswith('/grt.log'))})
    if {r['task_id'] for r in runs}!=set(ids):raise ValueError('incomplete M2 extraction')
    return {'version':'asap7-m2-primitives-dataset-v1','plan_path':str((folder/'plan.json').resolve()),'plan_sha256':sha(folder/'plan.json'),
            'protocol_sha256':sha(CONFIG),'rows':rows,'runs':runs,'failures':[],'old_test_labels_used':False}


def capacity(folder):
    cfg=read(CONFIG);data=extract_rows(folder,set(cfg['capacity_pilots']));exclusive(folder/'pilot-data.json',data)
    exclusive(folder/'capacity-proof.json',{'status':'passed','plan_sha256':sha(folder/'plan.json'),'pilot_data_sha256':sha(folder/'pilot-data.json'),
                                         'runs':data['runs'],'scope':'named <=64bit primitive/<=32bit divider/one complete binary32 bounded bundles only; per-task limits retained'})
    print(json.dumps({'status':'passed','runs':data['runs'],'rows':len(data['rows'])}))


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','admit','run','capacity','extract'])
    for name in ('folder','atom','out','wave','predecessor'):ap.add_argument('--'+name,type=Path)
    ap.add_argument('--timeout-recovery',action='store_true')
    ap.add_argument('--resume-original-grid',action='store_true')
    ap.add_argument('--phase-continuation',action='store_true')
    ap.add_argument('--mode',choices=['pilots','train','validation','test','fitting']);ap.add_argument('--limit',type=int,default=24);args=ap.parse_args()
    if args.action=='prepare':prepare(args.folder,args.atom,args.predecessor,args.timeout_recovery,args.resume_original_grid,args.phase_continuation)
    elif args.action=='admit':admit(args.folder,args.mode,args.out,args.limit)
    elif args.action=='run':run(args.wave)
    elif args.action=='capacity':capacity(args.folder)
    else:
        p=verify_plan(args.folder/'plan.json');splits=('train','validation') if args.mode=='fitting' else (args.mode,)
        exclusive(args.out,extract_rows(args.folder,{t['id'] for t in p['tasks'] if t['split'] in splits}))


if __name__=='__main__':main()
