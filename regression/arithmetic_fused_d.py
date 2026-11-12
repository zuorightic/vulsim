"""Independent G/S/node accounting, bit semantics, and D ranking oracle.

This consumes real model queries and reports. It never supplies candidate prices
to D, and it never reads final physical PPA to select or adjust a model.
"""
import argparse
from collections import defaultdict
from pathlib import Path
import random
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse.operator_condition_model import query
from experiments.arithmetic_dse.reduction_function_v2 import predict
from experiments.arithmetic_dse.stage67_factored_timing_v1 import complete_variant,connections,linear
from regression.arithmetic_function_d import projection,nonarithmetic,close


def evaluate_graph(graph, values, root):
    nodes={n['id']:n for n in graph['nodes']};memo=dict(values)
    def value(n):
        if n in memo:return memo[n]
        s=nodes[n];kind=s['kind'];w=s['width']
        def operand(a):
            if a['kind']=='symbol':return value(a['node'])
            if a['kind']=='literal':return sum(b<<i for i,b in enumerate(a['bits']))
            return 0
        args=[operand(a) for a in s['operands']]
        if kind=='constant':v=sum(1<<b for b in s['known_one'])
        elif kind=='input':v=0
        elif kind in ('add','addcarry'):v=sum(args)
        elif kind=='mul':v=args[0]*args[1]
        elif kind=='concat':
            v=0
            for a,x in zip(s['operands'],args):v=(v<<a['width'])|x
        elif kind in ('slice','bitselect'):v=args[0]>>(s['lo'] if kind=='slice' else s['bit'])
        elif kind in ('assign','cast','zext','trunc'):v=args[0]
        else:raise ValueError('unsupported independent graph operation '+kind)
        memo[n]=v&((1<<w)-1);return memo[n]
    return value(root)


def semantics(row,region):
    nodes={n['id']:n for n in row['graph']['nodes']};sources={b[0] for term in region['terms'] for b in term};rng=random.Random(20261112)
    for i in range(258):
        values={n:(0 if i==0 else (1<<nodes[n]['width'])-1 if i==1 else rng.getrandbits(nodes[n]['width'])) for n in sources}
        for n in values:
            values[n]=(values[n]&~sum(1<<b for b in nodes[n]['known_zero']))|sum(1<<b for b in nodes[n]['known_one'])
        expected=evaluate_graph(row['graph'],values,region['root'])&((1<<region['output_bits'])-1)
        actual=sum(sum(((values[s]>>b)&1)<<c for s,b,c in term) for term in region['terms'])&((1<<region['output_bits'])-1)
        if expected!=actual:raise ValueError('G canonical sum changes original finite-width graph')


