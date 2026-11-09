"""Accounted Verilator check of generic finite-bit fast sampling kernels."""
import argparse
import copy
import gzip
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.arithmetic_dse import model_fast_samples as samples
from experiments.arithmetic_dse.model_fast_preflight import read, sha, write


def verify(folder):
    data = read(folder / 'software/samples.json');log = (folder / 'simulate.log').read_text()
    if data['expected_marker'] not in log or '%Warning' in (folder / 'build.log').read_text():
        raise ValueError('sample RTL failed or emitted unchecked warnings')
    freezes = read(folder / 'source-freeze.json')
    if any(sha(ROOT / name) != digest for name, digest in freezes['files'].items()):
        raise ValueError('sampling producer changed during preflight')
    for c in data['cases']:
        if sha(folder / 'software' / (c['module'] + '.hex')) != c['vector_sha256']:
            raise ValueError('sample reference vectors changed')
    seed = dict(operation='mul', lhs_width=13, rhs_width=17, result_width=11)
    rejected = []
    for name, patch in [('unknown_operation', {'operation': 'div'}), ('overlap_known_bits', {'lhs_zero_hex': '1', 'lhs_one_hex': '1'}),
                        ('out_of_width_mask', {'lhs_zero_hex': '2000'}), ('invalid_width', {'lhs_width': 0}),
                        ('case_identity_as_semantics', {'case_id': 'MAC_32'}), ('carry_on_mul', {'carry': 'one'})]:
        bad = copy.deepcopy(seed);bad.update(patch)
        try: samples.source(bad, 'Guard')
        except ValueError: rejected.append(name)
        else: raise ValueError('invalid sampling semantics accepted: ' + name)
    proof = dict(version='arithmetic-fast-samples-proof-v1', status='passed',
        unique_kernels=len(data['cases']), required_shape_aliases=len(data['shape_aliases']),
        additional_parameter_contexts=sum(c['origin'] == 'independent_parameter_context' for c in data['cases']),
        arithmetic_comparisons=sum(c['rows'] for c in data['cases']),
        capture_and_valid_comparisons=True, reset_bubbles_and_invalid_capture_checked=True,
        rejections=rejected, source_role='software_preflight_only_not_training',
        physical_geometry_qualified=False, physical_admission_allowed=False, independent_physical_labels_read=False, PPA_calls=0)
    write(folder / 'proof.json', proof);print(json.dumps(proof), flush=True)


def package(folder, evidence):
    if evidence.exists(): raise ValueError('preserve sampling proof package')
    evidence.mkdir(parents=True)
    files = {'proof.json': folder / 'proof.json', 'samples.json': folder / 'software/samples.json',
             'source-freeze.json': folder / 'source-freeze.json', 'commands.json': folder / 'commands.json'}
    for p in (folder / 'software').iterdir(): files['software/' + p.name] = p
    for name in ('prepare.log', 'build.log', 'simulate.log', 'verify.log'): files['receipts/' + name] = folder / name
    for p in (Path(__file__), Path(samples.__file__)): files['source/' + str(p.relative_to(ROOT))] = p
    pool = {name: dict(sha256=sha(p), text=p.read_text()) for name, p in sorted(files.items())}
    (evidence / 'text-pool.json.gz').write_bytes(gzip.compress(json.dumps(pool, sort_keys=True, separators=(',', ':')).encode(), mtime=0))
    shutil.copy2(folder / 'proof.json', evidence / 'proof.json')
    (evidence / 'README.md').write_text('''# 近速度极限小算子采样源：软件前检

19个真实需求形状加4个额外参数上下文，验证非等宽、已知零／一位、低位截断和动态进位的同一生成器。23个核各96周期，Python任意精度参考与实际Verilator组合／捕获／valid检查通过；含复位、气泡、invalid时无条件捕获。没有执行物理采样／训练，未取得映射FF几何、原始路径／面积归属或级内负载资格。

text-pool保留生成器／检查源、实际RTL与向量、自检日志和命令；proof是软件范围收据，不能当成独立物理模型测试。新物理协议／容量／预算仍待准入，PPA0。父静态需求见step7_fast_preflight_v3。源码相同且安装Verilator后，可按mission主计划的当前命令重做软件检查；此包不含可执行文件或对象。
''')
    write(evidence / 'manifest.json', dict(version='arithmetic-fast-sample-software-evidence-v1',
        files={p.name: sha(p) for p in evidence.iterdir() if p.is_file()}))
    print(json.dumps(dict(status='sealed', bytes=sum(p.stat().st_size for p in evidence.iterdir()), PPA_calls=0)), flush=True)


