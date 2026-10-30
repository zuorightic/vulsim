"""Current experiment contracts; frozen v1 evidence remains immutable.

This module defines the Python experiment boundary. Compiler request plumbing,
BEIR expansion validation and scheduling are implemented in later plan steps.
"""
from fractions import Fraction
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIGS = Path(__file__).resolve().parent / 'configs'
WIDTHS = (8, 16, 32, 64, 128)
PLATFORMS = ('asap7', 'nangate45', 'sky130hd', 'gf180')
GROUPS = ('A', 'B', 'C', 'D')


class ContractError(ValueError):
    def __init__(self, code, message, *, stage='contract', **detail):
        super().__init__(message)
        self.code, self.stage, self.detail = code, stage, detail

    def as_dict(self):
        return {'failure_stage': self.stage, 'failure_code': self.code,
                'failure_reason': str(self), 'detail': self.detail}


def positive_int(value, name):
    if type(value) is not int or value <= 0:
        raise ContractError('invalid_request', f'{name}: positive integer required')
    return value


def content_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False).encode()).hexdigest()


def semantic_profile(request):
    """Reject unsupported numerical fields instead of silently ignoring them."""
    if not isinstance(request, dict):
        raise ContractError('unsupported_semantic_profile', 'profile must be an object')
    kind = request.get('kind')
    if kind == 'unsigned_integer':
        allowed = {'kind', 'width', 'signed', 'overflow'}
        if (request.keys() - allowed or request.get('width') not in WIDTHS
                or type(request.get('width')) is not int
                or request.get('signed', False) is not False
                or request.get('overflow', 'modulo') != 'modulo'):
            raise ContractError('unsupported_semantic_profile', 'unsupported integer format', request=request)
        return {'kind': kind, 'width': request['width'], 'signed': False,
                'overflow': 'modulo', 'version': 'arithmetic-semantics-v2'}
    if kind == 'binary32_mul_rne':
        if request.keys() - {'kind'}:
            raise ContractError('unsupported_semantic_profile', 'binary32 semantics are fixed', request=request)
        return {'kind': kind, 'version': 'arithmetic-semantics-v1',
                'rounding': 'nearest_ties_to_even', 'flags_width': 5}
    raise ContractError('unsupported_semantic_profile', 'unregistered numerical profile', request=request)


def template_parameters(request):
    """Validate a Mul template shape, without claiming it can be scheduled.

    This is a parameter schema, not an implementation/eligibility registry.
    A provider must still declare which validated shapes it actually implements.
    """
    if not isinstance(request, dict) or request.keys() - {'operation', 'W', 'R', 'block_width', 'product', 'reduction'}:
        raise ContractError('template_ineligible', 'unknown template parameter')
    try:
        w = positive_int(request.get('W'), 'W')
        r = positive_int(request.get('R'), 'R')
        b = request.get('block_width')
        if b is not None:
            positive_int(b, 'block_width')
    except ContractError as error:
        raise ContractError('template_ineligible', str(error)) from error
    product = request.get('product', 'full')
    if (request.get('operation') != 'Mul' or w > 128 or r > 2*w
            or product not in ('full', 'truncated') or (product == 'full' and r != 2*w)
            or (b is not None and not 2 <= b <= w)
            or request.get('reduction', 'carry_preserving_tree') != 'carry_preserving_tree'):
        raise ContractError('template_ineligible', 'unsupported template shape', request=request)
    return {**request, 'product': product, 'reduction': 'carry_preserving_tree',
            'schema_version': 'arithmetic-interfaces-v1'}


def topological(nodes):
    by_id = {node['id']: node for node in nodes}
    if len(by_id) != len(nodes):
        raise ContractError('invalid_expansion_graph', 'duplicate node identity')
    if any(dep not in by_id for node in nodes for dep in node.get('deps', [])):
        raise ContractError('invalid_expansion_graph', 'missing dependency')
    pending, result, seen = set(by_id), [], set()
    while pending:
        ready = sorted(name for name in pending if set(by_id[name].get('deps', [])) <= seen)
        if not ready:
            raise ContractError('invalid_expansion_graph', 'cyclic graph')
        result.extend(by_id[name] for name in ready)
        seen.update(ready)
        pending.difference_update(ready)
    return result


def heavy_depth(case):
    depths = {}
    for node in topological(case['reference_graph']):
        depths[node['id']] = int(node['heavy']) + max((depths[x] for x in node['deps']), default=0)
    return max(depths.values(), default=0)


def fixed_latency(case):
    return max(2, heavy_depth(case) + 1)


def case_manifest():
    return json.loads((ROOT / 'experiments/arithmetic/cases_v2.json').read_text())


