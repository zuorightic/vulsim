"""Independent report, physical-cost, group/position and offline-choice checks."""
import copy
import hashlib
import json
import math
from pathlib import Path
from .model_features import features,validate_query,infer
from .report_types import validate_report_types
from .step5_analysis import evaluate as topology_evaluate

ROOT=Path(__file__).resolve().parents[2]
WIRE={0,1,8,11,12,13,14,15,16,17,18,19,28}
OPS={1:'add',2:'sub',3:'mul',4:'div',5:'mod',6:'and',7:'or',8:'xor',9:'and',10:'or',
     11:'compare_eq',12:'compare_eq',13:'compare_rel',14:'compare_rel',15:'compare_rel',16:'compare_rel',17:'shl',18:'shr'}


def equal(a,b,label):
    if type(a) in (int,float) and type(b) in (int,float):okay=math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-8)
    else:okay=type(a) is type(b) and a==b
    if not okay:raise ValueError(f'offline model evidence mismatch: {label}: {a!r} != {b!r}')


def literal(v):return sum(int(word)<<(64*i) for i,word in enumerate(v['limbs']))


def graph_values(report):
    """Independent local unsigned value facts, with an explicit audit boundary.

    Unknown bits are retained. This audits the supported Mul/Add local graphs;
    it does not claim a portable proof for FP internals or arbitrary BEIR ops.
    """
    nodes={n['id']:n for n in report['graph']['nodes']};facts={};active=set()
    def value(v):
        if v['kind']==0:return visit(v['node'])
        if v['kind']==1:
            mask=(1<<v['width'])-1;ones=literal(v)&mask;return mask^ones,ones,v['width']
        return 0,0,v['width']
    def resize(f,w):
        z,o,old=f;mask=(1<<w)-1
        return (z|(((1<<w)-1)^((1<<old)-1) if w>old else 0))&mask,o&mask,w
    def visit(i):
        if i in facts:return facts[i]
        if i in active:raise ValueError('cycle in portable model value facts')
        active.add(i);n=nodes[i];w=n['width'];mask=(1<<w)-1;args=[value(v) for v in n['operands']];z=o=0;k=n['kind'];code=n['opcode']
        if k in (0,8,11,13):
            if n['signed_truncation']:raise ValueError('signed state truncation outside local audit domain')
            z,o,_=resize(args[0],w)
        elif k in (14,15):
            shift=n['lo'] if k==14 else n['bit'];z,o=args[0][0]>>shift,args[0][1]>>shift
        elif k==18:
            for a,b,bits in args:z=(z<<bits)|a;o=(o<<bits)|b
        elif k==2:
            possible=max((((1<<a[2])-1)^a[0]).bit_length() for a in args[:2])+1
            z=mask^((1<<min(w,possible))-1)
        elif k==4 and code in (1,2,3):pass # C++ does not infer partial arithmetic facts for these ops.
        elif k==1:pass
        else:raise ValueError('value/state proof outside portable audited local operation domain')
        if args and k!=1 and all(a|b==(1<<bits)-1 for a,b,bits in args):
            vs=[b for _,b,_ in args]
            if k in (0,8,11,13,14,15,18):pass
            elif k==2:o=sum(vs)&mask;z=mask^o
            elif k==4:
                o=({1:lambda:vs[0]+vs[1],2:lambda:vs[0]-vs[1],3:lambda:vs[0]*vs[1]}[code]())&mask;z=mask^o
        facts[i]=(z&mask,o&mask,w);active.remove(i);return facts[i]
    for i in nodes:visit(i)
    return facts


