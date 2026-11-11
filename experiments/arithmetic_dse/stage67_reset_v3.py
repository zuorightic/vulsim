"""Reset report successor: reacquire worst paths after endpoint enumeration.

OpenSTA path handles belong to the latest find_timing_paths query. Never keep
one across queries; retain the endpoint and reacquire it before reading points.
"""
import argparse
import inspect
from pathlib import Path
from types import FunctionType
from . import stage67_reset_v1 as parent


def render(folder,state,owners):
    text=inspect.getsource(parent.render)
    old=".split('if {![info exists stage7_requests]}')[0]"
    new=".split('if {![info exists stage7_requests]')[0]"
    if text.count(old)!=1:raise ValueError('reset helper boundary changed')
    text=text.replace(old,new)
    old="foreach point [get_property $worstpath points]"
    new="set worstto [lindex [s7_pins [list $worstend]] 0]\\nset worstfound [find_timing_paths -from $from -to $worstto -path_delay max -group_path_count 1]\\nif {[llength $worstfound]!=1} {error \\\"lost worst reset path\\\"}\\nset worstpath [lindex $worstfound 0]\\nforeach point [get_property $worstpath points]"
    if text.count(old)!=1:raise ValueError('worst reset path callsite changed')
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
