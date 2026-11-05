"""Versioned five-bank witnesses; original four-bank producer stays frozen."""
import csv,hashlib,json,math,re
from fnmatch import fnmatchcase
from pathlib import Path
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def label_requests(contract):
    """Expand explicit bank witnesses without changing legacy label rows."""
    rows=[]
    for row in contract['labels']:
        rows.append(row)
        if 'capture_banks' not in row:continue
        banks=row['capture_banks'];fanout=row.get('fanout')
        if type(fanout) is not int or not 2<=fanout<=5 or len(banks)!=fanout:raise ValueError('invalid capture-bank topology')
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
    if contract.get('version')!='arithmetic-model-labels-v2':raise ValueError('unsupported model label contract')
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
