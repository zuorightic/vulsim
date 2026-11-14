"""Portable v10 train isolation and pure Python/native consumption replay."""
import argparse
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch
from . import transition_incidence_features_v10 as geometry, transition_incidence_model_v10 as model
from .common_centered_replay_v1 import load, close
from .model_fast_preflight import key
from . import semantic_reset_features_v9 as context_geometry
from .semantic_fanout_replay_v8 import rejection_bundle
from .rebuffer_context_replay_v6 import verify_path


def verify_context_lineage(train, crossfit, predictions, bundle):
    rows = train['data']['S']
    if train['validation_labels_read'] or train['independent_labels_read'] or crossfit['uses_held_out_labels']:
        raise ValueError('training role differs')
    folds = {r['fold'] for r in rows}
    if set(crossfit['contexts']) != folds | {'all_train'} or len(folds) != 13:
        raise ValueError('context fold dimensions differ')
    for pair in train['paired_folds']:
        matched = [r for r in rows if r['source'] in (pair['old'],pair['new'])]
        if {r['fold'] for r in matched} != {pair['group']} or len({r['source'] for r in matched}) != 2:
            raise ValueError('paired source leakage')
    base = {}
    for r in rows:
        identity = r['source'], r['target_ps']
        if identity not in base:
            close(r['structure'],geometry.state_structure(r['spec'],r['target_ps']))
            base[identity] = {(q['path_class'],q['stage']):q['features'] for q in context_geometry.base_state_controls(r['structure'])}
    for fold,context in crossfit['contexts'].items():
        training = [r for r in rows if fold == 'all_train' or r['fold'] != fold]
        held = [r for r in rows if r['fold'] == fold]
        if (set(context['training_sources']) != {r['source'] for r in training}
                or set(context['excluded_sources']) != {r['source'] for r in held}
                or set(context['training_sources']) & set(context['excluded_sources']) or context['uses_held_out_labels']):
            raise ValueError('held-out context training leaked')
        lineage = [dict(source=r['source'],target_ps=r['target_ps'],stage=r['stage'],actual=r['actual'],
                        features=base[r['source'],r['target_ps']][r['path_class'],r['stage']])
                   for r in training if r['path_class']=='native_enable']
        if key(lineage) != context['training_rows_sha256']:
            raise ValueError('enable training lineage differs')
    checks = 0
    cache = {}
    for cls,record in predictions['S'].items():
        for mode in ('LOSO','train'):
            for r in record[mode]:
                fold = r['fold'] if mode == 'LOSO' else 'all_train'
                identity = fold,r['source'],r['target_ps']
                if identity not in cache:
                    cache[identity] = {(q['path_class'],q['stage']):q['features']
                                       for q in geometry.state_controls(r['structure'],crossfit['contexts'][fold]['function'])}
                close(r['f'],cache[identity][r['path_class'],r['stage']]);checks += 1
    close(bundle['context_function'],crossfit['contexts']['all_train']['function'])
    close(bundle['context_function'],bundle['models']['S']['native_enable']['functions']['R'])
    return checks


