"""Frozen v10 runtime functions; extracted without numerical edits from workload_diagnostic.py."""
import json

import math

from .workload_abcd import static_node

from .workload_v10 import MODEL_SHA

from . import wide_arithmetic as arithmetic, wide_alu_geometry as alu

from . import flow_structure_features as circuits, transition_incidence_features_v10 as v10_features

from . import semantic_fanout_features_v8 as fanout, semantic_reset_features_v9 as spans

from . import centered_response as response

from .prospective_cell_cover import cover

from .prospective_logic import Circuit

VERSION = 'workload-v10-complete-diagnostic-v1'


S_FEATURES = ['log2_logical_sinks','native_launch','log2_global_FF','log2_enabled_words',
              'capture_bank_reset_fraction','source_bank_reset_fraction','log2_target',
              'clock_pressure','native_logical_load','native_log_target']


def key(value): return json.dumps(value,sort_keys=True,separators=(',',':'))


def s_features(f):
    result = {n:float(f[n]) for n in S_FEATURES if n in f}
    result['log2_global_FF'] = math.log2(f['total_FF_bits']+1.)
    result['log2_enabled_words'] = math.log2(f['enabled_word_count']+1.)
    result['native_logical_load'] = f['native_launch']*f['log2_logical_sinks']
    result['native_log_target'] = f['native_launch']*f['log2_target']
    return result


def base_features(spec, target, local):
    """Numerical v2 adapter; all actual sink roles and mappings remain present."""
    f = arithmetic.features(spec,target); g = alu.geometry(spec); f.update(g['features'])
    used = g['used']
    if arithmetic.permutation(spec) == [1,0]: used = dict(lhs=used['rhs'],rhs=used['lhs'])
    for name,bits in used.items():
        f[name+'_live_bits']=float(len(bits));f['log2_'+name+'_live_bits']=math.log2(len(bits)+1.)
    z,o = arithmetic.known_result(spec)
    dynamic = set(g['dynamic_outputs']) if not g['mul'] else {i for i in range(spec['result_width']) if not ((z|o)>>i&1)}
    f.update(dynamic_result_bits=float(len(dynamic)),capture_banks=0.,capture_bits=0.,
             consumer_count=float(len(local['consumers'])),consumer_arithmetic_width=0.,
             consumer_operand_pin_uses=0.,consumer_mapping_position_mean=0.)
    uses=position=0.
    for cap in local['captures']:
        f['capture_banks']+=cap['banks'];f['capture_bits']+=cap['banks']*sum(type(b) is int and b in dynamic for b in cap['result_bit_map'])
    for c in local['consumers']:
        width = c['spec']['arithmetic_width'] if c.get('spec') else max(len(b['result_bit_map']) for b in c['bindings'])
        f['consumer_arithmetic_width']=max(f['consumer_arithmetic_width'],width)
        for binding in c['bindings']:
            for i,bit in enumerate(binding['result_bit_map']):
                if type(bit) is int and bit in dynamic:
                    uses+=1.;position+=i/max(1,width-1)
    f['consumer_operand_pin_uses']=uses;f['consumer_mapping_position_mean']=position/max(1.,uses)
    a,b=f['lhs_live_bits'],f['rhs_live_bits'];w=f['arithmetic_width']; pressure=f['clock_pressure']
    f.update(live_input_sum=a+b,log2_live_input_sum=math.log2(a+b+1.),operand_live_min=min(a,b),operand_live_max=max(a,b),
        log2_value_width=math.log2(f['value_width']+1.),result_high_fraction=f['result_lo']/w,
        log2_alu_work=math.log2(f['alu_work']+1.),pressure_alu_work=f['alu_work']*pressure,
        log2_operand_live_min=math.log2(min(a,b)+1.),log2_demand_hi=math.log2(spec['result_lo']+spec['value_width']+1.),
        compare_eq_work=f['predicate_eq']*max(a,b),compare_le_work=f['predicate_le']*max(a,b),
        compare_order_work=(1-f['predicate_eq'])*max(a,b))
    f['consumer_conditioning_proxy']=math.log2(f['consumer_arithmetic_width']+1.)*(1-f['consumer_mapping_position_mean'])
    f['consumer_load_work']=uses*f['consumer_conditioning_proxy']
    aa,bb=set(g['used']['lhs']),set(g['used']['rhs'])
    f['alu_overlap_fraction']=len(aa&bb)/max(1,len(aa|bb))
    return f


