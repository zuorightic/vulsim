"""Separate node, maximum-sum, boundary/wire and area errors on real pilots.

The result is a validation diagnosis.  A source/placement failure or incomplete
coverage cannot be turned into an independent joint qualification by this tool.
"""
import argparse
from collections import Counter,defaultdict
import math
from pathlib import Path

from .model_fast_preflight import read,write,sha
from .model_qualification_labels import canonical
from .model_physical_path_v2 import verify_combinational_arc
from .operator_condition_model import query
from .stage7_physical_prepare import compose
from .stage67_physical_readout_v1 import table
from . import backend
from . import model_logical_ownership_v2 as logical_ownership
from .platforms import profile
from .stage67_physical_probe_v1 import SUFFIX


def finite(value):
    v=float(value)
    if not math.isfinite(v):raise ValueError('nonfinite path value')
    return v


def verify_ownership_packet(owners):
    aliases={}
    for n in owners['instances']:
        if n.startswith('external_capture/'):aliases[n]='observer/__external__/'+n[len('external_capture/'):]
        elif n.startswith('core/') and not any(n.startswith(p) for p in owners['scopes'].values()):aliases[n]='capture/__native__/'+n[len('core/'):]
    if aliases!=owners['proof_aliases']:raise ValueError('forged ownership proof namespace')
    def pin(n):
        cell,term=n.rsplit('/',1);return aliases.get(cell,cell)+'/'+term
    packet=dict(origin='physical_snapshot',period_ps=1500,time_to_ps=1,instances={aliases.get(n,n):m for n,m in owners['instances'].items()},
        liberty=owners['liberty'],connections={pin(n):v for n,v in owners['connections'].items()},clock_nets=owners['clock_nets'],
        nodes={},pin_logic={},data_requests={},data_paths={})
    normalized=logical_ownership.normalize(packet,owners['scopes'],{})
    cert=logical_ownership.resolve(normalized,owners['scopes'],owners['top_ports'])
    if not cert['complete'] or cert!=owners['certificate']:raise ValueError('forged/stale full-census ownership certificate')
    reverse={v:k for k,v in aliases.items()};expected={reverse.get(n,n):('external_state' if o=='observer' else o) for n,o in cert['owners'].items()}
    if expected!=owners['owners']:raise ValueError('physical owner assignment differs from certificate')


def path_partition(points,owners,allowed_start,expected_end,independent_node=None):
    instances=owners['instances'];liberty=owners['liberty'];nets=owners['connections'];ports=owners['top_ports'];scope=owners['scopes']
    data=[(canonical(n),finite(t)) for n,t in points]
    start=[i for i,(n,_) in enumerate(data) if n in set(map(canonical,allowed_start))]
    if len(start)!=1 or not data or data[-1][0]!=canonical(expected_end):raise ValueError('timing witness has no unique declared start/end')
    data=data[start[0]:]
    if len(data)<2:raise ValueError('empty path witness')
    def pin(name):
        if name in ports:
            row=ports[name];return dict(cell=None,term=name,owner='top',direction='output' if row['direction']=='input' else 'input',net=row['net'],sequential=False)
        cell,terminal=name.rsplit('/',1)
        if cell not in instances or instances[cell] not in liberty or name not in nets:raise ValueError('unknown actual timing terminal')
        meta=liberty[instances[cell]];p=meta['pins'].get(terminal)
        if p is None or p['direction']!=nets[name]['direction']:raise ValueError('Liberty/census timing direction mismatch')
        return dict(cell=cell,term=terminal,owner=owners['owners'][cell],direction=p['direction'],net=nets[name]['net'],sequential=meta['sequential'])
    totals=defaultdict(float);nodes=defaultdict(float);order=[];segments=[]
    for i,((a,ta),(b,tb)) in enumerate(zip(data,data[1:])):
        left,right=pin(a),pin(b);delay=tb-ta
        if delay < -1e-5:raise ValueError('negative timing increment')
        if (i and left['sequential']) or (i!=len(data)-2 and right['sequential']):raise ValueError('path traverses an intermediate register')
        if left['cell'] is not None and left['cell']==right['cell']:
            verify_combinational_arc(liberty[instances[left['cell']]],left['term'],right['term']);owner=left['owner'];kind='node_cell' if owner in scope else 'boundary_cell'
        else:
            if left['direction']!='output' or right['direction']!='input' or left['net']!=right['net'] or left['net'].startswith('<unconnected'):
                raise ValueError('path does not follow an actual connected net')
            if left['owner']==right['owner']:
                owner=left['owner'];kind='node_wire' if owner in scope else 'boundary_wire'
            else:owner=left['owner']+'->'+right['owner'];kind='inter_owner_wire'
        totals[kind+':'+owner]+=delay
        if kind in ('node_cell','node_wire'):
            nodes[owner]+=delay
            if not order or order[-1]!=owner:
                if owner in order:raise ValueError('physical path reenters a DAG node')
                order.append(owner)
        if independent_node is not None and (left['owner']!=independent_node or right['owner']!=independent_node):raise ValueError('independent node path includes another owner')
        segments.append(dict(from_pin=a,to_pin=b,kind=kind,owner=owner,delay_ps=delay))
    total=data[-1][1]-data[0][1]
    if not math.isclose(math.fsum(s['delay_ps'] for s in segments),total,rel_tol=1e-12,abs_tol=1e-6):raise ValueError('path delay ownership does not conserve')
    if independent_node is not None and abs(data[0][1])>1e-5:raise ValueError('independent node origin is not zero')
    return dict(delay_ps=total,node_delay_ps=dict(nodes),node_order=order,totals_ps=dict(totals),segments=segments,
        start=data[0][0],end=data[-1][0],start_arrival_ps=data[0][1],end_arrival_ps=data[-1][1],increments_owned_once=True)


