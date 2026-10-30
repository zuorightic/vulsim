"""Fixed operation/width experiment costs, independent of backend measurements.

Consumes explicitly normalized scalar DAGs. This is the step-two executable
contract; the compiler CostProvider adapter and placement are later steps.
"""
from dataclasses import dataclass
from fractions import Fraction
import json
from pathlib import Path

from .contracts import ContractError, positive_int, topological

CONFIG = Path(__file__).resolve().parent / 'configs/fixed_op_width_v1.json'
WIRE = {'Input', 'Constant', 'Assign', 'Cast', 'ZExt', 'SExt', 'Trunc',
        'Slice', 'Concat', 'Repeat', 'ConstantShift'}
UNIT = {'Add', 'Sub', 'AddCarry', 'Neg', 'Eq', 'Ne', 'Lt', 'Le', 'Gt', 'Ge',
        'BitAnd', 'BitOr', 'BitXor', 'BitNot', 'LogicAnd', 'LogicOr', 'LogicNot',
        'Ite', 'ReduceAnd', 'ReduceOr', 'ReduceXor'}
DYNAMIC = {'Shl', 'Shr', 'DynamicBitSelect', 'DynamicSlice', 'DynamicWriteSlice', 'DynamicWriteBit'}


@dataclass(frozen=True)
class Cost:
    delay_weight: Fraction
    comb_weight: Fraction


def node_cost(op, data_widths, result_width, *, constant_shift=False,
              transaction_constant=False, diagnostic_square_mul=False):
    positive_int(result_width, 'result width')
    for width in data_widths:
        positive_int(width, 'input billing width')
    if op not in WIRE | UNIT | DYNAMIC | {'Mul', 'Div', 'Mod'}:
        raise ContractError('cost_uncovered', f'lower or reject operation before cost query: {op}',
                            stage='cost', operation=op)
    if op in {'Mul', 'Div', 'Mod'} and len(data_widths) != 2:
        raise ContractError('invalid_expansion_graph', f'{op}: two data operands required', stage='cost')
    config = json.loads(CONFIG.read_text())
    if transaction_constant or op in WIRE or (op in ('Shl', 'Shr') and constant_shift):
        return Cost(Fraction(0), Fraction(0))
    if op in ('Mul', 'Div', 'Mod'):
        width = max(data_widths)
        bucket = next((w for w in config['width_buckets'] if w >= width), None)
        if bucket is None:
            raise ContractError('cost_uncovered', 'arithmetic input width exceeds table', stage='cost', width=width)
        row = config['operations'][op]
        delay = Fraction(row['delay_weight'][str(bucket)])
        comb = (Fraction(bucket*bucket, 64) if op == 'Mul' and diagnostic_square_mul
                else Fraction(row['comb_weight'][str(bucket)]))
        return Cost(delay, comb)
    key = 'dynamic' if op in DYNAMIC else 'unit'
    row = config['categories'][key]
    return Cost(Fraction(row['delay_weight']), Fraction(row['comb_weight']))


def graph_cost(graph, *, verified_shared_divrem=None, diagnostic_square_mul=False):
    """Longest dependency path and sum over actual shared nodes.

    Zero extension is stripped only by following validated explicit ZExt nodes.
    An ordinary wide typed input remains wide; no observed value can shrink it.
    Optional shared Div/Mod receipts must identify the same normalized operands.
    """
    from .case_generator import validate_graph
    nodes = validate_graph(graph)
    by_id = {n['id']: n for n in nodes}
    live, stack = set(graph['outputs'].values()), list(graph['outputs'].values())
    while stack:
        for dep in by_id[stack.pop()]['deps']:
            if dep not in live:
                live.add(dep)
                stack.append(dep)
    costs, constant, arrivals, width_audit = {}, {}, {}, {}
    def billing_width(name):
        node = by_id[name]
        while node['op'] == 'ZExt':
            node = by_id[node['deps'][0]]
        return node['width']
    for n in nodes:
        name, deps = n['id'], n['deps']
        constant[name] = n['op'] != 'Input' and all(constant[d] for d in deps)
        if name not in live:
            continue
        widths = [billing_width(d) for d in deps]
        cost = node_cost(n['op'], widths, n['width'],
                         constant_shift=n['op'] in ('Shl', 'Shr') and constant[deps[1]],
                         transaction_constant=constant[name], diagnostic_square_mul=diagnostic_square_mul)
        costs[name] = cost
        arrivals[name] = cost.delay_weight + max((arrivals[d] for d in deps), default=Fraction(0))
        if n['op'] in ('Mul', 'Div', 'Mod'):
            width_audit[name] = {'input_type_widths': [by_id[d]['width'] for d in deps],
                                 'billing_widths': widths, 'result_width': n['width'],
                                 'basis': 'explicit_ZExt_chain_or_conservative_type'}
    excluded = set()
    shared_members = set()
    implementations = set()
    for receipt in verified_shared_divrem or []:
        implementation = receipt.get('implementation_id')
        members = receipt.get('members', [])
        if (not implementation or implementation in implementations or not receipt.get('proof_ref')
                or len(members) != 2 or len(set(members)) != 2
                or any(m not in costs or m in shared_members for m in members)):
            raise ContractError('invalid_expansion_graph', 'invalid shared implementation receipt', stage='cost')
        q, r = [by_id[m] for m in members]
        if ({q['op'], r['op']} != {'Div', 'Mod'} or q['deps'] != r['deps']
                or q['width'] != r['width'] or costs[members[0]] != costs[members[1]]):
            raise ContractError('invalid_expansion_graph', 'Div/Mod sharing is not established', stage='cost')
        excluded.add(members[1])
        shared_members.update(members)
        implementations.add(implementation)
    return {'mode': 'fixed-op-width-v1', 'delay_unit': 'abstract', 'comb_unit': 'abstract',
            'delay_weight': max(arrivals.values(), default=Fraction(0)),
            'comb_weight': sum((cost.comb_weight for name, cost in costs.items() if name not in excluded), Fraction(0)),
            'node_costs': costs, 'width_audit': width_audit,
            'shared_implementations': sorted(implementations)}