def operator_cover_features(spec, f):
    c,outputs = circuits.operator_circuit(spec); work=c.work(outputs); cov=cover(c,outputs)
    f.update({'cover_'+n:v for n,v in cov.items()})
    f.update(log2_cover_work=math.log2(cov['cells']+1.),
             cover_pressure_response=math.log2(1+cov['cells']/64)*f['clock_pressure'],
             cover_T_response=math.log2(1+cov['cells']/64)*f['log2_target'],
             cover_compound_fraction=cov['compound_cells']/max(1,cov['cells']),
             cover_wide_fraction=cov['wide_cells']/max(1,cov['cells']))
    f.update({'fanout_'+n:v for n,v in fanout.graph_loads(c,outputs).items()})
    f['fanout_repair_pressure']=f['fanout_internal_log2_repair_excess']*f['clock_pressure']
    f.update({'cone_'+n:v for n,v in spans.cone_spans(c,outputs).items()})
    f['cone_cut_pressure']=f['cone_log2_peak_cut']*f['clock_pressure']
    return cov,work


class DiagnosticPrices:
    def __init__(self,bundle):
        if bundle['version'] != VERSION or bundle['v10_sha256'] != MODEL_SHA:
            raise ValueError('diagnostic model identity mismatch')
        self.bundle=bundle; self.v10=bundle['v10']
        self.operator=self.v10['inherited_flow']['inherited_centered']['semantic_operator_model']
        self.cache={}
        self.reduction_geometry_cache={}

    def _linear(self,model,f):
        return math.fsum([model.get('intercept',0.)]+[c*f[n] for n,c in zip(model['features'],model['coefficients'],strict=True)])

    def operator_price(self,q):
        identity=('operator',key(q))
        if identity in self.cache:return self.cache[identity]
        spec=q['local_context']['producer'];arithmetic.validate(spec)
        if q['version'] != 'arithmetic-workload-query-v2' or q['flow_context']['profile_sha256'] != self.bundle['profile_sha256']:
            raise ValueError('actual v2 query/profile required')
        f=base_features(spec,q['flow_context']['target_period_ps'],q['local_context'])
        alias=arithmetic.aliases(spec)
        family='add' if spec['operation'] in ('add','adc') else 'compare' if spec['operation'] in ('ult','ule','eq') else spec['operation']
        exact = alias is not None or f['dynamic_result_bits']==0
        flags=[]
        if exact:
            d=a=0.; flags.append('proven_constant_or_wire_alias')
        else:
            m=self.operator['functions'][family]
            d=self._linear(m['delay_ps'],f);a=self._linear(m['area_um2'],f)
            if family in ('add','mux'):
                cov,work=operator_cover_features(spec,f)
                entry=self.v10['models']['Add' if family=='add' else 'Mux']
                value=response.predict(entry['function'],f)
                if family=='add': a=value*f[entry['reference']]
                else: d=value
                if not work['work']:
                    d=a=0.;exact=True;flags.append('constant_folded_Boolean_wire')
            else:
                cov=None
            if not exact:
                # One shared numerical floor rule; no application-specific repair.
                floor_d=self.bundle['numerical_floors']['gate_delay_ps']*max(1.,f['alu_depth'])
                floor_a=self.bundle['numerical_floors']['gate_area_um2']*max(1.,f['alu_work'])
                if family=='mul':
                    floor_d=self.bundle['numerical_floors']['gate_delay_ps'];floor_a=self.bundle['numerical_floors']['gate_area_um2']
                    # Known-one partial products also create addition work.
                    nonzero={p:[i for i in range(spec[p+'_width']) if arithmetic.bit_values(spec,p,i)!=(0,)] for p in ('lhs','rhs')}
                    terms=sum(i+j<spec['result_lo']+spec['value_width'] for i in nonzero['lhs'] for j in nonzero['rhs'])
                    if terms>f['retained_product_terms']:
                        f=dict(f,retained_product_terms=float(terms),pressure_product_terms=terms*f['clock_pressure'])
                        a=self._linear(m['area_um2'],f);flags.append('known_one_partial_product_work')
                if d<floor_d or a<floor_a:flags.append('shared_positive_Boolean_floor')
                d=max(floor_d,d);a=max(floor_a,a)
        result=dict(delay_ps=d,area_um2=a,source='v10 numerical functions + explicit v2 diagnostic adapter',
                    extrapolation=True,qualified=False,flags=flags)
        if not all(math.isfinite(v) and v>=0 for v in (d,a)):raise ValueError('invalid diagnostic operator price')
        self.cache[identity]=result;return result

    def reduction_price(self,q):
        # Normalize root *names* while preserving equality and bit positions.
        ids={};terms=[]
        for term in q['terms']:
            mapped=[]
            for source,bit,column in term:
                ids.setdefault(source,len(ids));mapped.append([ids[source],bit,column])
            terms.append(mapped)
        geometry=dict(q,terms=terms)
        identity=('G',key(geometry))
        if identity in self.cache:return self.cache[identity]
        # A sampling-window scan changes the period while querying the same
        # reduction. Cache the expensive circuit and coverage features by
        # normalized geometry, and keep the price cache keyed by the full query.
        geometry_key = key((geometry['output_bits'], terms))
        if geometry_key not in self.reduction_geometry_cache:
            self.reduction_geometry_cache[geometry_key] = v10_features.reduction_features(geometry)['intensive']
        f = v10_features.intensive_features_at_period(self.reduction_geometry_cache[geometry_key], q['target_ps'])
        entry=self.v10['models']['G']; values={}
        for name in ('area','delay'):
            e=entry[name];v=response.predict(e['function'],f)
            if e['reference'] is not None:v*=f[e['reference']]
            values[name]=v
        if min(values.values())<=0 or not all(map(math.isfinite,values.values())):
            raise ValueError('invalid G diagnostic response')
        result=dict(delay_ps=values['delay'],area_um2=values['area'],extrapolation=True,qualified=False,
                    source='v10 numerical G with actual terms; boundary/correlations diagnostic',
                    shared_input_root_pairs=q.get('shared_input_root_pairs',0))
        self.cache[identity]=result;return result


