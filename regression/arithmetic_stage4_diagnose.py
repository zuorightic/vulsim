"""Read-only diagnosis of actual mapped constant/FF output aliases."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read
from experiments.arithmetic_dse.model_context_samples import layout


def diagnose(root):
    for state in (root/'raw').iterdir():
        h=state/'history.json'
        if not h.exists() or not any(r['status']=='failed' for r in read(h)):continue
        for mapped in state.rglob('mapped.json'):
            folder=mapped.parent;design=read(mapped);pins=read(folder/'liberty-pins.json');top=design['modules']['ModelBundle']
            print('SOURCE',state.name,flush=True)
            for child,port in [('launch','value'),('capture','data')]:
                m=design['modules'][top['cells'][child]['type']];drivers={}
                for name,c in m['cells'].items():
                    for p,meta in pins[c['type']]['pins'].items():
                        if meta['direction']=='output':
                            for bit in c['connections'].get(p,[]):drivers[bit]=(name,p,c)
                for i,bit in enumerate(m['ports'][port]['bits']):
                    if isinstance(bit,str):continue
                    seen=set()
                    while bit in drivers and bit not in seen:
                        seen.add(bit);name,p,c=drivers[bit];meta=pins[c['type']]
                        if meta['sequential']:break
                        if not meta['buffer_or_inverter']:
                            print(dict(child=child,bit=i,cell=name,master=c['type'],pins=meta['pins'],connections=c['connections']),flush=True);break
                        inputs=[x for x,v in meta['pins'].items() if v['direction']=='input'];bit=c['connections'][inputs[0]][0]

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();diagnose(a.root)
