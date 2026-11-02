"""Freeze one user-requested 100ns diagnostic, then launch without retries."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, subprocess, sys

R=Path.cwd();sys.path.insert(0,str(R))
from experiments.arithmetic_dse.budget import Ledger,POLICY
from experiments.arithmetic_dse.platforms import profile
from experiments.arithmetic_dse.sdc import VERSION

B=R/'build/step6-relaxed-clock-20261102';A=B/'admission-v5.json'
old=R/'build/step6-review-20261102/physical-complete/asap7-step6-udr_unsigned_128-capacity-complete-v4'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent_path=R/'build/step6-review-20261102/completion-admission-v4.json'
parent=json.loads(parent_path.read_text());m=json.loads((old/'manifest.json').read_text())
t=dict(parent['tasks'][0]);task_id='asap7-step6-udr_unsigned_128-sdc100ns-v5'
t.update(id=task_id,period_ps=100000,abc_target_ps=1500,io_delay_max_ps=300,
         source_run=str(old),source_manifest_sha256=sha(old/'manifest.json'),
         mapped_netlist_file_sha256=sha(old/'results/asap7/arithmetic_probe/base/1_2_yosys.v'),
         constraints_sha256=sha(R/'experiments/arithmetic_dse/backend/constraints.sdc'),sdc_contract_version=VERSION,
         supersedes_task_id=parent['tasks'][0]['id'],
         diagnostic_role='SDC_only_relaxation_from_verified_mapping',
         IO_delay_policy='fixed_absolute_max_300ps_min_0ps; matches original1500ps x0.2',
         data_role='capacity_constraint_diagnostic_only; prohibited_as_training_target_or_C_D_benefit')
live=Ledger().summary();assert live['pending']==0
limits=json.loads(POLICY.read_text())['resources']
assert live['walltime_s']+16500<=limits['max_global_walltime_h']*3600
assert live['CPU_time_s']+33000<=limits['max_tool_CPU_time_h']*3600
assert t['rtl_sha256']==sha(Path(t['rtl']))==sha(old/'input.sv')
assert t['profile_sha256']==profile('asap7')['profile_sha256']
a={'id':'step6-udr-clock100ns-v5','purpose':'arithmetic_clock_relaxation_only',
   'created_at':datetime.now(timezone.utc).isoformat(),'policy_sha256':sha(POLICY),
   'authorization':'user requested relaxed clock rerun; subsequent steering sets100ns, replacing unlaunched200ns proposal',
   'parent_admission':{'path':str(parent_path),'sha256':sha(parent_path),'id':parent['id']},
   'starting_usage_live':live,'tasks':[t],'call_caps':{'synth':1,'grt':1,'final':0},
   'threads':2,'yosys_max_threads':2,'memory_limit_MiB':32768,
   'synthesis_timeout_s':300,'post_synthesis_through_grt_timeout_s':14400,
   'automatic_retries':0,'support_envelope':{'walltime_s':1800,'CPU_time_s':3600},
   'worst_case_walltime_s':16500,'CPU_envelope_s':33000,
   'reuse':'only identity-checked mapped netlist; fresh synthesis ODB/SDC and full floorplan-through-grt',
   'unexecuted_proposal_period_ps':200000,
   'scope':'singleUDR128; no controls/final/new structure/platform; original1500ps outcome and costs retained'}
assert not A.exists() and not (B/'run').exists()
A.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
(B/'usage-at-admission.json').write_bytes(Path('experiments/arithmetic/backend_usage.json').read_bytes())
cmd=[sys.executable,'-m','experiments.arithmetic_dse.backend','--platform','asap7',
     '--admission',str(A),'--admission-id',a['id'],'--task-id',task_id,
     '--rtl',t['rtl'],'--top',t['top'],'--out',str(B/'run'),
     '--period-ps','100000','--abc-target-ps','1500','--io-delay-max-ps','300',
     '--stage','grt','--budget-purpose','physical_recheck','--threads','2',
     '--memory-limit-mib','32768','--synth-timeout-s','300','--route-timeout-s','14400',
     '--resume-synth-from',str(old)]
(B/'launch.json').write_text(json.dumps({'started_at':datetime.now(timezone.utc).isoformat(),
    'admission_sha256':sha(A),'command':cmd},indent=2)+'\n')
print('START',task_id,flush=True)
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
with (B/'driver.log').open('x') as log:code=subprocess.call(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
result=json.loads((B/'run/manifest.json').read_text())
(B/'outcome.json').write_text(json.dumps({'version':'clock100ns-outcome-v1','driver_exit_code':code,
    'admission':str(A),'admission_sha256':sha(A),'manifest':str(B/'run/manifest.json'),
    'status':result['status'],'failure_stage':result.get('failure_stage'),'failure_reason':result.get('failure_reason'),
    'metrics':result['metrics'],'scope':a['scope']},indent=2)+'\n')
print('DONE',result['status'],result.get('failure_reason'),flush=True)
raise SystemExit(code)