def node_queries(report,bundle):
    nodes={n['id']:n for n in report['graph']['nodes']};users={i:0 for i in nodes};constant={};zero={};visiting=set();ordered=[]
    for n in nodes.values():
        for v in n['operands']:
            if v['kind']==0:
                if v['node'] not in nodes or v['width']!=nodes[v['node']]['width']:raise ValueError('dangling or mismatched BEIR reference')
                users[v['node']]+=1
    def width(v):
        seen=set()
        while v['kind']==0 and not v['signed']:
            if v['node'] in seen:raise ValueError('billing provenance cycle')
            seen.add(v['node']);n=nodes[v['node']]
            if n['kind'] not in (0,8,11) or len(n['operands'])!=1:break
            child=n['operands'][0]
            if child['signed'] or child['constant_signed'] or child['width']>v['width']:break
            v=child
        return v['width']
    def z(v):
        mask=(1<<v['width'])-1
        return (~literal(v))&mask if v['kind']==1 else zero[v['node']] if v['kind']==0 else 0
    def visit(i):
        if i in constant:return
        if i in visiting:raise ValueError('model graph cycle')
        visiting.add(i);n=nodes[i];deps=n['operands'];mask=(1<<n['width'])-1
        for v in deps:
            if v['kind']==0:visit(v['node'])
        constant[i]=n['kind']!=1 and all(v['kind']==1 or v['kind']==0 and constant[v['node']] for v in deps)
        zero[i]=0
        if n['kind'] in (0,8,11,13) and deps:
            zero[i]=(z(deps[0])|((mask^((1<<deps[0]['width'])-1)) if n['width']>deps[0]['width'] else 0))&mask
        elif n['kind'] in (14,15):zero[i]=(z(deps[0])>>(n['lo'] if n['kind']==14 else n['bit']))&mask
        elif n['kind']==18:
            value=0
            for v in deps:value=(value<<v['width'])|z(v)
            zero[i]=value&mask
        elif n['kind']==19:
            for _ in range(n['times']):zero[i]=(zero[i]<<deps[0]['width'])|z(deps[0])
            zero[i]&=mask
        equal(n['transaction_constant'],constant[i],'transaction constant classification')
        visiting.remove(i);ordered.append(i)
    for i in nodes:visit(i)
    interval_owner={}
    if bundle['stages']['grt'].get('mul_interval_model'):
        from .model_mul_intervals import validate_template
        for region in report['graph']['regions']:
            if region['template_id']=='mul-block-tree-v1':
                validate_template(report,region)
                for node in region['members']:interval_owner[node]=region
    queries=[]
    for i in ordered:
        n=nodes[i];deps=n['operands'];kind=n['kind'];code=n['opcode']
        if i in interval_owner:
            deferred=not (kind in WIRE) and not constant[i]
            equal(n.get('deferred_to_stage',False),deferred,'explicit composite ownership')
            equal(n['delay'],0,'no duplicate template node delay');equal(n['comb'],0,'no duplicate template node area')
            equal(n['physical_operation'],'mul-template-stage-member' if deferred else '','template node billing')
            if deferred:queries.append(i)
            continue
        if n.get('deferred_to_stage',False):raise ValueError('node deferred without a qualified template model')
        wire=kind in WIRE or kind==4 and code in (17,18) and len(deps)==2 and deps[1]['kind']==1
        if wire or constant[i]:
            equal(n['delay'],0,'semantic wiring/constant delay');equal(n['comb'],0,'semantic wiring/constant area');continue
        lhs=width(deps[0]);rhs=width(deps[1]) if len(deps)>1 else 0
        lz=(z(deps[0])&((1<<lhs)-1)).bit_count();rz=(z(deps[1])&((1<<rhs)-1)).bit_count() if rhs else 0
        if kind==4 and code in OPS:op=OPS[code]
        elif kind==2:op='add' if deps[2]['kind']==1 and literal(deps[2])==0 else 'addcarry'
        elif kind in (20,21,22):op={20:'reduce_or',21:'reduce_and',22:'reduce_xor'}[kind]
        elif kind==5:op={19:'eq_zero',20:'not',21:'neg'}[code];rhs=rz=0
        else:raise ValueError('physical report operation outside audited local domain')
        if kind==4 and code in (11,12) and any(v['kind']==1 and literal(v)==0 for v in deps):
            op='eq_zero';data=deps[1] if deps[0]['kind']==1 and literal(deps[0])==0 else deps[0];lhs=width(data);rhs=rz=0;lz=(z(data)&((1<<lhs)-1)).bit_count()
        def primary(v,visited=None):
            visited=set() if visited is None else visited
            if v['kind']!=0 or v['node'] in visited:return set()
            visited.add(v['node']);source=nodes[v['node']]
            if source['kind']==1:return {v['node']}
            return set().union(*(primary(x,visited) for x in source['operands']))
        data=deps[:3] if kind==2 else deps[:2];seen=set();correlated=False
        for v in data:
            leaves=primary(v);correlated|=bool(seen&leaves);seen|=leaves
        f=features(lhs,rhs,n['width'],max(1,users[i]),bundle['mapping_abc_target_ps'],report['request']['target_period_ps'],lz,rz,
                   literal_operands=op!='eq_zero' and any(v['kind']==1 for v in deps[:2]),
                   constant_carry=kind==2 and op=='addcarry' and deps[2]['kind']==1,correlated_operands=correlated)
        expected=validate_query(bundle,op,f,platform=report['request']['target_platform'],profile_sha256=report['request']['platform_profile_sha256'],stage='grt')
        if expected['status']!='predicted_in_domain':raise ValueError('reported covered node is outside fitted domain: '+expected['reason'])
        equal(n['physical_operation'],op,'operation extraction')
        if set(f)!=set(n['physical_features']):raise ValueError('physical feature field set mismatch')
        for key,value in f.items():equal(n['physical_features'][key],value,'feature '+key)
        equal(n['delay'],expected['delay_ps'],'native/Python node delay');equal(n['comb'],expected['comb_area_um2'],'native/Python node area')
        equal(n['cost_source'],bundle['id'],'model provenance');queries.append(i)
    return len(queries)


