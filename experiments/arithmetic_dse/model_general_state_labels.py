"""General-state path classes and exhaustive disjoint owner labels."""
import csv
from fnmatch import fnmatchcase
import math
from pathlib import Path

from .model_collection import sha
from .model_reference_labels_v2 import partition as reference_partition, canonical_instances

SCOPES={'launch/':'input_service','adapter/':'source_adapter','native/':'native_state',
        'external/':'external_state','observer/':'observer'}
REQUESTS=[
    ('native_data','register',['native/data_*'],['native/data_*']),
    ('native_enable','register',['launch/valid*','native/valid_*'],['native/data_*']),
    ('native_valid','register',['launch/valid*','native/valid_*'],['native/valid_*']),
    ('external_data','register',['native/data_*'],['external/data_*']),
    ('external_valid','register',['native/valid_*'],['external/valid*']),
    ('input_data','port',['in*'],['launch/data_*']),
    ('input_enable','port',['we*'],['launch/data_*']),
    ('input_valid','port',['iv'],['launch/valid*']),
    ('birth_data','register',['launch/data_*'],['native/data_*'])]


def render_requests():
    return 'set vulsim_reference_requests {\n'+''.join(
        '  {'+name+' '+kind+' {'+' '.join(src)+'} {'+' '.join(dst)+'}}\n' for name,kind,src,dst in REQUESTS)+'}\n'


def partition(prefix,cells,profile,s):
    return reference_partition(prefix,cells,profile,expected=s['expected_FF_bits'],scopes=SCOPES)


def labels(prefix,period,time_to_ps,cells,raw_instances):
    instances=canonical_instances(raw_instances)
    expected={name:(kind,src,dst) for name,kind,src,dst in REQUESTS}
    rows=list(csv.DictReader(Path(str(prefix)+'_reference_paths.tsv').read_text().splitlines(),delimiter='\t'))
    if len(rows)!=len(expected) or {r['id'] for r in rows}!=set(expected):raise ValueError('general-state path coverage incomplete')
    def pin(name):
        instance,port=name.rsplit('/',1)
        if instance not in instances or instances[instance] not in cells:raise ValueError('general-state unknown path instance')
        return instance,port,cells[instances[instance]]
    result=[]
    for row in rows:
        kind,src,dst=expected[row['id']];end,port,meta=pin(row['end'])
        if (row['kind']!=kind or port not in meta['data_pins']
            or not any(fnmatchcase(end,p) for p in dst)):
            raise ValueError('general-state path endpoint is not declared D')
        if kind=='register':
            start,port,meta=pin(row['start'])
            if not meta['sequential'] or meta['pins'][port]['direction']!='output':
                raise ValueError('general-state launch is not a state Q')
        else:start=row['start']
        if not any(fnmatchcase(start,p) for p in src):raise ValueError('general-state source outside declared scope')
        a,b,delay,slack=(float(row[k]) for k in ('start_arrival','end_arrival','delay','slack'))
        if any(not math.isfinite(v) for v in (a,b,delay,slack)) or delay<0 or not math.isclose(b-a,delay,rel_tol=1e-6,abs_tol=1e-6):
            raise ValueError('general-state invalid arrival difference')
        path=Path(str(prefix)+'_reference_'+row['id']+'_points.tsv')
        points=[line.split('\t') for line in path.read_text().splitlines()]
        chosen=[float(v) for name,v in points if name==row['start']]
        if (len(points)!=int(row['points']) or len(chosen)!=1 or not math.isclose(chosen[0],a,abs_tol=1e-6)
            or points[-1][0]!=row['end'] or not math.isclose(float(points[-1][1]),b,abs_tol=1e-6)):
            raise ValueError('general-state expanded path differs')
        d=delay*time_to_ps;H=period-(.2*period if kind=='port' else 0)-d-slack*time_to_ps
        margin,skew=float(row['setup_margin_s'])*1e12,float(row['clk_skew_s'])*1e12
        if not all(math.isfinite(v) for v in (H,margin,skew)):raise ValueError('general-state nonfinite boundary')
        result.append({'id':row['id'],'kind':kind,'delay_ps':d,'slack_ps':slack*time_to_ps,'H_ps':H,
            'start_pin':row['start'],'end_pin':row['end'],'raw_setup_margin_ps':margin,'raw_clock_skew_ps':skew,
            'points_sha256':sha(path),'expanded_report_sha256':sha(Path(str(prefix)+'_reference_'+row['id']+'.rpt')),
            'birth_adapter_path_diagnostic_only':row['id']=='birth_data'})
    return result
