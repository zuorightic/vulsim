"""Predeclared NNLS state candidates and conservative bank boundary freeze."""
import argparse
from importlib.metadata import version as package_version
import json
import math
import os
from pathlib import Path
import shutil
import sys

from .model_collection import sha, write
from .model_m2_state_collection import CONFIG, ROOT, read
from .model_training import metric

TYPED_FEATURES = ['data_bits', 'data_signals', 'valid_bits', 'enable_domains', 'reset_one_bits']
EXECUTION = {
    'version':'asap7-m2-state-fitting-execution-v1',
    'area_target':'whole_stdcell_area_including_taps_minus_postcapture_observer',
    'NNLS_bits_signals':['state_bits','state_signals'],
    'NNLS_typed_state_and_controls':TYPED_FEATURES,
    'exact_SDC_NNLS_typed_state_and_controls':TYPED_FEATURES,
    'NNLS_loss':'unweighted train-only squared error; no intercept or added margins',
    'exact_SDC':'independent nonnegative coefficients at each predeclared exact SDC; no interpolation',
    'ranking':'passing original median/P95 gates first; then MAE/mean_actual; serialized model bytes; stable candidate name',
    'gate_aggregation':'all complete validation banks within each physical stage; exact-target breakdown also reported',
    'boundary':'global maximum nonnegative H plus global maximum of all state data/enable/valid Q-D paths plus original 50ps reserve, separately per physical stage',
    'test_data':'forbidden; old state formula coefficients immutable and only grt available',
}


def predict(model, row):
    if model['kind'] == 'exact_SDC_nonnegative_linear':
        model = model['slices'][str(row['period_ps'])]
    if model['kind'] != 'nonnegative_linear':
        raise ValueError('unknown state area predictor')
    coefficients = model['coefficients']
    if any(not math.isfinite(c) or c < 0 for c in coefficients):
        raise ValueError('invalid nonnegative state coefficients')
    return sum(row['features'][key]*c for key,c in zip(model['features'],coefficients,strict=True))


def quality(model, rows, cfg):
    actual = [r['state_area_um2'] for r in rows]
    predicted = [predict(model, r) for r in rows]
    result = metric(actual, predicted, 1e-4)
    gates = cfg['quality_gates']
    passed = (result['median_relative_error'] <= gates['state_area_median_relative_error_max']
              and result['p95_relative_error'] <= gates['state_area_p95_relative_error_max'])
    return {'status':'passed' if passed else 'failed', **result,
            'normalized_MAE':result['MAE']/(sum(actual)/len(actual)),
            'underpredicted_banks':sum(p<a for p,a in zip(predicted,actual)),
            'predictions':[{'id':r['id'],'actual_um2':a,'predicted_um2':p} for r,a,p in zip(rows,actual,predicted)]}


def nnls(train, names):
    import numpy as np
    from scipy.optimize import nnls as solve
    x = np.asarray([[r['features'][n] for n in names] for r in train],dtype=float)
    y = np.asarray([r['state_area_um2'] for r in train],dtype=float)
    coefficients, _ = solve(x,y)
    return {'kind':'nonnegative_linear', 'features':names, 'coefficients':list(map(float,coefficients))}


def boundary(rows, cfg):
    paths = [p | {'row_id':r['id']} for r in rows for p in r['boundary_paths']]
    h = max(paths,key=lambda p:(p['H_ps'],p['row_id'],p['id']))
    qd = max(paths,key=lambda p:(p['QD_ps'],p['row_id'],p['id']))
    reserve = cfg['boundary']['engineering_reserve_ps']
    value = max(0.,h['H_ps'])+max(0.,qd['QD_ps'])+reserve
    return {'io_delay_fraction':.2, 'input_overhead_ps':value, 'register_overhead_ps':value,
        'actual_boundary_H_max_ps':max(0.,h['H_ps']), 'capture_control_path_max_ps':max(0.,qd['QD_ps']),
        'engineering_clock_reserve_ps':reserve, 'H_witness':h, 'QD_witness':qd,
        'fit_splits':['train','validation'], 'scope':'registered state-bank paths only; joint arithmetic/input boundary remains unqualified',
        'definition':'H=T-QD-slack includes clkQ/setup/skew/uncertainty once; control QD and engineering reserve separate'}


