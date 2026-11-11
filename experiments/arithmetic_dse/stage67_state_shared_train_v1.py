"""Train-only state-boundary and shared-area successor; no validation access."""
import argparse
import ast
from collections import Counter,defaultdict
from copy import deepcopy
import csv
import math
from pathlib import Path
import statistics

from .model_fast_preflight import read,write,sha,key
from .conditional_boundary_binding import frozen_fit,raw_context,SUFFIX
from .model_physical_path_v2 import canonical,verify_combinational_arc
from .model_context_samples import layout
from .operator_condition_model import query
from .model_fast_measurement import known_result

ROOT=Path(__file__).resolve().parents[2]
OLD=Path('/home/zyrv/vulsim-artifacts/stage67-accounting-20261111-v1/validation-initial/candidate-calibrated.json')
NODE_FIT=Path('/home/zyrv/vulsim-artifacts/operator-conditional-wide-20261110-v1/fit-data.json')
BINDING=Path('/home/zyrv/vulsim-artifacts/conditional-boundary-20261110-v3/binding-candidate.json')
NODE=ROOT/'experiments/arithmetic/models/asap7_conditional_operators_v1/operators.json'
MODELS={'shared_clock':['one','total_FF_bits','predicted_functional_area_um2'],'shared_physical':['one','predicted_functional_area_um2'],
    'root_repair':['one','input_data_bits','total_FF_bits','reset_one_bits']}


def table(path):return list(csv.DictReader(Path(path).read_text().splitlines(),delimiter='\t'))


def trace_roots(instances,pins,nets,owners):
    """Final non-root loads, with actual complete signal-net driver checks."""
    by_net=defaultdict(list)
    for pin,row in nets.items():by_net[row['net']].append(pin)
    roots={n for n,o in owners.items() if o=='root_repair'};memo={};visiting=set();proof={}
    def downstream(name):
        if name in memo:return memo[name]
        if name in visiting:raise ValueError('cyclic physical root branch')
        visiting.add(name);cell=pins[instances[name]];roles=set();terminals=[];links={}
        if cell['sequential'] or not(cell.get('buffer_or_inverter') or cell.get('constant_driver') or not any(v['direction']=='input' for v in cell['pins'].values())):raise ValueError('root is not unary/constant repair')
        for term,meta in cell['pins'].items():
            if meta['direction'] not in ('input','output'):continue
            full=name+'/'+term
            if full not in nets or nets[full]['direction']!=meta['direction']:raise ValueError('missing actual root signal pin')
            net=nets[full]['net'];peers=by_net[net];drivers=[p for p in peers if nets[p]['direction']=='output'];loads=[p for p in peers if nets[p]['direction']=='input']
            if net.startswith('<unconnected'):
                if meta['direction']!='output':raise ValueError('unconnected root input')
                links[term]=dict(net=net,drivers=[full],loads=[],unconnected_output=True);roles.add('top_or_unobserved');continue
            if len(drivers)>1:raise ValueError('ambiguous root net '+repr((name,term,net,drivers)))
            links[term]=dict(net=net,drivers=drivers,loads=loads)
            if meta['direction']=='output':
                if drivers!=[full]:raise ValueError('root output not unique driver')
                for pin in loads:
                    child=pin.rsplit('/',1)[0]
                    if child==name:raise ValueError('self-connected root')
                    if child in roots:roles.update(downstream(child))
                    else:roles.add(owners[child]);terminals.append(pin)
                if not loads:roles.add('top_or_unobserved')
        if not roles:raise ValueError('root has no final observed owner')
        visiting.remove(name);memo[name]=roles;proof[name]=dict(master=instances[name],sink_owners=sorted(roles),
            immediate_terminal_loads=sorted(terminals),pins=links,instrumentation_only=roles<={'source_adapter','observer'})
        return roles
    for name in sorted(roots):downstream(name)
    return proof


