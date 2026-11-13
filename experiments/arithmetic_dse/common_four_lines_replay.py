"""Replay the bounded four-line diagnostic package without EDA or a build."""
import gzip
import hashlib
import json
import math
from pathlib import Path
from . import operator_function_successor as operator
from . import reduction_wide_model as reduction
from . import state_control_consumer as state


def _load(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def _close(expected, actual):
    if isinstance(expected, dict):
        if expected.keys() != actual.keys():
            raise ValueError('diagnostic replay object keys differ')
        for name, value in expected.items():
            _close(value, actual[name])
    elif isinstance(expected, list):
        if len(expected) != len(actual):
            raise ValueError('diagnostic replay array sizes differ')
        for a, b in zip(expected, actual, strict=True):
            _close(a, b)
    elif type(expected) in (int, float) and type(expected) is not bool:
        if not math.isclose(expected, actual, rel_tol=1e-12, abs_tol=1e-8):
            raise ValueError('diagnostic replay numerical price differs')
    elif expected != actual:
        raise ValueError('diagnostic replay semantic value differs')


def replay(root=None):
    repo = Path(__file__).resolve().parents[2]
    root = Path(root) if root else repo / 'experiments/arithmetic/evidence/common_four_lines_v1'
    identity = json.loads((root / 'identity.json').read_text())
    for name, expected in identity['files'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ValueError('four-line evidence identity changed: ' + name)
    for name, expected in identity['source_sha256'].items():
        if hashlib.sha256((repo / name).read_bytes()).hexdigest() != expected:
            raise ValueError('four-line source identity changed: ' + name)
    cases = [
        ('operator', 'consumption--operator-prices', operator.predict),
        ('Mux', 'operator-Mux-successor--evaluation--native', operator.predict),
        ('G', 'G-wide-probes--native', reduction.predict),
        ('S', 'S-consumption--prices', state.predict),
    ]
    counts = {}
    for kind, prefix, predict in cases:
        if kind in ('operator', 'S'):
            input_name = prefix + '-input.json.gz'
            output_name = prefix + '-native.json.gz'
        else:
            input_name = prefix + '-input.json.gz'
            output_name = prefix + '-output.json.gz'
        request = _load(root / input_name)
        reference = _load(root / output_name)
        if len(request['queries']) != len(reference):
            raise ValueError('diagnostic replay request/result size mismatch')
        kwargs = dict(diagnostic=True)
        if kind == 'G':
            kwargs['extrapolate'] = True
        for query, actual in zip(request['queries'], reference, strict=True):
            expected = predict(request['model'], query, **kwargs)
            if expected['status'] != actual['status']:
                raise ValueError('diagnostic replay coverage differs')
            if kind == 'S' and expected['status'] == 'diagnostic_estimate':
                _close(expected, actual)
            elif expected['status'] != 'cost_uncovered':
                for field in ('operator_delay_ps', 'comb_area_um2'):
                    _close(expected[field], actual[field])
                if kind in ('operator', 'Mux'):
                    _close(expected['train_LOSO_delay_reserve_ps'], actual['train_LOSO_delay_reserve_ps'])
        first = request['queries'][0]
        if predict(request['model'], first)['status'] != 'cost_uncovered':
            raise ValueError('diagnostic package accepted as public price')
        counts[kind] = len(reference)
    return dict(status='passed', price_replays=counts, evidence_files=len(identity['files']),
                public_price_rejections=4, new_EDA_calls=0, full_D_ready=False)


if __name__ == '__main__':
    print(json.dumps(replay(), ensure_ascii=False, indent=2))
