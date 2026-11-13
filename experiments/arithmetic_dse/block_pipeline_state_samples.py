"""Parameterized state banks for the common block-pipeline extension.

Reuses the retained-state source, reset and cycle semantics. Parameters describe
word geometry, lifetimes and control, independently of any arithmetic workload.
Generating a bank grants neither physical preservation nor S/shared prices.
"""
from . import model_general_state_samples as base
from . import model_general_state_samples_v2 as retained

VERSION='block-pipeline-retained-state-banks-v1'
source=retained.source
step=retained.step
features=retained.features


def specification(word_widths, *, depth=2, lifetimes=None, root_widths=(63,65),
                  external_words=None, service_mode=0, reset_seed=0):
    if depth not in (1,2) or service_mode not in (0,1,2):
        raise ValueError('first common state domain has depth 1..2 and three service modes')
    if not 1<=len(word_widths)<=96 or any(type(w) is not int or not 1<=w<=96 for w in word_widths):
        raise ValueError('one to 96 words of one to 96 bits required')
    if not 2<=len(root_widths)<=4 or any(type(w) is not int or not 1<=w<=96 for w in root_widths) or sum(root_widths)>130:
        raise ValueError('two to four roots and at most 130 input data bits required')
    if lifetimes is None:lifetimes=[(1,depth)]*len(word_widths)
    if len(lifetimes)!=len(word_widths) or any(not 1<=a<=b<=depth for a,b in lifetimes):
        raise ValueError('explicit legal lifetime per word required')
    if external_words is None:
        terminal=[i for i,(_,end) in enumerate(lifetimes) if end==depth]
        if not terminal:raise ValueError('at least one word must reach the final native stage')
        external_words=terminal[:1]
    if not external_words or len(set(external_words))!=len(external_words):
        raise ValueError('distinct external capture words required')
    if any(type(i) is not int or not 0<=i<len(word_widths) or lifetimes[i][1]!=depth for i in external_words):
        raise ValueError('external words must survive through the final native stage')
    if sum(word_widths[i] for i in external_words)>256:
        raise ValueError('external data exceeds the first common domain')
    roots=[dict(width=w,reset=base.bits(f'block-state/{reset_seed}/root/{i}',w)) for i,w in enumerate(root_widths)]
    n=sum(root_widths);pairs=[(a,b) for b in range(1,n) for a in range(b)]
    if sum(word_widths)>len(pairs):raise ValueError('insufficient distinct two-input functions for retained words')
    packed=sum(r['reset']<<sum(x['width'] for x in roots[:i]) for i,r in enumerate(roots));cursor=0;words=[]
    for i,(width,(start,end)) in enumerate(zip(word_widths,lifetimes,strict=True)):
        selected=pairs[cursor:cursor+width];cursor+=width
        reset=base.bits(f'block-state/{reset_seed}/word/{i}',width)
        initial=sum((((packed>>a)^(packed>>b))&1)<<j for j,(a,b) in enumerate(selected))
        words.append(dict(declared_width=width,variable_mask=(1<<width)-1,variable_bits=width,
                          source_positions=[a for a,b in selected],source_positions_second=[b for a,b in selected],
                          invert=initial^reset,reset=reset,start=start,end=end))
    slots=[dict(name=f'data_{i}_s{stage}',word=i,stage=stage,variable_bits=w['variable_bits'],reset=w['reset'])
           for i,w in enumerate(words) for stage in range(w['start'],w['end']+1)]
    if sum(x['variable_bits'] for x in slots)>4096:
        raise ValueError('native data exceeds the first common domain')
    s=dict(roots=roots,service_mode=service_mode,depth=depth,words=words,external_words=list(external_words),slots=slots)
    s['expected_FF_bits']=dict(input_service=n+1,native_state=sum(x['variable_bits'] for x in slots)+depth,
                               external_state=sum(word_widths[i] for i in external_words)+1)
    s['features']=features(s,1500);s['semantic_signature']=base.semantic_signature(s)
    s.update(id='bank-'+s['semantic_signature'][:16],split='not_training',generator=VERSION,
             physical_preservation_qualified=False,price_qualification=False)
    return s
