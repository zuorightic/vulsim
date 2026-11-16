"""Run an independent, later case ahead of the serial physical controller.

Only the frozen target JSON, software inputs and original selector are used.
The isolated directory prevents two selectors from writing the same files.
Import is explicit and refuses a case that the serial worker has started.
No model, search credit, target or physical task is changed by this helper.
"""
import argparse
import os
from pathlib import Path
import shutil
import time

from .workload_abcd import read, write, sha
from .workload_final_selection import select_case, BASE


def prepare(root, cid):
    root = Path(root).resolve()
    target = root / 'targets' / (cid + '.json')
    software = root / 'software'
    isolated = root / 'parallel-software' / cid
    isolated.mkdir(parents=True, exist_ok=True)
    for name in ('bindings.json', 'characterization-contract.json', 'protocol.json'):
        source, dest = software / name, isolated / name
        if dest.exists() and sha(dest) != sha(source):
            raise ValueError('parallel software input changed: ' + name)
        if not dest.exists():
            shutil.copyfile(source, dest)
    case_dir = isolated / cid
    case_dir.mkdir(exist_ok=True)
    if not (case_dir / 'source').exists():
        shutil.copytree(software / cid / 'source', case_dir / 'source')
    source, dest = software / cid / 'static-pool.json', case_dir / 'static-pool.json'
    if dest.exists() and sha(dest) != sha(source):
        raise ValueError('parallel candidate pool changed')
    if not dest.exists():
        shutil.copyfile(source, dest)
    contract = dict(case=cid, targets_ps=read(target)['targets_ps'],
                    target_sha256=sha(target), static_pool_sha256=sha(source),
                    selector_source_sha256=sha(Path(__file__).with_name('workload_final_selection.py')),
                    model_sha256=sha(BASE / 'diagnostic-model.json'),
                    isolated_directory=str(isolated), response_refitted=False,
                    candidate_policy_changed=False, application_PPA_read=False,
                    EDA_calls=0)
    receipt = isolated / 'parallel-inputs.json'
    if receipt.exists() and read(receipt) != contract:
        raise ValueError('parallel input freeze changed')
    write(receipt, contract)
    return isolated, contract


def run(root, cid):
    isolated, contract = prepare(root, cid)
    result = select_case(isolated, cid, contract['targets_ps'])
    write(isolated / 'parallel-ready.json', dict(
        status='ready', case=cid,
        inputs_sha256=sha(isolated / 'parallel-inputs.json'),
        selections_sha256=sha(isolated / cid / 'final-selections.json'),
        target_count=len(result['records']), EDA_calls=0))
    return result


def import_ready(root, cid):
    root = Path(root).resolve()
    isolated, contract = prepare(root, cid)
    ready = read(isolated / 'parallel-ready.json')
    source_case, dest_case = isolated / cid, root / 'software' / cid
    final = dest_case / 'final-selections.json'
    if final.exists() or any(dest_case.glob('scores-T*')):
        raise ValueError('serial selector has already started this case; retain isolated result')
    if ready['selections_sha256'] != sha(source_case / 'final-selections.json'):
        raise ValueError('isolated selection changed after completion')
    # The serial worker is still processing an earlier independent case.
    # Publish the completed file last, so its ordinary existence check can
    # skip all work for this case. Absolute provenance paths stay valid.
    for src in source_case.iterdir():
        if src.name in ('source', 'static-pool.json', 'final-selections.json'):
            continue
        dest = dest_case / src.name
        if dest.exists():
            raise ValueError('serial output appeared during import: ' + str(dest))
        if src.is_dir():
            shutil.copytree(src, dest)
        else:
            shutil.copyfile(src, dest)
    selected = root / 'software' / 'selected' / cid
    if selected.exists():
        raise ValueError('serial selected artifacts appeared during import')
    shutil.copytree(isolated / 'selected' / cid, selected)
    staged = dest_case / '.parallel-final-selections.json'
    shutil.copyfile(source_case / 'final-selections.json', staged)
    # Link creation is atomic and cannot overwrite a concurrently published
    # serial result. It also avoids exposing a partially copied JSON file.
    os.link(staged, final)
    staged.unlink()
    write(isolated / 'parallel-imported.json', dict(
        status='imported', case=cid, targets_ps=contract['targets_ps'],
        selections_sha256=sha(final), numerical_identity_preserved=True,
        absolute_provenance_directory_retained=str(isolated), EDA_calls=0))
    return read(final)


def watch(root, cid):
    root = Path(root).resolve()
    target = root / 'targets' / (cid + '.json')
    while not target.exists():
        progress = read(root / 'A-reference' / 'progress.json')
        if any(e['task'] == cid + '-A-reference' for e in progress['errors']):
            raise RuntimeError('reference A failed; no clock may be invented: ' + cid)
        if cid + '-A-reference' in progress['completed']:
            from .workload_tight_run import freeze_target
            from .workload_contracts import load
            freeze_target(root, next(c for c in load()['cases'] if c['id'] == cid))
            break
        time.sleep(5)
    dest = root / 'software' / cid
    if (dest / 'final-selections.json').exists() or any(dest.glob('scores-T*')):
        raise RuntimeError('serial worker reached case before parallel launch: ' + cid)
    result = run(root, cid)
    if not (dest / 'final-selections.json').exists() and not any(dest.glob('scores-T*')):
        result = import_ready(root, cid)
        print('PARALLEL_IMPORTED ' + cid, flush=True)
    else:
        print('PARALLEL_ISOLATED_ONLY ' + cid, flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('run', 'import', 'watch'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--case', required=True)
    args = parser.parse_args()
    action = {'run': run, 'import': import_ready, 'watch': watch}[args.action]
    result = action(args.root, args.case)
    print(dict(case=args.case, targets_ps=result['targets_ps'], action=args.action))
