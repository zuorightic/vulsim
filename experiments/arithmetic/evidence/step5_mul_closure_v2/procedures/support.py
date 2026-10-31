from pathlib import Path
import hashlib,json,os,sys
ROOT=Path.cwd();sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.budget import Ledger
from experiments.arithmetic_dse.processes import run_command
out=ROOT/'build/step5-closure-20261031';stem=sys.argv[1];timeout=int(sys.argv[2]);command=sys.argv[3:]
assert not (out/(stem+'.command.json')).exists(),'new task ID required'
files=list((ROOT/'rtlzz/src').rglob('*.cpp'))+list((ROOT/'rtlzz/src').rglob('*.hpp'))+list((ROOT/'rtlzz/src').rglob('*.h'))
files += [ROOT/'rtlzz/main/main.cpp',*list((ROOT/'rtlzz/testv2').glob('*.cpp'))]
identity={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(out/(stem+'.sources.json')).write_text(json.dumps(identity,indent=2)+'\n')
ledger=Ledger();reservation=ledger.reserve(None,timeout,2,'step5_closure_review',command,out/stem,context={'target_platform':'common','admission_id':'step5-closure-software-v1','task_id':stem,'model_version':'not_applicable'})
env=os.environ.copy();env['OMP_NUM_THREADS']='2';env['OPENBLAS_NUM_THREADS']='2';env['PYTHONDONTWRITEBYTECODE']='1'
record=run_command(command,out,stem,timeout,env,8192,cpu_limit_s=reservation['CPU_time_s']);ledger.finish(reservation,record)
print({'stem':stem,'exit_code':record['exit_code'],'walltime_s':record['walltime_s']});print((out/(stem+'.log')).read_text()[-3000:]);raise SystemExit(record['exit_code'])
