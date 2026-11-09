"""Accounted consumer-shell, reader and thirteen-target protocol acceptance."""
import argparse
from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.arithmetic_dse import model_context_samples as shells
from experiments.arithmetic_dse import model_context_labels as labels
from experiments.arithmetic_dse import model_three_region_scan as scan
from experiments.arithmetic_dse.model_fast_preflight import read, write, sha

CONFIG = ROOT/'experiments/arithmetic_dse/configs/model_target_round1_v1.json'
LOADS = ROOT/'experiments/arithmetic/evidence/step7_fast_loads_v1'
REQUIREMENTS = ROOT/'experiments/arithmetic/evidence/step7_fast_preflight_v3/requirements.json'
ASSET = ROOT/'experiments/arithmetic_dse/reference_assets/context_readout.tcl'
YOSYS = Path('/home/zyrv/OpenROAD-flow-scripts/tools/install/yosys/bin/yosys')


def cohort(inventory):
    rows = []
    def add(features, role, provenance):
        shells.validate(features); signature = shells.identity(features)
        if any(r['source_group']==signature for r in rows): raise ValueError('duplicate source across roles')
        rows.append(dict(id='s'+signature[:16],source_group=signature,role=role,features=features,provenance=provenance))
    for key, item in sorted(inventory['contexts'].items()):
        add(item['features'],'train',dict(required_context=key,occurrences=item['occurrences']))
    for role, offset in (('validation',0),('locked_test',2)):
        specs = [dict(operation='mul',lhs_width=w,rhs_width=w,result_width=2*w,carry='zero',capture_banks=1)
                 for w in (8,8,16,16,32,32)]
        specs += [dict(operation='add',lhs_width=a,rhs_width=b,result_width=r,carry='zero',capture_banks=1,
                       lhs_zero_hex=hex((1 << z)-1)) for a,b,r,z in
                  ((17,29,30,3),(23,35,36,0),(31,47,48,7),(39,51,52,4),(55,64,64,16),(57,63,64,8))]
        for i,spec in enumerate(specs):
            add(shells.independent_context(spec,offset+i%2),role,dict(kind='new_local_connection_or_non_aligned_shape',index=i))
    return rows


def capacity_sources():
    specs = [dict(operation='mul',lhs_width=32,rhs_width=32,result_width=64,carry='zero',capture_banks=1),
             dict(operation='add',lhs_width=51,rhs_width=67,result_width=64,carry='zero',capture_banks=1,rhs_zero_hex='ffff'),
             dict(operation='add',lhs_width=56,rhs_width=64,result_width=64,carry='zero',capture_banks=1,lhs_zero_hex='ffffffffff',rhs_zero_hex='ffffffffff')]
    result = []
    for i,spec in enumerate(specs):
        features = shells.independent_context(spec,5+i)
        if i==0:
            features['captures']=[dict(banks=2,declared_width=64,result_bit_map=list(range(64)))]
        result.append(dict(id='capacity'+str(i),source_group=shells.identity(features),role='not_training',features=features,
                           targets_ps=((750,1500),(125,750),(25,250))[i]))
    return result