def evaluate(report,bundle,stages=None):
    stages=report['stages'] if stages is None else stages
    raw=topology_evaluate(report,stages);N=report['request']['L']-1;counts=[0]*(N+1);values=[0]*(N+1);areas=[0.]*(N+1)
    nodes={n['id']:n for n in report['graph']['nodes']};facts=graph_values(report)
    live={i for p in report['graph']['ports'] for i in p['nodes']}|{i for r in report['graph']['regions'] for i in r['outputs']}|{v['node'] for r in report['graph']['regions'] for v in r['inputs'] if v['node']!='literal'}
    stack=list(live)
    while stack:
        for v in nodes[stack.pop()]['operands']:
            if v['kind']==0 and v['node'] not in live:live.add(v['node']);stack.append(v['node'])
    for n in report['graph']['nodes']:
        if n['id'] not in live:continue
        if not n['transaction_constant'] and (n['delay']>0 or n.get('deferred_to_stage',False)):
            at=stages[int(n['id'])];counts[at]+=1;values[at]+=n['width']*math.prod(n['dims'])
        if not n['transaction_constant']:areas[stages[int(n['id'])]]+=n['comb']
    stage=bundle['stages']['grt'];c=stage['stage_correction'];delays=[float(v) for v in raw['stage_delays']];comb=0.
    for i,(n,bits) in enumerate(zip(counts,values)):
        from .model_mul_intervals import stage_query
        inside={key for key in live if stages[int(key)]==i}
        interval=stage_query(report,bundle,inside)
        if interval is not None:
            delays[i]=interval['delay_ps'];comb+=interval['comb_area_um2'];continue
        if n>c['max_operations'] or bits>c['max_live_result_bits']:raise ValueError('placement outside validated stage domain')
        if not n:continue
        domain=c['graph_domain']
        if domain['version']!='independent-single-output-arithmetic-tree-v1':raise ValueError('unknown stage graph domain')
        inside={key for key in live if stages[int(key)]==i};paid={key for key in inside if nodes[key]['delay']>0};users_in_stage={key:0 for key in paid}
        if sum(nodes[key]['physical_operation']=='mul' for key in paid)>domain['max_multiplications']:raise ValueError('too many stage multiplications')
        for key in paid:
            if len(paid)>1 and nodes[key]['physical_operation'] not in ('mul','add'):raise ValueError('unvalidated mixed operation stage')
            dependencies=set();visited=set()
            def upstream(v):
                if v['kind']!=0 or v['node'] not in inside or v['node'] in visited:return
                visited.add(v['node'])
                if v['node'] in paid:dependencies.add(v['node']);return
                for operand in nodes[v['node']]['operands']:upstream(operand)
            for operand in nodes[key]['operands']:upstream(operand)
            for dependency in dependencies:users_in_stage[dependency]+=1
        if any(value>1 for value in users_in_stage.values()) or sum(value==0 for value in users_in_stage.values())>domain['max_output_roots']:
            raise ValueError('placement outside validated stage dependency/exit shape')
        if c.get('composition_schema')=='cardinality-specific-stage-v1' and n==1:
            node=nodes[next(iter(paid))];single=stage['single_operation_models'][node['physical_operation']]
            delays[i]=(infer(single['delay'],node['physical_features'])+single['delay_margin_ps'])*single['validation_delay_scale']
            comb+=infer(single['area'],node['physical_features'])
        else:
            if c.get('composition_schema') not in (None,'cardinality-specific-stage-v1'):raise ValueError('unknown stage composition schema')
            delays[i]=c['delay_base_scale']*delays[i]+c['intercept_ps']+c['per_operation_ps']*n+c['per_result_bit_ps']*bits
            comb+=c['area_base_scale']*areas[i]+c['intercept_um2']+c['per_operation_um2']*n+c['per_result_bit_um2']*bits
    users={i:[] for i in live}
    for i in live:
        for v in nodes[i]['operands']:
            if v['kind']==0:users[v['node']].append(i)
    valid_inputs={i for p in report['graph']['ports'] if p['name']==report['protocol']['input_valid_name'] for i in p['nodes']}
    valid_outputs={i for p in report['graph']['ports'] if p['name']==report['protocol']['output_valid_name'] for i in p['nodes']}
    model_bits=model_signals=maximum_width=0;minimum_variable=None
    def saved(i,length,control):
        nonlocal model_bits,model_signals,maximum_width,minimum_variable
        n=nodes[i]
        if n['dims']:raise ValueError('array state outside validated model domain')
        z,o,w=facts[i];variable=w-(z|o).bit_count()
        if not length or not variable:return
        model_bits+=variable*length;model_signals+=length
        if not control:maximum_width=max(maximum_width,w);minimum_variable=min(minimum_variable if minimum_variable is not None else variable,variable)
    for i in live:
        if nodes[i]['transaction_constant']:continue
        end=N if i in valid_inputs else max([stages[int(i)]]+[stages[int(u)] for u in users[i]])
        saved(i,end-stages[int(i)],i in valid_inputs)
    for port in report['graph']['ports']:
        if port['direction']==1:
            for i in port['nodes']:saved(i,1,i in valid_outputs)
    s=stage['state_model'];domain=s['domain']
    if (not maximum_width or model_bits>domain['max_bits'] or model_signals>domain['max_signals'] or maximum_width>domain['max_data_word_width']
            or minimum_variable<domain['min_variable_data_word_bits']):raise ValueError('placement outside validated state/count/width domain')
    protocol=report['protocol']
    if (s['protocol_id']!='sync_zero_reset_valid_enable_v1' or not protocol['reset_enabled'] or not protocol['input_valid_name']
            or any(int(word)!=0 for words in protocol['input_reset_values'].values() for word in words)):
        raise ValueError('placement outside validated reset/enable protocol')
    state=model_bits*(s['bit_area_um2']+s['clock_area_per_bit_um2'])+model_signals*s['signal_area_um2']
    b=stage['boundary_model'];period=report['request']['target_period_ps'];budgets=[period*(1-b['io_delay_fraction'])-b['input_overhead_ps']]+[period-b['register_overhead_ps']]*N
    return {'stage_delays_ps':delays,'maximum_delay':max(delays),'comb_area_um2':comb,'state_area_um2':state,'total_area_um2':comb+state,
            'register_bits':raw['register_bits'],'register_count':raw['register_count'],'budgets_ps':budgets,
            'model_state_bits':model_bits,'model_state_signals':model_signals,
            'within_absolute_budget':all(x<=y for x,y in zip(delays,budgets)),
            'within_production_cap':all(x<=y for x,y in zip(delays,report['pipeline']['allowed_stage_delays_ps']))}


