"""Small Git evidence for sealed S failure; full raw archive stays in build."""
import argparse
from contextlib import redirect_stdout
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from .model_d_requirements_evidence import pack, unpack, sha, read, write
from .model_general_state_evidence import frozen_modules

ROOT = Path(__file__).resolve().parents[2]
VERSION = 'asap7-general-state-failure-summary-v2'


def seal(archive, folder, root):
    from .budget import Ledger
    manifest = read(archive / 'manifest.json')
    for name, h in manifest['files'].items():
        if sha(archive / name) != h: raise ValueError('full S archive differs before compact seal')
    folder.mkdir(parents=True, exist_ok=False)
    shutil.copy2(archive / 'documents-pool.json.gz', folder / 'documents-pool.json.gz')
    with tempfile.TemporaryDirectory() as td:
        source = Path(td); unpack(archive / 'source-pool.json.gz', source)
        own = source / 'experiments/arithmetic_dse/model_general_state_summary.py'
        own.write_bytes(Path(__file__).read_bytes())
        pack(folder / 'source-pool.json.gz', {str(p.relative_to(source)): p for p in source.rglob('*') if p.is_file()})
    for name in ('verdict.json', 'publication.json'):
        shutil.copy2(archive / name, folder / name)
    paid = read(archive / 'paid-entries.json')
    (folder / 'paid-entries.json.gz').write_bytes(gzip.compress(json.dumps(paid, separators=(',', ':')).encode(), mtime=0))
    receipt_files = {}; support = set()
    for relative, stems in [('independent-check-v1', ['raw-extract', 'one-time-evaluate']),
                            ('failure-evidence-check-v1', ['seal', 'portable', 'external', 'isolated'])]:
        for stem in stems:
            directory = root / relative; record = read(directory / (stem + '.command.json'))
            if record['exit_code']: raise ValueError('failed S evidence check cannot be claimed')
            support.add(record['budget_reservation_id'])
            for suffix in ('.command.json', '.log', '.resources.txt'):
                receipt_files[relative + '/' + stem + suffix] = directory / (stem + suffix)
    pack(folder / 'check-receipts.json.gz', receipt_files)
    entries = [e for e in read(Ledger().path)['entries'] if e['id'] in support]
    write(folder / 'check-paid-entries.json', entries)
    write(folder / 'raw-archive.json', {'path': str(archive), 'manifest_sha256': sha(archive / 'manifest.json'),
        'files': manifest['files'], 'bytes': sum(p.stat().st_size for p in archive.iterdir() if p.is_file()),
        'portable_scope': 'semantic source/features, frozen area validation/test, original boundary formula and one-shot verdict; paid receipts',
        'external_scope': 'full216 bank/432 stage/3888 path raw replay, actual Liberty/tools and saved complete CTS CEC',
        'raw_archive_checked_portable_external_isolated': True, 'raw_archive_not_required_for_portable_numerical_replay': True})
    (folder / 'README.md').write_text('''# ASAP7一般状态S首轮独立失败：Git小证据

train108／validation54／test54全部完成。一次性独立结果：synth通过，grt三个功能状态／控制面积分项通过原中位20%／P95 50%，控制边界69／72通过，拒绝发布。
1431ps native_enable超14.537323ps；4528ps native_valid超60.583038ps；11913ps native_valid超2.266129ps。原参数、九目标和50ps reserve不变，原54 test永久排除后继拟合／验证／算法／裕量／域选择。

便携数值核验：`python3 -B -m experiments.arithmetic_dse.model_general_state_summary verify --folder experiments/arithmetic/evidence/step7_general_state_failure_v2`
增加`--external`调用原字节完整原始归档，回放216银行／432阶段／3888路径、真实Liberty／工具及完整已存CTS CEC；不重新执行EDA／SAT。
隔离／篡改核验：上述模块改用`isolated --folder ...`。本小包便携模式重生成语义特征并重算固定验证、边界及独立结论，明确不声称只凭本包重建全部原始物理报告。全原始归档位置／hash见raw-archive.json，约106MiB，保存在build；其便携／external／隔离／篡改通过的付费收据随包。

用户已确认后继保留面积原参数，仅补native enable／valid控制边界，最终仍同时检查全部面积与八类非birth边界。新合成源、划分、拟合算法和新独立test须事先登记；不追改本包失败结论。完整D／正式36条未放行。Git由用户提交。
''')
    write(folder / 'manifest.json', {'version': VERSION, 'files': {p.name: sha(p) for p in folder.iterdir() if p.is_file()}})
    print(json.dumps({'status': 'sealed', 'bytes': sum(p.stat().st_size for p in folder.iterdir() if p.is_file()),
        'independent_status': 'failed', 'published': []}), flush=True)


