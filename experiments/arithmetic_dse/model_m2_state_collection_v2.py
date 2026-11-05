"""Versioned state collector: physical-master witness and paid pilot replay.

The v1 producer and failed manifests remain byte-identical. Only the witness
parser changes; RTL, features, clocks, splits and statistical gates do not.
"""
import argparse
import copy
import json
from pathlib import Path
import shutil
import sys

from . import model_m2_state_collection as base
from .budget import Ledger
from .model_collection import sha, write
from .model_m2_cec import leaf

ROOT = base.ROOT
BASE_VERIFY = base.verify
BASE_TASK = base.run_task
BASE_SEED = base.seed_mapping
BASE_WITNESS = base.state_witness
VERSION = 'asap7-m2-state-fitting-successor-v2'


def state_witness(directory, stage, cells):
    """Use the same frozen physical-master classification as stage_metrics."""
    from .platforms import profile
    p = profile('asap7')
    prefix = directory/'reports'/base.SUFFIX/('vulsim_'+stage)
    masters = {}
    physical_counts, physical_area = {}, 0.
    for line in Path(str(prefix)+'_cells.tsv').read_text().splitlines():
        master, count, area, filler, kind = line.split('\t')
        physical = (filler == '1' or kind in p['physical_master_types']
                    or any(master.startswith(s) for s in p['allowed_physical_prefixes']))
        masters[master] = (int(count), float(area), physical)
    # Delegate the strict FF names/counts to the immutable v1 implementation.
    # A synthetic zero-area, nonsequential entry is used only inside that
    # parser; physical area is read from OpenDB and accounted separately.
    augmented = copy.deepcopy(cells)
    instances = [line.split('\t')[:2] for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines()]
    seen = base.Counter(master for _, master in instances)
    for master, (count, area, physical) in masters.items():
        if seen[master] != count:
            raise ValueError('state instance/master counts disagree: '+master)
        if physical:
            if master in cells and cells[master]['sequential']:
                raise ValueError('sequential master classified physical: '+master)
            augmented[master] = {'sequential': False, 'area_um2': 0.}
            physical_counts[master] = count
            physical_area += count*area
        elif master not in cells:
            raise ValueError('unknown logical state-bank master: '+master)
    if set(seen) != set(masters):
        raise ValueError('state instance master missing from OpenDB summary')
    result = BASE_WITNESS(directory, stage, augmented)
    result.update(physical_master_instances=physical_counts,
                  separately_accounted_physical_area_um2=physical_area,
                  physical_area_removed_from_total=False)
    return result


def verify(folder):
    a = BASE_VERIFY(folder)
    if a.get('successor_version') != VERSION:
        raise ValueError('state v2 successor admission required')
    parent = a['predecessor']
    if sha(parent['admission_path']) != parent['admission_sha256']:
        raise ValueError('state predecessor admission changed')
    BASE_VERIFY(Path(parent['admission_path']).parent)
    for tid, inherited in a['inherited_paid_raw_runs'].items():
        if sha(Path(inherited['directory'])/'manifest.json') != inherited['manifest_sha256']:
            raise ValueError('state failed pilot manifest changed: '+tid)
    return a


def prepare(folder, predecessor, rtl_proof):
    old = BASE_VERIFY(predecessor)
    progress = base.read(predecessor/'progress.json')
    if progress['phase'] != 'stopped_on_error' or set(progress['active']):
        raise ValueError('settled stopped predecessor required')
    pilots = set(old['capacity_pilots'])
    if set(x['task_id'] for x in progress['errors']) != pilots:
        raise ValueError('only the two registered pilot parser failures may be inherited')
    inherited = {}
    for tid in sorted(pilots):
        directory = predecessor/'runs'/tid
        m = base.read(directory/'manifest.json')
        if (m['status'] != 'failed' or m.get('failure_reason') != 'unknown state-bank cell'
            or m.get('failure_stage') != 'grt-snapshot'
            or len(m['commands']) != 5 or any(c['exit_code'] for c in m['commands'])):
            raise ValueError('pilot is not an otherwise completed physical run')
        inherited[tid] = {'directory': str(directory), 'manifest_sha256': sha(directory/'manifest.json'),
                          'role': 'same registered training source; paid physical evidence only'}
    base.prepare(folder, rtl_proof)
    a = base.read(folder/'admission.json')
    path = Path(__file__).resolve()
    name = str(path.relative_to(ROOT))
    dst = folder/'source'/name
    shutil.copy2(path, dst)
    a['sources'][name] = sha(path)
    a.update(successor_version=VERSION,
             predecessor={'admission_path': str(predecessor/'admission.json'),
                          'admission_sha256': sha(predecessor/'admission.json')},
             inherited_paid_raw_runs=inherited,
             successor_change='OpenDB physical master classification only; immutable raw pilot replay, no physical retry',
             physical_relaunch_of_inherited_pilots=False)
    write(folder/'admission.json', a)
    verify(folder)