def lower_priority_case(builder, name, alternatives, default, width):
    """First true condition wins; return actual ordered Mux nodes."""
    result = default
    for number, (condition, value) in reversed(list(enumerate(alternatives))):
        result = builder.node(f'{name}_{number}', 'Ite', width, condition, value, result)
    return result


def lower_lookup(builder, name, index, entries, width, *, out_of_range=None):
    """Actual binary selection network, never a k-way cost-only placeholder.

    An explicit index width limits reachability. Non-power-of-two tables require
    a defined default whenever any possible index can exceed the table size.
    """
    by_id = {n['id']: n for n in builder.nodes}
    if index not in by_id or not entries or any(e not in by_id for e in entries):
        raise ContractError('invalid_expansion_graph', 'lookup references are incomplete')
    index_node = by_id[index]
    bits = index_node['width']
    if bits > 12 or len(entries) > 4096:
        raise ContractError('template_ineligible', 'selection network exceeds declared generation limit')
    if any(by_id[e]['width'] != width for e in entries):
        raise ContractError('width_contract_violation', 'lookup alternatives have different widths')
    if out_of_range is not None and (out_of_range not in by_id or by_id[out_of_range]['width'] != width):
        raise ContractError('width_contract_violation', 'invalid lookup default')
    if index_node['op'] == 'Constant':
        value = index_node['params']['value']
        if value < len(entries):
            return entries[value]
        if out_of_range is not None:
            return out_of_range
        raise ContractError('template_ineligible', 'undefined constant lookup index')
    size = 1 << bits
    if size > len(entries) and out_of_range is None:
        raise ContractError('template_ineligible', 'lookup has reachable undefined indices')
    level = [entries[i] if i < len(entries) else out_of_range for i in range(size)]
    for bit in range(bits):
        select = builder.node(f'{name}_index_{bit}', 'Slice', 1, index, low=bit)
        level = [builder.node(f'{name}_level_{bit}_{i//2}', 'Ite', width,
                              select, level[i+1], level[i]) for i in range(0, len(level), 2)]
    return level[0]


def candidate_score(delay_weight, comb_weight, register_bits, register_count, candidate_id):
    if any(x < 0 for x in (delay_weight, comb_weight, register_bits, register_count)):
        raise ValueError('negative candidate metric')
    return (delay_weight, comb_weight+register_bits, register_bits, register_count, candidate_id)


def state_cost(chains, *, valid_boundaries=0):
    """One shared chain per value; callers provide materialized live ranges."""
    if type(valid_boundaries) is not int or valid_boundaries < 0:
        raise ValueError('invalid valid chain length')
    seen, total, count = set(), valid_boundaries, valid_boundaries
    for chain in chains:
        name = chain['source']
        width = positive_int(chain['width'], 'register width')
        start, end = chain['producer_stage'], chain['last_consumer_stage']
        if name in seen or type(start) is not int or type(end) is not int or not 0 <= start <= end:
            raise ValueError('duplicate or invalid shared register chain')
        seen.add(name)
        total += width*(end-start)
        count += end-start
    return {'register_bits': total, 'register_signals': count, 'state_weight': total}
