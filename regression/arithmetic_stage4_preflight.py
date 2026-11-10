"""Read-only mapped-constant recovery and source-freeze contract checks."""
import argparse
from copy import deepcopy
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write
from experiments.arithmetic_dse.model_mapped_contract import mapped_contract


def verify(root,out):
    out.mkdir(parents=True,exist_ok=False);cfg=read(root/read(root/'active-collection.json')['path']);sources={r['id']:r for r in read(root/'corpus/manifest.json')['sources']};rows=[];negative=[]
    for source,ref in cfg['inherit_synth_by_source'].items():
        p=Path(ref['directory']);design=read(p/'mapped.json');pins=read(p/'liberty-pins.json');f=sources[source]['features']
        result=mapped_contract(design,f,pins);rows.append(dict(source=source,independent_banks=result['independent_banks']))
        broken=deepcopy(pins)
        for cell in broken.values():
            if cell['pins'] and not any(m['direction']=='input' for m in cell['pins'].values()):
                for meta in cell['pins'].values():
                    if meta.get('function')=='0':meta['function']='1'
        try:mapped_contract(design,f,broken)
        except ValueError:negative.append(source+'/wrong_Liberty_constant')
        else:raise ValueError('incorrect actual constant accepted')
    if len(rows)!=4 or len(negative)!=4:raise ValueError('four exact mapped constant recoveries required')
    write(out/'proof.json',dict(status='passed',real_mapped_sources=rows,wrong_constant_controls_rejected=negative,new_EDA_calls=0,synthesis_repeated=False))
    print(read(out/'proof.json'),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();verify(a.root,a.out)
