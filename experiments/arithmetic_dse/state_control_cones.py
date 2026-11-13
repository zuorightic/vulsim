"""Offline control DAG audit; mapped quantities are never prospective features."""
from collections import Counter,defaultdict,deque
from .model_physical_path_v2 import verify_combinational_arc

VERSION='state-control-combinational-DAG-audit-v1'


def trace(start,instances,liberty,nets):
    by_net=defaultdict(list)
    for pin,row in nets.items():by_net[row['net']].append(pin)
    if start not in nets or nets[start]['direction']!='output':raise ValueError('control Q/QN output required')
    queue=deque([start]);visited=set();cells=set();sinks=set();edges=set();arcs=set();other=set()
    while queue:
        pin=queue.popleft()
        if pin in visited:continue
        visited.add(pin);instance,term=pin.rsplit('/',1);meta=liberty[instances[instance]]
        if nets[pin]['direction']=='output':
            net=nets[pin]['net']
            if net.startswith('<unconnected'):continue
            drivers=[p for p in by_net[net] if nets[p]['direction']=='output']
            if drivers!=[pin]:raise ValueError('control net has ambiguous drivers')
            for dest in by_net[net]:
                if nets[dest]['direction']=='input':edges.add((pin,dest,0));queue.append(dest)
        elif meta['sequential']:
            if term in meta['data_pins']:sinks.add(pin)
            else:other.add(pin)
        else:
            outputs=[dst for src,dst in meta.get('timing_arcs',[]) if src==term]
            if not outputs:raise ValueError('control combinational input lacks a legal Liberty continuation')
            cells.add(instance)
            for out in outputs:
                verify_combinational_arc(meta,term,out);dest=instance+'/'+out
                if dest not in nets:raise ValueError('control arc lacks mapped output')
                arcs.add((pin,dest));edges.add((pin,dest,1));queue.append(dest)
    predecessors=defaultdict(list);successors=defaultdict(list)
    for a,b,cost in edges:predecessors[b].append((a,cost));successors[a].append((b,cost))
    indegree={p:len(predecessors[p]) for p in visited};order=deque(p for p in visited if indegree[p]==0);depth={p:0 for p in order};processed=0
    while order:
        p=order.popleft();processed+=1
        for dest,cost in successors[p]:
            depth[dest]=max(depth.get(dest,0),depth[p]+cost);indegree[dest]-=1
            if indegree[dest]==0:order.append(dest)
    if processed!=len(visited):raise ValueError('cyclic control combinational cone')
    histogram=Counter(instances[c] for c in cells);logic=sum(not liberty[instances[c]]['buffer_or_inverter'] for c in cells)
    return dict(start_pin=start,sequential_sink_pins=sorted(sinks),sequential_sink_count=len(sinks),
                non_data_sequential_pins=sorted(other),cell_count=len(cells),logic_cells=logic,
                buffer_inverter_cells=len(cells)-logic,cell_histogram=dict(histogram),
                max_cell_depth=max((depth[p] for p in sinks),default=0),
                max_net_sinks=max((sum(nets[p]['direction']=='input' for p in by_net[nets[pin]['net']])
                                  for pin in visited if nets[pin]['direction']=='output'),default=0),
                reconvergent_pins=sum(len(v)>1 for v in predecessors.values()),
                arcs=len(arcs),net_edges=sum(c==0 for a,b,c in edges),
                sink_depths={p:depth[p] for p in sorted(sinks)},
                usable_as_online_price_feature=False,mapped_capacitance_qualified=False)