def functional_circuit(graph,i):
    """Exact local nonarithmetic logic, sharing repeated actual operand bits."""
    n=graph.nodes[i];op=n['operation'];width=n['width'];c=Circuit()
    def operand(a,w=None):
        bits=graph.operand(a);w=len(bits) if w is None else w
        return [int(v) if isinstance(v,str) else c.leaf(v) for v in (bits+('0',)*w)[:w]]
    args=[operand(a) for a in n['operands']]
    def resize(a):return (a+[0]*width)[:width]
    if op in ('and','or','xor'):
        outputs=[c.gate(op,a,b) for a,b in zip(resize(args[0]),resize(args[1]),strict=True)]
    elif op=='not':outputs=[c.gate('not',a) for a in resize(args[0])]
    elif op in ('land','lor','lnot'):
        def boolean(a):
            while len(a)>1:a=[c.gate('or',a[j],a[j+1] if j+1<len(a) else 0) for j in range(0,len(a),2)]
            return a[0]
        first=boolean(args[0]);v=c.gate('not',first) if op=='lnot' else c.gate('and' if op=='land' else 'or',first,boolean(args[1]))
        outputs=[v]+[0]*(width-1)
    elif op in ('shl','shr'):
        value=resize(args[0])
        for k,control in enumerate(args[1]):
            shift=1<<k
            shifted=([0]*min(width,shift)+value)[:width] if op=='shl' else (value[min(width,shift):]+[0]*width)[:width]
            value=[c.gate('or',c.gate('and',c.gate('not',control),a),c.gate('and',control,b)) for a,b in zip(value,shifted,strict=True)]
        outputs=value
    elif op=='neg': outputs,_=c.prefix([c.gate('not',a) for a in resize(args[0])],[0]*width,1)
    else:raise ValueError('unsupported functional owner '+op)
    return c,[outputs[b] for b in sorted(graph.demand[i])]