def prepare(out):
    out.mkdir(parents=True,exist_ok=False)
    parent = read(LOADS/'manifest.json')
    for name,h in parent['files_sha256'].items():
        if sha(LOADS/name)!=h: raise ValueError('static parent evidence changed')
    inventory=read(LOADS/'loads.json'); requirements=read(REQUIREMENTS); config=read(CONFIG)
    rows=cohort(inventory); capacity=capacity_sources()
    if set(r['source_group'] for r in rows) & set(r['source_group'] for r in capacity): raise ValueError('capacity source leaks into fit/test')
    all_rows=rows+capacity
    modules=[];declarations=[];assignments=[];checks=[];initial=[];geometry_ports=[];geometry_instances=[]
    cycles=96
    for i,row in enumerate(all_rows):
        features=row['features'];g=shells.layout(features);name='Context'+str(i);n,r=g['input_bits'],g['output_bits']
        module=shells.source(features,name);modules.append(module)
        (out/(row['id']+'.sv')).write_text(shells.source(features))
        write(out/(row['id']+'.contract.json'),dict(version=shells.VERSION,features=features,geometry=g,
            physical_endpoint_qualification=False,required_node_scopes={'producer':'core/',**{'consumer'+str(j):'consumer'+str(j)+'/' for j in range(len(features['consumers']))}},
            source_group=row['source_group'],role=row['role']))
        width=n+2+r+1;rng=random.Random(int(row['source_group'][:16],16));old=0;valid=0;vectors=[]
        for cycle in range(cycles):
            value=[0,(1<<n)-1,1,1<<(n-1)][cycle] if cycle<4 else rng.getrandbits(n)
            rstn=int(cycle not in (0,1,40,41));iv=int(cycle%5 not in (1,3))
            result=shells.evaluate(features,old);ov=0 if not rstn else valid
            word=value
            for v,w in ((rstn,1),(iv,1),(result,r),(ov,1)):word=(word<<w)|v
            vectors.append(format(word,'x'))
            if not rstn:old=0;valid=0
            else:
                valid=iv
                if iv:old=value
        path=out/(row['id']+'.hex');path.write_text('\n'.join(vectors)+'\n')
        row.update(module=name,input_bits=n,output_bits=r,vector_sha256=sha(path),rtl_sha256=sha(out/(row['id']+'.sv')))
        declarations.append(f'reg [{width-1}:0] v{i}[0:{cycles-1}];reg [{n-1}:0] d{i};reg r{i},iv{i};wire y{i},ov{i};{name} dut{i}(.clk(clk),.rstn(r{i}),.iv(iv{i}),.data(d{i}),.y(y{i}),.ov(ov{i}));')
        assignments.append(f'{{d{i},r{i},iv{i}}}=v{i}[j][{width-1}:{r+1}];')
        checks.append(f'if(ov{i}!==v{i}[j][0])$fatal(1,"valid context{i} row%0d",j);if(j>0 && (dut{i}.observed!==v{i}[j][{r}:1] || y{i}!==( ^v{i}[j][{r}:1])))$fatal(1,"data context{i} row%0d",j);')
        initial.append(f'$readmemh("{path}",v{i});')
        geometry_ports.append(f'input wire [{n-1}:0] d{i},output wire y{i},ov{i}')
        geometry_instances.append(f'{name} g{i}(.clk(clk),.rstn(rstn),.iv(iv),.data(d{i}),.y(y{i}),.ov(ov{i}));')
    (out/'kernels.sv').write_text('\n'.join(modules))
    (out/'testbench.sv').write_text('module ContextTb;reg clk=0;integer j;\n'+'\n'.join(declarations)+'\ninitial begin\n'+'\n'.join(initial)+f'\nfor(j=0;j<{cycles};j=j+1)begin clk=0;\n'+'\n'.join(assignments)+'\n#5;clk=1;#1;\n'+'\n'.join(checks)+f'\n#4;end\n$display("CONTEXT_RTL_PASS sources={len(all_rows)} cycles={cycles} comparisons={len(all_rows)*cycles}");$finish;end\nendmodule\n')
    (out/'geometry-top.sv').write_text('module ContextGeometry(input wire clk,rstn,iv,'+','.join(geometry_ports)+');\n'+'\n'.join(geometry_instances)+'\nendmodule\n')
    (out/'geometry.ys').write_text(f'read_verilog -sv {out/"kernels.sv"} {out/"geometry-top.sv"}\nhierarchy -check -top ContextGeometry\nproc\nopt\ntechmap\nopt\ncheck\nwrite_json {out/"generic.json"}\n')
    graphs=json.loads(gzip.decompress((LOADS/'static-graphs.json.gz').read_bytes()))
    state_records=[dict(candidate=g['candidate'],placement=v['placement'],state=v['state'],
                        source_state_info=g['state_source_info'],stage_skeleton=v['stages']) for g in graphs for v in g['views']]
    write(out/'state-stage-requirements.json',dict(views=state_records,logical_projection_only=True,
        input_service='actual public service projection still required before S production binding',
        external_capture='unconditional actual public output; old enabled projection is not qualification',
        G_sources=['fresh parallel multiplication reduction','fresh serial add','shared-source and shifted-zero add','multiple-exit and live-through'],
        full_MAC_graph_may_train_G=False,required_shared_owners=['shared_clock','shared_physical','root_repair'],
        physical_price_qualification=False))
    write(out/'cohort.json',dict(version='arithmetic-context-source-cohort-v1',sources=rows,capacity_sources=capacity,
        source_roles_frozen=True,physical_labels_read=False,physical_admission_allowed=False,independent_test_allowed=False,
        parent_loads_sha256=sha(LOADS/'loads.json'),requirements_sha256=sha(REQUIREMENTS),protocol_sha256=sha(CONFIG),sampler_sha256=sha(scan.CONFIG)))
    write(out/'coverage.json',dict(required_shapes=len(requirements['operator_shapes']),required_contexts=len(inventory['contexts']),
        direct_capture_contexts=sum(not r['features']['consumers'] for r in rows[:63]),consumer_contexts=sum(bool(r['features']['consumers']) for r in rows[:63]),
        required_context_to_source={r['provenance']['required_context']:r['id'] for r in rows if 'required_context' in r['provenance']},
        source_counts=dict(Counter(r['role'] for r in rows)),static_legal_views=len(state_records),
        cases=[dict(case=c['case'],candidates=[dict(candidate=x['candidate'],assignment_trials=x['assignment_trials'],legal_views=x['legal_views']) for x in c['candidates']]) for c in requirements['cases']],
        physical_endpoint_qualification=False))
    write(out/'capacity-plan.json',dict(version='arithmetic-context-capacity-plan-v1',sources=capacity,physical_tasks=6,
        synth_calls_max=6,grt_calls_max=6,final_calls=0,resources=config['capacity'],later_work_reserved=config['later_work_reserved'],
        formal_operator_sources=len(rows),formal_operator_target_calls_max=13*len(rows),
        time_and_storage_estimates='obtain from these exact capacity sources before formal batch; unknown, not zero',
        prerequisites=['software proof hashes','mapped signal and semantic boundary coverage','actual FF/bank aliases','SDC/ABC/tool/library/CEC identity','live ledger and reserved later work'],
        physical_admission_allowed=False))
    shutil.copy2(CONFIG,out/'protocol.json');shutil.copy2(scan.CONFIG,out/'sampler-policy.json')
    print(json.dumps(dict(status='prepared',sources=len(rows),capacity_sources=len(capacity),required_contexts=63,physical_calls=0)),flush=True)


