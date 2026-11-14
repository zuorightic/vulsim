"""Offline audit of root-conditioned endpoint paths and branch budgets.

These are measured descriptors for explaining saved implementation controls.
They are prohibited as online pricing inputs. Instance origins are not pin
locations; root-conditioned worst paths are not Rebuffer's unrestricted
vertexWorstSlackPath. No physical causality or prospective accuracy is claimed.
"""
from collections import defaultdict
import math
import statistics

from .model_physical_path_v2 import verify_combinational_arc

VERSION = 'root-conditioned-control-branch-budget-audit-v15'


def distribution(values):
    values = sorted(values)
    if not values or any(not math.isfinite(v) for v in values):
        raise ValueError('nonempty finite distribution required')
    index = .95 * (len(values)-1)
    low = int(index)
    high = min(len(values)-1, low+1)
    return dict(count=len(values), minimum=values[0], median=statistics.median(values),
        P95=values[low] + (index-low)*(values[high]-values[low]), maximum=values[-1])


def close(a, b):
    if not math.isfinite(a) or not math.isfinite(b) or abs(a-b) > 1e-3:
        raise ValueError('timing identity mismatch')


def analyze(start, instances, library, nets, endpoints, paths, origins, period_ps):
    if set(endpoints) != set(paths) or period_ps <= 0:
        raise ValueError('timing endpoint boundary mismatch')
    branches = defaultdict(list)
    root_instance = start.rsplit('/', 1)[0]
    root_xy = origins[root_instance]
    checked_arcs = checked_wires = 0
    endpoint_distances = []
    for endpoint, row in endpoints.items():
        points = paths[endpoint]
        if not points or points[0]['pin'] != start or points[-1]['pin'] != endpoint:
            raise ValueError('control path launch/capture mismatch')
        close(row['root_arrival_ps'], points[0]['arrival_ps'])
        close(row['end_arrival_ps'], points[-1]['arrival_ps'])
        close(row['required_ps'], row['end_arrival_ps'] + row['slack_ps'])
        close(row['delay_ps'], row['end_arrival_ps'] - row['root_arrival_ps'])
        close(row['budget_ps'], row['required_ps'] - row['root_arrival_ps'])
        first = None
        for i, point in enumerate(points):
            pin = point['pin']
            if pin not in nets or not math.isfinite(point['arrival_ps']) or not math.isfinite(point['required_ps']):
                raise ValueError('unbound or nonfinite timing point')
            inst, terminal = pin.rsplit('/', 1)
            if inst not in origins or len(origins[inst]) != 2 or any(not math.isfinite(v) for v in origins[inst]):
                raise ValueError('unbound physical instance origin')
            if not math.isfinite(point['cap_fF']) or point['cap_fF'] < 0:
                raise ValueError('invalid measured input capacitance')
            if i:
                previous = points[i-1]
                src = previous['pin']
                src_inst, src_pin = src.rsplit('/', 1)
                if point['arrival_ps'] < previous['arrival_ps']-1e-3:
                    raise ValueError('nonmonotone control path')
                if src_inst == inst:
                    verify_combinational_arc(library[instances[inst]], src_pin, terminal)
                    checked_arcs += 1
                elif nets[src]['direction'] == 'output' and nets[pin]['direction'] == 'input' and nets[src]['net'] == nets[pin]['net']:
                    checked_wires += 1
                else:
                    raise ValueError('unconnected measured control path')
            meta = library[instances[inst]]
            if first is None and nets[pin]['direction'] == 'input' and not meta['buffer_or_inverter']:
                # Endpoint required minus the selected tail delay gives a
                # root-conditioned budget at the first non-buffer input.
                first = dict(pin=pin, cap_fF=point['cap_fF'],
                    budget_from_root_ps=row['slack_ps'] + point['arrival_ps'] - row['root_arrival_ps'],
                    distance_dbu=math.fsum(abs(x-y) for x,y in zip(origins[inst], root_xy)))
        if first is None:
            raise ValueError('no first non-buffer load on sequential endpoint path')
        branches[first['pin']].append(dict(endpoint=endpoint, **first))
        endpoint_distances.append(math.fsum(abs(x-y) for x,y in zip(origins[endpoint.rsplit('/', 1)[0]], root_xy)))
    rows = []
    for pin, members in sorted(branches.items()):
        if len({m['cap_fF'] for m in members}) != 1 or len({m['distance_dbu'] for m in members}) != 1:
            raise ValueError('inconsistent measured branch load identity')
        rows.append(dict(pin=pin, endpoint_count=len(members), endpoints=sorted(m['endpoint'] for m in members),
            cap_fF=members[0]['cap_fF'], distance_dbu=members[0]['distance_dbu'],
            tightest_budget_ps=min(m['budget_from_root_ps'] for m in members)))
    valid = [e for e in endpoints if e.rsplit('/', 1)[0].startswith('native/valid_')]
    if len(valid) != 1:
        raise ValueError('one valid capture required for this mechanism audit')
    valid = valid[0]
    data = [r for e,r in endpoints.items() if e != valid]
    return dict(version=VERSION, endpoints=len(endpoints), data_endpoints=len(data),
        first_nonbuffer_branches=len(rows), checked_cell_arcs=checked_arcs, checked_wires=checked_wires,
        valid_R_ps=period_ps-endpoints[valid]['slack_ps'],
        valid_budget_ps=endpoints[valid]['budget_ps'], valid_delay_ps=endpoints[valid]['delay_ps'],
        data_R_ps=distribution([period_ps-r['slack_ps'] for r in data]),
        data_endpoint_budget_ps=distribution([r['budget_ps'] for r in data]),
        branch_budget_ps=distribution([r['tightest_budget_ps'] for r in rows]),
        branch_cap_fF=distribution([r['cap_fF'] for r in rows]),
        branch_origin_distance_dbu=distribution([r['distance_dbu'] for r in rows]),
        endpoint_origin_distance_dbu=distribution(endpoint_distances),
        first_branch_pin_cap_sum_fF=math.fsum(r['cap_fF'] for r in rows), branches=rows,
        usable_as_online_price_feature=False, Rebuffer_unrestricted_budget_claimed=False,
        physical_causality_claimed=False, pin_coordinates_claimed=False)
