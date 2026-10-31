"""Audit step-one wide arithmetic evidence without build artifacts or EDA tools."""
from contextlib import redirect_stdout
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile

from .budget import cpu_seconds, usage

ROOT = Path(__file__).resolve().parents[2]
FREEZE = 'experiments/arithmetic/wide_baseline_freeze_v1.json'


def verify(root=ROOT):
    root = Path(root)
    freeze = json.loads((root/FREEZE).read_text())

    def check(path, expected):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'SHA-256 mismatch: {path}')

    current_mismatches = []
    snapshot = root/freeze['validated_source_snapshot']
    for relative, expected in freeze['files_sha256'].items():
        check(snapshot/relative, expected)
        current = root/relative
        if not current.exists() or hashlib.sha256(current.read_bytes()).hexdigest() != expected:
            current_mismatches.append(relative)
    for relative, expected in freeze['historical_freezes'].items():
        check(root/relative, expected)
    check(root/freeze['evidence_index'], freeze['evidence_index_sha256'])
    index = json.loads((root/freeze['evidence_index']).read_text())
    for item in index['files']:
        check(root/item['path'], item['sha256'])
    ev = root/freeze['evidence_directory']

    # Use the explicitly frozen oracle source even after a later revision.
    source = snapshot/'regression/generator_wide_arithmetic.py'
    spec = importlib.util.spec_from_file_location('wide_baseline_frozen_oracle', source)
    oracle = importlib.util.module_from_spec(spec)
    previous_path = sys.path.copy()
    try:
        spec.loader.exec_module(oracle)
    finally:
        sys.path[:] = previous_path
    reports = []
    negative_checks = []
    with tempfile.TemporaryDirectory(prefix='vul-wide-evidence-') as directory:
        temporary = Path(directory)
        (temporary/'vectors.json').write_bytes((ev/'vectors.json').read_bytes())
        (temporary/'vectors.txt').write_bytes((ev/'vectors.txt').read_bytes())
        for item in index['traces']:
            raw = temporary/'trace.log'
            raw.write_bytes(gzip.decompress((root/item['path']).read_bytes()))
            expected = item['report']
            with redirect_stdout(io.StringIO()):
                oracle.check_trace(temporary, raw, expected['L'])
            observed = json.loads(raw.with_suffix('.checks.json').read_text())
            if observed != {key: expected[key] for key in observed}:
                raise ValueError('trace aggregates differ')
            reports.append(expected)
        probe = next(item for item in index['traces'] if
                     item['report']['mode'] == 'enabled' and
                     item['report']['backend'] == 'native' and item['report']['L'] == 3)
        original = gzip.decompress((root/probe['path']).read_bytes())
        lines = original.decode().splitlines(keepends=True)
        field = [name for name, _ in oracle.fields()].index('full128')
        count = len(oracle.fields())
        for i, line in enumerate(lines):
            tokens = line.split()
            if tokens and tokens[0] == 'ROW' and tokens[2+count] == '1':
                tokens[3+count+field] = f'{int(tokens[3+count+field],16) ^ (1 << 255):064x}'
                lines[i] = ' '.join(tokens)+'\n'
                break
        else:
            raise ValueError('missing valid wide result for negative check')
        raw.write_text(''.join(lines))
        try:
            with redirect_stdout(io.StringIO()):
                oracle.check_trace(temporary, raw, 3)
        except AssertionError:
            negative_checks.append('product_bit255_corruption')
        else:
            raise ValueError('oracle accepted a corrupted high product bit')
        raw.write_bytes(original)
        try:
            with redirect_stdout(io.StringIO()):
                oracle.check_trace(temporary, raw, 2)
        except AssertionError:
            negative_checks.append('L3_trace_as_L2')
        else:
            raise ValueError('oracle accepted a wrong transaction latency')
    if ({(r['backend'], r['L']) for r in reports if r['mode'] == 'enabled'} !=
            {(backend, latency) for backend in ('sim', 'native', 'circt') for latency in (1, 3)}):
        raise ValueError('incomplete enabled backend matrix')
    if ({(r['backend'], r['L']) for r in reports if r['mode'] == 'disabled'} !=
            {(backend, latency) for backend in ('sim', 'native') for latency in (1, 3)}):
        raise ValueError('CIRCT disabled skipped native/software checks')
    for line in (ev/'facts.txt').read_text().splitlines():
        values = line.split()
        w = int(values[0])
        a, b, c, d, product, dot, carry, diff, low = (int(v, 16) for v in values[1:])
        if [product, dot, carry, diff, low] != [a*b, a*b+c*d, a+b+1,
                                              (a-b) & ((1 << w)-1), (a*b) & ((1 << w)-1)]:
            raise ValueError('constant-facts oracle differs')
    if (ev/'facts.log').read_text().strip() != 'WIDE FACTS PASS rows=185 checks=2960 max_width=257':
        raise ValueError('missing direct BEIR acceptance')

    before = json.loads((ev/'usage_before.json').read_text())
    after = json.loads((ev/'usage_checkpoint.json').read_text())
    if after['entries'][:len(before['entries'])] != before['entries']:
        raise ValueError('historical ledger entries changed')
    new = after['entries'][len(before['entries']):]
    if any(e['stage'] is not None or e['status'] == 'reserved' for e in new):
        raise ValueError('unexpected physical call or pending reservation')
    commands = {item['id']: item for item in index['commands']}
    if set(commands) != {entry['id'] for entry in new}:
        raise ValueError('incomplete command/resource evidence')
    for entry in new:
        item = commands[entry['id']]
        record = json.loads((root/item['command']).read_text())
        if (entry['exit_code'] != record['exit_code'] or entry['walltime_s'] != record['walltime_s']
                or record['cleanup']['remaining_live_pids']
                or abs(cpu_seconds(root/item['resources'])-entry['CPU_time_s']) > 1e-8):
            raise ValueError('command/resource settlement mismatch')
    total = usage(after['entries'])
    resources = json.loads((ev/'resources.json').read_text())
    if (total != after['usage'] or total['pending'] or resources['new_usage'] != usage(new)
            or resources['cumulative_usage'] != total):
        raise ValueError('resource summaries differ')
    live = root/'experiments/arithmetic/backend_usage.json'
    if live.exists() and json.loads(live.read_text())['entries'][:len(after['entries'])] != after['entries']:
        raise ValueError('live ledger dropped archived charges')
    compatibility = json.loads((ev/'compatibility-summary.json').read_text())
    if compatibility['status'] != 'passed' or compatibility['CIRCT'] != 'executed':
        raise ValueError('inherited regressions incomplete')
    return {'status': 'passed', 'freeze': freeze['version'],
            'source_scope': 'current' if not current_mismatches else 'explicit_historical_snapshot',
            'current_source_mismatches': current_mismatches,
            'source_files': len(freeze['files_sha256']), 'evidence_files': len(index['files']),
            'wide_configurations': len(reports), 'rows_per_configuration': 1843,
            'negative_checks_rejected': negative_checks,
            'facts_checks': 2960, 'new_usage': usage(new), 'cumulative_usage': total,
            'requires_build_directory': False, 'requires_EDA_tools': False}


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