def reader_fixture():
    ff=dict(sequential=True,buffer_or_inverter=False,data_pins=['D'],area_um2=2,
            pins={'D':dict(direction='input'),'Q':dict(direction='output')})
    gate=dict(sequential=False,buffer_or_inverter=True,data_pins=[],area_um2=1,
              pins={'A':dict(direction='input'),'Y':dict(direction='output')})
    cells={'FF':ff,'G':gate};instances={'launch/data':'FF','core/g':'G','consumer0/g':'G','capture/storage0':'FF'}
    nets={};assign={'launch/data/Q':'n0','core/g/A':'n0','core/g/Y':'n1','consumer0/g/A':'n1','consumer0/g/Y':'n2','capture/storage0/D':'n2','launch/data/D':'port','capture/storage0/Q':'observed'}
    for name,master in instances.items():
        for pin,meta in cells[master]['pins'].items():nets[name+'/'+pin]=dict(direction=meta['direction'],net=assign[name+'/'+pin])
    packet=dict(origin='synthetic_fixture',period_ps=100,time_to_ps=1,instances=instances,liberty=cells,connections=nets,clock_nets=[],
        pin_logic={p:'X' for p in ('core/g/A','core/g/Y','consumer0/g/A','consumer0/g/Y')},
        nodes={'producer':dict(inputs=['core/g/A'],outputs=['core/g/Y'],constants=[],output_paths={'core/g/Y':[['core/g/A',0],['core/g/Y',30]]}),
               'consumer0':dict(inputs=['consumer0/g/A'],outputs=['consumer0/g/Y'],constants=[],output_paths={'consumer0/g/Y':[['consumer0/g/A',0],['consumer0/g/Y',40]]})},
        data_requests={'bank0':{'from':['launch/data/Q'],'through':['core/g/Y'],'to':['capture/storage0/D']}},
        data_paths={'bank0':dict(start='launch/data/Q',end='capture/storage0/D',slack_ps=-5,
            points=[['launch/data/Q',10],['core/g/A',12],['core/g/Y',42],['consumer0/g/A',45],['consumer0/g/Y',85],['capture/storage0/D',90]])})
    return packet,{'producer':'core/','consumer0':'consumer0/'},{'bank0':['capture/storage0']}


