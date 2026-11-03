"""Independent, single-consumption testing and bounded interval model release.

Test labels never participate in predictor or margin selection. Publication
replays the frozen decision and does not change any fitted numeric parameter.
"""
import argparse
import copy
import json
import math
from pathlib import Path

from .model_collection import sha, write, verify_test_release
from .model_mul_intervals import CONFIG, features, key, infer
from .model_mul_interval_fit import extract, quality
from .model_training import metric

ROOT = Path(__file__).resolve().parents[2]


def validate_dataset(path, splits, selection_freeze=None):
    """Require all declared samples and stages, tied to their actual labels."""
    path = Path(path)
    data = json.loads(path.read_text())
    admission = Path(data['admission_path'])
    plan = json.loads(admission.read_text())
    if (data['version'] != 'arithmetic-mul-interval-dataset-v1'
            or data['admission_sha256'] != sha(admission)
            or data['protocol_sha256'] != sha(CONFIG)
            or plan['supplemental_protocol']['sha256'] != sha(CONFIG)
            or data.get('failures') or not data.get('rows')):
        raise ValueError('incomplete or changed interval dataset/admission/protocol')
    if 'test' in splits:
        verify_test_release(admission, selection_freeze,
                            {t['platform'] for t in plan['tasks'] if t['split'] == 'test'})
    expected = {}
    for task in plan['tasks']:
        if task['split'] not in splits:
            continue
        contract_path = Path(task['sample_contract'])
        if sha(contract_path) != task['sample_contract_sha256'] or sha(task['rtl']) != task['rtl_sha256']:
            raise ValueError('changed frozen sample source or contract')
        contract = json.loads(contract_path.read_text())
        for spec in contract['labels']:
            for stage in ('synth', 'grt') if task['stage'] == 'grt' else ('synth',):
                identity = task['id'] + '/' + spec['id'] + '/' + stage
                if identity in expected:
                    raise ValueError('duplicate declared interval sample')
                expected[identity] = (task, spec, stage)
    rows = data['rows']
    if len({r['id'] for r in rows}) != len(rows) or {r['id'] for r in rows} != set(expected):
        raise ValueError('incomplete or duplicate interval sample/stage coverage')
    for row in rows:
        task, spec, stage = expected[row['id']]
        static = features(spec)
        if (row['split'] != task['split'] or row['stage'] != stage
                or row['platform'] != task['platform'] or json.dumps(row['spec'],sort_keys=True) != json.dumps(spec,sort_keys=True)
                or row['source_sha256'] != task['rtl_sha256']
                or row['contract_sha256'] != task['sample_contract_sha256']
                or row['profile_sha256'] != task['profile_sha256']
                or row['period_ps'] != task['period_ps']
                or row['abc_target_ps'] != task['abc_target_ps']
                or row['features'].keys() != static.keys()
                or any(type(row['features'][k]) is not type(v) or row['features'][k] != v for k,v in static.items())
                or row['interval_key'] != key(spec)):
            raise ValueError('interval row differs from frozen task/graph features')
        for label in ('delay_ps', 'comb_area_um2'):
            if type(row[label]) not in (int, float) or not math.isfinite(row[label]) or row[label] <= 0:
                raise ValueError('positive finite physical interval label required')
        for label, capacity in [('launch_DFFs', sum(spec['input_widths'])), ('capture_DFFs', spec['capture_width'])]:
            if type(row[label]) is not int or not 0 < row[label] <= capacity:
                raise ValueError('invalid actual interval boundary count')
    # Re-extract actual manifests and mapped instances, not a second fitted or
    # synthetic dataset. The extraction gate precedes any independent test read.
    actual = extract(admission.parent, splits, selection_freeze)
    if json.dumps(data,sort_keys=True) != json.dumps(actual,sort_keys=True):
        raise ValueError('interval dataset differs from actual measurement replay')
    return data, plan


