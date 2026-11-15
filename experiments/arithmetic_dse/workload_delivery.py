"""Seal portable workload selections, implementations and physical receipts.

ODB, simulator binaries and bulk physical logs remain in the raw artifact
root. The portable package contains their recorded identities, selected RTL,
testbenches, full selected prices, all compact ranking records and reports.
"""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import shutil

from .workload_abcd import ROOT,read,write,sha
from .workload_results import save


def ensure_support_settled(root, report):
    if report['measurement_cost']['pending']:
        raise ValueError('settle every physical or proof leaf before sealing')
    for path in (root/'proofs').glob('*/admission.json'):
        folder=path.parent;command=folder/'command.json'
        if not command.is_file():
            raise ValueError('proof admission is still queued or running: '+folder.name)
        record=read(command)
        if record['cleanup']['remaining_live_pids']:
            raise ValueError('proof process cleanup is incomplete: '+folder.name)
        receipts=[read(p) for p in (folder/'proof.json',folder/'result/proof.json') if p.is_file()]
        if not record['exit_code'] and not any(p['status'] in ('passed','failed') for p in receipts):
            raise ValueError('proof command lacks its terminal validation receipt: '+folder.name)


def export(root,destination):
    root=Path(root).resolve();destination=Path(destination).resolve()
    if destination.exists():raise ValueError('preserve existing portable delivery')
    report=save(root)
    if report['status'] not in ('completed','settled_with_failures'):
        raise ValueError('settle every finite measurement before sealing; queued/running tasks are incomplete')
    ensure_support_settled(root,report)
    files={};tails={}
    def add(path):
        path=Path(path).resolve()
        if path.is_file():files[str(path)]=base64.b64encode(path.read_bytes()).decode()
    for name in ('selection-freeze.json','baselines-freeze.json'):
        p=root/name;add(p)
        for n in read(p)['files']:add(n)
    for pattern in ('*.json','*.log','comparison.md','comparison.csv','diagnostic-scores/*/*/*/selection.json',
                    'baseline-inputs/*/*.json','baseline-inputs/*/*.sv','baseline-inputs/*/*.log',
                    'diagnostic-inputs/*/*.json','diagnostic-inputs/*/*.sv','diagnostic-inputs/*/*.log',
                    'clock-readout*/*/*.json','clock-readout*/*/*.tsv','clock-readout*/*/*.tcl','clock-readout*/*/*.log',
                    'capacity/*/admission.json','capacity/*/progress.json','capacity/*/execution-note.json',
                    'capacity/*/queue-admission.json','capacity/*/queue-driver.py',
                    'capacity/*/authorization.json','authorizations/*.json','proposals/*/*.json','proposals/*/*.py',
                    'capacity-mechanism-source/**/*',
                    'waves/*/*.json','waves/*/driver.py','proofs/*/*.json','proofs/*/*.log',
                    'proofs/*/result/proof.json','proofs/*/result/cec.log','proofs/*/result/negative-*.log',
                    'capacity/*/*.py','capacity/*/source/**/*.py','capacity/*/source/**/*.tcl'):
        for p in root.glob(pattern):add(p)
    # Archive transitive local Python implementations without executing imports.
    # Existing source copies take precedence over the current worktree below.
    for p in (ROOT/'experiments/arithmetic_dse').glob('*.py'):add(p)
    for p in (ROOT/'regression').glob('test_workload*.py'):add(p)
    for directory in ('measurement-source','measurement-correction-source'):
        for p in (root/directory).rglob('*'):
            if p.is_file():add(p)
    baseline=read(root/'baselines.json')
    for row in baseline['records']:
        for method in ('A','B','C'):add(Path(row[method]['folder']).parent/'graph.json')
    runs=list((root/'runs').glob('*'))+list((root/'capacity').glob('*/runs/*'))
    for d in runs:
        if not (d/'manifest.json').exists():continue
        add(d/'manifest.json');add(d/'metrics.json');add(d/'config.mk');add(d/'input.sv')
        for p in d.glob('verify-*.py'):add(p)
        add(d/'logs/asap7/arithmetic_probe/base/4_rsz_lec_check.log')
        for p in (d/'flow-scripts').glob('*'):
            if p.is_file() and not p.is_symlink():add(p)
        for p in d.glob('*.command.json'):add(p)
        for p in d.glob('*.resources.txt'):add(p)
        for p in (d/'clock-readout').glob('*'):
            if p.is_file():add(p)
        for p in d.glob('reports/asap7/arithmetic_probe/base/vulsim_*'):
            if p.is_file():add(p)
        m=read(d/'manifest.json')
        for c in m['commands']:
            p=Path(c['log'])
            if c.get('exit_code') and p.exists():tails[str(p)]='\n'.join(p.read_text(errors='replace').splitlines()[-80:])
    payload=json.dumps(dict(version='nine-workload-diagnostic-portable-v1',files=files,
                            retained_failure_log_tails=tails),separators=(',',':')).encode()
    compressed=gzip.compress(payload,mtime=0);destination.mkdir(parents=True)
    chunks=[]
    for i,start in enumerate(range(0,len(compressed),512*1024)):
        data=compressed[start:start+512*1024];name=f'payload-{i:03d}.part'
        (destination/name).write_bytes(data);chunks.append(dict(file=name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
    replay=ROOT/'experiments/arithmetic_dse/reference_assets/workload_diagnostic_replay.py'
    shutil.copy2(replay,destination/'replay.py')
    write(destination/'manifest.json',dict(version='nine-workload-diagnostic-portable-v1',original_root=str(root),
        qualification=report['qualification'],chunks=chunks,payload_sha256=hashlib.sha256(compressed).hexdigest(),
        replay_sha256=sha(destination/'replay.py'),archived_files=len(files),cases=report['cases'],
        targets=report['targets'],method_records=report['method_records'],physical_tasks=report['physical_tasks'],
        status=report['status'],completed_physical_tasks=report['completed_physical_tasks'],
        failed_physical_tasks=report['failed_physical_tasks'],
        model_sha256=report['model_sha256'],raw_physical_artifacts_included=False,
        replay_scope='frozen identities, full candidate re-ranking, simulation receipts, physical reports and clock equations; no EDA or model refit'))
    return dict(files=len(files),compressed_bytes=len(compressed),chunks=len(chunks))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--destination',type=Path,required=True);a=p.parse_args();print(export(a.root,a.destination))