def run(folder, requirements, evidence):
    from experiments.arithmetic_dse.budget import Ledger, POLICY, usage
    from experiments.arithmetic_dse.processes import run_command
    if not shutil.which('verilator'): raise ValueError('Verilator required')
    folder.mkdir(parents=True, exist_ok=False);ledger = Ledger();before = read(ledger.path)
    config = read(ROOT / 'experiments/arithmetic_dse/configs/model_fast_prototype_v1.json');current = usage(before['entries']);limits = read(POLICY)['resources']
    if (current['walltime_s'] + 1200 + config['later_work_reserved']['walltime_s'] > limits['max_global_walltime_h'] * 3600
            or current['CPU_time_s'] + 4800 + config['later_work_reserved']['CPU_time_s'] > limits['max_tool_CPU_time_h'] * 3600):
        raise ValueError('sampling software preflight and later work not funded')
    write(folder / 'source-freeze.json', dict(requirements_sha256=sha(requirements), files={
        str(p.relative_to(ROOT)): sha(p) for p in (Path(__file__), Path(samples.__file__))}))
    ctx = dict(target_platform='asap7', admission_id=folder.name, task_id='P1-sampling-software-preflight')
    env = os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4');commands = []
    with ledger.job(ctx):
        def execute(command, name, timeout):
            r = ledger.reserve(None, timeout, 4, 'fast_sampling_source_validation', command, folder / name, context=ctx)
            record = run_command(command, folder, name, timeout, env, 8192, cpu_limit_s=r['CPU_time_s']);ledger.finish(r, record)
            commands.append({**record, 'budget_reservation_id': r['id']});write(folder / 'commands.json', commands)
            if record['exit_code']: raise RuntimeError(name + ' failed: ' + record['log'])
            print(name + ': ' + Path(record['log']).read_text()[-900:], flush=True)
        software = folder / 'software'
        execute([sys.executable, '-B', '-m', 'experiments.arithmetic_dse.model_fast_samples', '--requirements', str(requirements), '--out', str(software)], 'prepare', 120)
        execute(['verilator', '--binary', '--timing', '--top-module', 'SampleTb', '--Mdir', str(folder / 'obj'), '-j', '4', str(software / 'kernels.sv'), str(software / 'testbench.sv')], 'build', 600)
        execute([str(folder / 'obj/VSampleTb')], 'simulate', 120)
        execute([sys.executable, '-B', str(Path(__file__)), 'verify', '--out', str(folder)], 'verify', 120)
        if evidence:
            execute([sys.executable, '-B', str(Path(__file__)), 'package', '--out', str(folder), '--evidence', str(evidence)], 'package', 120)
    after = read(ledger.path);write(folder / 'resource-increment.json', dict(entries=after['entries'][len(before['entries']):], usage=usage(after['entries']), PPA_calls=0))
    if evidence:
        write(evidence / 'publication-closure.json', dict(manifest_sha256=sha(evidence / 'manifest.json'),
            entries=after['entries'][len(before['entries']):], usage=usage(after['entries']), physical_calls_added=0))


if __name__ == '__main__':
    p = argparse.ArgumentParser();p.add_argument('action', choices=('run', 'verify', 'package'));p.add_argument('--out', type=Path, required=True);p.add_argument('--requirements', type=Path);p.add_argument('--evidence', type=Path);a = p.parse_args()
    if a.action == 'verify': verify(a.out.resolve())
    elif a.action == 'package':
        if not a.evidence: p.error('--evidence required')
        package(a.out.resolve(), a.evidence.resolve())
    elif not a.requirements: p.error('--requirements required')
    else: run(a.out.resolve(), a.requirements.resolve(), a.evidence.resolve() if a.evidence else None)
