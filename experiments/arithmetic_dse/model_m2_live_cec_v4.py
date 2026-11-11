"""Structural CTS CEC with exact AIG indices for vector constant outputs.

No nested resource reservation: Yosys/ABC time, CPU and RSS belong to the
enclosing grt leaf and its whole-job lease. Unknown results fail the CTS call.
"""
import argparse
import json
from pathlib import Path
import subprocess
import time
import re

from .model_collection import sha, write
from .model_m2_cec import YOSYS, ABC, quote, read, cut_boundary, invert_aig_output
from .model_m2_aig import full_map
from .model_m2_state import compare_interfaces


def negative_targets(complete):
    rows,constants=complete
    predicates={'top_output':lambda s:not s.startswith('cec_state_'),
        'register_D':lambda s:s.startswith('cec_state_') and bytes.fromhex(s[10:]).endswith(b'\0D'),
        'register_CLK':lambda s:s.startswith('cec_state_') and bytes.fromhex(s[10:]).endswith(b'\0CLK')}
    targets={}
    for name,predicate in predicates.items():
        found=[int(v[1]) for v in rows if v[0]=='output' and predicate(v[3])]
        if not found:raise ValueError('missing actual required CEC output class '+name)
        targets[name]=found[0]
    # full_map has already matched each constant's bit-level symbol/index to
    # the complete AIG boundary. A vector symbol is never a scalar port name.
    for constant in constants:
        row=next(v for v in rows if v[0]=='output' and int(v[1])==constant['index'])
        if row[3].startswith('cec_state_'):
            if not bytes.fromhex(row[3][10:]).endswith(b'\0D'):raise ValueError('unexpected constant sequential timing pin')
            name='constant_register_D'
        else:name='constant_top_output'
        targets.setdefault(name,constant['index'])
    return targets


def check_result(log,equivalent):
    positive=bool(re.search(r'^Networks are equivalent(?: after structural hashing)?\.',log,re.M))
    negative=bool(re.search(r'^Networks are NOT EQUIVALENT',log,re.M))
    if re.search(r'Error:|Reading AIG.*failed|Wrong input|known file extension',log,re.I) or (positive,negative)!=(equivalent,not equivalent):
        raise ValueError('ABC did not return an explicit complete CEC conclusion')


def verify_proof(path,before,after):
    p=read(path);folder=Path(path).parent
    if p.get('version')!='m2-live-structural-cec-v4' or p.get('status')!='passed':raise ValueError('live proof not passed')
    if sha(before)!=p['before_sha256'] or sha(after)!=p['after_sha256']:raise ValueError('loaded live CTS pair changed')
    if sha(p['request_path'])!=p['request_sha256']:raise ValueError('changed live proof request')
    for name,h in p['artifacts'].items():
        if sha(folder/name)!=h:raise ValueError('changed live CEC artifact')
    for name,h in p['tools'].items():
        if sha(name)!=h:raise ValueError('changed live CEC tool')
    interfaces=[]
    for side in ('gold','gate'):
        interfaces.append(cut_boundary(read(folder/(side+'-hier.json')),'ModelBundle'))
    correspondence=compare_interfaces(*interfaces)
    if correspondence!=read(folder/'state-correspondence.json'):raise ValueError('changed state correspondence proof')
    b=p['boundary']
    complete=[full_map(folder/(side+'.aig'),folder/(side+'.map'),read(folder/(side+'-flat.json'))['modules']['ModelBundle'],b['input'],b['output']) for side in ('gold','gate')]
    maps=[v[0] for v in complete]
    if maps[0]!=maps[1]:raise ValueError('changed live CEC boundaries')
    check_result((folder/'cec.log').read_text(),True)
    required=negative_targets(complete[1])
    if set(p['negative_controls'])!=set(required) or p['negative_output_indices']!=required:raise ValueError('missing/wrong exact-index live negative controls')
    for name in p['negative_controls']:check_result((folder/('negative-'+name+'.log')).read_text(),False)
    print('LIVE_CEC_EXACT_PAIR_VERIFIED',flush=True)


