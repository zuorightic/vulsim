"""Adapt a VUL PIPELINE to the frozen selector and return its core for embedding."""
import argparse
import fcntl
import re
from pathlib import Path
from types import SimpleNamespace

from .compiler import build, verified_build
from .generate import generate
from .resources import ROOT, read, write, sha
from .candidate_grammar import resolve


def embedded_core(selection, request):
    """Keep VUL's launch/capture registers; namespace every selected core module."""
    row = selection['selected_candidate']
    artifact = row['artifact']
    source = Path(selection['rtl']).read_text()
    modules = list(re.finditer(r'(?m)^[ \t]*(?:\(\*[^\n]*\*\)[ \t]*)?module\s+([A-Za-z_]\w*)\b[\s\S]*?\bendmodule\b', source))
    names = [m[1] for m in modules]
    if names.count('WorkloadCore') != 1 or names.count('Workload') != 1 or len(set(names)) != len(names):
        raise ValueError('unexpected native workload module layout')
    prefix = request['top'] + '__autopipe'
    if not re.fullmatch(r'[A-Za-z_]\w*', prefix):
        raise ValueError('invalid VUL pipeline module name')
    rename = {name: prefix + '__' + name for name in names if name != 'Workload'}
    definitions = '\n\n'.join(m[0] for m in modules if m[1] != 'Workload')
    pattern = r'\b(?:' + '|'.join(re.escape(n) for n in sorted(rename, key=len, reverse=True)) + r')\b'
    definitions = re.sub(pattern, lambda m: rename[m[0]], definitions) + '\n'
    bindings = request['bindings']
    connections = []
    resets = {}
    if request['L'] > 1:
        connections.extend(['.clk(clk)', '.rstn(rstn)'])
    for port in artifact['ports']:
        name = port['name']
        if name not in bindings:
            raise ValueError('selected core has an unbound VUL port: ' + name)
        connections.append(f'.{name}({bindings[name]})')
        if not port['input']:
            value = int(port['reset_hex'], 16)
            resets[name] = [format((value >> shift) & ((1 << 64) - 1), 'x')
                            for shift in range(0, port['width'], 64)]
    iv, ov = request['iv'], request['ov']
    if iv:
        connections.extend([f'.{iv}({bindings[iv]})', f'.{ov}({bindings[ov]})'])
        resets[ov] = ['0']
    else:
        connections.extend([".__autopipe_iv(1'b1)", '.__autopipe_ov()'])
    instance = rename['WorkloadCore'] + ' core(' + ','.join(connections) + ');\n'
    return definitions, instance, resets


def select(request_file):
    request_file = Path(request_file).resolve()
    request = read(request_file)
    if request['schema'] != 'vul-autopipe-request-v1':
        raise ValueError('unsupported VUL auto-pipeline request')
    grammar = resolve(profile=request.get('candidate_profile'),
        mul_block_widths=request.get('mul_block_widths'), add_limb_widths=request.get('add_limb_widths'))
    output = request_file.parent
    # Serialize the initial compiler build across concurrent VUL module workers.
    build_dir = ROOT / 'build/autopipe'
    build_dir.mkdir(parents=True, exist_ok=True)
    with (build_dir / '.vul-build.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            verified_build(build_dir)
        except (OSError, ValueError, KeyError):
            build(build_dir, jobs=4)
    source = Path(request['source_file']).read_text()
    reset = dict(request['reset'])
    iv, ov = request['iv'], request['ov']
    if not iv:
        iv, ov = '__autopipe_iv', '__autopipe_ov'
        source = ('#pragma input_port ' + iv + '\nbool ' + iv + ';\n'
                  '#pragma output_port ' + ov + '\nbool ' + ov + ';\n') + source
        reset[iv] = ['0']
    native_source = output / 'source.cpp'
    native_source.write_text(source)
    source_request = output / 'source-request.json'
    write(source_request, dict(version='D-source-metadata-v1', source=dict(
        source=str(native_source), source_label=request['source_file'], top=request['top'],
        iv=iv, ov=ov, reset=reset, generated_source_sha256=sha(native_source))))
    selection = generate(SimpleNamespace(
        workload=None, source_request=source_request, platform=request['platform'],
        period_ps=float(request['period_ps']), latency=request['L'], method='D',
        build_dir=build_dir, out=output / 'search', timeout_s=request['timeout_s'],
        candidate_limit=256, check=False, candidate_profile=grammar['profile'],
        mul_block_widths=request.get('mul_block_widths'), add_limb_widths=request.get('add_limb_widths')))
    definitions, instance, resets = embedded_core(selection, request)
    (output / 'selected-core.sv').write_text(definitions)
    (output / 'instance.sv').write_text(instance)
    write(output / 'result.json', dict(
        schema='vul-autopipe-result-v1', platform=request['platform'], L=request['L'],
        T_clk_ps=request['period_ps'], selection_status=selection['selection_status'],
        summary=(f"{request['platform']} {selection['selection_status']}: predicted period "
                 f"{selection['prediction']['critical_required_ps']:.3f} ps, area "
                 f"{selection['prediction']['total_area_um2']:.3f} um^2; report {output / 'result.json'}"),
        selection=str(output / 'search/selection.json'),
        prediction=selection['prediction'], output_reset_values=resets,
        prediction_scope='PIPELINE kernel with boundary registers; excludes other VUL logic',
        VUL_boundary_registers_reused=True, additional_register_cycles=0,
        grammar=selection['search_grammar'],
        qualification=selection['qualification'], full_D_ready=selection['full_D_ready'],
        backend_calls=0, R1_R5_enabled=False))
    if request.get('release', False):
        for path in output.rglob('*.cpp'):
            path.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    args = parser.parse_args()
    select(args.request)


if __name__ == '__main__':
    main()
