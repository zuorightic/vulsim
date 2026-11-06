"""Static native-bank path requests, exact pin/arrival and FF witnesses."""
from collections import Counter
import csv
from fnmatch import fnmatchcase
import math
from pathlib import Path

from .model_collection import sha
from .model_m2_state_collection import SUFFIX,read

REQUESTS=[('state_data','register',['bank/dst*','bank/y*'],['bank/dst*','bank/y*']),
          ('state_enable','register',['bank/valid_q*','bank/ov*'],['bank/dst*','bank/y*']),
          ('state_valid','register',['bank/valid_q*','bank/ov*'],['bank/valid_q*','bank/ov*']),
          ('input_enable','port',['iv'],['bank/dst1_*'])]


def render_requests():
    return 'set vulsim_native_state_requests {\n'+''.join('  {'+name+' '+kind+' {'+' '.join(src)+'} {'+' '.join(dst)+'}}\n' for name,kind,src,dst in REQUESTS)+'}\n'


def labels(prefix,period,time_to_ps):
    rows=list(csv.DictReader(Path(str(prefix)+'_native_state_paths.tsv').read_text().splitlines(),delimiter='\t'))
    expected={name:(kind,src,dst) for name,kind,src,dst in REQUESTS}
    if len(rows)!=4 or {r['id'] for r in rows}!=set(expected):raise ValueError('native state label coverage incomplete')
    result=[]
    for row in rows:
        kind,src,dst=expected[row['id']]
        actual_src=row['start'] if kind=='port' else row['start'].rsplit('/',1)[0]
        if (row['kind']!=kind or not any(fnmatchcase(actual_src,p) for p in src)
            or not any(fnmatchcase(row['end'].rsplit('/',1)[0],p) for p in dst)):
            raise ValueError('native state path outside registered boundary')
        a,b,delay,slack=(float(row[k]) for k in ('start_arrival','end_arrival','delay','slack'))
        if any(not math.isfinite(v) for v in (a,b,delay,slack)) or delay<0 or not math.isclose(b-a,delay,rel_tol=1e-6,abs_tol=1e-6):
            raise ValueError('invalid native state arrival difference')
        path=Path(str(prefix)+'_native_'+row['id']+'_points.tsv')
        points=[line.split('\t') for line in path.read_text().splitlines()]
        selected=[float(v) for pin,v in points if pin==row['start']]
        if (len(points)!=int(row['points']) or len(selected)!=1 or not math.isclose(selected[0],a,abs_tol=1e-6)
            or points[-1][0]!=row['end'] or not math.isclose(float(points[-1][1]),b,abs_tol=1e-6)):
            raise ValueError('native state point trace differs')
        d,slack_ps=delay*time_to_ps,slack*time_to_ps
        result.append({'id':row['id'],'kind':kind,'delay_ps':d,'slack_ps':slack_ps,
            'H_ps':period-(.2*period if kind=='port' else 0)-d-slack_ps,
            'start_pin':row['start'],'end_pin':row['end'],'points_sha256':sha(path),
            'expanded_report_sha256':sha(Path(str(prefix)+'_native_'+row['id']+'.rpt'))})
    return result


def witness(directory,stage,cells):
    from .platforms import profile
    p=profile('asap7');spec=read(directory/'native-state-contract.json')['spec']
    prefix=directory/'reports'/SUFFIX/('vulsim_'+stage)
    instances=[line.split('\t')[:2] for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines()]
    masters={line.split('\t')[0]:line.split('\t')[1:] for line in Path(str(prefix)+'_cells.tsv').read_text().splitlines()}
    count=Counter(master for _,master in instances)
    for master,(n,area,filler,kind) in masters.items():
        if int(n)!=count[master]:raise ValueError('native state instance master count differs')
    data=valid=0;functional=observer=physical=0.
    for name,master in instances:
        n,area,filler,kind=masters[master]
        if filler=='1' or kind in p['physical_master_types'] or any(master.startswith(s) for s in p['allowed_physical_prefixes']):
            physical+=float(area);continue
        if master not in cells:raise ValueError('unknown native state logical master: '+master)
        c=cells[master]
        if name.startswith('bank/observer/'):
            if c['sequential']:raise ValueError('native observer unexpectedly contains state')
            observer+=c['area_um2'];continue
        if name.startswith('bank/'):functional+=c['area_um2']
        if c['sequential']:
            if any(fnmatchcase(name,pattern) for pattern in ('bank/dst*','bank/y*')):data+=1
            elif any(fnmatchcase(name,pattern) for pattern in ('bank/valid_q*','bank/ov*')):valid+=1
            else:raise ValueError('unaccounted native state cell: '+name)
    expected=(spec['features']['data_bits'],spec['stages'])
    if (data,valid)!=expected:raise ValueError(f'actual native state FFs differ: {(data,valid)} != {expected}')
    return {'actual_data_bits':data,'actual_valid_bits':valid,'functional_state_control_area_um2':functional,
        'excluded_observer_area_um2':observer,'physical_only_area_um2':physical,'mapped_counts_used_as_prediction_features':False}