def fit(dataset, out):
    cfg, data = read(CONFIG), read(dataset)
    if (data['version'] != 'asap7-m2-state-fitting-dataset-v1' or data['protocol_sha256'] != sha(CONFIG)
        or data['audit']['status'] != 'passed' or data['test_labels_read'] or not data['test_collection_locked']
        or len(data['rows']) != 216 or any(r['split'] not in ('train','validation') for r in data['rows'])):
        raise ValueError('complete audited fitting-only state dataset required')
    admission = read(data['admission_path'])
    if sha(data['admission_path']) != data['admission_sha256']:
        raise ValueError('state data admission changed')
    old_path = ROOT/cfg['old_state_baseline']
    if sha(old_path) != admission['baseline_model_sha256']:
        raise ValueError('old state numerical baseline changed')
    old = read(old_path)
    if (data['parent_primitives_sha256'] != cfg['parent_primitives_sha256']
        or sha(ROOT/cfg['parent_primitives']) != cfg['parent_primitives_sha256']):
        raise ValueError('published primitive parent changed')
    out.mkdir(parents=True,exist_ok=False)
    stages, reports = {}, {}
    for stage in ('synth','grt'):
        rows = [r for r in data['rows'] if r['stage'] == stage]
        train = [r for r in rows if r['split'] == 'train']
        val = [r for r in rows if r['split'] == 'validation']
        if len(train) != 72 or len(val) != 36:
            raise ValueError('complete stage state banks required')
        candidates, skipped = [], []
        for name in cfg['area_candidates']:
            if name == 'frozen_old_state_formula':
                if stage not in old['stages']:
                    skipped.append({'name':name,'reason':'immutable old model has no '+stage+' state formula'})
                    continue
                s = old['stages'][stage]['state_model']
                model = {'kind':'nonnegative_linear','features':['state_bits','state_signals'],
                         'coefficients':[s['bit_area_um2']+s['clock_area_per_bit_um2'],s['signal_area_um2']]}
            elif name == 'NNLS_bits_signals':
                model = nnls(train, EXECUTION[name])
            elif name == 'NNLS_typed_state_and_controls':
                model = nnls(train,TYPED_FEATURES)
            elif name == 'exact_SDC_NNLS_typed_state_and_controls':
                model = {'kind':'exact_SDC_nonnegative_linear',
                         'slices':{str(t):nnls([r for r in train if r['period_ps']==t],TYPED_FEATURES) for t in cfg['SDC_ps']}}
            else:
                raise ValueError('candidate not in registered implementation')
            q = quality(model,val,cfg)
            candidate = {'name':name,'model':model,'validation':q,
                'validation_by_exact_SDC':{str(t):quality(model,[r for r in val if r['period_ps']==t],cfg) for t in cfg['SDC_ps']},
                'serialized_model_bytes':len(json.dumps(model,sort_keys=True,separators=(',',':')).encode())}
            candidates.append(candidate)
        selected = min(candidates,key=lambda c:(c['validation']['status']!='passed',c['validation']['normalized_MAE'],c['serialized_model_bytes'],c['name']))
        ready = selected['validation']['status']=='passed'
        stages[stage] = {'quality_status':'awaiting_independent_test' if ready else 'failed_validation',
            'area_model':selected['model'], 'algorithm':selected['name'], 'boundary_model':boundary(rows,cfg)}
        reports[stage] = {'validation_status':selected['validation']['status'], 'selected_algorithm':selected['name'],
            'selected_validation':selected['validation'],'candidates':candidates,'unavailable_candidates':skipped}
    ready = stages['grt']['quality_status']=='awaiting_independent_test'
    model = {'version':'arithmetic-state-boundary-candidate-v1', 'id':'asap7-m2-state-boundary-v1',
        'quality_status':'awaiting_independent_test' if ready else 'failed_validation',
        'target_platform':'asap7','ABC_ps':cfg['ABC_ps'],'exact_SDC_ps':cfg['SDC_ps'],'IO':'0.2T',
        'measurement_static_identity_sha256':data['measurement_static_identity_sha256'],
        'feature_schema':cfg['feature_schema'],'feature_names':cfg['features'],'stages':stages,
        'domain':{'control_family':'valid_chain','clock_reset':'single-clock synchronous active-low reset',
            'word_widths':cfg['word_widths'],'max_data_depth':cfg['max_data_depth'],
            'max_parallel_words':cfg['max_parallel_words'],'max_enable_domains':cfg['max_enable_domains'],
            **{k:cfg[k] for k in ('max_input_bits','max_capture_bits','max_state_bits','max_state_signals')},
            'topology':'registered synthetic state-bank family; native bank equivalence binding still required',
            'reset':'variable zero/one per bit; test independent pattern unobserved',
            'width_padding':'only declared65/variable64 zero padding or unpadded sampled word widths',
            'continuous_SDC_qualified':False,'arbitrary_stage_boundary_qualified':False},
        'parent_primitives_sha256':cfg['parent_primitives_sha256'],'dataset_sha256':sha(dataset),
        'protocol_sha256':sha(CONFIG),'execution_definition':EXECUTION,
        'native_state_binding_qualified':False,'full_D_ready':False,'test_labels_read':False}
    write(out/'candidate.json',model)
    write(out/'validation.json',reports)
    sources = {}
    paths = [Path(__file__),CONFIG,Path(__file__).with_name('model_m2_state_replay.py'),
             Path(__file__).with_name('model_training.py')]
    for path in paths:
        name = str(path.relative_to(ROOT)); dst=out/'training-source'/name
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst);sources[name]=sha(path)
    write(out/'selection-freeze.json',{'version':'asap7-m2-state-boundary-selection-freeze-v1',
        'status':'frozen_awaiting_independent_test' if ready else 'failed_validation',
        'dataset_path':str(dataset),'dataset_sha256':sha(dataset),'admission_path':data['admission_path'],
        'admission_sha256':data['admission_sha256'],'protocol_sha256':sha(CONFIG),
        'candidate_sha256':sha(out/'candidate.json'),'validation_sha256':sha(out/'validation.json'),
        'parent_primitives_sha256':cfg['parent_primitives_sha256'],'training_sources':sources,
        'training_environment':{'python':sys.version, 'numpy':package_version('numpy'),'scipy':package_version('scipy'),
            'threads':{k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS')}},
        'test_observed':False,'deployable_stages_if_independently_passed':['grt'],
        'required_independent_tasks':36,'native_state_binding_qualified':False,'main_36_admitted':False})
    print(json.dumps({'status':'validation_passed' if ready else 'validation_failed',
        'stages':{stage:{'algorithm':r['selected_algorithm'],
            'median_relative_error':r['selected_validation']['median_relative_error'],
            'p95_relative_error':r['selected_validation']['p95_relative_error'],
            'boundary':stages[stage]['boundary_model']['register_overhead_ps']} for stage,r in reports.items()},
        'PPA_calls':0,'test_observed':False}),flush=True)


def verify(folder):
    f = read(folder/'selection-freeze.json')
    for key, name in (('candidate_sha256','candidate.json'),('validation_sha256','validation.json')):
        if sha(folder/name) != f[key]:
            raise ValueError('changed frozen state candidate/validation')
    if (sha(f['dataset_path']) != f['dataset_sha256'] or sha(f['admission_path']) != f['admission_sha256']
        or sha(CONFIG) != f['protocol_sha256'] or f['test_observed']):
        raise ValueError('changed state fit inputs or roles')
    for name,h in f['training_sources'].items():
        if sha(ROOT/name) != h or sha(folder/'training-source'/name) != h:
            raise ValueError('changed frozen state fitting producer')
    return f


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('fit','verify'))
    parser.add_argument('--dataset',type=Path)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    if args.action == 'fit':
        if args.dataset is None:
            parser.error('dataset required')
        fit(args.dataset.resolve(),args.out.resolve())
    else:
        verify(args.out.resolve())
        print('verified frozen state fit')


if __name__ == '__main__':
    main()
