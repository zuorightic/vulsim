"""Exclusive timing ownership on saved physical path points.

Node delays own cell arcs and intra-node wires. Edges own inter-owner wires;
service/capture/root-repair cell arcs stay outside node prices. These are
witness decompositions, not exhaustive operator maxima or prediction features.
"""
from collections import defaultdict
import csv
import math
from pathlib import Path
import re

VERSION = 'arithmetic-physical-path-ownership-v2-liberty-arcs'


def canonical(name):
    return re.sub(r'\\([\[\]])', r'\1', name)


def connections(path):
    result = {}
    for row in csv.DictReader(Path(path).read_text().splitlines(), delimiter='\t'):
        key = canonical(row['instance']) + '/' + row['pin']
        if key in result or row['direction'].lower() not in ('input', 'output', 'inout'):
            raise ValueError('ambiguous physical path connectivity')
        result[key] = dict(direction=row['direction'].lower(), net=canonical(row['net']))
    return result


def verify_combinational_arc(cell, source_pin, destination_pin):
    """Direction and explicit Liberty timing are independent requirements.

    Ordinary input-to-output steps and Liberty-declared output-to-output
    steps (e.g. CON -> SN) must both name an actual arc. A legal direction
    alone cannot establish a timing relationship between two cell pins.
    """
    source = cell['pins'][source_pin]['direction']
    destination = cell['pins'][destination_pin]['direction']
    if cell['sequential'] or source not in ('input', 'output') or destination != 'output':
        raise ValueError('invalid combinational cell timing step')
    if [source_pin, destination_pin] not in cell.get('timing_arcs', []):
        raise ValueError('cell step is not an actual Liberty timing arc')


