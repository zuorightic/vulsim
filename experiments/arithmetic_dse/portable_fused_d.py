"""Rebuild and verify the frozen D consumer on another checkout or machine.

The original delivery entry keeps its exact-binary check. This separate entry
admits a local build only after numerical accounting and emitted-RTL checks.
It uses the unchanged node/S/G functions and C++ selector for every real query.
"""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import math
from pathlib import Path
import shutil
import subprocess
import tempfile

from .model_fast_preflight import read, write, sha

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / 'experiments/arithmetic/models/asap7_fused_D_prototype_v1/bundle.json'
FIXTURES = ROOT / 'experiments/arithmetic/examples/fused_d'
RECEIPT = 'portable-verification.json'
VERSION = 'portable-fused-D-build-v1'


def identities():
    """Preserve the frozen delivery's model and consumer-source identities."""
    bundle = read(BUNDLE)
    if (bundle['output_scope'] != 'prototype-no-reset-timing-v1'
            or bundle['full_D_ready'] or bundle['reset_timing_checked']):
        raise ValueError('unsupported frozen D scope')
    deps = {}
    for name, entry in bundle['dependencies'].items():
        path = (BUNDLE.parent / entry['path']).resolve()
        if sha(path) != entry['sha256']:
            raise ValueError('frozen D dependency changed: ' + name)
        deps[name] = path
    for name, digest in bundle['consumer_sources'].items():
        if sha(ROOT / name) != digest:
            raise ValueError('frozen D consumer source changed: ' + name)
    return bundle, deps


def input_snapshot(deps):
    """Content identities, independent of checkout/build directory names.

    Include build inputs as well as the Python accounting oracle and runtime
    configuration. A source change requires new verification, not an exemption
    from the receipt. Mutable ledgers, documentation and physical PPA are absent.
    """
    paths = {BUNDLE, *deps.values(), ROOT / 'rtlzz/CMakeLists.txt',
             ROOT / 'regression/arithmetic_fused_d.py',
             ROOT / 'regression/arithmetic_function_d.py',
             ROOT / 'regression/portable_fused_d.py',
             ROOT / 'experiments/arithmetic_dse/configs/fixed_op_width_v1.json',
             ROOT / 'experiments/arithmetic_dse/configs/platforms/asap7.json'}
    for directory in ('rtlzz/src', 'rtlzz/main', 'vullib'):
        paths.update(p for p in (ROOT / directory).rglob('*')
                     if p.is_file() and p.suffix in ('.cpp', '.hpp', '.h', '.inc'))
    paths.update((ROOT / 'experiments/arithmetic_dse').glob('*.py'))
    paths.update(p for p in FIXTURES.rglob('*')
                 if p.is_file() and p.suffix in ('.cpp', '.json'))
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}


def execute(command, log, timeout):
    print('Running ' + str(command[0]) + '; log: ' + str(log), flush=True)
    with log.open('w') as stream:
        subprocess.run([str(x) for x in command], cwd=ROOT, stdout=stream,
                       stderr=subprocess.STDOUT, check=True, timeout=timeout)


def source_document(request):
    document = deepcopy(read(request))
    if document['version'] != 'D-source-metadata-v1':
        raise ValueError('unsupported source request schema')
    source = document['source']
    path = Path(source['source'])
    if not path.is_absolute():
        path = request.resolve().parent / path
    if sha(path) != source['generated_source_sha256']:
        raise ValueError('C++ source identity differs from request')
    source['source'] = str(path.resolve())
    return document


def invoke(binary, deps, request, period, latency, out, assignment_limit=1000000, timeout=300):
    if not math.isfinite(period) or period <= 0 or not 2 <= latency <= 16:
        raise ValueError('positive finite T and L=2..16 required')
    if not 1 <= assignment_limit <= 1000000:
        raise ValueError('assignment limit must be 1..1000000')
    if not math.isfinite(timeout) or not 0 < timeout <= 3600:
        raise ValueError('software timeout must be positive and at most 3600 seconds')
    if out.exists():
        raise ValueError('preserve existing D output: ' + str(out))
    document = source_document(request)
    # Only normalize the source filename. Reset, valid and arithmetic semantics
    # remain the caller's source request, checked by the same C++ compiler.
    with tempfile.TemporaryDirectory(prefix='portable-fused-D-') as tmp:
        normalized = Path(tmp) / 'source-request.json'
        write(normalized, document)
        command = [str(binary), '--root', str(ROOT), '--source-request', str(normalized),
                   '--node-model', str(deps['operators']),
                   '--state-binding', str(deps['S_binding']),
                   '--composition-policy', str(deps['composition']),
                   '--G-model', str(deps['G_reduction']), '--period-ps', str(period),
                   '--latency', str(latency), '--output-scope', 'prototype-no-reset-timing-v1',
                   '--assignment-limit', str(assignment_limit), '--out', str(out)]
        # Keep coverage refusals and diagnostic reports exactly as produced by
        # C++; this entry does not select from a partially covered candidate set.
        result = subprocess.run(command, cwd=ROOT, timeout=timeout)
    if result.returncode:
        raise ValueError('D refused or failed; inspect ' + str(out / 'selection.json'))
    report = read(out / 'selection.json')
    if (not report['coverage_complete'] or not report['structural_enumeration_complete']
            or not report['prototype_D_selection'] or report['full_D_ready']
            or report['reset_timing_checked']):
        raise ValueError('D result scope or coverage differs')
    if sha(out / 'D.sv') != report['artifact']['rtl_sha256']:
        raise ValueError('emitted RTL identity differs')
    return report, document