def primitive_areas(pins):
    xor=[];ff=[]
    def parity(function,inputs):
        expression=ast.parse(function.replace('*','&').replace('+','|').replace('!','~'),mode='eval')
        def value(node,env):
            if isinstance(node,ast.Name):return env[node.id]
            if isinstance(node,ast.Constant) and node.value in (0,1):return node.value
            if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.Invert):return 1-value(node.operand,env)
            if isinstance(node,ast.BinOp):
                a,b=value(node.left,env),value(node.right,env)
                if isinstance(node.op,ast.BitAnd):return a&b
                if isinstance(node.op,ast.BitOr):return a|b
                if isinstance(node.op,ast.BitXor):return a^b
            raise ValueError('unsupported primitive Boolean expression')
        try:truth=[value(expression.body,dict(zip(inputs,(a,b)))) for a,b in ((0,0),(0,1),(1,0),(1,1))]
        except (ValueError,KeyError):return False
        return truth in ([0,1,1,0],[1,0,0,1])
    for cell in pins.values():
        inputs=[p for p,v in cell['pins'].items() if v['direction']=='input'];outs=[v.get('function') or '' for v in cell['pins'].values() if v['direction']=='output']
        if not cell['sequential'] and len(inputs)==2 and len(outs)==1 and outs[0] and parity(outs[0],inputs):xor.append(cell['area_um2'])
        if cell['sequential'] and len(cell.get('clock_pins',[]))==1 and len(cell.get('data_pins',[]))==1 and len(inputs)==2:ff.append(cell['area_um2'])
    if not xor or not ff:raise ValueError('missing semantic XOR/FF primitive baseline')
    return dict(xor2_min_area_um2=min(xor),plain_FF_min_area_um2=min(ff),selection='minimum matching actual Liberty function class; never cell-name whitelist')


def state_area(model,owner,features):
    m=model['stages']['grt']['area_models'][owner]
    if m['kind']!='nonnegative_linear':raise ValueError('unsupported frozen S point area')
    return math.fsum(c*features[n] for n,c in zip(m['features'],m['coefficients'],strict=True))


