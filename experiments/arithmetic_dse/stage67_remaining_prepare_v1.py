"""Software-only coverage probes for the remaining three combination classes.

Fresh validation sources use 16-bit factors, broad 64-bit accumulation and the
same compatible real state wrapper. No locked source, label or price chooses a
placement. Physical work requires separate prospective finite admission.
"""
import argparse
from pathlib import Path
from .model_fast_preflight import write,read,sha
from . import stage67_shared_fit_v1 as shared
from . import stage7_physical_prepare as original


def rows():
    result=[]
    for kind in ('shared','bypass','cross_stage_saved_value'):
        name='stage_'+kind+'_16';inputs=[dict(name='a',width=16,reset_hex='0'),dict(name='b',width=16,reset_hex='0')]
        outputs=[dict(name='y',width=64)];prefix='Int<32> p=Int<32>(a*b);'
        if kind=='shared':
            prefix+='Int<64> sp{};sp.at<40,9>()=p;';expr='Int<64>(p)+sp';outputs.append(dict(name='product',width=32));extra='product=p;'
        else:
            inputs.append(dict(name='c',width=64,reset_hex='0'));extra=''
            if kind=='bypass':
                inputs.append(dict(name='bypass_in',width=29,reset_hex='0'));outputs += [dict(name='product',width=32),dict(name='bypass_out',width=29)]
                expr='Int<64>(p)+c';extra='product=p;bypass_out=bypass_in;'
            else:prefix+='Int<64> q=Int<64>(p)+c;';expr='q+Int<64>(p)'
        decl='\n'.join(f'#pragma {direction}_port {p["name"]}\nInt<{p["width"]}> {p["name"]};' for direction,ps in [('input',inputs),('output',outputs)] for p in ps)
        source='#include <fixint.hpp>\n#include <arithmetic.hpp>\n'+decl+'\n#pragma input_port iv\nbool iv;\n#pragma output_port ov\nbool ov;\nvoid stage7_top(){'+prefix+'y='+expr+';'+extra+'}\n'
        result.append(dict(id=name,kind=kind,w=16,v=16,inputs=inputs,outputs=outputs,role='validation',cut='first',output_reset={p['name']:0 for p in outputs},source_text=source))
    return result


def prepare(out):
    if out.exists():raise ValueError('preserve remaining-class preparation')
    out.mkdir(parents=True);sources=rows()
    for r in sources:
        d=out/'sources'/r['id'];d.mkdir(parents=True);p=d/'source.cpp';p.write_text(r.pop('source_text'));r.update(source=str(p),source_sha256=sha(p));write(d/'request.json',r)
    write(out/'sources.json',dict(sources=sources));write(out/'protocol.json',dict(version='remaining-three-classes-software-v1',roles={r['id']:'validation' for r in sources},targets_ps=[500,1500,3000],
        cut_selection='structural first; no price feedback',purpose='detect frozen node/S/shared coverage before any further physical admission',
        source_prices_or_IDs_are_not_model_features=True,physical_admission_allowed=False,independent_tests_unlocked=False,full_D_ready=False))
    print('REMAINING_THREE_CLASSES_SOFTWARE_REGISTERED physical_calls=0',flush=True)


def export(out,tool):
    from regression.arithmetic_steps123 import execute
    for r in read(out/'sources.json')['sources']:
        d=out/'sources'/r['id'];execute(out/'receipts'/('remaining-export-'+r['id']),'export',[str(tool),str(shared.ROOT),str(d/'request.json'),str(shared.NODE),str(shared.BINDING),str(d/'native')],120)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','export'));p.add_argument('--out',type=Path,required=True);p.add_argument('--tool',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare(a.out.resolve())
    else:export(a.out.resolve(),a.tool.resolve())