def state_projection(graph,state,L,target):
    # Valid slots carry the input graph node even at the external capture.
    # Its RTL name can differ from the source port after identifier sanitization.
    valid_origins = {slot['origin'] for slot in state['slots'] if slot['valid']}
    ports = [p for p in graph.ports if p['input'] and valid_origins.isdisjoint(p['nodes'])]
    widths=[p['width'] for p in ports];input_bits=sum(widths)
    owners={name:dict(data_bits=0,data_signals=0,valid_bits=0,enable_domains=0,reset_one_bits=0)
            for name in ('input_service','native_state','external_state')}
    owners['input_service'].update(data_bits=input_bits,data_signals=len(widths),valid_bits=1,enable_domains=len(widths)+1)
    words=[[] for _ in range(L)];ones=[0]*L
    for slot in state['slots']:
        f=owners['external_state' if slot['external_capture'] else 'native_state']
        if slot['valid']:f['valid_bits']+=slot['variable_bits'];continue
        f['data_bits']+=slot['variable_bits'];f['data_signals']+=int(slot['variable_bits']>0)
        mask=sum(int(x,16)<<(64*j) for j,x in enumerate(slot['variable_mask_hex']))
        reset=sum(int(x,16)<<(64*j) for j,x in enumerate(slot['reset_hex']))
        count=(mask&reset).bit_count();f['reset_one_bits']+=count
        if slot['variable_bits']:words[slot['stage']-1].append(slot['variable_bits']);ones[slot['stage']-1]+=count
    owners['native_state']['enable_domains']=sum(bool(w) for w in words[:-1])
    total=sum(f['data_bits']+f['valid_bits'] for f in owners.values())
    return dict(owners=owners,stage_words=words,stage_reset_one_bits=ones,input_widths=widths,
                total_FF_bits=total,L=L,target_ps=target)


def control_query(s,kind,stage,*,port_bits=None):
    target=s['target_ps'];words=s['stage_words'];total=s['total_FF_bits'];input_bits=sum(s['input_widths'])
    native=kind.startswith('native') and stage>0
    sinks=sum(words[stage]) if kind.startswith('native') else input_bits if kind=='input_valid' else 0
    count=len(words[stage]) if kind.startswith('native') else len(s['input_widths']) if kind=='input_valid' else 0
    ones=s['stage_reset_one_bits'][stage] if kind.startswith('native') else 0
    source_bits=sum(words[stage-1]) if native else input_bits
    source_ones=s['stage_reset_one_bits'][stage-1] if native else 0
    if port_bits is not None:sinks=port_bits;count=1;ones=0;native=False
    f=dict(total_FF_bits=total,enabled_word_count=count,native_launch=float(native),
           log2_logical_sinks=math.log2(sinks+2),capture_bank_reset_fraction=ones/max(1,sinks),
           source_bank_reset_fraction=source_ones/max(1,source_bits),log2_target=math.log2(target/500),clock_pressure=1500/target)
    return s_features(f)


