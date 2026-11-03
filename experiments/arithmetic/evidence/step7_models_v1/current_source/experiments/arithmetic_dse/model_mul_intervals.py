"""Actual native template graph intervals, packed-bit measurement boundaries.

No application PPA is accepted. Graphs come from the native registered template
exporter; every interval retains the graph identity and complete legal groups.
"""
import argparse,hashlib,json,math
from pathlib import Path
from .model_analysis import graph_values,literal
from .model_collection import sha,write,PROTOCOL
from .budget import POLICY,usage,Ledger
from .platforms import profile

CONFIG=Path(__file__).with_name('configs')/'model_mul_intervals_v2.json'
ROOT=Path(__file__).resolve().parents[2]

def interval(report,first,last):
    graph=report['graph'];r=graph['regions'][0];nodes={n['id']:n for n in graph['nodes']};groups=r['legal_groups']
    if r['template_id']!='mul-block-tree-v1' or not 0<=first<=last<len(groups):raise ValueError('registered complete group interval required')
    inside=set().union(*(set(g) for g in groups[first:last+1]));facts=graph_values(report)
    inputs=set();outputs=set()
    for key in inside:
        for v in nodes[key]['operands']:
            if v['kind']==0 and v['node'] not in inside:inputs.add(v['node'])
    for n in nodes.values():
        if n['id'] not in inside:
            for v in n['operands']:
                if v['kind']==0 and v['node'] in inside:outputs.add(v['node'])
    def unknown(key):
        z,o,w=facts[key];return ((1<<w)-1)^(z|o)
    needed={node:unknown(node) for node in outputs};pending=list(outputs)
    while pending:
        node=pending.pop();mask=needed[node]&unknown(node)
        if node not in inside or not mask:continue
        n=nodes[node];kind=n['kind'];operands=n['operands'];demands=[]
        if kind in (0,8,11,13):demands=[mask]
        elif kind==14:demands=[mask<<n['lo']]
        elif kind==18:
            offset=0;demands=[0]*len(operands)
            for k in reversed(range(len(operands))):demands[k]=(mask>>offset)&((1<<operands[k]['width'])-1);offset+=operands[k]['width']
        elif kind==2 or kind==4 and n['opcode']==3:demands=[(1<<min(mask.bit_length(),v['width']))-1 for v in operands]
        else:raise ValueError('unregistered interval bit dependency')
        for v,demand in zip(operands,demands):
            if v['kind']!=0:continue
            child=v['node'];before=needed.get(child,0);after=before|(demand&unknown(child))
            if after!=before:needed[child]=after;pending.append(child)
    def bits(key,consumed=False):
        mask=unknown(key)&needed.get(key,0) if consumed else unknown(key)
        return [i for i in range(nodes[key]['width']) if (mask>>i)&1]
    inputs=sorted((i for i in inputs if bits(i,True)),key=int);outputs=sorted((i for i in outputs if bits(i)),key=int)
    if not inputs or not outputs:raise ValueError('interval has no observable variable arithmetic path')
    params=r['parameters'];w=params['lhs_width'];divisor=2 if params['block_width']==w//2 else 4
    return {'template_id':r['template_id'],'width':w,'result_width':params['result_width'],'block_width':params['block_width'],
            'result_shape':'full' if params['result_width']==2*w else 'low','configuration':'half' if divisor==2 else 'quarter',
            'first':first,'last':last,'groups':len(groups),'members':sorted(inside,key=int),
            'input_nodes':inputs,'output_nodes':outputs,'input_bit_positions':{i:bits(i,True) for i in inputs},'output_bit_positions':{i:bits(i) for i in outputs},
            'input_widths':[len(bits(i,True)) for i in inputs],'capture_width':sum(len(bits(i)) for i in outputs),
            'graph_sha256':report['graph_sha256'],'facts':facts}

def key(spec):return '/'.join(map(str,(spec['configuration'],spec['result_shape'],spec['first'],spec['last'])))
def features(s):
    w=s['width'];return {'width':w,'width_squared':w*w,'log_width':math.log2(w),'capture_bits':s['capture_width'],
       'input_bits':sum(s['input_widths']),'block_width':s['block_width'],'first':s['first'],'last':s['last']}

def expression(node,operand):
    vs=[operand(v) for v in node['operands']];kind=node['kind']
    if kind in (0,8,11,13):return vs[0]
    if kind==14:return vs[0]+f'[{node["hi"]}:{node["lo"]}]'
    if kind==18:return '{'+','.join(vs)+'}'
    if kind==4 and node['opcode']==3:return ' * '.join(vs)
    if kind==2:return ' + '.join(vs)
    raise ValueError('unregistered interval operation')

