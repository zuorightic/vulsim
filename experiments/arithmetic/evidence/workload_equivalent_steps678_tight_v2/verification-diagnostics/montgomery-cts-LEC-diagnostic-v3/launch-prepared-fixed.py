import os
from pathlib import Path
from experiments.arithmetic_dse.workload_abcd import read,write,sha
from experiments.arithmetic_dse.budget import Ledger
from experiments.arithmetic_dse.processes import run_command

out=Path(__file__).resolve().parent
a=read(out/'admission.json')
if (out/'command.json').exists():raise ValueError('already attempted; no automatic retry')
for p,h in a['files'].items():
    if sha(p)!=h:raise ValueError('frozen diagnostic input changed')
ledger=Ledger()
if any(e.get('admission_id')==a['id'] for e in read(ledger.path)['entries']):
    raise ValueError('diagnostic leaf already reserved')
ctx=dict(admission_id=a['id'],task_id='CTS-netlist-equivalence',target_platform='asap7')
with ledger.job(ctx):
    context=dict(ctx,admission_sha256=sha(out/'admission.json'))
    reservation=ledger.reserve(None,300,4,'clock_calibration_verification',a['command'],out/'yosys',context=context)
    record=run_command(a['command'],out,'yosys',300,dict(os.environ,OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4'),8192,cpu_limit_s=reservation['CPU_time_s'])
    ledger.finish(reservation,record)
    write(out/'command.json',dict(record,budget_reservation_id=reservation['id']))
log=(out/'yosys.log').read_text(errors='replace')
passed=record['exit_code']==0 and 'Equivalence successfully proven!' in log
result=dict(status='passed' if passed else 'not_proven',command=record,admission_sha256=sha(out/'admission.json'),log_sha256=sha(out/'yosys.log'),original_check_unchanged=True,application_PPA_for_selection=False,launcher_sha256=sha(__file__))
write(out/'result.json',result)
print(result)