def reader_checks():
    packet,nodes,banks=reader_fixture();result=labels.extract(packet,nodes,banks)
    if (result['operator_delay_ps'],result['comb_area_um2'],result['data_setup_slack_ps'],result['total_cell_area_um2'])!=(30,1,-5,6): raise ValueError('reader loses isolated operator or exclusive areas')
    negatives=[]
    def reject(name,mutate):
        p=deepcopy(packet);mutate(p)
        try:labels.extract(p,nodes,banks)
        except ValueError:negatives.append(name)
        else:raise ValueError('bad physical reader accepted: '+name)
    reject('missing_independent_output',lambda p:p['nodes']['producer']['output_paths'].clear())
    reject('missing_signal_census',lambda p:p['connections'].pop('core/g/A'))
    reject('missing_node',lambda p:p['nodes'].pop('consumer0'))
    reject('incomplete_boundary',lambda p:p['nodes']['producer']['inputs'].clear())
    reject('service_in_node_delay',lambda p:p['nodes']['producer']['output_paths']['core/g/Y'].insert(0,['launch/data/Q',0]))
    reject('nonzero_node_origin',lambda p:p['nodes']['producer']['output_paths']['core/g/Y'][0].__setitem__(1,10))
    reject('bypass_not_through_producer',lambda p:p['data_requests']['bank0']['through'].clear())
    reject('wrong_capture_end',lambda p:p['data_paths']['bank0'].update(end='launch/data/D'))
    reject('disconnected_inter_node_wire',lambda p:p['connections']['consumer0/g/A'].update(net='unrelated'))
    reject('unknown_master',lambda p:p['instances'].update({'core/g':'UNKNOWN'}))
    reject('unowned_cell',lambda p:p['instances'].update({'alien/g':'G'}))
    reject('nonfinite_slack',lambda p:p['data_paths']['bank0'].update(slack_ps=float('nan')))
    reject('state_inside_node',lambda p:p['liberty']['G'].update(sequential=True))
    reject('missing_constant_classification',lambda p:p['pin_logic'].pop('core/g/A'))
    reject('constant_output_not_dynamic_label',lambda p:p['pin_logic'].update({'core/g/Y':'0'}))
    reject('direct_wire_without_alias_certificate',lambda p:p['connections']['core/g/Y'].update(net='n0'))
    reject('unexpected_whole_shell_WNS',lambda p:p.update(setup_worst_slack_ps=-999))
    multi=deepcopy(packet);multi_banks={**banks,'bank1':['capture/storage1']}
    multi['instances'].update({'core/branch':'G','capture/storage1':'FF','clockbuf':'G'})
    multi['connections'].update({'core/branch/A':dict(direction='input',net='n0'),'core/branch/Y':dict(direction='output',net='n3'),
        'capture/storage1/D':dict(direction='input',net='n3'),'capture/storage1/Q':dict(direction='output',net='observed1'),
        'clockbuf/A':dict(direction='input',net='clock_root'),'clockbuf/Y':dict(direction='output',net='clock_leaf')})
    multi['clock_nets']=['clock_root','clock_leaf'];multi['pin_logic'].update({'core/branch/A':'X','core/branch/Y':'X'})
    multi['nodes']['producer']['inputs'].append('core/branch/A');multi['nodes']['producer']['outputs'].append('core/branch/Y')
    multi['nodes']['producer']['output_paths']['core/branch/Y']=[['core/branch/A',0],['core/branch/Y',55]]
    multi['data_requests']['bank0']['through'].append('core/branch/Y')
    multi['data_requests']['bank1']={'from':['launch/data/Q'],'through':['core/g/Y','core/branch/Y'],'to':['capture/storage1/D']}
    multi['data_paths']['bank1']=dict(start='launch/data/Q',end='capture/storage1/D',slack_ps=4,
        points=[['launch/data/Q',10],['core/branch/A',12],['core/branch/Y',67],['capture/storage1/D',70]])
    distinct=labels.extract(multi,nodes,multi_banks)
    if distinct['operator_delay_ps']!=55 or distinct['data_setup_slack_ps']!=-5 or distinct['owner_area_um2']['shared_clock']!=1:
        raise ValueError('node maximum, worst slack and shared clock ownership conflated')
    hierarchy_clock=deepcopy(multi)
    hierarchy_clock['instances']['launch/clockbuf']=hierarchy_clock['instances'].pop('clockbuf')
    for pin in ('A','Y'):hierarchy_clock['connections']['launch/clockbuf/'+pin]=hierarchy_clock['connections'].pop('clockbuf/'+pin)
    if labels.extract(hierarchy_clock,nodes,multi_banks)['owner_area_um2']['shared_clock']!=1:
        raise ValueError('hierarchical clock buffer incorrectly billed as functional state')
    unused=deepcopy(packet);unused['liberty']['FF']['pins']['QN']=dict(direction='output')
    for cell in ('launch/data','capture/storage0'):unused['connections'][cell+'/QN']=dict(direction='output',net='<unconnected:'+cell+'/QN>')
    if labels.extract(unused,nodes,banks)['operator_delay_ps']!=30:raise ValueError('unused complementary FF pin breaks data coverage')
    constant=deepcopy(packet)
    constant['liberty']['G']['pins']['C']=dict(direction='input')
    constant['liberty']['K']=dict(sequential=False,buffer_or_inverter=False,constant_driver=True,data_pins=[],area_um2=0.5,pins={'Z':dict(direction='output')})
    constant['instances']['tie0']='K';constant['connections']['tie0/Z']=dict(direction='output',net='const0')
    for owner,cell in (('producer','core/g'),('consumer0','consumer0/g')):
        pin=cell+'/C';constant['connections'][pin]=dict(direction='input',net='const0');constant['pin_logic'][pin]='0';constant['nodes'][owner]['constants'].append(pin)
    constant_result=labels.extract(constant,nodes,banks)
    if constant_result['operator_delay_ps']!=30 or constant_result['owner_area_um2']['root_repair']!=0.5:
        raise ValueError('constant endpoint or root constant-driver charge incorrect')
    return dict(positive=result,multiple_output_positive=distinct,multiple_output_fixture=multi,multiple_output_banks=multi_banks,
                constant_boundary_positive=constant_result,constant_boundary_fixture=constant,
                hierarchical_clock_and_unused_FF_outputs_checked=True,
                negative_checks=negatives,fixture=packet,expected_nodes=nodes,expected_banks=banks,
                physical_labels=False,physical_endpoint_qualification=False)


