"""Retain the full N56 CEC, binding its top and clock pins to Workload."""
import argparse
import inspect
from pathlib import Path
from . import model_m2_live_cec_v3 as inherited
from .nangate45_cec import clock_symbol


def adapted(function,clock=False):
    source=inspect.getsource(function)
    assert 'ModelBundle' in source
    source=source.replace('ModelBundle','Workload')
    if clock:
        old="s.startswith('cec_state_') and bytes.fromhex(s[10:]).endswith(b'\\0CLK')"
        assert source.count(old)==1
        source=source.replace(old,'clock_symbol(s,interfaces,binding)')
    namespace=dict(function.__globals__);namespace['clock_symbol']=clock_symbol
    exec(compile(source,__file__,'exec'),namespace)
    return namespace[function.__name__]


prove=adapted(inherited.prove,clock=True)
verify_proof=adapted(inherited.verify_proof)


def main():
    p=argparse.ArgumentParser()
    for name in ('before','after','out','request'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();prove(a.before,a.after,a.out,a.request)


if __name__=='__main__':main()
