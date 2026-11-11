"""Reset mutation is rejected by the required census-plus-Boolean pipeline.

A direct mapped output alias establishes location, not reset semantics. The
separate exact state proof must reject a mutated reset on such a word.
"""
import argparse
import inspect
from pathlib import Path
from . import stage67_alias_qualify_v1 as base
from . import stage67_alias_qualify_v4 as parent


def run(root,out):
    old="reject('reset_bit',lambda:verify(design,pins,contract,source,rtl.replace(old,new)))"
    new="reject('reset_bit',lambda:semantics(view,verify(design,pins,contract,source,rtl.replace(old,new)),rtl.replace(old,new),contract))"
    text=inspect.getsource(base.run)
    if text.count(old)!=1:raise ValueError('reset negative callsite drift')
    # parent.run inspects base.run; preserve that workflow with a source reader
    # restricted to this one function, without changing any shared module.
    class Inspect:
        @staticmethod
        def getsource(fn):
            if fn is not base.run:raise ValueError('unexpected source adaptation')
            return text.replace(old,new)
    ns=dict(parent.run.__globals__);ns['inspect']=Inspect
    from types import FunctionType
    FunctionType(parent.run.__code__,ns)(root,out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.root.resolve(),a.out.resolve())
