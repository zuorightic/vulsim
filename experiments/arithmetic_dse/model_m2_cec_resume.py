"""Resume the three frozen M2 failures using complete structural CEC proofs."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import copy
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import shutil
import sys

from .budget import Ledger, POLICY
from .model_collection import sha, write
from .model_m2_cec import verify_proof
from .processes import run_command

ROOT = Path(__file__).resolve().parents[2]
SUFFIX = Path('asap7/arithmetic_probe/base')
ORFS = Path('/home/zyrv/OpenROAD-flow-scripts')
PLAN = ROOT/'build/step7-m2-models-20261104/primitives-v6/plan.json'
PAIRS = {
    'train-F1-divrem-w32-t2': ('primitives-v5/runs/train-F1-divrem-w32-t2', 'cec-F1-proof-v2'),
    'train-F3-divrem-w32-t2': ('primitives-v6/runs/train-F3-divrem-w32-t2', 'cec-F3-proof-v1'),
    'validation-F2-divrem-w32-t3': ('primitives-v6/runs/validation-F2-divrem-w32-t3', 'cec-validation-F2-proof-v1'),
}


def read(path):
    return json.loads(Path(path).read_text())


def render_cts(original, proof, wrapper, postrepair):
    marker = '    run_lec_test 4_rsz 4_before_rsz_lec.v 4_after_rsz_lec.v'
    if original.count(marker) != 1:
        raise ValueError('unsupported CTS proof boundary')
    verification = f'exec {{{sys.executable}}} -B {{{wrapper}}} {{{proof}}} $::env(RESULTS_DIR)/4_before_rsz_lec.v '
    if not postrepair:
        return original.replace(marker, '    '+verification+'$::env(RESULTS_DIR)/4_after_rsz_lec.v\n'
                                '    puts "Repair timing output passed structural CEC: exact pair verified"')
    start = original.index('\n  set result [catch { log_cmd detailed_placement } msg]', original.index(marker))
    prefix = '''utl::set_metrics_stage "cts__{}"
source $::env(SCRIPTS_DIR)/load.tcl
source $::env(SCRIPTS_DIR)/lec_check.tcl
erase_non_stage_variables cts
load_design 4_1_post_repair_pre_lec.odb 4_1_post_repair_pre_lec.sdc
proc save_progress { stage } {
  orfs_write_db $::env(RESULTS_DIR)/$stage.odb
  orfs_write_sdc $::env(RESULTS_DIR)/$stage.sdc
}
set_dont_use $::env(DONT_USE_CELLS)
set_placement_padding -global -left $::env(CELL_PAD_IN_SITES_DETAIL_PLACEMENT) -right $::env(CELL_PAD_IN_SITES_DETAIL_PLACEMENT)
write_lec_verilog 4_after_resume_load.v
'''
    return prefix+verification+'$::env(RESULTS_DIR)/4_after_resume_load.v\nif {1} {\n'+original[start:]


def prepare(folder):
    from .model_m2_collection import verify_plan
    plan = verify_plan(PLAN)
    folder.mkdir(parents=True, exist_ok=False)
    sources = {}
    for name in ('model_m2_cec.py', 'model_m2_cec_resume.py'):
        p = Path(__file__).with_name(name); shutil.copy2(p, folder/name); sources[name] = sha(p)
    tasks = []
    for tid, (run, proof) in PAIRS.items():
        source = PLAN.parent.parent/run; proof = PLAN.parent.parent/proof/'manifest.json'
        m = read(source/'manifest.json'); result = source/'results'/SUFFIX
        if m['status'] != 'failed':
            raise ValueError('resume only named failed source')
        verify_proof(proof, result/'4_before_rsz_lec.v', result/'4_after_rsz_lec.v')
        t = next(t for t in plan['tasks'] if t['id'] == tid)
        postrepair = (result/'4_1_post_repair_pre_lec.odb').exists()
        files = ['1_2_yosys.v', '1_synth.odb', '1_synth.sdc', '4_before_rsz_lec.v', '4_after_rsz_lec.v']
        files += ['4_1_post_repair_pre_lec.odb', '4_1_post_repair_pre_lec.sdc'] if postrepair else ['1_2_yosys.sdc', '3_place.odb', '3_place.sdc']
        checkpoints = {}
        for name in files:
            path = result/name; rel = str(path.relative_to(source)); h = sha(path)
            if m['evidence_sha256'].get(rel) != h:
                raise ValueError('changed recovery checkpoint')
            checkpoints[rel] = h
        tasks.append({'task': t, 'source_run': str(source), 'source_manifest_sha256': sha(source/'manifest.json'),
                      'proof': str(proof), 'proof_sha256': sha(proof), 'postrepair': postrepair, 'checkpoints': checkpoints})
    write(folder/'admission.json', {'version': 'm2-structural-cec-resume-v1', 'id': folder.name, 'tasks': tasks,
          'parent_plan': str(PLAN), 'parent_plan_sha256': sha(PLAN), 'sources': sources, 'policy_sha256': sha(POLICY),
          'parallel_jobs': 3, 'threads': 4, 'route_timeout_s': 3600, 'cts_tail_timeout_s': 600,
          'sampling_and_quality_gates_changed': False, 'test_locked': True, 'automatic_retries': 0})


def verify_admission(folder):
    a = read(folder/'admission.json')
    if sha(POLICY) != a['policy_sha256'] or sha(a['parent_plan']) != a['parent_plan_sha256']:
        raise ValueError('changed recovery parent/policy')
    for name, h in a['sources'].items():
        if sha(Path(__file__).with_name(name)) != h or sha(folder/name) != h:
            raise ValueError('changed recovery producer')
    for t in a['tasks']:
        if sha(Path(t['source_run'])/'manifest.json') != t['source_manifest_sha256'] or sha(t['proof']) != t['proof_sha256']:
            raise ValueError('changed source/proof')
    return a


def recover(folder, item):
    from .backend import stage_metrics, verify_orfs_area
    from .model_samples import read_labels, verify_capture_banks
    from .sdc import verify_sdc, rtl_ports
    a = verify_admission(folder); t = item['task']; source = Path(item['source_run']); old = read(source/'manifest.json')
    out = folder/'runs'/t['id']; out.mkdir(parents=True, exist_ok=False)
    m = copy.deepcopy(old)
    m.update(status='running', commands=[], metrics=[], admission_id=a['id'], started_at=datetime.now(timezone.utc).isoformat(),
             structural_cec_resume=True, source_run=str(source), source_manifest_sha256=item['source_manifest_sha256'],
             admission_sha256=sha(folder/'admission.json'), active_stage='preflight')
    for key in ('finished_at', 'failure_stage', 'failure_code', 'failure_reason', 'active_reservation'):
        m.pop(key, None)
    ledger = Ledger(); context = {'target_platform': 'asap7', 'admission_id': a['id'], 'task_id': t['id']}
    env = os.environ.copy(); env.update(OMP_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4', YOSYS_MAX_THREADS='4',
                                       QT_QPA_PLATFORM='offscreen', PYTHONDONTWRITEBYTECODE='1', VULSIM_LABEL_REQUESTS=str(out/'label_requests.tcl'))
    def save():
        write(out/'manifest.json', m)
    with ledger.job(context):
        m['budget_job_id'] = ledger.job_id
        def execute(command, stem, timeout, stage=None):
            reservation = ledger.reserve(stage, timeout, 4, 'characterization', command, out/stem,
                context={**context, 'admission_sha256': sha(folder/'admission.json')})
            m['active_reservation'] = reservation['id']; save()
            record = run_command(command, out, stem, timeout, env, 8192, cpu_limit_s=reservation['CPU_time_s'])
            ledger.finish(reservation, record); record['budget_reservation_id'] = reservation['id']; m['commands'].append(record); save()
            if record['exit_code']:
                raise RuntimeError(stem+': command failed; timeout='+str(record['timed_out']))
        try:
            save()
            for lib in old['libraries']:
                if sha(lib['path']) != lib['sha256']: raise ValueError('changed recovery library')
            for tool in old['tools'].values():
                if sha(tool['path']) != tool['sha256']: raise ValueError('changed physical tool')
            for name, h in old['files_sha256'].items():
                path = Path(name)
                if (path.is_relative_to(ORFS) or path.is_relative_to(ROOT/'experiments/arithmetic_dse/backend')) and sha(path) != h:
                    raise ValueError('changed physical asset')
            for name, h in item['checkpoints'].items():
                path = source/name
                if sha(path) != h: raise ValueError('changed recovery checkpoint')
                dst = out/name; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(path, dst)
            for name in ('input.sv', 'sample-contract.json', 'label_requests.tcl', 'liberty_cells.json'):
                shutil.copy2(source/name, out/name)
            for name, h in old['evidence_sha256'].items():
                if name.startswith('reports/'+str(SUFFIX)+'/vulsim_synth') or name.startswith('logs/'+str(SUFFIX)+'/1_synth'):
                    if sha(source/name) != h: raise ValueError('changed inherited synth evidence')
                    dst = out/name; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source/name, dst)
            scripts = out/'flow-scripts'; scripts.mkdir()
            for path in (source/'flow-scripts').iterdir():
                if path.is_symlink(): (scripts/path.name).symlink_to(path.resolve())
                elif path.is_file(): shutil.copy2(path, scripts/path.name)
            config = out/'config.mk'; config.write_text((source/'config.mk').read_text().replace(str(source), str(out)))
            wrapper = out/'verify-structural-cec.py'
            wrapper.write_text('import sys\nfrom pathlib import Path\nsys.path.insert(0,'+repr(str(ROOT))+')\n'
                               'from experiments.arithmetic_dse.model_m2_cec import verify_proof\nverify_proof(*map(Path,sys.argv[1:]))\n')
            script = out/'cts-resume.tcl'
            script.write_text(render_cts((ORFS/'flow/scripts/cts.tcl').read_text(), Path(item['proof']), wrapper, item['postrepair']))
            results = out/'results'/SUFFIX
            verify_proof(item['proof'], results/'4_before_rsz_lec.v', results/'4_after_rsz_lec.v')
            base = next(c['command'][:-1] for c in old['commands'] if c['log'].endswith('/grt.log'))
            base = [x.replace(str(source), str(out)) for x in base if not x.startswith('--assume-old=')]
            if item['postrepair']:
                m['active_stage'] = 'CTS_post_LEC'; save()
                execute(base+['run', 'RUN_SCRIPT='+str(script), 'RUN_LOG_NAME_STEM=4_1_cts_resume'], 'cts-post-lec', a['cts_tail_timeout_s'], 'grt')
                shutil.copy2(results/'4_1_cts.odb', results/'4_cts.odb')
                assume = ['--assume-old='+str(results/n) for n in ('4_1_cts.odb', '4_cts.odb', '4_cts.sdc')]
            else:
                cts = scripts/'cts.tcl'; cts.unlink(); shutil.copy2(script, cts)
                assume = ['--assume-old='+str(results/n) for n in ('1_2_yosys.v', '1_2_yosys.sdc', '1_synth.odb', '1_synth.sdc', '3_place.odb', '3_place.sdc')]
            m['active_stage'] = 'grt'; save()
            execute(base+assume+['grt'], 'grt', a['route_timeout_s'], 'grt')
            m['active_stage'] = 'grt_snapshot'; save()
            execute(base+['run', 'RUN_SCRIPT='+str(ROOT/'experiments/arithmetic_dse/backend/snapshot.tcl'),
                          'RUN_LOG_NAME_STEM=vulsim_grt', 'VULSIM_EVAL_STAGE=grt', 'VULSIM_EVAL_DB=5_1_grt.odb', 'VULSIM_EVAL_SDC=5_1_grt.sdc'], 'grt-snapshot', 120)
            reports = out/'reports'/SUFFIX; cells = read(out/'liberty_cells.json')['cells']
            g = stage_metrics(reports, 'grt', cells, t['period_ps'], selected=old['platform_profile'])
            g['model_labels'] = read_labels(reports/'vulsim_grt', out/'sample-contract.json', g['raw_report_units']['time']['to_ps'])
            g['model_capture_banks'] = verify_capture_banks(reports/'vulsim_grt', out/'sample-contract.json', cells)
            g.update(abc_target_ps=1500, mapping_context_sha256=old['mapping_context_sha256'], target_dependent_measurement=True)
            native = read(out/'logs'/SUFFIX/'5_1_grt.json')['globalroute__design__instance__area__stdcell']
            g['orfs_area_crosscheck'] = verify_orfs_area(g['cell_area_um2'], native); g['orfs_stdcell_area_um2'] = native
            verify_sdc((results/'5_1_grt.sdc').read_text(), old['platform_profile'], t['period_ps'], rtl_ports((out/'input.sv').read_text(), t['top']))
            if not g['timing_coverage_complete']: raise ValueError('incomplete resumed timing coverage')
            synth = copy.deepcopy(next(x for x in old['metrics'] if x['stage'] == 'synth')); synth['raw_reports_prefix'] = str(reports/'vulsim_synth')
            m.update(status='completed', metrics=[synth, g], checkpoint_reuse={
                'mode': 'complete_structural_CEC_exact_ODB_or_CTS_replay', 'proof_path': item['proof'], 'proof_sha256': item['proof_sha256'],
                'no_CTS_repair_replay': item['postrepair'], 'cold_runtime_claimed': False})
            m['files_sha256'].update({str(p): sha(p) for p in (script, config, wrapper)})
            write(out/'metrics.json', m['metrics'])
        except Exception as error:
            m.update(status='failed', failure_stage=m['active_stage'], failure_reason=str(error))
        finally:
            m['finished_at'] = datetime.now(timezone.utc).isoformat()
            m['evidence_sha256'] = {str(p.relative_to(out)): sha(p) for name in ('logs', 'reports', 'results') for p in (out/name).rglob('*') if p.is_file()}
            save()
    print(json.dumps({'task': t['id'], 'status': m['status'], 'reason': m.get('failure_reason')}), flush=True)
    if m['status'] != 'completed': raise RuntimeError(t['id']+': '+m['failure_reason'])
    return t['id']


def run(folder):
    a = verify_admission(folder)
    with (folder/'advance.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        write(folder/'progress.json', {'phase': 'structural_CEC_recovery', 'tasks': list(PAIRS)})
        errors = []
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(recover, folder, t) for t in a['tasks']]
            for future in futures:
                try: future.result()
                except Exception as error: errors.append(str(error))
        write(folder/'progress.json', {'phase': 'stopped_on_error' if errors else 'recovery_complete', 'errors': errors})
        if errors: raise RuntimeError(str(errors))


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('action', choices=['prepare', 'run'])
    ap.add_argument('--folder', type=Path, required=True); args = ap.parse_args()
    if args.action == 'prepare': prepare(args.folder.resolve())
    else: run(args.folder.resolve())


if __name__ == '__main__': main()
