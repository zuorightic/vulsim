#!/usr/bin/env python3
"""Check step-two semantics, partition and simple-cost contracts without PPA.

Optional independent SoftFloat cross-check:
  ARITHMETIC_SOFTFLOAT_DIR=/path/to/flat/softfloat python3 regression/arithmetic_contracts.py
"""
from fractions import Fraction
import json
import os
from pathlib import Path
import random
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.arithmetic_dse.contracts import check_freeze, check_partition, fixed_latency, target_period_ps
from experiments.arithmetic_dse.reference import (FPResult, f32_mul, f32_chain, udivrem,
                                            safe_divisor, case_manifest, evaluate_case)
from experiments.arithmetic_dse.simple_cost import (CONFIG as SIMPLE_COST_CONFIG, Cost, Value, node_cost, lookup_choices,
    region_delay, combinational_area, candidate_score, within_relative_cap)
from experiments.arithmetic_dse.softfloat_oracle import SoftFloatOracle

checks = 0


def check(condition, message='contract assertion'):
    global checks
    checks += 1
    if not condition:
        raise AssertionError(message)


def rejects(function):
    try:
        function()
    except ValueError:
        check(True)
    else:
        check(False, 'expected rejection')


def fp_fraction(bits):
    exponent = bits >> 23 & 255
    significand = bits & 0x7FFFFF
    if exponent == 255:
        raise ValueError('non-finite')
    power = -149 if exponent == 0 else exponent-150
    if exponent:
        significand |= 1 << 23
    value = Fraction(significand)*(Fraction(2)**power)
    return -value if bits >> 31 else value


manifest = case_manifest()
partition = check_partition(manifest)
check(partition['formal'] == 6 and partition['holdout'] == 3 and partition['group_records'] == 36)
check(partition['fixed_L'] == {c['id']: (3 if c['heavy_depth'] == 2 else 2) for c in manifest['cases']})
rejects(lambda: check_partition({**manifest, 'cases': manifest['cases'][:-1]}))

# Exhaustive small-width proof of the division wrapper, including zero divisor.
division_pairs = 0
for width in range(1, 7):
    for a in range(1 << width):
        for d in range(1 << width):
            q, r = udivrem(a, d, width)
            safe, is_zero = safe_divisor(d, width)
            qs, rs = divmod(a, safe)
            actual = ((1 << width)-1, a) if is_zero else (qs, rs)
            check(actual == (q, r))
            check(d == 0 or (q*d+r == a and 0 <= r < d))
            division_pairs += 1
rejects(lambda: udivrem(-1, 1, 16))
rejects(lambda: udivrem(1 << 16, 1, 16))

directed = [
    (0x3F800000, 0x40000000, 0x40000000, 0),
    (0x80000000, 0x40000000, 0x80000000, 0),
    (0x80000000, 0xC0000000, 0, 0),
    (0, 0x7F800000, 0x7FC00000, 16),
    (0x7FC12345, 0x3F800000, 0x7FC00000, 0),
    (0x7F812345, 0x3F800000, 0x7FC00000, 16),
    (0x7F800000, 0xBF800000, 0xFF800000, 0),
    (0x7F7FFFFF, 0x40000000, 0x7F800000, 5),
    (1, 0x3F800000, 1, 0),
    (1, 0x3F000000, 0, 3),
    (3, 0x3F000000, 2, 3),
    (0x00800000, 0x3F000000, 0x00400000, 0),
    (0x00800000, 0x3F7FFFFF, 0x00800000, 3),
    (0x3F800001, 0x3F800001, 0x3F800002, 1),
]
for a, b, bits, flags in directed:
    check(f32_mul(a, b) == FPResult(bits, flags), f'directed {a:08x} * {b:08x}')
    check(f32_mul(b, a) == FPResult(bits, flags), 'operand symmetry')

