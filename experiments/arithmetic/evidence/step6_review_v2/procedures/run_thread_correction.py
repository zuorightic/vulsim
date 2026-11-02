from pathlib import Path
import json,subprocess,sys
R=Path.cwd();B=R/'build/step6-review-20261102';A=B/'thread-admission-v3.json';a=json.loads(A.read_text());out=B/'physical-threads';out.mkdir(exist_ok=False);rows=[];ok={}
for t in a['tasks']:
 if t['stage']=='synth' and not ok.get(t['kernel'],False):
  rows.append({'task_id':t['id'],'status':'not_run','physical_calls':0,'reason':'baseline did not complete in admitted resource envelope; controls paused'});continue
 cmd=[sys.executable,'-m','experiments.arithmetic_dse.backend','--platform','asap7','--admission',str(A),'--admission-id',a['id'],'--task-id',t['id'],'--rtl',t['rtl'],'--top',t['top'],'--out',str(out/t['id']),'--period-ps',str(t['period_ps']),'--abc-target-ps',str(t['abc_target_ps']),'--stage',t['stage'],'--budget-purpose','physical_recheck','--memory-limit-mib','32768','--synth-timeout-s','1800','--route-timeout-s','3600']
 print('RUN',t['id'],flush=True)
 with (out/(t['id']+'.driver.log')).open('w') as log:code=subprocess.call(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT)
 path=out/t['id']/'manifest.json';assert path.exists(),t['id'];m=json.loads(path.read_text());rows.append({'task_id':t['id'],'status':m['status'],'driver_exit_code':code,'failure_code':m.get('failure_code'),'failure_stage':m.get('failure_stage'),'failure_reason':m.get('failure_reason'),'metrics':m['metrics'],'manifest':str(path)})
 if t['stage']=='grt':ok[t['kernel']]=m['status']=='completed'
 (B/'physical-outcome-v3.json').write_text(json.dumps({'version':'step6-capacity-outcome-v2','admission':str(A),'runs':rows,'scope':'independent bounded rechecks; preserved original failures; no training/main matrix'},indent=2)+'\n');print('DONE',t['id'],m['status'],m.get('failure_code'),flush=True)
(B/'physical-outcome-v3.json').write_text(json.dumps({'version':'step6-capacity-outcome-v2','admission':str(A),'runs':rows,'scope':'independent bounded rechecks; preserved original failures; no training/main matrix'},indent=2)+'\n')
