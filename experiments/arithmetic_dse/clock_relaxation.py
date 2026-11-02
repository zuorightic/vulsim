"""One controlled SDC relaxation using an identity-checked mapped netlist.

Yosys/ABC mapping is reused at the original 1500 ps target. ORFS regenerates
the synthesis ODB/SDC and runs a fresh floorplan -> CTS -> global route chain
at 100 ns, with the original absolute 300 ps I/O delays.
"""
import hashlib
import json
import shutil
from pathlib import Path
from .budget import POLICY,usage
from .characterization import mapped_netlist_hash
from .sdc import VERSION

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def task(args):
    if not args.admission:raise ValueError('clock relaxation requires a frozen admission')
    a=json.loads(Path(args.admission).read_text())
    if (a.get('purpose')!='arithmetic_clock_relaxation_only' or a['id']!=args.admission_id
            or a['policy_sha256']!=sha(POLICY) or a['call_caps']!={'synth':1,'grt':1,'final':0}
            or len(a['tasks'])!=1):raise ValueError('invalid one-task clock relaxation scope')
    t=a['tasks'][0]
    if (a.get('automatic_retries')!=0 or a.get('threads')!=2 or a.get('memory_limit_MiB')!=32768
            or a.get('synthesis_timeout_s')!=300 or a.get('post_synthesis_through_grt_timeout_s')!=14400
            or a.get('support_envelope')!={'walltime_s':1800,'CPU_time_s':3600}
            or a.get('worst_case_walltime_s')!=16500 or a.get('CPU_envelope_s')!=33000):
        raise ValueError('clock relaxation resource declaration mismatch')
    if (args.task_id!=t['id'] or args.platform!='asap7' or args.stage!='grt'
            or args.period_ps!=100000 or args.abc_target_ps!=1500 or args.io_delay_max_ps!=300
            or args.top!='Step6UDR128' or args.threads!=2 or args.memory_limit_mib!=32768
            or args.synth_timeout_s!=300 or args.route_timeout_s!=14400
            or not args.resume_synth_from or Path(args.resume_synth_from).resolve()!=Path(t['source_run']).resolve()):
        raise ValueError('clock relaxation must use the exact RTL, single SDC axis and mapped checkpoint')
    return a,t

def verify_admission(args,p,rtl,ledger):
    a,t=task(args);source=Path(t['source_run']);m=json.loads((source/'manifest.json').read_text())
    if (t['period_ps']!=args.period_ps or t['abc_target_ps']!=args.abc_target_ps or t['io_delay_max_ps']!=args.io_delay_max_ps
            or sha(source/'manifest.json')!=t['source_manifest_sha256'] or sha(rtl)!=t['rtl_sha256']
            or p['profile_sha256']!=t['profile_sha256'] or m['period_ps']!=1500
            or m['abc_target_ps']!=1500 or m['status']!='failed' or m['failure_code']!='timeout'
            or m['failure_stage']!='grt' or sha(source/'input.sv')!=t['rtl_sha256']
            or not any(x['stage']=='synth' and x['timing_coverage_complete'] for x in m['metrics'])
            or args.budget_purpose!='physical_recheck' or args.period_role!='resource_trial'
            or sha(Path(__file__).parent/'backend/constraints.sdc')!=t['constraints_sha256']
            or t['sdc_contract_version']!=VERSION):raise ValueError('clock relaxation source/conditions are not bound')
    total=usage(json.loads(ledger.path.read_text())['entries']);limits=json.loads(POLICY.read_text())['resources']
    entries=json.loads(ledger.path.read_text())['entries']
    if total['pending'] or any(e.get('admission_id')==a['id'] for e in entries):raise ValueError('unsettled or already attempted clock relaxation')
    if (total['synth']+1>limits['max_synthesis_calls'] or total['grt']+1>limits['max_global_route_calls']
            or total['walltime_s']+a['worst_case_walltime_s']>limits['max_global_walltime_h']*3600
            or total['CPU_time_s']+a['CPU_envelope_s']>limits['max_tool_CPU_time_h']*3600):
        raise ValueError('clock relaxation full resource envelope not funded')
    available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))
    if available<(32768+8192)*1024:raise ValueError('less than 40 GiB available before clock relaxation launch')
    return sha(args.admission)

def seed_mapped(args,out,results,environment,command,tools):
    a,t=task(args);source=Path(t['source_run']);m=json.loads((source/'manifest.json').read_text())
    for key in ('LIB_FILES','TECH_LEF','SC_LEF','CORNER','ASAP7_USE_VT','LIB_MODEL','TC_TEMPERATURE','ABC_DRIVER_CELL','ABC_LOAD_IN_FF','YOSYS_MAX_THREADS'):
        if environment.get(key)!=m['effective_environment'].get(key):raise ValueError('mapped reuse condition changed: '+key)
    for name,tool in tools.items():
        if tool['sha256']!=m['tools'][name]['sha256']:raise ValueError('mapped reuse tool changed: '+name)
    for lib in m['libraries']:
        if sha(lib['path'])!=lib['sha256']:raise ValueError('mapped reuse Liberty changed')
    for filename,h in m['files_sha256'].items():
        path=Path(filename)
        if path.is_relative_to(Path(args.orfs).resolve()) or path.is_relative_to(Path(__file__).parent/'backend'):
            if sha(path)!=h:raise ValueError('mapped/physical source asset changed: '+filename)
    name='1_2_yosys.v';old=source/'results/asap7/arithmetic_probe/base'/name
    if sha(old)!=t['mapped_netlist_file_sha256'] or m['evidence_sha256'].get(str(old.relative_to(source)))!=sha(old):
        raise ValueError('mapped netlist checkpoint identity mismatch')
    expected=next(x['mapped_netlist_sha256'] for x in m['metrics'] if x['stage']=='synth')
    if mapped_netlist_hash(old.read_text())!=expected:raise ValueError('normalized mapped graph identity mismatch')
    results.mkdir(parents=True,exist_ok=True)
    if any(results.iterdir()):raise ValueError('clock relaxation output must contain no inherited physical results')
    target=results/name;shutil.copy2(old,target);command.append('--assume-old='+str(target))
    return {'mode':'same_mapped_netlist_fresh_SDC_and_physical_chain',
            'source_manifest_sha256':sha(source/'manifest.json'),'source_netlist_file_sha256':sha(old),
            'normalized_mapped_netlist_sha256':expected,'reused':['Yosys_ABC_mapping_only'],
            'executed':['synthesis_ODB_SDC_regeneration','floorplan','placement','CTS','global_route'],
            'source_ABC_target_ps':1500,'old_SDC_period_ps':1500,'new_SDC_period_ps':100000,
            'IO_delay_max_ps':300,'old_ODB_or_old_SDC_copied':False,
            'timing_scope':'one fresh complete physical chain; mapping time inherited and separately reported'}
