"""Frozen microbenchmark tasks and Q-to-D label contracts for step seven."""
import csv,hashlib,json,math,re
from fnmatch import fnmatchcase
from pathlib import Path
from .budget import POLICY,usage

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def label_requests(contract):
    """Expand explicit bank witnesses without changing legacy label rows."""
    rows=[]
    for row in contract['labels']:
        rows.append(row)
        if 'capture_banks' not in row:continue
        banks=row['capture_banks'];fanout=row.get('fanout')
        if type(fanout) is not int or not 2<=fanout<=4 or len(banks)!=fanout:raise ValueError('invalid capture-bank topology')
        for bank in banks:
            if type(bank['static_bit_capacity']) is not int or bank['static_bit_capacity']!=row['capture_width']:raise ValueError('capture-bank width differs from native core')
            rows.append({'id':bank['id'],'source_cells':row['source_cells'],'target_cells':bank['target_cells'],'parent_sample_id':row['id']})
    if not rows or len({x['id'] for x in rows})!=len(rows):raise ValueError('unique nonempty model labels required')
    return rows

def verify_capture_banks(prefix,contract,cells):
    """Prove actual distinct electrical capture banks, not nominal fanout."""
    specifications=json.loads(Path(contract).read_text())['labels'];result={}
    contextual=[row for row in specifications if 'capture_banks' in row]
    if not contextual:return result
    label_requests({'labels':specifications})
    instances=[line.split('\t')[:2] for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines()]
    def matched(patterns):
        if isinstance(patterns,str):patterns=[patterns]
        return {name for name,master in instances if master in cells and cells[master]['sequential'] and any(fnmatchcase(name,p) for p in patterns)}
    for row in contextual:
        source=matched(row['source_cells']);capacity=sum(row['input_widths']);used=set();counts={}
        if not 0<len(source)<=capacity:raise ValueError('actual interval launch bank exceeds static capacity or is absent')
        for bank in row['capture_banks']:
            found=matched(bank['target_cells'])
            if not 0<len(found)<=bank['static_bit_capacity'] or used & found:
                raise ValueError('capture bank absent, merged, overlapping or larger than static capacity')
            used.update(found);counts[bank['id']]=len(found)
        if len(set(counts.values()))!=1 or used!=matched(row['target_cells']):
            raise ValueError('capture banks do not retain equal distinct mapped loads')
        result[row['id']]={'launch_DFFs':len(source),'capture_DFFs':len(used),'capture_bank_counts':counts,
                          'declared_capture_fanout':row['fanout'],'static_capacity_per_bank':row['capture_width'],
                          'static_launch_capacity':capacity,'mapped_counts_are_prediction_inputs':False}
    return result

def render_label_requests(path):
    contract=json.loads(Path(path).read_text())
    if contract.get('version')!='arithmetic-model-labels-v1':raise ValueError('unsupported model label contract')
    rows=label_requests(contract)
    lines=[]
    for row in rows:
        if not re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',row['id']):raise ValueError('nonstatic characterization sample name')
        selectors=[]
        for key in ('source_cells','target_cells'):
            patterns=row[key] if isinstance(row[key],list) else [row[key]]
            if not patterns or any(not isinstance(v,str) or not re.fullmatch('[A-Za-z0-9_/*]+',v) for v in patterns):raise ValueError('nonstatic characterization boundary name')
            selectors.append('{'+' '.join(patterns)+'}')
        lines.append('  {'+row['id']+' '+' '.join(selectors)+'}')
    return 'set vulsim_label_requests {\n'+'\n'.join(lines)+'\n}\n'

