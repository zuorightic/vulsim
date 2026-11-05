"""Rebuild state-bank fitting labels from raw reports and paid ancestry."""
import argparse
from collections import Counter
from contextlib import redirect_stdout
import io
import json
import math
from pathlib import Path

from .budget import Ledger, cpu_seconds
from .model_collection import sha, write
from . import model_m2_state_collection as collection
from .model_m2_state_collection_v2 import state_witness
from .model_m2_state_collection_v3 import rtl_ports
from .model_m2_state_samples import specifications, source, features

ROOT = collection.ROOT
SUFFIX = collection.SUFFIX


def read(path):
    return json.loads(Path(path).read_text())


class RawAudit:
    def __init__(self, entries):
        self.entries = {e['id']: e for e in entries}
        self.commands, self.directories, self.hashed = set(), {}, {}
        self.support_sidecar_reconciliations = []
        self.library_tables = {}

    def digest(self, path):
        path = Path(path).resolve()
        if path not in self.hashed:
            self.hashed[path] = sha(path)
        return self.hashed[path]

    def ancestry(self, directory, visiting=None):
        directory = Path(directory).resolve()
        if directory in self.directories:
            return
        visiting = set() if visiting is None else visiting
        if directory in visiting:
            raise ValueError('cyclic state evidence ancestry')
        visiting = visiting | {directory}
        m = read(directory/'manifest.json')
        admission = directory.parent.parent/'admission.json'
        owner = self.digest(admission)
        a = read(admission)
        if m['admission_id'] != a['id']:
            raise ValueError('physical manifest owner differs')
        for c in m['commands']:
            e = self.entries[c['budget_reservation_id']]
            if (e['status'] != 'completed' or e['command'] != c['command'] or c['exit_code']
                or e.get('admission_sha256') != owner or e.get('task_id') != m['task_id']
                or e.get('admission_id') != a['id'] or c['cleanup']['remaining_live_pids']
                or c['timed_out'] or c['memory_limit_exceeded'] or c['CPU_limit_exceeded']):
                raise ValueError('state physical command incomplete or unpaid')
            saved = Path(c['log'].removesuffix('.log')+'.command.json')
            if read(saved) != {k:v for k,v in c.items() if k != 'budget_reservation_id'}:
                # The shared support helper appends its reservation ID to the
                # saved command; backend leaves save it only in the manifest.
                if read(saved) != c:
                    self.reconcile_support_alias(saved, c, e, directory)
            self.commands.add(e['id'])
        for name, h in m.get('evidence_sha256', {}).items():
            if self.digest(directory/name) != h:
                raise ValueError('state raw evidence changed: '+name)
        for name, h in m.get('source_sha256', {}).items():
            local = directory/'source'/name
            if local.exists() and self.digest(local) != h:
                raise ValueError('state producer snapshot changed: '+name)
        for name, h in m['files_sha256'].items():
            if self.digest(name) != h:
                raise ValueError('state physical file changed: '+name)
        for asset in [*m['tools'].values(), *m['libraries']]:
            if self.digest(asset['path']) != asset['sha256']:
                raise ValueError('state physical tool/library changed')
        # Regenerate the prediction-independent cell table from the frozen
        # Liberty files; never trust an unbound cached area/sequential flag.
        signature = tuple((lib['path'],lib['sha256']) for lib in m['libraries'])
        if signature not in self.library_tables:
            from .platforms import library_data, profile
            libs, table = library_data([Path(lib['path']) for lib in m['libraries']],profile('asap7'))
            if libs != m['libraries']:
                raise ValueError('reparsed state Liberty identity differs')
            self.library_tables[signature] = table
        if read(directory/'liberty_cells.json')['cells'] != self.library_tables[signature]:
            raise ValueError('state Liberty area/sequential table changed')
        refs = []
        if m.get('inherited_raw_run'):
            ref = m['inherited_raw_run']
            refs.append((Path(ref['directory']), ref['manifest_sha256']))
        if m.get('checkpoint_reuse'):
            ref = m['checkpoint_reuse']
            raw = Path(ref['source_run'])
            if (ref['mode'] != 'exact_t0_mapping_fresh_SDC_ODB' or ref['old_ODB_or_SDC_copied']
                or ref['Yosys_ABC_reexecuted']
                or self.digest(raw/'results'/SUFFIX/'1_2_yosys.v') != ref['source_netlist_sha256']
                or self.digest(directory/'results'/SUFFIX/'1_2_yosys.v') != ref['source_netlist_sha256']):
                raise ValueError('state exact mapping reuse differs')
            refs.append((raw, ref['source_manifest_sha256']))
        for raw, h in refs:
            if self.digest(raw/'manifest.json') != h:
                raise ValueError('state ancestor manifest changed')
            for name in ('input.sv', 'sample-contract.json'):
                if self.digest(raw/name) != self.digest(directory/name):
                    raise ValueError('state mapping/replay source changed')
            self.ancestry(raw, visiting)
        if m['status'] != 'completed' and m.get('failure_reason') not in (
            'unknown state-bank cell', 'SDC IO coverage mismatch (includes reset/valid/data)'):
            raise ValueError('unsupported failed state ancestor')
        self.directories[directory] = self.digest(directory/'manifest.json')

    def reconcile_support_alias(self, saved, original, entry, directory):
        """Only the two already recorded v3 support-log alias failures qualify.

        Preserve the damaged sidecar bytes. The immutable ancestor manifest,
        original GNU time/log and settled ledger bind the successful support
        leaf. The observed sidecar is the separately paid v3 failed leaf.
        Physical command records never take this path.
        """
        observed = read(saved)
        failed = self.entries.get(observed.get('budget_reservation_id'), {})
        failed_dir = Path(observed.get('log', '')).parent
        expected_task = directory.name
        if (entry['stage'] is not None or failed.get('stage') is not None
            or directory.parent.parent.name != 'step7-state-boundary-20261105-v2'
            or expected_task not in ('state-train-large-w37-t0', 'state-train-large-w65-t0')
            or 'experiments.arithmetic_dse.model_m2_state_collection_v2' not in original['command']
            or 'experiments.arithmetic_dse.model_m2_state_collection_v3' not in observed.get('command', [])
            or failed_dir.parent.parent.name != 'step7-state-boundary-20261105-v3'
            or failed.get('status') != 'failed' or failed.get('exit_code') != 1
            or failed.get('command') != observed.get('command') or observed.get('exit_code') != 1
            or failed.get('task_id') != expected_task or failed_dir.name != expected_task
            or failed.get('admission_sha256') != sha(failed_dir.parent.parent/'admission.json')
            or not (failed_dir/'raw-replay.command.json').is_symlink()
            or (failed_dir/'raw-replay.command.json').resolve() != saved.resolve()
            or abs(entry['CPU_time_s']-cpu_seconds(original['gnu_time'])) > 1e-8
            or entry['walltime_s'] != original['walltime_s']
            or observed.get('cleanup', {}).get('remaining_live_pids')
            or abs(failed['CPU_time_s']-cpu_seconds(observed['gnu_time'])) > 1e-8):
            raise ValueError('unreconciled state command-sidecar mismatch: '+str(saved))
        old_log = Path(original['log']).read_text()
        new_log = Path(observed['log']).read_text()
        if ('"raw_replay": "passed"' not in old_log or '"PPA_calls": 0' not in old_log
            or 'FileExistsError' not in new_log or 'raw-replay.log' not in new_log):
            raise ValueError('state support alias failure evidence differs')
        self.support_sidecar_reconciliations.append({
            'role':'support_only_v3_same_name_symlink_overwrite; never a physical result',
            'observed_sidecar_path':str(saved), 'observed_sidecar_sha256':sha(saved),
            'original_manifest_path':str(directory/'manifest.json'),
            'original_manifest_sha256':sha(directory/'manifest.json'),
            'original_command':original, 'original_ledger_entry':entry,
            'original_log_sha256':sha(original['log']), 'original_resource_sha256':sha(original['gnu_time']),
            'paid_failed_v3_entry':failed, 'failed_log_sha256':sha(observed['log']),
            'failed_resource_sha256':sha(observed['gnu_time']),
            'source_bytes_restored_or_refunded':False})


