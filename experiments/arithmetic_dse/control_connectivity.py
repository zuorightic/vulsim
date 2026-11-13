"""Physical validation of control cones; never an inference feature source."""
from collections import defaultdict, deque

VERSION = 'control-cone-sequential-terminal-audit-v1'


def sequential_sinks(start_pin, instances, liberty, nets, owners,
                     excluded_owners=('observer', 'source_adapter', 'shared_physical', 'shared_clock')):
    """Follow real nets and legal Liberty arcs, stopping at sequential D pins.

    This measures an implemented logical cone. It does not turn the number of
    mapped pins into an online price input or an equivalent load capacitance.
    """
    if start_pin not in nets or nets[start_pin]['direction'] != 'output':
        raise ValueError('actual control launch output required')
    by_net=defaultdict(list)
    for pin, row in nets.items():
        by_net[row['net']].append(pin)
    queue=deque([start_pin]);visited=set();sinks=set();arcs=set();edges=set()
    while queue:
        pin=queue.popleft()
        if pin in visited:
            continue
        visited.add(pin)
        instance, term=pin.rsplit('/',1)
        if owners[instance] in excluded_owners:
            continue
        cell=liberty[instances[instance]]
        if nets[pin]['direction']=='output':
            net=nets[pin]['net']
            if net.startswith('<unconnected'):
                continue
            drivers=[p for p in by_net[net] if nets[p]['direction']=='output']
            if drivers != [pin]:
                raise ValueError('control net has ambiguous driver')
            for other in by_net[net]:
                if nets[other]['direction']=='input':
                    edges.add((pin,other));queue.append(other)
        elif cell['sequential']:
            if term in cell['data_pins']:
                sinks.add(pin)
        else:
            for left,right in cell.get('timing_arcs',[]):
                if left!=term:
                    continue
                if cell['pins'][left]['direction']!='input' or cell['pins'][right]['direction']!='output':
                    raise ValueError('invalid control combinational arc direction')
                dest=instance+'/'+right
                if dest not in nets:
                    raise ValueError('missing actual control output')
                arcs.add((pin,dest));queue.append(dest)
    return dict(start_pin=start_pin,sequential_sink_pins=sorted(sinks),
                sequential_sink_count=len(sinks),visited_pins=len(visited),
                actual_combinational_arcs=len(arcs),actual_net_edges=len(edges),
                mapped_capacitance_qualified=False,usable_as_online_price_feature=False)