def frozen_inputs(selection):
    selection = Path(selection)
    frozen = json.loads(selection.read_text())
    data = Path(frozen['fitting_dataset_path'])
    fit_data = json.loads(data.read_text())
    admission = Path(fit_data['admission_path'])
    platforms = [m['platform'] for m in frozen['models']]
    verify_test_release(admission, selection, platforms)
    if not frozen.get('training_sources'):
        raise ValueError('missing executed training source snapshot')
    for name, digest in frozen['training_sources'].items():
        if sha(ROOT/name) != digest or sha(selection.parent/'training-source'/name) != digest:
            raise ValueError('changed frozen training/evaluation implementation: ' + name)
    models = {}
    reports = {}
    for item in frozen['models']:
        platform = item['platform']
        report_path = selection.parent/(platform+'.fit.json')
        if sha(report_path) != item['fit_report_sha256']:
            raise ValueError('changed frozen interval fitting report')
        bundle = json.loads((selection.parent/(platform+'.candidate.json')).read_text())
        models[platform] = bundle
        reports[platform] = json.loads(report_path.read_text())
        if bundle['interval_base_model_sha256'] != item['base_model_sha256']:
            raise ValueError('changed qualified base model identity')
        if reports[platform]['grt']['model'] != bundle['stages']['grt']['mul_interval_model']:
            raise ValueError('fitting report and consumed candidate use different interval predictors')
    return frozen, admission, models, reports


def predictions(entry, row):
    return {'delay_ps': infer(entry['delay'], row['features']) * entry['validation_delay_scale'],
            'comb_area_um2': infer(entry['area'], row['features'])}


def ranking(rows, interval_models):
    """Only compare equivalent full-template half/quarter functions here.

    Intermediate intervals can have different inputs and outputs. Their ranking
    is not interpreted as candidate choice or whole-pipeline PPA improvement.
    """
    groups = {}
    for row in rows:
        spec = row['spec']
        if spec['first'] == 0 and spec['last'] == spec['groups']-1:
            groups.setdefault((spec['width'], spec['result_shape']), {})[spec['configuration']] = row
    records = []
    for (width, shape), pair in sorted(groups.items()):
        if set(pair) != {'half', 'quarter'}:
            raise ValueError('missing equivalent full-template ranking pair')
        a, b = pair['half'], pair['quarter']
        pa = predictions(interval_models[a['interval_key']], a)
        pb = predictions(interval_models[b['interval_key']], b)
        for label in ('delay_ps', 'comb_area_um2'):
            def order(x, y):
                return 0 if x == y else -1 if x < y else 1
            observed, predicted = order(a[label], b[label]), order(pa[label], pb[label])
            records.append({'width': width, 'result_shape': shape, 'label': label,
                            'half_observed': a[label], 'quarter_observed': b[label],
                            'half_predicted': pa[label], 'quarter_predicted': pb[label],
                            'observed_order': observed, 'predicted_order': predicted,
                            'order_matches': observed == predicted})
    return {'scope': 'equivalent full template half versus quarter at the fixed reference context; no state or pipeline ranking claim',
            'denominator': len(records), 'matching_pairs': sum(r['order_matches'] for r in records),
            'records': records, 'quality_gate': 'diagnostic; no post-test threshold introduced'}


