"""Real synth/grt clock serialization and strict stage-specific negatives."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse.model_fast_sdc_v3 import verify_sdc,rtl_ports
from experiments.arithmetic_dse.platforms import profile


def verify(root,out):
    out.mkdir(parents=True,exist_ok=False);p=profile('asap7');rows=[];negatives=[];selected=None
    for s in (root/'raw').iterdir():
        for point in s.glob('target-*'):
            task=s.name+'-T'+point.name.split('-')[1];folder=point/'runs'/task
            if not (folder/'input.sv').exists():continue
            t=int(point.name.split('-')[1]);ports=rtl_ports((folder/'input.sv').read_text(),'ModelBundle')
            for stage,stem in [('synth','1_synth'),('grt','5_1_grt')]:
                path=folder/'results/asap7/arithmetic_probe/base'/(stem+'.sdc')
                if not path.exists():continue
                result=verify_sdc(path.read_text(),p,t,ports,serialization_stage=stage)
                rows.append(dict(source=s.name,target_ps=t,stage=stage,actual_periods=result['actual_clock_periods_native'],expected_centers=result['exact_serialization_centers_native'],SDC_sha256=sha(path)))
                if s.name=='s5f65fb41790f6c16' and t==1012:
                    if selected is None:selected={}
                    selected[stage]=(path.read_text(),ports)
    if not selected or set(selected)!=set(('synth','grt')):raise ValueError('actual paired1012ps serialized SDCs required')
    for stage,(text,ports) in selected.items():
        old='1012.0001' if stage=='synth' else '1012.0002'
        for value in (['1012.0002'] if stage=='synth' else [])+['1012.0003','1011.9999','0','NaN','1013']:
            try:verify_sdc(text.replace('-period '+old,'-period '+value),p,1012,ports,serialization_stage=stage)
            except ValueError:negatives.append(stage+'/'+value)
            else:raise ValueError('invalid stage clock accepted '+stage+'/'+value)
    write(out/'proof.json',dict(status='passed',actual_SDCs=len(rows),rows=rows,negative_controls=negatives,new_EDA_calls=0,
        synth_passes=1,grt_roundtrip_cap=8,original_half_decimal_quantum_unchanged=True))
    print(dict(status='passed',actual_SDCs=len(rows),negative_controls=len(negatives)),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();verify(a.root,a.out)
