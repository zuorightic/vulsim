"""Structural prototype of the frozen B/C rules, not a physical cost model.

Inputs describe normalized scalar BEIR nodes. The C++ compiler adapter and
group-constrained scheduling are later steps; no existing scheduler is changed.
"""
from dataclasses import dataclass
import json
from pathlib import Path

CONFIG = Path(__file__).resolve().parent/'configs/simple_cost_v1.json'


@dataclass(frozen=True)
class Value:
    width: int
    known_zero: int = 0
    known_one: int = 0
    facts_valid: bool = False
    literal: int | None = None

    def __post_init__(self):
        if self.width <= 0:
            raise ValueError('positive width required')
        mask = (1 << self.width)-1
        if self.known_zero < 0 or self.known_one < 0 or (self.known_zero | self.known_one) & ~mask:
            raise ValueError('known bits exceed type width')
        if self.facts_valid and self.known_zero & self.known_one:
            raise ValueError('conflicting static facts')
        if self.literal is not None and not 0 <= self.literal <= mask:
            raise ValueError('literal exceeds type width')
        if self.facts_valid and self.literal is not None:
            if self.literal & self.known_zero or self.literal & self.known_one != self.known_one:
                raise ValueError('literal contradicts static facts')

    @property
    def effective_width(self) -> int:
        if self.literal is not None:
            return max(1, self.literal.bit_length())
        possible = ((1 << self.width)-1) & ~(self.known_zero if self.facts_valid else 0)
        return max(1, possible.bit_length())


@dataclass(frozen=True)
class Cost:
    delay: int
    area: int


def _selection(k: int, width: int, single_choice_proven: bool) -> Cost:
    if k == 1 and single_choice_proven:
        return Cost(0, 0)
    if k < 2:
        raise ValueError('single choice must be proven to be wiring')
    return Cost((k-1).bit_length(), width if k == 2 else k*width)


def lookup_choices(index: Value, count: int, *, truncate_to_bits: int | None = None) -> int:
    if count <= 0:
        raise ValueError('empty lookup')
    required = max(1, (count-1).bit_length())
    if truncate_to_bits is not None and truncate_to_bits != required:
        raise ValueError('index normalization does not match the lowered table')
    width = min(index.width, truncate_to_bits) if truncate_to_bits is not None else index.width
    mask = (1 << width)-1
    if index.literal is not None:
        value = index.literal & mask
        if value >= count:
            raise ValueError('undefined lookup index')
        return 1
    zero = index.known_zero & mask if index.facts_valid else 0
    one = index.known_one & mask if index.facts_valid else 0
    if mask & ~zero >= count:
        raise ValueError('possible undefined lookup index')
    # The possible maximum was checked, so at most count candidates are visited.
    return sum(1 for value in range(min(count, mask+1)) if not value & zero and value & one == one)


WIRE = {'Input', 'Constant', 'Assign', 'Cast', 'ZExt', 'SExt', 'Trunc',
        'ZeroExtend', 'SignExtend', 'Truncate', 'Slice', 'BitSelect',
        'WriteSlice', 'WriteBit', 'Concat', 'Repeat', 'PortRead', 'Aggregate'}
BIT = {'BitAnd', 'BitOr', 'BitXor', 'LogicAnd', 'LogicOr', 'LogicNot', 'BitNot'}
ADD = {'Add', 'Sub', 'AddCarry', 'Eq', 'Ne', 'Lt', 'Le', 'Gt', 'Ge', 'Neg'}
DYNAMIC = {'Shl', 'Shr', 'DynamicBitSelect', 'DynamicSlice', 'DynamicWriteSlice',
           'DynamicWriteBit', 'ReduceAnd', 'ReduceOr', 'ReduceXor'}


def node_cost(op: str, data: list[Value], result: Value, *,
              index: Value | None = None, table_count: int | None = None,
              truncate_to_bits: int | None = None, single_choice_proven: bool = False,
              transaction_constant: bool = False) -> Cost:
    # Reject unknown operators even when a caller marks a subgraph constant.
    supported = WIRE | BIT | ADD | DYNAMIC | {'Mul', 'Div', 'Mod', 'Ite', 'Case', 'Lookup', 'ArrayAccess'}
    if op not in supported:
        raise ValueError(f'unsupported normalized operation: {op}')
    if transaction_constant or op in WIRE:
        return Cost(0, 0)
    width = max([result.effective_width] + [value.effective_width for value in data])
    h = width.bit_length()  # ceil(log2(width+1)), without floating-point rounding.
    if op == 'Mul':
        if len(data) != 2:
            raise ValueError('Mul requires two data operands')
        m, n = (value.effective_width for value in data)
        return Cost(3*max(m, n, result.width).bit_length(), m*n)
    if op in {'Div', 'Mod'}:
        return Cost(width*h, width*width)
    if op in BIT:
        return Cost(1, width)
    if op in ADD:
        return Cost(h, width)
    if op in DYNAMIC:
        if op in {'Shl', 'Shr'} and index is not None and index.literal is not None:
            return Cost(0, 0)
        return Cost(h, width*h)
    # Plan 7.5 keeps the result type width for selections, even if its high
    # bits are proven zero. Ordinary arithmetic above uses effective widths.
    selection_width = max([result.width] + [value.effective_width for value in data])
    if op == 'Ite':
        if len(data) != 2:
            raise ValueError('Ite requires exactly two data alternatives')
        return Cost(1, selection_width)
    if op == 'Case':
        return _selection(len(data), selection_width, single_choice_proven)
    if index is None or table_count is None or len(data) != table_count:
        raise ValueError('lookup requires normalized index and all table entries')
    k = lookup_choices(index, table_count, truncate_to_bits=truncate_to_bits)
    return _selection(k, selection_width, single_choice_proven)


def region_delay(costs: dict[str, Cost], dependencies: dict[str, list[str]]) -> int:
    """DAG critical path, not the sum of parallel members; reject contraction cycles."""
    pending = set(costs)
    arrival = {}
    while pending:
        ready = sorted(name for name in pending if all(dep in arrival for dep in dependencies.get(name, [])))
        if not ready:
            raise ValueError('cyclic region or missing dependency')
        for name in ready:
            arrival[name] = costs[name].delay + max((arrival[dep] for dep in dependencies.get(name, [])), default=0)
            pending.remove(name)
    return max(arrival.values(), default=0)


def combinational_area(entries: list[tuple[str, Cost]], *,
                       verified_shared_divrem: dict[str, str] | None = None) -> int:
    """Only already-proven shared quotient/remainder implementations count once."""
    shared = verified_shared_divrem or {}
    seen = {}
    total = 0
    if len({name for name, _ in entries}) != len(entries):
        raise ValueError('duplicate node identity')
    for name, cost in entries:
        implementation = shared.get(name)
        if implementation is not None:
            if implementation in seen:
                if seen[implementation] != cost:
                    raise ValueError('inconsistent shared implementation costs')
                continue
            seen[implementation] = cost
        total += cost.area
    return total


def candidate_score(delay: int, area: int, register_bits: int,
                    register_count: int, candidate_id: str) -> tuple:
    if min(delay, area, register_bits, register_count) < 0:
        raise ValueError('negative candidate metric')
    return delay, area+register_bits, register_bits, register_count, candidate_id


def within_relative_cap(delay: int, baseline: int) -> bool:
    config = json.loads(CONFIG.read_text())['relative_delay_limit']
    if delay < 0 or baseline < 0:
        raise ValueError('negative abstract delay')
    return delay*config['denominator'] <= baseline*config['numerator']
