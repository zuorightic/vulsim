from pathlib import Path
import hashlib,json,subprocess,sys
R=Path.cwd();B=R/'build/step6-integration-20261031';A=B/'capacity-admission.json';admission=json.loads(A.read_text());summary=[];out=B/'physical';out.mkdir(exist_ok=False);completed={}
for task in admission['tasks']:
 if task['stage']=='synth' and not completed.get(task['kernel'],False):
  summary.append({'task_id':task['id'],'status':'not_run','reason':'baseline capacity task did not complete; dependent sensitivity domain paused','physical_calls':0});continue
 directory=out/task['id'];cmd=[sys.executable,'-m','experiments.arithmetic_dse.backend','--platform','asap7','--admission',str(A),'--admission-id',admission['id'],'--task-id',task['id'],'--rtl',task['rtl'],'--top',task['top'],'--out',str(directory),'--period-ps',str(task['period_ps']),'--abc-target-ps',str(task['abc_target_ps']),'--stage',task['stage'],'--budget-purpose','physical_recheck']
 print('RUN',task['id'],flush=True)
 with (out/(task['id']+'.driver.log')).open('w') as log:code=subprocess.call(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT)
 if not (directory/'manifest.json').exists():raise RuntimeError('backend produced no manifest '+task['id'])
 manifest=json.loads((directory/'manifest.json').read_text());result={'task_id':task['id'],'status':manifest['status'],'failure_code':manifest.get('failure_code'),'failure_stage':manifest.get('failure_stage'),'failure_reason':manifest.get('failure_reason'),'manifest':str(directory/'manifest.json'),'driver_exit_code':code,'metrics':manifest['metrics']};summary.append(result)
 if task['stage']=='grt':completed[task['kernel']]=manifest['status']=='completed'
 (B/'physical-summary.json').write_text(json.dumps({'version':'step6-bounded-physical-v1','runs':summary,'scope':'actual independent capacity/axis diagnostic; not training or main matrix; no automatic retry'},indent=2)+'\n');print(task['id'],manifest['status'],manifest.get('failure_code'),flush=True)
print('DONE finite physical list',flush=True)
