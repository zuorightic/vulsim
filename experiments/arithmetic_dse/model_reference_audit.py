"""Reparse the settled reference cohort; preserve failures, never fit or set H_ref."""
import argparse
from collections import Counter
from contextlib import redirect_stdout
from fractions import Fraction
import io
import json
from pathlib import Path

from .budget import Ledger, cpu_seconds
from .model_collection import sha, write
from .model_m2_state_replay import RawAudit
from .model_reference_collection import ROOT, SUFFIX, CONFIG, read
from .model_reference_collection_v3 import verify
from .model_reference_labels import liberty
from .model_reference_labels_v2 import labels, partition
from .model_reference_samples import spec, source


class ReferenceAudit(RawAudit):
    def ancestry(self, directory, visiting=None):
        directory = Path(directory).resolve()
        if directory in self.directories:
            return
        visiting = set() if visiting is None else visiting
        if directory in visiting:
            raise ValueError('cyclic reference ancestry')
        visiting = visiting | {directory}
        m = read(directory/'manifest.json')
        admission = directory.parent.parent/'admission.json'
        owner = self.digest(admission)
        a = read(admission)
        if m['admission_id'] != a['id']:
            raise ValueError('reference physical owner differs')
        for command in m['commands']:
            e = self.entries[command['budget_reservation_id']]
            if (e['status'] != 'completed' or e['command'] != command['command']
                or e.get('admission_sha256') != owner or e.get('task_id') != m['task_id']
                or e.get('admission_id') != a['id'] or command['exit_code']
                or command['cleanup']['remaining_live_pids'] or command['timed_out']
                or command['memory_limit_exceeded'] or command['CPU_limit_exceeded']
                or e['walltime_s'] != command['walltime_s']
                or abs(e['CPU_time_s']-cpu_seconds(command['gnu_time'])) > 1e-8):
                raise ValueError('reference physical command unpaid, incomplete or mismatched')
            saved = read(Path(command['log'].removesuffix('.log')+'.command.json'))
            if saved not in (command, {k:v for k,v in command.items() if k != 'budget_reservation_id'}):
                raise ValueError('reference command sidecar differs')
            self.digest(command['log'])
            self.digest(command['gnu_time'])
            self.commands.add(e['id'])
        for name, h in m.get('evidence_sha256', {}).items():
            if self.digest(directory/name) != h:
                raise ValueError('reference raw evidence changed: '+name)
        for name, h in m.get('source_sha256', {}).items():
            local = directory/'source'/name
            if local.exists() and self.digest(local) != h:
                raise ValueError('reference producer snapshot changed: '+name)
        for name, h in m['files_sha256'].items():
            if self.digest(name) != h:
                raise ValueError('reference physical file changed: '+name)
        for asset in [*m['tools'].values(), *m['libraries']]:
            if self.digest(asset['path']) != asset['sha256']:
                raise ValueError('reference physical tool/library changed')
        signature = tuple((v['path'],v['sha256']) for v in m['libraries'])
        if signature not in self.library_tables:
            from .platforms import library_data, profile
            libs, table = library_data([Path(v['path']) for v in m['libraries']], profile('asap7'))
            if libs != m['libraries']:
                raise ValueError('reference Liberty identity differs')
            self.library_tables[signature] = table
        if read(directory/'liberty_cells.json')['cells'] != self.library_tables[signature]:
            raise ValueError('reference Liberty area/FF table differs')
        reuse = m.get('checkpoint_reuse')
        if reuse:
            original = Path(reuse['source_run'])
            if (reuse['mode'] != 'exact_paid_synth_ODB_netlist_and_SDC'
                or not reuse['old_ODB_or_SDC_copied'] or reuse['Yosys_ABC_reexecuted']
                or self.digest(original/'manifest.json') != reuse['source_manifest_sha256']):
                raise ValueError('reference synthesis checkpoint identity differs')
            for name, h in reuse['files_sha256'].items():
                if (self.digest(original/'results'/SUFFIX/name) != h
                    or self.digest(directory/'results'/SUFFIX/name) != h):
                    raise ValueError('reference copied synthesis artifact differs')
            if 'native_synth_metric_sha256' in reuse:
                h = reuse['native_synth_metric_sha256']
                if (self.digest(reuse['native_synth_metric_source']) != h
                    or self.digest(directory/'logs'/SUFFIX/'1_synth.json') != h):
                    raise ValueError('reference inherited native synthesis metric differs')
            for name in ('input.sv','reference-contract.json'):
                if self.digest(original/name) != self.digest(directory/name):
                    raise ValueError('reference checkpoint source/contract differs')
            if any(e['stage'] == 'synth' for e in (self.entries[c['budget_reservation_id']] for c in m['commands'])):
                raise ValueError('reference synthesis checkpoint unexpectedly reexecuted')
            self.ancestry(original, visiting)
        if m['status'] != 'completed':
            reason = m.get('failure_reason', '')
            allowed = ('reference unknown path cell', 'unattributed functional cell: _1_')
            if not (m['status'] == 'failed' and (reason in allowed or '1_synth.json' in reason)):
                raise ValueError('unexpected failed reference ancestor')
            if any(self.entries[c['budget_reservation_id']]['stage'] == 'grt' for c in m['commands']):
                raise ValueError('reader-only predecessor unexpectedly routed')
        self.directories[directory] = self.digest(directory/'manifest.json')