def parse_stage(folder):
    owners=read(folder/'ownership.json');requests=read(folder/'requests.json');state=read(folder/'mapped-state.json')
    verify_ownership_packet(owners)
    if (folder/'timing_full_before.tsv').read_bytes()!=(folder/'timing_full_after.tsv').read_bytes():raise ValueError('node probes changed full paths')
    endpoints=table(folder/'timing_endpoints.tsv');node_bounds={n:{k:set() for k in ('inputs','outputs','constants')} for n in owners['scopes']}
    logic={};by_net=defaultdict(list)
    for name,row in owners['connections'].items():by_net[row['net']].append(name)
    top_nets={row['net'] for row in owners['top_ports'].values()}
    for row in endpoints:
        node,pin=row['node'],canonical(row['pin'])
        if node not in node_bounds or pin in logic:raise ValueError('unexpected/duplicate node boundary')
        logic[pin]=row['logic'];node_bounds[node][row['kind']].add(pin)
    for node in node_bounds:
        actual={k:set() for k in ('inputs','outputs','constants')}
        for pin,connection in owners['connections'].items():
            cell=pin.rsplit('/',1)[0]
            if owners['owners'][cell]!=node:continue
            cross=connection['net'] in top_nets or any(owners['owners'][other.rsplit('/',1)[0]]!=node for other in by_net[connection['net']])
            if not cross:continue
            if pin not in logic or logic[pin] not in ('0','1','X'):raise ValueError('boundary lacks constant/dynamic evidence')
            kind='constants' if logic[pin] in ('0','1') else 'inputs' if connection['direction']=='input' else 'outputs'
            actual[kind].add(pin)
        if actual!=node_bounds[node]:raise ValueError('node physical endpoint census mismatch')
    paths=[];node_paths=defaultdict(dict)
    for row in table(folder/'timing_independent_nodes.tsv'):
        node=row['request'];end=canonical(row['endpoint'])
        if node not in node_bounds or end not in node_bounds[node]['outputs'] or end in node_paths[node]:raise ValueError('independent endpoint missing/duplicate')
        file=folder/row['points']
        if file.parent!=folder:raise ValueError('path file escapes report directory')
        points=[line.split('\t') for line in file.read_text().splitlines()]
        part=path_partition(points,owners,node_bounds[node]['inputs'],end,node);node_paths[node][end]=part
    for node,bound in node_bounds.items():
        if set(node_paths[node])!=bound['outputs']:raise ValueError('independent maximum lacks an output')
    seen=defaultdict(set)
    for row in table(folder/'timing_full_before.tsv'):
        identifier=row['request'];req=requests[identifier];end=canonical(row['endpoint'])
        targets=set(map(canonical,req['to_pins']+req['to_ports']))
        if end not in targets or end in seen[identifier]:raise ValueError('functional endpoint mismatch/duplicate')
        seen[identifier].add(end);points=[line.split('\t') for line in (folder/row['points']).read_text().splitlines()]
        part=path_partition(points,owners,req['from_pins']+req['from_ports'],end)
        part.update(request=identifier,path_class=req['path_class'],stage=req['stage'],word=req['word'],slack_ps=finite(row['slack']),points_sha256=sha(folder/row['points']))
        paths.append(part)
    if set(seen)!=set(requests) or any(seen[n]!=set(map(canonical,q['to_pins']+q['to_ports'])) for n,q in requests.items()):raise ValueError('functional dynamic endpoint inventory incomplete')
    areas=defaultdict(float);ff=Counter()
    for name,master in owners['instances'].items():
        owner=owners['owners'][name];cell=owners['liberty'][master];areas[owner]+=cell['area_um2']
        if cell['sequential']:ff[owner]+=1
    if dict(ff)!=state['owner_FF_bits']:raise ValueError('actual state FF owners differ from semantic projection')
    nodes={n:dict(operator_delay_ps=max(p['delay_ps'] for p in node_paths[n].values()),comb_area_um2=areas[n],dynamic_outputs=len(node_paths[n])) for n in node_bounds}
    return dict(status='passed_strict_stage_readout',nodes=nodes,owner_area_um2=dict(areas),owner_FF_bits=dict(ff),
        total_area_um2=math.fsum(areas.values()),functional_paths=paths,node_paths=dict(node_paths),
        endpoint_checks=sum(map(len,seen.values())),probe_invariance=True,strict_actual_Liberty_arcs=True,
        stages_restart_at_registers=True,area_and_path_increments_owned_once=True,full_D_ready=False)


