"""Task-scoped step6 resource exception; shared global v5 budget unchanged."""
import hashlib
import json
from pathlib import Path
from .budget import POLICY,usage

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def limits(args):
    if not args.admission:raise ValueError('bounded recheck requires explicit admission')
    path=Path(args.admission);a=json.loads(path.read_text())
    if (a.get('purpose')!='arithmetic_capacity_recheck_only' or a['id']!=args.admission_id
            or a['policy_sha256']!=sha(POLICY)):
        raise ValueError('wrong bounded recheck identity')
    thread_fix=a.get('correction_kind')=='yosys_thread_limit'
    completion=a.get('execution_mode')=='complete_initial_backend'
    if completion and not thread_fix:raise ValueError('completion package is limited to the corrected UDR domain')
    count=3 if thread_fix else 6;synth_timeout=7200 if completion else 1800 if thread_fix else 900
    route_timeout=14400 if completion else 3600
    caps={'synth':count,'grt':1 if thread_fix else 2,'final':0}
    tasks=a['tasks'];matches=[t for t in tasks if t['id']==args.task_id]
    if len(tasks)!=count or len({t['id'] for t in tasks})!=count or len(matches)!=1:
        raise ValueError('only the frozen step6 recheck tasks are admitted')
    t=matches[0]
    if (a['call_caps']!=caps or args.stage!=t['stage']
            or args.stage not in ('synth','grt') or args.resume_synth_from
            or args.threads!=2 or args.memory_limit_mib!=32768
            or args.synth_timeout_s!=synth_timeout or args.route_timeout_s!=route_timeout):
        raise ValueError('recheck resources or stages differ from frozen scope')
    if (a.get('memory_limit_MiB')!=32768 or a.get('threads')!=2
            or a.get('synthesis_timeout_s')!=synth_timeout or a.get('post_synthesis_through_grt_timeout_s')!=route_timeout
            or a.get('automatic_retries')!=0):
        raise ValueError('admission does not declare the exact resource exception')
    if thread_fix and (any(x['kernel']!='udr_unsigned_128' for x in tasks) or a.get('yosys_max_threads')!=2):
        raise ValueError('thread correction is limited to the three UDR tasks')
    if t['kernel'] not in ('udr_unsigned_128','fp32_serial') or args.platform!='asap7':
        raise ValueError('unsupported recheck domain')
    return a,t

def verify_admission(args,p,rtl,ledger):
    a,t=limits(args)
    from .sdc import VERSION
    if (t['platform']!=p['platform'] or t['profile_sha256']!=p['profile_sha256']
            or t['rtl_sha256']!=sha(rtl) or t['top']!=args.top
            or t['period_ps']!=args.period_ps or t['abc_target_ps']!=args.abc_target_ps
            or args.budget_purpose!='physical_recheck' or args.period_role!='resource_trial'
            or args.io_delay_max_ps is not None or t['sdc_contract_version']!=VERSION
            or t['constraints_sha256']!=sha(Path(__file__).parent/'backend/constraints.sdc')):
        raise ValueError('recheck circuit/constraint identity differs from frozen task')
    parent=a['parent_admission']
    if sha(parent['path'])!=parent['sha256']:raise ValueError('changed parent admission')
    previous_tasks={x['id']:x for x in json.loads(Path(parent['path']).read_text())['tasks']}
    for task in a['tasks']:
        old=previous_tasks[task['supersedes_task_id']]
        for key in ('rtl_sha256','top','kernel','period_ps','abc_target_ps','stage','L','II'):
            if task[key]!=old[key]:raise ValueError('recheck changed circuit/timing condition '+key)
    state=json.loads(ledger.path.read_text());total=usage(state['entries'])
    attempts=[e for e in state['entries'] if e.get('admission_id')==a['id']]
    if total['pending']:raise ValueError('unsettled global ledger')
    if any(e.get('task_id')==t['id'] for e in attempts):raise ValueError('recheck task already attempted; no automatic retry')
    if t['stage']=='synth':
        baseline=next(x for x in a['tasks'] if x['kernel']==t['kernel'] and x['stage']=='grt')
        path=args.out.resolve().parent/baseline['id']/'manifest.json'
        m=json.loads(path.read_text()) if path.exists() else {}
        if (m.get('status')!='completed' or m.get('task_id')!=baseline['id']
                or not any(x['stage']=='grt' and x['timing_coverage_complete'] for x in m.get('metrics',[]))):
            raise ValueError('baseline incomplete; dependent controls are paused')
    resource=json.loads(POLICY.read_text())['resources']
    for stage,key in [('synth','max_synthesis_calls'),('grt','max_global_route_calls'),('final','max_detailed_route_calls')]:
        remaining=a['call_caps'][stage]-sum(e['stage']==stage for e in attempts)
        if total[stage]+remaining>resource[key]:raise ValueError('remaining recheck calls not funded')
    remaining_wall=sum(max(0,a['call_caps'][s]-sum(e['stage']==s for e in attempts))*timeout for s,timeout in [('synth',a['synthesis_timeout_s']),('grt',a['post_synthesis_through_grt_timeout_s'])])+a['support_envelope']['walltime_s']
    if total['walltime_s']+remaining_wall>resource['max_global_walltime_h']*3600 or total['CPU_time_s']+remaining_wall*2>resource['max_tool_CPU_time_h']*3600:
        raise ValueError('remaining recheck resource envelope not funded')
    # Recheck current availability before every task; the larger cap must not
    # silently consume memory belonging to another workload.
    available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))
    if available<(32768+8192)*1024:raise ValueError('less than 40 GiB available before recheck launch')
    return sha(args.admission)
