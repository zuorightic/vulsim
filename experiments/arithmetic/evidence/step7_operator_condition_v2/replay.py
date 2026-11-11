"""Stdlib portable restoration and independent macro-error arithmetic."""
import argparse
from collections import defaultdict
from copy import deepcopy
import gzip
import hashlib
import importlib
import json
import math
from pathlib import Path
from statistics import median
import sys
import tempfile


def read(path):return json.loads(path.read_text())
def digest(raw):return hashlib.sha256(raw).hexdigest()


def metrics(rows,predictor,field,floor,inference):
    groups=defaultdict(list);absolute=[]
    for row in rows:
        error=abs(inference.infer(predictor,row['features'])-row[field]);groups[row['source_id']].append(error/max(abs(row[field]),floor));absolute.append(error)
    if not groups:return dict(sources=0,rows=0,source_macro_median=None,source_macro_P95=None,source_macro_normalized_absolute_error=None,raw_MAE=None,passed=False)
    values=sorted(median(v) for v in groups.values());m=values[math.ceil(.5*len(values))-1];p95=values[math.ceil(.95*len(values))-1]
    return dict(sources=len(groups),rows=len(rows),source_macro_median=m,source_macro_P95=p95,
        source_macro_normalized_absolute_error=sum(sum(v)/len(v) for v in groups.values())/len(groups),raw_MAE=sum(absolute)/len(absolute),passed=m<=.15 and p95<=.35)


def compare(actual,expected):
    if actual.keys()!=expected.keys():raise ValueError('statistic keys differ')
    for k,v in actual.items():
        if isinstance(v,float):
            if not math.isclose(v,expected[k],rel_tol=1e-10,abs_tol=1e-8):raise ValueError('statistic differs '+k)
        elif v!=expected[k]:raise ValueError('statistic differs '+k)


def replay(evidence):
    m=read(evidence/'manifest.json');parts=[]
    for n,h in m['chunks'].items():
        if Path(n).name!=n:raise ValueError('unsafe chunk')
        raw=(evidence/n).read_bytes()
        if digest(raw)!=h:raise ValueError('changed chunk')
        parts.append(raw)
    raw=gzip.decompress(b''.join(parts))
    if digest(raw)!=m['payload_sha256'] or digest((evidence/'summary.json').read_bytes())!=m['review_sha256'] or digest((evidence/'replay.py').read_bytes())!=m['replay_sha256']:
        raise ValueError('changed payload or review')
    pool=json.loads(raw)
    with tempfile.TemporaryDirectory(prefix='operator-v2-restore-') as temporary:
        tree=Path(temporary)
        for n,v in pool['files'].items():
            if Path(n).is_absolute() or '..' in Path(n).parts:raise ValueError('unsafe member')
            p=tree/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(v)
            if p.read_text()!=v:raise ValueError('actual member restore differs')
        for n,h in m['source_sha256'].items():
            if digest((tree/'source'/n).read_bytes())!=h:raise ValueError('frozen source changed')
        sys.path.insert(0,str(tree/'source'))
        for name in list(sys.modules):
            if name=='experiments' or name.startswith('experiments.'):del sys.modules[name]
        model=importlib.import_module('experiments.arithmetic_dse.operator_condition_model')
        if not Path(model.__file__).is_relative_to(tree):raise ValueError('live inference used')
        candidate=read(tree/'fit-v2/candidate.json');validation=read(tree/'fit-v2/validation.json');fit=read(tree/'fit-data.json')
        if digest((tree/'fit-v2/candidate.json').read_bytes())!=validation['model_sha256']:raise ValueError('model receipt changed')
        vectors=0;covered=0
        for name in ('fit-data.json','test-data.json'):
            if not (tree/name).exists():continue
            data=read(tree/name)
            for row in data['rows']:
                scalar=pool['qualified_scalar_labels'][row['id']]
                if scalar['source_role']!=row['role'] or not scalar['physical_training_label_eligible']:raise ValueError('source role changed')
                for key in ('operator_delay_ps','comb_area_um2','data_setup_slack_ps'):
                    if scalar[key]!=row[key]:raise ValueError('qualified numerical label changed')
                if model.features(row['descriptor'])!=row['features']:raise ValueError('frozen feature extraction differs')
                if row['stage']=='grt':vectors+=1;covered+=model.query(candidate,row['descriptor'],True)['status']=='covered'
        for op,e in candidate['operations'].items():
            rows=[r for r in fit['rows'] if r['stage']=='grt' and r['role']=='validation' and r['operation']==op]
            for label,field,floor in (('delay','operator_delay_ps',10.),('area','comb_area_um2',.01)):
                compare(metrics(rows,e[label],field,floor,model),validation['operations'][op][label])
        independent='not_consumed'
        if (tree/'test-v2/independent-test.json').exists():
            report=read(tree/'test-v2/independent-test.json');tested=read(tree/'test-v2/tested-model.json');test=read(tree/'test-data.json')
            independent=report['status'];a=deepcopy(candidate);b=deepcopy(tested)
            for bundle in (a,b):
                bundle.pop('quality_status')
                for e in bundle['operations'].values():e.pop('status')
            if a!=b:raise ValueError('parameters/domain/reserve changed after test')
            for op,e in candidate['operations'].items():
                rows=[r for r in test['rows'] if r['stage']=='grt' and r['operation']==op]
                for label,field,floor in (('delay','operator_delay_ps',10.),('area','comb_area_um2',.01)):
                    compare(metrics(rows,e[label],field,floor,model),report['operations'][op][label])
        print(dict(status='passed_artifact_replay',restored_files=len(pool['files']),function_queries=vectors,covered=covered,
            validation_status=validation['status'],independent_status=independent,new_EDA_calls=0,full_D_ready=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);a=p.parse_args();replay(a.evidence.resolve())
