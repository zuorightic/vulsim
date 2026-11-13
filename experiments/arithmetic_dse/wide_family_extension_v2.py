"""Pending source successor from the pre-label factor audit, not prices."""
from . import wide_family_sources as parent,wide_arithmetic as arithmetic
from .model_fast_preflight import key

VERSION='wide-family-factor-sources-v2-high-result-training'


def sources():
    rows=parent.sources()
    # The v1 roster has no high-result train geometry. Add a non-power-of-two
    # width before training rather than pretending a qualification source
    # supplies fitting evidence, or relabeling validation/test as train.
    f=parent.local(arithmetic.spec('mul',96,96,192,lo=96,bits=96));h=key(f)
    if h in {r['source_group'] for r in rows+parent.qualification_sources()}:raise ValueError('successor role collision')
    rows.append(dict(id='wide-'+h[:16],role='train',source_group=h,features=f))
    return rows


qualification_sources=parent.qualification_sources
