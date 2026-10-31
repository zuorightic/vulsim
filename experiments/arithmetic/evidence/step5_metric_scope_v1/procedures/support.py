from pathlib import Path
import json,os,sys
R=Path.cwd();sys.path.insert(0,str(R))
from experiments.arithmetic_dse.budget import Ledger
from experiments.arithmetic_dse.processes import run_command
B=R/'build/step5-metric-scope-20261031';stem=sys.argv[1];command=sys.argv[2:];assert not (B/(stem+'.command.json')).exists()
ledger=Ledger();res=ledger.reserve(None,120,2,'step5_metric_scope_saved_report_review',command,B/stem,context={'target_platform':'asap7','task_id':stem,'admission_id':'step5-metric-scope-support-v1','model_version':'not_applicable'})
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['OMP_NUM_THREADS']='2'
record=run_command(command,B,stem,120,env,8192,cpu_limit_s=res['CPU_time_s']);ledger.finish(res,record);print((B/(stem+'.log')).read_text());print({'exit_code':record['exit_code'],'walltime_s':record['walltime_s']});raise SystemExit(record['exit_code'])
