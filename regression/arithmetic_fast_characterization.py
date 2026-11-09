"""Bounded-scan decisions and exclusive timing ownership, with paid raw replay."""
import argparse
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.arithmetic_dse import model_fast_scan as scan
from experiments.arithmetic_dse import model_fast_path as timing
from experiments.arithmetic_dse.model_fast_preflight import read, write, sha


def scan_checks():
    checks = []; rejected = []
    def history(response):
        rows = []
        while True:
            decision = scan.decide(rows, 'not_training'); q = decision['next_request']
            if q is None:
                return rows, decision
            delay, area, slack = response(q, len(rows))
            rows.append(dict(**q, status='completed', source_id='parameterized-source', role='not_training',
                             implementation_id='implementation-' + str(len(rows)), operator_delay_ps=delay,
                             area_um2=area, data_setup_slack_ps=slack, coverage_complete=True,
                             operator_maximum_covered=True))
    base, stable = history(lambda q, i: (600, 20, q['SDC_ps']-700))
    if not stable['stable_within_scan_envelope'] or len(base) > 10:
        raise ValueError('stable bracketed scan failed')
    checks.append('bracket_refinement_two_pressured_stable_points')
    _, result = history(lambda q, i: (100, 20, 1))
    if result['stable_within_scan_envelope'] or not any('bracket' in r for r in result['qualification_reasons']):
        raise ValueError('unpressured shell accepted')
    checks.append('positive_data_slack_never_replaced_by_negative_shell_WNS')
    _, result = history(lambda q, i: (100, 20, -1))
    if result['stable_within_scan_envelope'] or result['measured_points'] > 10:
        raise ValueError('all-failing scan accepted or unbounded')
    checks.append('all_failing_scan_stops_with_no_qualification')
    for delay in (540, 660):
        _, result = history(lambda q, i: (delay if q['phase'] == 'tighter' else 600, 20, q['SDC_ps']-700))
        if result['stable_within_scan_envelope'] or 'delay_response_exceeds_stability_band' not in result['qualification_reasons']:
            raise ValueError('nonstable delay accepted')
    checks.append('continued_improvement_and_large_regression_both_fail_stability')
    _, result = history(lambda q, i: (600, 20, 1 if q['phase'] == 'tighter' else q['SDC_ps']-700))
    if not result['nonmonotonic_data_feasibility'] or result['stable_within_scan_envelope']:
        raise ValueError('nonmonotonic data feasibility ignored')
    checks.append('nonmonotonic_feasibility_is_retained_and_unqualified')
    _, result = history(lambda q, i: ((630, 1, q['SDC_ps']-700) if i == 0 else
                                    (630.000001, 0.5, q['SDC_ps']-700) if i == 1 else (600, 10, q['SDC_ps']-700)))
    if result['provisional_pair']['implementation_id'] != 'implementation-0' or result['provisional_pair']['operator_delay_ps'] != 630:
        raise ValueError('5 percent exact boundary or paired selection differs')
    checks.append('five_percent_inclusive_exact_decimal_and_same_implementation_pair')
    first = copy.deepcopy(base[:1]); first[0] = {k: v for k, v in first[0].items() if k in ('phase','ABC_ps','SDC_ps','source_id','role')}
    first[0].update(status='failed', failure_reason='timeout retained')
    result = scan.decide(first, 'not_training')
    if result['next_request'] or result['provisional_pair'] or result['stable_within_scan_envelope']:
        raise ValueError('failure retried or zero label invented')
    checks.append('failed_point_stops_no_retry_no_numerical_label')
    _, result = history(lambda q, i: (100,20,q['SDC_ps']-700))
    if result['stable_within_scan_envelope'] or 'internal_operator_paths_not_both_pressured' not in result['qualification_reasons']:
        raise ValueError('service/boundary violation falsely qualifies unpressured operator')
    checks.append('boundary_H_cannot_substitute_for_internal_operator_pressure')
    def reject(name, mutate):
        rows = copy.deepcopy(base); mutate(rows)
        try:
            scan.decide(rows, 'not_training')
        except ValueError:
            rejected.append(name)
        else:
            raise ValueError('invalid scan accepted: ' + name)
    reject('ABC_differs_from_SDC', lambda rows: rows[0].update(ABC_ps=750))
    reject('skipped_clock_request', lambda rows: rows[0].update(ABC_ps=1000, SDC_ps=1000))
    reject('mixed_source', lambda rows: rows[1].update(source_id='other'))
    reject('mixed_role', lambda rows: rows[1].update(role='train'))
    reject('duplicate_implementation', lambda rows: rows[1].update(implementation_id=rows[0]['implementation_id']))
    reject('uncovered_operator_maximum', lambda rows: rows[0].update(operator_maximum_covered=False))
    reject('incomplete_coverage', lambda rows: rows[0].update(coverage_complete=False))
    reject('nonfinite_delay', lambda rows: rows[0].update(operator_delay_ps=float('nan')))
    reject('zero_area', lambda rows: rows[0].update(area_um2=0))
    reject('boolean_target', lambda rows: rows[0].update(ABC_ps=True, SDC_ps=True))
    reject('unexpected_label_or_identity_field', lambda rows: rows[0].update(case_id='MAC_32'))
    reject('post_terminal_point', lambda rows: rows.append(copy.deepcopy(rows[-1])))
    # Explore both possible measured data-feasibility outcomes for every request.
    # No monotonicity assumption enters this audit of the finite state machine.
    leaves = []; seen = 0
    def walk(rows):
        nonlocal seen
        seen += 1; q = scan._next(rows, scan.policy())
        if q is None:
            leaves.append(len(rows)); return
        if len(rows) >= 10 or q['ABC_ps'] != q['SDC_ps'] or q['SDC_ps'] in {r['SDC_ps'] for r in rows}:
            raise ValueError('bounded state-machine invariant failed')
        for slack in (-1, 1):
            walk(rows + [dict(**q, status='completed', data_setup_slack_ps=slack)])
    walk([])
    checks.append('all_binary_data_feasibility_traces_are_finite_without_duplicate_targets')
    return dict(checks=checks, rejected=rejected, exhaustive_states=seen, exhaustive_terminal_scans=len(leaves),
                maximum_points_seen=max(leaves), example_stable_history=base, example_stable_decision=stable,
                fixtures_are_measured_labels=False)