def reader_snapshot_checks(out,proof):
    """Round-trip real TSV adapter format; every number remains a fixture."""
    out.mkdir(parents=True,exist_ok=False);prefix=out/'fixture';packet=proof['multiple_output_fixture']
    def table(suffix,header,rows):
        Path(str(prefix)+'_'+suffix+'.tsv').write_text('\t'.join(header)+'\n'+''.join('\t'.join(map(str,row))+'\n' for row in rows))
    Path(str(prefix)+'_instances.tsv').write_text(''.join(n+'\t'+m+'\n' for n,m in packet['instances'].items()))
    table('connections',('instance','pin','direction','net'),[(pin.rsplit('/',1)[0],pin.rsplit('/',1)[1],v['direction'],v['net']) for pin,v in packet['connections'].items()])
    table('logic',('pin','logic'),packet['pin_logic'].items());table('clock_nets',('net',),[(n,) for n in packet['clock_nets']])
    table('endpoints',('node','kind','pin'),[(node,kind,pin) for node,v in packet['nodes'].items() for kind in ('inputs','outputs','constants') for pin in v[kind]])
    path_rows=[]
    for node,v in packet['nodes'].items():
        for i,(pin,points) in enumerate(v['output_paths'].items()):
            file=f'fixture_node_{node}_{i}_points.tsv';(out/file).write_text(''.join(p+'\t'+str(t)+'\n' for p,t in points));path_rows.append((node,pin,file))
    table('node_paths',('node','output','file'),path_rows)
    table('data_requests',('bank','kind','pin'),[(bank,kind,pin) for bank,v in packet['data_requests'].items() for kind,pins in v.items() for pin in pins])
    table('data_paths',('bank','start','end','slack'),[(bank,v['start'],v['end'],v['slack_ps']) for bank,v in packet['data_paths'].items()])
    shutil.copy2(str(prefix)+'_data_paths.tsv',str(prefix)+'_data_after.tsv')
    for bank,v in packet['data_paths'].items():
        Path(str(prefix)+'_data_'+bank+'_points.tsv').write_text(''.join(p+'\t'+str(t)+'\n' for p,t in v['points']))
    result=labels.read_snapshot(prefix,100,1,packet['liberty'],proof['expected_nodes'],proof['multiple_output_banks'],origin='synthetic_fixture')
    if result!=proof['multiple_output_positive']:raise ValueError('TSV adapter changes raw labels')
    return dict(status='passed',origin='synthetic_fixture',operator_maximum_ps=result['operator_delay_ps'],data_slack_ps=result['data_setup_slack_ps'])


