"""Frozen v10 runtime functions; extracted without numerical edits from workload_dot16_latency.py."""
def active_stages(raw, placement, weights):
    return sorted({placement[n['id']] for n in raw['nodes'] if weights.get(n['id'], 0.) > 0})


def depth_schedule(raw, units, L, weights):
    """Spread a path of indivisible live arithmetic units over the real L.

    Zero-cost wiring does not create arithmetic depth. The native compiler
    independently validates grouping, dependency and fixed-port legality.
    """
    nodes = raw['nodes']; membership = {n:k for k,u in enumerate(units) for n in u['members']}
    depths = []; dependencies = []; live = []
    for k, unit in enumerate(units):
        deps = sorted({membership[a['node']] for n in unit['members'] for a in nodes[n]['operands']
                       if a['node'] is not None and membership[a['node']] != k})
        if any(d >= k for d in deps):
            raise ValueError('scheduling units are not dependency ordered')
        positive = any(weights.get(n, 0.) > 0 for n in unit['members'])
        dependencies.append(deps); live.append(positive)
        depths.append(max((depths[d] for d in deps), default=0) + int(positive))
    span = max((d for d,p in zip(depths, live) if p), default=0)
    if span < L:
        raise ValueError('atomic arithmetic depth cannot fill the requested stages')
    stages = []; placement = [0] * len(nodes)
    for k, unit in enumerate(units):
        s = min(L-1, max(0, (depths[k]-1) * L // span))
        s = max(s, max((stages[d] for d in dependencies[k]), default=0))
        if unit['fixed']:
            s = 0 if all(nodes[n]['operation'] == 'input' for n in unit['members']) else L-1
        elif unit['constant']:
            s = 0
        stages.append(s)
        for n in unit['members']:
            placement[n] = s
    if active_stages(raw, placement, weights) != list(range(L)):
        raise ValueError('depth schedule still contains an arithmetic-empty stage')
    return placement