def prove(before, after, out, request):
    binding = read(request)
    out.mkdir(parents=True, exist_ok=False)
    result = {'version': 'm2-live-structural-cec-v4', 'status': 'running',
              'before_sha256': sha(before), 'after_sha256': sha(after), 'request_sha256': sha(request),
              'request_path':str(request),'tools':{str(p):sha(p) for p in (YOSYS,ABC)},
              'accounting': 'included in enclosing grt command; no nested charge', 'commands': []}
    def execute(command, stem):
        start = time.monotonic()
        with (out/(stem+'.log')).open('x') as stream:
            p = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, timeout=900)
        result['commands'].append({'command': command, 'exit_code': p.returncode, 'walltime_s': time.monotonic()-start})
        if p.returncode: raise RuntimeError('CEC command failed: '+stem)
    try:
        libcmd = []
        for lib in binding['libraries']:
            if sha(lib['path']) != lib['sha256']: raise ValueError('changed live CEC Liberty')
            libcmd.append('read_liberty -ignore_miss_func '+quote(lib['path']))
        interfaces = []
        for side, path in (('gold', before), ('gate', after)):
            script = out/(side+'-read.ys')
            script.write_text('\n'.join(libcmd+['read_verilog '+quote(path), 'hierarchy -check -top ModelBundle', 'write_json '+quote(out/(side+'-hier.json'))])+'\n')
            execute([str(YOSYS), '-T', '-s', str(script)], side+'-read')
            design = read(out/(side+'-hier.json')); b, s, c = cut_boundary(design, 'ModelBundle'); interfaces.append((b,s,c))
            write(out/(side+'-cut.json'), design)
            script = out/(side+'-aig.ys')
            script.write_text('\n'.join(['read_json '+quote(out/(side+'-cut.json')), 'hierarchy -check -top ModelBundle',
                'flatten -noscopeinfo', 'proc', 'opt', 'techmap', 'opt', 'check -assert', 'aigmap', 'check -assert',
                'write_json '+quote(out/(side+'-flat.json')), 'write_aiger -symbols -map '+str(out/(side+'.map'))+' '+quote(out/(side+'.aig'))])+'\n')
            execute([str(YOSYS), '-T', '-s', str(script)], side+'-aig')
            flat = read(out/(side+'-flat.json'))['modules']['ModelBundle']
            if any(v['type'] not in ('$_AND_', '$_NOT_') for v in flat['cells'].values()): raise ValueError('noncombinational live CEC')
            with (out/(side+'.aig')).open('rb') as stream: header=stream.readline().decode().split()
            if header[0]!='aig' or list(map(int,header[2:5]))!=[c['input'],0,c['output']]: raise ValueError('incomplete live AIG')
        correspondence=compare_interfaces(interfaces[0],interfaces[1])
        write(out/'state-correspondence.json',correspondence)
        counts=interfaces[0][2]; result['boundary']=counts
        complete=[full_map(out/(s+'.aig'),out/(s+'.map'),read(out/(s+'-flat.json'))['modules']['ModelBundle'],counts['input'],counts['output']) for s in ('gold','gate')]
        maps=[v[0] for v in complete]
        write(out/'complete-boundary.json',{'map':maps[0],'constant_outputs':{s:v[1] for s,v in zip(('gold','gate'),complete)}})
        if maps[0]!=maps[1]: raise ValueError('live CEC port order mismatch')
        execute([str(ABC), '-c', 'cec -n '+str(out/'gold.aig')+' '+str(out/'gate.aig')], 'cec')
        check_result((out/'cec.log').read_text(),True)
        controls=negative_targets(complete[1]);result['negative_output_indices']=controls
        for name,index in controls.items():
            mutated=out/(name+'.aig')
            invert_aig_output(out/'gate.aig',mutated,index)
            execute([str(ABC),'-c','cec -n '+str(out/'gold.aig')+' '+str(mutated)],'negative-'+name)
            check_result((out/('negative-'+name+'.log')).read_text(),False)
        result['negative_controls']=list(controls);result['status']='passed'
    except Exception as error:
        result.update(status='failed',reason=str(error));raise
    finally:
        result['artifacts']={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='proof.json'}
        write(out/'proof.json',result)
    print('LIVE_STRUCTURAL_CEC_PASSED full boundary and negative controls',flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('before','after','out','request'):ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args();prove(a.before,a.after,a.out,a.request)


if __name__=='__main__':main()
