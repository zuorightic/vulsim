"""Reset readout successor: use only the shared Tcl pin helper preamble."""
import argparse
import inspect
from pathlib import Path
from types import FunctionType
from . import stage67_reset_v1 as parent


def render(folder,state,owners):
    text=inspect.getsource(parent.render)
    old=".split('if {![info exists stage7_requests]}')[0]"
    new=".split('if {![info exists stage7_requests]')[0]"
    if text.count(old)!=1:raise ValueError('frozen reset helper split changed')
    ns=dict(parent.render.__globals__);exec(compile(text.replace(old,new),__file__,'exec'),ns)
    return ns['render'](folder,state,owners)


def collect(root):
    ns=dict(parent.collect.__globals__);ns['render']=render
    FunctionType(parent.collect.__code__,ns)(root)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('admit','collect','extract'));p.add_argument('--root',type=Path,required=True);p.add_argument('--role',default='train');p.add_argument('--freeze',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
    if a.action=='admit':parent.admit(a.root.resolve(),a.role,a.freeze.resolve() if a.freeze else None)
    elif a.action=='collect':collect(a.root.resolve())
    else:parent.extract(a.root.resolve(),a.out.resolve())
