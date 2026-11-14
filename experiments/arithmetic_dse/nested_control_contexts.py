"""Offline nested group contexts for stacked control models.

The outer group stays excluded from every context used in its experiment.
A training row also excludes its own complete group. Final downstream
training uses out-of-group contexts; deployment uses the all-train function.
No physical measurements, file access, or model fitting policy live here.
"""
from copy import deepcopy
import hashlib
import itertools
import json

VERSION = 'nested-control-contexts-v1'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def dimensions(rows):
    sources = {}
    identities = set()
    for row in rows:
        if row['role'] != 'train':
            raise ValueError('nested contexts require train rows only')
        source, fold = row['source'], row['fold']
        if source in sources and sources[source] != fold:
            raise ValueError('complete source must have one group across all targets')
        sources[source] = fold
        identity = source, row['target_ps'], row['stage']
        if identity in identities:
            raise ValueError('duplicate upstream training observation')
        identities.add(identity)
    folds = sorted(set(sources.values()))
    if len(folds) < 3:
        raise ValueError('nested contexts require at least three complete groups')
    return sources, folds


def route(outer, row_fold, contexts):
    """Return the exact upstream function needed for a downstream row."""
    if row_fold not in contexts['folds'] or outer not in contexts['folds'] + ['all_train']:
        raise ValueError('unknown complete group')
    excluded = [row_fold] if outer == 'all_train' or outer == row_fold else sorted([outer, row_fold])
    record = contexts['contexts'][digest(excluded)]
    if record['excluded_folds'] != excluded:
        raise ValueError('context exclusion identity differs')
    return record


def build(rows, inherited, features, fit):
    """Fit each distinct pair exclusion once; reuse frozen single exclusions.

    ``fit`` receives only retained enable rows. The caller supplies a fixed
    upstream algorithm, independent of downstream model selection.
    """
    rows = deepcopy(rows)
    sources, folds = dimensions(rows)
    if set(inherited) != set(folds) | {'all_train'}:
        raise ValueError('inherited single-exclusion contexts are incomplete')
    contexts = {}
    pair_fits = 0
    for excluded in [[], *[[fold] for fold in folds], *map(list, itertools.combinations(folds, 2))]:
        training = [r for r in rows if r['fold'] not in excluded]
        excluded_sources = sorted(source for source, fold in sources.items() if fold in excluded)
        training_sources = sorted({r['source'] for r in training})
        if set(training_sources) & set(excluded_sources):
            raise ValueError('source group exclusion leaked')
        lineage = [dict(source=r['source'], target_ps=r['target_ps'], stage=r['stage'],
                        actual=r['actual'], features={name:r['f'][name] for name in features}) for r in training]
        if len(excluded) <= 1:
            origin = inherited[excluded[0] if excluded else 'all_train']
            if (origin['uses_held_out_labels'] or origin['training_sources'] != training_sources
                    or origin['excluded_sources'] != excluded_sources):
                raise ValueError('inherited context source provenance differs')
            function = deepcopy(origin['function'])
            fitted = False
        else:
            function = fit(training)
            fitted = True
            pair_fits += 1
        contexts[digest(excluded)] = dict(function=function, excluded_folds=excluded,
            training_sources=training_sources, excluded_sources=excluded_sources,
            training_rows_sha256=digest(lineage), training_rows=len(training),
            newly_fitted=fitted, uses_held_out_labels=False)
    return dict(version=VERSION, folds=folds, contexts=contexts,
                algorithm_features=list(features), new_pair_context_fits=pair_fits,
                inherited_contexts=len(inherited), final_context_key=digest([]),
                downstream_train_context='exclude outer group and row group; all targets together',
                downstream_final_train_context='exclude row group',
                downstream_outer_test_context='exclude outer group',
                deployment_context='inherited all-train enable function',
                validation_labels_read=False, independent_labels_read=False)


def verify(rows, result):
    sources, folds = dimensions(rows)
    if result['version'] != VERSION or result['folds'] != folds:
        raise ValueError('nested context version or groups differ')
    expected = [[], *[[fold] for fold in folds], *map(list, itertools.combinations(folds, 2))]
    if set(result['contexts']) != {digest(x) for x in expected}:
        raise ValueError('nested context dimensions differ')
    for excluded in expected:
        record = result['contexts'][digest(excluded)]
        training = [r for r in rows if r['fold'] not in excluded]
        lineage = [dict(source=r['source'], target_ps=r['target_ps'], stage=r['stage'], actual=r['actual'],
                        features={name:r['f'][name] for name in result['algorithm_features']}) for r in training]
        if (record['excluded_folds'] != excluded or record['training_rows_sha256'] != digest(lineage)
                or record['training_rows'] != len(training) or record['uses_held_out_labels']
                or record['newly_fitted'] != (len(excluded) == 2)
                or record['training_sources'] != sorted({r['source'] for r in training})
                or record['excluded_sources'] != sorted(source for source, fold in sources.items() if fold in excluded)):
            raise ValueError('nested context training lineage differs')
    checks = 0
    for outer in folds + ['all_train']:
        for row in rows:
            record = route(outer, row['fold'], result)
            required = {row['fold']} | ({outer} if outer != 'all_train' else set())
            if set(record['excluded_folds']) != required or row['source'] in record['training_sources']:
                raise ValueError('row group or outer group leaked into context')
            checks += 1
    return dict(status='passed', context_functions=len(expected), routing_checks=checks,
                pair_context_fits=len(folds)*(len(folds)-1)//2,
                complete_groups=len(folds), upstream_observations=len(rows),
                independent_labels_read=False, validation_labels_read=False)
