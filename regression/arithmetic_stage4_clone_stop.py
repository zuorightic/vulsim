"""Record an actual hierarchy-clone qualification failure without relabeling it."""
import argparse
from pathlib import Path
import sys
from types import FunctionType

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.arithmetic_dse import model_physical_labels_v2 as labels
from experiments.arithmetic_dse.model_fast_preflight import read, write, sha


def verify(root, out):
    source = 's68decd5321da7cf0'
    folder = root/'raw'/source/'target-463/runs'/f'{source}-T463'
    contract = read(folder/'query-contract.json')
    cells = read(folder/'liberty-pins.json')
    reports = folder/'reports/asap7/arithmetic_probe/base'
    for line in (reports/'vulsim_grt_cells.tsv').read_text().splitlines():
        master, count, area, filler, kind = line.split('\t')
        if master not in cells:
            cells[master] = dict(sequential=False, buffer_or_inverter=False,
                physical_only=True, data_pins=[], pins={}, area_um2=0 if filler=='1' else float(area))
    namespace = dict(labels.read_snapshot.__globals__)
    namespace['extract'] = lambda packet, *args: packet
    capture = FunctionType(labels.read_snapshot.__code__, namespace, closure=labels.read_snapshot.__closure__)
    capture.__kwdefaults__ = labels.read_snapshot.__kwdefaults__
    packet = capture(reports/'context_grt', 463, 1, cells, contract['nodes'], contract['banks'])
    name = 'clone454'
    master = packet['instances'][name]
    if master != packet['instances']['core/_472_'] or master != 'OA211x2_ASAP7_75t_R':
        raise ValueError('actual cloned master differs')
    inputs = [p for p, meta in cells[master]['pins'].items() if meta['direction']=='input']
    if not inputs or cells[master]['sequential'] or cells[master]['buffer_or_inverter']:
        raise ValueError('expected real multi-input arithmetic clone')
    for pin in inputs:
        if packet['connections'][name+'/'+pin]['net'] != packet['connections']['core/_472_/'+pin]['net']:
            raise ValueError('clone does not share original inputs')
    try:
        labels.extract(packet, contract['nodes'], contract['banks'])
    except ValueError as error:
        if str(error) != 'unowned physical cell':
            raise
    else:
        raise ValueError('unsupported hierarchy clone was accepted')
    history = read(root/'raw'/source/'history.json')
    if len(history)!=3 or [r['status'] for r in history] != ['completed','completed','failed']:
        raise ValueError('source history differs')
    if (folder/'grt-labels.json').exists():
        raise ValueError('unqualified clone unexpectedly has a grt label')
    for stage in ('synth','grt'):
        if read(folder/(stage+'.command.json'))['exit_code']:
            raise ValueError('expected physically successful saved stages')
    write(out, dict(status='passed', source=source, target_ps=463, actual_clone=name,
        original='core/_472_', master=master, clone_pins={p:packet['connections'][name+'/'+p] for p in cells[master]['pins']},
        result='qualification_failure_retained; no node label generated; source stops at first failed point',
        prior_qualified_points_retained=2, new_synth=0, new_grt=0,
        qualification_source_sha256=sha(Path(labels.__file__)), history_sha256=sha(root/'raw'/source/'history.json'),
        raw_report_sha256={p.name:sha(p) for p in [reports/'context_grt_instances.tsv',reports/'context_grt_connections.tsv',folder/'liberty-pins.json']}))
    print('ACTUAL_HIERARCHY_CLONE_REJECTED; prior two points retained; no physical retry', flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--root',type=Path,required=True); p.add_argument('--out',type=Path,required=True)
    a=p.parse_args(); verify(a.root.resolve(),a.out.resolve())