def check_partition(manifest):
    # Regeneration checks signatures, original DAGs and IDs, not only counts.
    from .case_generator import generate_manifest
    if manifest != generate_manifest():
        raise ContractError('invalid_case_manifest', 'case manifest differs from the versioned generator')
    cases = manifest['cases']
    formal = sum(c['partition'] == 'formal' for c in cases)
    holdout = sum(c['partition'] == 'holdout' for c in cases)
    ids = {c['id'] for c in cases}
    if len(ids) != 43 or (formal, holdout) != (32, 11):
        raise ContractError('invalid_case_manifest', 'expected 32 formal and 11 holdout cases')
    if ids & set(manifest['training_identity_policy']['registered_training_ids']):
        raise ContractError('invalid_case_manifest', 'training/case identity overlap')
    return {'formal': formal, 'holdout': holdout, 'cases': len(cases),
            'records_per_platform': len(cases)*len(GROUPS),
            'all_platform_records': len(cases)*len(GROUPS)*len(PLATFORMS),
            'fixed_L': {c['id']: fixed_latency(c) for c in cases}}


def _time(value, name, *, positive=False):
    try:
        if isinstance(value, bool):
            raise ValueError('boolean timing')
        result = Fraction(str(value))
    except (ValueError, TypeError, ZeroDivisionError) as error:
        raise ContractError('invalid_reference', f'{name}: finite rational time required') from error
    if result < 0 or (positive and not result):
        raise ContractError('invalid_reference', f'{name}: invalid timing value')
    return result


def target_period_ps(case, reference_bundle, overhead_ps, *, platform):
    """Use only supplied frozen microbenchmark labels; never load backend data.

    Every non-wiring node is charged on the original dependency graph. Shared
    fanout is one node; parallel paths are combined by max, not by summation.
    The caller supplies a separate, nonoverlapping boundary overhead H_ref.
    """
    if not isinstance(reference_bundle,dict) or platform not in PLATFORMS or reference_bundle.get('platform') != platform:
        raise ContractError('invalid_reference', 'reference platform mismatch')
    if (reference_bundle.get('stage') != 'grt'
            or reference_bundle.get('label_definition') != 'combinational_data_path_excluding_boundary'
            or reference_bundle.get('source_role') != 'microbenchmark_only'
            or not isinstance(reference_bundle.get('reference_set_id'),str)
            or not reference_bundle['reference_set_id']
            or not isinstance(reference_bundle.get('settings_sha256'),str)
            or len(reference_bundle['settings_sha256']) != 64
            or any(c not in '0123456789abcdef' for c in reference_bundle['settings_sha256'])
            or not isinstance(reference_bundle.get('delays_ps'),dict)):
        raise ContractError('invalid_reference', 'reference label identity/scope is incomplete')
    arrivals = {}
    labels = reference_bundle['delays_ps']
    for node in topological(case['reference_graph']):
        primitive = node['primitive']
        if primitive is None:
            delay = Fraction(0)
        elif primitive not in labels:
            raise ContractError('missing_reference', f'missing microbenchmark: {primitive}')
        else:
            delay = _time(labels[primitive], primitive, positive=True)
        arrivals[node['id']] = delay + max((arrivals[x] for x in node['deps']), default=0)
    critical = max(arrivals.values(), default=Fraction(0))
    period = _time(overhead_ps, 'H_ref') + Fraction(3, 2)*critical/fixed_latency(case)
    if period <= 0:
        raise ContractError('invalid_reference', 'nonpositive target')
    return (period.numerator + period.denominator - 1)//period.denominator


def freeze_target_batch(cases, reference_bundle, overhead_by_case, *, platform):
    if not cases or len({c['id'] for c in cases}) != len(cases):
        raise ContractError('invalid_reference', 'nonempty unique target batch required')
    if set(overhead_by_case) != {c['id'] for c in cases}:
        raise ContractError('invalid_reference', 'one explicit H_ref per case required')
    periods = {c['id']: target_period_ps(c, reference_bundle, overhead_by_case[c['id']], platform=platform)
               for c in cases}
    payload = {'version': 'arithmetic-target-batch-v2', 'platform': platform,
               'rules_version': 'arithmetic-targets-v2', 'stage': 'grt',
               'reference_bundle_sha256': content_hash(reference_bundle),
               'overhead_ps': {k: str(_time(v, k)) for k, v in overhead_by_case.items()},
               'case_sha256': {c['id']: content_hash(c) for c in cases},
               'L': {c['id']: fixed_latency(c) for c in cases}, 'periods_ps': periods}
    return {**payload, 'batch_sha256': content_hash(payload)}
