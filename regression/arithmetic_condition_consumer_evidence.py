"""Compact step-8 software evidence, restored replay and isolated leaf fees."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse.budget import usage
from regression.arithmetic_condition_consumer import verify as replay

SOURCES=[
    'rtlzz/src/arithmetic_request.cpp','rtlzz/src/backend/arithmetic_model.cpp',
    'rtlzz/src/backend/arithmetic_condition.cpp','rtlzz/src/backend/arithmetic_condition.hpp',
    'rtlzz/src/backend/arithmetic_condition_provider.cpp','rtlzz/src/backend/arithmetic_condition_provider.hpp',
    'rtlzz/src/backend/arithmetic_condition_selection.cpp','rtlzz/src/backend/arithmetic_condition_selection.hpp',
    'rtlzz/src/backend/arithmetic_operator_query.cpp','rtlzz/src/backend/arithmetic_operator_query.hpp',
    'rtlzz/testv2/arithmetic_condition_consumer.cpp','rtlzz/docs/arithmetic-conditional-consumer.md',
    'experiments/arithmetic_dse/operator_query.py','experiments/arithmetic_dse/operator_condition_model.py',
    'regression/arithmetic_condition_consumer.py','regression/arithmetic_condition_consumer_evidence.py',
]


def publish(work,out):
    run=work/'acceptance-v5';previous=work/'acceptance-v3';inputs=work/'acceptance-v1/input'
    proof=read(run/'proof.json');sim=read(work/'simulation-v1/commands.json')[0]
    if proof['status']!='passed' or sim['exit_code'] or 'CONDITIONAL_SELECTED_RTL_PASS selections=3 cycles=160' not in Path(sim['log']).read_text():
        raise ValueError('software acceptance incomplete')
    files={}
    def add(p,name):files[name]=p.read_text()
    for p in inputs.iterdir():
        if p.is_file():add(p,'input/'+p.name)
    for name in ['consumer.json','partial-coverage.json']+[r['rtl_file'] for r in read(run/'native/consumer.json')['runs']]:add(run/'native'/name,'native/'+name)
    add(run/'proof.json','proof.json');cycle=[]
    for r in read(run/'native/consumer.json')['runs']:
        p=run/'native'/r['rtl_file'];old=previous/'native'/r['rtl_file']
        if sha(p)!=sha(old):raise ValueError('current selected RTL differs from actual simulated RTL')
        cycle.append(dict(target_ps=r['target_period_ps'],rtl_file=r['rtl_file'],sha256=sha(p)))
    files['cycle-proof.json']=json.dumps(dict(status='passed',selections=3,cycles_per_selection=160,RTL=cycle,
        simulation_command=sim,new_EDA_calls=0,full_D_ready=False),ensure_ascii=False,indent=2)+'\n'
    for name in ('cycles.sv','cycles-tb.sv','cycles.hex'):add(previous/name,'cycles/'+name)
    identities={name:sha(ROOT/name) for name in SOURCES}
    for name in SOURCES:add(ROOT/name,'source/'+name)
    reservation_ids=set()
    for path in sorted(work.glob('*/commands.json')):
        records=read(path)
        for record in records:
            reservation_ids.add(record['budget_reservation_id'])
            for field in ('log','gnu_time'):
                if record.get(field):
                    p=Path(record[field]);add(p,'support/'+path.parent.name+'/'+p.name)
        add(path,'support/'+path.parent.name+'/commands.json')
    ledger=read(ROOT/'experiments/arithmetic/backend_usage.json');entries=[e for e in ledger['entries'] if e['id'] in reservation_ids]
    # Publication itself may still be reserved here; closure is written after
    # verification. All earlier failed leaves remain in this exact subset.
    own_usage=usage(entries)
    if any(own_usage[s] for s in ('synth','grt','final')):raise ValueError('interface task unexpectedly launched physical optimization')
    files['resource-snapshot.json']=json.dumps(dict(entries=entries,usage=own_usage,
        subset_rule='exact reservation IDs from this task leaf command records; concurrent collection excluded'),ensure_ascii=False,indent=2)+'\n'
    collection=Path('/home/zyrv/vulsim-artifacts/operator-conditional-20261110');pointer=read(collection/'active-collection.json');cfg=read(collection/pointer['path'])
    for name,h in cfg['measurement_sources'].items():
        if sha(ROOT/name)!=h:raise ValueError('background measurement dependency changed '+name)
    progress=read(collection/'progress.json')
    files['background-checkpoint.json']=json.dumps(dict(phase=progress['phase'],points=progress['completed_points'],batch=progress['current_batch'],
        active_collection_sha256=pointer['sha256'],frozen_measurement_files_checked=len(cfg['measurement_sources']),measurement_sources_unchanged=True,
        locked_test_started=progress['independent_test_started']),indent=2)+'\n'
    raw=json.dumps(files,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode();compressed=gzip.compress(raw,compresslevel=9,mtime=0)
    out.mkdir(parents=True,exist_ok=False);chunks={}
    for n,start in enumerate(range(0,len(compressed),512*1024)):
        p=out/f'pool-{n:03d}.json.gz.part';p.write_bytes(compressed[start:start+512*1024]);chunks[p.name]=dict(sha256=sha(p),bytes=p.stat().st_size)
    write(out/'manifest.json',dict(version='conditional-consumer-evidence-v1',mode='TEST_ONLY',chunks=chunks,payload_sha256=hashlib.sha256(raw).hexdigest(),
        source_sha256=identities,proof_sha256=sha(run/'proof.json'),new_EDA_calls=0,full_D_ready=False))
    write(out/'software-proof.json',proof)
    (out/'README.md').write_text('# 第8步条件模型消费软件证据\n\n'
        '当前44视图、3目标、2064查询及18项负控通过，三份入选RTL各160周期通过。参数、S/边界价格及formal-schema-fixture均仅为软件夹具，不是物理独立验收。'
        '现有公共请求/CostProvider可加载第5步正式函数；完整生产选择仍需要第6—7步合格的S/shared/完整边界实现。\n\n'
        '分块池含源码、公共生成源码/完整BEIR视图、软件参数、当前消费报告、入选RTL、独立Python proof、实际仿真输入/记录和支持叶失败。'
        '资源按本任务命令记录的准确reservation ID提取，并行后台采集费用不混入本任务统计；全局Ledger原记录保留。\n\n'
        '在共享Ledger支持叶中执行 `python3 -B regression/arithmetic_condition_consumer_evidence.py verify --out '+str(out.relative_to(ROOT))+'`，会实际恢复全部文件，核对源码，并重新进行独立Python Query/DAG/归属/选择/RTL哈希检查。不会启动EDA。\n')
    if sum(p.stat().st_size for p in out.iterdir())>5*1024**2 or any(p.stat().st_size>1024**2 for p in out.iterdir()):raise ValueError('evidence size limit exceeded')
    print(dict(status='published',bytes=sum(p.stat().st_size for p in out.iterdir()),chunks=len(chunks),files=len(files)),flush=True)


def verify(out):
    m=read(out/'manifest.json');parts=[]
    for name,record in m['chunks'].items():
        p=out/name
        if sha(p)!=record['sha256'] or p.stat().st_size!=record['bytes']:raise ValueError('evidence chunk corrupted')
        parts.append(p.read_bytes())
    raw=gzip.decompress(b''.join(parts))
    if hashlib.sha256(raw).hexdigest()!=m['payload_sha256']:raise ValueError('evidence payload corrupted')
    files=json.loads(raw)
    for name,h in m['source_sha256'].items():
        if hashlib.sha256(files['source/'+name].encode()).hexdigest()!=h or sha(ROOT/name)!=h:raise ValueError('frozen source mismatch '+name)
    with tempfile.TemporaryDirectory(prefix='conditional-consumer-replay-') as tmp:
        tree=Path(tmp)
        for name,value in files.items():
            p=Path(name)
            if p.is_absolute() or '..' in p.parts:raise ValueError('invalid restored path')
            target=tree/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(value)
            if target.read_text()!=value:raise ValueError('actual restored bytes differ')
        expected=read(tree/'proof.json');(tree/'proof.json').unlink();replay(tree)
        if read(tree/'proof.json')!=expected:raise ValueError('restored independent replay differs')
        cycles=read(tree/'cycle-proof.json')
        if cycles['status']!='passed' or len(cycles['RTL'])!=3:raise ValueError('cycle evidence missing')
        for row in cycles['RTL']:
            if sha(tree/'native'/row['rtl_file'])!=row['sha256']:raise ValueError('simulated RTL identity differs')
    print('CONDITIONAL_CONSUMER_EVIDENCE_RESTORE_AND_REPLAY_PASS',flush=True)


def closure(work,out):
    ledger=read(ROOT/'experiments/arithmetic/backend_usage.json');ids=set()
    for path in work.glob('*/commands.json'):
        for record in read(path):ids.add(record['budget_reservation_id'])
    entries=[e for e in ledger['entries'] if e['id'] in ids]
    if len(entries)!=len(ids) or any(e['status']=='reserved' for e in entries):raise ValueError('task leaves not settled')
    write(out/'resource-closure.json',dict(version='conditional-consumer-resource-closure-v1',entries=entries,usage=usage(entries),
        failures_preserved=[e['id'] for e in entries if e.get('exit_code')],concurrent_collection_excluded=True,
        global_entries=len(ledger['entries']),global_closure_claimed=False,
        comment='Background collection still owns live leases; only this interface task is settled. This read-only bookkeeping leaf is closed by its outer command record.'))
    print(dict(status='task_leaves_settled',entries=len(entries),usage=usage(entries)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('publish','verify','closure'));p.add_argument('--work',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.action=='verify':verify(a.out.resolve())
    else:{'publish':publish,'closure':closure}[a.action](a.work.resolve(),a.out.resolve())