def reparse(directory, task):
    from .backend import stage_metrics, verify_orfs_area
    from .platforms import profile, verify_wire_readback
    from .model_samples import read_labels
    from .model_m2_live_cec_v3 import verify_proof
    from .model_m2_evaluate import measurement_identity
    from .sdc import verify_sdc
    m = read(directory/'manifest.json')
    cells = read(directory/'liberty_cells.json')['cells']
    p = profile('asap7')
    if (m['status'] != 'completed' or m['threads_per_tool'] != 4
        or sha(directory/'input.sv') != task['rtl_sha256']
        or sha(directory/'sample-contract.json') != task['sample_contract_sha256']
        or m['period_ps'] != task['period_ps'] or m['task_id'] != task['id']
        or len(m['metrics']) != 2 or {g['stage'] for g in m['metrics']} != {'synth', 'grt'}):
        raise ValueError('state task manifest mismatch/incomplete')
    metrics = []
    for stage in ('synth', 'grt'):
        reports = directory/'reports'/SUFFIX
        g = stage_metrics(reports, stage, cells, task['period_ps'], selected=p)
        g['model_labels'] = read_labels(reports/('vulsim_'+stage), directory/'sample-contract.json', g['raw_report_units']['time']['to_ps'])
        g['state_witness'] = state_witness(directory, stage, cells)
        wire = verify_wire_readback(reports/('vulsim_'+stage+'_layer_rc.tsv'), p)
        if wire is not None:
            g['wire_RC_readback'] = wire
        stem = {'synth': '1_synth', 'grt': '5_1_grt'}[stage]
        actual_sdc = directory/'results'/SUFFIX/(stem+'.sdc')
        contract = verify_sdc(actual_sdc.read_text(), p, task['period_ps'], rtl_ports((directory/'input.sv').read_text(), task['top']))
        if contract != m['sdc_contracts'][stage]:
            raise ValueError('state serialized SDC changed')
        native = read(directory/'logs'/SUFFIX/(stem+'.json'))[('synth' if stage == 'synth' else 'globalroute')+'__design__instance__area__stdcell']
        g['orfs_area_crosscheck'] = verify_orfs_area(g['cell_area_um2'], native)
        old = next(x for x in m['metrics'] if x['stage'] == stage)
        for key, value in g.items():
            if key != 'raw_reports_prefix' and value != old.get(key):
                raise ValueError('state reparsed metric differs: '+task['id']+'/'+stage+'/'+key)
        if not g['timing_coverage_complete']:
            raise ValueError('state timing coverage incomplete')
        metrics.append(g)
    with redirect_stdout(io.StringIO()):
        verify_proof(directory/'logs'/SUFFIX/'structural_cec/proof.json',
                     directory/'results'/SUFFIX/'4_before_rsz_lec.v', directory/'results'/SUFFIX/'4_after_rsz_lec.v')
    return m, metrics, measurement_identity(m)


