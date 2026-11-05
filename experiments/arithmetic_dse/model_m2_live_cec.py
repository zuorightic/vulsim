"""Structural CTS CEC inside an already charged backend process tree.

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


def check_result(log,equivalent):
    positive=bool(re.search(r'^Networks are equivalent(?: after structural hashing)?\.',log,re.M))
    negative=bool(re.search(r'^Networks are NOT EQUIVALENT',log,re.M))
    if re.search(r'Error:|Reading AIG.*failed|Wrong input|known file extension',log,re.I) or (positive,negative)!=(equivalent,not equivalent):
        raise ValueError('ABC did not return an explicit complete CEC conclusion')


def verify_proof(path,before,after):
    p=read(path);folder=Path(path).parent
    if p.get('version') not in ('m2-live-structural-cec-v1','m2-live-structural-cec-v2') or p.get('status')!='passed':raise ValueError('live proof not passed')
    if sha(before)!=p['before_sha256'] or sha(after)!=p['after_sha256']:raise ValueError('loaded live CTS pair changed')
    if sha(p['request_path'])!=p['request_sha256']:raise ValueError('changed live proof request')
    for name,h in p['artifacts'].items():
        if sha(folder/name)!=h:raise ValueError('changed live CEC artifact')
    for name,h in p['tools'].items():
        if sha(name)!=h:raise ValueError('changed live CEC tool')
    b=p['boundary']
    complete=[full_map(folder/(side+'.aig'),folder/(side+'.map'),read(folder/(side+'-flat.json'))['modules']['ModelBundle'],b['input'],b['output']) for side in ('gold','gate')]
    maps=[v[0] for v in complete]
    if maps[0]!=maps[1]:raise ValueError('changed live CEC boundaries')
    check_result((folder/'cec.log').read_text(),True)
    required={'top_output','register_D','register_CLK'}
    if any(v[1] for v in complete):required.add('constant_register_D')
    if set(p['negative_controls'])!=required:raise ValueError('missing live negative controls')
    for name in p['negative_controls']:check_result((folder/('negative-'+name+'.log')).read_text(),False)
    print('LIVE_CEC_EXACT_PAIR_VERIFIED',flush=True)


def prove(before, after, out, request):
    binding = read(request)
    out.mkdir(parents=True, exist_ok=False)
    result = {'version': 'm2-live-structural-cec-v2', 'status': 'running',
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
        if interfaces[0] != interfaces[1]: raise ValueError('changed full live CEC boundary/state model')
        counts=interfaces[0][2]; result['boundary']=counts
        complete=[full_map(out/(s+'.aig'),out/(s+'.map'),read(out/(s+'-flat.json'))['modules']['ModelBundle'],counts['input'],counts['output']) for s in ('gold','gate')]
        maps=[v[0] for v in complete]
        write(out/'complete-boundary.json',{'map':maps[0],'constant_outputs':{s:v[1] for s,v in zip(('gold','gate'),complete)}})
        if maps[0]!=maps[1]: raise ValueError('live CEC port order mismatch')
        execute([str(ABC), '-c', 'cec -n '+str(out/'gold.aig')+' '+str(out/'gate.aig')], 'cec')
        check_result((out/'cec.log').read_text(),True)
        controls={'top_output':lambda s:not s.startswith('cec_state_'),
                  'register_D':lambda s:s.startswith('cec_state_') and bytes.fromhex(s[10:]).endswith(b'\0D'),
                  'register_CLK':lambda s:s.startswith('cec_state_') and bytes.fromhex(s[10:]).endswith(b'\0CLK')}
        if complete[1][1]:
            constant_symbol=complete[1][1][0]['symbol']
            controls['constant_register_D']=lambda s:s==constant_symbol
        for name,predicate in controls.items():
            index=next(int(v[1]) for v in maps[1] if v[0]=='output' and predicate(v[3])); mutated=out/(name+'.aig')
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
