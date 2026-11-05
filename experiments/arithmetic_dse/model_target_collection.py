"""Frozen target/load sample plans and bounded waves with deferred independent tests."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import fcntl
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

from .budget import Ledger, POLICY, usage
from .model_collection import sha, write
from .model_mul_intervals import interval, source, key
from .model_target_features import clock_request, reference_values, features
from .platforms import profile

ROOT = Path(__file__).resolve().parents[2]
CONFIG = Path(__file__).with_name('configs')/'model_mul_interval_target_load_v3.json'
PURPOSE = 'arithmetic_interval_target_load_collection'
SUFFIX = Path('asap7/arithmetic_probe/base')


def read(path): return json.loads(Path(path).read_text())
def run_directory(folder, task):
    return Path(task['inherited_run']['directory']) if task.get('inherited_run') else folder/'runs'/task['id']

def measurement_context(manifest,task):
    """Explicit train-only 2-thread variation; deployment/validation/test are 4."""
    inherited=task.get('inherited_run')
    expected=2 if inherited else read(CONFIG)['resource_limits']['threads']
    if inherited and (task['split']!='train' or 'absolute-2250' not in task['target_roles']):
        raise ValueError('two-thread measurements are training-only')
    identity=dict(manifest['mapping_context'])
    controls=identity['tool_thread_controls']
    if (manifest['threads_per_tool']!=expected or set(controls)!={'YOSYS_MAX_THREADS','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','NUM_CORES'}
            or any(v!=expected for v in controls.values())):raise ValueError('unregistered measurement thread context')
    identity['tool_thread_controls']={k:read(CONFIG)['resource_limits']['threads'] for k in controls}
    for name in ('sdc_period_ps','io_delay_max_ps'):identity.pop(name)
    return identity
def exclusive(path, value):
    if Path(path).exists(): raise ValueError('preserve existing evidence: '+str(path))
    write(Path(path), value)


def sources():
    names = ['model_target_collection.py', 'model_target_features.py', 'model_mul_intervals.py',
             'model_analysis.py', 'model_collection.py', 'model_features.py', 'model_samples.py',
             'model_mul_interval_fit.py', 'backend.py', 'platform_probe.py', 'platforms.py',
             'budget.py', 'processes.py', 'sdc.py', 'characterization.py']
    return [Path(__file__).with_name(n) for n in names]+[CONFIG, POLICY]+sorted(p for p in Path(__file__).with_name('backend').iterdir() if p.is_file())


def prepare_reference(data, out):
    from .model_mul_interval_fit import verify_measurement
    dataset = read(data)
    a = read(dataset['admission_path'])
    if dataset['failures'] or any(r['split'] not in ('train', 'validation') for r in dataset['rows']):
        raise ValueError('reference may only read complete predecessor fitting data')
    if sha(dataset['admission_path']) != dataset['admission_sha256']: raise ValueError('changed reference admission')
    grouped = defaultdict(list)
    audited = []
    for t in a['tasks']:
        if t['split'] != 'train': continue
        directory = Path(dataset['admission_path']).parent/'runs'/t['id']
        m = read(directory/'manifest.json')
        cells = read(directory/'liberty_cells.json')['cells']
        verify_measurement(directory, m, t, a, cells)
        if m['status'] != 'completed': raise ValueError('incomplete predecessor training measurement')
        raw = next(x for x in m['metrics'] if x['stage']=='grt')
        labels = {x['id']:x for x in raw['model_labels']}
        for r in dataset['rows']:
            if r['stage']!='grt' or r['split']!='train' or r['id'].split('/')[0]!=t['id']: continue
            label = labels[r['id'].split('/')[1]]
            if label['data_delay_ps'] != r['delay_ps']: raise ValueError('reference does not match actual training label')
            grouped[r['interval_key']].append((r['features']['width'], r['delay_ps'], m['period_ps']-r['delay_ps']-label['slack_ps'], r['id']))
        audited.append({'task':t['id'],'manifest_sha256':sha(directory/'manifest.json')})
    entries = {}
    if len(grouped)!=42: raise ValueError('42 complete registered intervals required')
    for name, rows in grouped.items():
        rows.sort()
        if [r[0] for r in rows]!=[8,16,32]: raise ValueError('training reference anchor coverage mismatch')
        entries[name] = {'delay_anchors':[[r[0],r[1]] for r in rows], 'overhead_ps':max(0., max(r[2] for r in rows)),
                         'source_rows':[r[3] for r in rows]}
    out.parent.mkdir(parents=True,exist_ok=True)
    exclusive(out, {'version':'arithmetic-interval-training-reference-v1','role':'sampling_scale_only_not_a_qualified_cost_model',
                    'protocol_sha256':sha(CONFIG), 'dataset_sha256':sha(data), 'dataset_path':str(data.resolve()),
                    'admission_path':dataset['admission_path'], 'admission_sha256':sha(dataset['admission_path']),
                    'audited_train_runs':audited, 'intervals':entries, 'test_labels_read':False})
    print(json.dumps({'intervals':len(entries),'train_runs':len(audited),'reference':str(out)}))


def prepare(graphs, reference, out, predecessor=None):
    cfg, ref = read(CONFIG), read(reference)
    if ref['protocol_sha256']!=sha(CONFIG) or ref['test_labels_read']: raise ValueError('unbound training-side reference')
    out.mkdir(parents=True, exist_ok=False)
    indexed = []
    for path in sorted(graphs.glob('*.json')):
        report = read(path)
        groups = report['graph']['regions'][0]['legal_groups']
        for first in range(len(groups)):
            for last in range(first,len(groups)):
                spec = interval(report, first, last)
                if spec['width'] in sum(cfg['splits'].values(),[]): indexed.append((report,spec))
    task_list, counts = [], {}
    p = profile('asap7')
    for split, widths in cfg['splits'].items():
        items = [item for item in indexed if item[1]['width'] in widths]
        items.sort(key=lambda item:(reference_values(ref,key(item[1]),item[1]['width'])[0],item[1]['width'],key(item[1])))
        for fanout in cfg['capture_fanouts'][split]:
            packs, pack, ins, caps, low = [], [], 0, 0, None
            for item in items:
                spec=item[1];d,_=reference_values(ref,key(spec),spec['width'])
                ni=sum(spec['input_widths']);nc=spec['capture_width']*fanout;limits=cfg['pack']
                if pack and (len(pack)>=limits['max_samples'] or ins+ni>limits['max_input_bits']
                             or caps+nc>limits['max_capture_bits'] or d/low>limits['max_reference_delay_ratio']):
                    packs.append(pack);pack=[];ins=caps=0;low=None
                if low is None:low=d
                pack.append(item);ins+=ni;caps+=nc
            if pack:packs.append(pack)
            start=len(task_list)
            for number, pack in enumerate(packs):
                group=f'{split}-F{fanout}-b{number:03d}'
                folder=out/'sources'/group;folder.mkdir(parents=True)
                text,labels=source(pack,capture_fanout=fanout)
                rtl=folder/'input.sv';rtl.write_text(text)
                contract=folder/'contract.json'
                exclusive(contract,{'version':'arithmetic-model-labels-v1','source_group':group,'split':split,
                                    'protocol_sha256':sha(CONFIG),'labels':labels})
                targets={}
                for ratio in cfg['relative_data_budgets']:
                    raw=max(h+ratio*d for _,s in pack for d,h in [reference_values(ref,key(s),s['width'])])
                    target=clock_request(raw,cfg['clock_grid_ps'])
                    targets.setdefault(target['requested_period_ps'], {'target':target,'roles':[]})['roles'].append('relative-'+str(ratio))
                for period in cfg['absolute_SDC_ps']:
                    target=clock_request(period,cfg['clock_grid_ps'])
                    targets.setdefault(target['requested_period_ps'], {'target':target,'roles':[]})['roles'].append('absolute-'+str(period))
                for number2,(period,context) in enumerate(sorted(targets.items(),reverse=True)):
                    task_list.append({'id':group+f'-t{number2}','source_group':group,'split':split,'capture_fanout':fanout,
                                      'platform':'asap7','profile_sha256':p['profile_sha256'],'top':'ModelBundle','stage':'grt',
                                      'rtl':str(rtl.resolve()),'rtl_sha256':sha(rtl),'sample_contract':str(contract.resolve()),
                                      'sample_contract_sha256':sha(contract),'period_ps':period,'abc_target_ps':1500,
                                      'target_roles':context['roles'],'clock_representation':context['target'],
                                      'samples':len(labels),'input_bits':sum(sum(s['input_widths']) for s in labels),
                                      'capture_bits':sum(s['capture_width']*fanout for s in labels),
                                      'mapping_source_task':group+'-t0' if number2 else None})
            counts[split+'/F'+str(fanout)]={'bundles':len(packs),'tasks':len(task_list)-start,'interval_samples':len(items)}
    seen={}
    old=read(ref['admission_path']);blocked={t['rtl_sha256'] for t in old['tasks'] if t['split']=='test'}
    for t in task_list:
        if t['rtl_sha256'] in blocked: raise ValueError('old failed independent source reused')
        old_split=seen.setdefault(t['rtl_sha256'],t['split'])
        if old_split!=t['split']: raise ValueError('source family crosses partitions')
    snapshot=out/'source';hashes={}
    for path in sources():
        name=path.relative_to(ROOT);saved=snapshot/name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,saved)
        hashes[str(name)]=sha(saved)
    lineage = None
    if predecessor:
        prior = read(predecessor)
        # Same registered experiment, but no two-thread labels enter the successor.
        axes = ('id','source_group','split','capture_fanout','platform','profile_sha256','top','stage',
                'rtl_sha256','period_ps','abc_target_ps','target_roles','clock_representation','samples',
                'input_bits','capture_bits','mapping_source_task')
        if [[t[k] for k in axes] for t in prior['tasks']] != [[t[k] for k in axes] for t in task_list]:
            raise ValueError('thread successor must preserve all registered sample/target/split axes')
        excluded = []
        for t in prior['tasks']:
            mp=predecessor.parent/'runs'/t['id']/'manifest.json'
            if mp.exists():
                m=read(mp)
                if m['status']!='completed' or m['threads_per_tool']!=2:
                    raise ValueError('unsettled/unexpected predecessor execution')
                excluded.append({'task':t['id'],'manifest_path':str(mp.resolve()),'manifest_sha256':sha(mp)})
        lineage={'plan_path':str(predecessor.resolve()),'plan_sha256':sha(predecessor),
                 'reason':'user requested three concurrent tasks, six threads each',
                 'excluded_two_thread_runs':excluded,'old_labels_used_for_fitting':False}
    exclusive(out/'plan.json',{'version':'arithmetic-interval-target-load-plan-v1','purpose':PURPOSE,'id':out.name,
                              'protocol_sha256':sha(CONFIG),'policy_sha256':sha(POLICY), 'reference_path':str(reference.resolve()),
                              'reference_sha256':sha(reference),'tasks':task_list,'counts':counts,'source_snapshot':str(snapshot.resolve()),
                              'sources':hashes,'blocked_old_test_sources':sorted(blocked),'automatic_retries':0,'test_read_after_fit_only':True,
                              'not_training':False,'main_matrix_authorized':False,'predecessor':lineage})
    print(json.dumps({'counts':counts,'tasks':len(task_list),'rows':2*sum(t['samples'] for t in task_list),
                      'worst_per_task_wall_s':1800,'note':'full design is not a single physical admission; bounded waves required'},indent=2))


def verify_plan(path):
    p=read(path)
    if p['purpose']!=PURPOSE or p['protocol_sha256']!=sha(CONFIG) or p['policy_sha256']!=sha(POLICY):
        raise ValueError('changed target/load protocol or policy')
    if sha(p['reference_path'])!=p['reference_sha256']:raise ValueError('changed frozen sampling reference')
    if p.get('predecessor') and sha(p['predecessor']['plan_path'])!=p['predecessor']['plan_sha256']:
        raise ValueError('changed predecessor plan')
    for name,h in p['sources'].items():
        if sha(ROOT/name)!=h or sha(Path(p['source_snapshot'])/name)!=h:raise ValueError('changed collection source: '+name)
    return p


def selected_tasks(plan, mode):
    if mode=='baseline':return [t for t in plan['tasks'] if t['split']=='train' and 'absolute-2250' in t['target_roles']]
    if mode=='conditional':return [t for t in plan['tasks'] if t['split']=='train' and 'absolute-2250' not in t['target_roles']]
    if mode in ('validation','test'):return [t for t in plan['tasks'] if t['split']==mode]
    if mode=='fitting-full':return [t for t in plan['tasks'] if t['split'] in ('train','validation')]
    if mode=='fitting-baseline':return selected_tasks(plan,'baseline')+selected_tasks(plan,'validation')
    raise ValueError('unknown acquisition mode')


def prepare_successor(predecessor,reference,out):
    """Keep sealed two-thread train labels; every newly executed task uses four."""
    prior=read(predecessor);ref=read(reference)
    if ref['protocol_sha256']!=sha(CONFIG) or ref['test_labels_read']:raise ValueError('invalid successor reference')
    for name,h in prior['sources'].items():
        if sha(Path(prior['source_snapshot'])/name)!=h:raise ValueError('changed predecessor source snapshot')
    out.mkdir(parents=True,exist_ok=False)
    tasks=[];inherited=[]
    waves={read(f)['id']:(f,read(f)) for f in (predecessor.parent/'waves').glob('*.json')
           if not f.name.endswith('.outcome.json')}
    for old in prior['tasks']:
        t=dict(old);mp=predecessor.parent/'runs'/t['id']/'manifest.json'
        if sha(t['rtl'])!=t['rtl_sha256'] or sha(t['sample_contract'])!=t['sample_contract_sha256']:
            raise ValueError('changed registered source')
        if mp.exists():
            m=read(mp)
            if m['status']!='completed' or m['threads_per_tool']!=2 or t['split']!='train' or 'absolute-2250' not in t['target_roles']:
                raise ValueError('only settled two-thread baseline training may be inherited')
            wf,w=waves[m['admission_id']]
            if w['plan_sha256']!=sha(predecessor) or t['id'] not in w['task_ids']:raise ValueError('unbound inherited run')
            t['inherited_run']={'directory':str(mp.parent.resolve()),'manifest_sha256':sha(mp),
                                'wave_path':str(wf.resolve()),'wave_sha256':sha(wf),'threads':2}
            inherited.append(t['id'])
        tasks.append(t)
    if len(inherited)!=43:raise ValueError('successor inherits exactly the sealed 43 training tasks')
    hashes={}
    for path in sources():
        name=path.relative_to(ROOT);saved=out/'source'/name;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,saved)
        hashes[str(name)]=sha(saved)
    p={**prior,'id':out.name,'protocol_sha256':sha(CONFIG),'policy_sha256':sha(POLICY),
       'reference_path':str(reference.resolve()),'reference_sha256':sha(reference),'tasks':tasks,
       'source_snapshot':str((out/'source').resolve()),'sources':hashes,
       'predecessor':{'plan_path':str(predecessor.resolve()),'plan_sha256':sha(predecessor),
                      'inherited_training_tasks':inherited,'reason':'user authorized 4 jobs x 4 threads and retaining old train data'},
       'execution_threads':4,'inherited_training_threads':[2],'not_training':False}
    exclusive(out/'plan.json',p)
    print(json.dumps({'tasks':len(tasks),'inherited_train':len(inherited),'new_threads':4,'parallel_jobs':4}))


def funded(count, directory, *, pending_support=False, backend_ledger=None):
    total=usage(read(Ledger().path)['entries']);limits=read(POLICY)['resources'];later=read(CONFIG)['later_work_reserved']
    if backend_ledger is not None:
        total=backend_ledger.check_job_admission()
    elif total['pending'] and not pending_support:raise ValueError('pending leaf blocks target/load collection')
    wall=count*1800+1800
    threads=read(CONFIG)['resource_limits']['threads']
    if (total['walltime_s']+wall+later['walltime_s']>limits['max_global_walltime_h']*3600
            or total['CPU_time_s']+threads*wall+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600):raise ValueError('wave and future time reserve not funded')
    for stage,limit in [('synth','max_synthesis_calls'),('grt','max_global_route_calls')]:
        if total[stage]+count+later[stage]>limits[limit]:raise ValueError('wave and future calls not funded')
    if shutil.disk_usage(directory).free < count*512*1024**2+10*1024**3:raise ValueError('wave storage reserve not funded')
    return {'usage_before':total,'worst_case_walltime_s':wall,'CPU_envelope_s':threads*wall,'later_work_reserved':later}


def admit(folder, mode, out, limit=48, selection=None, screening=None):
    plan_path=(folder/'plan.json').resolve();p=verify_plan(plan_path)
    if not 1<=limit<=read(CONFIG)['resource_limits']['max_tasks_per_wave']:raise ValueError('invalid wave bound')
    if mode=='test':
        from .model_target_fit import verify_selection
        verify_selection(selection,plan_path)
    if mode=='conditional':
        from .model_target_fit import verify_screening
        verify_screening(screening,plan_path)
    pending=[]
    for t in selected_tasks(p,mode):
        directory=run_directory(folder,t)
        if directory.exists():
            if not (directory/'manifest.json').exists() or read(directory/'manifest.json')['status']!='completed':
                raise ValueError('failed/interrupted task requires explicit diagnosis, no automatic retry: '+t['id'])
        else:pending.append(t)
    if mode=='baseline':pending.sort(key=lambda t:(-t['capture_bits'],-t['input_bits'],t['id']))
    chosen=pending[:limit]
    if not chosen:raise ValueError('acquisition mode already complete')
    funding=funded(len(chosen),folder,pending_support=True)
    out.parent.mkdir(parents=True,exist_ok=True)
    exclusive(out,{'version':'arithmetic-target-load-wave-v1','purpose':PURPOSE,'id':p['id']+'-wave-'+out.stem,
                   'plan_path':str(plan_path),'plan_sha256':sha(plan_path),'protocol_sha256':sha(CONFIG),'policy_sha256':sha(POLICY),
                   'mode':mode,'task_ids':[t['id'] for t in chosen],'call_caps':{'synth':len(chosen),'grt':len(chosen),'final':0},
                   'funding':funding,'automatic_retries':0,'selection_freeze':str(selection.resolve()) if selection else None,
                   'selection_freeze_sha256':sha(selection) if selection else None,
                   'baseline_screening':str(screening.resolve()) if screening else None,
                   'baseline_screening_sha256':sha(screening) if screening else None})
    print(json.dumps({'wave':str(out),'mode':mode,'tasks':len(chosen),'remaining_after_wave':len(pending)-len(chosen),'funding':funding}))


def task(args):
    if not args.admission:raise ValueError('named target/load wave required')
    a=read(args.admission)
    if a['purpose']!=PURPOSE or a['id']!=args.admission_id or sha(a['plan_path'])!=a['plan_sha256']:
        raise ValueError('wave identity mismatch')
    p=verify_plan(a['plan_path']);matches=[t for t in p['tasks'] if t['id']==args.task_id]
    if len(matches)!=1 or args.task_id not in a['task_ids'] or a['automatic_retries']!=0:raise ValueError('task not admitted')
    t=matches[0]
    if t['id'] not in {item['id'] for item in selected_tasks(p,a['mode'])}:raise ValueError('task belongs to another acquisition phase')
    if a['mode']=='conditional':
        from .model_target_fit import verify_screening
        if not a['baseline_screening'] or sha(a['baseline_screening'])!=a['baseline_screening_sha256']:raise ValueError('changed baseline screening')
        verify_screening(Path(a['baseline_screening']),Path(a['plan_path']))
    source=run_directory(Path(a['plan_path']).parent,next(x for x in p['tasks'] if x['id']==t['mapping_source_task'])) if t['mapping_source_task'] else None
    if (args.platform!='asap7' or args.stage!='grt' or args.top!=t['top'] or args.period_ps!=t['period_ps']
            or args.abc_target_ps!=1500 or args.io_delay_max_ps is not None or args.threads!=read(CONFIG)['resource_limits']['threads'] or args.memory_limit_mib!=8192
            or args.synth_timeout_s!=300 or args.route_timeout_s!=1200 or args.budget_purpose!='characterization'
            or args.period_role!='resource_trial' or sha(args.rtl)!=t['rtl_sha256'] or not args.sample_contract
            or sha(args.sample_contract)!=t['sample_contract_sha256']
            or (args.resume_synth_from.resolve() if args.resume_synth_from else None)!=(source.resolve() if source else None)):
        raise ValueError('actual target/load request differs from frozen task')
    if t['split']=='test':
        from .model_target_fit import verify_selection
        if not args.selection_freeze or sha(args.selection_freeze)!=a['selection_freeze_sha256']:raise ValueError('missing/changed independent selection')
        verify_selection(args.selection_freeze,Path(a['plan_path']))
    return a,p,t


def verify_admission(args,platform,rtl,ledger):
    a,p,t=task(args)
    if t['profile_sha256']!=platform['profile_sha256']:raise ValueError('changed platform profile')
    entries=read(ledger.path)['entries']
    if any(e.get('task_id')==t['id'] and e.get('admission_id','').startswith(p['id']+'-wave-') for e in entries):
        raise ValueError('previous attempt exists, no automatic retry')
    funded(len(a['task_ids']),Path(a['plan_path']).parent,backend_ledger=ledger)
    return sha(args.admission)


def seed_mapped(args,out,results,environment,command,tools):
    a,p,t=task(args);directory=args.resume_synth_from
    m=read(directory/'manifest.json')
    if (m['status']!='completed' or m['abc_target_ps']!=1500 or m['io_delay_max_ps'] is not None
            or sha(directory/'input.sv')!=t['rtl_sha256'] or sha(directory/'sample-contract.json')!=t['sample_contract_sha256']
            or m['platform_profile']['profile_sha256']!=t['profile_sha256']):raise ValueError('mapping source identity mismatch')
    for name in ('LIB_FILES','TECH_LEF','SC_LEF','CORNER','ASAP7_USE_VT','LIB_MODEL','TC_TEMPERATURE','ABC_DRIVER_CELL','ABC_LOAD_IN_FF'):
        if environment.get(name)!=m['effective_environment'].get(name):raise ValueError('mapped reuse environment changed: '+name)
    if m['threads_per_tool']!=args.threads:
        src=next(x for x in p['tasks'] if x['id']==t['mapping_source_task'])
        if not src.get('inherited_run') or sha(directory/'manifest.json')!=src['inherited_run']['manifest_sha256']:
            raise ValueError('unqualified mapping thread transition')
    for name,tool in tools.items():
        if tool['sha256']!=m['tools'][name]['sha256']:raise ValueError('mapped reuse executable changed')
    for lib in m['libraries']:
        if sha(lib['path'])!=lib['sha256']:raise ValueError('mapped reuse library changed')
    for filename,h in m['files_sha256'].items():
        path=Path(filename)
        if path.is_relative_to(args.orfs.resolve()) or path.is_relative_to(Path(__file__).parent/'backend'):
            if sha(path)!=h:raise ValueError('mapped reuse physical asset changed: '+filename)
    old=directory/'results'/SUFFIX/'1_2_yosys.v';rel=str(old.relative_to(directory))
    if sha(old)!=m['evidence_sha256'][rel]:raise ValueError('changed mapped netlist')
    results.mkdir(parents=True,exist_ok=True)
    if any(results.iterdir()):raise ValueError('fresh physical directory required')
    target=results/old.name;shutil.copy2(old,target);command.append('--assume-old='+str(target))
    return {'mode':'same_mapping_fresh_SDC_IO_and_physical_chain','source_manifest_sha256':sha(directory/'manifest.json'),
            'source_netlist_sha256':sha(old),'source_run':str(directory.resolve()),'ABC_ps':1500,
            'old_SDC_ps':m['period_ps'],'new_SDC_ps':args.period_ps,'IO_policy':'0.2*T in each respective physical implementation',
            'old_ODB_or_SDC_copied':False,'Yosys_ABC_reexecuted':False}


def _run_task(wave,a,t,folder,indexed):
    tid=t['id'];directory=folder/'runs'/tid
    directory.parent.mkdir(exist_ok=True)
    command=[sys.executable,'-B','-m','experiments.arithmetic_dse.backend','--platform','asap7','--admission',str(wave.resolve()),
             '--admission-id',a['id'],'--task-id',tid,'--rtl',t['rtl'],'--top',t['top'],'--out',str(directory),
             '--period-ps',str(t['period_ps']),'--abc-target-ps','1500','--stage','grt','--budget-purpose','characterization',
             '--sample-contract',t['sample_contract'],'--threads',str(read(CONFIG)['resource_limits']['threads'])]
    if t['mapping_source_task']:command+=['--resume-synth-from',str(run_directory(folder,indexed[t['mapping_source_task']]))]
    if a['selection_freeze']:command+=['--selection-freeze',a['selection_freeze']]
    print('START',tid,'T',t['period_ps'],'samples',t['samples'],flush=True)
    with (folder/(tid+'.driver.log')).open('x') as log:result=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    m=read(directory/'manifest.json') if (directory/'manifest.json').exists() else {'status':'failed_before_manifest'}
    print('DONE',tid,m['status'],m.get('failure_reason'),flush=True)
    if result.returncode or m['status']!='completed':raise RuntimeError('target/load collection stopped: '+tid)
    return {'task':tid,'manifest_sha256':sha(directory/'manifest.json')}


def _schedule(task_ids,indexed,folder,workers,launch,on_done):
    """Bound launches; honor mapped-netlist dependencies, drain on pause/failure."""
    waiting=list(task_ids);active={};errors=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        while waiting or active:
            paused=(folder/'PAUSE').exists()
            while waiting and len(active)<workers and not paused and not errors:
                ready=None
                for tid in waiting:
                    source=indexed[tid]['mapping_source_task']
                    if source:
                        mp=run_directory(folder,indexed[source])/'manifest.json'
                        if not mp.exists() or read(mp).get('status')!='completed':continue
                    ready=tid;break
                if ready is None:break
                waiting.remove(ready);active[pool.submit(launch,ready)]=ready
            if not active:
                if errors:raise RuntimeError('; '.join(errors))
                if paused:print('PAUSED between tasks',flush=True);return
                if waiting:raise ValueError('mapped source missing or incomplete: '+','.join(waiting))
                return
            completed,_=wait(active,return_when=FIRST_COMPLETED)
            for future in completed:
                tid=active.pop(future)
                try:on_done(future.result())
                except Exception as error:errors.append(tid+': '+str(error))
    if errors:raise RuntimeError('; '.join(errors))


def run(wave):
    a=read(wave);p=verify_plan(a['plan_path']);folder=Path(a['plan_path']).parent
    with (folder/'collection.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('another collection driver owns this plan')
        indexed={t['id']:t for t in p['tasks']};outcomes=[];todo=[]
        for tid in a['task_ids']:
            directory=run_directory(folder,indexed[tid])
            if directory.exists():
                if not (directory/'manifest.json').exists() or read(directory/'manifest.json')['status']!='completed':
                    raise ValueError('prior failed task stops wave')
                outcomes.append({'task':tid,'manifest_sha256':sha(directory/'manifest.json')})
            else:todo.append(tid)
        def done(result):
            outcomes.append(result);write(wave.with_suffix('.outcome.json'),sorted(outcomes,key=lambda r:a['task_ids'].index(r['task'])))
        workers=read(CONFIG)['resource_limits']['parallel_jobs']
        if workers>read(POLICY)['resources']['parallel_jobs']:raise ValueError('wave exceeds global job slots')
        _schedule(todo,indexed,folder,workers,lambda tid:_run_task(wave,a,indexed[tid],folder,indexed),done)


def extract(folder,mode,selection=None):
    from .model_mul_interval_fit import verify_measurement
    from .model_samples import verify_capture_banks
    plan_path=folder/'plan.json';p=verify_plan(plan_path);reference=read(p['reference_path'])
    if mode=='test':
        from .model_target_fit import verify_selection
        verify_selection(selection,plan_path)
    rows=[];failures=[];tasks=selected_tasks(p,mode)
    waves={}
    for path in (folder/'waves').glob('*.json'):
        if path.name.endswith('.outcome.json'):continue
        candidate=read(path)
        if isinstance(candidate,dict) and candidate.get('version')=='arithmetic-target-load-wave-v1':waves[candidate['id']]=(path,candidate)
    ledger_entries={e['id']:e for e in read(Ledger().path)['entries']}
    for t in tasks:
        directory=run_directory(folder,t);mp=directory/'manifest.json'
        if not mp.exists():failures.append({'task':t['id'],'status':'not_run'});continue
        m=read(mp)
        if m['status']!='completed':failures.append({'task':t['id'],'status':m['status'],'reason':m.get('failure_reason')});continue
        inherited=t.get('inherited_run')
        if inherited:
            wave_path=Path(inherited['wave_path']);wave=read(wave_path)
            if (sha(mp)!=inherited['manifest_sha256'] or sha(wave_path)!=inherited['wave_sha256']
                    or wave['plan_sha256']!=p['predecessor']['plan_sha256'] or t['split']!='train'):
                raise ValueError('changed inherited training evidence')
        else:
            if m['admission_id'] not in waves:raise ValueError('actual run has no frozen wave admission')
            wave_path,wave=waves[m['admission_id']]
            if wave['plan_sha256']!=sha(plan_path):raise ValueError('wave does not bind current plan')
        if t['id'] not in wave['task_ids']:raise ValueError('wave does not bind actual task')
        for command in m['commands']:
            charge=ledger_entries[command['budget_reservation_id']]
            if charge['status']!='completed' or charge.get('admission_sha256')!=sha(wave_path) or charge.get('task_id')!=t['id']:
                raise ValueError('actual measurement is not bound to charged wave')
        if sha(directory/'input.sv')!=t['rtl_sha256'] or sha(directory/'sample-contract.json')!=t['sample_contract_sha256']:
            raise ValueError('changed source/boundary')
        cells=read(directory/'liberty_cells.json')['cells'];specs=read(directory/'sample-contract.json')['labels']
        # Wave admission is the actual leaf identity, while the frozen plan binds data grouping.
        verify_measurement(directory,m,t,{'id':m['admission_id']},cells)
        if (m['io_delay_max_ps'] is not None or m['threads_per_tool']!=(2 if inherited else read(CONFIG)['resource_limits']['threads'])
                or (not inherited and not m['admission_id'].startswith(p['id']+'-wave-'))):
            raise ValueError('wrong measurement wave or IO policy')
        for stage in m['metrics']:
            prefix=directory/'reports'/SUFFIX/('vulsim_'+stage['stage'])
            banks=verify_capture_banks(prefix,directory/'sample-contract.json',cells)
            if banks!=stage.get('model_capture_banks',{}):raise ValueError('bank structure mismatch')
            labels={l['id']:l for l in stage['model_labels']}
            instances=[line.split('\t')[:2] for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines()]
            for spec in specs:
                label=labels[spec['id']];area=0.;launch=capture=0
                for name,master in instances:
                    if master not in cells or not name.startswith(spec['instance_scope']):continue
                    cell=cells[master]
                    if cell['sequential']:
                        launch+=int(name.startswith(spec['instance_scope']+'src'))
                        capture+=int(name.startswith(spec['instance_scope']+'dst') or name.startswith(spec['instance_scope']+'y'))
                    elif name.startswith(spec['arithmetic_scope']):area+=cell['area_um2']
                if not 0<launch<=sum(spec['input_widths']) or not 0<capture<=spec['capture_width']*spec['fanout'] or area<=0:
                    raise ValueError('invalid actual core/boundary label')
                rows.append({'id':t['id']+'/'+spec['id']+'/'+stage['stage'],'task_id':t['id'],'split':t['split'],'platform':'asap7',
                             'stage':stage['stage'],'interval_key':key(spec),'spec':spec,'features':features(spec,t['period_ps'],reference),
                             'target_roles':t['target_roles'],'delay_ps':label['data_delay_ps'],'comb_area_um2':area,
                             'path_slack_ps':label['slack_ps'],'observed_H_ps':t['period_ps']-label['data_delay_ps']-label['slack_ps'],
                             'whole_setup_slack_ps':stage['setup_worst_slack_ps'],'whole_hold_slack_ps':stage['hold_worst_slack_ps'],
                             'capture_DFFs':capture,'launch_DFFs':launch,'bank_counts':banks.get(spec['id'],{}),
                             'source_sha256':t['rtl_sha256'],'manifest_sha256':sha(mp),'contract_sha256':t['sample_contract_sha256'],
                             'points_sha256':label['points_sha256'],'profile_sha256':t['profile_sha256'],'period_ps':t['period_ps'],'abc_target_ps':1500})
    return {'version':'arithmetic-target-load-dataset-v1','mode':mode,'plan_path':str(plan_path.resolve()),'plan_sha256':sha(plan_path),
            'protocol_sha256':sha(CONFIG),'reference_sha256':p['reference_sha256'],'expected_task_ids':[t['id'] for t in tasks],
            'rows':rows,'failures':failures,'old_failed_test_labels_read':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['reference','prepare','successor','admit','run','extract']);parser.add_argument('--data',type=Path)
    parser.add_argument('--graphs',type=Path);parser.add_argument('--reference',type=Path);parser.add_argument('--out',type=Path)
    parser.add_argument('--folder',type=Path);parser.add_argument('--wave',type=Path);parser.add_argument('--mode')
    parser.add_argument('--limit',type=int,default=48);parser.add_argument('--selection',type=Path);parser.add_argument('--screening',type=Path)
    parser.add_argument('--predecessor',type=Path)
    args=parser.parse_args()
    if args.action=='reference':prepare_reference(args.data,args.out)
    elif args.action=='prepare':prepare(args.graphs,args.reference,args.out,args.predecessor)
    elif args.action=='successor':prepare_successor(args.predecessor,args.reference,args.out)
    elif args.action=='admit':admit(args.folder,args.mode,args.out,args.limit,args.selection,args.screening)
    elif args.action=='run':run(args.wave)
    else:exclusive(args.out,extract(args.folder,args.mode,args.selection))


if __name__=='__main__':main()
