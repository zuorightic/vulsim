"""Proof-view successor borrows sequential definitions only.

Combinational cells are evaluated from the actual Liberty pin functions.
Their Yosys module definitions are unnecessary and may not be in the donor.
"""
import argparse
import inspect
from pathlib import Path
from . import stage67_alias_qualify_v1 as parent


def run(root,out):
    text=inspect.getsource(parent.run);old='dict(modules={n:models[n] for n in pins})';new="dict(modules={n:models[n] for n in pins if pins[n]['sequential']})"
    if text.count(old)!=1:raise ValueError('proof-view model selection drift')
    ns=dict(parent.run.__globals__);exec(compile(text.replace(old,new),__file__,'exec'),ns);ns['run'](root,out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.root.resolve(),a.out.resolve())
