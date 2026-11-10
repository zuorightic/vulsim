"""Actual serialized clock period and exact-error rejection, no new EDA."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write
from experiments.arithmetic_dse.model_fast_sdc_v2 import verify_sdc,rtl_ports
from experiments.arithmetic_dse.platforms import profile


def verify(folder,out):
    out.mkdir(parents=True,exist_ok=False);text=(folder/'results/asap7/arithmetic_probe/base/1_synth.sdc').read_text();ports=rtl_ports((folder/'input.sv').read_text(),'ModelBundle');p=profile('asap7')
    result=verify_sdc(text,p,1012,ports);rejected=[]
    for value in ('1012.0002','1011.9999','0','NaN','1013'):
        broken=text.replace('-period 1012.0001','-period '+value)
        try:verify_sdc(broken,p,1012,ports)
        except ValueError:rejected.append(value)
        else:raise ValueError('invalid serialized period accepted '+value)
    for old,new in [('set_clock_uncertainty -setup 20.0000','set_clock_uncertainty -setup 19.0000'),('set_input_delay 202.4000','set_input_delay 202.0000')]:
        try:verify_sdc(text.replace(old,new),p,1012,ports)
        except ValueError:rejected.append(new)
        else:raise ValueError('unrelated timing change accepted')
    write(out/'proof.json',dict(status='passed',actual=result,negative_controls=rejected,new_EDA_calls=0))
    print(read(out/'proof.json'),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();verify(a.folder,a.out)
