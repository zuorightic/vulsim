"""Versioned raw-name/constant-driver reconciliation; original readers immutable."""
from pathlib import Path
import re
from . import model_reference_labels as parent

BASE_PARTITION=parent.partition
BASE_LABELS=parent.labels
SCOPES={'launch/':'input_service','core/':'arithmetic','capture/':'native_state','external/':'external_state','observer/':'observer'}


def canonical_instances(instances):
    result={}
    for name,master in instances.items():
        key=re.sub(r'\\([\[\]])',r'\1',name)
        if key in result:raise ValueError('ambiguous OpenDB/OpenSTA escaped instance identity')
        result[key]=master
    return result


def partition(prefix,cells,profile,expected=None,scopes=None):
    selected=dict(SCOPES if scopes is None else scopes)
    instances={line.split('\t')[0]:line.split('\t')[1] for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines()}
    constants=[]
    for name,master in instances.items():
        if any(name.startswith(scope) for scope in selected) or master not in cells:continue
        cell=cells[master];pins=cell['pins']
        functions=[v['function'] for v in pins.values() if v['direction']=='output']
        if (not cell['sequential'] and not any(v['direction']=='input' for v in pins.values()) and functions
            and all(f is not None and re.sub(r'[\s()]','',f) in ('0','1',"1'b0","1'b1") for f in functions)):
            if any(other!=name and other.startswith(name) for other in instances):raise ValueError('ambiguous exact constant-driver owner')
            selected[name]='root_boundary_repair';constants.append(name)
    result,raw,connections=BASE_PARTITION(prefix,cells,profile,expected,selected)
    result['explicit_root_constant_drivers']=sorted(constants)
    return result,raw,connections


def labels(prefix,s,period,time_to_ps,cells,instances):
    return BASE_LABELS(prefix,s,period,time_to_ps,cells,canonical_instances(instances))
