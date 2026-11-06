"""Independent guards for conditional S bounds, split separation and fixed prices."""
import argparse
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.arithmetic_dse import model_general_control_fit as fit
from experiments.arithmetic_dse import model_general_control_test as independent
from experiments.arithmetic_dse.model_collection import sha, write


def run(folder, out):
    cfg = fit.dependencies(); f = fit.verify_fit(folder); c = fit.read(folder / 'candidate.json')
    d = fit.read(f['dataset_path']); row = next(r for r in d['rows'] if r['split'] == 'train')
    refusals = []
    for name, bad in [('unsupported-clock', {**row, 'period_ps': 1500}),
        ('negative-feature', {**row, 'control_features': {**row['control_features'], 'native_enable_bits_max': -1}}),
        ('nonfinite-feature', {**row, 'control_features': {**row['control_features'], 'native_data_bits': float('nan')}})]:
        try: fit.features(bad, cfg)
        except ValueError: refusals.append(name)
        else: raise ValueError('invalid conditional-bound context accepted')
    for split in ('validation', 'test'):
        try: fit.train_model('train_pooled_path_max', [{**row, 'split': split}], 'native_enable', cfg)
        except ValueError: refusals.append('calibration-' + split + '-refused')
        else: raise ValueError('non-train calibration accepted')
    # The smaller required delay can have the worse conditional margin.
    # Checking only the largest required delay would incorrectly accept this.
    synthetic = [dict(id='large-required', period_ps=1119, boundary_paths=[dict(id='native_valid', H_ps=0, delay_ps=10)]),
        dict(id='unsafe-smaller-required', period_ps=1119, boundary_paths=[dict(id='native_valid', H_ps=0, delay_ps=8)])]
    bounds = {'large-required': 15, 'unsafe-smaller-required': 6}
    check = fit.coverage(synthetic, ['native_valid'], lambda r, p: bounds[r['id']], [1119])
    if check['status'] != 'failed' or check['contexts'][0]['witness']['row_id'] != 'unsafe-smaller-required':
        raise ValueError('conditional independent test did not catch unsafe smaller requirement')
    parent = fit.read(ROOT / cfg['parent_general_candidate'])
    queries = 0
    for stage in ('synth', 'grt'):
        if c['stages'][stage]['area_models'] != parent['stages'][stage]['area_models']:
            raise ValueError('unchanged S area parameters differ')
        for t, paths in c['stages'][stage]['boundary_model']['immutable_by_exact_SDC'].items():
            for name, model in paths.items():
                if model != parent['stages'][stage]['boundary_model']['by_exact_SDC'][t][name]:
                    raise ValueError('unchanged S path parameters differ')
    # Exercise the actual frozen independent query on fitting-only rows.
    # This is a code consistency guard, never an independent quality claim.
    for r in d['rows']:
        if r['split'] != 'validation': continue
        for p in cfg['timing_labels']:
            if p == 'birth_data': continue
            value = independent.bound(c, r, p, cfg); queries += 1
            if value + fit.EPSILON_PS < fit.required(r, p):
                raise ValueError('frozen independent query differs from successful validation')
    result = dict(status='passed', refusals=refusals, conditional_unsafe_smaller_requirement_rejected=True,
        frozen_area_models_and_six_path_bounds_unchanged=True, actual_validation_bound_queries=queries,
        fresh_or_consumed_independent_labels_read=False, PPA_calls=0, producer_sha256=sha(__file__))
    write(out, result); print(json.dumps(result), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--fit', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True); args = parser.parse_args(); run(args.fit.resolve(), args.out.resolve())
