"""Shared finite structural grammar for the Python and VUL entry points."""
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY = Path(__file__).with_name('candidate_profiles.json')
CATALOG = ROOT / 'vullib/models/autopipe/workloads.json'


def widths(text, default, maximum=4096):
    try:
        result = list(default) if text is None else [int(v) for v in text.split(',')]
    except ValueError as error:
        raise ValueError('width grammar must be comma-separated integers') from error
    if not result or len(result) != len(set(result)) or any(v < 0 or v > maximum for v in result):
        raise ValueError(f'width grammar must contain distinct integers in 0..{maximum}')
    return result


def available_profiles():
    return ['generic', *(c['id'] for c in json.loads(CATALOG.read_text())['cases'])]


def resolve(workload=None, profile=None, mul_block_widths=None, add_limb_widths=None, method='D'):
    policy_bytes = POLICY.read_bytes()
    policy = json.loads(policy_bytes)
    if policy['schema'] != 'autopipe-candidate-profiles-v1':
        raise ValueError('unsupported candidate profile policy')
    selected = profile or workload or 'generic'
    if selected == 'generic':
        defaults = policy['generic']
    else:
        case = next((c for c in json.loads(CATALOG.read_text())['cases'] if c['id'] == selected), None)
        if case is None:
            raise ValueError('unknown candidate profile: ' + selected)
        structural = case['structural_search']
        defaults = dict(mul_block_widths=structural['mul_block_widths'],
                        add_limb_widths=structural['add_sub_limb_widths'])
    mul = widths(mul_block_widths, defaults['mul_block_widths'], policy['max_mul_block_width'])
    if 1 in mul:
        raise ValueError('multiply block width must be 0 or 2..128')
    add = widths(add_limb_widths, defaults['add_limb_widths'], policy['max_add_limb_width'])
    structures = [[0, 0]] if method in ['A', 'B'] else [list(p) for p in itertools.product(mul, add)]
    if len(structures) > policy['max_structures']:
        raise ValueError(f"frozen structural policy permits at most {policy['max_structures']} grammars")
    return dict(profile=selected, mul_block_widths=mul, add_limb_widths=add,
                structures=structures, policy_sha256=hashlib.sha256(policy_bytes).hexdigest())