def verify(folder, external=False):
    manifest = read(folder / 'manifest.json')
    if manifest['version'] != VERSION: raise ValueError('S summary version differs')
    for name, h in manifest['files'].items():
        if sha(folder / name) != h: raise ValueError('S summary identity mismatch: ' + name)
    with tempfile.TemporaryDirectory(prefix='S-summary-') as td:
        td = Path(td); source, docs, receipts = (td / n for n in ('source', 'documents', 'receipts'))
        unpack(folder / 'source-pool.json.gz', source); unpack(folder / 'documents-pool.json.gz', docs)
        unpack(folder / 'check-receipts.json.gz', receipts)
        modules = frozen_modules(source)
        candidate, fit, test, result, freeze = (read(docs / n) for n in ('candidate.json', 'fit-data.json', 'test-data.json', 'verdict.json', 'selection-freeze.json'))
        cfg = read(source / 'experiments/arithmetic_dse/configs/model_asap7_general_state_v2.json')
        admission = read(docs / 'test-admission.json'); consumption = read(docs / 'test-consumed.json')
        if (sha(docs / 'candidate.json') != freeze['candidate_sha256']
                or sha(docs / 'fit-data.json') != freeze['dataset_sha256']
                or sha(docs / 'selection-freeze.json') != admission['selection_freeze_sha256']
                or sha(docs / 'test-data.json') != consumption['dataset_sha256']
                or result != read(folder / 'verdict.json') or result['status'] != 'failed'
                or read(folder / 'publication.json')['published']):
            raise ValueError('S summary frozen identity differs')
        for name, h in admission['sources'].items():
            if sha(source / name) != h: raise ValueError('S archived producer differs')
        for name, h in read(docs / 'fit-byte-proof.json')['files'].items():
            if sha(docs / name) != h or sha(docs / 'repeat' / name) != h: raise ValueError('S repeated fit bytes differ')
        specs = {s['id']: s for s in modules['model_general_state_samples_v2'].specifications(cfg)}
        groups = {}; seen = set()
        for row in fit['rows'] + test['rows']:
            s = specs[row['source_group']]
            expected = {owner: modules['model_general_state_fit'].owner_features(s, row['period_ps'], owner) for owner in candidate['owners']}
            if (expected != row['owner_features'] or hashlib.sha256(modules['model_general_state_samples_v2'].source(s).encode()).hexdigest() != row['source_sha256']
                    or groups.setdefault(s['semantic_signature'], row['split']) != row['split'] or row['id'] in seen):
                raise ValueError('S fixed semantic features/grouping differ')
            seen.add(row['id'])
        if len(seen) != 432 or len(groups) != 24: raise ValueError('S summary coverage differs')
        for stage in ('synth', 'grt'):
            rows = [r for r in fit['rows'] if r['stage'] == stage]
            if modules['model_general_state_fit'].boundary(rows, cfg) != candidate['stages'][stage]['boundary_model']:
                raise ValueError('S original boundary formula differs')
            for owner in candidate['owners']:
                q = modules['model_general_state_test'].quality(candidate['stages'][stage]['area_models'][owner],
                    modules['model_general_state_fit'].owner_rows([r for r in rows if r['split'] == 'validation'], owner), cfg)
                if q != read(docs / 'validation.json')[stage]['selected_validation'][owner]: raise ValueError('S fixed validation differs')
        if modules['model_general_state_test'].verdict(candidate, test) != result: raise ValueError('S one-time fixed verdict differs')
        support = {e['id']: e for e in read(folder / 'check-paid-entries.json')}
        for p in receipts.rglob('*.command.json'):
            c = read(p); e = support.pop(c['budget_reservation_id'])
            if (c['exit_code'] or e['status'] != 'completed' or e['command'] != c['command']
                    or e['walltime_s'] != c['walltime_s']
                    or abs(e['CPU_time_s'] - modules['budget'].cpu_seconds(p.with_name(p.name.removesuffix('.command.json') + '.resources.txt'))) > 1e-8):
                raise ValueError('S evidence verification receipt differs')
        if support: raise ValueError('S support receipt coverage differs')
    if external:
        archive = read(folder / 'raw-archive.json'); path = Path(archive['path'])
        if sha(path / 'manifest.json') != archive['manifest_sha256']: raise ValueError('S raw archive identity differs')
        from .model_general_state_evidence import verify as raw_verify
        with redirect_stdout(io.StringIO()): raw_verify(path, external=True)
    print(json.dumps({'status': 'passed', 'external': external, 'stage_rows': 432, 'independent_status': 'failed',
        'published': [], 'PPA_calls': 0, 'full_D_ready': False}), flush=True)


