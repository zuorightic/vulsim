from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
R=Path.cwd();sys.path.insert(0,str(R));B=R/'build/step6-review-20261102'
from experiments.arithmetic_dse.budget import POLICY,usage
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent=R/'experiments/arithmetic/evidence/step6_capacity_v1/admission.json';old=json.loads(parent.read_text());live=json.loads((R/'experiments/arithmetic/backend_usage.json').read_text());u=usage(live['entries']);assert not u['pending'];tasks=[]
for t in old['tasks']:
 t=dict(t);previous=t['id'];t['id']=previous.removesuffix('-v1')+'-recheck-v2';t['supersedes_task_id']=previous
 assert sha(Path(t['rtl']))==t['rtl_sha256']
 name='UDR_128_C' if t['kernel']=='udr_unsigned_128' else 'F2_C'
 assert (B/'generated'/(name+'.json')).read_bytes()==Path(t['compiler_report']).read_bytes()
 t['current_compiler_report_sha256']=sha(B/'generated'/(name+'.json'));t['current_compiler_source_sha256']=sha(R/'rtlzz/src/backend/arithmetic_core.cpp')
 tasks.append(t)
p=json.loads(POLICY.read_text())['resources'];wall=6*900+2*3600+2400;cpu=wall*2
assert u['synth']+6<=p['max_synthesis_calls'] and u['grt']+2<=p['max_global_route_calls'];assert u['walltime_s']+wall<=p['max_global_walltime_h']*3600 and u['CPU_time_s']+cpu<=p['max_tool_CPU_time_h']*3600
mem={k:int(v.split()[0]) for k,v in [line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines()]};assert mem['MemAvailable']>=40*1024*1024
ad={'id':'step6-capacity-correction-v2','purpose':'arithmetic_capacity_recheck_only','created_at':datetime.now(timezone.utc).isoformat(),'policy_sha256':sha(POLICY),'parent_admission':{'path':str(parent),'sha256':sha(parent),'id':old['id']},'starting_usage_live':u,'tasks':tasks,'call_caps':{'synth':6,'grt':2,'final':0},'threads':2,'memory_limit_MiB':32768,'synthesis_timeout_s':900,'post_synthesis_through_grt_timeout_s':3600,'support_envelope':{'walltime_s':2400,'CPU_time_s':4800},'worst_case_walltime_s':wall,'CPU_envelope_s':cpu,'automatic_retries':0,'global_caps_changed':False,'host_meminfo_before':mem,'authorization':'User 2026-11-02 requests completion of step6 deferred/recheck tasks and increased memory; bounded 32GiB task exception, single job two threads, 15min synth and 60min post-synth->grt; exact original RTL/timing conditions','execution':'fresh synth for both baselines validates corrected backend path; controls run only if corresponding baseline completes; no final/original/model/main-matrix tasks','data_role':'capacity and condition-response diagnostic only; excluded from training target labels main matrix','recheck_reason':'UDR128 original 8GiB memory bound; F2 original hierarchy-reader defect repaired; nonzero proof P1 repaired without RTL change'}
path=B/'capacity-admission-v2.json';assert not path.exists();path.write_text(json.dumps(ad,indent=2)+'\n');print(json.dumps({'ready':True,'usage':u,'tasks':len(tasks),'memory_limit_MiB':32768,'walltime_envelope_s':wall,'CPU_envelope_s':cpu},indent=2))
