"""Exact alias qualification with generic declaration-width reset negative."""
import argparse
import inspect
from pathlib import Path
from . import stage67_alias_qualify_v1 as parent
from .stage67_mapped_state_v1 import flatten


def run(root,out):
    text=inspect.getsource(parent.run)
    replacements={
        'dict(modules={n:models[n] for n in pins})':"dict(modules={n:models[n] for n in {c['type'] for c in flatten(design,pins)[0].values()} if pins[n]['sequential']})",
        'old=missing+" <= 41\'h0";new=missing+" <= 41\'h200"':"slot=next(s for s in contract['state_slots'] if s['name']==missing);width=slot['declared_width'];bit=state['pure_bit_alias_proof'][0]['bits'][0]['bit'];old=missing+\" <= \"+str(width)+\"'h0\";new=missing+\" <= \"+str(width)+\"'h\"+format(1<<bit,'x')"
    }
    for old,new in replacements.items():
        if text.count(old)!=1:raise ValueError('alias qualification callsite drift '+old)
        text=text.replace(old,new)
    ns=dict(parent.run.__globals__);ns['flatten']=flatten;exec(compile(text,__file__,'exec'),ns);ns['run'](root,out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.root.resolve(),a.out.resolve())