def scanner_checks():
    histories=[];max_points=0
    def simulate(response,index):
        nonlocal max_points
        rows=[]
        while True:
            decision=scan.decide(rows,'fixture','not_training');q=decision['next_request']
            if q is None:break
            slack=response(q['SDC_ps'],len(rows))
            rows.append(dict(**q,status='completed',source_id='fixture',role='not_training',implementation_id='fixture-'+str(len(rows)),
                operator_delay_ps=600+(len(rows)%3)*10,comb_area_um2=20+len(rows),data_setup_slack_ps=slack,
                operator_maximum_covered=True,data_through_operator_covered=True,ownership_complete=True))
            if len(rows)>13 or len({r['SDC_ps'] for r in rows})!=len(rows):raise ValueError('unbounded/duplicate sampler')
        if decision['eligible_rows_retained']!=list(range(len(rows))):raise ValueError('conditional labels discarded')
        max_points=max(max_points,len(rows));histories.append(dict(index=index,history=rows,decision=decision));return rows,decision
    base,done=simulate(lambda t,i:t-700,'constant_effective_budget')
    if done['coverage_shortfall'] or done['stop_reason']!='regions_complete':raise ValueError('simple response cannot fill regions')
    for sign in (-1,1):
        _,decision=simulate(lambda t,i:sign*t/2,'single_region_'+str(sign))
        if not decision['coverage_shortfall']:raise ValueError('single-region response falsely covered')
    for seed in range(64):
        rng=random.Random(seed);values=[rng.choice([-0.5,-0.1,0,0.1,0.5]) for _ in range(13)]
        simulate(lambda t,i:t*values[i],'nonmonotone_'+str(seed))
    edges=[('-0.100000000001',0),('-0.1',1),('0',1),('0.1',1),('0.100000000001',2)]
    if any(scan.region(x)!=want for x,want in edges):raise ValueError('decimal region boundary error')
    negatives=[]
    def reject(name,mutate):
        rows=deepcopy(base);mutate(rows)
        try:scan.decide(rows,'fixture','not_training')
        except ValueError:negatives.append(name)
        else:raise ValueError('bad sampler history accepted: '+name)
    reject('wrong_ABC',lambda r:r[0].update(ABC_ps=100))
    reject('wrong_source',lambda r:r[0].update(source_id='other'))
    reject('wrong_role',lambda r:r[0].update(role='train'))
    reject('boolean_target',lambda r:r[0].update(SDC_ps=True,ABC_ps=True))
    reject('missing_operator_max',lambda r:r[0].update(operator_maximum_covered=False))
    reject('missing_through_coverage',lambda r:r[0].update(data_through_operator_covered=False))
    reject('missing_ownership',lambda r:r[0].update(ownership_complete=False))
    reject('duplicate_implementation',lambda r:r[1].update(implementation_id=r[0]['implementation_id']))
    reject('nonfinite_label',lambda r:r[0].update(operator_delay_ps=float('inf')))
    reject('negative_area',lambda r:r[0].update(comb_area_um2=-1))
    reject('posterior_feature',lambda r:r[0].update(measured_Tmin=1))
    first={k:v for k,v in base[0].items() if k in ('SDC_ps','ABC_ps','proposal','reference_ratio','source_id','role')}
    first.update(status='failed',failure_reason='timeout')
    failed=scan.decide([first],'fixture','not_training')
    if failed['next_request'] or failed['eligible_rows_retained'] or failed['stop_reason']!='failed_point_no_retry':raise ValueError('failed point retried or relabeled')
    return dict(histories=histories,trajectories=len(histories),maximum_points=max_points,exact_boundary_checks=edges,
                negative_checks=negatives,failure_retention=failed,synthetic_responses_not_measurements=True)


