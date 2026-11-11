"""Small v2 function evidence; complete physical products remain retained."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil

from .model_fast_preflight import read,write,sha

ROOT=Path(__file__).resolve().parents[2]


def publish(root,work,out):
    if out.exists():raise ValueError('preserve evidence version')
    fit=root/'fit-v2';candidate=read(fit/'candidate.json');files={};raw_identity={};labels={};datasets=[]
    def include(path,name):files[name]=path.read_text()
    for directory in ('experiments/arithmetic_dse','regression'):
        for path in (ROOT/directory).glob('*.py'):include(path,'source/'+str(path.relative_to(ROOT)))
    for path in (ROOT/'experiments/arithmetic_dse/configs').rglob('*.json'):include(path,'source/'+str(path.relative_to(ROOT)))
    for name in ('experiments/__init__.py','experiments/arithmetic_dse/__init__.py','regression/__init__.py'):
        if (ROOT/name).exists():include(ROOT/name,'source/'+name)
    for name,h in read(fit/'execution-source.json').items():
        if sha(fit/'execution-source'/name)!=h or sha(ROOT/name)!=h:raise ValueError('fit source changed before publication '+name)
        include(ROOT/name,'source/'+name)
    for name in ('fit-data.json','test-data.json','corpus/manifest.json','corpus/protocol.json','new-sources.json','collection.json','active-collection.json',
                 'progress.json','v2-work-status.json','test-acquisition-v2.json','independent-evaluation-consumed.json'):
        if (root/name).exists():include(root/name,name)
    for name in ('fit-data.json','test-data.json'):
        if not (root/name).exists():continue
        dataset=read(root/name);datasets.append(dataset)
        for row in dataset['rows']:
            path=Path(row['measurement_path'])/(row['stage']+'-labels.json');label=read(path)
            if sha(path)!=row['label_sha256'] or label['source_role']!=row['role'] or not label['physical_training_label_eligible']:
                raise ValueError('qualified physical label/role changed')
            labels[row['id']]={k:label[k] for k in ('operator_delay_ps','comb_area_um2','data_setup_slack_ps','source_role','physical_training_label_eligible','CTS_CEC_sha256')}
            raw_identity[str(path)]=dict(sha256=sha(path),bytes=path.stat().st_size)
    for directory in ('fit-v2','test-v2'):
        if (root/directory).exists():
            for path in (root/directory).rglob('*.json'):
                if 'execution-source' not in path.parts:include(path,str(path.relative_to(root)))
    for path in work.rglob('commands.json'):include(path,'receipts/'+str(path.relative_to(work)))
    for name in ('ownership-stop-audit.json','fit-preflight.json','current-preflight.json'):
        if (work/name).exists():include(work/name,'work-review/'+name)
    for directory in work.glob('diagnostic-fit-*'):
        if not directory.is_dir():continue
        for name in ('candidate.json','validation.json','execution-source.json'):
            if (directory/name).exists():include(directory/name,'work-review/'+directory.name+'/'+name)
        for name in ('experiments/arithmetic_dse/operator_condition_fit_v2.py','regression/arithmetic_condition_v2.py'):
            path=directory/'execution-source'/name
            if path.exists():include(path,'work-review/'+directory.name+'/execution-source/'+name)
    for path in (root/'controller-attempts').rglob('*.json'):
        include(path,str(path.relative_to(root)))
    for directory in work.glob('stage7-preparation*'):
        for path in directory.glob('*.json'):include(path,directory.name+'/'+path.name)
    archives=[]
    for path in sorted((root/'archives').glob('*.index.json')):
        r=read(path)
        if r['status']!='passed' or not r['actual_restore_and_every_member_hash_checked']:raise ValueError('physical archive restoration incomplete')
        archives.append({k:v for k,v in r.items() if k!='members'}|dict(index_sha256=sha(path),member_count=len(r['members'])))
    validation=read(fit/'validation.json');test=read(root/'test-v2/independent-test.json') if (root/'test-v2/independent-test.json').exists() else None
    summary=dict(version='operator-condition-v2-review-v1',validation_status=validation['status'],independent_status=test['status'] if test else 'not_consumed',
        fitting_points=sum(r['stage']=='grt' for r in read(root/'fit-data.json')['rows']),
        independent_points=sum(r['stage']=='grt' for r in read(root/'test-data.json')['rows']) if (root/'test-data.json').exists() else 0,
        validation={op:{k:r[k] for k in ('delay','area','selected_delay','selected_area','source_counts','validation_subdomains','clock_validation')} for op,r in validation['operations'].items()},
        support_method=validation['selected_support'],demand=[{k:t[k] for k in ('target_ps','contexts','covered_contexts','views','covered_views')} for t in validation['demand']['targets']],
        independent_operations=test['operations'] if test else None,model_sha256=sha(fit/'candidate.json'),
        published_model=str(root/'test-v2/tested-model.json') if test else None,
        physical_archive_restore_receipts=archives,retained_physical_root=str(root),raw_labels_replayed_at_final_extraction=all(d['raw_labels_replayed'] for d in datasets),
        portable_scope='qualified scalar labels and immutable identities, feature/prediction/statistics replay; complete physical path tables, ODB and CEC artifacts retained externally',
        source_and_view_ids_not_predictors=True,S_G_joint_qualification=False,full_D_ready=False)
    pool=dict(files=files,qualified_scalar_labels=labels,raw_identity=raw_identity)
    raw=json.dumps(pool,sort_keys=True,separators=(',',':')).encode();compressed=gzip.compress(raw,mtime=0)
    out.mkdir(parents=True);chunks={}
    for index,at in enumerate(range(0,len(compressed),512*1024)):
        name=f'pool-{index:03d}.gzpart';(out/name).write_bytes(compressed[at:at+512*1024]);chunks[name]=sha(out/name)
    write(out/'summary.json',summary);shutil.copy2(ROOT/'regression/arithmetic_operator_v2_replay.py',out/'replay.py')
    write(out/'manifest.json',dict(version='operator-condition-evidence-v2',chunks=chunks,payload_sha256=hashlib.sha256(raw).hexdigest(),
        source_sha256={n[7:]:hashlib.sha256(v.encode()).hexdigest() for n,v in files.items() if n.startswith('source/')},
        review_sha256=sha(out/'summary.json'),replay_sha256=sha(out/'replay.py'),members=len(files),full_D_ready=False))
    (out/'README.md').write_text('# v2小算子函数证据\n\n'
        '通用数值函数f(x,T)，随后供S与DAG／必要G消费；44候选仅用于需求与覆盖回归。验收状态见summary.json，不能把失败或未消费test写成合格。\n\n'
        '运行`python3 -I -B replay.py --evidence .`可实际恢复冻结源码、标签摘要及数据，复算特征、预测、覆盖、误差与参数不变性；在共享Ledger支持叶下执行。此小包不包含全部物理路径、ODB或CEC产物，完整产物和逐批实际恢复归档保存在`'+str(root)+'`，保留至用户清理。\n\n'
        '仅验收独立节点函数；S／G完整联合与正式D资格另行验证。\n')
    size=sum(p.stat().st_size for p in out.iterdir())
    if size>5*1024**2 or any(p.stat().st_size>1024**2 for p in out.iterdir()):raise ValueError('evidence exceeds compact envelope')
    print(dict(status='packed',bytes=size,members=len(files),qualified_scalar_labels=len(labels)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('root','work','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();publish(a.root.resolve(),a.work.resolve(),a.out.resolve())