def source(items):
    modules=[];ports=['input wire clk,rstn,iv','output reg ov'];instances=[];labels=[]
    def rng(w):return f'[{w-1}:0] ' if w>1 else ''
    for idx,(report,spec) in enumerate(items):
        name=f's{idx:03d}';nodes={n['id']:n for n in report['graph']['nodes']};facts=spec['facts'];ins=spec['input_nodes'];decl=[]
        for k,node in enumerate(ins):decl.append(f'input wire {rng(len(spec["input_bit_positions"][node]))}x{k}')
        width=spec['capture_width'];decl.append(f'output wire [{width-1}:0] value');body=[]
        for k,node in enumerate(ins):
            pos=spec['input_bit_positions'][node];at={bit:j for j,bit in enumerate(pos)};z,o,w=facts[node]
            values=[('x'+str(k)+(f'[{at[b]}]' if len(pos)>1 else '')) if b in at else "1'b"+str((o>>b)&1) for b in reversed(range(w))]
            body.append(f'wire [{w-1}:0] v{node}='+('{'+','.join(values)+'}' if len(values)>1 else values[0])+';')
        def operand(v):
            if v['kind']==1:return str(v['width'])+"'d"+str(literal(v))
            node=v['node'];z,o,w=facts[node]
            return str(w)+"'d"+str(o) if (z|o)==(1<<w)-1 or node not in spec['members'] and node not in ins else 'v'+node
        for node in spec['members']:
            n=nodes[node];z,o,w=facts[node]
            if (z|o)==(1<<w)-1:body.append(f'wire [{w-1}:0] v{node}={w}\'d{o};');continue
            body.append(f'wire [{w-1}:0] v{node}='+expression(n,operand)+';')
        values=['v'+node+f'[{bit}]' for node in reversed(spec['output_nodes']) for bit in reversed(spec['output_bit_positions'][node])]
        body.append('assign value={'+','.join(values)+'};')
        modules.append(f'(* keep_hierarchy=1 *) module Core_{name}('+','.join(decl)+');\n'+'\n'.join(body)+'\nendmodule\n')
        args=[f'input wire {rng(w)}in{k}' for k,w in enumerate(spec['input_widths'])];body=[]
        for k,w in enumerate(spec['input_widths']):body.append(f'(* keep *) reg [{w-1}:0] src{k};always @(posedge clk)if(!rstn)src{k}<=0;else if(iv)src{k}<=in{k};')
        body.append(f'wire [{width-1}:0] value;Core_{name} core('+','.join(f'.x{k}(src{k})' for k in range(len(ins)))+',.value(value));')
        body.append(f'(* keep, dont_touch *) reg [{width-1}:0] dst;always @(posedge clk)dst<=value;assign y=^dst;')
        modules.append(f'(* keep_hierarchy=1 *) module Cell_{name}(input wire clk,rstn,iv,'+','.join(args)+',output wire y);\n'+'\n'.join(body)+'\nendmodule\n')
        connections=['.clk(clk)','.rstn(rstn)','.iv(iv)',f'.y(y{idx})'];ports.append(f'output wire y{idx}')
        for k,w in enumerate(spec['input_widths']):ports.append(f'input wire {rng(w)}x{idx}_{k}');connections.append(f'.in{k}(x{idx}_{k})')
        instances.append(f'Cell_{name} {name}('+','.join(connections)+');')
        saved={k:v for k,v in spec.items() if k!='facts'}
        labels.append({**saved,'id':name,'source_cells':name+'/src*','target_cells':[name+'/dst*',name+'/y*'],'instance_scope':name+'/',
                       'arithmetic_scope':name+'/core/','fanout':1,'result_width':width,'semantic_result_width':spec['result_width'],
                       'features':features(spec),'interval_key':key(spec),'role':'template_interval','boundary':'native typed graph; packed variable launch/capture, known constants reconstructed'})
    return '\n'.join(modules)+'module ModelBundle('+',\n'.join(ports)+');\nalways @(posedge clk)if(!rstn)ov<=0;else ov<=iv;\n'+'\n'.join(instances)+'\nendmodule\n',labels