def replay(folder, tid):
    """Reparse saved reports and verify physical commands, CEC and all hashes."""
    from .backend import stage_metrics, verify_orfs_area
    from .model_samples import read_labels
    from .model_m2_live_cec_v3 import verify_proof
    from .model_m2_evaluate import measurement_identity
    from .platforms import profile, verify_wire_readback
    from .sdc import verify_sdc, rtl_ports
    a = verify(folder)
    t = next(t for t in a['tasks'] if t['id'] == tid)
    raw = Path(a['inherited_paid_raw_runs'][tid]['directory'])
    old = base.read(raw/'manifest.json')
    parent = a['predecessor']
    entries = {e['id']: e for e in base.read(Ledger().path)['entries']}
    if sha(raw/'input.sv') != t['rtl_sha256'] or sha(raw/'sample-contract.json') != t['sample_contract_sha256']:
        raise ValueError('inherited pilot RTL/geometry differs')
    for name, h in old['evidence_sha256'].items():
        if sha(raw/name) != h:
            raise ValueError('inherited pilot raw evidence changed: '+name)
    for command in old['commands']:
        entry = entries[command['budget_reservation_id']]
        if (entry['status'] != 'completed' or entry.get('task_id') != tid
            or entry.get('admission_sha256') != parent['admission_sha256']
            or entry['command'] != command['command'] or command['cleanup']['remaining_live_pids']):
            raise ValueError('inherited pilot command unpaid or mismatched')
    if measurement_identity(old) != a['measurement_static_identity_sha256']:
        raise ValueError('inherited pilot physical identity differs')
    for asset in [*old['tools'].values(), *old['libraries']]:
        if sha(asset['path']) != asset['sha256']:
            raise ValueError('pilot physical tool/library changed')
    cells, p = base.read(raw/'liberty_cells.json')['cells'], profile('asap7')
    metrics, sdc_contracts = [], {}
    for stage in ('synth', 'grt'):
        reports = raw/'reports'/base.SUFFIX
        g = stage_metrics(reports, stage, cells, t['period_ps'], selected=p)
        g['model_labels'] = read_labels(reports/('vulsim_'+stage), raw/'sample-contract.json', g['raw_report_units']['time']['to_ps'])
        g['state_witness'] = state_witness(raw, stage, cells)
        wire = verify_wire_readback(reports/('vulsim_'+stage+'_layer_rc.tsv'), p)
        if wire is not None:
            g['wire_RC_readback'] = wire
        stem = {'synth': '1_synth', 'grt': '5_1_grt'}[stage]
        sdc = raw/'results'/base.SUFFIX/(stem+'.sdc')
        sdc_contracts[stage] = verify_sdc(sdc.read_text(), p, t['period_ps'], rtl_ports((raw/'input.sv').read_text(), t['top']))
        if stage in old['sdc_contracts'] and sdc_contracts[stage] != old['sdc_contracts'][stage]:
            raise ValueError('inherited pilot SDC differs')
        native = base.read(raw/'logs'/base.SUFFIX/(stem+'.json'))[('synth' if stage == 'synth' else 'globalroute')+'__design__instance__area__stdcell']
        g['orfs_area_crosscheck'] = verify_orfs_area(g['cell_area_um2'], native)
        if not g['timing_coverage_complete']:
            raise ValueError('pilot timing coverage incomplete')
        metrics.append(g)
    verify_proof(raw/'logs'/base.SUFFIX/'structural_cec/proof.json',
                 raw/'results'/base.SUFFIX/'4_before_rsz_lec.v', raw/'results'/base.SUFFIX/'4_after_rsz_lec.v')
    out = folder/'runs'/tid
    for path in raw.iterdir():
        if path.name not in ('manifest.json', 'metrics.json'):
            (out/path.name).symlink_to(path.resolve(), target_is_directory=path.is_dir())
    m = copy.deepcopy(old)
    m.update(status='completed', admission_id=a['id'], state_collection_version=VERSION,
             state_admission_sha256=sha(folder/'admission.json'), metrics=metrics, sdc_contracts=sdc_contracts,
             commands=[], inherited_physical_commands=old['commands'],
             inherited_raw_run=a['inherited_paid_raw_runs'][tid],
             physical_reexecuted=False, raw_replay_status='passed')
    m.pop('failure_reason', None)
    m.pop('failure_stage', None)
    write(out/'metrics.json', metrics)
    write(out/'manifest.json', m)
    print(json.dumps({'task': tid, 'raw_replay': 'passed', 'PPA_calls': 0,
                      'actual_register_bits': metrics[-1]['state_witness']['actual_register_bits']}), flush=True)


