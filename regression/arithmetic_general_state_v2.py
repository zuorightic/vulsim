"""Versioned retained-state software preflight; original failures unchanged."""
import argparse
import inspect
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from regression import arithmetic_general_state as parent
from experiments.arithmetic_dse import model_general_state_samples_v2 as samples
from experiments.arithmetic_dse.model_collection import sha,write

CONFIG=ROOT/'experiments/arithmetic_dse/configs/model_asap7_general_state_v2.json'


def worker(out):
    text=inspect.getsource(parent.worker)
    old='''parity=0
            for j,w in enumerate(s['words']):
                value=new[f'external.data_{j}'] if j in s['external_words'] else new[f'native.data_{j}_s{w["end"]}']
                parity^=value.bit_count()%2'''
    if text.count(old)!=1:raise ValueError('unsupported retained observation preflight point')
    text=text.replace(old,'parity=sum(value.bit_count() for value in new.values())%2')
    namespace=dict(parent.worker.__globals__);namespace.update(CONFIG=CONFIG,source=samples.source,
        specifications=samples.specifications,features=samples.features,step=samples.step,__file__=__file__)
    exec(compile(text,str(Path(__file__).resolve())+'::retained_preflight','exec'),namespace)
    namespace['worker'](out)
    proof=json.loads((out/'proof.json').read_text());proof['version']='general-state-software-preflight-v2-retained'
    proof['all_semantic_state_outputs_explicitly_observed']=True
    for name in ('experiments/arithmetic_dse/model_general_state_samples_v2.py','regression/arithmetic_general_state.py'):
        proof['producer_sha256'][name]=sha(ROOT/name)
    write(out/'proof.json',proof)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();worker(args.out.resolve())
