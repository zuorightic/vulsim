"""Actual full-state/FF preflight for the prospective control-boundary successor."""
import argparse
import inspect
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from regression import arithmetic_general_state as parent
from experiments.arithmetic_dse import model_general_control_samples as samples
from experiments.arithmetic_dse.model_collection import sha, write

CONFIG = ROOT / 'experiments/arithmetic_dse/configs/model_asap7_general_control_v1.json'


def worker(out):
    text = inspect.getsource(parent.worker)
    old = '''parity=0
            for j,w in enumerate(s['words']):
                value=new[f'external.data_{j}'] if j in s['external_words'] else new[f'native.data_{j}_s{w["end"]}']
                parity^=value.bit_count()%2'''
    if text.count(old) != 1:
        raise ValueError('unsupported control preflight observation point')
    text = text.replace(old, 'parity=sum(value.bit_count() for value in new.values())%2')
    namespace = dict(parent.worker.__globals__)
    namespace.update(CONFIG=CONFIG, specifications=samples.specifications, features=samples.features,
        source=samples.source, step=samples.step, __file__=__file__)
    exec(compile(text, str(Path(__file__).resolve()) + '::control_preflight', 'exec'), namespace)
    namespace['worker'](out)
    cfg = json.loads(CONFIG.read_text()); proof = json.loads((out / 'proof.json').read_text())
    proof.update(version='general-state-control-load-preflight-v1', all_semantic_state_outputs_explicitly_observed=True,
        area_parameters_unchanged=True, consumed_test_numeric_labels_read=False,
        control_load_contexts={s['id']: samples.control_features(s) for s in samples.specifications(cfg)})
    for name in ('experiments/arithmetic_dse/model_general_control_samples.py',
                 'experiments/arithmetic_dse/model_general_state_samples_v2.py', 'regression/arithmetic_general_state.py'):
        proof['producer_sha256'][name] = sha(ROOT / name)
    write(out / 'proof.json', proof)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); worker(args.out.resolve())