def audit(report,source,bundle,base):
    deps={n:read((base/d['path']).resolve()) for n,d in bundle['dependencies'].items() if n in ('operators','S_binding','composition','state_model','G_reduction')}
    node,S,binding,policy,G=(deps[n] for n in ('operators','state_model','S_binding','composition','G_reduction'))
    target=report['target_period_ps'];scores=[];counts=defaultdict(int);semantic_seen=set()
    for row in report['candidates']:
        if row['status']!='covered':raise ValueError('incomplete coverage cannot produce accepted D RTL')
        out=row['estimate'];owners,control=projection(row,source);areas={n:linear(S['stages']['grt']['area_models'][n],f) for n,f in owners.items()};prices={};g_owned={n for r in out['G_regions'] for n in r['additions']}
        for q in row['queries']:
            p=query(node,q['descriptor']);n=q['trace']['node'];counts['node_queries']+=1
            if (p['status']!='covered' and n not in g_owned) or n in prices:raise ValueError('uncovered/duplicate independent node query')
            prices[n]=p
        removed=set();regions=out['G_regions'];regional_area=0
        for region in regions:
            p=predict(G,region['output_bits'],region['terms'],target);counts['G_queries']+=1
            for name in ('delay_ps','area_um2'):close(p[name],region[name])
            for name,v in p['features'].items():close(v,region['features'][name])
            if removed&set(region['additions']):raise ValueError('duplicate G interior charge')
            removed.update(region['additions']);regional_area+=p['area_um2']
            key=(row['graph']['graph_sha256'],region['root'])
            if key not in semantic_seen:semantics(row,region);semantic_seen.add(key);counts['bit_semantic_vectors']+=258
        if set(p['node'] for p in out['replaced_node_prices'])!=removed:raise ValueError('G replacement inventory differs')
        if set(p['node'] for p in out['node_prices'])!=set(prices)-removed:raise ValueError('G internal nodes still charged or outside nodes lost')
        areas['operators']=sum(v['comb_area_um2'] for n,v in prices.items() if n not in removed);areas['G_reductions']=regional_area
        for n in removed:del prices[n]
        for r in regions:prices[r['root']]=dict(operator_delay_ps=r['delay_ps'],delay_reserve_ps=0,comb_area_um2=r['area_um2'])
        ff=sum(f['data_bits']+f['valid_bits'] for f in owners.values())
        f=dict(one=1.,total_FF_bits=ff,sqrt_FF_bits=ff**.5,predicted_functional_area_um2=sum(areas.values()),reset_one_bits=sum(f['reset_one_bits'] for f in owners.values()),input_data_bits=owners['input_service']['data_bits'],input_ports=owners['input_service']['data_signals'],clock_pressure=1500/target)
        for owner,m in policy['shared_area_models'].items():areas[owner]=linear(m,f)
        if set(areas)!=set(out['owner_area_um2']):raise ValueError('G/S/shared owner inventory differs')
        for n,v in areas.items():close(v,out['owner_area_um2'][n])
        for n,v in f.items():close(v,out['shared_features'][n])
        close(sum(areas.values()),row['total_area_um2']);v=complete_variant(row['graph'],dict(state=row['state_query'],cuts=row['cuts']));violation=nonarithmetic(row,source,binding,control,target)
        for cut,native in zip(v['cuts'],out['stages'],strict=True):
            rs=[r for r in regions if r['stage']==cut['stage']];interior={n for r in rs for n in r['additions']};roots={r['root'] for r in rs}
            arcs=[a|dict(wire_point_ps=policy['inter_arithmetic_wire_point_ps'] if a['owner']=='inter_arithmetic' else 0.) for a in connections(row['graph'],cut,row['queries']) if not (a['sink_kind']=='operator' and a['sink'] in interior)]
            for a in arcs:
                if a['source_kind']=='operator' and a['source'] in interior and a['source'] not in roots:raise ValueError('observed G interior')
            for r in rs:
                for j,term in enumerate(r['terms']):
                    groups=defaultdict(list)
                    for n,b,c in term:groups[n].append([b,c])
                    for n,bits in sorted(groups.items()):arcs.append(dict(source_kind='launch',source=n,sink_kind='operator',sink=r['root'],operand_index=j,bit_pairs=bits,owner='S_boundary',wire_point_ps=0.,G_region_input=True))
            if arcs!=native['connections']:raise ValueError('G/S independent exact bit-arc inventory differs')
            counts['arcs']+=len(arcs);preds=defaultdict(list);captures=defaultdict(list)
            for a in arcs:(preds if a['sink_kind']=='operator' else captures)[a['sink']].append(a)
            capture_owner='external_state' if cut['stage']==len(v['cuts'])-1 else 'native_state'
            def boundary(n,pure):
                is_native=any(not s['valid'] and not s['external_capture'] and s['origin']==n and s['stage']==cut['stage'] for s in row['state_query']['slots'])
                return policy['forward_boundary_point_ps' if pure else 'boundary_point_ps'][('native_state' if is_native else 'input_service')+'->'+capture_owner]
            memo={}
            def arrive(n,guard=False):
                if (n,guard) not in memo:
                    memo[n,guard]=max((boundary(a['source'],False) if a['source_kind']=='launch' else arrive(a['source'],guard)+policy['inter_arithmetic_wire_point_ps'] for a in preds[n]),default=0.)+prices[n]['operator_delay_ps']+(prices[n]['delay_reserve_ps'] if guard else 0.)
                return memo[n,guard]
            expected={}
            for n,edges in captures.items():
                def maximum(guard):return max(boundary(a['source'],True) if a['source_kind']=='launch' else arrive(a['source'],guard) for a in edges)
                point=maximum(False);margin=policy['reserve']['joint_reserve_ps'];expected[n]=dict(node=n,point_required_period_ps=point,point_slack_ps=target-point,legacy_node_guard_required_period_ps=maximum(True),decision_required_period_ps=point+margin,decision_slack_ps=target-point-margin,joint_reserve_ps=margin);violation=max(violation,point+margin-target)
            if set(expected)!={c['node'] for c in native['captures']}:raise ValueError('G capture inventory differs')
            for capture in native['captures']:
                for k,x in expected[capture['node']].items():close(x,capture[k])
        close(violation,row['timing_violation_ps']);scores.append((violation,sum(areas.values()),row['view']));counts['candidates']+=1
    feasible=any(v==0 for v,_,_ in scores);best=min((0. if feasible else v,area,name) for v,area,name in scores if not feasible or v==0)
    if best[2]!=report['selected_view']:raise ValueError('D objective/ranking differs from independent exhaustive oracle')
    close(best[1],report['selected_area_um2']);close(best[0],report['selected_timing_violation_ps'])
    selected=next(r for r in report['candidates'] if r['view']==report['selected_view'])
    fields=('root','stage','output_bits','terms','members','additions','features','policy')
    a=report['artifact']['emitted_G_regions'];b=selected['estimate']['G_regions']
    if [{k:r[k] for k in fields} for r in a]!=[{k:r[k] for k in fields} for r in b]:raise ValueError('emission and prediction use different G regions')
    return dict(target_ps=target,selected=best[2],area_um2=best[1],violation_ps=best[0],counts=dict(counts))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--outputs',type=Path,required=True);p.add_argument('--source-request',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    bundle=read(a.bundle);source=read(a.source_request)['source'];rows=[]
    for report in sorted(a.outputs.glob('*/selection.json')):
        r=read(report);rows.append(audit(r,source,bundle,a.bundle.resolve().parent))
        if sha(report.parent/'D.sv')!=r['artifact']['rtl_sha256']:raise ValueError('D RTL identity changed')
    if not rows:raise ValueError('no actual D outputs')
    write(a.out,dict(status='passed',rows=rows,physical_PPA_used=False,full_D_ready=False));print('FUSED_D_ORACLE_PASS targets='+str(len(rows)),flush=True)


if __name__=='__main__':main()