def reparse(directory, task, pin_cells):
    from .backend import stage_metrics, verify_orfs_area
    from .model_m2_evaluate import measurement_identity
    from .model_m2_live_cec_v3 import verify_proof
    from .platforms import profile, verify_wire_readback
    from .sdc import verify_sdc, rtl_ports
    m = read(directory/'manifest.json')
    p = profile('asap7')
    cells = read(directory/'liberty_cells.json')['cells']
    s = spec(task['id'])
    if (m['status'] != 'completed' or m['task_id'] != task['id']
        or m['threads_per_tool'] != 4 or m['memory_limit_MiB'] != 8192
        or m['period_ps'] != task['period_ps'] or m['abc_target_ps'] != 1500
        or m['data_role'] != 'microbenchmark_reference_only'
        or sha(directory/'input.sv') != task['rtl_sha256']
        or sha(directory/'reference-contract.json') != task['contract_sha256']
        or len(m['metrics']) != 2 or [g['stage'] for g in m['metrics']] != ['synth','grt']):
        raise ValueError('reference task/source/context differs')
    metrics = []
    for stage in ('synth','grt'):
        reports = directory/'reports'/SUFFIX
        g = stage_metrics(reports, stage, cells, task['period_ps'], selected=p)
        prefix = reports/('vulsim_'+stage)
        ownership, instances, _ = partition(prefix, pin_cells, p,
            expected={n:s[n+'_bits'] for n in ('input_service','native_state','external_state')})
        owner_path = directory/('reference-'+stage+'-ownership.json')
        if ownership != read(owner_path) or abs(g['cell_area_um2']-ownership['total_area_um2']) > 1e-6:
            raise ValueError('reference unique physical ownership does not reproduce')
        g['reference_paths'] = labels(prefix, s, task['period_ps'], g['raw_report_units']['time']['to_ps'], pin_cells, instances)
        g['reference_owner_area_um2'] = ownership['owner_area_um2']
        g['reference_owner_FF_bits'] = ownership['owner_FF_bits']
        g['reference_ownership_sha256'] = sha(owner_path)
        rc = verify_wire_readback(Path(str(prefix)+'_layer_rc.tsv'), p)
        if rc is not None:
            g['wire_RC_readback'] = rc
        stem = {'synth':'1_synth','grt':'5_1_grt'}[stage]
        contract = verify_sdc((directory/'results'/SUFFIX/(stem+'.sdc')).read_text(), p,
            task['period_ps'], rtl_ports((directory/'input.sv').read_text(), 'ModelBundle'))
        if contract != m['sdc_contracts'][stage]:
            raise ValueError('reference actual SDC does not reproduce')
        native = read(directory/'logs'/SUFFIX/(stem+'.json'))[
            ('synth' if stage == 'synth' else 'globalroute')+'__design__instance__area__stdcell']
        g['orfs_area_crosscheck'] = verify_orfs_area(g['cell_area_um2'], native)
        old = next(v for v in m['metrics'] if v['stage'] == stage)
        for key, value in g.items():
            if key != 'raw_reports_prefix' and old.get(key) != value:
                raise ValueError('reference raw replay differs: '+task['id']+'/'+stage+'/'+key)
        if not g['timing_coverage_complete']:
            raise ValueError('reference timing coverage incomplete')
        metrics.append(g)
    if read(directory/'metrics.json') != m['metrics']:
        raise ValueError('reference metric sidecar differs')
    with redirect_stdout(io.StringIO()):
        verify_proof(directory/'logs'/SUFFIX/'structural_cec/proof.json',
            directory/'results'/SUFFIX/'4_before_rsz_lec.v',directory/'results'/SUFFIX/'4_after_rsz_lec.v')
    return m, metrics, measurement_identity(m)


def data_paths(requirements, rows):
    """Original-DAG longest paths only; no H rule or numerical target selection."""
    prices = {r['task_id']:next(p['reference_data_delay_ps'] for p in r['paths'] if p['id']=='data')
              for r in rows if r['stage']=='grt'}
    result = {}
    for name, case in requirements['cases'].items():
        values, traces = {}, {}
        for node in case['reference_graph']:
            if node['id'] in values or any(d not in values for d in node['deps']):
                raise ValueError('reference DAG order or identity invalid')
            previous = max(node['deps'], key=lambda d:values[d]) if node['deps'] else None
            price = Fraction(str(prices[node['primitive']])) if node['primitive'] else Fraction(0)
            values[node['id']] = (values[previous] if previous else Fraction(0))+price
            traces[node['id']] = (traces[previous] if previous else [])+[node['id']]
        end = max(values, key=values.get)
        result[name] = {'L':case['L'], 'D_ref_ps':str(values[end]), 'D_ref_decimal_ps':float(values[end]),
                        'critical_node_path':traces[end], 'required_labels':case['required_labels'],
                        'H_ref_ps':None, 'T_target_ps':None}
    return result