def prepare(graphs,out,platforms):
    cfg=json.loads(CONFIG.read_text());out.mkdir(parents=True,exist_ok=False);tasks=[];counts={}
    for split,widths in cfg['splits'].items():
        items=[]
        for path in sorted(graphs.glob('*.json')):
            report=json.loads(path.read_text());r=report['graph']['regions'][0]
            if r['parameters']['lhs_width'] not in widths:continue
            for first in range(len(r['legal_groups'])):
                for last in range(first,len(r['legal_groups'])):items.append((report,interval(report,first,last)))
        packs=[];pack=[];bits=0
        for item in items:
            size=sum(item[1]['input_widths'])
            if pack and (len(pack)>=cfg['pack_limit']['samples'] or bits+size>cfg['pack_limit']['input_variable_bits']):packs.append(pack);pack=[];bits=0
            pack.append(item);bits+=size
        if pack:packs.append(pack)
        counts[split]={'samples':len(items),'bundles':len(packs)}
        for n,pack in enumerate(packs):
            name=f'{split}-b{n:03d}';folder=out/name;folder.mkdir();text,labels=source(pack);(folder/'input.sv').write_text(text)
            write(folder/'contract.json',{'version':'arithmetic-model-labels-v1','source_group':name,'split':split,'protocol_sha256':sha(CONFIG),'labels':labels})
            write(folder/'graphs.json',{'reports':{r['graph_sha256']:r for r,_ in pack}})
            for platform in platforms:
                p=profile(platform);ref=json.loads(PROTOCOL.read_text())['reference_abc_ps'][platform]
                tasks.append({'id':platform+'-'+name,'platform':platform,'profile_sha256':p['profile_sha256'],'top':'ModelBundle','period_ps':ref,'abc_target_ps':ref,'stage':'grt',
                   'rtl':str((folder/'input.sv').resolve()),'rtl_sha256':sha(folder/'input.sv'),'sample_contract':str((folder/'contract.json').resolve()),'sample_contract_sha256':sha(folder/'contract.json'),
                   'source_group':name,'split':split,'samples':len(labels),'capacity_scope':'native template interval <=32; max6 cores; input<=640bits unless single-core',
                   'synth_timeout_s':300,'route_timeout_s':1200,'memory_limit_MiB':8192})
    a={'version':'arithmetic-model-collection-admission-v1','id':out.name,'purpose':'arithmetic_model_collection','protocol_sha256':sha(PROTOCOL),'policy_sha256':sha(POLICY),
       'supplemental_protocol':{'path':str(CONFIG.resolve()),'sha256':sha(CONFIG)},'tasks':tasks,'automatic_retries':0,'call_caps':{'synth':len(tasks),'grt':len(tasks),'final':0},
       'support_walltime_s':10800,'worst_case_leaf_walltime_s':len(tasks)*1860+10800,'later_work_reserved':{'walltime_s':86400,'CPU_time_s':172800,'synth':688,'grt':688},
       'test_read_after_fit_only':True,'main_matrix_authorized':False,'complete_native_graphs':str(graphs.resolve()),'data_exclusions':cfg['data_exclusions']}
    total=usage(json.loads(Ledger().path.read_text())['entries']);limits=json.loads(POLICY.read_text())['resources']
    # Preparation is itself a charged support leaf; launch checks pending separately.
    if total['walltime_s']+a['worst_case_leaf_walltime_s']+86400>limits['max_global_walltime_h']*3600:raise ValueError('batch not funded')
    write(out/'admission.json',a);print({'counts':counts,'tasks':len(tasks),'worst_case_wall_s':a['worst_case_leaf_walltime_s']})

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare']);p.add_argument('--graphs',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--platforms',nargs='+',default=['asap7','nangate45','sky130hd','gf180']);a=p.parse_args();prepare(a.graphs,a.out,a.platforms)
if __name__=='__main__':main()