rng = random.Random(20261026)
nearest_checks = 0
for _ in range(2000):
    a, b = rng.getrandbits(32), rng.getrandbits(32)
    if (a >> 23 & 255) == 255 or (b >> 23 & 255) == 255:
        continue
    result = f32_mul(a, b)
    magnitude = result.bits & 0x7FFFFFFF
    if magnitude >= 0x7F7FFFFF:
        continue
    exact = abs(fp_fraction(a)*fp_fraction(b))
    rounded = fp_fraction(magnitude)
    distance = abs(exact-rounded)
    if magnitude:
        check(distance <= abs(exact-fp_fraction(magnitude-1)))
        if distance == abs(exact-fp_fraction(magnitude-1)):
            check(magnitude & 1 == 0)
    check(distance <= abs(exact-fp_fraction(magnitude+1)))
    if distance == abs(exact-fp_fraction(magnitude+1)):
        check(magnitude & 1 == 0)
    check(bool(result.flags & 1) == (exact != rounded))
    if magnitude < 0x00800000 and exact != rounded:
        check(bool(result.flags & 2))
    check(not result.flags & 2 or bool(result.flags & 1))
    nearest_checks += 1

case_evaluations = 0
for case in manifest['cases']:
    for sample in range(128):
        inputs = {name: (0 if sample == 0 else (1 << width)-1 if sample == 1 else rng.getrandbits(width))
                  for name, width in case['inputs'].items()}
        output = evaluate_case(case['id'], inputs)
        check(set(output) == set(case['outputs']))
        case_evaluations += 1
    rejects(lambda case=case: evaluate_case(case['id'], {}))
check(evaluate_case('H_F1', {'a':0, 'b':0x7F800000, 'bypass':0x7F812345, 'select':0}) == {'bits':0x7F812345, 'flags':0})
check(f32_chain(0x7F7FFFFF, 0x40000000, 0) == FPResult(0x7FC00000, 21))
check(evaluate_case('M1', {'a':0xFFFFFFFF, 'b':0xFFFFFFFF, 'c':0xFFFFFFFFFFFFFFFF}) == {'y':0xFFFFFFFE00000000})
check(evaluate_case('M2', {'a':65535, 'b':65535, 'c':65535, 'd':65535}) == {'y':8589672450})
check(evaluate_case('D1', {'a':65535,'d':0}) == {'q':65535,'r':65535})
check(evaluate_case('H_M1', {'a':0xFFFFFFFF,'b':0xFFFFFFFF,'c':0xFFFFFFFF,'select':1}) == {'y':0})

# Width normalization, truncation and control/data role separation.
full = node_cost('Mul', [Value(32), Value(32)], Value(64))
check(full == Cost(21, 1024))
check(node_cost('Mul', [Value(32), Value(32)], Value(64)) == full)  # following Trunc is separate
check(node_cost('Mul', [Value(32), Value(32)], Value(32)) == Cost(18, 1024))
check(node_cost('Mul', [Value(16), Value(16)], Value(32)) == Cost(18, 256))
extended = Value(32, known_zero=0xFFFF0000, facts_valid=True)
check(node_cost('Mul', [extended, extended], Value(32)) == Cost(18, 256))
check(Value(32, known_zero=0xFFFF0000).effective_width == 32)
check(node_cost('AddCarry', [Value(32), Value(32)], Value(33)) == Cost(6, 33))
check(node_cost('Trunc', [Value(64)], Value(32)) == Cost(0, 0))
check(node_cost('Shl', [Value(32)], Value(32), index=Value(32, literal=3)) == Cost(0, 0))
check(node_cost('Shl', [Value(32)], Value(32), index=Value(5)) == Cost(6, 192))
check(node_cost('Ite', [Value(8), Value(8)], Value(8)) == Cost(1, 8))
check(node_cost('Case', [Value(8)]*2, Value(8)) == Cost(1, 8))
check(node_cost('Case', [Value(8)]*4, Value(8)) == Cost(2, 32))
check(node_cost('Case', [Value(8)], Value(8), single_choice_proven=True) == Cost(0, 0))
check(lookup_choices(Value(32), 8, truncate_to_bits=3) == 8)
check(lookup_choices(Value(3, known_zero=4, facts_valid=True), 8) == 4)
check(lookup_choices(Value(3, known_one=3, facts_valid=True), 8) == 2)
check(node_cost('Lookup', [Value(8)]*8, Value(8), index=Value(1), table_count=8) == Cost(1, 8))
check(node_cost('Lookup', [Value(8)]*8, Value(8), index=Value(3), table_count=8) == Cost(3, 64))
# Plan 7.5: selections retain the result TYPE width even with proven high zeros.
# Cover both narrow data types and wide data types narrowed by static facts.
narrowed32 = Value(32, known_zero=0xFFFFFF00, facts_valid=True)
for alternatives in ([Value(8)]*2, [narrowed32]*2):
    check(node_cost('Ite', alternatives, narrowed32) == Cost(1, 32),
          'Ite must charge the 32-bit result type')
    check(node_cost('Case', alternatives, narrowed32) == Cost(1, 32),
          'Case must charge the 32-bit result type')
    check(node_cost('Lookup', alternatives, narrowed32, index=Value(1), table_count=2) == Cost(1, 32),
          'Lookup must charge the 32-bit result type')
