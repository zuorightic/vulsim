"""Constant-folded Boolean work, including the flow's Kogge--Stone prefix.

This module constructs logic from semantic inputs. It reads no netlists or
physical results and launches no processes. Node counts are work proxies;
technology mapping and electrical repair remain separate modeling tasks.
"""
import math

VERSION = 'prospective-boolean-Kogge-Stone-v1'


class Circuit:
    def __init__(self):
        self.nodes = {}
        self.leaves = {}
        self._intern = {}
        self._next = 2

    def leaf(self, key):
        if key not in self.leaves:
            self.leaves[key] = self._next
            self._next += 1
        return self.leaves[key]

    def gate(self, kind, a, b=0):
        if kind == 'not':
            if a < 2:
                return 1 - a
            if a in self.nodes and self.nodes[a][0] == 'not':
                return self.nodes[a][1]
        elif kind in ('and', 'or', 'xor'):
            if kind == 'and':
                if a == 0 or b == 0:
                    return 0
                if a == 1:
                    return b
                if b == 1 or a == b:
                    return a
            elif kind == 'or':
                if a == 1 or b == 1:
                    return 1
                if a == 0:
                    return b
                if b == 0 or a == b:
                    return a
            else:
                if a == 0:
                    return b
                if b == 0:
                    return a
                if a == b:
                    return 0
                if a == 1:
                    return self.gate('not', b)
                if b == 1:
                    return self.gate('not', a)
            if a > b:
                a, b = b, a
        else:
            raise ValueError('unknown prospective Boolean operation')
        key = kind, a, b
        if key not in self._intern:
            self._intern[key] = self._next
            self.nodes[self._next] = key
            self._next += 1
        return self._intern[key]

    def prefix(self, a, b, carry=0):
        """Return sum and all carries, matching lcu_kogge_stone.v's loops."""
        if len(a) != len(b) or not a:
            raise ValueError('equal nonempty prefix operands required')
        p = [self.gate('xor', x, y) for x, y in zip(a, b, strict=True)]
        original = p.copy()
        g = [self.gate('and', x, y) for x, y in zip(a, b, strict=True)]
        g[0] = self.gate('or', g[0], self.gate('and', p[0], carry))
        for level in range((len(a) - 1).bit_length()):
            step = 1 << level
            # Descending order preserves the previous level's dependencies.
            for j in range(len(a) - 1, step - 1, -1):
                g[j] = self.gate('or', g[j], self.gate('and', p[j], g[j - step]))
                p[j] = self.gate('and', p[j], p[j - step])
        return [self.gate('xor', original[i], g[i - 1] if i else carry)
                for i in range(len(a))], g

    def compress(self, columns):
        """Generic unsigned maccmap compression, with a Kogge--Stone merge."""
        columns = [list(c) for c in columns]
        width = len(columns)
        summands, packed = [], []
        while any(columns):
            summands.append([c.pop(0) if c else 0 for c in columns])
            while True:
                maximum = max(map(len, columns))
                position = max(i for i, c in enumerate(columns) if len(c) == maximum)
                if maximum == 0 or position > 4:
                    break
                required = sum(1 << i for i in range(position + 1) if len(columns[i]) == maximum)
                if required > max(len(summands) - 1, 0) - len(packed):
                    break
                for i in range(position + 1):
                    if len(columns[i]) == maximum:
                        packed.extend([columns[i].pop(0)] * (1 << i))
        rounds = 0
        while len(summands) > 2:
            following = []
            for offset in range(0, len(summands), 3):
                group = summands[offset:offset + 3]
                if len(group) < 3:
                    following.extend(group)
                    continue
                sums, carries = [], []
                for a, b, c in zip(*group, strict=True):
                    p = self.gate('xor', a, b)
                    sums.append(self.gate('xor', p, c))
                    carries.append(self.gate('or', self.gate('and', a, b), self.gate('and', p, c)))
                following.extend([sums, [packed.pop() if packed else 0] + carries[:-1]])
            summands = following
            rounds += 1
        if not summands:
            outputs = [0] * width
        elif len(summands) == 1:
            outputs = summands[0]
        else:
            outputs, _ = self.prefix(*summands, packed.pop() if packed else 0)
        if packed:
            raise ValueError('unconsumed compressor carry')
        return outputs, rounds

    def evaluate(self, outputs, leaf_values):
        values = {0: 0, 1: 1}
        values.update({node: int(bool(leaf_values[key])) for key, node in self.leaves.items()})
        for node, (kind, a, b) in self.nodes.items():
            x, y = values[a], values[b]
            values[node] = 1 - x if kind == 'not' else x & y if kind == 'and' else x | y if kind == 'or' else x ^ y
        return sum(values[node] << i for i, node in enumerate(outputs))

    def work(self, outputs):
        live, pending, loads = set(), list(outputs), {}
        while pending:
            node = pending.pop()
            loads[node] = loads.get(node, 0) + 1
            if node not in self.nodes or node in live:
                continue
            live.add(node)
            _, a, b = self.nodes[node]
            pending.extend((a, b))
        depth, xd, cd = {0: 0, 1: 0}, {0: 0, 1: 0}, {0: 0, 1: 0}
        for node, (kind, a, b) in self.nodes.items():
            if node not in live:
                continue
            depth[node] = max(depth.get(a, 0), depth.get(b, 0)) + 1
            xd[node] = max(xd.get(a, 0), xd.get(b, 0)) + (kind == 'xor')
            cd[node] = max(cd.get(a, 0), cd.get(b, 0)) + (kind != 'xor')
        lookup = {self.nodes[n]: n for n in live}

        def at(kind, a, b):
            return lookup.get((kind, *sorted((a, b))))

        bundled, full = set(), 0
        for carry in sorted(live):
            kind, u, v = self.nodes[carry]
            if kind != 'or' or u not in self.nodes or v not in self.nodes:
                continue
            for ab, pc in ((u, v), (v, u)):
                if self.nodes[ab][0] != 'and' or self.nodes[pc][0] != 'and':
                    continue
                a, b = self.nodes[ab][1:]
                p = at('xor', a, b)
                if p is None or p not in self.nodes[pc][1:]:
                    continue
                c = self.nodes[pc][2] if self.nodes[pc][1] == p else self.nodes[pc][1]
                total = at('xor', p, c)
                members = {carry, ab, pc, p, total}
                if total is not None and not members & bundled:
                    bundled.update(members)
                    full += 1
                    break
        half = 0
        for node in sorted(live - bundled):
            kind, a, b = self.nodes[node]
            pair = at('and', a, b) if kind == 'xor' else None
            if pair is not None and pair not in bundled:
                bundled.update((node, pair))
                half += 1
        result = {kind: float(sum(self.nodes[n][0] == kind for n in live))
                  for kind in ('xor', 'and', 'or', 'not')}
        result.update(work=float(len(live)), depth=float(max((depth.get(n, 0) for n in outputs), default=0)),
                      xor_depth=float(max((xd.get(n, 0) for n in outputs), default=0)),
                      carry_depth=float(max((cd.get(n, 0) for n in outputs), default=0)),
                      log2_max_fanout=math.log2(max(loads.values(), default=0) + 1.),
                      full_cuts=float(full), half_cuts=float(half))
        for kind in ('xor', 'and', 'or', 'not'):
            result['unpaired_' + kind] = float(sum(self.nodes[n][0] == kind for n in live - bundled))
        return result