def path_checks():
    ff = dict(sequential=True, buffer_or_inverter=False, data_pins=['D'],
              pins={'D':dict(direction='input'), 'Q':dict(direction='output')})
    gate = dict(sequential=False, buffer_or_inverter=True, data_pins=[],
                pins={'A':dict(direction='input'), 'Y':dict(direction='output')})
    pins = {'FF':ff, 'G':gate}
    instances = {'launch/q':'FF', 'launch/repair':'G', 'n0/g':'G', 'n1/g':'G', 'capture/d':'FF'}
    points = [('launch/q/Q',10), ('launch/repair/A',12), ('launch/repair/Y',20),
              ('n0/g/A',23), ('n0/g/Y',53), ('n1/g/A',58), ('n1/g/Y',98), ('capture/d/D',100)]
    names = ('a','a','b','b','c','c','d','d')
    nets = {n:dict(net=v, direction=pins[instances[n.rsplit('/',1)[0]]]['pins'][n.rsplit('/',1)[1]]['direction'])
            for (n,_),v in zip(points,names)}
    def query(rows=points, wires=nets, scopes=None):
        return timing.decompose(rows, points[0][0], points[-1][0], instances,pins,wires,scopes or {'node0':'n0/','node1':'n1/'})
    result = query()
    if (result['Q_to_D_ps'], result['node_delay_ps'], result['non_node_delay_ps']) != (90, {'node0':30, 'node1':40}, 20):
        raise ValueError('serial path ownership double counts or loses service/edge delay')
    checks = ['two_serial_nodes_plus_service_and_three_wires_conserve_Q_to_D']
    failed = []
    def reject(name, fn):
        try:
            fn()
        except ValueError:
            failed.append(name)
        else:
            raise ValueError('invalid path accepted: '+name)
    changed = copy.deepcopy(nets); changed['n1/g/A']['net'] = 'unconnected'
    reject('path_jumps_between_disconnected_nets', lambda: query(wires=changed))
    reject('overlapping_node_scopes', lambda: query(scopes={'x':'n0/','y':'n0/g/'}))
    reject('unknown_node_scope', lambda: query(scopes={'x':'missing/'}))
    changed_points = points.copy(); changed_points[4] = (changed_points[4][0], 5)
    reject('negative_timing_step', lambda: query(rows=changed_points))
    changed_points = points.copy(); changed_points[3] = ('n0/g/Z',23)
    reject('unknown_Liberty_pin', lambda: query(rows=changed_points))
    changed = copy.deepcopy(nets); changed['n1/g/A']['direction'] = 'output'
    reject('Liberty_connectivity_disagreement', lambda: query(wires=changed))
    return dict(checks=checks, rejected=failed, fixtures_are_physical_measurements=False)


