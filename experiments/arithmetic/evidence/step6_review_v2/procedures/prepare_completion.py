from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,shutil
R=Path.cwd();sys.path.insert(0,str(R));B=R/'build/step6-review-20261102'
from experiments.arithmetic_dse.budget import POLICY,usage
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();parent=B/'thread-admission-v3.json';a=json.loads(parent.read_text());tasks=[]
for t in a['tasks']:
 t=dict(t);t['supersedes_task_id']=t['id'];t['id']=t['id'].replace('threads-v3','complete-v4');tasks.append(t)
s=json.loads((R/'experiments/arithmetic/backend_usage.json').read_text());u=usage(s['entries']);assert not u['pending']
a.update(id='step6-udr-completion-v4',created_at=datetime.now(timezone.utc).isoformat(),parent_admission={'path':str(parent),'sha256':sha(parent),'id':a['id']},tasks=tasks,execution_mode='complete_initial_backend',synthesis_timeout_s=7200,post_synthesis_through_grt_timeout_s=14400,synth_CPU_limit_s=14400,post_synthesis_CPU_limit_s=28800,starting_usage_live=u,worst_case_walltime_s=3*7200+14400+2400,CPU_envelope_s=2*(3*7200+14400+2400),scope='User explicitly prioritizes finishing initial backend over capacity-probe cutoff; complete only the three remaining corrected UDR tasks, same circuit/L/II/platform/clock, no F2 repeat/original/final/matrix; preserve lower-envelope trials and all charges')
a['authorization_note']='2026-11-02 user: 先跑完后端; 初版实验不宜终止; 资源上限可能不够. Versioned completion envelope: 32GiB, Yosys pool 2, 2h synth and 4h full post-synth->grt, same shared v5 total; checkpoint before ABC preserves expensive lowering without changing synthesis passes.'
a['automatic_retries']=0;a['planning_note']='If current completion envelope proves insufficient, review actual progress and remaining global funding under this user authorization; do not call the initial backend experiment complete from a timeout alone.'
p=json.loads(POLICY.read_text())['resources'];assert u['synth']+3<=p['max_synthesis_calls'] and u['grt']+1<=p['max_global_route_calls'];assert u['walltime_s']+a['worst_case_walltime_s']<=p['max_global_walltime_h']*3600 and u['CPU_time_s']+a['CPU_envelope_s']<=p['max_tool_CPU_time_h']*3600
path=B/'completion-admission-v4.json';assert not path.exists();path.write_text(json.dumps(a,indent=2)+'\n');print(json.dumps({'ready':True,'starting_usage':u,'memory_limit_MiB':32768,'synth_limit_s':7200,'complete_post_synth_grt_limit_s':14400,'launch_walltime_envelope_s':a['worst_case_walltime_s'],'launch_CPU_envelope_s':a['CPU_envelope_s'],'free_disk_GiB':shutil.disk_usage(B).free/2**30},indent=2))