def state_rows(fit,S):
    runs={r['task_id']:r for r in fit['runs']};areas=[];paths=[];primitives=None
    roles={'birth_data':'input_service->native_state','native_data':'native_state->native_state','external_data':'native_state->external_state'}
    for row in fit['rows']:
        if row['split']!='train' or row['stage']!='grt':continue
        d=Path(runs[row['task_id']]['directory'])
        if sha(d/'manifest.json')!=row['manifest_sha256']:raise ValueError('S train snapshot changed')
        pins,instances,nets=raw_context(str(d),'grt');ownership=read(d/'general-grt-ownership.json')
        owners={canonical(v['instance']):('root_repair' if v['owner']=='root_boundary_repair' else v['owner']) for v in ownership['ownership']}
        # The old S partition follows clock drivers backwards from FFs. CTS
        # dummy loads have dangling outputs and therefore are not ancestors
        # of an FF; classify them from actual clock-net incidence, as the
        # current arithmetic readout does. Names never determine this move.
        clock_nets={v['net'] for pin,v in nets.items() if owners[pin.rsplit('/',1)[0]]=='shared_clock'}
        clock_moved=[]
        for name,owner in list(owners.items()):
            cell=pins.get(instances[name])
            if owner=='root_repair' and cell and cell['buffer_or_inverter'] and any(nets.get(name+'/'+p,{}).get('net') in clock_nets for p,v in cell['pins'].items() if v['direction']=='input'):
                owners[name]='shared_clock';clock_moved.append(name)
        proof=trace_roots(instances,pins,nets,owners);primitives=primitives or primitive_areas(pins);spec=read(d/'general-state-contract.json')['spec']
        allFF=sum(v['state_bits'] for v in row['owner_features'].values());ones=sum(v['reset_one_bits'] for v in row['owner_features'].values())
        # Synthetic logic is represented by semantic gate counts, not its
        # measured area. Production arithmetic comes from the frozen node f.
        xor_pairs={(min(a,b),max(a,b)) for w in spec['words'] for a,b in zip(w['source_positions'],w['source_positions_second'])}
        adapter_area=len(xor_pairs)*primitives['xor2_min_area_um2'];observer_area=max(0,allFF-1)*primitives['xor2_min_area_um2']
        functional=math.fsum(state_area(S,o,f) for o,f in row['owner_features'].items())+adapter_area+observer_area
        label={k:row['owner_area_um2'].get(k,0) for k in ('shared_clock','shared_physical')}
        clock_area=math.fsum(pins[instances[n]]['area_um2'] for n in clock_moved);label['shared_clock']+=clock_area
        label['root_repair']=math.fsum(v['area_um2'] for v in ownership['ownership'] if owners[canonical(v['instance'])]=='root_repair' and not proof[canonical(v['instance'])]['instrumentation_only'])
        areas.append(dict(source='S/'+row['source_group'],role='train',target_ps=row['period_ps'],
            features=dict(one=1.,total_FF_bits=allFF,input_data_bits=row['owner_features']['input_service']['data_bits'],reset_one_bits=ones,predicted_functional_area_um2=functional),
            labels=label,full_root_repair_area_um2=row['owner_area_um2'].get('root_boundary_repair',0),root_proof=proof,
            snapshot_manifest_sha256=row['manifest_sha256'],semantic_instrumentation_area_um2=adapter_area+observer_area,
            clock_incident_loads_reassigned=clock_moved,clock_reassigned_area_um2=clock_area,
            complete_census_sha256=key(dict(instances=instances,nets=nets,owners=owners))))
        prefix=d/'reports'/SUFFIX/'vulsim_grt'
        for path in row['boundary_paths']:
            if path['id'] not in roles:continue
            file=Path(str(prefix)+'_reference_'+path['id']+'_points.tsv')
            if sha(file)!=path['points_sha256']:raise ValueError('S training witness changed')
            points=[(canonical(a),float(t)) for a,t in (line.split('\t') for line in file.read_text().splitlines())];start=canonical(path['start_pin']);end=canonical(path['end_pin'])
            positions=[i for i,(a,_) in enumerate(points) if a==start]
            if len(positions)!=1 or points[-1][0]!=end:raise ValueError('unique declared Q/D needed')
            segments=[];removed=0
            def excluded(cell):return owners[cell]=='source_adapter' or (cell in proof and proof[cell]['instrumentation_only'])
            for (left,a),(right,b) in zip(points[positions[0]:],points[positions[0]+1:]):
                x,p=left.rsplit('/',1);y,q=right.rsplit('/',1);delay=b-a
                if not math.isfinite(delay) or delay< -1e-5:raise ValueError('invalid physical delay')
                if x==y:verify_combinational_arc(pins[instances[x]],p,q)
                elif nets[left]['direction']!='output' or nets[right]['direction']!='input' or nets[left]['net']!=nets[right]['net']:raise ValueError('disconnected actual path')
                # An edge entirely inside instrumentation is also excluded;
                # every cross-boundary wire remains in the full S boundary.
                drop=excluded(x) and excluded(y)
                if drop:removed+=delay
                segments.append(dict(from_pin=left,to_pin=right,delay_ps=delay,excluded_instrumentation=drop))
            value=row['period_ps']-path['slack_ps']-removed
            if value<0:raise ValueError('negative corrected S point')
            paths.append(dict(source=row['source_group'],role='train',target_ps=row['period_ps'],path_class=path['id'],boundary_role=roles[path['id']],
                full_required_period_ps=row['period_ps']-path['slack_ps'],removed_instrumentation_ps=removed,value_ps=value,segments=segments,witness_sha256=sha(file),actual_arcs_and_nets_verified=True))
        raw_context.cache_clear()
    return areas,paths,primitives