def verify_report(report,bundle,rtl=None):
    schemas=json.loads((ROOT/'experiments/arithmetic_dse/configs/arithmetic_compiler_interfaces_v1.json').read_text())['report_schemas_backend_model'];validate_report_types(report,schemas)
    equal(json.loads(report['graph_identity_text']),report['graph'],'graph serialization')
    equal(hashlib.sha256(report['graph_identity_text'].encode()).hexdigest(),report['graph_sha256'],'graph hash')
    equal(json.loads(report['schedule_identity_text']),{'stages':report['stages'],'protocol':report['protocol']},'schedule serialization')
    equal(hashlib.sha256((report['graph_sha256']+report['schedule_identity_text']).encode()).hexdigest(),report['schedule_sha256'],'schedule hash')
    if rtl is not None:equal(hashlib.sha256(rtl.encode()).hexdigest(),report['rtl_sha256'],'RTL bytes')
    for key in ('target_platform','platform_profile_sha256','model_bundle_sha256'):equal(report['cost_query_context'][key],report['request'][key],'query context '+key)
    equal(report['cost_query_context']['feature_schema'],bundle['feature_schema'],'query feature ABI')
    queries=node_queries(report,bundle);cost=evaluate(report,bundle);p=report['pipeline']
    for a,b in [('maximum_delay','final_delay'),('comb_area_um2','predicted_comb_area_um2'),('state_area_um2','predicted_state_area_um2'),('total_area_um2','predicted_total_area_um2'),('register_bits','register_bits'),('register_count','register_count'),('model_state_bits','model_state_bits'),('model_state_signals','model_state_signals')]:equal(cost[a],p[b],b)
    for a,b in zip(cost['stage_delays_ps'],p['stage_delays_ps']):equal(a,b,'stage delay')
    equal(cost['budgets_ps'][0],p['input_data_budget_ps'],'input absolute budget')
    if len(cost['budgets_ps'])>1:equal(cost['budgets_ps'][1],p['register_data_budget_ps'],'register absolute budget')
    if not cost['within_absolute_budget'] or not cost['within_production_cap']:raise ValueError('selected implementation violates frozen data budget/cap')
    return {'queries':queries,**cost}