def extract(folder, requirements, out):
    if out.exists():
        raise ValueError('preserve previous reference audit')
    a = verify(folder)
    progress = read(folder/'progress.json')
    if (progress['phase'] != 'reference_collection_complete' or progress['active']
        or progress['waiting'] or progress['errors']
        or set(progress['completed']) != {t['id'] for t in a['tasks']}):
        raise ValueError('settled complete reference cohort required')
    ledger = read(Ledger().path)
    audit = ReferenceAudit(ledger['entries'])
    cfg = read(CONFIG)
    pin_cells = read(a['Liberty_pin_table'])
    first = read(folder/'runs'/a['tasks'][0]['id']/'manifest.json')
    base_cells = read(folder/'runs'/a['tasks'][0]['id']/'liberty_cells.json')['cells']
    if liberty(first['libraries'], base_cells) != pin_cells:
        raise ValueError('reference actual Liberty pin/ff/function table differs')
    atom = Path(read(a['software_proof_path'])['atom_path']).read_text()
    rows, runs = [], []
    for task in a['tasks']:
        directory = folder/'runs'/task['id']
        if source(spec(task['id']), atom) != (directory/'input.sv').read_text():
            raise ValueError('reference executable source does not regenerate')
        audit.ancestry(directory)
        m, metrics, identity = reparse(directory, task, pin_cells)
        if (identity != a['measurement_static_identity_sha256']
            or m['reference_admission_sha256'] != sha(folder/'admission.json')):
            raise ValueError('reference common physical identity differs')
        for g in metrics:
            rows.append({'task_id':task['id'], 'stage':g['stage'], 'paths':g['reference_paths'],
                'owner_area_um2':g['reference_owner_area_um2'], 'owner_FF_bits':g['reference_owner_FF_bits'],
                'setup_slack_ps':g['setup_worst_slack_ps'], 'hold_slack_ps':g['hold_worst_slack_ps'],
                'hold_review_required':g['hold_review_required'], 'timing_coverage_complete':True,
                'manifest_sha256':sha(directory/'manifest.json')})
        runs.append({'id':task['id'], 'directory':str(directory), 'manifest_sha256':sha(directory/'manifest.json'),
                     'checkpoint_reused':bool(m.get('checkpoint_reuse'))})
    # The v2 failed read-only snapshots are genuine paid work, retained separately
    # from the synthesis ancestry and never promoted to numeric reference labels.
    predecessor = Path(a['support_predecessor_admission']).parent
    for key in a['capacity_pilots']:
        audit.ancestry(predecessor/'runs'/key)
    req = read(requirements)
    expected = read(ROOT/'experiments/arithmetic_dse/configs/model_asap7_m2_joint_requirements_v1.json')
    if sha(requirements) != expected['reference_requirements_sha256'] or req['unique_labels'] != cfg['labels']:
        raise ValueError('original reference graph/label requirements changed')
    counts = Counter(audit.entries[i]['stage'] for i in audit.commands)
    if len(rows) != 34 or counts['synth'] != 17 or counts['grt'] != 17:
        raise ValueError('reference stage/call totals differ or synthesis was repeated')
    result = {'version':'asap7-reference-raw-audit-v1', 'status':'passed',
        'admission_path':str(folder/'admission.json'), 'admission_sha256':sha(folder/'admission.json'),
        'protocol_sha256':sha(CONFIG), 'requirements_path':str(requirements), 'requirements_sha256':sha(requirements),
        'measurement_static_identity_sha256':a['measurement_static_identity_sha256'],
        'rows':rows, 'runs':runs, 'original_DAG_data_references':data_paths(req, rows),
        'audit':{'physical_runs':17, 'stage_rows':34, 'path_labels':sum(len(r['paths']) for r in rows),
            'paid_leaf_commands':len(audit.commands), 'paid_leaf_ids':sorted(audit.commands),
            'synth':counts['synth'], 'grt':counts['grt'], 'support':counts[None],
            'failed_reader_runs_retained':6, 'reused_synthesis_checkpoints':3,
            'raw_file_hashes_checked':len(audit.hashed),
            'ancestor_manifests':{str(k):v for k,v in audit.directories.items()}},
        'producer_sha256':sha(Path(__file__)), 'source_role':'microbenchmark_reference_only',
        'model_fit_allowed':False, 'formal_PPA_read':False, 'PPA_calls':0,
        'H_ref_aggregation_rule_frozen':False, 'numerical_targets_frozen':False, 'full_D_ready':False}
    write(out, result)
    print(json.dumps({k:result[k] for k in ('status','audit','numerical_targets_frozen','PPA_calls')}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, required=True)
    parser.add_argument('--requirements', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    extract(args.folder.resolve(), args.requirements.resolve(), args.out.resolve())