def run_task(folder, task):
    a = verify(folder)
    if task['id'] not in a['inherited_paid_raw_runs']:
        return BASE_TASK(folder, task)
    out = folder/'runs'/task['id']
    out.mkdir(parents=True, exist_ok=False)
    ledger = base.StateLedger(folder, task)
    ctx = {'target_platform': 'asap7', 'admission_id': a['id'], 'task_id': task['id']}
    with ledger.job(ctx):
        record = leaf([sys.executable, '-B', '-m', 'experiments.arithmetic_dse.model_m2_state_collection_v2',
              'replay', '--folder', str(folder), '--task', task['id']], out, 'raw-replay', 120, ledger, ctx)
        m = base.read(out/'manifest.json')
        m.update(commands=[record], budget_job_id=ledger.job_id)
        write(out/'manifest.json', m)
    return task['id']


def seed_mapping(folder, task, out):
    a = verify(folder)
    parent = a['inherited_paid_raw_runs'].get(task['mapping_source_task'])
    if parent is None:
        return BASE_SEED(folder, task, out)
    # BASE_SEED needs the completed replay manifest, while the configuration
    # and saved command still name the original, paid physical run. Build a
    # temporary view through a local copy of its function globals, leaving v1
    # source and all original files untouched.
    import types
    raw = Path(parent['directory'])
    certified = base.read(folder/'runs'/task['mapping_source_task']/'manifest.json')
    certified['commands'] = certified['inherited_physical_commands']
    def read_certified(path):
        return certified if Path(path) == raw/'manifest.json' else base.read(path)
    namespace = dict(BASE_SEED.__globals__)
    namespace['read'] = read_certified
    fn = types.FunctionType(BASE_SEED.__code__, namespace)
    return fn(raw.parent.parent, task, out)


def seal_capacity(folder, admission):
    rows = []
    for tid in admission['capacity_pilots']:
        directory = folder/'runs'/tid
        m = base.read(directory/'manifest.json')
        if m['status'] != 'completed' or len(m['metrics']) != 2 or m.get('raw_replay_status') != 'passed':
            raise ValueError('state successor pilot replay incomplete')
        cells = base.read(directory/'liberty_cells.json')['cells']
        for metric in m['metrics']:
            if state_witness(directory, metric['stage'], cells) != metric['state_witness']:
                raise ValueError('state successor capacity witness changed')
        commands = m['commands']+m['inherited_physical_commands']
        rows.append({'task_id': tid, 'manifest_sha256': sha(directory/'manifest.json'),
                     'inherited_raw_run': m['inherited_raw_run'],
                     'actual_register_bits': m['metrics'][-1]['state_witness']['actual_register_bits'],
                     'peak_RSS_MiB': max(c['sampled_process_tree_peak_rss_KiB'] for c in commands)/1024,
                     'physical_reexecuted': False})
    base.exclusive(folder/'capacity-proof.json', {'status': 'passed', 'version': VERSION,
        'admission_sha256': sha(folder/'admission.json'), 'runs': rows,
        'scope': 'registered fitting geometries; independent capacity and stage combination remain gated'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'run', 'status', 'verify', 'replay'))
    parser.add_argument('--folder', type=Path, required=True)
    parser.add_argument('--predecessor', type=Path)
    parser.add_argument('--rtl-proof', type=Path)
    parser.add_argument('--task')
    args = parser.parse_args()
    folder = args.folder.resolve()
    if args.action == 'prepare':
        if args.predecessor is None or args.rtl_proof is None:
            parser.error('prepare requires predecessor and RTL proof')
        prepare(folder, args.predecessor.resolve(), args.rtl_proof.resolve())
    elif args.action == 'replay':
        replay(folder, args.task)
    elif args.action == 'run':
        base.verify, base.state_witness = verify, state_witness
        base.run_task, base.seed_mapping = run_task, seed_mapping
        base.seal_capacity = seal_capacity
        base.run(folder)
    elif args.action == 'status':
        base.status(folder)
    else:
        verify(folder)
        print('verified state successor v2')


if __name__ == '__main__':
    main()
