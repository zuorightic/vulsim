"""Exhaustive cell ownership and Q/core/capture timing decomposition."""
from collections import Counter,defaultdict
import csv
from fnmatch import fnmatchcase
import gzip
import math
from pathlib import Path
import re

from .model_collection import sha
from .model_reference_samples import requests


def blocks(text,kind):
    pattern=r'\b'+kind+r'\s*\(\s*"?([^"\s,)]+)[^)]*\)\s*\{'
    for m in re.finditer(pattern,text):
        level=1;at=m.end();quoted=False;escaped=False
        while at<len(text) and level:
            c=text[at]
            if escaped:escaped=False
            elif c=='\\':escaped=True
            elif c=='"':quoted=not quoted
            elif not quoted:
                if c=='{':level+=1
                elif c=='}':level-=1
            at+=1
        if level:raise ValueError('unbalanced Liberty block')
        yield m[1],text[m.end():at-1]


def liberty(libraries,base_cells):
    result={}
    for entry in libraries:
        path=Path(entry['path'])
        if sha(path)!=entry['sha256']:raise ValueError('reference Liberty identity mismatch')
        text=(gzip.decompress(path.read_bytes()).decode() if path.suffix=='.gz' else path.read_text())
        for name,body in blocks(text,'cell'):
            if name not in base_cells:raise ValueError('reference unknown Liberty cell')
            pins={}
            for pin,part in blocks(body,'pin'):
                direction=re.search(r'\bdirection\s*:\s*"?(input|output|inout|internal)\b',part)
                if not direction:raise ValueError('Liberty pin lacks direction')
                function=re.search(r'\bfunction\s*:\s*"([^"]+)"',part)
                pins[pin]={'direction':direction[1],'function':function[1] if function else None}
            sequential=base_cells[name]['sequential'];clock=set();data=set()
            for _,part in blocks(body,'ff'):
                for attr,target in [('clocked_on',clock),('next_state',data)]:
                    match=re.search(r'\b'+attr+r'\s*:\s*"([^"]+)"',part)
                    if not match:raise ValueError('reference FF lacks '+attr)
                    target.update(p for p in re.findall(r'[A-Za-z_][A-Za-z0-9_]*',match[1]) if p in pins)
            ins={p for p,v in pins.items() if v['direction']=='input'};outs=[v['function'] for v in pins.values() if v['direction']=='output']
            buffer=(not sequential and len(ins)==1 and len(outs)==1 and outs[0] is not None and
                re.sub(r'[\s()!~]','',outs[0])==next(iter(ins)))
            result[name]={**base_cells[name],'pins':pins,'clock_pins':sorted(clock),'data_pins':sorted(data),'buffer_or_inverter':buffer}
    if set(result)!=set(base_cells):raise ValueError('reference Liberty cell table incomplete')
    return result


def partition(prefix,cells,profile,expected=None,scopes=None):
    scopes=scopes or {'launch/':'input_service','core/':'arithmetic','capture/':'native_state','external/':'external_state','observer/':'observer'}
    instances={};masters={}
    for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines():
        name,master,*_=line.split('\t')
        if name in instances:raise ValueError('duplicate physical instance')
        instances[name]=master
    for line in Path(str(prefix)+'_cells.tsv').read_text().splitlines():
        master,n,area,filler,kind=line.split('\t');masters[master]={'count':int(n),'area':float(area),'filler':filler=='1','type':kind}
    if Counter(instances.values())!=Counter({m:r['count'] for m,r in masters.items()}):raise ValueError('instance/master accounting mismatch')
    connections={};drivers=defaultdict(list)
    for row in csv.DictReader(Path(str(prefix)+'_reference_connections.tsv').read_text().splitlines(),delimiter='\t'):
        key=(row['instance'],row['pin'])
        if key in connections or row['instance'] not in instances:raise ValueError('unknown/duplicate physical pin')
        connections[key]=row['net']
        if row['direction']=='OUTPUT' and row['net']!='<unconnected>':drivers[row['net']].append(key)
    clocks=set();pending=[]
    for name,master in instances.items():
        if master in cells and cells[master]['sequential']:
            if not cells[master]['clock_pins'] or not cells[master]['data_pins']:raise ValueError('unsupported used sequential Liberty interface')
            for pin in cells[master]['clock_pins']:
                net=connections.get((name,pin))
                if net is None or net=='<unconnected>':raise ValueError('state has missing clock connection')
                pending.append(net)
    seen=set()
    while pending:
        net=pending.pop()
        if net in seen:continue
        seen.add(net)
        if len(drivers[net])>1:raise ValueError('multiply-driven clock net')
        for name,pin in drivers[net]:
            master=instances[name]
            if master not in cells or not cells[master]['buffer_or_inverter']:raise ValueError('unsupported non-buffer clock logic')
            clocks.add(name)
            for p,v in cells[master]['pins'].items():
                if v['direction']=='input':pending.append(connections[(name,p)])
    area=defaultdict(float);counts=Counter();ff=Counter();ownership=[]
    for name,master in instances.items():
        physical=masters[master];value=physical['area']
        if not math.isfinite(value) or value<0:raise ValueError('invalid physical cell area')
        if physical['filler']:owner='excluded_filler'
        elif physical['type'] in profile['physical_master_types'] or any(master.startswith(p) for p in profile['allowed_physical_prefixes']):owner='shared_physical'
        else:
            if master not in cells:raise ValueError('functional cell missing Liberty')
            c=cells[master]
            if not math.isclose(value,c['area_um2'],rel_tol=1e-6,abs_tol=1e-6):raise ValueError('reference LEF/Liberty area mismatch')
            matches=[owner for prefix,owner in scopes.items() if name.startswith(prefix)]
            if len(matches)>1:raise ValueError('overlapping functional ownership scopes')
            if name in clocks:owner='shared_clock'
            elif matches:owner=matches[0]
            elif c['buffer_or_inverter']:owner='root_boundary_repair'
            else:raise ValueError('unattributed functional cell: '+name)
            if c['sequential']:
                if owner not in ('input_service','native_state','external_state'):raise ValueError('state outside declared owner')
                ff[owner]+=1
        area[owner]+=value;counts[owner]+=1;ownership.append({'instance':name,'master':master,'owner':owner,'area_um2':value})
    if expected is not None:
        for owner,n in expected.items():
            if ff[owner]!=n:raise ValueError(f'reference state geometry differs: {owner} {ff[owner]} != {n}')
    total=sum(r['count']*r['area'] for r in masters.values() if not r['filler'])
    owned=sum(v for k,v in area.items() if k!='excluded_filler')
    if not math.isclose(total,owned,rel_tol=1e-12,abs_tol=1e-9):raise ValueError('reference area partition incomplete')
    return {'owner_area_um2':dict(area),'owner_cells':dict(counts),'owner_FF_bits':dict(ff),'total_area_um2':total,
        'ownership':ownership,'clock_buffer_instances':sorted(clocks),'all_cells_accounted_once':True,
        'post_mapping_counts_used_as_prediction_features':False},instances,connections


