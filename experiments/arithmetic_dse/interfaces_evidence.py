"""Portable step4 request/region/cost/RTL and cycle evidence, without a compiler."""
import argparse,gzip,hashlib,importlib.util,json,math,re
from pathlib import Path
from .budget import usage,cpu_seconds
from .fixed_cost import node_cost
from .report_types import validate_report_types
from .freeze_history import source_location
ROOT=Path(__file__).resolve().parents[2]
ORIGINAL='experiments/arithmetic/arithmetic_interfaces_freeze_v1.json'
FREEZE='experiments/arithmetic/arithmetic_interfaces_freeze_v2.json'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(path):
    p=Path(path);return gzip.decompress(p.read_bytes()).decode() if p.suffix=='.gz' else p.read_text()
def same(a,b,label):
    if isinstance(a,bool) or isinstance(b,bool):
        okay=type(a) is type(b) and a==b
    elif type(a) is int and type(b) is int:
        okay=a==b
    elif isinstance(a,(int,float)) and isinstance(b,(int,float)):
        okay=math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-9)
    else:okay=a==b
    if not okay:raise ValueError(f'step4 evidence mismatch: {label}: {a!r} != {b!r}')
def verify_report(report,rtl,features,*,embedded=False,report_schemas=None):
    if report_schemas is None:
        report_schemas=json.loads((ROOT/'experiments/arithmetic_dse/configs/arithmetic_compiler_interfaces_v1.json').read_text())['report_schemas']
    validate_report_types(report,report_schemas)
    same(report['version'],'arithmetic-structure-report-v2','report version');same(report['status'],'passed','compile status')
    same(json.loads(report['graph_identity_text']),report['graph'],'actual graph serialization')
    same(hashlib.sha256(report['graph_identity_text'].encode()).hexdigest(),report['graph_sha256'],'graph hash')
    schedule=json.loads(report['schedule_identity_text']);same(schedule,{'stages':report['stages'],'protocol':report['protocol']},'schedule/protocol serialization')
    same(hashlib.sha256((report['graph_sha256']+report['schedule_identity_text']).encode()).hexdigest(),report['schedule_sha256'],'schedule hash')
    same(hashlib.sha256(rtl.encode()).hexdigest(),report['rtl_sha256'],'emitted kernel hash')
    same(report['delay_unit'],'abstract','cost units');same(report['comb_unit'],'abstract','comb units')
    same(report['request']['cost_mode'],'fixed','no fake D result');same(report['D_inference_implemented'],False,'inference scope')
    protocol=report['protocol'];same(protocol['register_stages'],report['request']['L']-1,'L/N protocol')
    same(report['request']['II'],1,'initiation interval')
    if type(protocol['reset_enabled']) is not bool or type(protocol['reset_active_low']) is not bool:raise ValueError('invalid reset protocol type')
    if not embedded and protocol['register_stages']>0:
        if not re.search(r'@\s*\(\s*posedge\s+'+re.escape(protocol['clock_name'])+r'\s*\)',rtl):raise ValueError('reported clock absent from actual sequential RTL')
    kinds={v:k for k,v in features['operation_kinds'].items()};opcodes={v:k for k,v in features['opcodes'].items()}
    graph=report['graph'];nodes={str(n['id']):n for n in graph['nodes']};same(set(nodes),{str(i) for i in range(len(nodes))},'dense IDs')
    order=[];visiting=set();seen=set()
    def visit(i):
        if i in seen:return
        if i in visiting:raise ValueError('step4 graph cycle')
        if i not in nodes:raise ValueError('step4 dangling graph reference')
        visiting.add(i);n=nodes[i]
        if type(n['kind']) is not int or type(n['opcode']) is not int or n['kind'] not in kinds or n['opcode'] not in opcodes:raise ValueError('step4 unsupported opcode identity')
        if type(n['width']) is not int or n['width']<=0 or any(type(d) is not int or d<=0 for d in n['dims']):raise ValueError('step4 invalid type shape')
        for operand in n['operands']:
            if operand['kind']==0:
                visit(operand['node']);same((operand['width'],operand['dims']),(nodes[operand['node']]['width'],nodes[operand['node']]['dims']),'reference type')
            elif operand['kind']==1:
                same(operand['constant_width'],operand['width'],'literal width');limbs=list(map(int,operand['limbs']));width=operand['width']
                if len(limbs)>(width+63)//64 or any(w<0 or w>=1<<64 for w in limbs) or (sum(w<<(64*i) for i,w in enumerate(limbs))>>width):raise ValueError('step4 invalid literal padding')
            elif operand['kind']!=2:raise ValueError('step4 unsupported operand kind')
        visiting.remove(i);seen.add(i);order.append(i)
    for i in nodes:visit(i)
    constant={};costs={}
    def width(operand):
        current=operand;seen=set()
        while current['kind']==0 and not current['signed']:
            i=current['node']
            if i in seen:raise ValueError('billing provenance cycle')
            seen.add(i);n=nodes[i]
            if kinds[n['kind']] not in ('ZExt','Assign','Cast') or len(n['operands'])!=1:break
            child=n['operands'][0]
            if child['signed'] or child['constant_signed'] or child['width']>current['width']:break
            current=child
        return current['width']
    wire={'Assign','PortRead','Cast','ZExt','SExt','Trunc','Slice','BitSelect','WriteSlice','WriteBit','Concat','Repeat','Aggregate'}
    for i in order:
        n=nodes[i];kind=kinds[n['kind']];deps=n['operands'];op=opcodes[n['opcode']]
        constant[i]=kind!='PortRead' and all(v['kind']==1 or (v['kind']==0 and constant[v['node']]) for v in deps)
        if not n['dims']:same(n['transaction_constant'],constant[i],'static transaction-constant proof')
        if kind in wire:d=a=0
        elif kind in ('Binary','Unary'):
            widths=[width(v) for v in deps];shift_constant=op in ('Shl','Shr') and (deps[1]['kind']==1 or (deps[1]['kind']==0 and constant[deps[1]['node']]))
            c=node_cost(op,widths,n['width'],transaction_constant=constant[i],constant_shift=shift_constant);d=float(c.delay_weight);a=float(c.comb_weight)
            if op in ('Mul','Div','Mod'):same(n['billing_width'],max(widths),'arithmetic billing width')
        else:
            c=node_cost(kind,[width(v) for v in deps],n['width'],transaction_constant=constant[i]);d=float(c.delay_weight);a=float(c.comb_weight)
        same(n['covered'],True,'cost coverage');same(n['cost_source'],'fixed-op-width-v1','cost source');same(n['delay'],d,'node delay');same(n['comb'],a,'node comb');costs[i]=(d,a)
    owners={};port_ids={i for p in graph['ports'] for i in p['nodes']}
    region_results=[]
    for region in graph['regions']:
        same(region['internally_cuttable'],False,'step4 atomic scope')
        for field in ('C_selected','D_covered','D_selected','physically_evaluated'):same(region[field],False,'capability '+field)
        members=set(region['members'])
        if len(members)!=len(region['members']) or not members or not set(region['outputs'])<=members or members&port_ids:raise ValueError('invalid region membership/ports')
        for i in members:
            if i in owners:raise ValueError('overlapping region members')
            owners[i]=region['id']
        arrivals={}
        for i in order:
            if i not in members:continue
            arrivals[i]=costs[i][0]+max((arrivals[v['node']] for v in nodes[i]['operands'] if v['kind']==0 and v['node'] in members),default=0)
        same(region['delay'],max(arrivals.values()),'atomic longest path');same(region['comb'],sum(costs[i][1] for i in members),'atomic unique sum')
        if region['template_id']=='mul-original-v1':
            same(len(members),1,'original Mul member');n=nodes[next(iter(members))];same(kinds[n['kind']],'Binary','original Mul kind');same(opcodes[n['opcode']],'Mul','original Mul opcode')
            parameters={'lhs_width':width(n['operands'][0]),'rhs_width':width(n['operands'][1]),'result_width':n['width']};same(region['parameters'],parameters,'template width parameters')
        elif region['template_id']=='softfloat3d-bitvector-mul-v1':same(region['parameters'],{},'FP parameter scope')
        else:raise ValueError('unregistered region template')
        region_results.append(region['id'])
    # Recompute the selected schedule, costs and shared register chains.
    stages=report['stages'];N=report['request']['L']-1;same(len(stages),len(nodes),'stage coverage')
    live=set(port_ids)|{i for r in graph['regions'] for i in r['outputs']}|{v['node'] for r in graph['regions'] for v in r['inputs'] if v['node']!='literal'}
    stack=list(live)
    while stack:
        for v in nodes[stack.pop()]['operands']:
            if v['kind']==0 and v['node'] not in live:live.add(v['node']);stack.append(v['node'])
    users={i:[] for i in nodes}
    for i in live:
        for v in nodes[i]['operands']:
            if v['kind']==0:users[v['node']].append(i)
    arrivals={};stage_delays=[0]*(N+1);comb=register_bits=register_count=0
    valid_name=report['protocol']['input_valid_name'];valid_nodes=[p['nodes'][0] for p in graph['ports'] if p['name']==valid_name] if valid_name else []
    for i in order:
        if i not in live:continue
        stage=stages[int(i)]
        if stage<0 or stage>N:raise ValueError('invalid computation stage')
        d,a=costs[i]
        if constant[i]:arrivals[i]=0;continue
        before=0
        for v in nodes[i]['operands']:
            if v['kind']!=0 or constant[v['node']]:continue
            parent=stages[int(v['node'])]
            if parent>stage:raise ValueError('backwards schedule dependency')
            if parent==stage:before=max(before,arrivals[v['node']])
        arrivals[i]=before+d;stage_delays[stage]=max(stage_delays[stage],arrivals[i]);comb+=a
        end=max([stage,*[stages[int(u)] for u in users[i]]])
        if i in valid_nodes:end=N
        length=end-stage;bits=nodes[i]['width']*math.prod(nodes[i]['dims']);register_bits+=length*bits;register_count+=length
    for region in graph['regions']:
        if len({stages[int(i)] for i in region['members']})!=1:raise ValueError('atomic region cut by schedule')
    pipeline=report['pipeline'];same(pipeline['final_delay'],max(stage_delays),'selected stage delay');same(pipeline['comb'],comb,'selected comb cost');same(pipeline['register_bits'],register_bits,'shared register bits');same(pipeline['register_count'],register_count,'shared register chains');same(pipeline['allowed_delay'],pipeline['baseline_delay']*105/100,'fixed abstract cap')
    if pipeline['final_delay']>pipeline['allowed_delay']+1e-9:raise ValueError('selected schedule exceeded cap')
    return {'nodes':len(nodes),'regions':len(region_results),'comb':comb,'register_bits':register_bits}

