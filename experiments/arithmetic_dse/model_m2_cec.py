"""Versioned structural CEC for exact saved CTS pairs; all tool leaves charged."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil

from .budget import Ledger
from .model_collection import sha, write
from .processes import run_command

ROOT = Path(__file__).resolve().parents[2]
YOSYS = Path('/home/zyrv/OpenROAD-flow-scripts/tools/install/yosys/bin/yosys')
ABC = YOSYS.with_name('yosys-abc')


def read(path):
    return json.loads(Path(path).read_text())


def quote(path):
    return '"' + str(path).replace('\\', '\\\\').replace('"', '\\"') + '"'


def leaf(command, out, stem, timeout, ledger, context):
    reservation = ledger.reserve(None, timeout, 4, 'm2_structural_CEC', command, out/stem, context=context)
    env = os.environ.copy()
    env.update(OMP_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4', YOSYS_MAX_THREADS='4', PYTHONDONTWRITEBYTECODE='1')
    record = run_command(command, out, stem, timeout, env, 8192, cpu_limit_s=reservation['CPU_time_s'])
    ledger.finish(reservation, record)
    record['budget_reservation_id'] = reservation['id']
    write(out/(stem+'.command.json'), record)
    if record['exit_code']:
        raise RuntimeError(f'{stem} failed; see {record["log"]}')
    return record


def sequential_model(module):
    return any(re.match(r'\$_?(?:dff|adff|sdff|dffe|dlatch|sr|ff)', c['type'], re.I)
               for c in module.get('cells', {}).values())


def cut_boundary(design, top):
    """Expose *every* sequential pin; same named FF is a state correspondence.

    The sequential cell model must be byte-identical on both sides (checked by
    the caller). No internal combinational point is assumed equivalent.
    """
    modules = design['modules']
    m = modules[top]
    boundary = {}
    for name, port in m['ports'].items():
        if port['direction'] not in ('input', 'output'):
            raise ValueError('inout boundary unsupported')
        boundary['top:'+name] = {'direction': port['direction'], 'width': len(port['bits'])}
    seq = {}
    for name, cell in list(m['cells'].items()):
        model = modules.get(cell['type'])
        if model is None:
            raise ValueError('missing cell model: '+cell['type'])
        if not sequential_model(model):
            continue
        seq[name] = {'type': cell['type'], 'parameters': cell.get('parameters', {}), 'model': model, 'pins': {}}
        for pin, bits in cell['connections'].items():
            direction = model['ports'][pin]['direction']
            if direction not in ('input', 'output') or len(bits) != len(model['ports'][pin]['bits']):
                raise ValueError('unsupported sequential pin')
            # This encoding cannot collide with a Verilog instance/pin separator.
            portname = 'cec_state_' + (name+'\0'+pin).encode().hex()
            if portname in m['ports']:
                raise ValueError('boundary port collision')
            cutdir = 'input' if direction == 'output' else 'output'
            m['ports'][portname] = {'direction': cutdir, 'bits': bits}
            boundary['state:'+name+':'+pin] = {'direction': cutdir, 'width': len(bits)}
            seq[name]['pins'][pin] = {'direction': direction, 'width': len(bits)}
        del m['cells'][name]
    if not seq:
        raise ValueError('empty sequential boundary')
    # Use exactly the same ordered port vector for the two AIGs, including
    # unused primary inputs. Internal net names never supply assumptions.
    m['ports'] = dict(sorted(m['ports'].items()))
    counts = {d: sum(p['width'] for p in boundary.values() if p['direction'] == d) for d in ('input', 'output')}
    return boundary, seq, counts


def aig_map(path, inputs, outputs):
    lines = [line.split() for line in Path(path).read_text().splitlines()]
    expected = {'input': inputs, 'output': outputs}
    if any(len(v) != 4 or v[0] not in expected for v in lines):
        raise ValueError('unexpected AIG map entry')
    for kind, count in expected.items():
        selected = [v for v in lines if v[0] == kind]
        if [int(v[1]) for v in selected] != list(range(count)):
            raise ValueError('incomplete AIG map')
    if len({(v[0], v[2], v[3]) for v in lines}) != len(lines):
        raise ValueError('duplicate AIG map port')
    return lines


def check_result(log, equivalent):
    positive = bool(re.search(r'Networks are equivalent\.', log))
    negative = bool(re.search(r'Networks are NOT EQUIVALENT', log))
    if re.search(r'Error:|Reading AIG.*failed|Wrong input|known file extension', log, re.I) or (positive, negative) != (equivalent, not equivalent):
        raise ValueError('ABC did not return the required explicit CEC conclusion')


def invert_aig_output(source, destination, index):
    raw = Path(source).read_bytes()
    header, rest = raw.split(b'\n', 1)
    values = header.split()
    if values[0] != b'aig' or int(values[3]) != 0 or not 0 <= index < int(values[4]):
        raise ValueError('mutation requires a combinational AIG output')
    lines = rest.split(b'\n', int(values[4]))
    lines[index] = str(int(lines[index]) ^ 1).encode()
    Path(destination).write_bytes(header+b'\n'+b'\n'.join(lines))


def verify_proof(path, before, after):
    """Consume a distinct ABC proof schema, never a fabricated Kepler log."""
    path = Path(path); p = read(path); folder = path.parent
    if p.get('version') != 'm2-structural-cec-v1' or p.get('status') != 'passed':
        raise ValueError('structural proof not passed')
    if sha(before) != p['gold_sha256'] or sha(after) != p['gate_sha256']:
        raise ValueError('CTS netlists differ from proven pair')
    if sha(Path(p['source'])/'manifest.json') != p['source_manifest_sha256']:
        raise ValueError('changed CEC source manifest')
    if sha(folder/'producer.py') != p['producer_sha256']:
        raise ValueError('changed CEC producer snapshot')
    for name, h in p['artifacts'].items():
        if sha(folder/name) != h:
            raise ValueError('changed CEC artifact: '+name)
    for name, h in p['tools'].items():
        if sha(name) != h:
            raise ValueError('changed CEC tool')
    for lib in p['libraries']:
        if sha(lib['path']) != lib['sha256']:
            raise ValueError('changed CEC library')
    b = p['boundary']
    if aig_map(folder/'gold.map', b['input'], b['output']) != aig_map(folder/'gate.map', b['input'], b['output']):
        raise ValueError('CEC port order mismatch')
    check_result((folder/'cec.log').read_text(), True)
    if set(p.get('negative_controls', [])) != {'top_output', 'register_D', 'register_CLK'}:
        raise ValueError('missing negative controls')
    for name in p['negative_controls']:
        check_result((folder/('negative-'+name+'.log')).read_text(), False)
    entries = {e['id']: e for e in read(Ledger().path)['entries']}
    for command in p['commands']:
        entry = entries[command['budget_reservation_id']]
        if (entry['status'] != 'completed' or entry['command'] != command['command']
                or command['exit_code'] or command['cleanup']['remaining_live_pids']):
            raise ValueError('unsettled or failed CEC leaf')
    print('STRUCTURAL_CEC_VERIFIED complete boundaries, negative controls, exact netlists', flush=True)
    return p


def pilot(source, out, expected_inputs, expected_outputs, timeout):
    if re.search(r'[^a-zA-Z0-9_./-]', str(out)):
        raise ValueError('unsupported tool output path')
    out.mkdir(parents=True, exist_ok=False)
    shutil.copy2(__file__, out/'producer.py')
    old = read(source/'manifest.json')
    context = {'target_platform': 'asap7', 'admission_id': out.name, 'task_id': 'structural-cec'}
    ledger = Ledger()
    result = {'version': 'm2-structural-cec-v1', 'status': 'running', 'source': str(source),
              'source_manifest_sha256': sha(source/'manifest.json'), 'producer_sha256': sha(__file__),
              'tools': {str(p): sha(p) for p in (YOSYS, ABC)}, 'libraries': old['libraries'], 'commands': []}
    write(out/'manifest.json', result)
    with ledger.job(context):
        try:
            libcmd = []
            for lib in old['libraries']:
                if sha(lib['path']) != lib['sha256']:
                    raise ValueError('changed Liberty')
                # Some libraries contain unused ICG cells without a Boolean
                # output function. Skip those definitions, then require every
                # instantiated cell to resolve with hierarchy -check and the
                # final AND/NOT-only whitelist below.
                libcmd.append('read_liberty -ignore_miss_func '+quote(lib['path']))
            boundaries, sequences, counts = [], [], []
            for side, name in (('gold', '4_before_rsz_lec.v'), ('gate', '4_after_rsz_lec.v')):
                path = source/'results/asap7/arithmetic_probe/base'/name
                if old['evidence_sha256'].get(str(path.relative_to(source))) != sha(path):
                    raise ValueError('changed saved netlist')
                result[side+'_sha256'] = sha(path)
                script = out/(side+'-read.ys')
                script.write_text('\n'.join(libcmd+['read_verilog '+quote(path), 'hierarchy -check -top ModelBundle',
                                                      'write_json '+quote(out/(side+'-hier.json'))])+'\n')
                result['commands'].append(leaf([str(YOSYS), '-T', '-s', str(script)], out, side+'-read', 120, ledger, context))
                design = read(out/(side+'-hier.json'))
                b, s, c = cut_boundary(design, 'ModelBundle')
                boundaries.append(b); sequences.append(s); counts.append(c)
                write(out/(side+'-cut.json'), design)
                if c != {'input': expected_inputs, 'output': expected_outputs}:
                    raise ValueError('complete boundary count differs from original LEC')
                script = out/(side+'-aig.ys')
                script.write_text('\n'.join(['read_json '+quote(out/(side+'-cut.json')),
                    'hierarchy -check -top ModelBundle', 'flatten -noscopeinfo', 'proc', 'opt', 'techmap', 'opt',
                    'check -assert', 'aigmap', 'check -assert',
                    'write_json '+quote(out/(side+'-flat.json')),
                    'write_aiger -symbols -map '+str(out/(side+'.map'))+' '+quote(out/(side+'.aig'))])+'\n')
                result['commands'].append(leaf([str(YOSYS), '-T', '-s', str(script)], out, side+'-aig', 120, ledger, context))
                flat = read(out/(side+'-flat.json'))['modules']['ModelBundle']
                if any(not c['type'].startswith(('$_AND_', '$_NOT_')) for c in flat['cells'].values()):
                    raise ValueError('noncombinational or unknown cell in AIG')
                with (out/(side+'.aig')).open('rb') as stream:
                    header = stream.readline().decode('ascii').split()
                if header[0] != 'aig' or list(map(int, header[2:5])) != [expected_inputs, 0, expected_outputs]:
                    raise ValueError('AIG boundary coverage mismatch')
            if boundaries[0] != boundaries[1] or sequences[0] != sequences[1]:
                raise ValueError('state models or full interfaces differ')
            write(out/'boundary.json', {'pins': boundaries[0], 'sequential_cells': sequences[0], 'counts': counts[0]})
            result['boundary'] = counts[0]
            maps = [aig_map(out/(s+'.map'), expected_inputs, expected_outputs) for s in ('gold', 'gate')]
            if maps[0] != maps[1]:
                raise ValueError('AIG port order mismatch')
            result['commands'].append(leaf([str(ABC), '-c', 'cec -n '+str(out/'gold.aig')+' '+str(out/'gate.aig')],
                                           out, 'cec', timeout, ledger, context))
            check_result((out/'cec.log').read_text(), True)
            controls = {'top_output': lambda s: not s.startswith('cec_state_'),
                        'register_D': lambda s: s.startswith('cec_state_') and bytes.fromhex(s[10:]).endswith(b'\0D'),
                        'register_CLK': lambda s: s.startswith('cec_state_') and bytes.fromhex(s[10:]).endswith(b'\0CLK')}
            result['negative_controls'] = []
            for name, predicate in controls.items():
                index = next(int(v[1]) for v in maps[1] if v[0] == 'output' and predicate(v[3]))
                mutated = out/('negative-'+name+'.aig')
                invert_aig_output(out/'gate.aig', mutated, index)
                result['commands'].append(leaf([str(ABC), '-c', 'cec -n '+str(out/'gold.aig')+' '+str(mutated)],
                                               out, 'negative-'+name, 120, ledger, context))
                check_result((out/('negative-'+name+'.log')).read_text(), False)
                result['negative_controls'].append(name)
            result['status'] = 'passed'
        except Exception as error:
            result.update(status='failed', reason=str(error))
        finally:
            result['artifacts'] = {p.name: sha(p) for p in out.iterdir() if p.is_file() and p.name != 'manifest.json'}
            write(out/'manifest.json', result)
    print(json.dumps({'status': result['status'], 'reason': result.get('reason'), 'out': str(out)}), flush=True)
    if result['status'] != 'passed':
        raise RuntimeError(result['reason'])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--inputs', type=int, required=True)
    ap.add_argument('--outputs', type=int, required=True)
    ap.add_argument('--timeout', type=int, default=900)
    args = ap.parse_args()
    pilot(args.source.resolve(), args.out.resolve(), args.inputs, args.outputs, args.timeout)


if __name__ == '__main__':
    main()