def local_node_query(spec,flow):
    r=spec['result_width']
    return dict(version='arithmetic-operator-query-v1',semantics='unsigned-modulo-v1',declared_result_width=r,required_result_bits=list(range(r)),
        local_context=dict(producer=spec,consumers=[],captures=[dict(banks=1,declared_width=r,result_bit_map=list(range(r)))]),
        topology=dict(operand_shared_input_roots=0,same_stage_remaining_depth=1),flow_context=flow)


def node_rows(data,S,model,primitives):
    rows=[];omitted=[]
    for row in data['rows']:
        if row['role']!='train' or row['stage']!='grt':continue
        p=Path(row['measurement_path']);label_path=p/'grt-labels.json'
        if sha(label_path)!=row['label_sha256']:raise ValueError('original node train label changed')
        label=read(label_path);g=layout(row['descriptor']['local_context']);n=g['input_bits'];capture=sum(len(c['live_tokens']) for c in g['captures']);allFF=n+capture+2
        prefix=p/'reports'/SUFFIX/'context_grt';instances={canonical(a):b for a,b in (line.split('\t') for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines())}
        pins=read(p/'liberty-pins.json');nets={canonical(v['instance'])+'/'+v['pin']:dict(direction=v['direction'].lower(),net=canonical(v['net'])) for v in table(str(prefix)+'_connections.tsv')}
        scopes=read(p/'query-contract.json')['nodes'];owners={}
        clocks={v['net'] for v in table(str(prefix)+'_clock_nets.tsv')}
        for name,master in instances.items():
            cell=pins.get(master)
            if cell is None:owners[name]='shared_physical';continue
            if cell['buffer_or_inverter'] and any(nets.get(name+'/'+t,{}).get('net') in clocks for t in cell['pins']):owners[name]='shared_clock'
            elif any(name.startswith(v) for v in scopes.values()):owners[name]='arithmetic'
            elif name.startswith('launch/'):owners[name]='input_service'
            elif name.startswith('capture/'):owners[name]='native_state'
            elif name.startswith('observer/'):owners[name]='observer'
            elif '/' not in name and not cell['sequential']:owners[name]='root_repair'
            else:raise ValueError('unowned original node train cell')
        proof=trace_roots(instances,pins,nets,owners)
        repair=math.fsum(pins[instances[name]]['area_um2'] for name,v in proof.items() if not v['instrumentation_only'])
        input_features=dict(data_bits=n,data_signals=1,valid_bits=1,enable_domains=1,reset_one_bits=0)
        valid_features=dict(data_bits=0,data_signals=0,valid_bits=1,enable_domains=0,reset_one_bits=0)
        priced=[query(model,row['descriptor'])]+[query(model,local_node_query(c['spec'],row['descriptor']['flow_context'])) for c in row['descriptor']['local_context']['consumers']]
        feature=dict(one=1.,total_FF_bits=allFF,input_data_bits=n,reset_one_bits=0)
        if all(v['status']=='covered' for v in priced):
            # Capture data in these shells is an unconditional unreset FF;
            # its valid bit follows the original reset-bearing S protocol.
            functional=state_area(S,'input_service',input_features)+capture*primitives['plain_FF_min_area_um2']+state_area(S,'external_state',valid_features)
            functional+=math.fsum(v['comb_area_um2'] for v in priced)+max(0,capture-1)*primitives['xor2_min_area_um2'];feature['predicted_functional_area_um2']=functional
        else:omitted.append(dict(source=row['source_group'],target_ps=row['target_ps'],component='shared_physical',reason='one required arithmetic node lacks frozen function coverage'))
        rows.append(dict(source='node/'+row['source_group'],role='train',target_ps=row['target_ps'],features=feature,
            labels=dict(shared_clock=label['owner_area_um2'].get('shared_clock',0),shared_physical=label['owner_area_um2'].get('shared_physical',0),root_repair=repair),
            full_root_repair_area_um2=label['owner_area_um2'].get('root_repair',0),root_proof=proof,raw_label_sha256=row['label_sha256'],
            semantic_FF_census=dict(input=n+1,capture=capture+1),complete_census_sha256=key(dict(instances=instances,nets=nets,owners=owners))))
    return rows,omitted