def extract(folder, out):
    from .model_m2_state_collection_v4 import verify
    a = verify(folder)
    progress = read(folder/'progress.json')
    fitting = {t['id'] for t in a['tasks'] if t['split'] in ('train', 'validation')}
    if (progress['phase'] != 'fitting_collection_complete' or set(progress['completed']) != fitting
        or progress['active'] or progress['errors'] or progress['waiting'] or not progress['test_locked']):
        raise ValueError('complete fitting collection and locked tests required')
    cfg = read(collection.CONFIG)
    specs = {s['id']:s for s in specifications(cfg)}
    ledger = read(Ledger().path)
    audit = RawAudit(ledger['entries'])
    rows, runs, grouped = [], [], {}
    for t in a['tasks']:
        if t['split'] == 'test':
            if (folder/'runs'/t['id']).exists():
                raise ValueError('independent state test observed before freeze')
            continue
        directory = folder/'runs'/t['id']
        spec = specs[t['source_group']]
        rtl, labels = source(spec)
        c = read(directory/'sample-contract.json')
        if ((directory/'input.sv').read_text() != rtl or c['state_geometry'] != spec
            or c['labels'] != labels or c['source_group'] != t['source_group'] or c['split'] != t['split']
            or t['features'] != features(spec, t['period_ps'])):
            raise ValueError('state source/feature/split regeneration differs')
        audit.ancestry(directory)
        m, metrics, identity = reparse(directory, t)
        if identity != a['measurement_static_identity_sha256']:
            raise ValueError('state measurement differs from primitive identity')
        prior = grouped.setdefault(t['rtl_sha256'], t['split'])
        if prior != t['split']:
            raise ValueError('same state source crossed splits')
        for g in metrics:
            witness = g['state_witness']
            area = g['cell_area_um2']-witness['excluded_observer_area_um2']
            functional = witness['scoped_state_control_area_um2']
            overhead = area-functional
            if area <= 0 or overhead < -1e-6 or g['sequential_cells'] != spec['features']['state_bits']:
                raise ValueError('state bank area/count decomposition invalid')
            paths = [{'id':x['id'], 'QD_ps':x['data_delay_ps'], 'slack_ps':x['slack_ps'],
                      'H_ps':t['period_ps']-x['data_delay_ps']-x['slack_ps'],
                      'start_pin':x['start_pin'], 'end_pin':x['end_pin']} for x in g['model_labels']]
            if {x['id'] for x in paths} != {'state_data', 'state_enable', 'state_valid'}:
                raise ValueError('state path labels incomplete')
            values = [area, overhead, *[v for x in paths for v in (x['QD_ps'],x['H_ps'],x['slack_ps'])]]
            if any(not math.isfinite(x) for x in values):
                raise ValueError('nonfinite state label')
            rows.append({'id': t['id']+'/'+g['stage'], 'task_id':t['id'], 'source_group':t['source_group'],
                'split':t['split'], 'stage':g['stage'], 'period_ps':t['period_ps'], 'features':t['features'],
                'control_family':spec['enable_source_policy'], 'reset_pattern':spec['reset_pattern'],
                'state_area_um2':area, 'functional_state_control_area_um2':functional,
                'unassigned_clock_physical_port_area_um2':max(0.,overhead),
                'physical_only_area_um2':g['physical_only_area_um2'],
                'excluded_observer_area_um2':witness['excluded_observer_area_um2'], 'boundary_paths':paths,
                'whole_setup_slack_ps':g['setup_worst_slack_ps'], 'whole_hold_slack_ps':g['hold_worst_slack_ps'],
                'source_sha256':t['rtl_sha256'], 'manifest_sha256':sha(directory/'manifest.json')})
        runs.append({'task_id':t['id'], 'manifest_sha256':sha(directory/'manifest.json'),
                     'CTS_proof_sha256':sha(directory/'logs'/SUFFIX/'structural_cec/proof.json')})
    if len(rows) != 216 or Counter(r['split'] for r in rows) != {'train':144, 'validation':72}:
        raise ValueError('state fitting label coverage differs')
    result = {'version':'asap7-m2-state-fitting-dataset-v1', 'admission_path':str(folder/'admission.json'),
        'admission_sha256':sha(folder/'admission.json'), 'protocol_sha256':sha(collection.CONFIG),
        'parent_primitives_sha256':a['parent_model_sha256'],
        'measurement_static_identity_sha256':a['measurement_static_identity_sha256'],
        'test_labels_read':False, 'test_collection_locked':True, 'rows':sorted(rows,key=lambda r:r['id']),
        'support_sidecar_reconciliations':audit.support_sidecar_reconciliations,
        'runs':sorted(runs,key=lambda r:r['task_id']), 'audit':{'status':'passed',
            'source_groups':len(grouped), 'physical_runs':len(runs), 'stage_rows':len(rows),
            'path_labels':sum(len(r['boundary_paths']) for r in rows), 'paid_leaf_commands':len(audit.commands),
            'paid_leaf_ids':sorted(audit.commands),
            'raw_ancestor_manifests':{str(k):v for k,v in sorted(audit.directories.items())},
            'raw_file_hashes_checked':len(audit.hashed), 'PPA_calls':0}}
    if out.exists():
        raise ValueError('preserve prior state extraction')
    write(out, result)
    print(json.dumps(result['audit'] | {'paid_leaf_ids':'saved in dataset', 'raw_ancestor_manifests':'saved in dataset'}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    extract(args.folder.resolve(), args.out.resolve())


if __name__ == '__main__':
    main()
