"""Same complete CTS CEC, negative clock control from actual Liberty pins.

The inherited ASAP7 helper spells its clock negative control 'CLK'. Nangate45
spells that pin 'CK'. All state pins are still exposed on both sides, and the
same full AIG equivalence plus D/clock/top-output negative proofs are required.
"""
import inspect
from pathlib import Path
from . import model_m2_live_cec_v3 as parent


def clock_symbol(symbol,interfaces,binding):
    if not symbol.startswith('cec_state_'):return False
    instance,pin=bytes.fromhex(symbol[10:]).decode().split('\0')
    state=interfaces[1][1][instance]
    return pin in binding['sequential_clock_pins'][state['type']]


def prove(before,after,out,request):
    text=inspect.getsource(parent.prove).replace(
        "s.startswith('cec_state_') and bytes.fromhex(s[10:]).endswith(b'\\0CLK')",
        'clock_symbol(s,interfaces,binding)')
    if text==inspect.getsource(parent.prove):raise ValueError('inherited clock predicate changed')
    ns=dict(parent.prove.__globals__);ns['clock_symbol']=clock_symbol
    exec(compile(text,__file__,'exec'),ns)
    ns['prove'](before,after,out,request)


verify_proof=parent.verify_proof


def main():
    import argparse
    p=argparse.ArgumentParser()
    for name in ('before','after','out','request'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();prove(a.before,a.after,a.out,a.request)


if __name__=='__main__':main()
