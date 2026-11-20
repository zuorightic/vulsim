#!/usr/bin/env python3
"""Exercise the public VUL entry, both cost models and unchanged cycle semantics."""
from pathlib import Path
import json
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'build/vulrtlgen'


def run(command, success=True):
    result = subprocess.run(list(map(str, command)), cwd=ROOT, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)
    if (result.returncode == 0) != success:
        raise AssertionError(str(command) + '\n' + result.stdout[-8000:])
    return result.stdout


with tempfile.TemporaryDirectory(prefix='vul-autopipe-entry-') as directory:
    base = Path(directory)
    sentinel = base / 'preserve'
    sentinel.mkdir()
    (sentinel / 'keep').write_text('existing output')
    ordinary = ROOT / 'example/prodcon/TopModule.vul'
    common = [TOOL, '-t', ordinary, '-o', sentinel, '-f']
    invalid = [
        ['--target-backend', 'asap7'],
        ['--candidate-profile', 'mac32'],
        ['--auto-pipeline'],
        ['--auto-pipeline', '--target-backend', 'unknown', '--target-period-ps', '950'],
        ['--auto-pipeline', '--target-backend', 'asap7', '--target-period-ps', 'nan'],
        ['--auto-pipeline', '--target-backend', 'asap7', '--target-period-ps', '-1'],
        ['--auto-pipeline', '--target-backend', 'asap7', '--target-period-ps', '950', '--autopipe-timeout', '0'],
        ['--auto-pipeline', '--target-backend', 'asap7', '--target-period-ps', '950', '--circt'],
        ['--auto-pipeline', '--target-backend', 'asap7', '--target-period-ps', '950', '--arithmetic-request', 'unused.json'],
        ['--auto-pipeline', '--target-backend', 'asap7', '--target-period-ps', '950', '--candidate-profile', 'unknown'],
        ['--auto-pipeline', '--target-backend', 'asap7', '--target-period-ps', '950', '--candidate-profile', ''],
        ['--auto-pipeline', '--target-backend', 'asap7', '--target-period-ps', '950', '--mul-block-widths', ''],
        ['--auto-pipeline', '--target-backend', 'asap7', '--target-period-ps', '950', '--add-limb-widths', ''],
        ['--auto-pipeline', '--target-backend', 'asap7', '--target-period-ps', '950', '--mul-block-widths', '0,16,16'],
        ['--auto-pipeline', '--target-backend', 'asap7', '--target-period-ps', '950', '--mul-block-widths', '0,256'],
        ['--auto-pipeline', '--target-backend', 'asap7', '--target-period-ps', '950', '--add-limb-widths', '0,4097'],
        ['--auto-pipeline', '--target-backend', 'asap7', '--target-period-ps', '950', '--mul-block-widths', '0,4,8,16,32'],
        ['--auto-pipeline', '--target-backend', 'asap7', '--target-period-ps', '950'],  # no PIPELINE
    ]
    for flags in invalid:
        run(common + flags, success=False)
        assert (sentinel / 'keep').read_text() == 'existing output'
    print('PASS auto-pipeline argument diagnostics preserve existing output', flush=True)

    example = ROOT / 'example/autopipe/mac32'
    plain = base / 'plain'
    run([TOOL, '-m', example / 'Main.utb', '-o', plain])
    assert not list(plain.rglob('*.autopipe'))
    assert 'AUTOPIPE MAC32 PASS' in run([plain / 'run.sh'])
    print('PASS original PIPELINE generation and cycle reference', flush=True)

    for platform, period in [('asap7', '950'), ('nangate45', '1500')]:
        out = base / platform
        run([TOOL, '-m', example / 'Main.utb', '-o', out,
             '--auto-pipeline', '--target-backend', platform, '--target-period-ps', period,
             '--candidate-profile', 'mac32'])
        reports = list(out.rglob('*.autopipe/result.json'))
        assert len(reports) == 1, reports
        report = json.loads(reports[0].read_text())
        assert report['platform'] == platform and report['L'] == 2
        assert report['VUL_boundary_registers_reused'] and report['additional_register_cycles'] == 0
        assert report['backend_calls'] == 0
        assert report['grammar']['mul_block_widths'] == [0, 4, 8, 16]
        assert report['grammar']['add_limb_widths'] == [0]
        assert 'AUTOPIPE MAC32 PASS' in run([out / 'run.sh'])
        print(f'PASS {platform}: model selection, unsigned arithmetic, valid, nonzero reset and latency', flush=True)

    # Two cores in one module must have distinct generated module names. The
    # extra core has no valid ports and no internal register stage (latency 1).
    case = base / 'multiple'
    case.mkdir()
    shutil.copyfile(example / 'header.uh', case / 'header.uh')
    top = (example / 'TopModule.vul').read_text().replace(
        '    QUERY(valid, bool);', '    QUERY(valid, bool);\n    QUERY(extra, Int<8>);')
    top += '\nPIPELINE(other, 1, IREG(x, Int<8>) { x=11; }, OREG(z, Int<8>)) { z=x+Int<8>(5); }\nQUERY(extra, Int<8>) { return z; }\n'
    (case / 'TopModule.vul').write_text(top)
    main = (example / 'Main.utb').read_text().replace(
        'QUERY(valid, bool);', 'QUERY(valid, bool);\nQUERY(extra, Int<8>);').replace(
        '            sim_nextcycle();', '            sim_nextcycle();\n            if (extra()!=Int<8>(16)) std::exit(4);')
    (case / 'Main.utb').write_text(main)
    out = base / 'multiple-out'
    run([TOOL, '-m', case / 'Main.utb', '-o', out, '--auto-pipeline',
         '--target-backend', 'asap7', '--target-period-ps', '950', '--candidate-profile', 'mac32'])
    assert len(list(out.rglob('*.autopipe/result.json'))) == 2
    assert 'AUTOPIPE MAC32 PASS' in run([out / 'run.sh'])
    print('PASS multiple embedded cores and latency-1 core without valid', flush=True)

    out = base / 'release'
    run([TOOL, '-t', ROOT / 'example/autopipe/mac32/TopModule.vul', '-o', out,
         '--auto-pipeline', '--target-backend', 'asap7', '--target-period-ps', '1200',
         '--candidate-profile', 'mac32', '-r'])
    assert not list(out.rglob('*.cpp'))
    assert len(list(out.rglob('*.autopipe/result.json'))) == 1
    run(['verilator', '--lint-only', '--top-module', 'TopModule_top', out / 'top.sv'])
    print('PASS release mode: selected RTL compiles and intermediate C++ is omitted', flush=True)
