"""Build the frozen native exporter and stage its immutable input configuration."""
from pathlib import Path
import shutil
import subprocess

from .resources import ROOT, MODELS, read, write, sha, verify_models


def compiler_inputs():
    files = [ROOT / 'rtlzz/CMakeLists.txt']
    for directory in ['rtlzz/src', 'rtlzz/main', 'vullib']:
        files.extend(p for p in (ROOT / directory).rglob('*')
                     if p.is_file() and p.suffix in {'.cpp', '.hpp', '.h', '.inc'})
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(files)}


def native_root(build):
    """Stage old exporter resource paths inside the ignored build directory.

    This preserves the frozen C++ exporter and its submodule identity. The
    checkout needs only vullib/models; no research directory is read.
    """
    root = Path(build) / 'native-root'
    root.mkdir(parents=True, exist_ok=True)
    headers = root / 'vullib'
    if headers.is_symlink() and headers.resolve() != (ROOT / 'vullib').resolve():
        headers.unlink()
    if not headers.exists():
        headers.symlink_to(ROOT / 'vullib', target_is_directory=True)
    config = root / 'experiments/arithmetic_dse/configs'
    (config / 'platforms').mkdir(parents=True, exist_ok=True)
    for source, destination in [(MODELS / 'profiles/asap7.json', config / 'platforms/asap7.json'),
                                (MODELS / 'fixed_op_width_v1.json', config / 'fixed_op_width_v1.json')]:
        shutil.copyfile(source, destination)
    return root


def build(directory, jobs=4):
    verify_models()
    directory = Path(directory).resolve()
    if not 1 <= jobs <= 32:
        raise ValueError('build jobs must be between 1 and 32')
    for executable in ['cmake', 'clang++-18', 'llvm-config-18']:
        if not shutil.which(executable):
            raise ValueError('required tool missing: ' + executable)
    if not (ROOT / 'rtlzz/CMakeLists.txt').is_file():
        raise ValueError('initialize RTLzz: git submodule update --init --recursive')
    directory.mkdir(parents=True, exist_ok=True)
    commands = [
        ['cmake', '-S', str(ROOT / 'rtlzz'), '-B', str(directory), '-DCMAKE_BUILD_TYPE=Release'],
        ['cmake', '--build', str(directory), '--target', 'rtlzz-workload', '-j', str(jobs)],
    ]
    for stem, command in zip(['configure', 'build'], commands):
        print('Compiling: ' + ' '.join(command), flush=True)
        with (directory / (stem + '.log')).open('w') as log:
            subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT, timeout=900)
    binary = directory / 'rtlzz-workload'
    write(directory / 'autopipe-build.json', dict(schema='autopipe-v10-build-v1',
        binary_sha256=sha(binary), inputs=compiler_inputs(), model_manifest_sha256=sha(MODELS / 'manifest.json')))
    native_root(directory)
    print('Compiler ready: ' + str(binary), flush=True)
    return binary


def verified_build(directory):
    verify_models()
    directory = Path(directory).resolve()
    receipt = read(directory / 'autopipe-build.json')
    binary = directory / 'rtlzz-workload'
    if receipt['schema'] != 'autopipe-v10-build-v1' or sha(binary) != receipt['binary_sha256']:
        raise ValueError('compiler differs from its build receipt; rebuild')
    if compiler_inputs() != receipt['inputs']:
        raise ValueError('compiler sources or headers changed; run the build command again')
    if sha(MODELS / 'manifest.json') != receipt['model_manifest_sha256']:
        raise ValueError('model resource manifest changed; rebuild')
    return binary, native_root(directory)