def analyze(root,result):
    if result.exists():raise ValueError('preserve prior analysis')
    result.mkdir(parents=True);admission=read(root/'admission.json');previous=Path(admission['parent']);software=previous/'software';model=read(admission['model']['path'])
    coverage=[];gaps=Counter();statuses=Counter()
    for export_path in sorted(software.glob('*/export.json')):
        export=read(export_path)
        for variant in export['variants']:
            for target in variant['targets']:
                prices=[dict(node=q['trace']['node'],**query(model,q['descriptor'])) for q in target['queries']]
                for p in prices:
                    statuses[p['status']]+=1
                    if p['status']!='covered':gaps[p['reason']]+=1
                baseline=compose(export,variant,target,prices)
                coverage.append(dict(source=export_path.parent.name,placement=variant['id'],target_ps=target['target_ps'],prices=prices,zero_G=baseline))
    write(result/'software-coverage.json',dict(status='passed_real_model_query_audit',queries=dict(statuses),uncovered_reasons=dict(gaps),
        rows=coverage,model_sha256=admission['model']['sha256'],S_binding_sha256=admission['S_binding']['sha256'],full_D_ready=False))
    points=[]
    for task in admission['tasks']:
        bank=root/'runs'/task['id'];pointer=bank/'physical-directory.json';directory=Path(read(pointer)['path']) if pointer.exists() else bank
        baseline=read(Path(task['input_directory'])/'baseline.json');prices={'node_'+str(p['node']):p for p in baseline['prices']}
        stage_labels={}
        for stage in ('synth','grt'):
            label=parse_stage(root/'readout-v1'/task['id']/stage)
            g=backend.stage_metrics(directory/'reports'/SUFFIX,stage,read(directory/'liberty_cells.json')['cells'],1500,selected=profile('asap7'))
            if abs(label['total_area_um2']-g['cell_area_um2'])>1e-5:raise ValueError('exclusive areas differ from whole stage')
            label['whole_shell_metrics']=g;write(result/(task['id']+'-'+stage+'-labels.json'),label);stage_labels[stage]=label
        actual=stage_labels['grt'];node_errors={}
        for node,observed in actual['nodes'].items():
            p=prices[node]
            node_errors[node]=dict(predicted_delay_ps=p['operator_delay_ps'],observed_delay_ps=observed['operator_delay_ps'],
                delay_error=abs(p['operator_delay_ps']-observed['operator_delay_ps'])/max(10,observed['operator_delay_ps']),
                predicted_area_um2=p['comb_area_um2'],observed_area_um2=observed['comb_area_um2'],
                area_error=abs(p['comb_area_um2']-observed['comb_area_um2'])/max(.01,observed['comb_area_um2']),reserve_ps=p['delay_reserve_ps'])
        witnesses=[]
        for p in actual['functional_paths']:
            if not p['node_order']:continue
            independent=math.fsum(actual['nodes'][n]['operator_delay_ps'] for n in p['node_order'])
            observed=math.fsum(p['node_delay_ps'].values());predicted=math.fsum(prices[n]['operator_delay_ps'] for n in p['node_order'])
            witnesses.append(dict(path_class=p['path_class'],stage=p['stage'],endpoint=p['end'],slack_ps=p['slack_ps'],node_order=p['node_order'],
                observed_node_segment_sum_ps=observed,observed_independent_max_sum_ps=independent,
                independent_max_sum_conservatism_ps=independent-observed,predicted_node_sum_ps=predicted,
                node_function_error_on_independent_max_sum_ps=predicted-independent,
                empirical_reserves_ps=math.fsum(prices[n]['delay_reserve_ps'] for n in p['node_order']),
                observed_complete_required_period_ps=1500-p['slack_ps'],
                observed_nonnode_boundary_wire_clock_ps=1500-p['slack_ps']-observed))
        zero=baseline['zero_G'];predicted_area=zero['total_area_um2'];observed_area=actual['total_area_um2'];class_rows=[]
        for stage in zero['stages']:
            physical_paths=[p for p in actual['functional_paths'] if p['stage']==stage['stage'] and p['node_order'] and p['path_class'] in ('native_data','external_data')]
            if not physical_paths:raise ValueError('arithmetic stage lacks measured capture paths')
            # compose() already stores full predicted capture slack, including
            # its DAG arrival and the S capture budget exactly once.
            predicted_required=max(1500-p['slack_ps'] for p in stage['captures'])
            actual_needed=max(1500-p['slack_ps'] for p in physical_paths)
            class_rows.append(dict(stage=stage['stage'],predicted_required_period_ps=predicted_required,observed_required_period_ps=actual_needed,
                relative_error=abs(predicted_required-actual_needed)/max(10,actual_needed),predicted_setup_slack_ps=1500-predicted_required,
                observed_setup_slack_ps=1500-actual_needed,false_feasible=predicted_required<=1500<actual_needed,
                conservative_rejection=actual_needed<=1500<predicted_required))
        nonnode_areas={n:dict(predicted_um2=zero['owners_um2'].get(n,0),observed_um2=actual['owner_area_um2'].get(n,0)) for n in zero['owners_um2'] if n!='operators'}
        points.append(dict(task=task['id'],source='serial',placement=task['placement'],target_ps=1500,node_errors=node_errors,
            S_shared_areas=nonnode_areas,total_area=dict(predicted_um2=predicted_area,observed_um2=observed_area,relative_error=abs(predicted_area-observed_area)/max(.01,observed_area)),
            arithmetic_stages=class_rows,witness_decomposition=witnesses,whole_shell=actual['whole_shell_metrics'],
            state_FF_bits=actual['owner_FF_bits'],S_reset_enable_qualification='pending_actual_function_check',
            zero_G=0,full_D_ready=False))
    # This finite one-source pilot cannot release the independent joint domain.
    quality_failures=[]
    for p in points:
        if p['total_area']['relative_error']>.35:quality_failures.append(p['task']+'/total_area_error_above_P95_gate')
        for stage in p['arithmetic_stages']:
            if stage['relative_error']>.35:quality_failures.append(p['task']+'/stage'+str(stage['stage'])+'_delay_error_above_P95_gate')
            if stage['false_feasible']:quality_failures.append(p['task']+'/false_feasible')
    report=dict(version='stage67-pilot-zero-G-diagnosis-v1',status='pilot_quality_failed' if quality_failures else 'pilot_numerical_gates_passed_not_independent',
        measured_points=2,complete_sources=1,clock_ps=1500,coverage_uncovered_nodes=sum(gaps.values()),
        failures=quality_failures,points=points,independent_joint_tests_unlocked=False,S_coefficients_changed=False,node_model_changed=False,
        zero_G_joint_qualified=False,full_D_ready=False)
    write(result/'pilot-diagnosis.json',report)
    print(dict(status=report['status'],points=2,query_status=dict(statuses),failures=quality_failures,full_D_ready=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--result',type=Path,required=True);a=p.parse_args();analyze(a.root.resolve(),a.result.resolve())
