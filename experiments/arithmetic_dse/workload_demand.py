"""Prospective wide Query/state inventory from real RTLzz graphs and placements.

There is no price fallback. Interface representation, semantic price support,
and physical qualification are deliberately separate results.
"""
import argparse
from collections import deque, Counter
from functools import lru_cache
import json
from pathlib import Path
from . import wide_operator_query as wide
from . import workload_regions

ARITHMETIC = {'add', 'adc', 'sub', 'mul', 'ult', 'ule', 'eq', 'mux'}
WIRE = {'wire', 'slice', 'bitselect', 'concat'}


class Graph:
    def __init__(self, raw):
        if raw['version'] != 'prospective-workload-graph-v1':
            raise ValueError('unknown graph representation')
        self.nodes, self.ports = raw['nodes'], raw['ports']
        if any(n['id'] != i or not 1 <= n['width'] <= 4096 for i, n in enumerate(self.nodes)):
            raise ValueError('dense scalar graph with widths 1..4096 required')
        self.demand = [set() for _ in self.nodes]
        queue = deque()

        def feed(i, bits):
            bits = {b for b in bits if 0 <= b < self.nodes[i]['width']}
            if not bits <= self.demand[i]:
                self.demand[i] |= bits
                queue.append(i)

        for p in self.ports:
            if not p['input']:
                for n in p['nodes']:
                    feed(n, range(p['width']))
        while queue:
            i = queue.popleft()
            n = self.nodes[i]
            if n['constant'] or n['operation'] == 'input':
                continue
            wanted, op = self.demand[i], n['operation']
            if op == 'concat':
                base = 0
                for a in reversed(n['operands']):
                    if a['node'] is not None:
                        feed(a['node'], (b - base for b in wanted))
                    base += a['width']
                if base != n['width']:
                    raise ValueError('concat width mismatch')
            else:
                for k, a in enumerate(n['operands']):
                    if a['signed']:
                        raise ValueError('unsigned graph required')
                    if a['node'] is None:
                        continue
                    if op == 'slice':
                        bits = [b + n['lo'] for b in wanted]
                    elif op == 'bitselect':
                        bits = [n['bit']]
                    elif op in ('wire', 'not'):
                        bits = wanted
                    elif op == 'adc' and k == 2 or op == 'mux' and k == 0:
                        bits = [0]
                    elif op == 'mux':
                        bits = wanted
                    elif op in ('add', 'adc', 'sub', 'mul'):
                        bits = range(max(wanted, default=-1) + 1)
                    else:
                        bits = range(a['width'])
                    feed(a['node'], bits)

    def operand(self, a):
        if a['node'] is not None:
            return self.origins(a['node'])
        value = int(a['literal_hex'], 16)
        return tuple(str((value >> b) & 1) for b in range(a['width']))

    @lru_cache(None)
    def origins(self, i):
        n = self.nodes[i]
        op, width = n['operation'], n['width']
        if op == 'concat':
            bits = tuple(b for a in reversed(n['operands']) for b in self.operand(a))
        elif op in WIRE:
            a = self.operand(n['operands'][0])
            lo = n['lo'] if op == 'slice' else n['bit'] if op == 'bitselect' else 0
            bits = (a[lo:lo + width] + ('0',) * width)[:width]
        elif op in ('and', 'or', 'xor'):
            a, b = (self.operand(x) for x in n['operands'])
            a, b = (a + ('0',)*width)[:width], (b + ('0',)*width)[:width]

            def combine(x, y, bit):
                if x == y:
                    return '0' if op == 'xor' else x
                if op == 'and':
                    return '0' if '0' in (x,y) else y if x == '1' else x if y == '1' else (i,bit)
                if op == 'or':
                    return '1' if '1' in (x,y) else y if x == '0' else x if y == '0' else (i,bit)
                return y if x == '0' else x if y == '0' else (i,bit)

            bits = tuple(combine(x,y,b) for b,(x,y) in enumerate(zip(a,b,strict=True)))
        else:
            bits = tuple((i, b) for b in range(width))
        z, o = int(n['known_zero_hex'], 16), int(n['known_one_hex'], 16)
        if z & o or len(bits) != width:
            raise ValueError('invalid known bits or mapping')
        return tuple('1' if o >> b & 1 else '0' if z >> b & 1 else value for b, value in enumerate(bits))

    def wire_equivalent(self, i):
        return all(not isinstance(b, tuple) or b[0] != i for b in self.origins(i))

    def evaluate(self, inputs):
        """Independent integer evaluation for checking proposed G ownership."""
        ports = {n: p['name'] for p in self.ports if p['input'] for n in p['nodes']}

        @lru_cache(None)
        def value(i):
            n = self.nodes[i]
            op, w = n['operation'], n['width']
            if op == 'input':
                return inputs[ports[i]] & ((1 << w)-1)
            if n['constant']:
                return int(n['known_one_hex'],16)
            args = [value(a['node']) if a['node'] is not None else int(a['literal_hex'],16) for a in n['operands']]
            if op == 'wire': result = args[0]
            elif op == 'slice': result = args[0] >> n['lo']
            elif op == 'bitselect': result = args[0] >> n['bit']
            elif op == 'concat':
                result = 0
                for a,v in zip(n['operands'],args,strict=True): result = (result << a['width']) | v
            elif op == 'add' or op == 'adc': result = sum(args)
            elif op == 'sub': result = args[0] - args[1]
            elif op == 'mul': result = args[0] * args[1]
            elif op == 'not': result = ~args[0]
            elif op == 'lnot': result = not args[0]
            elif op == 'neg': result = -args[0]
            elif op == 'land': result = bool(args[0] and args[1])
            elif op == 'lor': result = bool(args[0] or args[1])
            elif op == 'and': result = args[0] & args[1]
            elif op == 'or': result = args[0] | args[1]
            elif op == 'xor': result = args[0] ^ args[1]
            elif op == 'shl': result = args[0] << args[1]
            elif op == 'shr': result = args[0] >> args[1]
            elif op == 'mux': result = args[1] if args[0] else args[2]
            elif op == 'ult': result = args[0] < args[1]
            elif op == 'ule': result = args[0] <= args[1]
            elif op == 'ugt': result = args[0] > args[1]
            elif op == 'uge': result = args[0] >= args[1]
            elif op == 'eq': result = args[0] == args[1]
            elif op == 'ne': result = args[0] != args[1]
            else: raise ValueError('unknown graph operation '+op)
            return int(result) & ((1 << w)-1)

        return [value(i) for i in range(len(self.nodes))]

    def billing(self, a):
        while a['node'] is not None:
            n = self.nodes[a['node']]
            if n['operation'] != 'wire' or len(n['operands']) != 1 or n['operands'][0]['width'] > a['width']:
                break
            a = n['operands'][0]
        return a['width']

    @lru_cache(None)
    def roots(self, i):
        n = self.nodes[i]
        if n['constant']:
            return frozenset()
        if n['operation'] == 'input':
            return frozenset((i,))
        return frozenset().union(*(self.roots(a['node']) for a in n['operands'] if a['node'] is not None))

    def spec(self, i):
        n = self.nodes[i]
        op, args = n['operation'], n['operands']
        if op not in ARITHMETIC:
            raise ValueError('not a priced arithmetic family')
        data = args[1:] if op == 'mux' else args[:2]
        wa, wb = map(self.billing, data)
        r = max(self.demand[i]) + 1
        w = max(wa, wb) if op in ('ult', 'ule', 'eq') else max(r, wa + wb) if op == 'mul' else max(r, wa, wb)
        control = 'zero'
        if op in ('adc', 'mux'):
            bit = self.operand(args[2] if op == 'adc' else args[0])[0]
            control = {'0': 'zero', '1': 'one'}.get(bit, 'dynamic')
        spec = dict(operation=op, lhs_width=wa, rhs_width=wb, arithmetic_width=w,
                    result_lo=0, value_width=r, status='none', result_width=r,
                    carry=control, capture_banks=1)
        for name, a, width in zip(('lhs', 'rhs'), data, (wa, wb), strict=True):
            bits = self.operand(a)[:width]
            for field, token in (('zero', '0'), ('one', '1')):
                spec[f'{name}_{field}_hex'] = hex(sum(1 << b for b, v in enumerate(bits) if v == token))
        if op == 'adc' and control == 'zero':
            spec['operation'] = 'add'
        return spec


