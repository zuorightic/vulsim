"""Compact review artifacts and deterministic portable inference replay.

Full EDA snapshots remain in the explicit retained collection and its actually
restored archives. This small package carries prices, parameters and raw-file
identities, and does not claim to replace those full physical artifacts.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics

from .model_fast_preflight import read, write, sha
from . import operator_condition_model as inference

ROOT=Path(__file__).resolve().parents[2]


def summary(root, data):
    rows=[r for r in data['rows'] if r['stage']=='grt'];by_source=defaultdict(list)
    for row in rows:by_source[row['source_id']].append(row)
    responses=[]
    for source,local in sorted(by_source.items()):
        def span(field):
            values=[r[field] for r in local]
            return dict(min=min(values),max=max(values),range=max(values)-min(values),
                relative_range=(max(values)-min(values))/max(statistics.median(values),1e-12))
        responses.append(dict(source_id=source,role=local[0]['role'],operation=local[0]['operation'],points=len(local),
            target_ps=span('target_ps'),delay_ps=span('operator_delay_ps'),area_um2=span('comb_area_um2'),
            minimum_through_data_slack_ps=min(r['data_setup_slack_ps'] for r in local)))
    roles=Counter(r['role'] for r in rows);regions=Counter();shortfall=[];stops=Counter()
    for source in data['coverage']:
        stops[source['stop_reason']]+=1
        for region in source['regions']:regions[region['region']]+=region['effective_points']
        if source['coverage_shortfall']:shortfall.append(source['source_id'])
    semantic={}
    for op in sorted({r['operation'] for r in rows}):
        local=[r for r in rows if r['operation']==op]
        semantic[op]=dict(sources=len({r['source_id'] for r in local}),
            source_counts={role:len({r['source_id'] for r in local if r['role']==role}) for role in ('train','validation','locked_test')},
            widths=sorted({(r['features']['lhs_width'],r['features']['rhs_width'],r['features']['result_width']) for r in local}),
            consumers=sorted({(r['features']['consumer_count'],r['features']['consumer_lhs_max'],r['features']['consumer_rhs_max'],r['features']['consumer_result_max']) for r in local}),
            capture_banks=sorted({r['features']['capture_banks'] for r in local}),
            target_range_ps=[min(r['target_ps'] for r in local),max(r['target_ps'] for r in local)])
    return dict(version='operator-condition-coverage-response-v1',main_stage='grt',sources=len(data['coverage']),valid_points=len(rows),
        point_roles=dict(roles),regions=dict(regions),shortfall_sources=shortfall,stop_reasons=dict(stops),
        failures=data['failures'],node_response_by_source=responses,semantic_coverage=semantic,
        sampling_slack_is_not_operator_delay=True,three_regions_are_not_a_model_quality_gate=True,
        full_D_ready=False)


def publish(root,out):
    progress=read(root/'progress.json')
    if progress['phase'] not in ('fitting_collection_complete','independent_collection_complete'):
        raise ValueError('settled bounded collection required')
    data=read(root/'fit-data.json');report=summary(root,data)
    if (root/'test-data.json').exists():report['independent_coverage']=summary(root,read(root/'test-data.json'))
    fit=root/'fit-v1';freeze=read(fit/'selection-freeze.json')
    files={};labels={};raw_identity={}
    def include(path,name):
        if name in files:raise ValueError('duplicate evidence path '+name)
        files[name]=path.read_text()
    for path in (root/'corpus').rglob('*'):
        if path.is_file():include(path,'corpus/'+str(path.relative_to(root/'corpus')))
    names=set(freeze['implementation_sources'])
    names.update(read(root/read(root/'active-collection.json')['path'])['measurement_sources'])
    names.update(['experiments/arithmetic_dse/operator_condition_evidence.py','regression/arithmetic_stage4_clone_stop.py',
        'regression/arithmetic_stage45_completion.py','regression/arithmetic_operator_evidence_replay.py'])
    for name in sorted(names):include(ROOT/name,'source/'+name)
    for name in ('fit-data.json','test-data.json','progress.json','collection.json','active-collection.json','clone-stop-proof.json',
        'completion-audit-v1.json','fit-source-macro-preflight.json','independent-evaluation-consumed.json'):
        if (root/name).exists():include(root/name,name)
    for directory in ('fit-v1','test-v1','amendments'):
        if (root/directory).exists():
            for p in (root/directory).rglob('*.json'):include(p,str(p.relative_to(root)))
    for state in (root/'raw').iterdir():
        if not (state/'history.json').exists():continue
        include(state/'history.json','histories/'+state.name+'.json')
    for dataset in [data]+([read(root/'test-data.json')] if (root/'test-data.json').exists() else []):
        for row in dataset['rows']:
            p=Path(row['measurement_path']);label=p/(row['stage']+'-labels.json')
            labels[row['id']]=read(label)
            relatives=[row['stage']+'-labels.json','liberty-pins.json','mapped-contract.json','operator-port-contract.json','query-contract.json',
                'logs/asap7/arithmetic_probe/base/structural_cec/proof.json']
            relatives += [str(x.relative_to(p)) for x in (p/'reports/asap7/arithmetic_probe/base').glob('context_'+row['stage']+'_*') if x.is_file()]
            for name in relatives:
                x=p/name;raw_identity[str(x)]=dict(sha256=sha(x),bytes=x.stat().st_size)
    archives=[]
    for p in sorted((root/'archives').glob('*.index.json')):
        receipt=read(p)
        if receipt['status']!='passed' or not receipt['actual_restore_and_every_member_hash_checked']:raise ValueError('archive restore receipt missing')
        archives.append({k:v for k,v in receipt.items() if k!='members'}|dict(index_path=str(p),index_sha256=sha(p),member_count=len(receipt['members'])))
    payload=dict(files=files,qualified_labels=labels,raw_identity=raw_identity,archives=archives)
    raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode();compressed=gzip.compress(raw,compresslevel=9,mtime=0)
    out.mkdir(parents=True,exist_ok=False);chunks={}
    for i,at in enumerate(range(0,len(compressed),512*1024)):
        name=f'pool-{i:03d}.json.gz.part';p=out/name;p.write_bytes(compressed[at:at+512*1024]);chunks[name]=dict(sha256=sha(p),bytes=p.stat().st_size)
    write(out/'coverage-response.json',report)
    (out/'replay.py').write_text((ROOT/'regression/arithmetic_operator_evidence_replay.py').read_text())
    write(out/'manifest.json',dict(version='operator-condition-evidence-v1',chunks=chunks,payload_sha256=hashlib.sha256(raw).hexdigest(),
        source_sha256={name:sha(ROOT/name) for name in sorted(names)},fit_data_sha256=sha(root/'fit-data.json'),
        selection_sha256=sha(fit/'selection-freeze.json'),validation_passed=freeze['validation_passed'],
        test_consumed=(root/'independent-evaluation-consumed.json').exists(),retained_full_artifact_root=str(root),
        full_raw_snapshots_in_git=False,full_D_ready=False))
    (out/'README.md').write_text('# 条件算子第4—5步证据\n\n'
        '源角色、完整有效标签、拟合数据、候选参数、验证/独立结果、源码、失败及实际归档恢复收据收录在分块gzip包中。'
        'raw_identity绑定完整原始路径报告；本小包不包含全部ODB/原始报告。完整物理产物与已逐成员恢复的归档保存在`'+str(root)+'`，保留至用户明确清理。\n\n'
        '验证入口：`python3 -B -m experiments.arithmetic_dse.operator_condition_evidence verify --out '+str(out.relative_to(ROOT))+'`。'
        '在共享Ledger支持叶下执行；可加`--check-retained`核对本机原始报告。该操作不启动EDA。\n\n'
        '函数只给节点独立最大组合时延与同一实现组合面积。质量及域外拒绝见manifest/validation/test；S/G联合价格与完整D仍未授予资格。\n')
    if any(p.stat().st_size>1024*1024 for p in out.iterdir()) or sum(p.stat().st_size for p in out.iterdir())>5*1024*1024:
        raise ValueError('compact evidence size limit exceeded; preserve provisional package')
    print(dict(status='published',bytes=sum(p.stat().st_size for p in out.iterdir()),labels=len(labels),raw_files=len(raw_identity)),flush=True)


def verify(out,check_retained=False):
    manifest=read(out/'manifest.json');parts=[]
    for name,identity in manifest['chunks'].items():
        p=out/name
        if sha(p)!=identity['sha256'] or p.stat().st_size!=identity['bytes']:raise ValueError('evidence chunk changed')
        parts.append(p.read_bytes())
    raw=gzip.decompress(b''.join(parts))
    if hashlib.sha256(raw).hexdigest()!=manifest['payload_sha256']:raise ValueError('evidence payload changed')
    pool=json.loads(raw);files=pool['files'];data=json.loads(files['fit-data.json']);candidate=json.loads(files['fit-v1/candidate.json']);predictions=covered=0
    for name,h in manifest['source_sha256'].items():
        if hashlib.sha256(files['source/'+name].encode()).hexdigest()!=h or sha(ROOT/name)!=h:raise ValueError('frozen source differs '+name)
    for name in ('fit-data.json','test-data.json'):
        if name not in files:continue
        for row in json.loads(files[name])['rows']:
            label=pool['qualified_labels'][row['id']]
            if label['source_role']!=row['role'] or not label['physical_training_label_eligible']:raise ValueError('qualified role mismatch')
            for key in ('operator_delay_ps','comb_area_um2','data_setup_slack_ps'):
                if row[key]!=label[key]:raise ValueError('stored physical price differs')
            if row['stage']=='grt':
                answer=inference.query(candidate,row['descriptor'],True);predictions+=1;covered+=answer['status']=='covered'
                if answer['status']=='covered' and any(not math.isfinite(answer[k]) for k in ('operator_delay_ps','comb_area_um2')):raise ValueError('nonfinite frozen prediction')
    if check_retained:
        for name,identity in pool['raw_identity'].items():
            p=Path(name)
            if sha(p)!=identity['sha256'] or p.stat().st_size!=identity['bytes']:raise ValueError('retained raw file changed '+name)
    print(dict(status='passed',formal_rows=len(pool['qualified_labels']),inference_queries=predictions,covered=covered,
        raw_files=len(pool['raw_identity']),retained_files_checked=check_retained,new_EDA_calls=0,full_D_ready=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('publish','verify'));p.add_argument('--root',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--check-retained',action='store_true');a=p.parse_args()
    if a.action=='publish':publish(a.root.resolve(),a.out.resolve())
    else:verify(a.out.resolve(),a.check_retained)