def verify_selection(report,bundle):
    rows=report['selection']['candidates'];ranked=[];count=0
    for row in rows:
        if row['status']!='scheduled':continue
        data=row['computation'];result=verify_report(data,bundle);score=[result['total_area_um2'],result['maximum_delay'],result['register_bits'],row['id']]
        if len(score)!=len(row['score']):raise ValueError('D ranking key shape')
        for a,b in zip(score,row['score']):equal(a,b,'D ranking')
        if data['selection_role']!='evaluated_candidate':raise ValueError('candidate falsely marked final selected')
        if any(r['D_selected'] for r in data['graph']['regions']):raise ValueError('unselected candidate capability flag')
        equal(row['final_stages'],data['stages'],'candidate final map');moving=list(row['initial_stages']);current=evaluate(data,bundle,moving)
        groups={};owned=set()
        for region in data['graph']['regions']:
            for k,group in enumerate(region['legal_groups'] if region['internally_cuttable'] else [region['members']]):groups[region['id']+('/group'+str(k) if region['internally_cuttable'] else '/atomic')]=group;owned.update(group)
        for n in data['graph']['nodes']:
            if n['id'] not in owned:groups['node#'+n['id']]=[n['id']]
        for move in row['moves']:
            if not move['accepted']:continue
            group=groups[move['group']]
            if any(moving[int(i)]!=move['from'] for i in group):raise ValueError('accepted move start mismatch')
            for i in group:moving[int(i)]=move['to']
            after=evaluate(data,bundle,moving)
            if not after['within_absolute_budget'] or not after['within_production_cap'] or after['total_area_um2']>=current['total_area_um2']:raise ValueError('invalid accepted physical area move')
            current=after
        equal(moving,row['final_stages'],'actual move trace');ranked.append((score,row['id']));count+=1
    if not ranked or min(ranked)[1]!=report['selection']['selected_candidate']:raise ValueError('D did not choose frozen predicted ranking')
    equal(report['selection']['candidate_PPA_calls'],0,'offline selection PPA calls')
    return {'scheduled_candidates':count,'rejected_candidates':len(rows)-count,'outer_choice':'verified within covered evaluated candidate subset; inspect rejections','global_optimality_claim':False}