def state_price(bundle,projection,comb_area):
    area={};models=bundle['S']['area_models'];valid=bundle['S']['valid_bit_area_um2']
    for name,f in projection['owners'].items():
        model=models[name]
        value=sum(f[n]*c for n,c in zip(model['features'],model['coefficients'],strict=True))
        if 'valid_bits' in model['features'] and model['coefficients'][model['features'].index('valid_bits')]==0:
            value+=valid*f['valid_bits']
        area[name]=value
    total_functional=comb_area+sum(area.values());inputs=projection['owners']['input_service']
    shared_f=dict(one=1.,total_FF_bits=projection['total_FF_bits'],sqrt_FF_bits=math.sqrt(projection['total_FF_bits']),
                  predicted_functional_area_um2=total_functional,clock_pressure=1500/projection['target_ps'],
                  input_data_bits=inputs['data_bits'],input_ports=inputs['data_signals'],
                  reset_one_bits=sum(f['reset_one_bits'] for f in projection['owners'].values()))
    for name,m in bundle['shared'].items():area[name]=sum(c*shared_f[n] for n,c in zip(m['features'],m['coefficients'],strict=True))
    controls=[];functions=bundle['S']['functions'];L=projection['L']
    for stage in range(L-1):
        for kind in ('native_enable','native_valid'):
            f=control_query(projection,kind,stage)
            controls.append(dict(stage=stage,path_class=kind,required_ps=response.predict(functions[kind],f),features=f))
    f=control_query(projection,'external_valid',L-1)
    controls.append(dict(stage=L-1,path_class='external_valid',required_ps=response.predict(functions['external_valid'],f),features=f))
    # Real external reset/write-enable ports are separate input-to-register
    # paths. Reusing the input_valid response is explicitly an unqualified
    # electrical-load proxy, rather than hiding these paths or setting zero.
    for name,bits in [('input_valid',sum(projection['input_widths'])),('reset_port_proxy',projection['total_FF_bits'])]+[
            ('input_write_enable_proxy',w) for w in projection['input_widths']]:
        f=control_query(projection,'input_valid',0,port_bits=bits)
        controls.append(dict(stage=-1,path_class=name,required_ps=response.predict(functions['input_valid'],f)/.8,features=f))
    boundary=bundle['S']['data_boundary_ps'];reserve=bundle['S']['joint_reserve_ps']
    controls.extend([dict(stage=-1,path_class='input_data_boundary_proxy',required_ps=boundary['input_service->native_state']/.8),
                     dict(stage=L,path_class='output_port_boundary_proxy',required_ps=boundary['native_state->external_state']/.8)])
    return dict(area_owners_um2=area,total_area_um2=comb_area+sum(area.values()),controls=controls,
                reserve_ps=reserve,extrapolation=True,qualified=False,projection=projection)