def decompose(points, start, end, instances, pins, nets, node_scopes, time_to_ps=1):
    if not math.isfinite(time_to_ps) or time_to_ps <= 0 or not node_scopes:
        raise ValueError('positive time conversion and explicit node scopes required')
    if any(not isinstance(v, str) or not v.endswith('/') or v == '/' for v in node_scopes.values()):
        raise ValueError('node scope must be an explicit hierarchy prefix')
    prefixes = list(node_scopes.values())
    if any(a.startswith(b) for i, a in enumerate(prefixes) for j, b in enumerate(prefixes) if i != j):
        raise ValueError('overlapping timing ownership scopes')
    if any(not isinstance(k, str) or not k or k in ('input_service', 'native_state', 'root_repair') for k in node_scopes):
        raise ValueError('node identity collides with boundary ownership')
    def metadata(name):
        cell, pin = name.rsplit('/', 1)
        if cell not in instances or instances[cell] not in pins or pin not in pins[instances[cell]]['pins']:
            raise ValueError('unknown physical timing pin')
        master = pins[instances[cell]]; terminal = master['pins'][pin]
        if name not in nets or terminal['direction'] != nets[name]['direction']:
            raise ValueError('Liberty and physical connectivity disagree')
        scopes = [k for k, v in node_scopes.items() if cell.startswith(v)]
        if len(scopes) == 1:
            owner = scopes[0]
            if master['sequential']:
                raise ValueError('sequential cell inside combinational node')
        elif cell.startswith('launch/'):
            owner = 'input_service'
        elif cell.startswith('capture/'):
            owner = 'native_state'
        elif '/' not in cell and master['buffer_or_inverter'] and not master['sequential']:
            owner = 'root_repair'
        else:
            raise ValueError('timing cell outside explicit node/boundary owners')
        return cell, pin, master, terminal['direction'], owner
    if len(points) < 2 or any(not isinstance(v, (float, int)) or isinstance(v, bool) or not math.isfinite(v) for _, v in points):
        raise ValueError('finite ordered physical path required')
    points = [(canonical(n), v) for n, v in points]
    start, end = canonical(start), canonical(end)
    indices = [i for i, (n, _) in enumerate(points) if n == start]
    if len(indices) != 1 or points[-1][0] != end:
        raise ValueError('unique Q and final D boundaries required')
    points = points[indices[0]:]
    first, last = metadata(start), metadata(end)
    if (first[4] != 'input_service' or not first[2]['sequential'] or first[3] != 'output'
            or last[4] != 'native_state' or not last[2]['sequential'] or last[1] not in last[2]['data_pins']):
        raise ValueError('path must span declared launch Q to capture D')
    segments = []; totals = defaultdict(float); node_totals = defaultdict(float); order = []
    for i, ((a, ta), (b, tb)) in enumerate(zip(points, points[1:])):
        left, right = metadata(a), metadata(b); delay = (tb - ta) * time_to_ps
        if not math.isfinite(delay) or delay < -1e-5:
            raise ValueError('negative or nonfinite physical path increment')
        if i and left[2]['sequential'] or i != len(points)-2 and right[2]['sequential']:
            raise ValueError('intermediate sequential pin in combinational data path')
        if left[0] == right[0]:
            # Multi-output library cells can expose an internal output-to-output
            # timing vertex (e.g. CON -> SN); retain its measured increment.
            verify_combinational_arc(left[2], left[1], right[1])
            owner = left[4]; kind = 'node_cell' if owner in node_scopes else 'boundary_cell'
        else:
            if (left[3] != 'output' or right[3] != 'input' or nets[a]['net'] == '<unconnected>'
                    or nets[a]['net'] != nets[b]['net']):
                raise ValueError('path wire does not follow actual connected physical net')
            if left[4] == right[4]:
                owner = left[4]; kind = 'node_wire' if owner in node_scopes else 'boundary_wire'
            else:
                owner = left[4] + '->' + right[4]; kind = 'inter_owner_wire'
        totals[kind + ':' + owner] += delay
        if kind in ('node_cell', 'node_wire'):
            node_totals[owner] += delay
            if not order or order[-1] != owner:
                if owner in order:
                    raise ValueError('path reenters an earlier node; declared combinational graph is inconsistent')
                order.append(owner)
        segments.append(dict(from_pin=a, to_pin=b, kind=kind, owner=owner, delay_ps=delay))
    total = (points[-1][1] - points[0][1]) * time_to_ps
    summed = math.fsum(s['delay_ps'] for s in segments)
    if not math.isclose(total, summed, rel_tol=1e-12, abs_tol=1e-6):
        raise ValueError('physical path timing ownership does not conserve delay')
    if not node_totals:
        raise ValueError('arithmetic node absent from data path')
    return dict(version=VERSION, Q_to_D_ps=total, node_delay_ps=dict(node_totals), node_order=order,
                non_node_delay_ps=total-math.fsum(node_totals.values()), totals_ps=dict(totals), segments=segments,
                increments_owned_exactly_once=True, operator_maximum_covered=False,
                role='raw_path_witness_only_not_a_training_or_prediction_feature')


def from_saved(prefix, label, pins, node_scopes, time_to_ps=1):
    from .model_reference_labels_v2 import canonical_instances
    raw = {}
    for line in Path(str(prefix) + '_instances.tsv').read_text().splitlines():
        row = line.split('\t')
        if row[0] in raw:
            raise ValueError('duplicate saved physical instance')
        raw[row[0]] = row[1]
    file = Path(str(prefix) + '_reference_' + label['id'] + '_points.tsv')
    points = [(n, float(v)) for n, v in (line.split('\t') for line in file.read_text().splitlines())]
    result = decompose(points, label['start_pin'], label['end_pin'], canonical_instances(raw), pins,
                       connections(str(prefix) + '_reference_connections.tsv'), node_scopes, time_to_ps)
    if not math.isclose(result['Q_to_D_ps'], label['data_delay_ps'], abs_tol=1e-6, rel_tol=1e-9):
        raise ValueError('saved witness differs from registered Q-D label')
    return result
