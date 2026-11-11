"""Offline certificates for physical logic wholly inside one arithmetic owner.

No clone-name, master-name, source-ID or price whitelist is used. Only a cell
whose complete signal neighbourhood is internal to exactly one declared node
can be recovered. Cross-node optimization and unresolved chains stay refused.
"""
from collections import defaultdict
from copy import deepcopy
from types import FunctionType,SimpleNamespace
import hashlib
import json

from . import model_qualification_labels as qualified

VERSION='arithmetic-logical-ownership-v1'


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def normalize(packet,nodes,banks):
    namespace=dict(qualified.extract.__globals__)
    namespace['parent']=SimpleNamespace(extract=lambda p,*args:p)
    result=FunctionType(qualified.extract.__code__,namespace)(packet,nodes,banks)
    result.pop('reader_adapter');return result


def resolve(packet,scopes,top_ports):
    """Derive owners from the full actual stage census, independent of timing."""
    if not scopes or any(not p.endswith('/') or p=='/' for p in scopes.values()):raise ValueError('explicit node scopes required')
    prefixes=list(scopes.values())
    if any(a.startswith(b) for i,a in enumerate(prefixes) for j,b in enumerate(prefixes) if i!=j):raise ValueError('overlapping scopes')
    instances=packet['instances'];lib=packet['liberty'];connections=packet['connections'];owners={};unresolved={};by_net=defaultdict(list)
    ports={qualified.canonical(p):dict(v,net=qualified.canonical(v['net'])) for p,v in top_ports.items()}
    top_nets={p['net'] for p in ports.values()}
    for pin,row in connections.items():
        name,terminal=pin.rsplit('/',1)
        if name not in instances or instances[name] not in lib or terminal not in lib[instances[name]]['pins']:raise ValueError('unknown census terminal')
        if row['direction']!=lib[instances[name]]['pins'][terminal]['direction']:raise ValueError('census and Liberty direction differ')
        by_net[row['net']].append(pin)
    expected={n+'/'+p for n,m in instances.items() for p,v in lib[m]['pins'].items() if v['direction'] in ('input','output')}
    if set(connections)!=expected:raise ValueError('incomplete actual signal census')
    for name,master in instances.items():
        cell=lib[master];matches=[o for o,p in scopes.items() if name.startswith(p)]
        clock=not cell['sequential'] and cell['buffer_or_inverter'] and any(connections[name+'/'+p]['net'] in packet['clock_nets'] for p in cell['pins'])
        if clock:owner='shared_clock'
        elif matches:
            if cell['sequential']:raise ValueError('state inside arithmetic node')
            owner=matches[0]
        elif name.startswith('launch/'):owner='input_service'
        elif name.startswith('capture/'):owner='native_state'
        elif name.startswith('observer/'):owner='observer'
        elif cell.get('physical_only'):owner='shared_physical'
        elif '/' not in name and not cell['sequential'] and (cell['buffer_or_inverter'] or cell.get('constant_driver')):owner='root_repair'
        else:unresolved[name]='outside declared hierarchy';continue
        owners[name]=owner
    recovered=[];seed_owners=dict(owners)
    # Deliberately no propagation through unresolved roots: each first-version
    # certificate must be directly closed by known arithmetic-owned neighbours.
    for name in sorted(unresolved):
        cell=lib[instances[name]]
        if cell['sequential'] or cell.get('physical_only') or cell['buffer_or_inverter']:
            unresolved[name]='not an unowned combinational logic cell';continue
        ins=[p for p,v in cell['pins'].items() if v['direction']=='input'];outs=[p for p,v in cell['pins'].items() if v['direction']=='output']
        if not ins or not outs or any(not cell['pins'][p].get('function') for p in outs):
            unresolved[name]='missing combinational Liberty function';continue
        witness={};seen_owners=set();reason=None
        for terminal in ins+outs:
            pin=name+'/'+terminal;net=connections[pin]['net'];neighbours=[p for p in by_net[net] if p.rsplit('/',1)[0]!=name]
            if net in top_nets or net in packet['clock_nets'] or net.startswith('<unconnected'):
                reason='top-level/clock/unconnected net touches recovered cell';break
            peers={seed_owners.get(p.rsplit('/',1)[0]) for p in neighbours}
            if not neighbours or None in peers or not peers<=set(scopes):reason='neighbour outside declared arithmetic owner';break
            drivers=[p for p in by_net[net] if connections[p]['direction']=='output']
            loads=[p for p in by_net[net] if connections[p]['direction']=='input']
            if terminal in ins and (len(drivers)!=1 or drivers[0].rsplit('/',1)[0]==name):reason='input lacks unique internal driver';break
            if terminal in outs and (drivers!=[pin] or not loads):reason='output lacks unique driver and internal loads';break
            seen_owners.update(peers);witness[terminal]=dict(net=net,drivers=sorted(drivers),loads=sorted(loads))
        if reason or len(seen_owners)!=1:
            unresolved[name]=reason or 'more than one logical owner in neighbourhood';continue
        owner=next(iter(seen_owners));owners[name]=owner
        recovered.append(dict(instance=name,master=instances[name],owner=owner,pins=witness,
            liberty_function={p:cell['pins'][p]['function'] for p in outs},
            proof='all actual signal drivers/loads internal to one declared node; no top/state/clock or unresolved neighbour'))
    for row in recovered:unresolved.pop(row['instance'])
    identity=dict(instances=instances,connections=connections,liberty=lib,clock_nets=packet['clock_nets'],top_ports=ports,scopes=scopes)
    return dict(version=VERSION,input_sha256=digest(identity),scopes=scopes,owners=owners,recovered=recovered,unresolved=unresolved,
        complete=not unresolved,physical_design_modified=False,model_features_added=False)


