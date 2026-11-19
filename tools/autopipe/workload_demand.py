"""Frozen v10 runtime functions; extracted without numerical edits from workload_demand.py."""
from collections import deque

from functools import lru_cache

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