def _verify_original(root,parents):
    """Read immutable v1 reports with their exact frozen reader, never coerce v2."""
    root=Path(root);freeze=json.loads((root/ORIGINAL).read_text());directory=root/freeze['evidence_directory']
    for relative,expected in freeze['files_sha256'].items():
        original=source_location(root,ORIGINAL,relative,expected)
        same(digest(original),expected,'original source '+relative);same(digest(root/freeze['validated_source_snapshot']/relative),expected,'source snapshot '+relative)
    reader_path=root/freeze['validated_source_snapshot']/'experiments/arithmetic_dse/interfaces_evidence.py'
    name=__package__+'._frozen_step4_interfaces_v1'
    spec=importlib.util.spec_from_file_location(name,reader_path);reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    for relative,expected in freeze['historical_freezes'].items():same(digest(root/relative),expected,'historical freeze '+relative)
    same(digest(root/freeze['evidence_index']),freeze['evidence_index_sha256'],'index');index=json.loads((root/freeze['evidence_index']).read_text())
    for relative,expected in index['files_sha256'].items():same(digest(root/relative),expected,'evidence '+relative)
    same(digest(root/'experiments/arithmetic_dse/configs/fixed_op_width_v1.json'),
         'd83c391e3b5435b40d9805c869b01cd9ff8cdf2dae27c173223ca4614d2c59bd','implemented fixed C table identity')
    schema=json.loads((root/'experiments/arithmetic_dse/configs/beir_cost_features_v1.json').read_text());reports=json.loads((directory/'report_index.json').read_text());totals=[]
    for item in reports:
        r=json.loads(read(root/item['report']));rtl=read(root/item['rtl'])
        if item.get('embedded_wrapper'):
            start,end=item['byte_range'];same((root/item['embedded_wrapper']).read_bytes()[start:end],rtl.encode(),'actual embedded kernel range')
        totals.append(reader.verify_report(r,rtl,schema,embedded=bool(item.get('embedded_wrapper'))))
    regression=json.loads((directory/'accepted/regression.json').read_text());trace=reader.verify_trace(directory,regression);same(regression['status'],'passed','regression');same(regression['new_PPA_calls'],{'synth':0,'grt':0,'final':0},'no physical calls')
    before=json.loads((directory/'usage_before.json').read_text());after=json.loads((directory/'usage_after.json').read_text());same(after['entries'][:len(before['entries'])],before['entries'],'immutable charges');extra=after['entries'][len(before['entries']):]
    if usage(after['entries'])['pending'] or any(e['stage'] is not None for e in extra):raise ValueError('unexpected physical or pending step4 charge')
    resources=json.loads((directory/'resources.json').read_text());same(resources['new_usage'],usage(extra),'step4 cost');same(resources['cumulative_usage'],usage(after['entries']),'cumulative cost')
    receipts=json.loads((directory/'command_index.json').read_text());same({e['id'] for e in extra},{r['id'] for r in receipts},'complete command receipts')
    for receipt in receipts:
        e=next(e for e in extra if e['id']==receipt['id']);r=json.loads((root/receipt['record']).read_text());same(r['exit_code'],e['exit_code'],'leaf result');same(r['walltime_s'],e['walltime_s'],'leaf wall');same(cpu_seconds(root/receipt['CPU_report']),e['CPU_time_s'],'leaf CPU')
        if r['cleanup']['remaining_live_pids'] or r['timed_out'] or r['memory_limit_exceeded'] or r['CPU_limit_exceeded']:raise ValueError('unreconciled leaf cleanup/resource failure')
    parent_results={}
    if parents:
        from .platform_evidence import verify as physical
        from .placement_evidence import verify as placement
        from .step2_evidence import verify as step2
        parent_results={'physical_v7':physical(root),'placement':placement(root),'step2':step2(root)}
    return {'status':'passed','freeze':freeze['version'],'source_files':len(freeze['files_sha256']),'evidence_files':len(index['files_sha256']),'reports_recomputed':len(totals),'reported_nodes':sum(t['nodes'] for t in totals),'reported_regions':sum(t['regions'] for t in totals),'native_cpp_checks':regression['native_cpp_checks'],'functional':trace,'new_usage':resources['new_usage'],'cumulative_usage':resources['cumulative_usage'],'parent_status':{k:v['status'] for k,v in parent_results.items()},'requires_build_directory':False,'requires_compiler_or_EDA':False,'D_inference_or_main_matrix':False,'scope':'step4 original Mul/atomic binary32/request/fixed cost/preflight; step5 split selection and step7 models pending'}