def compute_report(rows, models, fits):
    cfg = json.loads(CONFIG.read_text())
    platforms = {}
    for platform, bundle in models.items():
        stages = {}
        for stage in cfg['stages']:
            stage_rows = [r for r in rows if r['platform'] == platform and r['stage'] == stage]
            model = fits[platform][stage]['model']
            intervals = model['intervals']
            if {r['interval_key'] for r in stage_rows} != set(intervals):
                raise ValueError('independent test interval class coverage differs from fitted model')
            entries = {}
            for name, entry in intervals.items():
                subset = [r for r in stage_rows if r['interval_key'] == name]
                if len(subset) != len(cfg['splits']['test']) or {r['features']['width'] for r in subset} != set(cfg['splits']['test']):
                    raise ValueError('incomplete independent test widths per interval')
                if not entry['validation_ready']:
                    entries[name] = {'status': 'failed_validation', 'independent_test_evaluated': False}
                    continue
                result = quality(entry, subset, bundle['mapping_abc_target_ps'])
                pred = [predictions(entry, r) for r in subset]
                result['conservative_rejections'] = sum(
                    r['delay_ps'] <= r['delay_ps']*ratio < p['delay_ps']
                    for r, p in zip(subset, pred) for ratio in cfg['feasibility_ratios'])
                result['samples'] = len(subset)
                result['predictions'] = [{'id': r['id'], **p} for r, p in zip(subset, pred)]
                entries[name] = result
            tested = [r for r in stage_rows if intervals[r['interval_key']]['validation_ready']]
            all_predictions = [predictions(intervals[r['interval_key']],r) for r in tested]
            aggregate = {'tested_samples':len(tested),'interval_classes':len(intervals),
                         'false_feasible':sum(e.get('false_feasible',0) for e in entries.values()),
                         'denominator':sum(e.get('denominator',0) for e in entries.values()),
                         'conservative_rejections':sum(e.get('conservative_rejections',0) for e in entries.values()),
                         'acceptance_rule':'original frozen gates must pass for every interval class'}
            if tested:
                aggregate['delay']=metric([r['delay_ps'] for r in tested],[p['delay_ps'] for p in all_predictions],max(1,bundle['mapping_abc_target_ps']*.001))
                aggregate['area']=metric([r['comb_area_um2'] for r in tested],[p['comb_area_um2'] for p in all_predictions],1e-4)
            stages[stage] = {'status': 'passed' if all(e['status'] == 'passed' for e in entries.values()) else 'failed',
                             'base_stage_available': stage in bundle['stages'], 'samples': len(stage_rows),
                             'intervals': entries, 'aggregate':aggregate,
                             'ranking':ranking(stage_rows, intervals) if len(tested)==len(stage_rows) else {'status':'not_evaluated_failed_validation'}}
        platforms[platform] = {'quality_status': stages['grt']['status'], 'stages': stages}
    return platforms


def evaluate(data, selection, out):
    data, selection, out = map(Path, (data, selection, out))
    marker = selection.parent/'independent-test-consumption.json'
    if marker.exists():
        raise ValueError('independent test already consumed; preserve result and use verify, never refit/retest in place')
    frozen, admission, models, fits = frozen_inputs(selection)
    if not data.is_file():
        raise ValueError('independent test dataset does not exist')
    if out.exists():
        raise ValueError('independent test output must be a new directory')
    # Exclusive claim beside the immutable selection prevents using a second
    # output directory to silently repeat a test after seeing its results.
    with marker.open('x') as stream:
        json.dump({'status': 'started', 'selection_sha256': sha(selection),
                   'test_dataset_sha256': sha(data), 'output': str(out.resolve())}, stream, indent=2)
    out.mkdir(parents=True)
    try:
        dataset, plan = validate_dataset(data, ['test'], selection)
        if dataset['admission_sha256'] != sha(admission):
            raise ValueError('independent test admission differs from selection')
        report = {'version': 'arithmetic-mul-interval-independent-test-v1',
                  'selection_freeze_sha256': sha(selection), 'test_dataset_sha256': sha(data),
                  'test_dataset_path': str(data.resolve()), 'admission_sha256': sha(admission),
                  'protocol_sha256': sha(CONFIG), 'platforms': compute_report(dataset['rows'], models, fits),
                  'numeric_parameters_changed': False, 'test_used_for_fitting': False,
                  'full_step7_complete': False, 'main_matrix_authorized': False}
        write(out/'independent-test.json', report)
        write(marker, {'status': 'completed', 'selection_sha256': sha(selection),
                       'test_dataset_sha256': sha(data), 'output': str(out.resolve()),
                       'report_sha256': sha(out/'independent-test.json')})
        return report
    except Exception as exc:
        write(marker, {'status': 'failed_evaluation', 'selection_sha256': sha(selection),
                       'test_dataset_sha256': sha(data), 'output': str(out.resolve()), 'reason': str(exc)})
        raise


def verify(selection, result):
    selection, result = Path(selection), Path(result)
    frozen, admission, models, fits = frozen_inputs(selection)
    marker = json.loads((selection.parent/'independent-test-consumption.json').read_text())
    if (marker['status'] != 'completed' or marker['selection_sha256'] != sha(selection)
            or Path(marker['output']).resolve() != result.parent.resolve()
            or marker['report_sha256'] != sha(result)):
        raise ValueError('independent test result/consumption identity mismatch')
    report = json.loads(result.read_text())
    data = Path(report['test_dataset_path'])
    if (report['selection_freeze_sha256'] != sha(selection) or report['protocol_sha256'] != sha(CONFIG)
            or report['admission_sha256'] != sha(admission)
            or report['test_dataset_sha256'] != sha(data) or marker['test_dataset_sha256'] != sha(data)):
        raise ValueError('changed independent test dataset or selection')
    dataset, _ = validate_dataset(data, ['test'], selection)
    expected = compute_report(dataset['rows'], models, fits)
    if report['platforms'] != expected or report['numeric_parameters_changed'] or report['test_used_for_fitting']:
        raise ValueError('independent test numerical replay mismatch')
    return report, models, fits


