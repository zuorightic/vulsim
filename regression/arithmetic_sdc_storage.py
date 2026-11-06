"""Actual SDC storage replay and strict constraint-corruption refusals."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse import sdc
from experiments.arithmetic_dse import sdc_storage_v3 as successor
from experiments.arithmetic_dse.model_collection import sha,write
from experiments.arithmetic_dse.platforms import profile


def run(out,parent):
    out.mkdir(parents=True,exist_ok=False);p=profile('asap7');rows=[];refusals=[]
    for directory in sorted((parent/'runs').iterdir()):
        m=json.loads((directory/'manifest.json').read_text());path=directory/'results/asap7/arithmetic_probe/base/1_synth.sdc'
        text=path.read_text();ports=sdc.rtl_ports((directory/'input.sv').read_text(),'ModelBundle')
        value=successor.verify_sdc(text,p,m['period_ps'],ports)
        rows.append({'id':directory.name,'sdc_sha256':sha(path),'maximum_IO_storage_error_ps':value['maximum_IO_storage_error_ps']})
        if m['period_ps']==14897:
            try:sdc.verify_sdc(text,p,m['period_ps'],ports)
            except sdc.SdcContractError:pass
            else:raise ValueError('original strict decimal-only mismatch not reproduced')
            mutations={'beyond-exact-storage':'2979.4011','positive-delay-to-zero':'0.0000','nonfinite-IO':'nan'}
            for name,replacement in mutations.items():
                corrupted=text.replace('set_input_delay 2979.4001','set_input_delay '+replacement)
                if corrupted==text:raise ValueError('actual IO corruption point absent')
                try:successor.verify_sdc(corrupted,p,m['period_ps'],ports)
                except ValueError:refusals.append(directory.name+'/'+name)
                else:raise ValueError('changed IO constraint accepted: '+name)
            for name,corrupted in [('clock-period-changed',text.replace('14897.0000','14896.0000')),
                ('uncertainty-changed',text.replace('-setup 20.0000','-setup 19.0000')),
                ('timing-exception',text+'set_false_path -from [get_ports iv]\n'),
                ('command-injection',text+'set_load 1; puts bad\n')]:
                try:successor.verify_sdc(corrupted,p,m['period_ps'],ports)
                except ValueError:refusals.append(directory.name+'/'+name)
                else:raise ValueError('changed non-IO constraint accepted: '+name)
    if len(rows)!=4 or len(refusals)!=14:raise ValueError('complete actual storage/negative replay missing')
    result={'status':'passed','producer_sha256':sha(Path(successor.__file__)),'actual_SDCs':rows,
        'negative_refusals':refusals,'exact_binary32_second_IO_storage_only':True,
        'clock_transition_uncertainty_driver_load_and_syntax_rules_unchanged':True,'PPA_calls':0}
    write(out/'proof.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--parent',type=Path,required=True);args=parser.parse_args();run(args.out.resolve(),args.parent.resolve())
