"""Independent read-only audit; no selector, model, RTL or EDA mutation.

Propagate conservative unsigned bit facts and upper bounds through the frozen
graphs. Unsupported operations retain only the graph's existing bit facts.
This diagnoses software state masks, not the number of mapped physical flops.
"""
import collections
import functools
import hashlib
import itertools
import json
import pathlib
import random
import sys

ROOT = pathlib.Path('/home/zyrv/vulsim')
LIVE = ROOT.parent / 'vulsim-artifacts/workload-equivalent-two-depths-v1'
OUT = pathlib.Path(__file__).resolve().parent
sys.setrecursionlimit(20000)


def read(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def limb_mask(words):
    return sum(int(word, 16) << (64 * i) for i, word in enumerate(words))


def resize(f, width):
    old_width, zero, one, upper = f
    mask = (1 << width) - 1
    if width > old_width:
        zero |= mask ^ ((1 << old_width) - 1)
    # Truncation is not monotone: do not mask an interval endpoint.
    return width, zero & mask, one & mask, min(upper, mask)


def trailing_zero(f):
    width, zero, _, upper = f
    if upper == 0:
        return 1000000  # A literal zero must not cap the result at its width.
    i = 0
    while i < width and zero & (1 << i):
        i += 1
    return i


def facts_for(raw):
    nodes = {n['id']: n for n in raw['nodes']}

    def operand(a):
        if a['node'] is not None:
            return resize(node(a['node']), a['width'])
        width = a['width']
        value = int(a['literal_hex'], 16) & ((1 << width) - 1)
        return width, ((1 << width) - 1) ^ value, value, value

    @functools.lru_cache(None)
    def node(i):
        n = nodes[i]
        width = n['width']
        mask = (1 << width) - 1
        old_zero = int(n['known_zero_hex'], 16) & mask
        old_one = int(n['known_one_hex'], 16) & mask
        zero, one, upper = 0, 0, mask
        op = n['operation']
        # Input operands are port descriptions, not literals.
        args = [operand(a) for a in n['operands']] if op != 'input' else []
        unsigned = not any(a.get('signed', False) for a in n['operands'])
        if args and unsigned:
            if op == 'wire':
                _, zero, one, upper = resize(args[0], width)
            elif op == 'slice':
                _, z, o, u = args[0]
                lo = n['lo']
                zero, one = (z >> lo) & mask, (o >> lo) & mask
                upper = min(mask, u >> lo)
            elif op == 'concat':
                zero, one, upper = 0, 0, 0
                for w, z, o, u in args:
                    zero = (zero << w) | z
                    one = (one << w) | o
                    upper = (upper << w) | u
                zero, one = zero & mask, one & mask
                upper = min(upper, mask)
            elif op == 'mul':
                upper = min(mask, args[0][3] * args[1][3])
                tz = min(width, sum(trailing_zero(a) for a in args))
                zero = (1 << tz) - 1
            elif op == 'adc':
                terms = [resize(a, width) for a in args]
                carry = {0}
                for bit in range(width):
                    choices = []
                    for _, z, o, _ in terms:
                        choices.append((0,) if z >> bit & 1 else (1,) if o >> bit & 1 else (0, 1))
                    sums = {sum(values) + c for values in itertools.product(*choices) for c in carry}
                    possible = {v & 1 for v in sums}
                    if possible == {0}:
                        zero |= 1 << bit
                    elif possible == {1}:
                        one |= 1 << bit
                    carry = {v >> 1 for v in sums}
                upper = min(mask, sum(a[3] for a in args))
        # Every bit above a conservative maximum is also provably zero.
        zero |= mask ^ ((1 << upper.bit_length()) - 1)
        if (zero & old_one) or (one & old_zero):
            raise AssertionError(('existing facts contradict independent facts', i))
        zero |= old_zero
        one |= old_one
        assert not zero & one
        upper = min(upper, mask ^ zero)
        return width, zero, one, upper

    return node, nodes


def audit(folder):
    raw = read(folder / 'graph.json')
    state = read(folder / 'state.json')
    fact, nodes = facts_for(raw)
    stages = collections.defaultdict(lambda: dict(original_variable_bits=0,
        additional_proven_zero_bits=0, reset_compatible_zero_bits=0, affected_slots=0))
    examples = []
    for slot in state['slots']:
        if slot['valid']:
            continue
        _, zero, _, _ = fact(slot['origin'])
        var = limb_mask(slot['variable_mask_hex'])
        assert var.bit_count() == slot['variable_bits']
        reset = limb_mask(slot['reset_hex'])
        extra = zero & var
        compatible = extra & ~reset
        row = stages[slot['stage']]
        row['original_variable_bits'] += var.bit_count()
        row['additional_proven_zero_bits'] += extra.bit_count()
        row['reset_compatible_zero_bits'] += compatible.bit_count()
        row['affected_slots'] += bool(extra)
        if extra and len(examples) < 8:
            examples.append(dict(origin=slot['origin'], stage=slot['stage'],
                operation=nodes[slot['origin']]['operation'], declared_width=slot['declared_width'],
                original_variable_bits=var.bit_count(), proven_zero_in_variable_bits=extra.bit_count(),
                additional_zero_mask_hex=hex(extra), reset_compatible=compatible == extra,
                external_capture=slot['external_capture']))
    total = {k: sum(v[k] for v in stages.values()) for k in next(iter(stages.values()), {})}
    assert total['original_variable_bits'] == state['features']['data_bits']
    total['conservative_remaining_bits'] = total['original_variable_bits'] - total['reset_compatible_zero_bits']
    return dict(folder=str(folder), graph_sha256=sha(folder / 'graph.json'),
        state_sha256=sha(folder / 'state.json'), operations=dict(collections.Counter(n['operation'] for n in raw['nodes'])),
        totals=total, stages=dict(stages), examples=examples,
        unsupported_operations=sorted({n['operation'] for n in raw['nodes']} - {'input', 'wire', 'slice', 'concat', 'mul', 'adc'}))


def enumerate_witness(folder):
    raw = read(folder / 'graph.json')
    fact, nodes = facts_for(raw)
    def evaluate(i, inputs, cache):
        if i in cache:
            return cache[i]
        n = nodes[i]
        if n['operation'] == 'input':
            value = inputs.get(i, 0)
        else:
            args = [(evaluate(a['node'], inputs, cache) if a['node'] is not None else int(a['literal_hex'], 16))
                    & ((1 << a['width']) - 1) for a in n['operands']]
            op = n['operation']
            if op == 'wire': value = args[0]
            elif op == 'slice': value = args[0] >> n['lo']
            elif op == 'mul': value = args[0] * args[1]
            elif op == 'adc': value = sum(args)
            elif op == 'concat':
                value = 0
                for a, v in zip(n['operands'], args): value = value << a['width'] | v
            else: raise AssertionError(op)
        value &= (1 << n['width']) - 1
        cache[i] = value
        return value
    union = 0
    maximum = 0
    count = 0
    for a, b, c in itertools.product(range(16), repeat=3):
        v = evaluate(4111, {0: a, 1: (b << 8) | (c << 12)}, {})
        assert v == (a * b << 8) + (a * c << 12)
        assert v & fact(4111)[1] == 0
        union |= v
        maximum = max(maximum, v)
        count += 1
    maximum_input = (1 << 128) - 1
    rng = random.Random(20261116)
    vectors = [(0, 0), (maximum_input, maximum_input), (1, maximum_input),
               (maximum_input, 1), (1 << 127, 1 << 127)]
    vectors += [(rng.getrandbits(128), rng.getrandbits(128)) for _ in range(59)]
    checked = 0
    for a, b in vectors:
        cache = {}
        assert evaluate(4, {0: a, 1: b, 2: 1}, cache) == a * b
        for i in nodes:
            v = evaluate(i, {0: a, 1: b, 2: 1}, cache)
            _, zero, one, upper = fact(i)
            assert v & zero == 0 and v & one == one and v <= upper, (i, v)
            checked += 1
    return dict(origin=4111, expression='(A[3:0]*B[11:8]<<8)+(A[3:0]*B[15:12]<<12)',
        exhaustive_assignments=count, declared_width=21, original_variable_bits=21,
        exhaustive_zero_mask_hex=hex(((1 << 21) - 1) ^ union),
        independent_proven_zero_mask_hex=hex(fact(4111)[1]), maximum=maximum,
        full_graph_concrete_vectors=len(vectors), full_graph_node_value_checks=checked,
        full_product_matches_python=True,
        note='All 12 relevant input bits enumerated; other input bits have no path to origin 4111.')


def main():
    rows = []
    cache = {}
    for plan in sorted((LIVE / 'plans').glob('*.json')):
        doc = read(plan)
        for group in read(pathlib.Path(doc['selection']))['records']:
            m = group['methods']['D']
            folder = pathlib.Path(m['rtl']).parent
            key = (sha(folder / 'graph.json'), sha(folder / 'state.json'))
            if key not in cache:
                cache[key] = audit(folder)
            rows.append(dict(cache[key], folder=str(folder), case=doc['case'], L=m['L'],
                T_ps=group['target']['T_ps'], grammar=m['grammar'], rtl_sha256=m['rtl_sha256']))
    witness_folder = ROOT.parent / 'vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software/selected/mul128/T600-L4/D'
    output = dict(version='independent-state-known-zero-audit-v1',
        new_EDA_calls=0, new_model_fits=0, frozen_sources_modified=False,
        method='Conservative unsigned ternary addition, structural bit propagation and independent operand upper bounds; no correlation assumption.',
        scope='Software state masks only; physical flop saving and revised PPA are not measured.',
        witness=enumerate_witness(witness_folder), selected_D=rows)
    (OUT / 'known-bit-audit.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(output['witness'], ensure_ascii=False))
    for r in rows:
        print(r['case'],r['L'],r['T_ps'],r['totals'],flush=True)


if __name__ == '__main__':
    main()
