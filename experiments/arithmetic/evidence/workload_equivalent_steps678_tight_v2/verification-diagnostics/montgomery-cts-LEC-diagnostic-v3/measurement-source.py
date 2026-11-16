"""One finite, separately charged diagnostic of an existing CTS netlist pair.

This does not replace the original check or modify its physical process.
Yosys expands the exact Liberty functions and proves all equivalence cells,
including internal cutpoints and register boundaries. A timeout or an
unproved cell remains a failed diagnostic, never a functional pass.
"""
import argparse
import gzip
import os
from pathlib import Path

from .workload_abcd import read,write,sha
from .budget import Ledger
from .processes import run_command


def run(physical_directory,output):
    physical_directory=Path(physical_directory).resolve();output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=False)
    results=physical_directory/'results/asap7/arithmetic_probe/base'
    before=results/'4_before_rsz_lec.v';after=results/'4_after_rsz_lec.v'
    # Use the exact library list already passed to the original checker.
    config=physical_directory/'objects/asap7/arithmetic_probe/base/4_rsz_lec_test.yml'
    lines=config.read_text().splitlines();start=lines.index('liberty_files:')+1
    libraries=[]
    for line in lines[start:]:
        if not line.startswith(' '):break
        libraries.append(Path(line.strip().removeprefix('-').strip()))
    if len(libraries)!=5:raise ValueError('unexpected ASAP7 CTS library list')
    local=[]
    for p in libraries:
        dest=output/p.name.removesuffix('.gz')
        dest.write_bytes(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes());local.append(dest)
    # Some unused ASAP7 clock-gating cells have no supported IQ function.
    # They may be skipped at import; hierarchy -check below still rejects
    # either netlist if it actually instantiates an unavailable cell.
    library_commands=['read_liberty -ignore_miss_func '+str(p) for p in local]
    script=output/'equivalence.ys'
    commands=[]
    for source,name in ((before,'gold'),(after,'gate')):
        commands+=library_commands+['read_verilog '+str(source),'hierarchy -check -top Workload',
            'flatten','proc','opt_clean','rename Workload '+name,'design -stash '+name]
    commands+=['design -reset','design -copy-from gold -as gold gold','design -copy-from gate -as gate gate',
        'equiv_make -inames gold gate equiv','hierarchy -check -top equiv','equiv_struct',
        'equiv_simple -seq 1','equiv_status -assert']
    script.write_text('\n'.join(commands)+'\n')
    binary=Path('/home/zyrv/OpenROAD-flow-scripts/tools/install/yosys/bin/yosys')
    command=[str(binary),'-s',str(script)]
    inputs=[before,after,config,script,binary,Path(__file__)]+libraries+local
    admission=dict(id=output.name,role='verification_diagnostic',source_directory=str(physical_directory),
        files={str(p):sha(p) for p in inputs},command=command,support_calls=1,automatic_retries=0,
        timeout_s=300,memory_limit_MiB=8192,threads=4,application_PPA_for_selection=False,
        original_physical_check_replaced=False,original_physical_result_changed=False)
    write(output/'admission.json',admission)
    ledger=Ledger();context=dict(admission_id=admission['id'],task_id='CTS-netlist-equivalence',
        target_platform='asap7',admission_sha256=sha(output/'admission.json'))
    env=dict(os.environ,OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4')
    with ledger.job({k:context[k] for k in ('admission_id','task_id','target_platform')}):
        for p,h in admission['files'].items():
            if sha(p)!=h:raise ValueError('diagnostic input changed before launch')
        reservation=ledger.reserve(None,300,4,'clock_calibration_verification',command,output/'yosys',context=context)
        record=run_command(command,output,'yosys',300,env,8192,cpu_limit_s=reservation['CPU_time_s'])
        ledger.finish(reservation,record)
        write(output/'command.json',dict(record,budget_reservation_id=reservation['id']))
    log=(output/'yosys.log').read_text(errors='replace')
    passed=record['exit_code']==0 and 'Equivalence successfully proven!' in log
    result=dict(status='passed' if passed else 'not_proven',command=record,
        admission_sha256=sha(output/'admission.json'),log_sha256=sha(output/'yosys.log'),
        original_check_unchanged=True,application_PPA_for_selection=False)
    write(output/'result.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--physical-directory',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(run(a.physical_directory,a.output))