def replay(root=None,native=None):
    repo=Path(__file__).resolve().parents[2]
    root=Path(root) if root else repo/'experiments/arithmetic/evidence/common_transition_incidence_v10'
    identity=load(root/'identity.json')
    for name,digest in identity['files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('evidence changed: '+name)
    for name,digest in identity['source_sha256'].items():
        if hashlib.sha256((repo/name).read_bytes()).hexdigest()!=digest:raise ValueError('source changed: '+name)
    for name,entry in load(root/'source-and-tools.json.gz')['files'].items():
        if hashlib.sha256(entry['text'].encode()).hexdigest()!=entry['sha256']:raise ValueError('archived source differs: '+name)
    frozen=load(root/'freeze.json.gz');raw=gzip.decompress((root/'candidate.json.gz').read_bytes())
    if hashlib.sha256(raw).hexdigest()!=frozen['candidate_sha256']:raise ValueError('candidate differs from freeze')
    bundle=json.loads(raw);close(bundle,load(root/'runtime-bundle.json.gz'))
    train=load(root/'train-data.json.gz')
    context_checks=verify_context_lineage(train,load(root/'context-crossfit.json.gz'),load(root/'train-predictions.json.gz'),bundle)
    # The v8 mechanism labels are now train. Each must bind to its original run.
    origin=load(root/'inherited-v8-identity.json.gz')
    for name in ('physical-receipts.json.gz','path-proof-cases.json.gz'):
        if hashlib.sha256((root/('inherited-v8-'+name)).read_bytes()).hexdigest()!=origin['files'][name]:
            raise ValueError('inherited physical evidence origin differs')
    parents=load(root/'inherited-v8-physical-receipts.json.gz')
    new_sources={p['new'] for p in train['paired_folds'] if p.get('origin')=='v8_identical_query_train_contrast'}
    new_rows=[r for r in train['data']['S'] if r['source'] in new_sources]
    if len(new_sources)!=2 or len(new_rows)!=36:raise ValueError('train contrast duty differs')
    for row in new_rows:
        run=next(r for r in parents['runs'] if r['task']==row['source']+'-T'+str(row['target_ps']))
        metrics=next(m for m in run['manifest']['metrics'] if m['stage']=='grt')
        label=next(p for p in metrics['general_state_paths'] if p['id']==row['label_id'])
        close(row['actual'],label['delay_ps']+label['H_ps'])
        if row['manifest_sha256']!=run['manifest_sha256']:raise ValueError('inherited train label identity differs')
    cases=sum((load(root/name)['cases'] for name in ('consumption-cases.json.gz','evaluation-consumption-cases.json.gz')),[])
    fc=sum((load(root/name)['cases'] for name in ('feature-cases.json.gz','evaluation-feature-cases.json.gz')),[])
    rejects=load(root/'rejection-cases.json.gz')['cases']
    funcs=dict(operator=model.predict_operator,G=model.predict_reduction,S=model.predict_state)
    feats=dict(operator=geometry.operator_features,G=geometry.reduction_features,S=lambda q:geometry.state_controls(q,bundle['context_function']))
    counts=dict(price_queries=0,feature_queries=0,priced=0,rejections=0)
    with patch('subprocess.Popen',side_effect=AssertionError('online process')):
        with patch('builtins.open',side_effect=AssertionError('online file read')):
            with patch('pathlib.Path.open',side_effect=AssertionError('online path read')):
                for case in cases:
                    for q,expected in zip(case['queries'],case['expected'],strict=True):
                        actual=funcs[case['kind']](bundle,q,diagnostic=True);close(actual,expected)
                        counts['price_queries']+=1;counts['priced']+=actual['status']!='cost_uncovered'
                for case in fc:
                    for q,expected in zip(case['queries'],case['expected'],strict=True):
                        actual=feats[case['kind']](q)
                        if case['kind']=='S':actual=[{k:r[k] for k in ('path_class','control_source','stage','features')} for r in actual]
                        close(actual,expected);counts['feature_queries']+=1
                for case in rejects:
                    actual=funcs[case['kind']](rejection_bundle(bundle,case),case['query'],diagnostic=not case['public'])
                    if actual['status']!='cost_uncovered':raise ValueError('unsupported/public request accepted')
                    counts['rejections']+=1
    settlement=load(root/'settlement.json')
    if any(settlement['increment_usage'].values()) or settlement['recorded_cumulative_ledger']['pending']:raise ValueError('unexpected new physical work')
    report=load(root/'evaluation--report.json.gz')
    if any(report[k] for k in ('fresh_validation','validation_tuning','independent_labels_read','public_D_changed')):raise ValueError('regression role differs')
    # Recheck the real Liberty connectivity of the six inherited train runs.
    proof=load(root/'inherited-v8-path-proof-cases.json.gz');negatives=0
    for case in proof['cases']:
        verify_path(case,proof['pin_classes'])
        master,src,dst=case['arcs'][0];modified=deepcopy(proof['pin_classes'])
        modified[master]['timing_arcs']=[a for a in modified[master]['timing_arcs'] if a!=[src,dst]]
        try:verify_path(case,modified)
        except ValueError as error:
            if 'actual Liberty' not in str(error):raise
            negatives+=1
        else:raise ValueError('missing Liberty arc accepted')
    if negatives!=156:raise ValueError('inherited path proof differs')
    if native:
        with tempfile.TemporaryDirectory(prefix='transition-incidence-v10-') as folder:
            folder=Path(folder)
            def invoke(request):
                (folder/'in.json').write_text(json.dumps(request))
                subprocess.run([str(Path(native).resolve()),str(folder/'in.json'),str(folder/'out.json')],check=True,timeout=120)
                return load(folder/'out.json')
            for mode,requests in (('prices',cases),('features',fc)):
                for case in requests:
                    request=dict(kind=case['kind'],queries=case['queries'])
                    if mode=='prices':request.update(model=bundle,diagnostic=True)
                    elif case['kind']=='S':request['context_function']=bundle['context_function']
                    actual=invoke(request)
                    if mode=='features' and case['kind']=='S':actual=[[{k:r[k] for k in ('path_class','control_source','stage','features')} for r in rows] for rows in actual]
                    close(actual,case['expected'])
            for case in rejects:
                result=invoke(dict(kind=case['kind'],queries=[case['query']],model=rejection_bundle(bundle,case),diagnostic=not case['public']))
                if result[0]['status']!='cost_uncovered':raise ValueError('native rejection differs')
    return dict(status='passed',**counts,context_feature_checks=context_checks,new_train_sources=0,new_train_rows=0,inherited_contrast_train_sources=2,inherited_contrast_train_rows=36,
                inherited_strict_paths=156,missing_arc_negatives=negatives,source_files=len(identity['source_sha256']),
                native_replayed=bool(native),new_EDA_calls=0,online_physical_calls=0,online_file_reads=0,
                independent_labels_read=False,public_D_changed=False,full_D_ready=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path);parser.add_argument('--native',type=Path)
    args=parser.parse_args();print(json.dumps(replay(args.root,args.native),indent=2))
