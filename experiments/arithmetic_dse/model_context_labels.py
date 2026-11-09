"""Strict local-context labels from raw pin/path packets, with exclusive owners.

An exhaustive mapped boundary census and through-producer data constraints are
required. Synthetic packets qualify the reader software only, never silicon or
the new physical shells. The physical producer is context_readout.tcl.
"""
import math
import csv
from pathlib import Path
from collections import defaultdict

from . import model_fast_path as timing

VERSION = 'arithmetic-context-labels-v1'


def read_snapshot(prefix, period_ps, time_to_ps, liberty, expected_nodes, expected_banks, *, origin='physical_snapshot'):
    """Consume context_readout.tcl files; no EDA invocation or admission."""
    prefix = Path(prefix)
    def table(suffix):
        return list(csv.DictReader(Path(str(prefix)+'_'+suffix+'.tsv').read_text().splitlines(), delimiter='\t'))
    instance_rows = [line.split('\t') for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines()]
    if len({r[0] for r in instance_rows}) != len(instance_rows): raise ValueError('duplicate physical instance')
    instances = dict(instance_rows)
    connections = {}
    for row in table('connections'):
        pin = row['instance']+'/'+row['pin']
        if pin in connections: raise ValueError('duplicate physical terminal')
        connections[pin] = dict(direction=row['direction'],net=row['net'])
    def points(filename):
        path = prefix.parent/filename
        if path.parent != prefix.parent or path.name != filename: raise ValueError('path-point file escapes snapshot')
        return [(name,float(arrival)) for name,arrival in (line.split('\t') for line in path.read_text().splitlines())]
    nodes = {node:dict(inputs=[],outputs=[],constants=[],output_paths={}) for node in expected_nodes}
    for row in table('endpoints'):
        if row['node'] not in nodes or row['kind'] not in ('inputs','outputs','constants'): raise ValueError('unknown node boundary')
        nodes[row['node']][row['kind']].append(row['pin'])
    for row in table('node_paths'):
        node = nodes[row['node']]
        if row['output'] in node['output_paths']: raise ValueError('duplicate independent output path')
        node['output_paths'][row['output']] = points(row['file'])
    requests = {bank:dict(**{'from':[], 'through':[], 'to':[]}) for bank in expected_banks}
    for row in table('data_requests'):
        if row['bank'] not in requests or row['kind'] not in requests[row['bank']]: raise ValueError('unknown data constraint')
        requests[row['bank']][row['kind']].append(row['pin'])
    data = {}
    for row in table('data_paths'):
        bank = row['bank']
        if bank in data: raise ValueError('duplicate capture path')
        data[bank] = dict(start=row['start'],end=row['end'],slack_ps=float(row['slack'])*time_to_ps,
                          points=points(prefix.name+'_data_'+bank+'_points.tsv'))
    logic_rows = table('logic')
    if len({r['pin'] for r in logic_rows}) != len(logic_rows): raise ValueError('duplicate boundary logic pin')
    if Path(str(prefix)+'_data_paths.tsv').read_bytes() != Path(str(prefix)+'_data_after.tsv').read_bytes():
        raise ValueError('independent probe changed normal data labels')
    clock_rows = table('clock_nets')
    if len({r['net'] for r in clock_rows}) != len(clock_rows): raise ValueError('duplicate clock net')
    packet = dict(origin=origin,period_ps=period_ps,time_to_ps=time_to_ps,instances=instances,liberty=liberty,
        clock_nets=[r['net'] for r in clock_rows],
        connections=connections,pin_logic={r['pin']:r['logic'] for r in logic_rows},nodes=nodes,data_requests=requests,data_paths=data)
    return extract(packet, expected_nodes, expected_banks)


