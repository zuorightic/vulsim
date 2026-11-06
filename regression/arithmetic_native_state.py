"""Native state layout audit; no PPA or independent timing/area labels read."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.budget import Ledger
from experiments.arithmetic_dse.model_m2_cec import leaf
from experiments.arithmetic_dse.model_collection import sha,write
from experiments.arithmetic_dse.case_generator import generate_manifest
from experiments.arithmetic_dse.whole_graph import reset_inputs,port_name
from experiments.arithmetic_dse.model_m2_native_coverage import CASES


def prepare(out):
    sources=ROOT/'build/step7-d-interface-20261105/public-nine-v1/generated'
    cases={c['id']:c for c in generate_manifest()['cases']}
    rows=[]
    for name in CASES:
        source=sources/name/'sim/top.logic.cpp.pipeline_core.cpp'
        dst=out/'sources'/(name+'.cpp');dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dst)
        text=dst.read_text();top=re.search(r'void (LogicSubModule_\w+)\(\)',text)[1]
        coverage=json.loads((ROOT/'experiments/arithmetic/evidence/step7_m2_native_integration_v1/public-nine/coverage.json').read_text())
        entry=next(c for c in coverage['cases'] if c['case']==name)
        values=reset_inputs(cases[name]);reset={'__vul_port_'+port_name(key):[format((value>>(64*i))&((1<<64)-1),'x') for i in range((cases[name]['inputs'][key]+63)//64)] for key,value in values.items()}
        reset['__vul_port_iv']=['0']
        rows.append({'name':name,'source':str(dst),'top':top,'N':entry['L']-1,
            'iv':'__vul_port_iv','ov':'__vul_port_ov','reset':reset,
            'public_VUL_source_sha256':entry['source_sha256'],'generated_source_sha256':sha(dst)})
    fixtures=[('two_mux','Int<8>a,b,c,d,y,z;bool sa,sb,iv,ov;',['a','b','c','d','sa','sb','iv'],['y','z','ov'],
        'y=sa?a:b;z=sb?c:d;',{'a':['3'],'b':['5'],'c':['7'],'d':['b'],'sa':['0'],'sb':['1'],'iv':['0']},1),
        ('padded65','Int<32>a,b;Int<65>y;bool iv,ov;',['a','b','iv'],['y','ov'],'y=a*b;',{'a':['80000035'],'b':['80000035'],'iv':['0']},2),
        ('shared','Int<16>a,b,c;Int<32>y;Int<33>z;bool iv,ov;',['a','b','c','iv'],['y','z','ov'],
        'Int<32> t=a*b;y=t;z=Int<33>(t)+Int<33>(c);',{'a':['8035'],'b':['8035'],'c':['8035'],'iv':['0']},2)]
    for name,decl,inputs,outputs,body,reset,n in fixtures:
        text='#include <fixint.hpp>\n'+decl+'\n'+''.join('#pragma input_port '+p+'\n' for p in inputs)+''.join('#pragma output_port '+p+'\n' for p in outputs)+'void top(){'+body+'}\n'
        dst=out/'sources'/(name+'.cpp');dst.write_text(text)
        rows.append({'name':name,'source':str(dst),'top':'top','N':n,'iv':'iv','ov':'ov','reset':reset})
    write(out/'cases.json',{'cases':rows,'PPA_calls':0})


def verify(out):
    data=json.loads((out/'native/queries.json').read_text());rows=data['rows']
    cases={c['name']:c for c in json.loads((out/'cases.json').read_text())['cases']}
    if len(rows)!=12 or len(data['rejections'])!=5 or data['PPA_calls']:
        raise ValueError('native state audit incomplete')
    stats=[]
    for row in rows:
        slots=row['slots'];f=row['features'];data_slots=[s for s in slots if not s['valid'] and s['variable_bits']]
        control=[s for s in slots if s['valid']]
        for s in slots:
            mask=sum(int(v,16)<<(64*i) for i,v in enumerate(s['variable_mask_hex']))
            if mask.bit_count()!=s['variable_bits'] or mask>>s['declared_width']:
                raise ValueError('native state mask/variable count mismatch')
            if s['enable_stage']!=(-1 if s['valid'] else s['stage']-1):
                raise ValueError('native per-stage valid enable mismatch')
        bits=sum(s['variable_bits'] for s in data_slots);valid=sum(s['variable_bits'] for s in control)
        reset_ones=sum((sum(int(v,16)<<(64*i) for i,v in enumerate(s['reset_hex'])) & sum(int(v,16)<<(64*i) for i,v in enumerate(s['variable_mask_hex']))).bit_count() for s in data_slots)
        expected=dict(state_bits=bits+valid,state_signals=len(data_slots)+len(control),data_bits=bits,data_signals=len(data_slots),valid_bits=valid,
            valid_signals=len(control),enable_domains=len({s['enable_stage'] for s in data_slots}),reset_one_bits=reset_ones,
            max_declared_width=max(s['declared_width'] for s in data_slots),min_variable_width=min(s['variable_bits'] for s in data_slots),sdc_period_ps=1500)
        if f!=expected or not row['materialized_checked'] or row['qualified_price']:
            raise ValueError('native typed state features or qualification differs')
        internal=[s for s in slots if not s['external_capture']]
        if len(internal)!=row['internal_registers'] or sum(s['declared_width'] for s in internal)!=row['internal_register_bits']:
            raise ValueError('actual materialized internal register accounting differs')
        # Cross-check each native slot against the emitted always_ff RTL name,
        # full reset literal and actual valid guard, independently of features.
        rtl=(out/'native'/(row['case']+'.sv')).read_text()
        reset_region=rtl.split('if (!rstn) begin',1)[1].split('end else begin',1)[0]
        internal_data=[s for s in internal if not s['valid']]
        for s in internal:
            reset=sum(int(v,16)<<(64*i) for i,v in enumerate(s['reset_hex']))
            actual=re.search(r'\b'+re.escape(s['name'])+r'\s*<=\s*(\d+)\x27h([0-9a-fA-F]+)',reset_region)
            if actual is None or int(actual[1])!=s['declared_width'] or int(actual[2],16)!=reset:
                raise ValueError('native slot differs from actual emitted reset')
        body=rtl.split('end else begin',1)[1]
        if row['valid_input_rtl_name']!=cases[row['case']]['iv']:
            if not re.search(r'assign\s+'+re.escape(row['valid_input_rtl_name'])+r'\s*=\s*'+re.escape(cases[row['case']]['iv'])+r'\s*;',rtl):
                raise ValueError('native primary valid alias is not the actual input port')
        valid_by_stage={s['stage']:s['name'] for s in internal if s['valid']}
        for s in internal:
            previous=row['valid_input_rtl_name'] if s['stage']==1 else valid_by_stage[s['stage']-1]
            if s['valid']:
                if not re.search(r'\b'+re.escape(s['name'])+r'\s*<=\s*'+re.escape(previous)+r'\s*;',body):
                    raise ValueError('native valid chain differs from emitted RTL')
            elif not re.search(r'if\s*\(\s*'+re.escape(previous)+r'\s*\)\s*begin\s*'+re.escape(s['name'])+r'\s*<=',body):
                raise ValueError('native data enable differs from emitted RTL')
        if not internal_data or not any(s['enable_stage']==0 for s in internal_data):
            raise ValueError('audit failed to expose actual first-stage input valid')
        stats.append({'case':row['case'],'features':f,'first_enable_is_input_valid':True,
            'state_model_v1_topology_qualified':False,'needs_native_protocol_successor':True})
    padded=next(row for row in rows if row['case']=='padded65')
    if not any(s['declared_width']==65 and s['variable_bits']==64 for s in padded['slots']):
        raise ValueError('native 65/64 padding not exercised')
    write(out/'audit.json',{'status':'passed','cases':stats,'PPA_calls':0,'guard_rejections':len(data['rejections']),
        'projected_materialized_reset_and_RTL_accounting':True,'state_model_v1_used_as_qualified_native_price':False,
        'limitation':'native first enable is input valid and subsequent enables follow stage, unlike registered rotated v1 banks; external input/service state has separate ownership'})
    print(json.dumps({'status':'passed','real_public_VUL_cores':9,'extra_fixtures':3,'guard_rejections':5,'PPA_calls':0,
        'qualified_native_state_price':False,'successor_qualification_required':True}),flush=True)


def run(out,build):
    out.mkdir(parents=True,exist_ok=False);prepare(out)
    ledger=Ledger();ctx={'target_platform':'asap7','admission_id':out.name,'task_id':'native-state-layout-and-domain-audit'}
    with ledger.job(ctx):
        for command,name,timeout in [(['cmake','-S',str(ROOT/'rtlzz'),'-B',str(build),'-DCMAKE_BUILD_TYPE=Release'],'configure',300),
            (['cmake','--build',str(build),'--target','arithmetic-native-state-test','-j4'],'build',1800),
            ([str(build/'testv2/arithmetic-native-state-test'),str(ROOT),str(out/'cases.json'),str(out/'native')],'native',900),
            ([sys.executable,'-B',str(Path(__file__).resolve()),'verify','--out',str(out)],'verify',300)]:
            leaf(command,out,name,timeout,ledger,ctx)
            print((out/(name+'.log')).read_text()[-1800:],flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('run','verify'))
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--build',type=Path,default=ROOT/'build/step4-rtlzz')
    args=parser.parse_args()
    if args.action=='run':run(args.out.resolve(),args.build.resolve())
    else:verify(args.out.resolve())


if __name__=='__main__':main()