def verify(out, replay=None):
    out.mkdir(parents=True, exist_ok=False)
    result = dict(version='arithmetic-fast-characterization-software-v1', scan=scan_checks(), paths=path_checks(),
                  PPA_calls=0, fitting_allowed=False, physical_admission_allowed=False, full_D_ready=False)
    witnesses = []
    if replay:
        admission = read(replay/'admission.json'); pins = read(replay/'liberty-pins.json')
        for relative, h in admission['sources'].items():
            if sha(replay/'source'/relative) != h:
                raise ValueError('frozen diagnostic producer changed')
        for task in admission['tasks']:
            folder = Path(task['inherit_completed']['directory']) if task.get('inherit_completed') else replay/'runs'/task['id']
            manifest = read(folder/'manifest.json')
            for name, h in manifest['evidence_sha256'].items():
                if sha(folder/name) != h:
                    raise ValueError('original physical artifact differs')
            for stage in ('synth','grt'):
                label_file = folder/('fast-'+stage+'-observations.json'); observation = read(label_file)
                prefix = folder/'reports/asap7/arithmetic_probe/base'/('vulsim_'+stage)
                for label in observation['paths']:
                    if not label['id'].startswith('data'):
                        continue
                    detail = timing.from_saved(prefix,label,pins,{'operator':'core/'})
                    raw_points = [(n,float(v)) for n,v in (line.split('\t') for line in
                        Path(str(prefix)+'_reference_'+label['id']+'_points.tsv').read_text().splitlines())]
                    raw_instances = dict(line.split('\t')[:2] for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines())
                    raw_instances = {timing.canonical(n): master for n,master in raw_instances.items()}
                    needed = {timing.canonical(n).rsplit('/',1)[0] for n,_ in raw_points if '/' in n}
                    # Exclude clock-path prefix before the registered launch Q.
                    index = next(i for i,(n,_) in enumerate(raw_points) if timing.canonical(n)==timing.canonical(label['start_pin']))
                    raw_points = raw_points[index:];needed = {timing.canonical(n).rsplit('/',1)[0] for n,_ in raw_points}
                    raw_instances = {n:raw_instances[n] for n in needed}
                    raw_nets = timing.connections(str(prefix)+'_reference_connections.tsv')
                    portable_input = dict(points=raw_points,start=label['start_pin'],end=label['end_pin'],
                        instances=raw_instances,pins={n:pins[n] for n in set(raw_instances.values())},
                        nets={timing.canonical(n):raw_nets[timing.canonical(n)] for n,_ in raw_points},
                        node_scopes={'operator':'core/'},time_to_ps=1)
                    entry = dict(task_id=task['id'], stage=stage, source_role=task['source_role'],
                                 original_observation_sha256=sha(label_file), original_label=label, decomposition=detail,
                                 replay_input=portable_input)
                    witnesses.append(entry)
        result.update(raw_path_count=len(witnesses), raw_source_role='not_training', diagnostic_labels_used_for_fitting=False,
                      operator_maximum_coverage_qualified=False,
                      replay_admission_sha256=sha(replay/'admission.json'))
    payload = json.dumps(witnesses,sort_keys=True,separators=(',',':')).encode()
    (out/'path-witnesses.json.gz').write_bytes(gzip.compress(payload,mtime=0))
    write(out/'proof.json',result)
    write(out/'witness-summary.json',[
        dict(task_id=r['task_id'],stage=r['stage'],path_id=r['original_label']['id'],
             Q_to_D_ps=r['decomposition']['Q_to_D_ps'], operator_internal_ps=r['decomposition']['node_delay_ps']['operator'],
             boundary_and_wires_ps=r['decomposition']['non_node_delay_ps']) for r in witnesses])
    print(json.dumps(dict(status='passed', scan_checks=len(result['scan']['checks']), path_checks=len(result['paths']['checks']),
                         negatives=len(result['scan']['rejected'])+len(result['paths']['rejected']),
                         binary_terminal_scans=result['scan']['exhaustive_terminal_scans'], raw_paths=len(witnesses), PPA_calls=0)),flush=True)


def run(out, replay):
    from experiments.arithmetic_dse.budget import Ledger, usage
    from experiments.arithmetic_dse.processes import run_command
    out.mkdir(parents=True, exist_ok=False); ledger = Ledger(); before = read(ledger.path)
    source_paths = [Path(__file__), Path(scan.__file__), Path(timing.__file__), scan.CONFIG]
    for path in source_paths:
        dest=out/'source'/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
    ctx = dict(target_platform='asap7',admission_id=out.name,task_id='fast-characterization-software')
    command = [sys.executable,'-B',str(Path(__file__)),'verify','--out',str(out/'verification'),'--replay',str(replay)]
    env = os.environ.copy(); env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4')
    with ledger.job(ctx):
        reservation=ledger.reserve(None,180,4,'fast_characterization_software_and_saved_raw_replay',command,out/'verify',context=ctx)
        record=run_command(command,out,'verify',180,env,8192,cpu_limit_s=reservation['CPU_time_s']);ledger.finish(reservation,record)
        write(out/'commands.json',[dict(**record,budget_reservation_id=reservation['id'])])
    after=read(ledger.path)
    write(out/'resource-increment.json',dict(entries=after['entries'][len(before['entries']):],usage=usage(after['entries']),PPA_calls=0))
    print(Path(record['log']).read_text()[-3000:],flush=True)
    if record['exit_code']:
        raise RuntimeError('characterization software failed; evidence and costs retained')
    write(out/'manifest.json',dict(sources={str(p.relative_to(ROOT)):sha(p) for p in source_paths},
                                 artifacts={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()},
                                 source_role='software_preflight_only_not_training', PPA_calls=0))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('run','verify'));parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--replay',type=Path,required=True);args=parser.parse_args()
    if args.action=='run':
        run(args.out.resolve(),args.replay.resolve())
    else:
        verify(args.out.resolve(),args.replay.resolve())