def extract(packet, expected_nodes, expected_banks):
    required = {'origin', 'period_ps', 'instances', 'liberty', 'connections', 'pin_logic',
                'nodes', 'data_requests', 'data_paths', 'time_to_ps', 'clock_nets'}
    if set(packet) != required or packet['origin'] not in ('synthetic_fixture', 'physical_snapshot'):
        raise ValueError('complete explicit raw context packet required')
    period, scale = packet['period_ps'], packet['time_to_ps']
    if any(isinstance(v, bool) or not isinstance(v, (int,float)) or not math.isfinite(v) or v <= 0 for v in (period,scale)):
        raise ValueError('positive finite period and units required')
    scopes = dict(expected_nodes)
    if set(packet['nodes']) != set(scopes) or not scopes or 'producer' not in scopes:
        raise ValueError('all declared nodes, including producer, required')
    prefixes = list(scopes.values())
    if any(not x.endswith('/') for x in prefixes) or any(a.startswith(b) for i,a in enumerate(prefixes) for j,b in enumerate(prefixes) if i!=j):
        raise ValueError('overlapping context ownership')
    instances, cells, nets = packet['instances'], packet['liberty'], packet['connections']
    areas = defaultdict(float); pin_owner = {}; directions = {}; by_net = defaultdict(list)
    for name, master in instances.items():
        if master not in cells: raise ValueError('unknown Liberty master')
        cell = cells[master]; matches = [owner for owner,scope in scopes.items() if name.startswith(scope)]
        clock_buffer = (not cell['sequential'] and cell['buffer_or_inverter']
                        and any(nets.get(name+'/'+pin,{}).get('net') in packet['clock_nets'] for pin in cell['pins']))
        if clock_buffer:
            owner = 'shared_clock'
        elif matches:
            owner = matches[0]
            if cell['sequential']: raise ValueError('state inside combinational node')
        elif name.startswith('launch/'): owner = 'input_service'
        elif name.startswith('capture/'): owner = 'native_state'
        elif name.startswith('observer/'): owner = 'observer'
        elif cell.get('physical_only',False): owner = 'shared_physical'
        elif '/' not in name and not cell['sequential'] and (cell['buffer_or_inverter'] or cell.get('constant_driver',False)):
            owner = 'shared_clock' if any(nets.get(name+'/'+pin,{}).get('net') in packet['clock_nets'] for pin in cell['pins']) else 'root_repair'
        else: raise ValueError('unowned physical cell')
        area = cell['area_um2']
        if isinstance(area,bool) or not isinstance(area,(int,float)) or not math.isfinite(area) or area < 0:
            raise ValueError('invalid Liberty area')
        areas[owner] += area
        for pin, meta in cell['pins'].items():
            if meta['direction'] not in ('input','output'): continue
            full = name+'/'+pin
            if full not in nets or nets[full]['direction'] != meta['direction']:
                raise ValueError('missing or inconsistent raw signal-pin census')
            pin_owner[full] = owner; directions[full] = meta['direction']; by_net[nets[full]['net']].append(full)
    if set(nets) != set(pin_owner): raise ValueError('unexpected connection or power pin in signal census')
    boundaries = {}
    for owner in scopes:
        inputs = set(); outputs = set(); constants = set()
        for pin in pin_owner:
            if pin_owner[pin] != owner: continue
            cross = any(pin_owner[p] != owner for p in by_net[nets[pin]['net']])
            if not cross: continue
            if pin not in packet['pin_logic'] or packet['pin_logic'][pin] not in ('0','1','X'):
                raise ValueError('boundary constant/variable classification absent')
            if packet['pin_logic'][pin] in ('0','1'): constants.add(pin)
            elif directions[pin]=='input': inputs.add(pin)
            else: outputs.add(pin)
        boundaries[owner] = dict(inputs=inputs, outputs=outputs, constants=constants)
    estimates = {}
    for owner, declared in packet['nodes'].items():
        if set(declared) != {'inputs','outputs','constants','output_paths'}:
            raise ValueError('unknown node label field')
        actual = boundaries[owner]
        for kind in ('inputs','outputs','constants'):
            if len(declared[kind]) != len(set(declared[kind])) or set(declared[kind]) != actual[kind]:
                raise ValueError('node endpoint coverage incomplete or duplicated')
        if not actual['inputs'] or not actual['outputs']:
            raise ValueError('empty dynamic node; constant/passthrough requires a separately verified alias certificate')
        paths = declared['output_paths']
        if set(paths) != actual['outputs']:
            raise ValueError('independent maximum missing for a dynamic output')
        maximum = 0
        for output, points in paths.items():
            if not points or points[0][0] not in actual['inputs'] or points[-1][0] != output:
                raise ValueError('wrong independent node boundary')
            if abs(points[0][1]) > 1e-6:
                raise ValueError('independent node query lacks zero arrival origin')
            for (a, ta), (b, tb) in zip(points, points[1:]):
                if any(isinstance(t,bool) or not isinstance(t,(int,float)) or not math.isfinite(t) for t in (ta,tb)) or tb < ta-1e-6:
                    raise ValueError('invalid node arrival increments')
                if a not in pin_owner or b not in pin_owner or pin_owner[a] != owner or pin_owner[b] != owner:
                    raise ValueError('service or other node included in operator delay')
                ca, cb = a.rsplit('/',1)[0], b.rsplit('/',1)[0]
                if ca == cb:
                    if directions[a]!='input' or directions[b]!='output': raise ValueError('invalid cell arc')
                elif directions[a]!='output' or directions[b]!='input' or nets[a]['net']!=nets[b]['net']:
                    raise ValueError('disconnected internal wire')
            maximum = max(maximum, (points[-1][1]-points[0][1])*scale)
        estimates[owner] = dict(operator_delay_ps=maximum, comb_area_um2=areas[owner], independent_dynamic_outputs=len(paths))
    requests = packet['data_requests']
    if set(requests) != set(expected_banks) or set(packet['data_paths']) != set(expected_banks):
        raise ValueError('all functional capture banks required')
    # All launch data Q and every actual capture data D in the declared bank
    # enter the request; clock/control pins cannot substitute for data endpoints.
    launch_data = set()
    capture_data = set()
    for pin, owner in pin_owner.items():
        name, term = pin.rsplit('/',1); cell = cells[instances[name]]
        if owner=='input_service' and cell['sequential'] and '/valid' not in name and directions[pin]=='output' and len(by_net[nets[pin]['net']])>1: launch_data.add(pin)
        if owner=='native_state' and cell['sequential'] and term in cell['data_pins'] and '/valid' not in name: capture_data.add(pin)
    all_targets = set(); slacks = []; decompositions = []
    for bank, request in requests.items():
        if set(request) != {'from','through','to'} or set(request['from']) != launch_data or set(request['through']) != boundaries['producer']['outputs']:
            raise ValueError('functional query must cover launch data and pass through producer outputs')
        if any(len(values)!=len(set(values)) for values in request.values()):raise ValueError('duplicate functional constraint pin')
        targets = set(request['to'])
        if not targets or not targets <= capture_data or targets & all_targets:
            raise ValueError('capture data banks overlap or contain control')
        if any(not any(pin.rsplit('/',1)[0].startswith(pattern) for pattern in expected_banks[bank]) for pin in targets):
            raise ValueError('capture bank outside registered storage aliases')
        all_targets |= targets
        row = packet['data_paths'][bank]
        if set(row) != {'start','end','points','slack_ps'} or row['start'] not in launch_data or row['end'] not in targets:
            raise ValueError('wrong through-data endpoints')
        if not any(name in boundaries['producer']['outputs'] for name,_ in row['points']):
            raise ValueError('unrelated bypass used as operator data slack')
        slack = row['slack_ps']
        if isinstance(slack,bool) or not isinstance(slack,(int,float)) or not math.isfinite(slack):
            raise ValueError('signed finite data slack required')
        detail = timing.decompose(row['points'],row['start'],row['end'],instances,cells,nets,scopes,scale)
        slacks.append(slack); decompositions.append(detail)
    if all_targets != capture_data: raise ValueError('capture bank census incomplete')
    return dict(version=VERSION, nodes=estimates, operator_delay_ps=estimates['producer']['operator_delay_ps'],
                comb_area_um2=estimates['producer']['comb_area_um2'], data_setup_slack_ps=min(slacks),
                owner_area_um2=dict(areas), total_cell_area_um2=sum(areas.values()), path_decompositions=decompositions,
                operator_maximum_covered=True,data_through_operator_covered=True,ownership_complete=True,
                origin=packet['origin'], physical_training_label_eligible=False,
                eligibility_note='physical protocol/tool/semantic-port/FF/SDC/CEC identity checks required in future admitted runner')