def isolated(folder):
    with tempfile.TemporaryDirectory(prefix='S-summary-isolated-') as td:
        tmp = Path(td); local = tmp / 'evidence'; shutil.copytree(folder, local); source = tmp / 'source'
        unpack(local / 'source-pool.json.gz', source)
        code = '''import builtins,io,os,runpy,subprocess,sys
from pathlib import Path
source,folder=sys.argv[1:]
def guarded(original):
 def checked(path,*a,**kw):
  if isinstance(path,(str,bytes,os.PathLike)) and str(Path(path).resolve()).startswith('/home/zyrv/'):
   raise RuntimeError('original tree read forbidden')
  return original(path,*a,**kw)
 return checked
builtins.open=guarded(builtins.open);io.open=guarded(io.open)
def forbidden(*a,**kw):raise RuntimeError('replay subprocess forbidden')
subprocess.Popen=forbidden
sys.path.insert(0,source);sys.argv=['sealed','verify','--folder',folder]
runpy.run_module('experiments.arithmetic_dse.model_general_state_summary',run_name='__main__')
'''
        env = os.environ.copy(); env.update(PATH='', PYTHONDONTWRITEBYTECODE='1'); env.pop('PYTHONPATH', None)
        cmd = [sys.executable, '-B', '-c', code, str(source), str(local)]
        p = subprocess.run(cmd, cwd=tmp, env=env, capture_output=True, text=True)
        if p.returncode: raise ValueError('S summary isolated replay failed: ' + p.stderr[-2500:])
        for name in ('documents-pool.json.gz', 'verdict.json', 'publication.json'):
            path = local / name; original = path.read_bytes(); changed = bytearray(original); changed[len(changed) // 2] ^= 1; path.write_bytes(changed)
            p = subprocess.run(cmd, cwd=tmp, env=env, capture_output=True, text=True); path.write_bytes(original)
            if p.returncode == 0 or 'S summary identity mismatch' not in p.stderr: raise ValueError('S summary tamper accepted')
    print(json.dumps({'status': 'passed', 'original_tree_and_build_and_ledger_denied': True, 'PATH_empty': True,
        'replay_subprocess_denied': True, 'documents_verdict_publication_tamper_rejected': True, 'PPA_calls': 0}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('action', choices=('seal', 'verify', 'isolated'))
    parser.add_argument('--folder', type=Path, required=True); parser.add_argument('--archive', type=Path); parser.add_argument('--root', type=Path)
    parser.add_argument('--external', action='store_true'); args = parser.parse_args()
    if args.action == 'seal': seal(args.archive.resolve(), args.folder.resolve(), args.root.resolve())
    elif args.action == 'isolated': isolated(args.folder.resolve())
    else: verify(args.folder.resolve(), args.external)
