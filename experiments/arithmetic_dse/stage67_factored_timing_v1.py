"""Independent Python consumer of typed S boundaries and simple shared prices."""
import argparse
from collections import Counter,defaultdict
from copy import deepcopy
import math
from pathlib import Path

from .model_fast_preflight import read,write,sha
from .operator_condition_model import query
from .stage67_owned_timing_v1 import connections,WIRES,sha_model


def complete_variant(graph,variant):
    result=deepcopy(variant)
    for cut in result['cuts']:
        members=set(cut['members'])|{n['id'] for n in graph['nodes'] if n['kind'] in WIRES};launches=set(cut['launches']);captures={c['node'] for c in cut['captures']}
        for slot in result['state']['slots']:
            if slot['valid'] or not slot['variable_bits']:continue
            if slot['stage']==cut['stage']:launches.add(slot['origin'])
            if slot['stage']==cut['stage']+1:captures.add(slot['origin'])
        if cut['stage']==0:launches|={n['id'] for n in graph['nodes'] if n['kind']=='input' and n['id'] not in cut['controls']}
        cut.update(members=sorted(members),launches=sorted(launches),captures=[dict(node=n) for n in sorted(captures)])
    return result


def linear(model,features):
    if model['kind']!='nonnegative_linear' or len(model['features'])!=len(model['coefficients']):raise ValueError('invalid simple shared/state model')
    value=0
    for n,c in zip(model['features'],model['coefficients'],strict=True):
        if not math.isfinite(c) or c<0:raise ValueError('invalid nonnegative coefficient')
        if 'numeric_support' in model:
            low,high=model['numeric_support'][n]
            if not low<=features[n]<=high:raise ValueError('shared area outside frozen semantic feature support')
        value+=c*features[n]
    return value


def area(graph,variant,target,policy,node_model,S):
    owners={n:dict(data_bits=0,data_signals=0,valid_bits=0,enable_domains=0,reset_one_bits=0) for n in ('input_service','native_state','external_state')}
    controls=set(variant['cuts'][0]['controls']);inputs=[n for n in graph['nodes'] if n['kind']=='input' and n['id'] not in controls]
    for n in inputs:
        active=n['width']-len(set(n['known_zero'])|set(n['known_one']))
        if active:owners['input_service']['data_bits']+=active;owners['input_service']['data_signals']+=1
    owners['input_service']['valid_bits']=1;owners['input_service']['enable_domains']=owners['input_service']['data_signals']+1;enables=set()
    for slot in variant['state']['slots']:
        f=owners['external_state' if slot['external_capture'] else 'native_state']
        if slot['valid']:f['valid_bits']+=1
        elif slot['variable_bits']:
            f['data_bits']+=slot['variable_bits'];f['data_signals']+=1
            mask=sum(int(v,16)<<(64*i) for i,v in enumerate(slot['variable_mask_hex']));reset=sum(int(v,16)<<(64*i) for i,v in enumerate(slot['reset_hex']));f['reset_one_bits']+=(mask&reset).bit_count()
            if not slot['external_capture']:enables.add(slot['enable_stage'])
    owners['native_state']['enable_domains']=len(enables)
    prices=[query(node_model,q['descriptor']) for q in target['queries']]
    if any(v['status']!='covered' for v in prices):raise ValueError('node function outside frozen support')
    areas={n:linear(S['stages']['grt']['area_models'][n],f) for n,f in owners.items()};areas['operators']=sum(v['comb_area_um2'] for v in prices)
    features=dict(one=1.,input_data_bits=owners['input_service']['data_bits'],total_FF_bits=sum(f['data_bits']+f['valid_bits'] for f in owners.values()),
        reset_one_bits=sum(f['reset_one_bits'] for f in owners.values()),predicted_functional_area_um2=sum(areas.values()))
    for n,m in policy['shared_area_models'].items():areas[n]=linear(m,features)
    return dict(shared_features=features,owner_area_um2=areas,total_area_um2=sum(areas.values()))