def read_labels(prefix,contract,time_to_ps):
    rows=list(csv.DictReader(Path(str(prefix)+'_model_paths.tsv').read_text().splitlines(),delimiter='\t'))
    expected={x['id']:x for x in label_requests(json.loads(Path(contract).read_text()))}
    if len(rows)!=len(expected) or {x['sample_id'] for x in rows}!=set(expected):raise ValueError('incomplete characterization labels')
    result=[]
    for row in rows:
        specification=expected[row['sample_id']]
        for field,selector in [('start_pin','source_cells'),('end_pin','target_cells')]:
            patterns=specification[selector] if isinstance(specification[selector],list) else [specification[selector]]
            if not any(fnmatchcase(row[field].rsplit('/',1)[0],pattern) for pattern in patterns):raise ValueError('raw model path outside declared register boundary')
        start,end,delay=(float(row[k]) for k in ('start_arrival_native','end_arrival_native','data_delay_native'))
        if any(not math.isfinite(x) for x in (start,end,delay)) or delay<0 or not math.isclose(end-start,delay,abs_tol=1e-6,rel_tol=1e-6):raise ValueError('invalid Q-to-D arrival difference')
        points=Path(str(prefix)+'_model_'+row['sample_id']+'_points.tsv')
        values=[line.split('\t') for line in points.read_text().splitlines()]
        q=[float(v) for pin,v in values if pin==row['start_pin']]
        if len(values)!=int(row['point_count']) or len(q)!=1 or not math.isclose(q[0],start,abs_tol=1e-6):raise ValueError('model label start Q point mismatch')
        if values[-1][0]!=row['end_pin'] or not math.isclose(float(values[-1][1]),end,abs_tol=1e-6):raise ValueError('model label end D point mismatch')
        entry={'id':row['sample_id'],'data_delay_ps':delay*time_to_ps,'start_pin':row['start_pin'],'end_pin':row['end_pin'],
                       'label_definition':'launch_Q_to_capture_D_arrival_difference_excludes_clock_clkQ_setup',
                       'points_sha256':sha(points),'contract_sha256':sha(contract)}
        if 'parent_sample_id' in specification:entry['parent_sample_id']=specification['parent_sample_id']
        extra=('slack_native','setup_margin_s','clk_skew_s')
        if any(k in row for k in extra):
            if not all(k in row and math.isfinite(float(row[k])) for k in extra):raise ValueError('incomplete/nonfinite boundary timing label')
            entry.update(slack_ps=float(row['slack_native'])*time_to_ps,setup_margin_ps=float(row['setup_margin_s'])*1e12,clock_skew_ps=float(row['clk_skew_s'])*1e12)
            raw=Path(str(prefix)+'_model_'+row['sample_id']+'.rpt')
            entry['expanded_path_report_sha256']=sha(raw)
        result.append(entry)
    return result

def verify_admission(args,p,rtl,ledger):
    a=json.loads(args.admission.read_text());matches=[t for t in a['tasks'] if t['id']==args.task_id]
    if (a['purpose']!='arithmetic_model_probe_only' or a['id']!=args.admission_id
            or a['policy_sha256']!=sha(POLICY) or len(matches)!=1 or a['automatic_retries']!=0):raise ValueError('invalid model probe admission')
    t=matches[0]
    if (t['platform']!=p['platform'] or t['profile_sha256']!=p['profile_sha256']
            or t['rtl_sha256']!=sha(rtl) or t['top']!=args.top or t['period_ps']!=args.period_ps
            or t['abc_target_ps']!=args.abc_target_ps or t['stage']!=args.stage
            or args.stage not in ('synth','grt') or args.budget_purpose!='characterization'
            or args.threads!=2 or args.memory_limit_mib!=8192 or args.resume_synth_from
            or args.synth_timeout_s!=300 or args.route_timeout_s!=1200
            or not args.sample_contract or sha(args.sample_contract)!=t['sample_contract_sha256']
            or args.io_delay_max_ps is not None):raise ValueError('model probe differs from frozen task')
    total=usage(json.loads(ledger.path.read_text())['entries']);entries=json.loads(ledger.path.read_text())['entries']
    if total['pending'] or any(e.get('admission_id')==a['id'] and e.get('task_id')==t['id'] for e in entries):raise ValueError('pending or previously attempted model probe')
    limits=json.loads(POLICY.read_text())['resources']
    previous=[e for e in entries if e.get('admission_id')==a['id']]
    for stage,key in [('synth','max_synthesis_calls'),('grt','max_global_route_calls'),('final','max_detailed_route_calls')]:
        remaining=a['call_caps'][stage]-sum(e['stage']==stage for e in previous)
        if remaining<0 or total[stage]+remaining>limits[key]:raise ValueError('model probe calls not funded')
    wall=(a['call_caps']['synth']-sum(e['stage']=='synth' for e in previous))*300+(a['call_caps']['grt']-sum(e['stage']=='grt' for e in previous))*1200+a['support_walltime_s']
    if total['walltime_s']+wall>limits['max_global_walltime_h']*3600 or total['CPU_time_s']+2*wall>limits['max_tool_CPU_time_h']*3600:raise ValueError('model probe time not funded')
    return sha(args.admission)