check(node_cost('Case', [narrowed32]*4, narrowed32) == Cost(2, 128))
check(node_cost('Lookup', [narrowed32]*8, narrowed32, index=Value(3), table_count=8) == Cost(3, 256))
check(node_cost('ArrayAccess', [narrowed32]*2, narrowed32, index=Value(1), table_count=2) == Cost(1, 32))
wide_data = Value(64, known_zero=0xFFFFFF0000000000, facts_valid=True)
check(node_cost('Ite', [wide_data, narrowed32], narrowed32) == Cost(1, 40))
# The selection exception must not disable effective-width charging elsewhere.
check(node_cost('Add', [narrowed32]*2, narrowed32) == Cost(4, 8))
check(node_cost('BitAnd', [narrowed32]*2, narrowed32) == Cost(1, 8))
selection_cost = node_cost('Ite', [narrowed32]*2, narrowed32)
check(candidate_score(selection_cost.delay, selection_cost.area, 0, 0, 'selection')
      > candidate_score(1, 16, 0, 0, 'competitor'), 'equal-delay ranking must use the full selection area')
rejects(lambda: lookup_choices(Value(3), 6))
rejects(lambda: node_cost('Lookup', [Value(8)]*8, Value(8), index=Value(3, literal=2), table_count=8))
rejects(lambda: node_cost('ExternalIP', [], Value(8), transaction_constant=True))
rejects(lambda: Value(8, known_zero=1, known_one=1, facts_valid=True))
check(region_delay({'a': Cost(3, 4), 'b': Cost(3, 4), 'c': Cost(1, 2)}, {'c':['a','b']}) == 4)
rejects(lambda: region_delay({'a':Cost(1,1), 'b':Cost(1,1)}, {'a':['b'],'b':['a']}))
entries = [('q', Cost(80,256)), ('r', Cost(80,256))]
check(combinational_area(entries) == 512)
check(combinational_area(entries, verified_shared_divrem={'q':'qr','r':'qr'}) == 256)
check(within_relative_cap(105,100) and not within_relative_cap(106,100))
check(candidate_score(3,100,16,2,'a') < candidate_score(3,100,16,2,'b'))
check(candidate_score(3,100,16,2,'z') < candidate_score(4,1,1,1,'a'))
# Compare a declared two-stage original/split structure using the same rules.
# This is a structural contract prototype, not a claim about compiler grouping.
partial_cost = node_cost('Mul', [Value(16), Value(16)], Value(32))
reduction_costs = [node_cost('AddCarry', [Value(32), Value(32)], Value(33)),
                   node_cost('AddCarry', [Value(33), Value(33)], Value(34)),
                   node_cost('Add', [Value(64), Value(64)], Value(64))]
