"""Independent, model-only evaluator for the frozen step5 multiplier graph.

This is an acceptance oracle, not a new C/D selector or compiler materializer.
The C++ export supplies actual normalized nodes, facts and production results;
Python recomputes costs, paths and shared register chains from those nodes.
"""
import hashlib
import itertools
import json
from .simple_cost import Value, node_cost


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def analyze(graph, config):
    nodes = graph['nodes']
    if [n['id'] for n in nodes] != list(range(len(nodes))):
        raise ValueError('non-contiguous graph identities')
    groups = graph['groups']
    members = [n for group in groups for n in group]
    if len(groups) != 3 or any(not g for g in groups) or len(members) != len(set(members)):
        raise ValueError('unexpected or overlapping groups')
    if graph['template_version'] != config['template_version'] or graph['split_version'] != config['split_version']:
        raise ValueError('template/group version changed')
    deps = {n['id']: [v['node'] for v in n['operands'] if v['kind'] == 0] for n in nodes}
    users = {n['id']: set() for n in nodes}
    for user, sources in deps.items():
        for source in sources:
            users[source].add(user)
    order, pending = [], set(deps)
    while pending:
        ready = sorted(i for i in pending if set(deps[i]) <= set(order))
        if not ready:
            raise ValueError('cyclic or missing dependency')
        order.extend(ready)
        pending.difference_update(ready)
    # Ignore no dead nodes silently: the frozen small graph must be all live.
    live = {n['id'] for n in nodes if n['input'] or n['output']}
    stack = list(live)
    while stack:
        for source in deps[stack.pop()]:
            if source not in live:
                live.add(source)
                stack.append(source)
    if live != set(deps):
        raise ValueError('unexpected dead nodes in exported graph')
    integer = lambda limbs: sum(v << (64*i) for i, v in enumerate(limbs))
    def value(n):
        return Value(n['width'], integer(n['known_zero']), integer(n['known_one']), n['facts_valid'])
    def operand(v):
        if v['kind'] == 0:
            n = nodes[v['node']]
            return Value(v['width'], integer(n['known_zero']), integer(n['known_one']), n['facts_valid'])
        if v['kind'] == 1:
            return Value(v['width'], literal=integer(v['limbs']))
        raise ValueError('raw port outside input')
    costs, constants = {}, {}
    for i in order:
        n = nodes[i]
        constants[i] = not n['input'] and all(
            v['kind'] == 1 or (v['kind'] == 0 and constants[v['node']]) for v in n['operands'])
        data = [] if n['input'] else [operand(v) for v in n['operands']]
        if n['operation'] == 'AddCarry':
            data = data[:2]  # The third operand is a carry role, not a data width.
        c = node_cost('Input' if n['input'] else n['operation'], data, value(n),
                      transaction_constant=constants[i])
        if (c.delay, c.area) != (n['cpp_delay'], n['cpp_area']):
            raise ValueError(f'Python/C++ cost disagreement at node {i}')
        costs[i] = c
    def evaluate(stages):
        reasons = []
        for n in nodes:
            i = n['id']
            if not 0 <= stages[i] <= graph['N'] or (n['input'] and stages[i]) or (n['output'] and stages[i] != graph['N']):
                reasons.append(f'node {i}: fixed endpoint/stage range violation')
            for d in deps[i]:
                if not constants[d] and stages[d] > stages[i]:
                    reasons.append(f'backwards dependency {d}->{i}: {stages[d]}>{stages[i]}')
        for group in groups:
            if len({stages[i] for i in group}) != 1:
                reasons.append('inconsistent group stage')
        if reasons:
            return {'dependency_legal': False, 'reasons': reasons}
        arrival, delays = {}, [0]*(graph['N']+1)
        for i in order:
            arrival[i] = 0 if nodes[i]['input'] or constants[i] else costs[i].delay + max(
                (arrival[d] for d in deps[i] if not constants[d] and stages[d] == stages[i]), default=0)
            delays[stages[i]] = max(delays[stages[i]], arrival[i])
        chains = []
        for i in order:
            if constants[i]:
                continue
            end = max([stages[i]]+[stages[j] for j in users[i]])
            if i == graph['valid_input']:
                end = graph['N']
            if end > stages[i]:
                chains.append({'source': i, 'name': nodes[i]['name'], 'width': nodes[i]['width'],
                               'producer_stage': stages[i], 'register_stages': list(range(stages[i]+1, end+1)),
                               'consumer_nodes': sorted(users[i]), 'is_valid': i == graph['valid_input']})
        return {'dependency_legal': True, 'stage_delays': delays, 'peak_delay': max(delays),
                'register_bits': sum(c['width']*len(c['register_stages']) for c in chains),
                'register_count': sum(len(c['register_stages']) for c in chains), 'chains': chains}
    points = []
    for assignment in itertools.product(range(graph['N']+1), repeat=len(groups)):
        stages = list(graph['production_stages'])
        for group, at in zip(groups, assignment):
            for i in group:
                stages[i] = at
        point = {'group_stages': list(assignment), 'node_stages': stages, **evaluate(stages)}
        point['schedule_sha256'] = fingerprint({'structure': nodes, 'groups': groups, 'stages': stages})
        points.append(point)
    legal = [p for p in points if p['dependency_legal']]
    t0 = min(p['peak_delay'] for p in legal)
    for p in legal:
        p['default_feasible'] = p['peak_delay']*100 <= t0*105
        p['diagnostic_feasible'] = p['peak_delay'] <= config['diagnostic_cap']
        p['default_reason'] = 'within_frozen_cap' if p['default_feasible'] else f'peak {p["peak_delay"]} exceeds frozen 105/100*T0={t0*105}/100'
    feasible = [p for p in legal if p['default_feasible']]
    selected = next(p for p in legal if p['node_stages'] == graph['production_stages'])
    report = graph['report']
    if (t0 != report['baseline_delay'] or t0*105/100 != report['allowed_delay'] or
            any(selected[k] != report[k] for k in ['stage_delays', 'register_bits', 'register_count']) or
            selected['peak_delay'] != report['final_delay'] or not selected['default_feasible']):
        raise ValueError('independent evaluation differs from actual production schedule')
    actual = sorted((r['source'], r['stage'], r['width'], r['is_valid']) for r in graph['registers'])
    expected = sorted((c['source'], stage, c['width'], c['is_valid']) for c in selected['chains'] for stage in c['register_stages'])
    if actual != expected:
        raise ValueError('materialized shared register chains differ from analysis')
    if any(any(r['reset']) for r in graph['registers']):
        raise ValueError('unexpected nonzero reset in this multiplier fixture')
    return {'version': 'step5-placement-analysis-v1', 'status': 'passed', 'units': 'abstract, not ps',
            'scope': 'all three-group stage assignments; frozen production placement for outer nodes',
            'enumeration_owner': 'independent acceptance oracle; not an instrumented compiler search trace',
            'structure_sha256': fingerprint({'nodes': nodes, 'groups': groups}), 'L': config['L'], 'II': config['II'],
            'schedule_trials': len(points), 'dependency_legal_trials': len(legal), 'T0': t0,
            'default_cap': t0*105/100, 'default_feasible_count': len(feasible),
            'production_group_stages': selected['group_stages'], 'production_schedule_sha256': selected['schedule_sha256'],
            'production_register_chains_verified': True,
            'evidence_type': 'constraint_determined' if len(feasible) == 1 else 'multiple_feasible',
            'preference_selection_demonstrated': False,
            'diagnostic': {'cap': config['diagnostic_cap'],
                           'feasible_count': sum(p['diagnostic_feasible'] for p in legal),
                           'scope': config['diagnostic_scope'], 'production_policy_changed': False},
            'cap17': {'feasible_count': sum(p['peak_delay'] <= 17 for p in legal),
                      'interpretation': 'group0 itself has delay18; cap17 does not identify the cost of (0,0,1)'},
            'points': points}