def extract(directory, target_ps):
    directory = Path(directory)
    inventory = json.loads((directory / 'inventory.json').read_text())
    graph = Graph(json.loads((directory / 'graph.json').read_text()))
    specs = {n['id']: graph.spec(n['id']) for n in graph.nodes
             if n['operation'] in ARITHMETIC and graph.demand[n['id']] and not n['constant']}
    binding_index = {i: [] for i in specs}
    for n in graph.nodes:
        if not graph.demand[n['id']] or n['operation'] in WIRE | {'input'} or graph.wire_equivalent(n['id']):
            continue
        for pin, a in enumerate(n['operands']):
            raw = graph.operand(a)
            origins = {b[0] for b in raw if isinstance(b, tuple)} & specs.keys()
            for i in sorted(origins):
                mapping = [b[1] if isinstance(b, tuple) and b[0] == i else b if isinstance(b, str) else 'external' for b in raw]
                role = 'carry' if n['operation'] == 'adc' and pin == 2 else (
                    'selector' if n['operation'] == 'mux' and pin == 0 else 'data')
                binding_index[i].append(dict(sink=n['id'], operand_index=pin, role=role, result_bit_map=mapping))
    views = []
    for view in inventory['views']:
        stages = view['placement']
        users = [set() for _ in graph.nodes]
        for n in graph.nodes:
            if graph.demand[n['id']]:
                for a in n['operands']:
                    if a['node'] is not None and stages[a['node']] == stages[n['id']]:
                        users[a['node']].add(n['id'])

        @lru_cache(None)
        def remaining(i):
            return int(i in specs) + max((remaining(j) for j in users[i]), default=0)

        state = json.loads((directory / view['directory'] / 'state.json').read_text())
        captures = [s for s in state['slots'] if not s['valid'] and s['variable_bits']]
        rows = []
        for i, spec in specs.items():
            cons, caps, control_uses = [], [], []
            connections = [dict(b, sink_stage=stages[b['sink']], crosses_stage=stages[b['sink']] != stages[i]) for b in binding_index[i]]
            grouped = {}
            for binding in connections:
                child = binding['sink']
                if child == i or child not in specs or stages[child] != stages[i]:
                    continue
                if binding['role'] != 'data':
                    control_uses.append(child)
                    continue
                child_spec = specs[child]
                n = graph.nodes[child]
                k = binding['operand_index'] - int(n['operation'] == 'mux')
                width = child_spec[('lhs_width', 'rhs_width')[k]]
                mapping = binding['result_bit_map'][:width]
                if child_spec['operation'] not in ('ult', 'ule', 'eq', 'mux'):
                    mapping = [v if b < child_spec['value_width'] else 'undemanded' for b, v in enumerate(mapping)]
                if any(type(b) is int for b in mapping):
                    grouped.setdefault(child, []).append(dict(operand_index=k, result_bit_map=mapping))
            cons = [dict(spec=specs[child], bindings=bindings,
                         other_dynamic_inputs='independent_launch; source correlations require G validation')
                    for child, bindings in sorted(grouped.items())]
            for slot in captures:
                # Charge an origin only at its immediate launch->capture edge;
                # later forwarding banks belong to S, not the arithmetic node.
                if slot['stage'] != stages[i] + 1:
                    continue
                mapping = ['undemanded' if pos not in graph.demand[slot['origin']] else
                           b[1] if isinstance(b, tuple) and b[0] == i else b if isinstance(b, str) else 'external'
                           for pos, b in enumerate(graph.origins(slot['origin']))]
                if any(type(b) is int for b in mapping):
                    caps.append(dict(banks=1, declared_width=slot['declared_width'], result_bit_map=mapping))
            local = dict(producer=spec, consumers=cons, captures=caps)
            operands = graph.nodes[i]['operands']
            data = operands[1:] if graph.nodes[i]['operation'] == 'mux' else operands[:2]
            roots = [graph.roots(a['node']) if a['node'] is not None else frozenset() for a in data]
            q = dict(version=wide.VERSION, semantics='unsigned-wide-arithmetic-semantics-v1',
                     declared_result_width=graph.nodes[i]['width'], required_result_bits=list(range(spec['result_width'])),
                     local_context=local,
                     flow_context=dict(target_platform='asap7', evaluation_stage='grt', target_period_ps=target_ps,
                                       abc_target_ps=target_ps, profile_sha256=inventory['profile_sha256'],
                                       boundary_policy='unsigned-wide-family-hierarchy-v1'),
                     topology=dict(operand_shared_input_roots=len(roots[0] & roots[1]),
                                   same_stage_remaining_depth=remaining(i)))
            reasons = []
            if control_uses:
                reasons.append('producer feeds arithmetic carry/selector pins outside current wide binding ABI')
            try:
                features = wide.features(q)
            except (ValueError, TypeError, KeyError, OverflowError) as error:
                features = None
                reasons.append(str(error))
            rows.append(dict(node=i, stage=stages[i], required_graph_bits=sorted(graph.demand[i]), query=q,
                             successor_connections=connections,
                             interface_status='represented' if features is not None and not reasons else 'needs_successor',
                             interface_gaps=reasons, control_consumers=control_uses,
                             feature_count=len(features) if features else 0,
                             price_status='not_requested; no qualification granted'))
        words = [s for s in captures if not s['external_capture']]
        views.append(dict(directory=view['directory'], operators=rows,
                          G=workload_regions.extract(graph, stages, state, target_ps),
                          state=dict(materialized_checked=state['materialized_checked'],
                                     native_data_bits=sum(s['variable_bits'] for s in words),
                                     native_words=len(words), max_word_bits=max((s['declared_width'] for s in captures), default=0),
                                     parallel_words_by_stage=dict(Counter(s['stage'] for s in words)),
                                     external_data_bits=sum(s['variable_bits'] for s in captures if s['external_capture']),
                                     input_service_data_bits=sum(p['width'] for p in graph.ports if p['input'] and p['name'] != inventory.get('input_valid_port','iv')),
                                     state_file=view['directory'] + '/state.json'),
                          functional_logic_needing_separate_price=[n['id'] for n in graph.nodes
                              if graph.demand[n['id']] and not n['constant'] and n['operation'] not in ARITHMETIC | WIRE | {'input'}
                              and not graph.wire_equivalent(n['id'])]))
    return dict(version='prospective-workload-demand-v1', target_ps=target_ps,
                actual_compiler_graph=True, actual_materialized_placements=True,
                operator_provider='one shared provider per family; no width routing', views=views,
                query_flow_contract='prospective wide owner hierarchy; native diagnostic RTL has no price/boundary qualification',
                new_EDA_calls=0, prices_requested=0, price_qualification_granted=False,
                full_D_ready=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--target-ps', type=float, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    if not 0 < args.target_ps < 1e9:
        raise ValueError('finite positive numerical T required')
    args.out.write_text(json.dumps(extract(args.directory, args.target_ps), indent=2) + '\n')
