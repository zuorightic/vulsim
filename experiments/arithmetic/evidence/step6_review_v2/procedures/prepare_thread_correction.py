from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
R=Path.cwd();sys.path.insert(0,str(R));B=R/'build/step6-review-20261102'
from experiments.arithmetic_dse.budget import POLICY,usage
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();parent=B/'capacity-admission-v2.json';a=json.loads(parent.read_text());tasks=[]
for t in a['tasks']:
 if t['kernel']!='udr_unsigned_128':continue
 t=dict(t);t['supersedes_task_id']=t['id'];t['id']=t['id'].replace('recheck-v2','threads-v3');tasks.append(t)
new=dict(a,id='step6-udr-thread-correction-v3',created_at=datetime.now(timezone.utc).isoformat(),tasks=tasks,parent_admission={'path':str(parent),'sha256':sha(parent),'id':a['id']},call_caps={'synth':3,'grt':1,'final':0},correction_kind='yosys_thread_limit',yosys_max_threads=2,synthesis_timeout_s=1800,automatic_retries=0,scope='one explicit correction after diagnosed Yosys thread-pool enforcement defect; UDR only; no new F2/original/final/main-matrix tasks',synth_CPU_limit_s=3600,post_synthesis_CPU_limit_s=7200)
new['starting_usage_live']=usage(json.loads((R/'experiments/arithmetic/backend_usage.json').read_text())['entries']);u=new['starting_usage_live'];assert not u['pending']
new['worst_case_walltime_s']=3*1800+3600+2400;new['CPU_envelope_s']=2*new['worst_case_walltime_s'];p=json.loads(POLICY.read_text())['resources'];assert u['walltime_s']+new['worst_case_walltime_s']<=p['max_global_walltime_h']*3600 and u['CPU_time_s']+new['CPU_envelope_s']<=p['max_tool_CPU_time_h']*3600
new['authorization_note']='existing user request to complete deferred tasks; diagnosed resource-control defect, separately admitted correction, preserved CPU-limited v2 and all fees; 32GiB/2 worker-thread cap, 1800s synth, 3600s post-synth->grt; no automatic further retry'
path=B/'thread-admission-v3.json';assert not path.exists();path.write_text(json.dumps(new,indent=2)+'\n');print(json.dumps({'ready':True,'tasks':3,'envelope_walltime_s':new['worst_case_walltime_s'],'starting_usage':u},indent=2))