def stage_query(report,bundle,members,*,allow_none=True):
    """Independent typed-graph reconstruction of one covered stage interval."""
    nodes={n['id']:n for n in report['graph']['nodes']};inside=set(members);regions=[];facts=graph_values(report)
    for region in report['graph']['regions']:
        if region['template_id']=='mul-block-tree-v1' and inside.intersection(region['members']):regions.append(region)
    if not regions:
        if allow_none:return None
        raise ValueError('missing native template interval')
    if len(regions)!=1:raise ValueError('unvalidated multi-template stage composition')
    r=regions[0];first=last=None
    for g,group in enumerate(r['legal_groups']):
        active={node for node in group if (facts[node][0]|facts[node][1])!=(1<<facts[node][2])-1}
        if active & inside:
            if not active<=inside or last is not None and g!=last+1:raise ValueError('partial or disjoint template interval')
            if first is None:first=g
            last=g
    if first is None:return {'delay_ps':0.,'comb_area_um2':0.}
    isolated={**report,'graph':{**report['graph'],'regions':[r]}}
    spec=interval(isolated,first,last);model=bundle['stages']['grt']['mul_interval_model'];request=report['request']
    if (model['version']!='arithmetic-mul-group-interval-model-v1' or model['quality_status']!='passed'
        or spec['width']%4 or spec['width']<model['min_width'] or spec['width']>model['max_width']
        or spec['block_width'] not in (spec['width']//2,spec['width']//4) or spec['result_width'] not in (spec['width'],2*spec['width'])
        or request['target_period_ps']!=model['sdc_period_ps'] or bundle['mapping_abc_target_ps']!=model['abc_target_ps']):raise ValueError('template interval outside qualified geometry/context')
    for node in inside-set(r['members']):
        n=nodes[node]
        if n['delay'] or n['comb'] or n.get('deferred_to_stage'):raise ValueError('unvalidated arithmetic combined with template interval')
    entry=model['intervals'][key(spec)]
    if entry['quality_status']!='passed':raise ValueError('unqualified template interval model')
    from .model_features import infer
    f=features(spec);return {'delay_ps':infer(entry['delay'],f)*entry['validation_delay_scale'],'comb_area_um2':infer(entry['area'],f),'features':f,'interval_key':key(spec)}


def validate_template(report,region):
    """Structural certificate for the measured power-of-two block tree family."""
    nodes={n['id']:n for n in report['graph']['nodes']};t=region['parameters'];w=t['lhs_width'];block=t['block_width']
    if w!=t['rhs_width'] or w%4 or block not in (w//2,w//4):raise ValueError('unsupported measured template geometry')
    def canonical(v):
        seen=set()
        while v['kind']==0:
            if v['node'] in seen:raise ValueError('source cycle')
            seen.add(v['node']);n=nodes[v['node']]
            if n['kind'] not in (0,8,11) or len(n['operands'])!=1:break
            child=n['operands'][0]
            if v['signed'] or child['signed'] or child['constant_signed'] or child['width']>v['width']:break
            v=child
        return v
    def ref(node):return {'kind':0,'node':node,'width':nodes[node]['width'],'signed':False,'constant_signed':False}
    original=[canonical(ref(v['node'])) for v in region['inputs']]
    if any(v['kind']!=0 for v in original) or original[0]['node']==original[1]['node']:raise ValueError('unvalidated template original sources')
    coords={};covered=set();levels={}
    for node in region['members']:
        n=nodes[node]
        if n['kind']==4 and n['opcode']==3:
            pair=[]
            for axis,v in enumerate(n['operands']):
                v=canonical(v)
                if v['kind']!=0:raise ValueError('product is not from a block')
                s=nodes[v['node']]
                if s['kind']!=14 or s['lo']%block or s['lo']<0 or s['hi']!=s['lo']+block-1 or s['hi']>=w or v['width']!=block:raise ValueError('wrong template block coordinate')
                source=canonical(s['operands'][0])
                if source['kind']!=0 or source['node']!=original[axis]['node']:raise ValueError('wrong template original source')
                pair.append(s['lo'])
            xy=tuple(pair)
            if xy in covered or n['width']!=2*block:raise ValueError('repeated block or wrong leaf precision')
            covered.add(xy);coords[node]=xy;levels[node]=0
    if covered!={(a,b) for a in range(0,w,block) for b in range(0,w,block)}:raise ValueError('missing partial-product coordinate')
    used={};active=set()
    def reduction(v,shift=0):
        v=canonical(v)
        if v['kind']!=0 or v['node'] in active:raise ValueError('invalid reduction source/cycle')
        node=v['node'];n=nodes[node];active.add(node)
        if node in coords:
            if shift!=sum(coords[node]):raise ValueError('wrong partial-product shift')
            used[node]=used.get(node,0)+1;level=0
        elif n['kind']==18:
            if len(n['operands'])!=2 or n['operands'][1]['kind']!=1 or literal(n['operands'][1])!=0:raise ValueError('invalid product shift')
            level=reduction(n['operands'][0],shift+n['operands'][1]['width'])
        elif n['kind']==2:
            if shift or len(n['operands'])!=3 or n['operands'][2]['kind']!=1 or literal(n['operands'][2])!=0:raise ValueError('invalid reduction carry')
            level=1+max(reduction(v) for v in n['operands'][:2]);width=0
            for v in n['operands'][:2]:
                e=nodes[v['node']]
                if e['kind']!=11:raise ValueError('missing reduction precision extension')
                levels[v['node']]=level;width=max(width,e['operands'][0]['width'])
            if n['width']!=width+1:raise ValueError('wrong reduction precision')
        else:raise ValueError('unregistered reduction connection')
        levels[node]=level;active.remove(node);return level
    node=region['outputs'][0];n=nodes[node];v=ref(node)
    if n['kind']==14:
        if n['lo']!=0 or n['hi']!=t['result_width']-1:raise ValueError('wrong result truncation')
        v=n['operands'][0]
    level=reduction(v);levels[node]=level
    if set(used)!=set(coords) or any(n!=1 for n in used.values()):raise ValueError('missing or repeated reduction product')
    for g,group in enumerate(region['legal_groups']):
        for node in group:
            n=nodes[node];expected=levels.get(node)
            if expected is None and n['kind']==14:expected=0
            if expected!=g:raise ValueError('legal group differs from measured reduction level')
    return True
