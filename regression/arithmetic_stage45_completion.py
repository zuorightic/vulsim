"""Audit saved qualification stops and bounded scan completion, without EDA."""
import argparse
import ast
from collections import Counter
import inspect
from pathlib import Path
import sys
from types import FunctionType

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read, write, sha
from experiments.arithmetic_dse import model_physical_labels_v2 as labels
from experiments.arithmetic_dse.operator_stage4 import decisions, verify_sources


def audit(root, out):
    cfg = verify_sources(root)
    failures = []
    for row in read(root/'corpus/manifest.json')['sources']:
        if row['role'] == 'locked_test':
            if (root/'raw'/row['id']).exists():
                raise ValueError('locked test already touched before selection')
            continue
        history_path = root/'raw'/row['id']/'history.json'
        history = read(history_path) if history_path.exists() else []
        for point in history:
            if point['status'] != 'failed':
                continue
            if point['failure_reason'] != 'unowned physical cell':
                raise ValueError('unreviewed qualification stop: '+point['failure_reason'])
            target = point['SDC_ps']
            folder = root/'raw'/row['id']/('target-'+str(target))/'runs'/(row['id']+'-T'+str(target))
            contract, cells = read(folder/'query-contract.json'), read(folder/'liberty-pins.json')
            reports = folder/'reports/asap7/arithmetic_probe/base'
            for line in (reports/'vulsim_grt_cells.tsv').read_text().splitlines():
                master, count, area, filler, kind = line.split('\t')
                if master not in cells:
                    cells[master] = dict(sequential=False, buffer_or_inverter=False, physical_only=True,
                                         data_pins=[], pins={}, area_um2=0 if filler == '1' else float(area))
            namespace = dict(labels.read_snapshot.__globals__)
            namespace['extract'] = lambda packet, *args: packet
            capture = FunctionType(labels.read_snapshot.__code__, namespace, closure=labels.read_snapshot.__closure__)
            capture.__kwdefaults__ = labels.read_snapshot.__kwdefaults__
            packet = capture(reports/'context_grt', target, 1, cells, contract['nodes'], contract['banks'])
            clones = []
            for name, master in packet['instances'].items():
                cell = cells[master]
                if '/' in name or cell['sequential'] or cell['buffer_or_inverter'] or cell.get('physical_only') or cell.get('constant_driver'):
                    continue
                inputs = [p for p, m in cell['pins'].items() if m['direction'] == 'input']
                same_inputs = [other for other, m in packet['instances'].items() if m == master and other != name
                               and any(other.startswith(scope) for scope in contract['nodes'].values())
                               and all(packet['connections'][name+'/'+p]['net'] == packet['connections'][other+'/'+p]['net'] for p in inputs)]
                if not inputs or not same_inputs:
                    raise ValueError('unowned cell has no actual arithmetic clone witness: '+name)
                clones.append(dict(instance=name, master=master, actual_same_input_arithmetic_instances=same_inputs,
                                   pins={p: packet['connections'][name+'/'+p] for p in cell['pins']}))
            if not clones:
                raise ValueError('missing actual unowned arithmetic clone')
            try:
                labels.extract(packet, contract['nodes'], contract['banks'])
            except ValueError as error:
                if str(error) != 'unowned physical cell':
                    raise
            else:
                raise ValueError('unqualified clone accepted')
            if (folder/'grt-labels.json').exists() or any(read(folder/(s+'.command.json'))['exit_code'] for s in ('synth', 'grt')):
                raise ValueError('saved physical stage/failed-label identity differs')
            failures.append(dict(source=row['id'], role=row['role'], target_ps=target, clones=clones,
                                 prior_valid_points=sum(p['status']=='completed' for p in history),
                                 history_sha256=sha(history_path), original_failure_preserved=True,
                                 invalid_label_generated=False, raw_identity={p.name: sha(p) for p in (
                                     reports/'context_grt_instances.tsv', reports/'context_grt_connections.tsv', folder/'liberty-pins.json')}))
    pending = decisions(root, ['train', 'validation'])
    result = dict(status='passed', failures=failures, pending_source_targets=[dict(source=r['id'], target_ps=q['SDC_ps']) for _,r,_,q in pending],
                  measurement_sources=len(cfg['measurement_sources']), locked_test_untouched=True,
                  new_synth=0, new_grt=0, source_ownership_rules_changed=False)
    write(out, result)
    print(result, flush=True)


def inventory(root, run, out):
    from experiments.arithmetic_dse import operator_condition_model as inference
    bundle = read(root/'fit-v1/candidate.json')
    reports = read(run/'real-boundary.json')
    targets, queries = [], []
    for report in reports['runs']:
        reasons = Counter()
        views = []
        covered = total = 0
        for row in report['candidates']:
            missing = []
            for node in row['node_prices']:
                descriptor = node['descriptor']
                answer = inference.query(bundle, descriptor, True)
                queries.append(dict(descriptor=descriptor, allow_candidate=True))
                total += 1
                covered += answer['status'] == 'covered'
                if answer['status'] != 'covered':
                    reasons[answer['reason']] += 1
                    missing.append(dict(node=node['node'], reason=answer['reason']))
            views.append(dict(view=row['view'], covered=not missing, missing=missing))
        targets.append(dict(target_ps=report['target_period_ps'], queries=total, covered=covered,
                            views=len(views), covered_views=sum(v['covered'] for v in views),
                            missing_reasons=dict(reasons), view_coverage=views))
    # Report the unclamped predictor response required by the frozen protocol.
    # Reuse its exact source, changing only the final reporting clamp; the
    # inference module and frozen prediction behavior stay untouched.
    tree = ast.parse(inspect.getsource(inference.infer))
    tree.body[0].body[-1].value = ast.Name(id='value', ctx=ast.Load())
    tree = ast.fix_missing_locations(tree)
    namespace = dict(inference.infer.__globals__)
    exec(compile(tree, 'unclamped_prediction_diagnostic', 'exec'), namespace)
    raw = namespace['infer']
    negatives = Counter()
    for row in read(root/'fit-data.json')['rows']:
        if row['stage'] != 'grt':
            continue
        entry = bundle['operations'][row['operation']]
        for name in ('delay', 'area'):
            if raw(entry[name], row['features']) < 0:
                negatives[row['role']+'/'+row['operation']+'/'+name] += 1
    write(out, dict(status='reported', targets=targets, candidate_sha256=sha(root/'fit-v1/candidate.json'),
                    descriptor_witness_sha256=sha(run/'real-boundary.json'), node_fixture_prices_used=False,
                    raw_unclamped_negative_predictions=dict(negatives), independent_labels_read=False,
                    missing_coverage_is_not_zero_price=True, full_D_ready=False))
    write(out.with_name('D-query-native-input.json'), dict(model=bundle, queries=queries))
    print(dict(targets=[{k:v for k,v in r.items() if k!='view_coverage'} for r in targets],
               raw_unclamped_negative_predictions=dict(negatives)), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('audit', 'inventory'), nargs='?', default='audit')
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--run', type=Path)
    a = p.parse_args()
    if a.action == 'audit':
        audit(a.root.resolve(), a.out.resolve())
    else:
        inventory(a.root.resolve(), a.run.resolve(), a.out.resolve())
