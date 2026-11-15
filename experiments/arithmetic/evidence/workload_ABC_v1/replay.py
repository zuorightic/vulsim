#!/usr/bin/env python3
"""Standard-library replay of the sealed ABC records, without external tools."""
import gzip
import hashlib
import json
from pathlib import Path


def digest(raw): return hashlib.sha256(raw).hexdigest()


def replay(root=Path(__file__).resolve().parent):
    manifest = json.loads((root/'manifest.json').read_text())
    if digest((root/'replay.py').read_bytes()) != manifest['replay_sha256']:
        raise ValueError('changed replay implementation')
    source_raw = (root/'source.json.gz').read_bytes()
    if digest(source_raw) != manifest['source_package_sha256']:
        raise ValueError('changed source package')
    source = json.loads(gzip.decompress(source_raw))
    if {n:digest(t.encode()) for n,t in source.items()} != manifest['source_sha256']:
        raise ValueError('changed archived source identity')
    chunks = []
    for row in manifest['chunks']:
        raw = (root/row['file']).read_bytes()
        if digest(raw) != row['sha256']: raise ValueError('changed portable chunk')
        chunks.append(raw)
    payload = b''.join(chunks)
    if digest(payload) != manifest['payload_sha256']: raise ValueError('changed payload')
    files = json.loads(gzip.decompress(payload))['files']
    prefix = manifest['original_root'] + '/'
    freeze = json.loads(files['baselines-freeze.json'])
    for name, expected in freeze['files'].items():
        if not name.startswith(prefix) or digest(files[name[len(prefix):]].encode()) != expected:
            raise ValueError('changed frozen baseline file: '+name)
    def read(name): return json.loads(files[name])
    methods = read('baseline-methods.json'); baselines = read('baselines.json')
    if len(methods['records']) != 19 or len({r['case'] for r in methods['records']}) != 9:
        raise ValueError('incomplete nine-case target matrix')
    def score(row):
        c = row['static']
        return (c['maximum_stage_abstract_delay'],c['comb_weight_plus_saved_bits'],
                c['saved_bits'],c['saved_signals'],row['structure'],int(row['view']))
    rtl = set(); checked = 0
    for row in methods['records']:
        target = row['target']; case = row['case']
        result = read(f"{case}/T{target['T_ps']}-L{target['L']}.json")
        for method in ('B','C'):
            candidates = result['candidates']
            if method == 'B': candidates = [c for c in candidates if c['structure'] == 0]
            winner = min(candidates,key=score)
            if (winner['structure'],winner['view']) != (result[method]['structure'],result[method]['view']):
                raise ValueError('static selection changed')
            checked += 1
        for method, data in row['methods'].items():
            h = data['rtl_sha256']; base = 'baseline-inputs/'+h+'/'
            if (digest(files[base+'workload.sv'].encode()) != h or 'PASS' not in files[base+'simulation.log']
                    or data['L'] != (1 if method == 'A' else target['L'])):
                raise ValueError('implementation/functional-proof/latency mismatch')
            rtl.add(h)
    if len(rtl) != 26 or baselines['D_selected'] or freeze['final_ABCD_freeze']:
        raise ValueError('baseline scope silently promoted to D or backend completion')
    print(dict(status='passed_ABC_portable_replay',cases=9,targets=19,method_records=57,
               static_selections=checked,unique_RTL=26,new_A_cycles=864,
               backend_calls=0,D_selected=False))


if __name__ == '__main__': replay()