split_delay = max(partial_cost.delay, sum(cost.delay for cost in reduction_costs))
check(split_delay == 19)
check(candidate_score(split_delay, 4*partial_cost.area+sum(c.area for c in reduction_costs),128,4,'split16')
      < candidate_score(full.delay,full.area,64,1,'original'))
for _ in range(1000):
    a,b = rng.getrandbits(32),rng.getrandbits(32)
    lo=(1<<16)-1
    partial=[(a&lo)*(b&lo), (a&lo)*(b>>16), (a>>16)*(b&lo), (a>>16)*(b>>16)]
    combined=partial[0]+((partial[1]+partial[2])<<16)+(partial[3]<<32)
    check(combined == a*b and (combined & 0xFFFFFFFF) == (a*b & 0xFFFFFFFF))
for case in manifest['cases']:
    # Synthetic timings test the formula; these are not physical measurements.
    calibration = {name:100 for name in case['calibration_path']}
    check(target_period_ps(case, calibration, 20) == (185 if case['id'] == 'D2' else 130))
    rejects(lambda case=case: target_period_ps(case, {}, 20))
rejects(lambda: target_period_ps(manifest['cases'][0], {'mul_u32_full64':-1, 'add_u64':1}, 20))

softfloat_count = 0
softfloat_details = None
source = os.environ.get('ARITHMETIC_SOFTFLOAT_DIR')
if source:
    with tempfile.TemporaryDirectory(prefix='arithmetic-softfloat-') as directory:
        oracle = SoftFloatOracle(Path(source), Path(directory)/'oracle.so')
        rng = random.Random(730021)
        edges = [0,0x80000000,1,3,0x007FFFFF,0x00800000,0x00800001,
                 0x3F000000,0x3F7FFFFF,0x3F800000,0x3F800001,
                 0x40000000,0x7F7FFFFF,0xFF7FFFFF,0x7F800000,0xFF800000,
                 0x7FC00000,0x7F812345,0xFFC01234,0xFF812345]
        pairs = [(a,b) for a in edges for b in edges]
        pairs += [(rng.getrandbits(32), rng.getrandbits(32)) for _ in range(20000)]
        for a,b in pairs:
            expected = oracle.multiply(a,b)
            actual = f32_mul(a,b)
            check((actual.bits,actual.flags) == expected,
                  f'SoftFloat mismatch {a:08x}*{b:08x}: {actual}, {expected}')
            softfloat_count += 1
        softfloat_details = {'source':str(Path(source).resolve()), 'source_sha256':oracle.source_hashes,
                             'build_command':oracle.command, 'vectors':softfloat_count}

freeze_path = ROOT/'experiments/arithmetic/freeze_v3.json'
freeze = check_freeze(freeze_path)
cost_config = json.loads(SIMPLE_COST_CONFIG.read_text())

report = {'status':'passed', 'checks':checks, 'division_exhaustive_pairs':division_pairs,
          'fp_directed_vectors':len(directed), 'fp_exact_nearest_checks':nearest_checks,
          'case_reference_evaluations':case_evaluations, 'partition':partition,
          'simple_cost_structural_checks':'passed',
          'simple_cost_version':cost_config['version'], 'width_rule_version':cost_config['width_rule_version'],
          'freeze':{'path':str(freeze_path.relative_to(ROOT)), 'version':freeze['version'],
                    'files_checked':len(freeze['files_sha256'])},
          'mul_candidate_prototype':{'L':2,'original_max_stage_cost':full.delay,
                                      'split_max_stage_cost':split_delay,'selected_by_C':'split16'},
          'softfloat_crosscheck':softfloat_details,
          'physical_measurements_read':False, 'hardware_arithmetic_integration':'not_run'}
if os.environ.get('ARITHMETIC_REPORT'):
    Path(os.environ['ARITHMETIC_REPORT']).write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
