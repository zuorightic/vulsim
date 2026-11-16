"""Finite ledger-accounted launch of the conservative mapped repair proof."""
import argparse
import os
from pathlib import Path
import shutil
import sys

from .workload_abcd import read,write,sha
from .budget import Ledger
from .processes import run_command


def run(physical_directory,output):
    physical_directory=Path(physical_directory).resolve();output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=False)
    config=physical_directory/'objects/asap7/arithmetic_probe/base/4_rsz_lec_test.yml'
    text=config.read_text().splitlines();start=text.index('liberty_files:')+1;libraries=[]
    for line in text[start:]:
        if not line.startswith(' '):break
        libraries.append(Path(line.strip().removeprefix('-').strip()))
    folder=physical_directory/'results/asap7/arithmetic_probe/base'
    before,after=folder/'4_before_rsz_lec.v',folder/'4_after_rsz_lec.v'
    source=Path(__file__).with_name('workload_buffer_equivalence.py')
    command=[sys.executable,str(source),'--before',str(before),'--after',str(after),
             '--liberty',*map(str,libraries),'--output',str(output/'proof.json')]
    files=[before,after,config,source,Path(__file__)]+libraries
    a=dict(id=output.name,role='verification_diagnostic',support_calls=1,automatic_retries=0,
        files={str(p):sha(p) for p in files},command=command,timeout_s=300,memory_limit_MiB=8192,threads=4,
        original_physical_check_replaced=False,application_PPA_for_selection=False)
    write(output/'admission.json',a)
    for p in (source,Path(__file__)):shutil.copyfile(p,output/p.name)
    ledger=Ledger();context=dict(target_platform='asap7',admission_id=a['id'],task_id='CTS-netlist-structural-proof')
    with ledger.job(context):
        if any(sha(p)!=h for p,h in a['files'].items()):raise ValueError('proof input changed')
        reservation=ledger.reserve(None,300,4,'clock_calibration_verification',command,output/'proof',
            context=dict(context,admission_sha256=sha(output/'admission.json')))
        record=run_command(command,output,'proof',300,dict(os.environ,OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4'),
            8192,cpu_limit_s=reservation['CPU_time_s'])
        ledger.finish(reservation,record);write(output/'command.json',dict(record,budget_reservation_id=reservation['id']))
    result=dict(status='proven' if record['exit_code']==0 else 'not_proven',command=record,
        proof=read(output/'proof.json') if (output/'proof.json').exists() else None,
        original_check_unchanged=True,application_PPA_for_selection=False,admission_sha256=sha(output/'admission.json'))
    write(output/'result.json',result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--physical-directory',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(run(a.physical_directory,a.output))
