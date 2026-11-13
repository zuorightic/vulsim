"""Replay the common narrow/wide model diagnostic without EDA or a build."""
import gzip
import hashlib
import json
import math
from pathlib import Path
from . import operator_function_successor as operator
from . import reduction_mapping_model as reduction
from . import reduction_mapping_features as geometry
from . import state_control_shared_model as state


def _load(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def _close(a, b):
    if isinstance(a, dict):
        if a.keys() != b.keys():
            raise ValueError('model replay keys differ')
        for n, v in a.items():
            _close(v, b[n])
    elif isinstance(a, list):
        if len(a) != len(b):
            raise ValueError('model replay lengths differ')
        for v, w in zip(a, b, strict=True):
            _close(v, w)
    elif type(a) in (int, float) and type(a) is not bool:
        if not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-8):
            raise ValueError('model replay numerical result differs')
    elif a != b:
        raise ValueError('model replay value differs')


def replay(root=None):
    repo = Path(__file__).resolve().parents[2]
    root = Path(root) if root else repo / 'experiments/arithmetic/evidence/common_model_repair_v1'
    identity = json.loads((root / 'identity.json').read_text())
    for name, digest in identity['files'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise ValueError('repair evidence changed: ' + name)
    for name, digest in identity['source_sha256'].items():
        if hashlib.sha256((repo / name).read_bytes()).hexdigest() != digest:
            raise ValueError('repair implementation changed: ' + name)
    counts = {}
    for prefix, kind, predict in [
            (prefix, kind, predict)
            for prefix in ('final-consumption-v3', 'validation-consumption')
            for kind, predict in [('operator', operator.predict), ('G', reduction.predict), ('S', state.predict)]]:
        request = _load(root / (prefix + '--' + kind + '-prices-input.json.gz'))
        results = _load(root / (prefix + '--' + kind + '-prices-native.json.gz'))
        for q, expected in zip(request['queries'], results, strict=True):
            actual = predict(request['model'], q, diagnostic=True)
            if actual['status'] != expected['status']:
                raise ValueError('model replay coverage differs')
            if actual['status'] == 'diagnostic_estimate':
                if kind == 'S':
                    _close(actual, expected)
                else:
                    for key in ('operator_delay_ps', 'comb_area_um2'):
                        _close(actual[key], expected[key])
        for suffix, diagnostic in ([('invalid', True), ('public', False)] if prefix == 'final-consumption-v3' else []):
            bad = _load(root / ('final-consumption-v3--' + kind + '-' + suffix + '-input.json.gz'))
            for q in bad['queries']:
                if predict(bad['model'], q, diagnostic=diagnostic)['status'] != 'cost_uncovered':
                    raise ValueError('invalid or public model request accepted')
        counts[prefix + ':' + kind] = len(results)
    request = _load(root / 'final-consumption-v3--G-features-input.json.gz')
    result = _load(root / 'final-consumption-v3--G-features-native.json.gz')
    for q, expected in zip(request['queries'], result, strict=True):
        _close(geometry.features(q['output_bits'], q['terms'], q['target_ps']), expected)
    counts['G_features'] = len(result)
    return dict(status='passed', replays=counts, evidence_files=len(identity['files']),
                new_EDA_calls=0, same_operator_one_shared_model=True,
                independent_labels_read=False, full_D_ready=False)


if __name__ == '__main__':
    print(json.dumps(replay(), ensure_ascii=False, indent=2))