def estimate(graph,variant,target,policy,model,S):
    if policy['version']!='factored-state-shared-v1' or policy['operator_model_sha256']!=sha_model(model):raise ValueError('changed successor node/policy identity')
    t=target['target_ps']
    if not policy['target_interval_ps'][0]<=t<=policy['target_interval_ps'][1]:raise ValueError('outside successor target interval')
    prices={q['trace']['node']:query(model,q['descriptor']) for q in target['queries']}
    if any(v['status']!='covered' for v in prices.values()):return dict(status='cost_uncovered')
    try:areas=area(graph,variant,target,policy,model,S)
    except ValueError:return dict(status='cost_uncovered')
    v=complete_variant(graph,variant);wire=policy['inter_arithmetic_wire_point_ps'];reserve=policy['reserve']['joint_reserve_ps'];stages=[];point_violation=0;decision=0
    for cut in v['cuts']:
        arcs=connections(graph,cut,target['queries']);inputs=defaultdict(list);captures=defaultdict(list)
        for e in arcs:(inputs if e['sink_kind']=='operator' else captures)[e['sink']].append(e)
        capture_owner='external_state' if cut['stage']==len(v['cuts'])-1 else 'native_state'
        def boundary(n,pure=False):
            native=any(not s['valid'] and not s['external_capture'] and s['origin']==n and s['stage']==cut['stage'] for s in v['state']['slots'])
            return policy['forward_boundary_point_ps' if pure else 'boundary_point_ps'][('native_state' if native else 'input_service')+'->'+capture_owner]
        memo={};visiting=set()
        def arrival(n,guard):
            key=(n,guard)
            if key in memo:return memo[key]
            if n in visiting or n not in prices:raise ValueError('unpriced/cyclic arithmetic')
            visiting.add(n);value=max((boundary(e['source']) if e['source_kind']=='launch' else arrival(e['source'],guard)+wire for e in inputs[n]),default=0.)
            value+=prices[n]['operator_delay_ps']+(prices[n]['delay_reserve_ps'] if guard else 0);visiting.remove(n);memo[key]=value;return value
        rows=[]
        for c in cut['captures']:
            if c['node'] not in captures:continue
            def maximum(guard):return max(boundary(e['source'],True) if e['source_kind']=='launch' else arrival(e['source'],guard) for e in captures[c['node']])
            point=maximum(False);oldguard=maximum(True);rows.append(dict(node=c['node'],point_required_period_ps=point,point_slack_ps=t-point,
                legacy_node_guard_required_period_ps=oldguard,decision_required_period_ps=point+reserve,decision_slack_ps=t-point-reserve,joint_reserve_ps=reserve))
            point_violation=max(point_violation,point-t);decision=max(decision,point+reserve-t)
        stages.append(dict(stage=cut['stage'],connections=arcs,captures=rows))
    return dict(status='candidate_covered',stages=stages,point_violation_ps=point_violation,decision_arithmetic_violation_ps=decision,**areas,
        zero_G_joint_qualified=False,full_D_ready=False)


def compare(native,policy,model,S,out):
    if out.exists():raise ValueError('preserve successor parity')
    out.mkdir(parents=True);n=read(native);p=read(policy);m=read(model);s=read(S)
    if n['policy_sha256']!=sha(policy) or n['model_sha256']!=sha(model) or p['state_model_sha256']!=sha(S):raise ValueError('native policy/model/S identity differs')
    counts=Counter();records=[]
    for source in n['sources']:
        for variant in source['variants']:
            for target in variant['targets']:
                predicted=estimate(variant['graph'],variant,target,p,m,s);actual=target['owned_timing'];counts[predicted['status']]+=1
                if predicted['status']!=actual['status']:raise ValueError('C++/Python successor coverage differs')
                if predicted['status']=='candidate_covered':
                    for left,right in zip(predicted['stages'],actual['stages'],strict=True):
                        arcs=[e|dict(wire_point_ps=p['inter_arithmetic_wire_point_ps'] if e['owner']=='inter_arithmetic' else 0.) for e in left['connections']]
                        if arcs!=right['connections']:raise ValueError('complete-state exact bit arcs differ')
                        for a,b in zip(left['captures'],right['captures'],strict=True):
                            if a.keys()!=b.keys() or any(not math.isclose(a[k],b[k],abs_tol=1e-8,rel_tol=1e-10) for k in a):raise ValueError('typed boundary stage prices differ')
                    for key in ('shared_features','owner_area_um2'):
                        if predicted[key].keys()!=actual[key].keys() or any(not math.isclose(predicted[key][k],actual[key][k],abs_tol=1e-8,rel_tol=1e-10) for k in predicted[key]):raise ValueError('semantic shared features/area differs')
                    if not math.isclose(predicted['total_area_um2'],actual['total_area_um2'],abs_tol=1e-8):raise ValueError('unique total area differs')
                records.append(dict(source=source['source'],placement=variant['id'],target_ps=target['target_ps'],**predicted))
    write(out/'parity.json',dict(status='passed_factored_state_shared_native_parity',counts=dict(counts),rows=records,requests=len(records),full_D_ready=False));print(dict(status='passed_factored_state_shared_native_parity',counts=dict(counts),requests=len(records)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('native','policy','model','S','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();compare(a.native.resolve(),a.policy.resolve(),a.model.resolve(),a.S.resolve(),a.out.resolve())
