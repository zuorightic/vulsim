"""Successor certificate for a closed island of logic plus internal buffers."""
from collections import defaultdict
from types import FunctionType

from . import model_logical_ownership_v1 as parent

VERSION='arithmetic-logical-ownership-v2-closed-islands'
normalize=parent.normalize
digest=parent.digest


def resolve(packet,scopes,top_ports):
    base=parent.resolve(packet,scopes,top_ports)
    instances=packet['instances'];lib=packet['liberty'];connections=packet['connections'];by_net=defaultdict(list)
    for pin,row in connections.items():by_net[row['net']].append(pin)
    candidates=set()
    recovered_before={r['instance'] for r in base['recovered']}
    for name,master in instances.items():
        c=lib[master]
        if '/' in name or c['sequential'] or c.get('physical_only') or c.get('constant_driver') or base['owners'].get(name)=='shared_clock':continue
        outputs=[p for p,v in c['pins'].items() if v['direction']=='output']
        if outputs and all(c['pins'][p].get('function') for p in outputs):candidates.add(name)
    adjacency=defaultdict(set)
    for pins in by_net.values():
        members={p.rsplit('/',1)[0] for p in pins}&candidates
        for n in members:adjacency[n].update(members-{n})
    ports={parent.qualified.canonical(n):dict(v,net=parent.qualified.canonical(v['net'])) for n,v in top_ports.items()}
    top_nets={r['net'] for r in ports.values()};todo=set(candidates);islands=[]
    while todo:
        first=min(todo);members={first};pending=[first];todo.remove(first)
        while pending:
            n=pending.pop()
            for other in adjacency[n]&todo:todo.remove(other);members.add(other);pending.append(other)
        if not (members&set(base['unresolved']) or members&recovered_before):continue
        witness={};neighbour_owners=set();reason=None
        for name in sorted(members):
            for term,meta in lib[instances[name]]['pins'].items():
                pin=name+'/'+term;net=connections[pin]['net']
                if net in top_nets or net in packet['clock_nets'] or net.startswith('<unconnected'):reason='top/clock/unconnected island net';break
                pins=by_net[net];drivers=[p for p in pins if connections[p]['direction']=='output'];loads=[p for p in pins if connections[p]['direction']=='input']
                if len(drivers)!=1 or not loads:reason='island net lacks one driver and live sinks';break
                external=[p for p in pins if p.rsplit('/',1)[0] not in members]
                owners={base['owners'].get(p.rsplit('/',1)[0]) for p in external}
                if not owners<=set(scopes):reason='island crosses node/state/unknown owner';break
                neighbour_owners.update(owners);witness[pin]=dict(net=net,drivers=sorted(drivers),loads=sorted(loads))
            if reason:break
        if reason or len(neighbour_owners)!=1:
            for n in members&set(base['unresolved']):base['unresolved'][n]=reason or 'island has ambiguous/absent arithmetic owner'
            continue
        owner=next(iter(neighbour_owners));islands.append(dict(members=sorted(members),owner=owner,pins=witness))
        base['recovered']=[r for r in base['recovered'] if r['instance'] not in members]
        for n in sorted(members):
            base['owners'][n]=owner;base['unresolved'].pop(n,None)
            base['recovered'].append(dict(instance=n,master=instances[n],owner=owner,island_members=sorted(members),
                pins={pin.rsplit('/',1)[1]:row for pin,row in witness.items() if pin.rsplit('/',1)[0]==n},
                liberty_function={p:v['function'] for p,v in lib[instances[n]]['pins'].items() if v['direction']=='output'},
                proof='complete connected root combinational island has exactly one external arithmetic owner; no top/state/clock/unknown neighbour'))
    base.update(version=VERSION,complete=not base['unresolved'],closed_islands=islands)
    base['recovered'].sort(key=lambda r:r['instance'])
    return base


def extract(packet,nodes,banks,top_ports,certificate):
    namespace=dict(parent.extract.__globals__);namespace.update(resolve=resolve,VERSION=VERSION)
    return FunctionType(parent.extract.__code__,namespace)(packet,nodes,banks,top_ports,certificate)