def checks(out):
    out.mkdir(parents=True,exist_ok=False)
    reader=reader_checks();scanner=scanner_checks()
    reader['TSV_adapter_roundtrip']=reader_snapshot_checks(out/'reader-TSV',reader)
    write(out/'reader.json',reader);write(out/'scanner.json',scanner)
    spec=dict(operation='mul',lhs_width=3,rhs_width=2,result_width=5,carry='zero',capture_banks=1)
    f=dict(producer=spec,consumers=[],captures=[dict(banks=2,declared_width=5,result_bit_map=[0,1,2,3,4])])
    for a in range(8):
        for b in range(4):
            value=a|(b<<3);want=a*b
            if shells.evaluate(f,value)!=want|(want<<5):raise ValueError('independent tiny-multiply bit mapping differs')
    negatives=[]
    variants=[('bad_result_bit',lambda x:x['captures'][0]['result_bit_map'].__setitem__(0,5)),
              ('bad_origin_bool',lambda x:x['captures'][0]['result_bit_map'].__setitem__(0,True)),
              ('missing_capture_bit',lambda x:x['captures'][0]['result_bit_map'].pop()),
              ('case_as_feature',lambda x:x.update(case_id='MAC_32')),
              ('overlapping_known_masks',lambda x:x['producer'].update(lhs_zero_hex='1',lhs_one_hex='1'))]
    for name,change in variants:
        bad=deepcopy(f);change(bad)
        try:shells.layout(bad)
        except ValueError:negatives.append(name)
        else:raise ValueError('bad shell accepted: '+name)
    write(out/'proof.json',dict(status='passed',tiny_arithmetic_cases=32,shell_negatives=negatives,
        reader_negatives=len(reader['negative_checks']),scanner_negatives=len(scanner['negative_checks']),
        sampler_trajectories=scanner['trajectories'],maximum_sampler_points=scanner['maximum_points'],
        physical_endpoint_qualification=False,PPA_calls=0))
    print(json.dumps(read(out/'proof.json')),flush=True)


def verify(out):
    software=out/'software';c=read(software/'cohort.json');design=read(software/'generic.json');geometries={}
    for row in c['sources']+c['capacity_sources']:
        if sha(software/(row['id']+'.sv'))!=row['rtl_sha256']:raise ValueError('source changed after simulation')
        geometries[row['id']]=shells.generic_geometry(design,row['module'],row['features'])
    marker=f'CONTEXT_RTL_PASS sources={len(geometries)} cycles=96 comparisons={len(geometries)*96}'
    if marker not in (out/'simulate.log').read_text() or '%Warning' in (out/'verilator.log').read_text():raise ValueError('RTL acceptance incomplete or warnings')
    counts=Counter(r['role'] for r in c['sources'])
    if dict(counts)!={'train':63,'validation':12,'locked_test':12}:raise ValueError('source role counts changed')
    if len({r['source_group'] for r in c['sources']+c['capacity_sources']})!=90:raise ValueError('source groups leak across roles')
    write(out/'geometry-proof.json',dict(status='passed',geometries=geometries,software_geometry_only=True))
    write(out/'round1-proof.json',dict(status='passed',sources=87,capacity_sources=3,required_contexts=63,
        RTL_comparisons=90*96,FF_geometry_checked_sources=90,roles=dict(counts),software_checks=read(out/'checks/proof.json'),
        physical_endpoint_qualification=False,physical_admission_allowed=False,fitting_allowed=False,
        independent_test_allowed=False,production_binding_implemented=False,full_D_ready=False))
    print(json.dumps(read(out/'round1-proof.json')),flush=True)


