"""Retain every state output and use distinct correlated two-input XOR bits."""
import re
from . import model_general_state_samples as base

features=base.features
VERSION='general-state-bank-contract-v2-retained-observation'


def specifications(cfg):
    result=base.specifications(cfg)
    for index,s in enumerate(result):
        count=sum(r['width'] for r in s['roots']);pairs=[(a,b) for b in range(1,count) for a in range(b)]
        packed=sum(r['reset']<<sum(x['width'] for x in s['roots'][:j]) for j,r in enumerate(s['roots']))
        cursor=(index*137)%len(pairs)
        for w in s['words']:
            selected=[pairs[(cursor+k)%len(pairs)] for k in range(w['variable_bits'])];cursor+=w['variable_bits']
            w['source_positions']=[a for a,b in selected];w['source_positions_second']=[b for a,b in selected]
            reset=sum((((packed>>a)^(packed>>b))&1)<<k for k,(a,b) in enumerate(selected))
            w['invert']=reset^w['reset']
        s['semantic_signature']=base.semantic_signature(s)
    if len({s['semantic_signature'] for s in result})!=len(result):raise ValueError('duplicate retained source semantics')
    return result


def source(s):
    text=base.source(s).replace('output reg ','(* keep *) output reg ')
    for j,w in enumerate(s['words']):
        first=','.join(f'roots[{at}]' for at in reversed(w['source_positions']))
        second=','.join(f'roots[{at}]' for at in reversed(w['source_positions_second']))
        old=f'assign word{j}={{{first}}}^{w["variable_bits"]}\'h{w["invert"]:x};'
        new=f'assign word{j}=({{{first}}}^{{{second}}})^{w["variable_bits"]}\'h{w["invert"]:x};'
        if text.count(old)!=1:raise ValueError('unsupported adapter retention rewrite')
        text=text.replace(old,new)
    observed=['root'+str(j) for j in range(len(s['roots']))]+['launch_valid']
    observed += ['native_'+x['name'] for x in s['slots']]
    observed += [f'native_valid_{k}' for k in range(1,s['depth']+1)]
    observed += [f'external_data_{j}' for j in s['external_words']]+['ov']
    width=sum(s['expected_FF_bits'].values())
    pattern=r'GeneralObserver observer\(\.value\(\{[^\n]+\}\),\.y\(y\)\);'
    if len(re.findall(pattern,text))!=1:raise ValueError('unsupported observer retention point')
    text=re.sub(pattern,'GeneralObserver observer(.value({'+','.join(observed)+'}),.y(y));',text)
    pattern=r'module GeneralObserver\(input wire \[\d+:0\] value,output wire y\);'
    if len(re.findall(pattern,text))!=1:raise ValueError('unsupported observer declaration')
    return re.sub(pattern,f'module GeneralObserver(input wire [{width-1}:0] value,output wire y);',text)


def step(s,old,inputs,reset):
    result=base.step(s,old,inputs,reset)
    packed=sum(old[f'launch.data_{j}']<<sum(r['width'] for r in s['roots'][:j]) for j in range(len(s['roots'])))
    for x in s['slots']:
        w=s['words'][x['word']]
        if x['stage']!=w['start']:continue
        enable=old['launch.valid'] if x['stage']==1 else old[f'native.valid_{x["stage"]-1}']
        if not reset and enable:
            value=sum((((packed>>a)^(packed>>b))&1)<<k for k,(a,b) in enumerate(zip(w['source_positions'],w['source_positions_second'])))^w['invert']
            result['native.'+x['name']]=value
    return result
