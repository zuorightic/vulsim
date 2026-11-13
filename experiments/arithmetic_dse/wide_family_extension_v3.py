"""Unconfound control versus capture and extend numerical leaf coverage.

These sources are training factors, never width/candidate price entries.
The original registry and all validation/test roles remain unchanged.
"""
from . import wide_family_extension_v2 as parent,wide_family_sources as shells,wide_arithmetic as arithmetic
from .model_fast_preflight import key

VERSION='wide-family-factor-sources-v3-load-and-rectangular-controls'


def supplemental_sources():
    s=arithmetic.spec
    definitions=[shells.local(s('adc',128,128,128,status='carry',control='one'),banks=1),
                 shells.local(s('add',128,96,129),banks=2),
                 shells.local(s('add',8,8,8),consumer_width=64,shift=29),
                 shells.local(s('mul',32,64,96))]
    banned={r['source_group'] for r in parent.sources()+parent.qualification_sources()};result=[]
    for q in definitions:
        h=key(q)
        if h in banned:raise ValueError('supplemental role collision')
        result.append(dict(id='wide-'+h[:16],source_group=h,role='train',family='operator',features=q))
    return result


def sources():return parent.sources()+supplemental_sources()
