"""Independent bit-map oracle and zero-G point/guard composition.

No physical feature is an input to estimate().  Measurements are consumed only
by validation(), after point parameters have been derived from training data.
"""
import argparse
from collections import Counter,defaultdict
from copy import deepcopy
import math
from pathlib import Path

from .model_fast_preflight import read,write,sha
from .operator_condition_model import query


WIRES={'assign','cast','zext','trunc','slice','bitselect','concat'}


def connections(graph,cut,queries):
    nodes={n['id']:n for n in graph['nodes']};members=set(cut['members']);launches=set(cut['launches'])
    specs={q['trace']['node']:q['descriptor']['local_context']['producer'] for q in queries if q['trace']['stage']==cut['stage']}
    memo={};visiting=set()
    def operand(o):
        if o['signed']:raise ValueError('signed mapping is outside successor policy')
        if o['kind']=='symbol':return roots(o['node'])
        if o['kind']=='literal':
            if len(o['bits'])!=o['width'] or any(b not in (0,1) for b in o['bits']):raise ValueError('invalid literal bit map')
            return [('constant',v,0) for v in o['bits']]
        raise ValueError('unknown bit-map operand')
    def roots(n):
        if n in memo:return memo[n]
        if n in visiting:raise ValueError('cyclic exact bit map')
        visiting.add(n);v=nodes[n];w=v['width'];kind=v['kind']
        if w<1 or w>257:raise ValueError('invalid mapped width')
        if kind=='constant':bits=[('constant',int(b in v['known_one']),0) for b in range(w)]
        elif n in launches or n in specs:bits=[('launch' if n in launches else 'operator',n,b) for b in range(w)]
        elif n not in members or kind not in WIRES:raise ValueError('missing launch/operator or unsupported wire')
        elif kind=='concat':bits=[b for o in reversed(v['operands']) for b in operand(o)]
        else:
            if len(v['operands'])!=1:raise ValueError('pure wire arity')
            bits=operand(v['operands'][0])
            if kind in ('slice','bitselect'):
                low=v['lo'] if kind=='slice' else v['bit']
                if low<0 or low+w>len(bits):raise ValueError('selection outside source')
                bits=bits[low:low+w]
            else:bits=(bits+[('constant',0,0)]*w)[:w]
        if len(bits)!=w:raise ValueError('exact wire width mismatch')
        if set(v['known_zero'])&set(v['known_one']):raise ValueError('conflicting known bits')
        for b in v['known_zero']:bits[b]=('constant',0,0)
        for b in v['known_one']:bits[b]=('constant',1,0)
        visiting.remove(n);memo[n]=bits;return bits
    groups=defaultdict(list)
    def add(bits,sink_kind,sink,operand_index,limit):
        for destination,(source_kind,source,bit) in enumerate(bits[:limit]):
            if source_kind!='constant':groups[(source_kind,source,sink_kind,sink,operand_index)].append([bit,destination])
    for n,spec in specs.items():
        for index,o in enumerate(nodes[n]['operands']):add(operand(o),'operator',n,index,spec['result_width'])
    for n in sorted(c['node'] for c in cut['captures']):add(roots(n),'capture',n,-1,nodes[n]['width'])
    return [dict(source_kind=k[0],source=k[1],sink_kind=k[2],sink=k[3],operand_index=k[4],bit_pairs=v,
        owner='inter_arithmetic' if k[0]=='operator' and k[2]=='operator' else 'S_boundary') for k,v in sorted(groups.items())]