def prepare(build, jobs):
    bundle, deps = identities()
    if not 1 <= jobs <= 4:
        raise ValueError('prepare permits 1..4 compiler jobs')
    for name in ('cmake', 'iverilog', 'vvp'):
        if not shutil.which(name):
            raise ValueError('required tool missing: ' + name)
    snapshot = input_snapshot(deps)
    # A fresh directory prevents accidentally certifying the original local
    # binary or stale object files. Failed attempts remain available for review.
    build.mkdir(parents=True, exist_ok=False)
    execute(['cmake', '-S', ROOT / 'rtlzz', '-B', build, '-DCMAKE_BUILD_TYPE=Release'],
            build / 'configure.log', 60)
    execute(['cmake', '--build', build, '--target', 'rtlzz-fused-d', '-j', str(jobs)],
            build / 'build.log', 480)
    binary = build / 'rtlzz-fused-d'
    expectations = read(FIXTURES / 'expected.json')
    if expectations['role'] != 'software_acceptance_only_never_online_prices':
        raise ValueError('invalid acceptance fixture role')
    from regression.arithmetic_fused_d import audit
    from regression.portable_fused_d import rtl_check
    checks = []
    cases = []
    for fixture in expectations['cases']:
        out = build / 'verification' / fixture['id']
        report, document = invoke(binary, deps, FIXTURES / fixture['source_request'],
                                  fixture['target_ps'], fixture['L'], out)
        if (report['selected_view'] != fixture['selected_view']
                or report['selection_status'] != fixture['status']):
            raise ValueError('rebuild selection differs: ' + fixture['id'])
        selected = next(row for row in report['candidates']
                        if row['view'] == report['selected_view'])
        guarded = max(c['decision_required_period_ps']
                      for s in selected['estimate']['stages'] for c in s['captures'])
        values = dict(area_um2=report['selected_area_um2'],
                      violation_ps=report['selected_timing_violation_ps'],
                      guarded_data_period_ps=guarded)
        for name, value in values.items():
            if not math.isclose(value, fixture[name], rel_tol=1e-8, abs_tol=1e-6):
                raise ValueError('rebuild numeric result differs: ' + fixture['id'] + '/' + name)
        checks.append(dict(id=fixture['id'],
                           oracle=audit(report, document['source'], bundle, BUNDLE.parent),
                           selection_sha256=sha(out / 'selection.json'),
                           rtl_sha256=sha(out / 'D.sv'), **values))
        cases.append((out, report))
    rtl = rtl_check(cases, build / 'verification/simulation')
    if input_snapshot(deps) != snapshot:
        raise ValueError('source/model inputs changed during verification')
    receipt = dict(version=VERSION, status='passed',
                   created_utc=datetime.now(timezone.utc).isoformat(),
                   binary='rtlzz-fused-d', binary_sha256=sha(binary),
                   frozen_delivery_binary_sha256=bundle['consumer_binary_sha256'],
                   frozen_bundle_sha256=sha(BUNDLE), inputs=snapshot,
                   numerical_checks=checks, rtl=rtl,
                   physical_PPA_calls=0, full_D_ready=False,
                   reset_timing_checked=False)
    write(build / RECEIPT, receipt)
    print('PORTABLE_D_PREPARED cases=' + str(len(checks))
          + ' receipt=' + str(build / RECEIPT), flush=True)


def verified_build(build):
    _, deps = identities()
    receipt = read(build / RECEIPT)
    if receipt['version'] != VERSION or receipt['status'] != 'passed':
        raise ValueError('local build has no successful verification receipt')
    binary = build / 'rtlzz-fused-d'
    if sha(binary) != receipt['binary_sha256']:
        raise ValueError('local verified executable changed; prepare a new build')
    current = input_snapshot(deps)
    if current != receipt['inputs']:
        names = sorted(k for k in set(current) | set(receipt['inputs'])
                       if current.get(k) != receipt['inputs'].get(k))
        raise ValueError('verified inputs changed; prepare a new build: ' + ', '.join(names[:8]))
    if sha(BUNDLE) != receipt['frozen_bundle_sha256']:
        raise ValueError('verified bundle changed')
    return binary, deps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest='action', required=True)
    p = actions.add_parser('prepare', help='fresh build, numerical oracle and short RTL check')
    p.add_argument('--build-dir', type=Path, default=ROOT / 'build/portable-fused-d')
    p.add_argument('--jobs', type=int, default=4)
    p = actions.add_parser('run', help='query real functions and emit selected D RTL')
    p.add_argument('--build-dir', type=Path, default=ROOT / 'build/portable-fused-d')
    p.add_argument('--source-request', type=Path, required=True)
    p.add_argument('--period-ps', type=float, required=True)
    p.add_argument('--latency', type=int, required=True)
    p.add_argument('--assignment-limit', type=int, default=1000000)
    p.add_argument('--timeout-s', type=float, default=300,
                   help='software enumeration/selection timeout, at most 3600 seconds')
    p.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        build = args.build_dir.resolve()
        if args.action == 'prepare':
            prepare(build, args.jobs)
        else:
            binary, deps = verified_build(build)
            out = args.out.resolve()
            report, _ = invoke(binary, deps, args.source_request.resolve(), args.period_ps,
                               args.latency, out, args.assignment_limit, args.timeout_s)
            write(out / 'invocation.json', dict(
                version=VERSION, bundle_sha256=sha(BUNDLE),
                local_build_receipt_sha256=sha(build / RECEIPT),
                consumer_binary_sha256=sha(binary),
                original_source_request_sha256=sha(args.source_request),
                target_period_ps=args.period_ps, L=args.latency,
                selection_status=report['selection_status'], candidate_PPA_calls=0,
                full_D_ready=False, reset_timing_checked=False))
            print('D_RTL ' + str(out / 'D.sv'), flush=True)
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        parser.exit(2, 'portable D: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
