"""Preregister fresh synthetic combinations; no physical prices or EDA."""
import argparse
from functools import lru_cache
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import write,sha


def prepare(out):
    if out.exists():raise ValueError('preserve preparation')
    out.mkdir(parents=True)
    cases=[
        dict(name='serial',nodes=[dict(op='mul',a=8,b=8,r=16,inputs=[]),dict(op='add',a=40,b=32,r=41,inputs=[0]),dict(op='add',a=64,b=41,r=64,inputs=[1])],captures=[2],stages=[[0,1,2]]),
        dict(name='parallel',nodes=[dict(op='mul',a=8,b=8,r=16,inputs=[]),dict(op='mul',a=16,b=16,r=32,inputs=[]),dict(op='add',a=48,b=64,r=64,inputs=[0,1])],captures=[2],stages=[[0,1,2]]),
        dict(name='shared',nodes=[dict(op='mul',a=8,b=8,r=16,inputs=[]),dict(op='add',a=32,b=32,r=33,inputs=[0,0])],captures=[0,1],stages=[[0,1]],correlation='same arithmetic value bound twice; node label and S ownership must be checked before G'),
        dict(name='wide_reduction',nodes=[dict(op='mul',a=8,b=8,r=16,inputs=[]),dict(op='mul',a=16,b=16,r=32,inputs=[]),dict(op='add',a=64,b=64,r=64,inputs=[0,1])],captures=[2],stages=[[0,1,2]],mapping_shifts=[48,16]),
        dict(name='bypass',nodes=[dict(op='mul',a=16,b=16,r=32,inputs=[]),dict(op='add',a=32,b=64,r=64,inputs=[0])],captures=[0,1],stages=[[0,1]],separate_bypass_capture_bits=29),
        dict(name='cross_stage_saved_value',nodes=[dict(op='mul',a=8,b=8,r=16,inputs=[]),dict(op='add',a=64,b=64,r=64,inputs=[0]),dict(op='add',a=64,b=16,r=64,inputs=[1,0])],captures=[2],stages=[[0],[1,2]],saved_value=dict(node=0,through_stage=1),extra_capture_banks=2)
    ]
    checks=[]
    def stage_values(case,delay):
        values=[]
        for stage,members in enumerate(case['stages']):
            inside=set(members);launch=11.+stage
            @lru_cache(None)
            def arrival(i):
                if i not in inside:return launch
                return max((arrival(j)+1 for j in case['nodes'][i]['inputs']),default=launch)+delay[i]
            def paths(i):
                if i not in inside:return [([],1)]
                parents=case['nodes'][i]['inputs']
                if not parents:return [([i],0)]
                return [(p+[i],edges+(1 if p else 0)) for j in parents for p,edges in paths(j)]
            endpoints=[i for i in members if i in case['captures'] or any(i in n['inputs'] for j,n in enumerate(case['nodes']) if j not in inside)]
            for end in endpoints:
                enumerated=launch+max(sum(delay[i] for i in p)+edges for p,edges in paths(end))
                if enumerated!=arrival(end):raise ValueError('stage-cut path oracle differs from DAG arrival')
            values.append(dict(stage=stage,launch_ps=launch,capture_required_ps=480.,
                captures=[dict(node=i,arrival_ps=arrival(i),slack_ps=480.-arrival(i)) for i in endpoints]))
        return values
    for case in cases:
        nodes=case['nodes']
        # Test fixture costs deliberately unrelated to a physical model.
        delay=[7.+i for i in range(len(nodes))];area=[3.+2*i for i in range(len(nodes))]
        @lru_cache(None)
        def arrival(i):return max((arrival(j)+1 for j in nodes[i]['inputs']),default=0)+delay[i]
        def paths(i):
            return [p+[i] for j in nodes[i]['inputs'] for p in paths(j)] if nodes[i]['inputs'] else [[i]]
        for capture in case['captures']:
            enumerated=max(sum(delay[i] for i in p)+len(p)-1 for p in paths(capture))
            if enumerated!=arrival(capture):raise ValueError('DAG propagation and path enumeration differ')
        reached=set()
        def walk(i):
            reached.add(i)
            for j in nodes[i]['inputs']:walk(j)
        for i in case['captures']:walk(i)
        unique_area=sum(area[i] for i in reached)
        path_area=sum(area[i] for end in case['captures'] for p in paths(end) for i in p)
        if case['name']=='shared' and path_area<=unique_area:raise ValueError('shared-node negative lost duplication')
        stages=stage_values(case,delay)
        if case['name']=='cross_stage_saved_value':
            changed=delay[:];changed[0]=1007.;shifted=stage_values(case,changed)
            if stages[1]!=shifted[1] or stages[1]['captures'][0]['arrival_ps']!=31.:
                raise ValueError('previous-stage arithmetic delay crossed a register boundary')
        checks.append(dict(case=case['name'],unique_area=unique_area,path_sum_area=path_area,
            combinational_arrivals=[arrival(i) for i in case['captures']],stage_boundaries=stages,mode='TEST_ONLY'))
    write(out/'combination-protocol.json',dict(version='operator-state-DAG-zero-correction-preparation-v2',cases=cases,
        clocks_ps=[500,1500,3000],source_role='new synthetic combination qualification, never arithmetic fit/test',
        physical_admission_allowed=False,frozen_operator_model=None,
        S_sha256=sha(ROOT/'experiments/arithmetic/evidence/step7_general_state_v1/asap7-general-state.json'),
        reuse='real ConditionalBoundaryProvider and native DAG/unique area path; fixture oracle only prepares software checks',
        zero_G_first=True,error_partition=['actual node price/label and load','independent node maxima conservatism','S/register/control and wire boundary','ownership or duplicate/missing area','remaining stable selection-relevant residual'],
        prephysical_requirements=['qualified operator function and supported node queries','actual public materialization and S query','explicit hierarchy and state/port census','exact source/role/T/endpoint admission and funded retained artifacts'],
        full_D_ready=False))
    write(out/'proof.json',dict(status='passed_preparation_only',cases=len(cases),checks=checks,
        physical_labels_read=False,new_EDA_calls=0,actual_model_joint_qualified=False,full_D_ready=False))
    print(dict(status='passed_preparation_only',cases=len(cases),new_EDA_calls=0),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();prepare(a.out.resolve())
