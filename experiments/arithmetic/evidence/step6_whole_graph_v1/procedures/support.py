from pathlib import Path
import hashlib,json,os,sys
R=Path.cwd();sys.path.insert(0,str(R))
from experiments.arithmetic_dse.budget import Ledger
from experiments.arithmetic_dse.processes import run_command
B=R/'build/step6-integration-20261031';stem=sys.argv[1];timeout=int(sys.argv[2]);command=sys.argv[3:];assert not (B/(stem+'.command.json')).exists()
files=[p for base in ('rtlzz/src','rtlzz/testv2','experiments/arithmetic_dse','regression') for p in (R/base).rglob('*') if p.is_file() and p.suffix in ('.cpp','.hpp','.h','.py','.json') and '__pycache__' not in p.parts]
(B/(stem+'.sources.json')).write_text(json.dumps({str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n')
ledger=Ledger();reservation=ledger.reserve(None,timeout,2,'step6_integration_validation',command,B/stem,context={'target_platform':'common','admission_id':'step6-software-v1','task_id':stem,'model_version':'not_implemented_step7'})
env=os.environ.copy();env.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1',MAKEFLAGS='-j2')
record=run_command(command,B,stem,timeout,env,8192,cpu_limit_s=reservation['CPU_time_s']);ledger.finish(reservation,record);print({'stem':stem,'exit_code':record['exit_code'],'walltime_s':record['walltime_s']});print((B/(stem+'.log')).read_text()[-4000:]);raise SystemExit(record['exit_code'])
