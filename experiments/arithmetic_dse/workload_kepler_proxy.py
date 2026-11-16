#!/usr/bin/python3
"""Fail-closed verification adapter for separately admitted repair batches.

The ORFS before/after Verilog and Liberty files are read without modification.
Only the sufficient buffer/size graph proof is supported. A changed function,
connection, unsupported transformation or timeout aborts the original Tcl
call. Its entire runtime and memory remain in the parent physical leaf.
"""
import argparse
import hashlib
import json
from pathlib import Path
import signal
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from workload_buffer_equivalence import prove


def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(config):
    before=[];libraries=[];mode=None;log=None
    for line in Path(config).read_text().splitlines():
        if line=='input_paths:':mode='inputs';continue
        if line=='liberty_files:':mode='libraries';continue
        if line.startswith('log_file:'):
            log=Path(line.split(':',1)[1].strip());mode=None;continue
        if line.startswith(' ') and line.strip().startswith('- '):
            value=line.strip()[2:].strip()
            if mode=='inputs':before.append(Path(value))
            elif mode=='libraries':libraries.append(Path(value))
            else:raise ValueError('unsupported verifier configuration list')
    if len(before)!=2 or not libraries or log is None:raise ValueError('incomplete verifier configuration')
    log.parent.mkdir(parents=True,exist_ok=True)
    def timeout(signum,frame):raise TimeoutError('300 second structural proof limit')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(300)
    try:
        result=prove(*before,libraries)
        result.update(inputs_sha256={str(p):digest(p) for p in before+libraries+[Path(config)]},
            verifier_sha256=digest(__file__),prover_sha256=digest(Path(__file__).with_name('workload_buffer_equivalence.py')),
            verification_protocol='buffer-size-repair-proof-v1',physical_netlists_modified=False)
    except Exception as error:
        result=dict(status='not_proven',reason=str(error),verification_protocol='buffer-size-repair-proof-v1')
    finally:signal.alarm(0)
    content=json.dumps(result,indent=2)+'\n';log.write_text(content)
    log.with_suffix('.proof.json').write_text(content);print(content)
    return 0 if result['status']=='proven' else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,required=True);a=parser.parse_args()
    raise SystemExit(main(a.config))
