"""Offline buffer-independent connectivity comparison of saved control cones.

This accepts mapped connectivity solely for mechanism auditing. Its hashes,
counts and sink identities must never become prospective pricing features.
Equal normalized expressions are evidence about this representation, not a
general graph-isomorphism or Boolean-equivalence certificate.
"""
from collections import Counter, defaultdict
from functools import lru_cache
import ast
import hashlib
import json

VERSION = 'saved-control-expression-connectivity-audit-v14'


def fingerprint(start, instances, library, nets):
    by_net = defaultdict(list)
    for pin, row in nets.items():
        if row['direction'] == 'output' and not row['net'].startswith('<unconnected'):
            by_net[row['net']].append(pin)
    for net, pins in by_net.items():
        if len(pins) != 1:
            raise ValueError('ambiguous saved net drivers: '+net)
    expressions = {}

    def node(kind, *children):
        if kind in ('and', 'or', 'xor'):
            children = tuple(sorted(children))
        if kind == 'not' and expressions.get(children[0], (None,))[0] == 'not':
            return expressions[children[0]][1]
        value = kind, *children
        digest = hashlib.sha256(json.dumps(value, separators=(',', ':')).encode()).hexdigest()
        expressions[digest] = value
        return digest

    evaluating = set()

    @lru_cache(maxsize=None)
    def net_value(net):
        if net not in by_net:
            return node('port', net)
        return pin_value(by_net[net][0])

    @lru_cache(maxsize=None)
    def pin_value(pin):
        if pin in evaluating:
            raise ValueError('cyclic saved combinational connectivity')
        instance, terminal = pin.rsplit('/', 1)
        meta = library[instances[instance]]
        if meta['sequential']:
            return node('state', pin)
        evaluating.add(pin)
        function = meta['pins'][terminal]['function']
        if not function:
            raise ValueError('missing saved Liberty function')

        def walk(part):
            if isinstance(part, ast.Name):
                other = instance+'/'+part.id
                if other not in nets:
                    raise ValueError('missing saved Boolean input')
                return net_value(nets[other]['net'])
            if isinstance(part, ast.Constant) and type(part.value) is int and part.value in (0, 1):
                return node('constant', part.value)
            if isinstance(part, ast.UnaryOp) and isinstance(part.op, ast.Invert):
                return node('not', walk(part.operand))
            if isinstance(part, ast.BinOp) and type(part.op) in (ast.BitAnd, ast.BitOr, ast.BitXor):
                return node({ast.BitAnd: 'and', ast.BitOr: 'or', ast.BitXor: 'xor'}[type(part.op)],
                    walk(part.left), walk(part.right))
            raise ValueError('unsupported saved Liberty expression')

        result = walk(ast.parse(function.replace('*', '&').replace('+', '|').replace('!', '~'), mode='eval').body)
        evaluating.remove(pin)
        return result

    from .state_control_cones import trace
    cone = trace(start, instances, library, nets)
    sinks = {pin: net_value(nets[pin]['net']) for pin in cone['sequential_sink_pins']}
    # Only primitive syntax, commutation, wire-buffer removal and double-NOT
    # cancellation are normalized. Different expressions can still be equal.
    normalized = sorted(sinks.items())
    return dict(version=VERSION, start_pin=start, sinks=sinks,
        sink_expression_sha256=hashlib.sha256(json.dumps(normalized, separators=(',', ':')).encode()).hexdigest(),
        sink_count=len(sinks), logic_cells=cone['logic_cells'],
        buffer_inverter_cells=cone['buffer_inverter_cells'], max_cell_depth=cone['max_cell_depth'],
        cell_histogram=cone['cell_histogram'], max_net_sinks=cone['max_net_sinks'],
        expression_nodes=len(expressions), expressions=expressions,
        usable_as_online_price_feature=False, graph_isomorphism_claimed=False,
        Boolean_equivalence_claimed=False)