def verify(root=ROOT,parents=True):
    root=Path(root);freeze=json.loads((root/FREEZE).read_text());directory=root/freeze['evidence_directory']
    for relative,expected in freeze['files_sha256'].items():
        same(digest(root/relative),expected,'current source '+relative)
        same(digest(root/freeze['source_snapshots'][relative]),expected,'current snapshot '+relative)
    for relative,expected in freeze['historical_freezes'].items():same(digest(root/relative),expected,'historical freeze '+relative)
    same(digest(root/freeze['evidence_index']),freeze['evidence_index_sha256'],'index')
    index=json.loads((root/freeze['evidence_index']).read_text())
    for relative,expected in index['files_sha256'].items():same(digest(root/relative),expected,'evidence '+relative)
    inherited=_verify_original(root,parents)
    types=json.loads((root/'experiments/arithmetic_dse/configs/arithmetic_compiler_interfaces_v1.json').read_text())['report_schemas']
    features=json.loads((root/'experiments/arithmetic_dse/configs/beir_cost_features_v1.json').read_text())
    reports=json.loads((directory/'report_index.json').read_text());totals=[]
    for item in reports:
        report=json.loads(read(root/item['report']));previous=json.loads(read(root/item['inherited_report']))
        rtl=read(root/item['rtl'])
        if item.get('embedded_wrapper'):
            start,end=item['byte_range'];same((root/item['embedded_wrapper']).read_bytes()[start:end],rtl.encode(),'actual embedded kernel range')
        total=verify_report(report,rtl,features,embedded=bool(item.get('embedded_wrapper')),report_schemas=types);totals.append(total)
        for key in ('graph','graph_identity_text','schedule_identity_text','graph_sha256','schedule_sha256','rtl_sha256','request','protocol','stages'):
            if key!='rtl_sha256' or not item.get('annotation_prefix_from'):
                same(report[key],previous[key],'unchanged measured computation '+key)
        if item.get('annotation_prefix_from'):
            old_rtl=read(root/item['inherited_rtl'])
            same(rtl.replace(item['annotation_prefix_from'],item['annotation_prefix_to']),old_rtl,'only source annotation prefix differs')
            same([line.split('//',1)[0] for line in rtl.splitlines()],[line.split('//',1)[0] for line in old_rtl.splitlines()],'executable VUL kernel bytes unchanged')
        for key,value in report['pipeline'].items():
            if key!='register_bits':same(value,previous['pipeline'][key],'unchanged pipeline '+key)
    for item in json.loads((directory/'failure_index.json').read_text()):
        report=json.loads(read(root/item['report']));validate_report_types(report,types)
        same(report['status'],'failed','rejection status');same(report['failure_code'],item['failure_code'],'rejection code')
    parent_directory=root/json.loads((root/ORIGINAL).read_text())['evidence_directory']
    before=json.loads((parent_directory/'usage_after.json').read_text())
    delta=json.loads((directory/'usage_delta.json').read_text())
    same(delta['prefix_sha256'],digest(parent_directory/'usage_after.json'),'resource prefix identity')
    same(delta['prefix_entries'],len(before['entries']),'resource prefix length')
    entries=delta['entries'];combined=before['entries']+entries
    if any(e['stage'] is not None for e in entries) or usage(combined)['pending']:raise ValueError('unexpected physical/pending report-only repair')
    live=root/'experiments/arithmetic/backend_usage.json'
    if live.exists():same(json.loads(live.read_text())['entries'][:len(combined)],combined,'live ledger prefix retained')
    resources=json.loads((directory/'resources.json').read_text());same(resources['new_usage'],usage(entries),'review usage');same(resources['cumulative_usage'],usage(combined),'cumulative usage')
    receipts=json.loads((directory/'command_index.json').read_text());same({e['id'] for e in entries},{r['id'] for r in receipts},'complete review receipts')
    for receipt in receipts:
        entry=next(e for e in entries if e['id']==receipt['id']);record=json.loads((root/receipt['record']).read_text())
        same(record['exit_code'],entry['exit_code'],'leaf outcome');same(record['walltime_s'],entry['walltime_s'],'leaf wall');same(cpu_seconds(root/receipt['CPU_report']),entry['CPU_time_s'],'leaf CPU')
        if any(record[k] for k in ('timed_out','memory_limit_exceeded','CPU_limit_exceeded','unexpected_live_descendants')) or record['cleanup']['remaining_live_pids']:raise ValueError('unclean report repair leaf')
    policy=json.loads((root/'experiments/arithmetic_dse/configs/evidence_storage_v1.json').read_text())
    sizes=[(root/path).stat().st_size for path in index['files_sha256']]+[(root/freeze['evidence_index']).stat().st_size,(root/FREEZE).stat().st_size]
    size=sum(sizes)
    if max(sizes)>policy['new_git_single_file_max_bytes'] or size>policy['new_git_package_target_bytes']:raise ValueError('new evidence exceeds storage policy; partition before bulk work')
    summary=json.loads((directory/'checks.json').read_text());same(summary['status'],'passed','review checks')
    return {'status':'passed','freeze':freeze['version'],'report_version':'arithmetic-structure-report-v2','source_files':len(freeze['files_sha256']),'new_source_snapshots':sum(not v.startswith('experiments/arithmetic/evidence/step4_interfaces_v1/') for v in freeze['source_snapshots'].values()),'new_evidence_files':len(index['files_sha256']),'new_evidence_bytes':size,'reports_recomputed':len(totals),'report_counters_require_integer_tokens':True,'inherited_original_status':inherited['status'],'inherited_reports':inherited['reports_recomputed'],'inherited_functional':inherited['functional'],'parent_status':inherited['parent_status'],'new_usage':resources['new_usage'],'cumulative_usage':resources['cumulative_usage'],'requires_build_directory':False,'requires_compiler_or_EDA':False,'scope':'report serialization/types, historical navigation and storage policy; computation/RTL unchanged'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--no-parents',action='store_true');a=p.parse_args();print(json.dumps(verify(a.root,not a.no_parents),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