def publish(selection, result, out):
    selection, result, out = map(Path, (selection, result, out))
    report, models, fits = verify(selection, result)
    out.mkdir(parents=True, exist_ok=False)
    published, failed = [], []
    for platform, original in models.items():
        scope = report['platforms'][platform]
        if scope['quality_status'] != 'passed':
            failed.append(platform)
            continue
        bundle = copy.deepcopy(original)
        # The qualified base is grt-only. Synth test failures remain in the
        # independent report; this never manufactures a missing synth base.
        bundle['stages'] = {'grt': bundle['stages']['grt']}
        model = bundle['stages']['grt']['mul_interval_model']
        model['quality_status'] = 'passed'
        for entry in model['intervals'].values():
            entry['quality_status'] = 'passed'
        bundle['quality_status'] = 'passed'
        bundle['id'] = platform+'-native-mul-interval-qualified-v1'
        bundle['interval_independent_test_sha256'] = sha(result)
        bundle['interval_selection_freeze_sha256'] = sha(selection)
        bundle['interval_release_scope'] = 'one qualified template interval per stage at fixed R; base node/state/stage domains unchanged; not full step seven'
        write(out/(platform+'.json'), bundle)
        published.append({'platform': platform, 'sha256': sha(out/(platform+'.json'))})
    manifest = {'version': 'arithmetic-mul-interval-release-v1', 'selection_freeze_sha256': sha(selection),
                'independent_test_sha256': sha(result), 'published': published, 'failed_platforms': failed,
                'full_step7_complete': False, 'main_matrix_authorized': False}
    write(out/'release.json', manifest)
    return manifest


def reproduce(selection, base, out):
    """Refit only the frozen train/validation data, without reading test rows."""
    from .model_mul_interval_fit import fit
    selection, base, out = map(Path, (selection, base, out))
    frozen, _, _, _ = frozen_inputs(selection)
    for item in frozen['models']:
        if sha(base/(item['platform']+'.json')) != item['base_model_sha256']:
            raise ValueError('reproduction base model differs from frozen fit')
    fit(Path(frozen['fitting_dataset_path']),base,out)
    for item in frozen['models']:
        platform=item['platform']
        if sha(out/(platform+'.candidate.json'))!=item['candidate_sha256'] or sha(out/(platform+'.fit.json'))!=item['fit_report_sha256']:
            raise ValueError('interval fitting did not reproduce frozen candidate and validation report bytes')
    result={'status':'passed','selection_freeze_sha256':sha(selection),'test_labels_read':False,
            'platforms':[m['platform'] for m in frozen['models']],'comparison':'identical candidate and fitting-report bytes'}
    write(out/'reproducibility.json',result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['test', 'verify', 'publish','reproduce'])
    parser.add_argument('--selection-freeze', type=Path, required=True)
    parser.add_argument('--data', type=Path)
    parser.add_argument('--result', type=Path)
    parser.add_argument('--base', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.action == 'test':
        if args.data is None or args.out is None:
            parser.error('test requires --data and --out')
        result = evaluate(args.data, args.selection_freeze, args.out)
        print(json.dumps({p: x['quality_status'] for p, x in result['platforms'].items()}))
    elif args.action == 'publish':
        if args.result is None or args.out is None:
            parser.error('publish requires --result and --out')
        print(json.dumps(publish(args.selection_freeze, args.result, args.out)))
    elif args.action == 'reproduce':
        if args.base is None or args.out is None:
            parser.error('reproduce requires --base and --out')
        print(json.dumps(reproduce(args.selection_freeze,args.base,args.out)))
    else:
        if args.result is None:
            parser.error('verify requires --result')
        report, _, _ = verify(args.selection_freeze, args.result)
        print(json.dumps({'verified': True, 'platforms': list(report['platforms'])}))


if __name__ == '__main__':
    main()