def execute_leaf(out,name,command,timeout=180):
    from experiments.arithmetic_dse.budget import Ledger,usage
    from experiments.arithmetic_dse.processes import run_command
    out.mkdir(parents=True,exist_ok=False);ledger=Ledger();before=read(ledger.path)
    ctx=dict(target_platform='asap7',admission_id=out.name,task_id=name)
    env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4')
    try:
        with ledger.job(ctx):
            r=ledger.reserve(None,timeout,4,'target_round1_software',command,out/name,context=ctx)
            record=run_command(command,out,name,timeout,env,8192,cpu_limit_s=r['CPU_time_s']);ledger.finish(r,record)
            write(out/'commands.json',[dict(**record,budget_reservation_id=r['id'])])
    finally:
        after=read(ledger.path);write(out/'resource-increment.json',dict(entries=after['entries'][len(before['entries']):],usage=usage(after['entries']),PPA_calls=0))
    print(Path(record['log']).read_text()[-3000:],flush=True)
    if record['exit_code']:raise RuntimeError('paid leaf failed; source/log/cost retained: '+str(out))


def run(out):
    from experiments.arithmetic_dse.budget import Ledger,usage,POLICY
    out.mkdir(parents=True,exist_ok=False);ledger=Ledger();before=read(ledger.path);records=[]
    cfg=read(CONFIG);u=usage(before['entries']);limits=read(POLICY)['resources'];reserved=cfg['later_work_reserved']
    if u['walltime_s']+1800+reserved['walltime_s']>limits['max_global_walltime_h']*3600 or u['CPU_time_s']+7200+reserved['CPU_time_s']>limits['max_tool_CPU_time_h']*3600:raise ValueError('software and later work not funded')
    env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4')
    from experiments.arithmetic_dse.processes import run_command
    ctx=dict(target_platform='asap7',admission_id=out.name,task_id='round1-software')
    try:
        with ledger.job(ctx):
            def leaf(command,name,timeout):
                reservation=ledger.reserve(None,timeout,4,'target_round1_software',command,out/name,context=ctx)
                record=run_command(command,out,name,timeout,env,8192,cpu_limit_s=reservation['CPU_time_s']);ledger.finish(reservation,record)
                records.append(dict(**record,budget_reservation_id=reservation['id']));write(out/'commands.json',records)
                print(name+': '+Path(record['log']).read_text()[-1200:],flush=True)
                if record['exit_code']:raise RuntimeError('round1 leaf failed; retained '+record['log'])
            leaf([sys.executable,'-B',str(Path(__file__)),'checks','--out',str(out/'checks')],'checks',180)
            leaf([sys.executable,'-B',str(Path(__file__)),'prepare','--out',str(out/'software')],'prepare',180)
            leaf(['verilator','--binary','--timing','--top-module','ContextTb','--Mdir',str(out/'obj'),'-j','4',str(out/'software/kernels.sv'),str(out/'software/testbench.sv')],'verilator',600)
            leaf([str(out/'obj/VContextTb')],'simulate',120)
            leaf([str(YOSYS),'-s',str(out/'software/geometry.ys')],'generic-geometry',300)
            leaf([sys.executable,'-B',str(Path(__file__)),'verify','--out',str(out)],'verify',180)
    finally:
        after=read(ledger.path);write(out/'resource-increment.json',dict(entries=after['entries'][len(before['entries']):],usage=usage(after['entries']),PPA_calls=0))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('run','prepare','checks','verify','leaf'))
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--name',default='support');parser.add_argument('--timeout',type=int,default=180)
    args,command=parser.parse_known_args()
    if args.action=='leaf':execute_leaf(args.out.resolve(),args.name,command[1:] if command[:1]==['--'] else command,args.timeout)
    else:
        if command:parser.error('unexpected arguments: '+str(command))
        globals()[args.action](args.out.resolve())