def labels(prefix,s,period,time_to_ps,cells,instances):
    expected={r['id']:r for r in requests(s)}
    table=list(csv.DictReader(Path(str(prefix)+'_reference_paths.tsv').read_text().splitlines(),delimiter='\t'))
    if len(table)!=len(expected) or {r['id'] for r in table}!=set(expected):raise ValueError('reference path coverage incomplete')
    result=[]
    def pin_info(name):
        cell,pin=name.rsplit('/',1)
        if cell not in instances or instances[cell] not in cells:raise ValueError('reference unknown path cell')
        return cell,pin,cells[instances[cell]]
    for row in table:
        request=expected[row['id']];kind=request['kind']
        end_cell,end_pin,end_meta=pin_info(row['end'])
        if end_pin not in end_meta['data_pins'] or not any(fnmatchcase(end_cell,x) for x in request['to']):raise ValueError('reference endpoint not declared capture D')
        if kind=='register':
            start_cell,start_pin,start_meta=pin_info(row['start'])
            if start_meta['pins'][start_pin]['direction']!='output' or not start_meta['sequential'] or not any(fnmatchcase(start_cell,x) for x in request['from']):raise ValueError('reference launch not declared Q')
        elif not any(fnmatchcase(row['start'],x) for x in request['from']):raise ValueError('reference port start mismatch')
        a,b,delay,slack=[float(row[k]) for k in ('start_arrival','end_arrival','delay','slack')]
        if any(not math.isfinite(x) for x in (a,b,delay,slack)) or delay<0 or not math.isclose(b-a,delay,abs_tol=1e-6,rel_tol=1e-6):raise ValueError('invalid reference path arrival difference')
        path=Path(str(prefix)+'_reference_'+row['id']+'_points.tsv');points=[line.split('\t') for line in path.read_text().splitlines()]
        selected=[float(v) for name,v in points if name==row['start']]
        if len(points)!=int(row['points']) or len(selected)!=1 or not math.isclose(selected[0],a,abs_tol=1e-6) or points[-1][0]!=row['end'] or not math.isclose(float(points[-1][1]),b,abs_tol=1e-6):raise ValueError('reference points differ from label')
        d=delay*time_to_ps;H=period-(.2*period if kind=='port' else 0)-d-slack*time_to_ps
        entry={'id':row['id'],'kind':kind,'start_pin':row['start'],'end_pin':row['end'],'QD_or_PD_ps':d,'slack_ps':slack*time_to_ps,
            'clock_capture_term_ps':H,'raw_setup_margin_ps':float(row['setup_margin_s'])*1e12,'raw_clock_skew_ps':float(row['clk_skew_s'])*1e12,
            'points_sha256':sha(path),'expanded_report_sha256':sha(Path(str(prefix)+'_reference_'+row['id']+'.rpt'))}
        if not math.isfinite(entry['raw_setup_margin_ps']) or not math.isfinite(entry['raw_clock_skew_ps']):raise ValueError('nonfinite reference clock terms')
        if row['id']=='data':
            core=[]
            for name,value in points:
                if name.startswith('core/'):
                    _,pin,meta=pin_info(name)
                    if meta['pins'][pin]['direction']=='output':core.append((name,float(value)))
            if not core:raise ValueError('reference arithmetic core output absent from expanded path')
            end_core,t=core[-1];reference=(t-a)*time_to_ps;suffix=(b-t)*time_to_ps
            if reference<=0 or suffix < -1e-6 or not math.isclose(reference+suffix,d,abs_tol=1e-6,rel_tol=1e-9):raise ValueError('invalid core/capture decomposition')
            entry.update(reference_data_delay_ps=reference,capture_suffix_ps=suffix,core_end_pin=end_core,
                joint_reference_overhead_ps=H+suffix,
                label_definition='launch_Q_to_last_core_output_including_launch_wire; capture_suffix_and_clock_terms_separate')
        result.append(entry)
    return result
