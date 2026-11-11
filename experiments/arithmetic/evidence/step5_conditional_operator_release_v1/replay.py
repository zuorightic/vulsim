"""Isolated replay of a step-5 publication; only restored artifacts are used."""
import argparse
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


def read(p):return json.loads(p.read_text())
def digest(b):return hashlib.sha256(b).hexdigest()


def equal(a,b):
    if isinstance(a,float) or isinstance(b,float):return isinstance(a,(int,float)) and isinstance(b,(int,float)) and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-8)
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)):return isinstance(b,(list,tuple)) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    return a==b


def macro(rows,predictor,field,floor,model):
    groups={};absolute=[]
    for r in rows:
        err=abs(model.infer(predictor,r['features'])-r[field]);groups.setdefault(r['source_id'],[]).append(err/max(abs(r[field]),floor));absolute.append(err)
    values=sorted(median(v) for v in groups.values());m=values[math.ceil(.5*len(values))-1];p95=values[math.ceil(.95*len(values))-1]
    return dict(sources=len(groups),rows=len(rows),source_macro_median=m,source_macro_P95=p95,
        source_macro_normalized_absolute_error=sum(sum(v)/len(v) for v in groups.values())/len(groups),raw_MAE=sum(absolute)/len(absolute),passed=m<=.15 and p95<=.35)


def replay(evidence):
    m=read(evidence/'manifest.json');compressed=b''
    for n,h in m['chunks'].items():
        if Path(n).name!=n:raise ValueError('unsafe evidence part')
        b=(evidence/n).read_bytes()
        if digest(b)!=h:raise ValueError('changed evidence part')
        compressed+=b
    raw=gzip.decompress(compressed)
    if digest(raw)!=m['payload_sha256'] or digest((evidence/'replay.py').read_bytes())!=m['replay_sha256']:raise ValueError('changed replay/payload')
    for n,h in m['public_files'].items():
        if digest((evidence/n).read_bytes())!=h:raise ValueError('changed public file '+n)
    pool=json.loads(raw)
    with tempfile.TemporaryDirectory(prefix='step5-release-restored-') as tmp:
        tree=Path(tmp)
        for n,v in pool['files'].items():
            if Path(n).is_absolute() or '..' in Path(n).parts:raise ValueError('unsafe member')
            p=tree/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(v)
            if p.read_text()!=v:raise ValueError('member restore differs')
        sys.path.insert(0,str(tree/'source'))
        for n in list(sys.modules):
            if n=='experiments' or n.startswith('experiments.'):del sys.modules[n]
        model=importlib.import_module('experiments.arithmetic_dse.operator_condition_model');ownership=importlib.import_module('experiments.arithmetic_dse.model_logical_ownership_v2')
        if not all(Path(x.__file__).is_relative_to(tree) for x in (model,ownership)):raise ValueError('live implementation used')
        released=read(tree/'release/operators.json');candidate=read(tree/'ancestor/candidate.json');accept=read(tree/'release/acceptance.json')
        if digest((tree/'release/operators.json').read_bytes())!=accept['released_model_sha256']:raise ValueError('published model changed')
        a,b=deepcopy(candidate),deepcopy(released)
        for x in (a,b):x.pop('quality_status',None);x.pop('release',None)
        for op in a['operations']:
            a['operations'][op].pop('status');b['operations'][op].pop('status')
            for n in ('target_period_ps','abc_target_ps','log2_target_ps'):
                if n in a['operations'][op]['domain']['numeric_support']:b['operations'][op]['domain']['numeric_support'][n]=a['operations'][op]['domain']['numeric_support'][n]
        if a!=b:raise ValueError('predictors, support or reserves changed')
        for e in released['operations'].values():
            if e['domain']['numeric_support']['target_period_ps']!=[500,3000]:raise ValueError('publication interval differs')
        fresh=read(tree/'release/fresh-data.json')['rows'];old=read(tree/'ancestor/independent-test.json')
        if old['status']!='failed_independent' or not accept['original_failed_independent_verdict_retained']:raise ValueError('ancestor failure erased')
        physical=0
        for t in pool['physical_packets']:
            label=ownership.extract(t['packet'],t['nodes'],t['banks'],t['ports'],t['certificate'])
            for key in ('nodes','operator_delay_ps','comb_area_um2','data_setup_slack_ps','owner_area_um2','total_cell_area_um2','path_decompositions'):
                if not equal(label[key],t['label'][key]):raise ValueError('fresh physical packet/label differs '+t['task']+'/'+key)
            physical+=1
        for op,e in released['operations'].items():
            group=[r for r in fresh if r['operation']==op]
            for label,field,floor in (('delay','operator_delay_ps',10.),('area','comb_area_um2',.01)):
                if not equal(macro(group,e[label],field,floor,model),accept['operations'][op]['fresh'][label]):raise ValueError('fresh error arithmetic differs')
                exact=[r for r in group if r['target_ps']==1000]
                if not equal(macro(exact,e[label],field,floor,model),accept['operations'][op]['exact1000ps'][label]):raise ValueError('exact 1000ps error differs')
        input=read(tree/'release/native-input.json');native=read(tree/'release/native-output.json');count=0
        for q,answer in zip(input['queries'],native,strict=True):
            p=model.query(released,q['descriptor'],False)
            if answer['status']!=p['status']:raise ValueError('native/Python coverage differs')
            if p['status']=='covered':
                for k in ('operator_delay_ps','delay_reserve_ps','conservative_operator_delay_ps','comb_area_um2'):
                    if not math.isclose(answer[k],p[k],rel_tol=1e-10,abs_tol=1e-8):raise ValueError('native numerical price differs')
            count+=1
        public=read(tree/'release/public-consumer.json');nodes=0
        for target in public['targets']:
            if len(target['views'])!=44:raise ValueError('real query inventory incomplete')
            for view in target['views']:
                for quote in view['node_prices']:
                    p=model.query(released,quote['descriptor'])
                    if p['status']!='covered':raise ValueError('required real query uncovered')
                    for k in ('operator_delay_ps','delay_reserve_ps','comb_area_um2'):
                        if not math.isclose(p[k],quote[k],rel_tol=1e-10,abs_tol=1e-8):raise ValueError('actual native consumer quote differs')
                    nodes+=1
        if nodes!=2752 or not public['full_D_joint_gate_retained']:raise ValueError('joint production gate missing')
    print(dict(status='passed_step5_release_isolated_replay',physical_stages=physical,native_vectors=count,actual_D_node_queries=nodes,
        restored_members=len(pool['files']),new_EDA_calls=0,full_D_ready=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);a=p.parse_args();replay(a.evidence.resolve())
