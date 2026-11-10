"""Standalone stdlib restoration of the frozen incremental acceptance."""
import argparse
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile


def read(path):return json.loads(path.read_text())
def digest(data):return hashlib.sha256(data).hexdigest()


def replay(evidence):
    manifest=read(evidence/'manifest.json');compressed=[]
    if digest((evidence/'summary.json').read_bytes())!=manifest['review_sha256']:
        raise ValueError('review changed')
    if digest((evidence/'replay.py').read_bytes())!=manifest['replay_sha256']:
        raise ValueError('replay changed')
    for name,h in manifest['chunks'].items():
        if Path(name).name!=name:raise ValueError('unsafe chunk')
        raw=(evidence/name).read_bytes()
        if digest(raw)!=h:raise ValueError('chunk changed')
        compressed.append(raw)
    raw=gzip.decompress(b''.join(compressed))
    if digest(raw)!=manifest['payload_sha256']:raise ValueError('payload changed')
    pool=json.loads(raw)
    with tempfile.TemporaryDirectory(prefix='steps123-incremental-restore-') as directory:
        restored=Path(directory)
        for name,content in pool['files'].items():
            if Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('unsafe member')
            dest=restored/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(content)
            if dest.read_text()!=content:raise ValueError('actual restore changed')
        for name,h in manifest['source_sha256'].items():
            if digest((restored/name).read_bytes())!=h:raise ValueError('frozen source changed')
        sys.path.insert(0,str(restored))
        for name in list(sys.modules):
            if name in ('experiments','regression') or name.startswith(('experiments.','regression.')):del sys.modules[name]
        feature=importlib.import_module('regression.arithmetic_incremental_acceptance')
        physical=importlib.import_module('regression.arithmetic_incremental_physical')
        protocol=importlib.import_module('regression.arithmetic_incremental_protocol')
        wide=importlib.import_module('experiments.arithmetic_dse.operator_condition_wide')
        if any(not Path(m.__file__).is_relative_to(restored) for m in (feature,physical,protocol,wide)):
            raise ValueError('live module replaced frozen source')
        expected=read(restored/'vectors/feature-proof.json')
        feature.verify(restored/'vectors')
        if expected!=read(restored/'vectors/feature-proof.json'):raise ValueError('feature replay changed')
        physical.verify(restored/'collection',restored/'physical-replay',portable=True)
        result=read(restored/'physical-replay/proof.json')
        saved=read(restored/'proofs/physical-replay-v2-proof.json')
        if result['rows']!=saved['rows'] or result['single_arc_negative_checks']!=saved['single_arc_negative_checks']:
            raise ValueError('portable physical replay changed')
        wide.preflight(restored/'sampler.json')
        saved_sampler=read(restored/'proofs/sampler-proof-v4.json')
        if read(restored/'sampler.json')!=saved_sampler:raise ValueError('sampler replay differs')
        protocol.gates(restored/'collection',restored/'sampler.json',restored/'gates')
        if read(restored/'gates/proof.json')['count']!=read(restored/'proofs/gates-v1-proof.json')['count']:
            raise ValueError('protocol gate replay differs')
        summary=read(restored/'summary.json')
        if summary!=read(evidence/'summary.json'):raise ValueError('summary binding differs')
        print(dict(status='passed',restored_files=len(pool['files']),feature_queries=expected['queries'],
            physical_points=len(result['points']),physical_stages=result['stages'],negative_arcs=result['negative_checks'],
            protocol_checks=summary['protocol_checks'],new_EDA_calls=0,physical_test_labels_read=False,
            full_CEC_scope='saved conclusions/logs only; full exact pair checked in original local replay',full_D_ready=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True)
    a=p.parse_args();replay(a.evidence.resolve())