def estimate(graph,variant,target,policy,model):
    if policy['operator_model_sha256']!=sha_model(model):raise ValueError('changed node model dependency')
    t=target['target_ps']
    if not policy['target_interval_ps'][0]<=t<=policy['target_interval_ps'][1]:raise ValueError('outside owned timing target domain')
    prices={q['trace']['node']:query(model,q['descriptor']) for q in target['queries']}
    bad=[p for p in prices.values() if p['status']!='covered']
    if bad:return dict(status='cost_uncovered')
    if len(prices)!=len(target['queries']):raise ValueError('duplicate node price')
    boundary=policy['boundary_point_ps'];wire=policy['inter_arithmetic_wire_point_ps'];reserve=policy['reserve']['joint_reserve_ps'];stages=[];guard=0.;point_v=0.
    for cut in variant['cuts']:
        arcs=connections(graph,cut,target['queries']);inputs=defaultdict(list);capture_edges=defaultdict(list)
        for edge in arcs:(inputs if edge['sink_kind']=='operator' else capture_edges)[edge['sink']].append(edge)
        capture_owner='external_state' if cut['stage']==len(variant['cuts'])-1 else 'native_state'
        def B(launch):
            native=any(not s['valid'] and not s['external_capture'] and s['origin']==launch and s['stage']==cut['stage'] for s in variant['state']['slots'])
            return boundary[('native_state' if native else 'input_service')+'->'+capture_owner]
        memo={};visiting=set()
        def arrival(n,legacy_guard):
            key=(n,legacy_guard)
            if key in memo:return memo[key]
            if n in visiting or n not in prices:raise ValueError('unpriced/cyclic normalized operator')
            visiting.add(n)
            value=max((B(e['source']) if e['source_kind']=='launch' else arrival(e['source'],legacy_guard)+wire for e in inputs[n]),default=0.)
            value+=prices[n]['operator_delay_ps']+(prices[n]['delay_reserve_ps'] if legacy_guard else 0.)
            visiting.remove(n);memo[key]=value;return value
        captures=[]
        for c in cut['captures']:
            n=c['node']
            if n not in capture_edges:continue
            def maximum(old):return max(B(e['source']) if e['source_kind']=='launch' else arrival(e['source'],old) for e in capture_edges[n])
            point=maximum(False);nodeguard=maximum(True);captures.append(dict(node=n,point_required_period_ps=point,point_slack_ps=t-point,
                legacy_node_guard_required_period_ps=nodeguard,decision_required_period_ps=point+reserve,decision_slack_ps=t-point-reserve,joint_reserve_ps=reserve))
            point_v=max(point_v,point-t);guard=max(guard,point+reserve-t)
        stages.append(dict(stage=cut['stage'],connections=arcs,captures=captures))
    return dict(status='candidate_covered',stages=stages,point_violation_ps=point_v,decision_arithmetic_violation_ps=guard,G_delay_ps=0.,joint_qualified=False,full_D_ready=False)


def sha_model(model):
    # The oracle receives the frozen file's exact identity separately; mutable
    # in-memory models must not bypass the published content check.
    import hashlib,json
    return hashlib.sha256((json.dumps(model,indent=2,ensure_ascii=False)+'\n').encode()).hexdigest()


def compare(native_path,policy_path,model_path,out):
    if out.exists():raise ValueError('preserve native parity attempt')
    out.mkdir(parents=True);native=read(native_path);policy=read(policy_path);model=read(model_path)
    if native['policy_sha256']!=sha(policy_path) or native['model_sha256']!=sha(model_path):raise ValueError('native used another model/policy')
    counts=Counter();rows=[]
    for source in native['sources']:
        for variant in source['variants']:
            for target in variant['targets']:
                p=estimate(variant['graph'],variant,target,policy,model);c=target['owned_timing'];counts[p['status']]+=1
                if p['status']!=c['status']:raise ValueError('native/oracle coverage mismatch')
                if p['status']=='candidate_covered':
                    for ps,cs in zip(p['stages'],c['stages'],strict=True):
                        oracle=[{**e,'wire_point_ps':policy['inter_arithmetic_wire_point_ps'] if e['owner']=='inter_arithmetic' else 0.} for e in ps['connections']]
                        if oracle!=cs['connections']:raise ValueError('C++/Python exact bit/owner connection mismatch')
                        for pp,cp in zip(ps['captures'],cs['captures'],strict=True):
                            if pp.keys()!=cp.keys() or any(not math.isclose(pp[k],cp[k],abs_tol=1e-8,rel_tol=1e-10) for k in pp):raise ValueError('C++/Python point/guard price mismatch')
                    if not math.isclose(p['point_violation_ps'],c['point_violation_ps'],abs_tol=1e-8):raise ValueError('point stage violation mismatch')
                rows.append(dict(source=source['source'],placement=variant['id'],target_ps=target['target_ps'],**p))
    write(out/'parity.json',dict(status='passed_owned_timing_native_parity',counts=dict(counts),queries=len(rows),rows=rows,
        model_sha256=sha(model_path),policy_sha256=sha(policy_path),full_D_ready=False))
    print(dict(status='passed_owned_timing_native_parity',counts=dict(counts),queries=len(rows)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--policy',type=Path,required=True);p.add_argument('--model',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();compare(a.native.resolve(),a.policy.resolve(),a.model.resolve(),a.out.resolve())
