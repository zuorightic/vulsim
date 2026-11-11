"""Semantic composition checks on real graphs and exact synthetic bit maps."""
import argparse
from copy import deepcopy
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write
from experiments.arithmetic_dse.stage67_owned_timing_v1 import connections


def run(native,out):
    if out.exists():raise ValueError('preserve semantic check attempt')
    out.mkdir(parents=True);data=read(native);positive=[];negative=[];cuts_checked=0;inserted=0
    def rejected(name,fn):
        try:fn()
        except (ValueError,KeyError):negative.append(name)
        else:raise ValueError('accepted malformed bit map '+name)
    for source in data['sources']:
        for variant in source['variants']:
            target=next(t for t in variant['targets'] if t['target_ps']==1500)
            if target['owned_timing']['status']!='candidate_covered':continue
            for cut in variant['cuts']:
                expected=connections(variant['graph'],cut,target['queries']);graph=deepcopy(variant['graph']);changed=deepcopy(cut)
                fresh=max(n['id'] for n in graph['nodes'])+1;extra=[]
                for n in graph['nodes']:
                    if n['id'] not in cut['members']:continue
                    for o in n['operands']:
                        if o['kind']!='symbol':continue
                        extra.append(dict(id=fresh,width=o['width'],kind='assign',known_zero=[],known_one=[],lo=0,hi=0,bit=0,operands=[deepcopy(o)]))
                        o['node']=fresh;changed['members'].append(fresh);fresh+=1;inserted+=1
                graph['nodes']+=extra
                if expected!=connections(graph,changed,target['queries']):raise ValueError('redundant aliases changed real normalized bit connections')
                launches=set(cut['launches'])
                if any(e['source_kind']=='operator' and e['source'] in launches for e in expected):raise ValueError('register cut failed to reset arrival origin')
                if any(e['owner']=='inter_arithmetic' and e['sink_kind']!='operator' for e in expected):raise ValueError('state edge billed as operator wire')
                cuts_checked+=1
    positive+=['real_graph_redundant_alias_insertion','actual_register_cuts_restart_at_launch','state_wires_excluded_from_inter_operator_charge']
    def node(i,w,k,ops=(),**kw):return dict(id=i,width=w,kind=k,known_zero=[],known_one=[],operands=list(ops),lo=0,hi=0,bit=0)|kw
    def ref(i,w):return dict(kind='symbol',node=i,width=w,signed=False)
    def literal(w,bits):return dict(kind='literal',width=w,signed=False,bits=bits)
    # A shared four-bit source is shifted, zero padded and truncated; the
    # common origin fans out to two operand relationships and one capture.
    graph=dict(nodes=[node(0,4,'input'),node(1,4,'mul',[ref(0,4),ref(0,4)]),
        node(2,8,'concat',[literal(2,[0,0]),ref(1,4),literal(2,[0,0])]),
        node(3,5,'trunc',[ref(2,8)]),node(4,5,'add',[ref(3,5),ref(3,5)]),node(5,4,'cast',[ref(1,4)])])
    cut=dict(stage=0,members=[1,2,3,4,5],launches=[0],captures=[dict(node=4),dict(node=5)])
    queries=[dict(trace=dict(stage=0,node=i),descriptor=dict(local_context=dict(producer=dict(result_width=w)))) for i,w in ((1,4),(4,5))]
    arcs=connections(graph,cut,queries);shared=[e for e in arcs if e['owner']=='inter_arithmetic']
    assert len(shared)==2 and all(e['source']==1 and e['sink']==4 and e['bit_pairs']==[[0,2],[1,3],[2,4]] for e in shared)
    assert len([e for e in arcs if e['source']==1])==3
    positive+=['shift_padding_truncation_preserves_exact_bit_map','shared_origin_preserves_operand_fanout_and_capture']
    bad=deepcopy(graph);bad['nodes'][2]['operands'][1]['signed']=True;rejected('signed_mapping',lambda:connections(bad,cut,queries))
    bad=deepcopy(graph);bad['nodes'][3]['kind']='unpriced_logic';rejected('unsupported_wire',lambda:connections(bad,cut,queries))
    bad=deepcopy(graph);bad['nodes'][3]['operands'][0]['node']=999;rejected('missing_node',lambda:connections(bad,cut,queries))
    bad=deepcopy(graph);bad['nodes'][3]['operands'][0]['node']=3;rejected('wire_cycle',lambda:connections(bad,cut,queries))
    bad=deepcopy(graph);bad['nodes'][3].update(kind='slice',lo=6);rejected('out_of_range_slice',lambda:connections(bad,cut,queries))
    bad=deepcopy(graph);bad['nodes'][3]['known_one']=[1];bad['nodes'][3]['known_zero']=[1];rejected('contradictory_known_bits',lambda:connections(bad,cut,queries))
    result=dict(status='passed_owned_timing_semantics',real_cuts=cuts_checked,redundant_aliases_inserted=inserted,positives=positive,negatives=negative,
        physical_calls=0,full_D_ready=False)
    write(out/'proof.json',result);print(result,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.native.resolve(),a.out.resolve())
