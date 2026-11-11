"""Report-only indexed-Boolean extraction successor; no physical reruns."""
import argparse
import inspect
from pathlib import Path
from . import stage67_shared_extract_v2 as previous
from . import stage67_shared_collect_v1 as base
from . import stage67_state_semantics_v2 as semantics
from .model_fast_preflight import read,write,sha


def extract(root,out,completed_subset=False):
    # Keep v2's full input/implementation checks and actual mapped/grt census.
    checked=dict(previous.extract.__globals__);checked['successor_semantics']=semantics
    text=inspect.getsource(previous.extract)
    old="namespace=dict(base.extract.__globals__);exec"
    new="namespace=dict(base.extract.__globals__);namespace['semantics']=successor_semantics;exec"
    if text.count(old)!=1:raise ValueError('checked extractor callsite drift')
    text=text.replace(old,new)
    exec(compile(text,__file__,'exec'),checked);checked['extract'](root,out,completed_subset)
    d=read(out/'dataset.json');d.update(version='shared-compatible-dataset-v3',indexed_Boolean_producer_sha256=sha(Path(semantics.__file__)),extractor_sha256=sha(Path(__file__)))
    write(out/'dataset.json',d)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--completed-subset',action='store_true');a=p.parse_args();extract(a.root.resolve(),a.out.resolve(),a.completed_subset)
