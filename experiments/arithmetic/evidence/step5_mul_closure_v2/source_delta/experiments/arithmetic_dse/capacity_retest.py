"""One explicitly admitted post-synthesis -> grt capacity retest, no synthesis.

The task-level 3600s exception never changes backend_policy_v5, final limits or
other admissions. Exact checkpoint/flow identities and fresh output prevent
Make from silently turning this into a CTS-only continuation.
"""
import hashlib,json,math
from pathlib import Path
from .budget import POLICY,usage
from .sdc import VERSION,verify_sdc,rtl_ports

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def task(args):
 if not args.admission:raise ValueError('checkpoint reuse requires an explicit retest admission')
 admission=json.loads(Path(args.admission).read_text())
 if admission.get('purpose')!='mul_capacity_retest_only' or admission['id']!=args.admission_id or admission['policy_sha256']!=digest(POLICY):raise ValueError('wrong retest admission identity')
 if len(admission['tasks'])!=1 or admission['call_caps']!={'synth':0,'grt':1,'final':0}:raise ValueError('retest may only execute one grt leaf')
 t=admission['tasks'][0]
 if t['id']!=args.task_id or args.stage!='grt' or not args.resume_synth_from:raise ValueError('only the named complete post-synthesis grt chain is admitted')
 if (t['grt_walltime_limit_s']!=3600 or t['grt_CPU_limit_s']!=7200 or args.route_timeout_s!=3600 or args.threads!=2 or args.memory_limit_mib!=8192 or t['threads']!=2 or t['memory_limit_MiB']!=8192):raise ValueError('retest resource request differs from explicit one-task exception')
 if Path(args.resume_synth_from).resolve()!=Path(t['resume_directory']).resolve():raise ValueError('wrong synthesis checkpoint source')
 return admission,t

def verify_admission(args,p,rtl,ledger):
 admission,t=task(args)
 if (args.platform!='asap7' or args.budget_purpose!='physical_recheck' or args.period_role!='resource_trial' or args.io_delay_max_ps is not None or t['profile_sha256']!=p['profile_sha256'] or digest(rtl)!=t['rtl_sha256'] or args.top!=t['top'] or args.period_ps!=1500 or args.abc_target_ps!=1500):raise ValueError('retest circuit/platform/constraint identity mismatch')
 source=Path(args.resume_synth_from);manifest=source/'manifest.json'
 if digest(manifest)!=t['source_manifest_sha256']:raise ValueError('changed original run manifest')
 previous=json.loads(manifest.read_text())
 if previous['task_id']!='asap7-mul128-C-capacity-v1' or previous['status']!='failed' or previous['failure_code']!='timeout' or previous['stages_requested']!='grt':raise ValueError('not the specified original timeout task')
 if previous['platform_profile']['profile_sha256']!=p['profile_sha256']:raise ValueError('source platform mismatch')
 # All checkpoint identities were frozen before launch in the original manifest.
 for name,h in t['checkpoint_sha256'].items():
  path=source/'results/asap7/arithmetic_probe/base'/name
  if digest(path)!=h or previous['evidence_sha256'].get(str(path.relative_to(source)))!=h:raise ValueError('unbound synthesis checkpoint '+name)
 verify_sdc((source/'results/asap7/arithmetic_probe/base/1_synth.sdc').read_text(),p,args.period_ps,rtl_ports((source/'input.sv').read_text()))
 if digest(source/'input.sv')!=t['rtl_sha256']:raise ValueError('source input RTL changed')
 if digest(Path(__file__).parent/'backend/constraints.sdc')!=t['constraints_sha256'] or t['sdc_contract_version']!=VERSION:raise ValueError('constraint contract changed')
 state=json.loads(ledger.path.read_text());total=usage(state['entries'])
 if total['pending']:raise ValueError('unsettled global ledger')
 if any(e.get('admission_id')==admission['id'] for e in state['entries']):raise ValueError('one retest already attempted; no automatic retry')
 limits=json.loads(POLICY.read_text())['resources'];remaining=admission['remaining_launch_envelope']
 if total['grt']+1>limits['max_global_route_calls'] or total['walltime_s']+remaining['walltime_s']>limits['max_global_walltime_h']*3600 or total['CPU_time_s']+remaining['CPU_time_s']>limits['max_tool_CPU_time_h']*3600:raise ValueError('retest full live resource envelope not funded')
 return digest(args.admission)

def seed_checkpoint(args,out,results,command,environment):
 admission,t=task(args);source=Path(args.resume_synth_from);old=json.loads((source/'manifest.json').read_text())
 # Tool and all ORFS/platform/SDC script identities, excluding only the Python
 # orchestration we intentionally repaired. Paths still refer to original files.
 orfs=Path(args.orfs).resolve();assets=Path(__file__).parent/'backend'
 for path,h in old['files_sha256'].items():
  p=Path(path)
  if p.is_relative_to(orfs) or p.is_relative_to(assets):
   if digest(p)!=h:raise ValueError('retest physical asset or script changed: '+path)
 for tool in old['tools'].values():
  if digest(tool['path'])!=tool['sha256']:raise ValueError('retest tool binary changed')
 for key in ('LIB_FILES','TECH_LEF','SC_LEF','RCX_RULES','ABC_DRIVER_CELL','ABC_LOAD_IN_FF','CORNER','ASAP7_USE_VT','LIB_MODEL','TC_TEMPERATURE'):
  if environment.get(key)!=old['effective_environment'].get(key):raise ValueError('retest effective condition changed: '+key)
 results.mkdir(parents=True,exist_ok=True)
 if any(results.iterdir()):raise ValueError('post-synthesis target must contain no later-stage products')
 import shutil
 for name,h in t['checkpoint_sha256'].items():
  target=results/name;shutil.copy2(source/'results/asap7/arithmetic_probe/base'/name,target)
  if digest(target)!=h:raise ValueError('checkpoint copy mismatch')
  command.append('--assume-old='+str(target))
 return {'mode':'full_post_synthesis_to_grt','source_manifest':str(source/'manifest.json'),'source_manifest_sha256':digest(source/'manifest.json'),'reused_stages':['synth'],'executed_stages':['floorplan','placement','CTS','global_route'],'checkpoint_sha256':t['checkpoint_sha256'],'make_assume_old_targets':[str(results/name) for name in t['checkpoint_sha256']],'later_stage_products_copied':0,'old_synthesis_metrics':old['metrics'][0],'timing_origin':'one new grt leaf beginning before floorplan, synthesis excluded; not stitched time'}