def fit_shared(rows):
    import numpy as np
    from scipy.optimize import nnls
    result={}
    for owner,names in MODELS.items():
        eligible=[r for r in rows if all(n in r['features'] for n in names)];counts=Counter(r['source'] for r in eligible)
        weights=np.asarray([1/math.sqrt(counts[r['source']]) for r in eligible]);x=np.asarray([[r['features'][n] for n in names] for r in eligible]);y=np.asarray([r['labels'][owner] for r in eligible]);coefficients,_=nnls(x*weights[:,None],y*weights)
        result[owner]=dict(kind='nonnegative_linear',features=names,coefficients=list(map(float,coefficients)),
            numeric_support={n:[min(r['features'][n] for r in eligible),max(r['features'][n] for r in eligible)] for n in names},
            training_rows=len(eligible),training_sources=len(counts),objective='source-balanced train-only squared error; fixed feature set, no validation selection')
    return result


def derive(out):
    if out.exists():raise ValueError('preserve train derivation attempt')
    out.mkdir(parents=True);fit,h=frozen_fit();old=read(OLD);model=read(NODE);S=read(BINDING.parent/'reused-S.json');data=read(NODE_FIT)
    if data['independent_labels_read']:raise ValueError('node dataset must be fitting only')
    s_rows,paths,primitives=state_rows(fit,S);n_rows,omitted=node_rows(data,S,model,primitives);rows=s_rows+n_rows;shared=fit_shared(rows)
    groups=defaultdict(lambda:defaultdict(list))
    for row in paths:groups[row['boundary_role']][row['source']].append(row['value_ps'])
    boundaries={role:statistics.median(statistics.median(values) for values in sources.values()) for role,sources in groups.items()}
    candidate=deepcopy(old);candidate.update(version='factored-state-shared-v1',boundary_point_ps=boundaries,shared_area_models=shared,
        area_features='one,input_data_bits,total_FF_bits,reset_one_bits,predicted_functional_area_um2; production graph and frozen S/node functions only',
        parent_policy_sha256=sha(OLD),training_primitive_baseline=primitives)
    candidate['forward_boundary_point_ps']=dict(boundaries)
    candidate['forward_boundary_point_ps']['input_service->native_state']=boundaries['native_state->native_state']
    candidate['forward_scope']='pure register-to-register data transfer; reuse native_data FF-Q/capture-state class, no birth adapter path; all dynamic state banks enumerated'
    candidate['derivation'].update(S_train_fit_sha256=h,node_fit_sha256=sha(NODE_FIT),root_policy='exclude only branches whose complete final non-root loads are adapter/observer; keep all state or mixed responsibilities',
        shared_models='simple train-only source-balanced NNLS; clock additionally includes semantic functional footprint',node_parameters_changed=False,old_S_coefficients_changed=False,validation_labels_read=False,
        birth_data_remains_arithmetic_load_diagnostic=True,pure_forwarding_uses_existing_native_data_class=True)
    candidate['reserve'].update(calibration_status='inherited_50ps_not_recalibrated_for_successor',joint_reserve_ps=50.)
    write(out/'candidate.json',candidate);write(out/'training-audit.json',dict(version='state-shared-training-audit-v1',area_rows=rows,path_rows=paths,omitted_component_rows=omitted,primitive_baseline=primitives,
        S_train_fit_sha256=h,node_fit_sha256=sha(NODE_FIT),only_train=True,validation_labels_read=False,physical_calls=0,full_D_ready=False))
    print(dict(status='derived_factored_state_shared_train_candidate',S_boundary_point_ps=boundaries,
        shared_models=shared,S_rows=len(s_rows),node_rows=len(n_rows),omitted_physical_rows=len(omitted),full_D_ready=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();derive(a.out.resolve())
