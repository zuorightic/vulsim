"""Bounded formal operator batches, immutable roles, real archive restoration.

This is an outer controller. EDA/support leaves retain their existing Ledger
charges; controller waiting and scheduling are not charged a second time.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile

from .model_fast_preflight import read,write,sha,key
from . import operator_collection as collect
from .budget import Ledger,POLICY,usage
from .processes import run_command

ROOT=Path(__file__).resolve().parents[2]
FIT_CONFIG=ROOT/'experiments/arithmetic_dse/configs/operator_condition_fit_v1.json'
PARENT=ROOT/'experiments/arithmetic/evidence/step7_steps123_v2'
ARC=ROOT/'experiments/arithmetic/evidence/step7_steps123_v3'
DEFAULT=Path('/home/zyrv/vulsim-artifacts/operator-conditional-20261110')


def atomic(path,value):
    temp=path.with_suffix(path.suffix+'.tmp');write(temp,value);os.replace(temp,path)


def support(root,name,command,timeout=300):
    out=root/'support'/name;out.mkdir(parents=True,exist_ok=False)
    ledger=Ledger();ctx=dict(target_platform='asap7',admission_id=root.name+'-stage4',task_id=name)
    with ledger.job(ctx):
        r=ledger.reserve(None,timeout,4,'operator_stage4_support',command,out/name,context=ctx)
        env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='4',OMP_NUM_THREADS='4')
        record=run_command(command,out,name,timeout,env,8192,cpu_limit_s=r['CPU_time_s']);ledger.finish(r,record)
        write(out/'commands.json',[dict(**record,budget_reservation_id=r['id'])])
    if record['exit_code']:raise ValueError('paid support failed '+record['log'])
    return record


def inventory(root):
    return {str(p.relative_to(root)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in root.rglob('*') if p.is_file()}


def archive(root,paths,name):
    """Archive regular contents, then restore and hash every original member."""
    root=root.resolve();target=root/'archives'/name;target.parent.mkdir(exist_ok=True)
    if target.exists():raise ValueError('archive already exists; never overwrite')
    members={}
    for path in paths:
        if path.is_dir():
            for p in path.rglob('*'):
                # Point source is a shared directory link, archived once below.
                if p.is_file():members[str(p.relative_to(root))]=p
        else:members[str(path.relative_to(root))]=path
    index={name:dict(sha256=sha(p),bytes=p.stat().st_size) for name,p in members.items()}
    with target.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as compressed:
            with tarfile.open(fileobj=compressed,mode='w|',dereference=True) as bundle:
                for name,p in sorted(members.items()):bundle.add(p,arcname=name,recursive=False)
    with tempfile.TemporaryDirectory(prefix='restore-',dir=root/'restore') as d:
        restored=Path(d)
        with tarfile.open(target,'r:gz') as bundle:
            for member in bundle:
                if not member.isfile() or member.name not in index or Path(member.name).is_absolute() or '..' in Path(member.name).parts:raise ValueError('unexpected archive member')
                dest=restored/member.name;dest.parent.mkdir(parents=True,exist_ok=True)
                with bundle.extractfile(member) as stream,dest.open('wb') as out:shutil.copyfileobj(stream,out)
        if inventory(restored)!=index:raise ValueError('actual archive restoration differs')
    receipt=dict(version='operator-full-artifact-restore-v1',status='passed',archive=str(target),archive_sha256=sha(target),archive_bytes=target.stat().st_size,
        logical_bytes=sum(v['bytes'] for v in index.values()),members=index,actual_restore_and_every_member_hash_checked=True,
        storage_class='explicit retained local on-disk artifact directory; same-disk failure is not covered',retention='retain until explicit user cleanup',
        no_raw_artifacts_deleted=True)
    write(target.with_suffix(target.suffix+'.index.json'),receipt)
    print('RESTORED '+name+' files='+str(len(index))+' archive_bytes='+str(receipt['archive_bytes']),flush=True)
    return receipt


def prepare(root):
    from .steps123_evidence import load
    if root.exists():raise ValueError('collection destination occupied')
    state=read(Ledger().path)
    # Preparation itself is an already reserved support leaf. The shared
    # Ledger has checked live locks; reject unreconciled jobs, not this leaf.
    if any(j['status']=='unsettled' for j in state.get('jobs',[])):raise ValueError('resources unsettled')
    settled=state['entries'][:next((i for i,e in enumerate(state['entries']) if e['status']=='reserved'),len(state['entries']))]
    fixed=read(ARC/'manifest.json')
    for name in ('experiments/arithmetic_dse/model_physical_labels_v2.py','experiments/arithmetic_dse/model_physical_path_v2.py'):
        if sha(ROOT/name)!=fixed['source_sha256'][name]:raise ValueError('strict Liberty reader not active')
    _,pool=load(PARENT);root.mkdir(parents=True);(root/'restore').mkdir();(root/'archives').mkdir()
    for name,h in pool['files'].items():
        if name.startswith('corpus/'):
            data=pool['blobs'][h].encode();p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            if sha(p)!=h:raise ValueError('immutable corpus changed during recovery')
    corpus=root/'corpus';manifest=read(corpus/'manifest.json');roles={r['source_group']:r['role'] for r in manifest['sources']}
    if len(roles)!=58:raise ValueError('source role inventory differs')
    for row in manifest['sources']:
        if row['role']!='locked_test':collect.next_request(corpus,row['id'],[])
    paths=collect.measurement_sources()+[str(Path(__file__).relative_to(ROOT)),str(FIT_CONFIG.relative_to(ROOT))]
    freeze=root/'measurement-source';hashes={}
    for name in sorted(set(paths)):
        p=freeze/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,p);hashes[name]=sha(p)
    write(root/'source-freeze.json',hashes)
    shutil.copy2(FIT_CONFIG,root/'fit-protocol.json')
    (root/'README.md').write_text('# Retained conditional-operator experiment artifacts\n\n'
        'Explicit local persistent collection directory, outside build/cache. Retain raw outputs, admissions, failures and verified archives until user explicitly requests cleanup.\n'
        'Archives are actually restored and every member hash is checked. This is same-disk local retention, not off-machine backup.\n'
        'Old not_training diagnostics and consumed test data are excluded; all source periods inherit their immutable role.\n')
    later=read(corpus/'protocol.json')['later_work_reserved'];limits=read(POLICY)['resources'];u=usage(state['entries'])
    if (u['synth']+12+later['synth']>limits['max_synthesis_calls'] or u['grt']+12+later['grt']>limits['max_global_route_calls']
        or u['walltime_s']+35280+later['walltime_s']>limits['max_global_walltime_h']*3600
        or u['CPU_time_s']+141120+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600
        or shutil.disk_usage(root).free<later['storage_bytes']+8*1024**3):raise ValueError('first batch not funded')
    write(root/'collection.json',dict(version='operator-stage4-collection-v1',id=root.name,created_at=datetime.now(timezone.utc).isoformat(),
        source_manifest_sha256=sha(corpus/'manifest.json'),protocol_sha256=sha(corpus/'protocol.json'),fit_protocol_sha256=sha(root/'fit-protocol.json'),
        measurement_sources=hashes,qualification_proof_path=str(ARC/'verification.json'),qualification_proof_sha256=sha(ARC/'verification.json'),
        source_counts=dict(train=30,validation=14,locked_test=14),batch_source_targets_max=12,parallel_jobs=3,threads_per_tool=4,
        initial_roles=['train','validation'],locked_test_requires_selection_freeze=True,per_source_target_cap=13,
        target_ceiling=754,ceiling_is_not_blanket_admission=True,automatic_retries=0,later_work_reserved=later,
        storage=dict(destination=str(root),retention='until explicit user cleanup',same_disk_local_only=True,
            measured_working_bytes_per_point_ceiling=391451120,first_batch_max_additional_bytes=8*1024**3,
            shared_sources_once_per_collection=True,archive_restore_after_every_batch=True,raw_and_archives_both_retained=True),
        baseline_entries=len(settled),baseline_usage=usage(settled),baseline_entries_sha256=key(settled),full_D_ready=False))
    atomic(root/'progress.json',dict(phase='prepared',batches=[],completed_points=0,errors=[],independent_test_started=False))
    archive(root,[root/'corpus',freeze,root/'source-freeze.json',root/'fit-protocol.json',root/'collection.json',root/'README.md'],'initial-source-freeze.tar.gz')
    print('PREPARED formal source roles58; first roles train/validation; independent test locked',flush=True)


def verify_sources(root):
    active=root/'active-collection.json'
    if active.exists():
        pointer=read(active);path=root/pointer['path']
        if sha(path)!=pointer['sha256']:raise ValueError('collection amendment changed')
        cfg=read(path)
    else:cfg=read(root/'collection.json')
    freeze=root/cfg.get('source_freeze_directory','measurement-source')
    for name,h in cfg['measurement_sources'].items():
        if sha(ROOT/name)!=h or sha(freeze/name)!=h:raise ValueError('measurement source freeze drift '+name)
    if sha(root/'corpus/manifest.json')!=cfg['source_manifest_sha256']:raise ValueError('role manifest drift')
    return cfg


def amend(root):
    """Explicit source-freeze repair; retain paid outputs and prelaunch failures."""
    progress=read(root/'progress.json')
    if progress['phase']!='stopped_on_error':raise ValueError('one diagnosed stopped batch required')
    state=read(Ledger().path)
    if any(j['status']=='unsettled' for j in state.get('jobs',[])):raise ValueError('unsettled physical work')
    active=root/'active-collection.json';old=read(root/read(active)['path']) if active.exists() else read(root/'collection.json')
    changes=root/'amendments';changes.mkdir(exist_ok=True)
    number=1+max([0]+[int(p.name.rsplit('-',1)[1]) for p in root.glob('measurement-source-amendment-*')])
    freeze=root/('measurement-source-amendment-'+str(number));hashes={}
    for name in sorted(set(collect.measurement_sources()+[str(Path(__file__).relative_to(ROOT)),str(FIT_CONFIG.relative_to(ROOT)),
            'experiments/arithmetic_dse/operator_point_continue.py'])):
        dest=freeze/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest);hashes[name]=sha(dest)
    preserved=[];recoveries=dict(old.get('inherit_synth_by_source',{}))
    for error in progress['errors']:
        if error['error']!='shared measurement source freeze changed':continue
        point=root/'raw'/error['source']/('target-'+str(error['target_ps']))
        if not point.exists():continue
        history=point.parent/'history.json'
        if history.exists() and any(r['SDC_ps']==error['target_ps'] and r['status']=='completed' for r in read(history)):continue
        if (point/'admission.json').exists() or (point/'runs').exists():raise ValueError('cannot treat a physical attempt as prelaunch repair')
        task=error['source']+'-T'+str(error['target_ps'])
        if any(e.get('task_id')==task for e in state['entries']):raise ValueError('prelaunch task already has paid leaves')
        target=root/'prelaunch-failures'/('amendment-'+str(number)+'-'+task);target.parent.mkdir(exist_ok=True);point.rename(target)
        preserved.append(dict(source=str(point),preserved=str(target),paid_physical_calls=0))
    for error in progress['errors']:
        if error['error']!='logical FF output driven by arithmetic instead of storage':continue
        statepath=root/'raw'/error['source'];t=error['target_ps'];point=statepath/('target-'+str(t));task=error['source']+'-T'+str(t)
        if not point.exists():continue
        if (statepath/'history.json').exists() and any(r['SDC_ps']==t and r['status']=='completed' for r in read(statepath/'history.json')):continue
        previous=point/'runs'/task;m=read(previous/'manifest.json')
        if m['status']!='completed' or [r['stage'] for r in m['metrics']]!=['synth'] or (previous/'grt.command.json').exists():raise ValueError('only exact successful synth before grt can continue')
        from .model_mapped_contract import mapped_contract
        source=next(r for r in read(root/'corpus/manifest.json')['sources'] if r['id']==error['source'])
        mapped_contract(read(previous/'mapped.json'),source['features'],read(previous/'liberty-pins.json'))
        before={str(p.relative_to(previous)):sha(p) for p in (previous/'results/asap7/arithmetic_probe/base').iterdir() if p.is_file()}
        target=root/'reader-stops'/('amendment-'+str(number)+'-'+task);target.parent.mkdir(exist_ok=True);statepath.rename(target)
        parent=target/point.name/'runs'/task
        recoveries[error['source']]=dict(directory=str(parent),manifest_sha256=sha(parent/'manifest.json'),files_sha256=before,
            original_failed_history_sha256=sha(target/'history.json'),source_role=source['role'],target_ps=t,
            reason='actual Liberty constant TIE output resolved by declared function; same successful synthesis inherited, no physical repeat')
    for error in progress['errors']:
        if error['error']!='qualification synth failed':continue
        statepath=root/'raw'/error['source'];t=error['target_ps'];point=statepath/('target-'+str(t));task=error['source']+'-T'+str(t)
        if not point.exists():continue
        history=read(statepath/'history.json')
        if any(r['SDC_ps']==t and r['status']=='completed' for r in history):continue
        previous=point/'runs'/task;m=read(previous/'manifest.json')
        if m.get('failure_code')!='sdc_contract_mismatch' or not ('period' in m.get('failure_reason','').lower() and 'rounding' in m.get('failure_reason','').lower() or m.get('failure_reason','').startswith('SDC period mismatch:')):
            raise ValueError('physical synth failure is not a serialized-period recovery')
        if read(previous/'synth.command.json')['exit_code'] or (previous/'grt.command.json').exists():raise ValueError('actual synth stage did not succeed')
        for name,h in m['evidence_sha256'].items():
            if sha(previous/name)!=h:raise ValueError('failed post-synth checkpoint changed')
        from .model_fast_sdc_v2 import verify_sdc,rtl_ports
        from .platforms import profile
        verify_sdc((previous/'results/asap7/arithmetic_probe/base/1_synth.sdc').read_text(),profile('asap7'),t,rtl_ports((previous/'input.sv').read_text(),'ModelBundle'))
        before={str(p.relative_to(previous)):sha(p) for p in (previous/'results/asap7/arithmetic_probe/base').iterdir() if p.is_file()}
        target=root/'reader-stops'/('SDC-amendment-'+str(number)+'-'+task);target.parent.mkdir(exist_ok=True);point.rename(target)
        saved_history=target/'failed-history.json';(statepath/'history.json').rename(saved_history)
        if not history or history[-1]['SDC_ps']!=t or history[-1]['status']!='failed':raise ValueError('exact failed suffix history required')
        write(statepath/'history.json',history[:-1]);parent=target/'runs'/task
        recoveries[error['source']]=dict(directory=str(parent),manifest_sha256=sha(parent/'manifest.json'),files_sha256=before,
            original_failed_history_sha256=sha(saved_history),source_role=history[-1]['role'],target_ps=t,
            reason='exact binary32-second plus decimal period serialization; successful synth reused; no target/IO/uncertainty change')
    cfg={**old,'measurement_sources':hashes,'source_freeze_directory':freeze.name,
        'amendment_reason':'explicit metadata/reader/source-freeze continuation; no completed measurement repeated',
        'parent_collection_sha256':sha(root/'collection.json'),'prelaunch_failures_preserved':preserved}
    cfg['inherit_synth_by_source']=recoveries
    progress['completed_points']=sum(sum(r['status']=='completed' for r in read(path)) for path in (root/'raw').glob('*/history.json'))
    path=changes/f'amendment-{number:03d}.json';write(path,cfg)
    recovered_points=list({p.parent for p in (root/'raw').glob('*/target-*/reader-continuation-*.json')})
    archive(root,[freeze,path]+recovered_points+[p.parent/'history.json' for p in recovered_points],'amendment-'+str(number)+'-source-freeze.tar.gz')
    atomic(root/'active-collection.json',dict(path=str(path.relative_to(root)),sha256=sha(path)))
    progress.update(phase='explicit_amendment_ready');progress.setdefault('amendments',[]).append(dict(path=str(path),sha256=sha(path),no_physical_retry=True));atomic(root/'progress.json',progress)
    print('AMENDMENT_FROZEN preserved paid points; explicit reader/source continuation',flush=True)


def decisions(root,roles,selection=None):
    rows=read(root/'corpus/manifest.json')['sources'];result=[]
    # Start with a large full Mul and Add, then cover all sources round-robin.
    for row in rows:
        if row['role'] not in roles:continue
        state=root/'raw'/row['id'];history=read(state/'history.json') if (state/'history.json').exists() else []
        d=collect.next_request(root/'corpus',row['id'],history,selection)
        if d['decision']['next_request'] is not None:result.append((len(history),row,state,d['decision']['next_request']))
    result.sort(key=lambda item:(item[0],-(item[1]['features']['producer']['lhs_width']*item[1]['features']['producer']['rhs_width']),item[1]['id']))
    return result


def run(root,mode='fitting',selection=None,max_batches=None):
    cfg=verify_sources(root);roles=['train','validation'] if mode=='fitting' else ['locked_test']
    if mode!='fitting' and selection is None:raise ValueError('independent model freeze required')
    progress=read(root/'progress.json');count=0
    if progress['phase']=='running':raise ValueError('previous controller did not settle; reconcile explicitly')
    while True:
        verify_sources(root);pending=decisions(root,roles,selection)
        if not pending:
            progress.update(phase=mode+'_collection_complete');atomic(root/'progress.json',progress);break
        if max_batches is not None and count>=max_batches:
            progress.update(phase=mode+'_bounded_batch_complete');atomic(root/'progress.json',progress);break
        batchno=len(progress['batches']);name=f'batch-{batchno:03d}';b=root/'batches'/name;b.mkdir(parents=True,exist_ok=False)
        # First three paid targets also check capacity of exact formal sources.
        selected=pending[:3 if batchno==0 else 12];later=cfg['later_work_reserved'];n=len(selected)
        u=usage(read(Ledger().path)['entries']);limits=read(POLICY)['resources']
        if (u['synth']+n+later['synth']>limits['max_synthesis_calls'] or u['grt']+n+later['grt']>limits['max_global_route_calls']
            or u['walltime_s']+2940*n+later['walltime_s']>limits['max_global_walltime_h']*3600
            or u['CPU_time_s']+11760*n+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600
            or shutil.disk_usage(root).free<later['storage_bytes']+n*391451120+1024**3):raise ValueError('exact batch is not funded; no launch')
        release=dict(version='operator-stage4-admission-v1',physical_admission_allowed=True,source_manifest_sha256=cfg['source_manifest_sha256'],
            measurement_source_sha256=cfg['measurement_sources'],qualification_proof_path=cfg['qualification_proof_path'],qualification_proof_sha256=cfg['qualification_proof_sha256'],
            independent_test_allowed=mode!='fitting',source_target_requests=[dict(source_id=r['id'],role=r['role'],SDC_ps=q['SDC_ps'],ABC_ps=q['ABC_ps']) for _,r,_,q in selected],
            inherit_synth_by_source=cfg.get('inherit_synth_by_source',{}),
            batch_storage_bytes=n*391451120,batch_timeout_wall_s=2940*n,batch_timeout_CPU_s=11760*n,later_work_reserved=later,
            verified_initial_restore_sha256=sha(root/'archives/initial-source-freeze.tar.gz.index.json'))
        write(b/'admission.json',release);progress.update(phase='running',current_batch=name,independent_test_started=mode!='fitting');atomic(root/'progress.json',progress)
        errors=[];done=[]
        def execute(item):
            _,row,state,q=item
            collect.execute_next(root/'corpus',row['id'],state,b/'admission.json',selection)
            return state/('target-'+str(q['SDC_ps']))
        with ThreadPoolExecutor(max_workers=3) as workers:
            futures={workers.submit(execute,item):item for item in selected}
            for future in as_completed(futures):
                item=futures[future];_,row,state,q=item
                try:
                    point=future.result();done.append(point);progress['completed_points']+=1
                    print('POINT_COMPLETE '+row['role']+' '+row['id']+' T='+str(q['SDC_ps'])+' total='+str(progress['completed_points']),flush=True)
                except Exception as e:
                    errors.append(dict(source=row['id'],target_ps=q['SDC_ps'],error=str(e)))
                    print('POINT_FAILED '+row['id']+' '+str(e),flush=True)
                atomic(root/'progress.json',progress)
        write(b/'results.json',dict(completed=[str(p) for p in done],errors=errors))
        paths=[b]+[state/('target-'+str(q['SDC_ps'])) for _,row,state,q in selected if (state/('target-'+str(q['SDC_ps']))).exists()]
        paths += [state/'history.json' for _,_,state,_ in selected if (state/'history.json').exists()]
        support(root,'archive-'+name,[sys.executable,'-B','-m','experiments.arithmetic_dse.operator_stage4','archive','--root',str(root),'--batch',name],300)
        progress['batches'].append(dict(name=name,source_targets=n,completed=len(done),errors=errors));progress['errors']+=errors
        progress.update(phase='batch_settled');atomic(root/'progress.json',progress);count+=1
        print('BATCH_SETTLED '+name+' completed='+str(len(done))+' errors='+str(len(errors)),flush=True)
        if errors:
            progress.update(phase='stopped_on_error');atomic(root/'progress.json',progress);raise ValueError('batch failure preserved; explicit diagnosis before continuation')
    print(json.dumps(dict(phase=progress['phase'],completed_points=progress['completed_points'],batches=len(progress['batches']),errors=len(progress['errors']))),flush=True)


def archive_batch(root,name):
    b=root/'batches'/name;release=read(b/'admission.json');paths=[b]
    for r in release['source_target_requests']:
        state=root/'raw'/r['source_id'];point=state/('target-'+str(r['SDC_ps']))
        if point.exists():paths.append(point)
        if (state/'history.json').exists():paths.append(state/'history.json')
    archive(root,paths,name+'.tar.gz')


if __name__=='__main__':
    import sys
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','run','archive','amend'));p.add_argument('--root',type=Path,default=DEFAULT)
    p.add_argument('--mode',choices=('fitting','independent'),default='fitting');p.add_argument('--selection',type=Path);p.add_argument('--max-batches',type=int);p.add_argument('--batch');a=p.parse_args();root=a.root.resolve()
    if a.action=='prepare':prepare(root)
    elif a.action=='archive':archive_batch(root,a.batch)
    elif a.action=='amend':amend(root)
    else:run(root,a.mode,a.selection.resolve() if a.selection else None,a.max_batches)
