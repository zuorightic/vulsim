"""Extract stage-local path evidence without inferring mapper/STA equivalence."""
from decimal import Decimal
import re


def critical_path(text):
    paths = []
    for block in re.split(r'(?=Startpoint:)',text):
        if not block.startswith('Startpoint:'):
            continue
        start = re.search(r'^Startpoint:\s*(.*)',block,re.M)[1].strip()
        end = re.search(r'^Endpoint:\s*(.*)',block,re.M)[1].strip()
        slack = re.search(r'([-+\d.]+)\s+slack\s+\(',block)
        if not slack:
            continue
        row = {'startpoint':start,'endpoint':end,
               'path_group':re.search(r'^Path Group:\s*(.*)',block,re.M)[1].strip(),
               'slack_ps':float(slack[1])}
        pins = {}
        for line in block.splitlines():
            match = re.match(r'^\s*([-+\d.\s]+)\s+[\^v]\s+(.+?)\s+\([^)]+\)\s*$',line)
            if match:
                numbers = match[1].split()
                if len(numbers)>=2:
                    pins[match[2]] = (Decimal(numbers[-2]),Decimal(numbers[-1]))
        qname = next((name for name in pins if name in [start+'/Q',start+'/QN']),None)
        if qname and end+'/D' in pins:
            clkq = pins[qname][0]
            qd = pins[end+'/D'][1]-pins[qname][1]
            row.update(clock_to_Q_ps=float(clkq),Q_to_D_combinational_ps=float(qd),
                       launch_clock_arrival_ps=float(pins[start+'/CLK'][1]),
                       endpoint_D_arrival_ps=float(pins[end+'/D'][1]))
            setup = re.search(r'([-+\d.]+)\s+[-+\d.]+\s+library setup time',block)
            uncertainty = re.search(r'([-+\d.]+)\s+[-+\d.]+\s+clock uncertainty',block)
            if setup and uncertainty:
                setup_ps,uncertainty_ps = abs(Decimal(setup[1])),abs(Decimal(uncertainty[1]))
                row.update(library_setup_ps=float(setup_ps),setup_uncertainty_ps=float(uncertainty_ps),
                           data_and_setup_sum_ps=float(clkq+qd+setup_ps+uncertainty_ps),
                           sum_interpretation='excludes capture/launch clock skew; equals setup period requirement only under ideal common clock')
        paths.append(row)
    if not paths:
        raise ValueError('no complete reported max timing path')
    return min(paths,key=lambda row:row['slack_ps'])


def master_inventory(text):
    counts = {}
    for line in text.splitlines():
        master,count,*_ = line.split('\t')
        counts[master] = int(count)
    return {'counts_by_master':dict(sorted(counts.items())),
            'total_instances':sum(counts.values()),
            'buffer_instances':sum(n for name,n in counts.items() if name.startswith('BUF')),
            'inverter_instances':sum(n for name,n in counts.items() if name.startswith('INV')),
            'sequential_instances':sum(n for name,n in counts.items() if name.startswith(('DFF','SDFF')))}
