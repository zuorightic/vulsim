"""Verify the revised step-two frozen sources, vectors, traces and accounting.

No compiler, EDA installation or build directory is required. Frozen Python
references load in a separate namespace, so later active-source changes cannot
silently redefine this historical verification.
"""
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import re
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
FREEZE = 'experiments/arithmetic/step2_freeze_v4.json'


def check_trace(text, case, rows, oracle):
    count = comparisons = 0
    done = False
    for line in text.splitlines():
        if line.startswith('ROW '):
            fields = line.split()
            if count >= len(rows) or int(fields[1]) != count:
                raise ValueError('trace sequence mismatch')
            expected = oracle(case,rows[count])
            if [int(x,16) for x in fields[2:]] != list(expected.values()):
                raise ValueError(f'{case["id"]}: arithmetic mismatch at row {count}')
            comparisons += len(expected)
            count += 1
        elif line.startswith('CASE RUN PASS'):
            if done or line != f'CASE RUN PASS rows={len(rows)}':
                raise ValueError('invalid completion marker')
            done = True
    if not done or count != len(rows):
        raise ValueError('incomplete functional trace')
    return comparisons


def verify(root=ROOT):
    root = Path(root)
    freeze = json.loads((root/FREEZE).read_text())
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    snapshot = root/freeze['validated_source_snapshot']
    mismatches = []
    for relative, expected in freeze['files_sha256'].items():
        if digest(snapshot/relative) != expected:
            raise ValueError(f'frozen source mismatch: {relative}')
        if not (root/relative).is_file() or digest(root/relative) != expected:
            mismatches.append(relative)
    for relative, expected in freeze['historical_freezes'].items():
        if digest(root/relative) != expected:
            raise ValueError(f'historical freeze was changed: {relative}')
    if digest(root/freeze['evidence_index']) != freeze['evidence_index_sha256']:
        raise ValueError('evidence index hash mismatch')
    index = json.loads((root/freeze['evidence_index']).read_text())
    for item in index['files']:
        if digest(root/item['path']) != item['sha256']:
            raise ValueError(f'evidence hash mismatch: {item["path"]}')
    ev = root/freeze['evidence_directory']
    namespace = '_vulsim_step2_frozen_'+freeze['files_sha256']['experiments/arithmetic_dse/reference.py'][:12]
    package = types.ModuleType(namespace)
    package.__path__ = [str(snapshot/'experiments/arithmetic_dse')]
    sys.modules[namespace] = package
    previous_bytecode_policy = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        contracts = importlib.import_module(namespace+'.contracts')
        generator = importlib.import_module(namespace+'.case_generator')
        reference = importlib.import_module(namespace+'.reference')
        manifest = json.loads((ev/'cases_v2.json').read_text())
        partition = contracts.check_partition(manifest)
        by_id = {c['id']:c for c in manifest['cases']}
        functional = {'sim':0,'native':0}
        for item in index['traces']:
            case = by_id[item['case']]
            rows = json.loads((ev/'sources'/case['id']/'vectors.json').read_text())
            text = gzip.decompress((root/item['path']).read_bytes()).decode()
            count = check_trace(text,case,rows,reference.evaluate_spec)
            if count != item['output_values_compared']:
                raise ValueError('trace aggregate mismatch')
            functional[item['backend']] += count
        if (sorted(x['case'] for x in index['traces'] if x['backend']=='sim') != sorted(by_id)
                or sorted(x['case'] for x in index['traces'] if x['backend']=='native') != sorted(freeze['native_cases'])):
            raise ValueError('functional case coverage mismatch')
        for case in manifest['cases']:
            source = ev/'sources'/case['id']
            for name, text in generator.source_files(case).items():
                if (source/name).read_text() != text:
                    raise ValueError('generated source differs from frozen generator')
            rows = json.loads((source/'vectors.json').read_text())
            if rows != generator.validation_vectors(case):
                raise ValueError('vectors differ from deterministic frozen generator')
        # Bypass hashing to test the arithmetic checker itself on a high bit.
        item = next(x for x in index['traces'] if x['case']=='DOT2_128' and x['backend']=='sim')
        text = gzip.decompress((root/item['path']).read_bytes()).decode()
        lines = text.splitlines()
        at = next(i for i,line in enumerate(lines) if line.startswith('ROW '))
        fields = lines[at].split()
        fields[2] = f'{int(fields[2],16) ^ (1 << 256):x}'
        lines[at] = ' '.join(fields)
        rows = json.loads((ev/'sources/DOT2_128/vectors.json').read_text())
        try:
            check_trace('\n'.join(lines),by_id['DOT2_128'],rows,reference.evaluate_spec)
        except ValueError:
            negative = '257th_output_bit_corruption_rejected'
        else:
            raise ValueError('arithmetic checker accepted high-bit corruption')
    finally:
        sys.dont_write_bytecode = previous_bytecode_policy
        for name in list(sys.modules):
            if name == namespace or name.startswith(namespace+'.'):
                del sys.modules[name]
    before = json.loads((ev/'usage_before.json').read_text())
    after = json.loads((ev/'usage_checkpoint.json').read_text())
    if after['entries'][:len(before['entries'])] != before['entries']:
        raise ValueError('historical resource entries changed')
    entries = after['entries'][len(before['entries']):]
    def totals(items):
        return {**{s:sum(e['stage']==s for e in items) for s in ('synth','grt','final')},
                'support_calls':sum(e['stage'] is None for e in items),
                'walltime_s':sum(e['walltime_s'] for e in items),
                'CPU_time_s':sum(e['CPU_time_s'] for e in items),
                'pending':sum(e['status']=='reserved' for e in items)}
    resources = json.loads((ev/'resources.json').read_text())
    if (after['usage'] != totals(after['entries']) or resources['new_usage'] != totals(entries)
            or resources['cumulative_usage'] != after['usage'] or after['usage']['pending']):
        raise ValueError('resource aggregates differ from leaf entries')
    receipts = {item['id']:item for item in index['commands']}
    if set(receipts) != {e['id'] for e in entries}:
        raise ValueError('incomplete leaf command receipts')
    for entry in entries:
        item = receipts[entry['id']]
        record = json.loads((root/item['record']).read_text())
        values = re.findall(r'(?:User|System) time \(seconds\):\s*([\d.]+)',(root/item['resources']).read_text())
        if (entry['stage'] is not None or entry['status']=='reserved'
                or entry['exit_code'] != record['exit_code']
                or entry['walltime_s'] != record['walltime_s']
                or len(values) != 2 or abs(sum(map(float,values))-entry['CPU_time_s']) > 1e-8
                or record['cleanup']['remaining_live_pids']):
            raise ValueError('support resource settlement mismatch')
    live = root/'experiments/arithmetic/backend_usage.json'
    if live.exists() and json.loads(live.read_text())['entries'][:len(after['entries'])] != after['entries']:
        raise ValueError('live ledger dropped checkpoint entries')
    return {'status':'passed','freeze':freeze['version'],'source_files':len(freeze['files_sha256']),
            'evidence_files':len(index['files']),'partition':partition,
            'functional_output_values':functional,'negative_check':negative,
            'new_support_commands':len(entries),'failed_support_commands':sum(e['exit_code']!=0 for e in entries),
            'current_source_mismatches':mismatches,
            'verification_scope':'current_source' if not mismatches else 'frozen_source_snapshot_only',
            'requires_build_directory':False,'requires_EDA_tools':False,
            'native_dynamic_divmod':'not_implemented; step6','D_model':'not_implemented; step7'}


if __name__ == '__main__':
    print(json.dumps(verify(),indent=2))
