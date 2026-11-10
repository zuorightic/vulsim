"""Compact incremental acceptance with independent restoration, no EDA."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse.budget import Ledger,usage


def pack(root,work,out):
    if out.exists():raise ValueError('preserve evidence version')
    proof=read(work/'physical-replay-v2/proof.json')
    if proof['status']!='passed' or len(proof['points'])!=6:raise ValueError('physical replay incomplete')
    files={};external={}
    def include(path,name):files[name]=path.read_text()
    def add(name,value):files[name]=json.dumps(value,sort_keys=True,separators=(',',':'))+'\n'
    def ext(path):external[str(path)]=dict(sha256=sha(path),bytes=path.stat().st_size)
    # Frozen import closure; later live work cannot silently replace the replay.
    for path in (ROOT/'experiments/arithmetic_dse').glob('*.py'):
        include(path,str(path.relative_to(ROOT)))
    for path in (ROOT/'experiments/arithmetic_dse/configs').rglob('*.json'):
        include(path,str(path.relative_to(ROOT)))
    for name in ('arithmetic_incremental_acceptance.py','arithmetic_incremental_protocol.py','arithmetic_incremental_physical.py',
                 'arithmetic_incremental_evidence.py','arithmetic_steps123.py','arithmetic_physical_label_contract.py','arithmetic_liberty_arc_contract.py'):
        include(ROOT/'regression'/name,'regression/'+name)
    for name in ('experiments/__init__.py','experiments/arithmetic_dse/__init__.py','regression/__init__.py'):
        if (ROOT/name).exists():include(ROOT/name,name)
    required=read(ROOT/'experiments/arithmetic_dse/configs/operator_condition_fit_v2.json')['required_freeze_sources']
    for name in required:include(ROOT/name,name)
    for path in (work/'feature-vectors-v2').glob('*.json'):
        include(path,'vectors/'+path.name)
    for name in ('gates-v1/proof.json','admission-checks-v1/proof.json','sampler-proof-v4.json','physical-replay-v2/proof.json','pilot.json'):
        include(work/name,'proofs/'+name.replace('/','-'))
    for path in work.glob('*/commands.json'):include(path,'receipts/'+path.parent.name+'.json')
    for name in ('new-sources.json','corpus/manifest.json','corpus/protocol.json','collection.json','active-collection.json',
        'software-admission.json','software-admission-v2.json','active-software-admission.json','steps123-addendum-v2.json',
        'fit-protocol.json','fit-protocol-v2.json','progress.json'):
        include(root/name,'collection/'+name)
    for path in (root/'amendments').glob('*.json'):include(path,'collection/amendments/'+path.name)
    software=ROOT/'build/step7-operator-wide-20261110/software'
    for path in software.glob('*'):
        if path.is_file() and path.name!='sim':include(path,'bank-software/'+path.name)
    archive_refs=[]
    for path in (root/'archives').glob('*.index.json'):
        receipt=read(path)
        if receipt['status']!='passed' or not receipt['actual_restore_and_every_member_hash_checked']:raise ValueError('restore failed')
        if sha(Path(receipt['archive']))!=receipt['archive_sha256']:raise ValueError('retained archive changed')
        archive_refs.append({k:v for k,v in receipt.items() if k!='members'}|dict(index_sha256=sha(path),member_count=len(receipt['members'])))
        ext(path)
    from experiments.arithmetic_dse.model_mapped_contract import mapped_contract,operator_port_contract
    suffix=Path('asap7/arithmetic_probe/base')
    for point in proof['points']:
        path=Path(point['directory']);prefix='collection/'+str(path.relative_to(root))+'/'
        include(path.parents[2]/'history.json','collection/'+str((path.parents[2]/'history.json').relative_to(root)))
        for name in ('input.sv','mapped-contract.json','operator-port-contract.json','liberty-pins.json','query-contract.json',
                     'synth-labels.json','grt-labels.json','manifest.json','synth.command.json','grt.command.json'):
            include(path/name,prefix+name)
        design=read(path/'mapped.json');pins=read(path/'liberty-pins.json');top=design['modules']['ModelBundle']
        projected={'modules':{'ModelBundle':dict(cells=top['cells'],ports=top['ports'])}}
        for cell in top['cells'].values():
            typ=cell['type']
            if typ not in design['modules']:continue
            m=design['modules'][typ];children={}
            for name,c in m.get('cells',{}).items():
                outputs={p:b for p,b in c['connections'].items() if pins[c['type']]['pins'].get(p,{}).get('direction')=='output'}
                children[name]=dict(type=c['type'],connections=c['connections'] if typ in (top['cells']['launch']['type'],top['cells']['capture']['type']) else outputs)
            projected['modules'][typ]=dict(ports=m['ports'],cells=children)
        if mapped_contract(projected, next(r['features'] for r in read(root/'new-sources.json')['sources'] if r['id']==point['source']),pins)!=read(path/'mapped-contract.json'):
            raise ValueError('semantic projection lost state evidence')
        add(prefix+'mapped.json',projected)
        for p in (path/'reports'/suffix).iterdir():
            if p.is_file() and p.name.startswith(('context_','vulsim_')) and p.suffix!='.v':include(p,prefix+'reports/'+str(suffix/p.name))
        cec=path/'logs'/suffix/'structural_cec';receipt=read(cec/'proof.json')
        for name in ['proof.json','cec.log','state-correspondence.json']+['negative-'+c+'.log' for c in receipt['negative_controls']]:
            include(cec/name,prefix+'logs/'+str(suffix/'structural_cec'/name))
        for p in path.rglob('*'):
            if p.is_file():ext(p)
    # Scope fees by exact receipt IDs / the three new point roots, not global slices.
    ids={r['budget_reservation_id'] for p in work.glob('*/commands.json') for r in read(p)}
    new_prefixes=[str(root/'raw'/r['source_id']/('target-'+str(r['SDC_ps'])))+'/' for r in read(work/'pilot.json')['requests']]
    archive_prefix=str(root/'support/archive-batch-001')+'/'
    entries=[e for e in read(Ledger().path)['entries'] if e['id'] in ids or any(str(e.get('output','')).startswith(p) for p in new_prefixes+[archive_prefix])]
    if any(e['status']=='reserved' for e in entries):raise ValueError('scoped fee unsettled')
    add('fees/entries.json',entries)
    resource=dict(status='settled_snapshot_before_pack',entries=len(entries),usage=usage(entries),
        includes_failed_support_attempts=True,global_ledger_not_claimed_closed=True,
        pack_restore_publication_leaves_settled_in_following_closure=True)
    demand=read(work/'feature-vectors-v2/demand-audit.json')
    field_map=dict(operation_and_widths='local_context.producer',result_truncation='producer.result_width; result_bit_map undemanded',
        shifted_zero_padding='consumers[].bindings[].result_bit_map; producer/consumer known zero masks',
        load_and_fanout='consumers[] count; bindings per operand; mapped repeated bits; effective consumer widths and masks',
        capture='captures[] and capture_banks; actual bank aliases checked physically',
        T='flow_context.target_period_ps and abc_target_ps, numerical input',
        generalization='unseen connections in validation/new locked sources, exact1000ps reserved on new independent sources',
        exclusions='view/source/shape IDs are not predictors; correlated inputs require G qualification')
    summary=dict(status='passed_incremental_steps123',demand=demand,field_map=field_map,
        feature_proof=read(work/'feature-vectors-v2/feature-proof.json'),
        protocol_checks=read(work/'gates-v1/proof.json')['count'],admission_checks=7,
        new_physical_points=3,reused_wide_points=3,physical_stages=12,negative_arc_checks=24,
        physical_contexts=5,new_point_roles='train unchanged; existing validation point retained',
        test_sources_still_locked=18,stage4_and5='in progress; no v2 fit or independent evaluation',
        step6_and8_prework='retained; joint and production qualifications pending',
        clocks='500/1500/3000 planned checks; 1000 independent holdout; no continuous domain granted',
        qualification='finite observability, exclusive labels and execution protocol; no price lookup or model accuracy claim',
        retained_root=str(root),archives=archive_refs,resources=resource,full_D_ready=False)
    out.mkdir(parents=True)
    add('summary.json',summary);add('external-index.json',external)
    raw=json.dumps(dict(files=files),sort_keys=True,separators=(',',':')).encode();compressed=gzip.compress(raw,mtime=0)
    chunks={}
    for i,at in enumerate(range(0,len(compressed),512*1024)):
        name=f'pool-{i:03d}.gzpart';(out/name).write_bytes(compressed[at:at+512*1024]);chunks[name]=sha(out/name)
    write(out/'summary.json',summary)
    shutil.copy2(ROOT/'regression/arithmetic_incremental_replay.py',out/'replay.py')
    write(out/'manifest.json',dict(version='steps123-incremental-evidence-v1',chunks=chunks,
        payload_sha256=hashlib.sha256(raw).hexdigest(),members=len(files),
        source_sha256={n:hashlib.sha256(v.encode()).hexdigest() for n,v in files.items() if n.startswith(('experiments/','regression/','rtlzz/'))},
        review_sha256=sha(out/'summary.json'),replay_sha256=sha(out/'replay.py'),
        portable_scope='restored physical tables/semantic mapped projections/Liberty arc negatives; numerical feature oracle and saved native parity; frozen sampler/gate regressions',
        external_scope='full ODB/netlists and exact CEC artifacts/tools checked in local physical replay; portable package keeps conclusions/logs only',full_D_ready=False))
    (out/'README.md').write_text('# 第1—3步增量验收\n\n'
        '主线：通用小算子函数 → S边界 → DAG与必要G → 流水放置 → RTL。44候选只作需求／回归集。\n\n'
        '本包补齐消费者数值特征、后继角色／质量／时钟／资源协议和有限物理可测性。详情见summary.json，完整产物保存在`'+str(root)+'`，保留至用户清理。\n\n'
        '在共享Ledger支持叶中运行：`python3 -I -B replay.py --evidence .`。脚本独立恢复冻结源码及原始路径表；不启动EDA或模型测试。\n\n'
        '新增3 synth／3 grt；复用此前3点，合计6点12阶段。物理资格不授予预测精度、连续T、S/G联合或正式D资格。18个locked_test仍锁定。第4—5步仍需后续有限采集及v2拟合／独立验收。\n')
    size=sum(p.stat().st_size for p in out.iterdir())
    if size>5*1024**2 or any(p.stat().st_size>1024**2 for p in out.iterdir()):raise ValueError('compact evidence size exceeded')
    print(dict(status='packed',members=len(files),bytes=size,external_files=len(external)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('root','work','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();pack(a.root.resolve(),a.work.resolve(),a.out.resolve())
