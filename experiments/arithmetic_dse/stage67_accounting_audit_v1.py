"""Training-only derivation of exclusive S/data-wire point estimates.

No synthesis, routing or consumed test is read.  The candidate is deliberately
unqualified: original S areas, control guards and node parameters are retained.
"""
import argparse
from collections import defaultdict
import math
from pathlib import Path
import statistics

from .model_fast_preflight import read,write,sha
from .conditional_boundary_binding import frozen_fit,raw_context,SUFFIX
from .model_physical_path_v2 import canonical,verify_combinational_arc

ROOT=Path(__file__).resolve().parents[2]
DEFAULT_NODE_FIT=Path('/home/zyrv/vulsim-artifacts/operator-conditional-wide-20261110-v1/fit-data.json')


def state_path(directory,path,period):
    pins,instances,nets=raw_context(str(directory),'grt')
    prefix=directory/'reports'/SUFFIX/'vulsim_grt'
    file=Path(str(prefix)+'_reference_'+path['id']+'_points.tsv')
    points=[(canonical(n),float(v)) for n,v in (line.split('\t') for line in file.read_text().splitlines())]
    positions=[i for i,(n,_) in enumerate(points) if n==canonical(path['start_pin'])]
    if len(positions)!=1 or points[-1][0]!=canonical(path['end_pin']):raise ValueError('S training path boundary differs')
    points=points[positions[0]:];adapter=0.;wire=0.;segments=[]
    for (left,ta),(right,tb) in zip(points,points[1:]):
        ca,pa=left.rsplit('/',1);cb,pb=right.rsplit('/',1);increment=tb-ta
        if not math.isfinite(increment) or increment < -1e-5:raise ValueError('invalid S physical arrival increment')
        if ca==cb:verify_combinational_arc(pins[instances[ca]],pa,pb)
        elif left not in nets or right not in nets or nets[left]['direction']!='output' or nets[right]['direction']!='input' or nets[left]['net']!=nets[right]['net']:
            raise ValueError('S training wire is not connected')
        is_adapter=ca.startswith('adapter/') and cb.startswith('adapter/')
        if is_adapter:adapter+=increment
        elif ca!=cb:wire+=increment
        segments.append(dict(from_pin=left,to_pin=right,delay_ps=increment,source_adapter_internal=is_adapter))
    value=period-path['slack_ps']-adapter
    if not math.isfinite(value) or value<0:raise ValueError('invalid S point boundary')
    return dict(value_ps=value,full_required_period_ps=period-path['slack_ps'],slack_ps=path['slack_ps'],
        source_adapter_internal_ps=adapter,remaining_data_wire_ps=wire,
        path_sha256=sha(file),actual_arcs_and_nets_verified=True,segments=segments)


def derive(out,model,binding,node_fit=DEFAULT_NODE_FIT):
    if out.exists():raise ValueError('preserve accounting derivation')
    out.mkdir(parents=True);fit,fit_hash=frozen_fit();runs={r['task_id']:r for r in fit['runs']};state_groups=defaultdict(lambda:defaultdict(list));state_rows=[]
    roles={'birth_data':'input_service->native_state','native_data':'native_state->native_state','external_data':'native_state->external_state'}
    for row in fit['rows']:
        if row['split']!='train' or row['stage']!='grt':continue
        directory=Path(runs[row['task_id']]['directory'])
        if sha(directory/'manifest.json')!=row['manifest_sha256']:raise ValueError('S training physical manifest changed')
        for path in row['boundary_paths']:
            if path['id'] not in roles:continue
            value=state_path(directory,path,row['period_ps']);role=roles[path['id']]
            state_groups[role][row['source_group']].append(value['value_ps'])
            state_rows.append(dict(source=row['source_group'],role='train',task=row['task_id'],target_ps=row['period_ps'],path_class=path['id'],boundary_role=role,**value))
        raw_context.cache_clear()
    boundaries={};group_values={}
    for role,groups in state_groups.items():
        medians={name:statistics.median(v) for name,v in groups.items()}
        boundaries[role]=statistics.median(medians.values());group_values[role]=medians
    if set(boundaries)!=set(roles.values()):raise ValueError('missing S boundary role')
    data=read(node_fit);wire_groups=defaultdict(list);wire_rows=[]
    if data.get('independent_labels_read'):raise ValueError('node fitting snapshot includes independent labels')
    for row in data['rows']:
        if row['role']!='train' or row['stage']!='grt':continue
        label_path=Path(row['measurement_path'])/'grt-labels.json'
        if sha(label_path)!=row['label_sha256']:raise ValueError('frozen arithmetic training label changed')
        label=read(label_path);nodes=set(label['nodes']);values=[]
        for path in label['path_decompositions']:
            for segment in path['segments']:
                pair=segment['owner'].split('->')
                if segment['kind']=='inter_owner_wire' and len(pair)==2 and set(pair)<=nodes:
                    value=segment['delay_ps']
                    if not math.isfinite(value) or value<0:raise ValueError('invalid arithmetic inter-owner wire')
                    values.append(value)
        if values:
            wire_groups[row['source_group']].append(statistics.median(values))
            wire_rows.append(dict(source=row['source_group'],role='train',target_ps=row['target_ps'],label_sha256=row['label_sha256'],
                median_inter_arithmetic_wire_ps=statistics.median(values),wire_values_ps=values))
    if not wire_groups:raise ValueError('no qualified training inter-arithmetic wire')
    wire_medians={name:statistics.median(v) for name,v in wire_groups.items()};wire=statistics.median(wire_medians.values());old=read(binding)
    candidate=dict(version='owned-composition-timing-v1',quality_status='candidate_accounting',full_D_ready=False,
        operator_model_sha256=sha(model),S_binding_sha256=sha(binding),state_model_sha256=old['state_model']['sha256'],
        target_interval_ps=[500,3000],boundary_point_ps=boundaries,inter_arithmetic_wire_point_ps=wire,
        reserve=dict(kind='validation_max_positive_stage_residual_plus_engineering',engineering_ps=50.,joint_reserve_ps=50.,calibration_status='not_calibrated'),
        ownership=dict(node='cell arcs and intra-node wires',S='full register-data boundary including state gates, Q/setup/clock and adjacent data wires',
            inter_arithmetic='one scalar propagation edge per source/sink arithmetic relationship after exact bit mapping',
            pure_bit_connections='zero intrinsic delay; load and bit mapping preserved',nonarithmetic='inherit original real S control/service/bypass checks'),
        derivation=dict(S_train_fit_sha256=fit_hash,node_fit_sha256=sha(node_fit),parameter_rule='median per whole training source, then median across sources',
            old_S_coefficients_changed=False,node_parameters_changed=False,consumed_tests_read=False,pilot_labels_used_for_point_parameters=False))
    write(out/'candidate.json',candidate);write(out/'training-audit.json',dict(state_rows=state_rows,state_source_medians=group_values,
        arithmetic_wire_rows=wire_rows,arithmetic_wire_source_medians=wire_medians,S_train_fit_sha256=fit_hash,node_fit_sha256=sha(node_fit),
        only_train_for_point_parameters=True,physical_calls=0,full_D_ready=False))
    print(dict(status='derived_train_only_owned_accounting',S_boundary_point_ps=boundaries,wire_point_ps=wire,
        state_paths=len(state_rows),wire_points=len(wire_rows),wire_sources=len(wire_groups),full_D_ready=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--model',type=Path,required=True);p.add_argument('--binding',type=Path,required=True);a=p.parse_args();derive(a.out.resolve(),a.model.resolve(),a.binding.resolve())