def extract(packet,nodes,banks,top_ports,certificate):
    p=normalize(packet,nodes,banks);expected=resolve(p,nodes,top_ports)
    if expected!=certificate:raise ValueError('forged or stale logical ownership certificate')
    if not expected['complete']:raise ValueError('logical ownership remains unresolved')
    # A bijective proof-only namespace lets the frozen strict reader check
    # area, endpoint closure, every Liberty arc and path partition consistently.
    # Physical names/nets/ODB are never renamed. The mapping is exported below.
    aliases={r['instance']:nodes[r['owner']]+'__ownership_recovered__/'+r['instance'] for r in expected['recovered']}
    if set(aliases.values())&set(p['instances']) or len(set(aliases.values()))!=len(aliases):raise ValueError('ownership alias collision')
    def pin(value):
        cell,terminal=value.rsplit('/',1);return aliases.get(cell,cell)+'/'+terminal
    p['instances']={aliases.get(n,n):m for n,m in p['instances'].items()}
    p['connections']={pin(n):v for n,v in p['connections'].items()}
    p['pin_logic']={pin(n):v for n,v in p['pin_logic'].items()}
    p['nodes']={name:{**{k:[pin(n) for n in row[k]] for k in ('inputs','outputs','constants')},
        'output_paths':{pin(n):[(pin(a),t) for a,t in points] for n,points in row['output_paths'].items()}} for name,row in p['nodes'].items()}
    p['data_requests']={name:{kind:[pin(n) for n in values] for kind,values in row.items()} for name,row in p['data_requests'].items()}
    p['data_paths']={name:dict(row,start=pin(row['start']),end=pin(row['end']),points=[(pin(a),t) for a,t in row['points']]) for name,row in p['data_paths'].items()}
    result=qualified.extract(p,nodes,banks)
    reverse={v:k for k,v in aliases.items()}
    def physical(value):
        if isinstance(value,str):
            for alias,actual in reverse.items():
                if value==alias:return actual
                if value.startswith(alias+'/'):return actual+value[len(alias):]
            return value
        if isinstance(value,list):return [physical(x) for x in value]
        if isinstance(value,tuple):return tuple(physical(x) for x in value)
        if isinstance(value,dict):return {physical(k):physical(v) for k,v in value.items()}
        return value
    result=physical(result)
    result.update(reader_adapter=VERSION,ownership_certificate_sha256=digest(certificate),recovered_cells=deepcopy(expected['recovered']),
        physical_training_label_eligible=False,eligibility_note='successor report replay; old frozen collection and test verdict unchanged')
    return result
