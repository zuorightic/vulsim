"""Acceptance of real stage7 preparation, never physical/model qualification."""
import argparse
from collections import Counter
from copy import deepcopy
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse.stage7_physical_prepare import compose,OWNERS


def verify(out,result):
    if result.exists():raise ValueError('preserve verification')
    result.mkdir(parents=True)
    deps=read(out/'dependencies.json');structures=read(out/'structures.json');protocol=read(out/'protocol.json')
    for name,digest in deps['preparation_sources'].items():
        assert sha(ROOT/name)==digest,('changed preparation',name)
    for kind in ('model','S_binding'):
        assert sha(Path(deps[kind]['path']))==deps[kind]['sha256'],kind
    assert len(structures['rows'])==16
    assert Counter(r['role'] for r in structures['rows'])=={'combination_validation':12,'locked_joint_test':4}
    assert not protocol['physical_admission_allowed'] and not protocol['full_D_ready']
    sim=read(out/'receipts'/(out.name+'-simulate')/'commands.json')[0]
    assert sim['exit_code']==0 and 'STAGE7_REAL_RTL_PASS cores=16 cycles=192' in Path(sim['log']).read_text()
    checks=[];negative=[];cut_checks=0;shared_checks=0
    for row in structures['rows']:
        assert sha(out/row['rtl'])==row['rtl_sha256']
        assert sha(out/row['endpoint_contract'])==row['endpoint_sha256']
        d=out/'sources'/row['source'];source=read(d/'request.json');e=read(d/'native/export.json')
        assert sha(Path(source['source']))==source['source_sha256']==row['source_sha256']
        v=next(v for v in e['variants'] if v['id']==row['placement']);assert v['state']['materialized_checked']
        assert v['state']['layout_sha256']==row['layout_sha256'];assert len(v['cuts'])==2
        nodes={n['id']:n for n in e['graph']['nodes']};target=deepcopy(v['targets'][1])
        # Deliberately software-only boundary/price fixtures, over the ACTUAL
        # optimized graph/cut. An independent path-list oracle checks max/sum.
        fixture=[]
        for n in e['arithmetic_nodes']:fixture.append(dict(node=n,status='covered',conservative_operator_delay_ps=7+n/10,comb_area_um2=3+n/10))
        b=target['real_S_candidate'];b.update(covered=True,reason='TEST_ONLY real-graph recurrence oracle',owners_um2={k:1. for k in OWNERS if k!='operators'})
        b['stages']=[]
        for cut in v['cuts']:
            b['stages'].append(dict(cut_sha256=cut['sha256'],launches=[dict(node=n,ps=11.) for n in cut['launches']],
                captures=[dict(node=n['node'],ps=480.) for n in cut['captures']],
                wires=[dict(zip(('from','to','ps'),[*edge,1.])) for edge in cut['edges']],other_timing_violation_ps=0.))
        score=compose(e,v,target,fixture);delays={p['node']:p['conservative_operator_delay_ps'] for p in fixture}
        assert score['owners_um2']['operators']==sum(p['comb_area_um2'] for p in fixture)
        for cut,stage in zip(v['cuts'],score['stages'],strict=True):
            launches=set(cut['launches'])
            def paths(n):
                if nodes[n]['constant']:return [([],0.,0.)]
                if n in launches:return [([],11.,0.)]
                parents=[p for p in nodes[n]['parents'] if not nodes[p]['constant']]
                if not parents:return [([n],0.,0.)]
                return [(path+[n],launch,wire+1.) for p in parents for path,launch,wire in paths(p)]
            for endpoint in stage['captures']:
                alternatives=paths(endpoint['node']);exact=max(launch+wire+sum(delays.get(n,0.) for n in path) for path,launch,wire in alternatives)
                assert abs(exact-endpoint['arrival_ps'])<1e-9
                cut_checks+=1
                if len(alternatives)>1:shared_checks+=1
        before=score['stages'][1];changed=deepcopy(fixture)
        earlier={n for n in e['arithmetic_nodes'] if v['placement'][n]==0}
        for p in changed:
            if p['node'] in earlier:p['conservative_operator_delay_ps']+=1000000
        assert compose(e,v,target,changed)['stages'][1]==before,'delay crossed a register cut'
        for name,modify in (
            ('duplicate_node',lambda t,p:p.append(deepcopy(p[0]))),
            ('missing_node',lambda t,p:p.pop()),
            ('missing_owner',lambda t,p:t['real_S_candidate']['owners_um2'].pop('root_repair')),
            ('forged_cut',lambda t,p:t['real_S_candidate']['stages'][0].update(cut_sha256='0'*64)),
            ('missing_wire',lambda t,p:next(s for s in t['real_S_candidate']['stages'] if s['wires'])['wires'].pop()),
            ('missing_capture',lambda t,p:next(s for s in t['real_S_candidate']['stages'] if s['captures'])['captures'].pop())):
            t,p=deepcopy(target),deepcopy(fixture);modify(t,p)
            try:compose(e,v,t,p)
            except ValueError:negative.append(row['id']+'/'+name)
            else:raise AssertionError('accepted invalid '+name)
        checks.append(dict(structure=row['id'],native_registers=len(v['registers']),state_materialized=True,cut_oracle=True,price_fixture_only=True))
    diagnostic=read(out/'coverage-diagnostic.json');gaps=Counter()
    for r in diagnostic['rows']:
        for t in r['rows']:
            for p in t['prices']:
                if p['status']!='covered':gaps[p['reason']]+=1
    model=read(Path(deps['model']['path']))
    blockers=[]
    if any(o['status']!='passed_independent' for o in model['operations'].values()):blockers.append('frozen node candidate is awaiting independent qualification')
    if gaps:blockers.append('uncovered actual node queries; see exact coverage diagnostic')
    blockers += ['no funded exact physical pilot admission yet','mapped endpoint/state/owner/CEC qualification will be checked on pilot synth snapshot']
    # Every cell below is pending, never an invented zero physical result.
    acceptance=[]
    for item in protocol['primary_matrix']:
        acceptance.append(dict(**item,status='not_measured',state_retention=None,endpoint_coverage=None,exclusive_owner_conservation=None,
            node_error=None,independent_max_conservatism=None,boundary_wire_error=None,full_stage_delay_area_error=None,
            false_feasible=None,conservative_rejection=None,paired_ranking=None,hold_ps=None))
    write(result/'acceptance-table.json',dict(version='stage7-physical-acceptance-table-v1',rows=acceptance,never_interpret_null_as_zero=True))
    write(result/'proof.json',dict(status='passed_real_RTL_preparation_only',sources=8,validation_sources=6,locked_sources=2,
        native_placements=16,simulation_cycles_per_placement=192,stage_capture_path_oracle_checks=cut_checks,multiple_path_checks=shared_checks,
        negative_rejections=len(negative),checks=checks,negative_checks=negative,model_query_status=diagnostic['summary'],uncovered_reasons=dict(gaps),
        physical_admission_blockers=blockers,physical_calls=0,physical_endpoint_qualification=False,zero_G_qualified=False,full_D_ready=False))
    print(dict(status='passed_real_RTL_preparation_only',placements=16,negative_rejections=len(negative),gaps=dict(gaps)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--result',type=Path,required=True);a=p.parse_args();verify(a.out.resolve(),a.result.resolve())