def evaluate(graph,view,state,owners,prices,*,static_cal=False,owner_queries=None):
    bundle=prices.bundle;L=state['internal_stages']+1;placement=view['placement'];target=owners['target_ps']
    if owners['graph_sha256'] != state['graph_sha256'] or owners['layout_sha256'] != state['layout_sha256']:
        raise ValueError('actual graph/state/owner identity differs')
    # A local request describes an equivalent characterization shell. The
    # outer target, state, placement, captures and all query semantics stay
    # unchanged. Keys are OWNER IDs: equal-shape instances may get different T.
    actual_queries={r['node']:r['query'] for r in owners['operators']}
    actual_queries.update({g['root']:g['query'] for g in owners['G_regions']})
    if owner_queries is not None:
        if state['features']['sdc_period_ps']!=target:
            raise ValueError('global state/owner target differs')
        if static_cal or set(owner_queries)!=set(actual_queries):
            raise ValueError('equivalent requests require exact dynamic owner coverage')
        for i,q in owner_queries.items():
            original=actual_queries[i]
            if 'flow_context' in q:
                flow=q['flow_context'];t=flow['target_period_ps']
                restored=dict(q,flow_context=dict(flow,
                    target_period_ps=original['flow_context']['target_period_ps'],
                    abc_target_ps=original['flow_context']['abc_target_ps']))
                consistent=flow['abc_target_ps']==t
            else:
                t=q['target_ps'];restored=dict(q,target_ps=original['target_ps']);consistent=True
            if not consistent or not math.isfinite(t) or t<=0 or restored!=original:
                raise ValueError('equivalent request changed non-T semantics')
        actual_queries=owner_queries
    delay={};area={};records=[];regions={g['root']:g for g in owners['G_regions']};members=set()
    bridge=bundle['static_bridge']['alpha']
    for region in regions.values():
        if members & set(region['members']):raise ValueError('duplicate G member ownership')
        members.update(region['members'])
    for row in owners['operators']:
        i=row['node'];p=prices.operator_price(actual_queries[i])
        if static_cal and p['delay_ps']+p['area_um2']>0:
            weight=static_node(graph,graph.nodes[i]);p=dict(p,delay_ps=weight*bridge['operator_delay_ps'],area_um2=weight*bridge['comb_area_um2'])
        delay[i]=p['delay_ps'];area[i]=p['area_um2'];records.append(dict(node=i,kind='operator',**p))
    for i,g in regions.items():
        p=prices.reduction_price(actual_queries[i])
        if static_cal:
            group=set(g['members']);cache={}
            def local(n):
                if n not in group:return 0.
                if n not in cache:cache[n]=static_node(graph,graph.nodes[n])+max((local(a['node']) for a in graph.nodes[n]['operands'] if a['node'] is not None),default=0.)
                return cache[n]
            p=dict(p,delay_ps=local(i)*bridge['operator_delay_ps'],area_um2=sum(static_node(graph,graph.nodes[n]) for n in group)*bridge['comb_area_um2'])
        delay[i]=p['delay_ps'];area[i]=p['area_um2'];records.append(dict(node=i,kind='G',**p))
    for i in owners['functional_logic']:
        c,outputs=functional_circuit(graph,i);cov=cover(c,outputs)
        d=cov['depth']*bundle['numerical_floors']['gate_delay_ps'];a=cov['area']
        if static_cal and a>0:
            weight=static_node(graph,graph.nodes[i]);d=weight*bridge['operator_delay_ps'];a=weight*bridge['comb_area_um2']
        delay[i]=d;area[i]=a;records.append(dict(node=i,kind='functional',delay_ps=d,area_um2=a,source='exact local Boolean DAG/legal library cover',qualified=False))
    if len(delay)!=len(owners['operators'])+len(regions)+len(owners['functional_logic']):raise ValueError('owner overlap')
    active=set();arrivals={}
    def arrival(i):
        if i in arrivals:return arrivals[i]
        if i in active:raise ValueError('cycle in owned timing DAG')
        active.add(i)
        if i in regions:children={s for term in regions[i]['terms'] for s,bit,col in term}
        else:children={a['node'] for a in graph.nodes[i]['operands'] if a['node'] is not None}
        value=max((arrival(n)+(bundle['inter_owner_wire_ps'] if n in delay and i in delay else 0.)
                   for n in children if placement[n]==placement[i]),default=0.)+delay.get(i,0.)
        arrivals[i]=value;active.remove(i);return value
    stages=[0.]*L
    for slot in state['slots']:
        if slot['valid'] or not slot['variable_bits']:continue
        i=slot['origin'];capture=slot['stage']-1
        stages[capture]=max(stages[capture],arrival(i) if placement[i]==capture else 0.)
    projection=state_projection(graph,state,L,target);S=state_price(bundle,projection,sum(area.values()))
    boundaries=bundle['S']['data_boundary_ps'];complete=[]
    for stage,d in enumerate(stages):
        boundary=boundaries['native_state->external_state'] if stage==L-1 else boundaries['input_service->native_state'] if stage==0 else boundaries['native_state->native_state']
        checks=[d+boundary]+[c['required_ps'] for c in S['controls'] if c['stage']==stage]
        complete.append(dict(stage=stage,comb_delay_ps=d,boundary_ps=boundary,required_ps=max(checks)+S['reserve_ps']))
    port_required=max(c['required_ps'] for c in S['controls'] if c['stage'] in (-1,L))+S['reserve_ps']
    required=max(port_required,max(s['required_ps'] for s in complete));violation=max(0.,required-target)
    return dict(version=VERSION,status='diagnostic_complete',qualified=False,static_cal=static_cal,
                target_ps=target,L=L,critical_required_ps=required,violation_ps=violation,target_met=violation==0,
                total_area_um2=S['total_area_um2'],comb_area_um2=sum(area.values()),stages=complete,
                port_required_ps=port_required,S=S,owners=records,owners_count=len(records),
                G_members_not_billed_separately=len(members),extrapolation=True,candidate_PPA_calls=0)
