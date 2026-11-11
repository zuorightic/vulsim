"""Prospective shared-function successor: numerical features, no identity prices.

Fresh compatible service/native/capture shells. Source identity partitions roles
and balances training only; it is never an inference feature or support key.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import inspect
import math
from pathlib import Path
import random
import re

from .model_fast_preflight import read,write,sha
from .operator_condition_model import query
from . import stage7_physical_prepare as prep

ROOT=Path(__file__).resolve().parents[2]
NODE=ROOT/'experiments/arithmetic/models/asap7_conditional_operators_v1/operators.json'
BINDING=Path('/home/zyrv/vulsim-artifacts/conditional-boundary-20261110-v3/binding-candidate.json')
PARENT=Path('/home/zyrv/vulsim-artifacts/stage67-state-shared-20261111-v1/derivation-v5/candidate.json')
FEATURES={
 'shared_clock':['one','total_FF_bits','sqrt_FF_bits','predicted_functional_area_um2','clock_pressure'],
 'shared_physical':['one','predicted_functional_area_um2'],
 'root_repair':['one','input_data_bits','total_FF_bits','reset_one_bits','input_ports','clock_pressure']}


def specs():
    # Widths, fanout and functional footprints vary independently as far as
    # the frozen node/S domains permit. All numeric T of a source keep role.
    definitions=[
      ('train_p16',16,'products',1,'early',0,'train'),
      ('train_p24',24,'products',4,'early',1,'train'),
      ('train_p32',32,'products',4,'early',2,'train'),
      ('train_r16',16,'reduce',3,'first',1,'train'),
      ('train_r24',24,'reduce',2,'first',2,'train'),
      ('train_r32',32,'reduce',2,'first',0,'train'),
      ('train_c16',16,'chain',1,'first',2,'train'),
      ('train_c32',32,'chain',1,'early',1,'train'),
      ('validation_p20',20,'products',3,'early',1,'validation'),
      ('validation_r28',28,'reduce',2,'first',2,'validation'),
      ('validation_c24',24,'chain',1,'first',1,'validation'),
      ('locked_p28',28,'products',3,'early',2,'locked_test'),
      ('locked_r20',20,'reduce',3,'first',1,'locked_test')]
    rows=[]
    for ident,w,kind,count,cut,pattern,role in definitions:
        ports=2 if count==1 else 4
        inputs=[dict(name=n,width=w) for n in ('a','b','c','d')[:ports]]
        if kind=='chain':inputs=[dict(name='a',width=w),dict(name='b',width=w),dict(name='c',width=64),dict(name='d',width=32 if w==16 else 0)]
        inputs=[p for p in inputs if p['width']]
        for i,p in enumerate(inputs):
            value=0 if not pattern else ((0x1209 if pattern==1 else 0xa531) << (i%3))&((1<<p['width'])-1)
            p['reset_hex']=format(value,'x')
        pairs=[('a','b'),('b','c'),('c','d'),('d','a')][:count]
        if kind=='chain':pairs=[('a','b')]
        products=''.join(f'Int<{2*w}> p{i}=Int<{2*w}>({a}*{b});' for i,(a,b) in enumerate(pairs))
        if kind=='products':
            outputs=[dict(name='y'+str(i),width=2*w) for i in range(count)]
            body=products+''.join(f'y{i}=p{i};' for i in range(count))
        else:
            outputs=[dict(name='y',width=64)]
            if kind=='reduce':
                body=products+'Int<64> q=Int<64>(p0)+Int<64>(p1);'
                body+=('y=q+Int<64>(p2);' if count==3 else 'y=q;')
            else:
                body=products+'Int<64> q=Int<64>(p0)+c;'+('y=q+Int<64>(d);' if w==16 else 'y=q;')
        declarations='\n'.join(f'#pragma {direction}_port {p["name"]}\nInt<{p["width"]}> {p["name"]};' for direction,ports_ in [('input',inputs),('output',outputs)] for p in ports_)
        source='#include <fixint.hpp>\n#include <arithmetic.hpp>\n'+declarations+'\n#pragma input_port iv\nbool iv;\n#pragma output_port ov\nbool ov;\nvoid stage7_top(){'+body+'}\n'
        row=dict(id=ident,w=w,kind=kind,count=count,cut=cut,role=role,reset_pattern=pattern,inputs=inputs,outputs=outputs,pairs=pairs,source_text=source)
        row['output_reset']=reference(row,{p['name']:int(p['reset_hex'],16) for p in inputs});rows.append(row)
    return rows


def reference(r,x):
    products=[x[a]*x[b] for a,b in r['pairs']]
    if r['kind']=='products':return {'y'+str(i):p for i,p in enumerate(products)}
    return dict(y=(sum(products) if r['kind']=='reduce' else products[0]+x['c']+x.get('d',0))&((1<<64)-1))


def init(out):
    if out.exists():raise ValueError('preserve preparation attempts')
    out.mkdir(parents=True);rows=specs()
    for r in rows:
        d=out/'sources'/r['id'];d.mkdir(parents=True);p=d/'source.cpp';p.write_text(r.pop('source_text'));r.update(source=str(p),source_sha256=sha(p));write(d/'request.json',r)
    demand=read(Path('/home/zyrv/vulsim-artifacts/stage67-shared-fit-20261111-v1/demand-v1/proof.json'))
    fs=[]
    for t in demand['targets']:
        for v in t['views']:
            d=v['diagnostics'];o=d['owner_features']
            fs.append(dict(total_FF_bits=d['total_FF_bits'],predicted_functional_area_um2=v['predicted_functional_area_um2'],input_data_bits=o['input_service']['data_bits'],reset_one_bits=sum(x['reset_one_bits'] for x in o.values())))
    write(out/'demand-summary.json',dict(numerical_ranges={k:[min(x[k] for x in fs),max(x[k] for x in fs)] for k in fs[0]},covered=81,refused=51,
        gap='predicted functional footprint beyond previous 913.268761um2 maximum',physical_labels_used=False,inventory_is_not_support_whitelist=True))
    write(out/'sources.json',dict(sources=rows))
    write(out/'protocol.json',dict(version='shared-compatible-function-fit-v1',dependencies={k:dict(path=str(p),sha256=sha(p)) for k,p in [('node',NODE),('S_binding',BINDING),('parent',PARENT)]},
      features=FEATURES,feature_definitions=dict(clock_pressure='1500 / numerical target_ps',sqrt_FF_bits='sqrt(total semantic FF bits)',
      predicted_functional_area_um2='sum of frozen S three exclusive state areas and frozen node combination areas',input_ports='actual variable input data signals',reset_one_bits='sum of S projected variable reset-one bits'),
      model='nonnegative linear, one common coefficient vector per exclusive owner; source-balanced train-only least squares',
      forbidden_features=['source ID','shape ID','candidate ID','placement ID','exact-T indicator','per-source intercept','measured functional area'],
      roles={r['id']:r['role'] for r in rows},targets_ps=[500,1500,3000],exact_1000ps='reserved, no measurement or parameter selection',
      train_requests=[dict(source=r['id'],target_ps=t) for r in rows if r['role']=='train' for t in (500,1500,3000)],
      validation_requests=[dict(source=r['id'],target_ps=t) for r in rows if r['role']=='validation' for t in (500,1500,3000)],
      collection_gate='node and S query coverage; cycle/reference/state/reset check before admission; exact finite admissions separate',
      initial_batch_sources=[r['id'] for r in rows if r['role']=='train'],
      capacity=dict(train_synth=24,train_grt=24,validation_synth=9,validation_grt=9,support=600,threads=4,parallel_jobs=4,memory_per_job_MiB=8192),
      independent_test_unlock=False,old_validation='six consumed placement measurements diagnostics only; no tuning',
      support='per registered numerical feature range observed in eligible train; numerical T in [500,3000]; no identity whitelist',
      gates=dict(owner_area_median_max=.15,owner_area_P95_max=.35,total_area_median_max=.15,total_area_P95_max=.35,false_feasible_max=0),
      freeze_before_validation=['features','parameters','support','reserve','implementation'],old_S_and_node_unchanged=True,G_delay_ps=0,reserve_ps=50,full_D_ready=False))
    print('SHARED_PROTOCOL_REGISTERED train=8 validation=3 locked=2 T=500,1500,3000',flush=True)


def export(out,tool):
    from regression.arithmetic_steps123 import execute
    deps=read(out/'protocol.json')['dependencies']
    for r in read(out/'sources.json')['sources']:
        # Locked sources are registered now, not compiled/measured or inspected.
        if r['role']=='locked_test':continue
        d=out/'sources'/r['id']
        execute(out/'receipts'/(out.name+'-export-'+r['id']),'export',[str(tool),str(ROOT),str(d/'request.json'),deps['node']['path'],deps['S_binding']['path'],str(d/'native')],120)


def wrapper(r,v,d):
    top,text=prep.wrapper(r,v,d)
    # Native reset constants already come from the actual compiler. Public
    # input/output state must use those same numeric reset values too.
    launch='iv<=0;'+''.join(p['name']+'<=0;' for p in r['inputs'])
    newlaunch='iv<=0;'+''.join(f'{p["name"]}<={p["width"]}\'h{p["reset_hex"]};' for p in r['inputs'])
    capture='ov<=0;'+''.join(p['name']+'<=0;' for p in r['outputs'])
    newcapture='ov<=0;'+''.join(f'{p["name"]}<={p["width"]}\'h{r["output_reset"][p["name"]]:x};' for p in r['outputs'])
    if text.count(launch)!=1 or text.count(capture)!=1:raise ValueError('reset adapter callsite drift')
    return top,text.replace(launch,newlaunch).replace(capture,newcapture)


def features(diagnostics,functional,t):
    o=diagnostics['owner_features'];ff=diagnostics['total_FF_bits']
    return dict(one=1.,total_FF_bits=ff,sqrt_FF_bits=math.sqrt(ff),predicted_functional_area_um2=functional,
      input_data_bits=o['input_service']['data_bits'],reset_one_bits=sum(x['reset_one_bits'] for x in o.values()),
      input_ports=o['input_service']['data_signals'],clock_pressure=1500/t)


def products(out):
    model=read(NODE);rows=[];modules=[];tb=['module SharedTb;reg clk=0;integer j;'];drive=[];check=[];loads=[]
    for r in read(out/'sources.json')['sources']:
        if r['role']=='locked_test':continue
        d=out/'sources'/r['id']/'native';e=read(d/'export.json');v=e['variants'][0];i=len(rows);top,rtl=wrapper(r,v,d)
        rtlp=d/'measurement.sv';rtlp.write_text(rtl);modules.append(rtl)
        contract=prep.endpoint_contract(r,v,e)
        for p in contract['input_service']:p['reset']=int(next(x for x in r['inputs'] if x['name']==p['port'])['reset_hex'],16)
        contract['external_capture']['reset']=r['output_reset'];write(d/'endpoints.json',contract)
        predictions=[]
        for target in v['targets']:
            prices=[dict(node=q['trace']['node'],**query(model,q['descriptor'])) for q in target['queries']]
            if any(p['status']!='covered' for p in prices):raise ValueError('node coverage preflight '+r['id']+' '+repr(prices))
            s=target['real_S_candidate']
            if not s['covered']:raise ValueError('S coverage preflight '+r['id']+' '+s['reason'])
            functional=sum(s['owners_um2'][n] for n in ('input_service','native_state','external_state'))+sum(p['comb_area_um2'] for p in prices)
            predictions.append(dict(target_ps=target['target_ps'],features=features(target['diagnostics'],functional,target['target_ps']),node_prices=prices,
                state_areas={n:s['owners_um2'][n] for n in ('input_service','native_state','external_state')}))
        write(d/'features.json',dict(source=r['id'],role=r['role'],predictions=predictions))
        rows.append(dict(source=r['id'],role=r['role'],placement=v['id'],rtl=str(rtlp),rtl_sha256=sha(rtlp),endpoint_contract=str(d/'endpoints.json'),endpoint_sha256=sha(d/'endpoints.json'),native=str(d)))
        ni=sum(p['width'] for p in r['inputs']);no=sum(p['width'] for p in r['outputs'])+1;bits=ni+len(r['inputs'])+3+no
        rng=random.Random(int(hashlib.sha256(r['id'].encode()).hexdigest()[:16],16));held={p['name']:int(p['reset_hex'],16) for p in r['inputs']};iv=0;core=dict(r['output_reset']);cv=0;vectors=[]
        for cycle in range(192):
            rst=int(cycle not in (0,1,71,72,131));ivd=int(cycle%7 not in (1,2,5));ivw=int(cycle%11!=4)
            x={p['name']:rng.getrandbits(p['width']) for p in r['inputs']};wen={p['name']:int((cycle+k)%9!=3) for k,p in enumerate(r['inputs'])}
            expected=core if rst else r['output_reset'];ov=cv if rst else 0;word=0
            for value,width in [(rst,1),(ivd,1),(ivw,1)]+[(x[p['name']],p['width']) for p in r['inputs']]+[(wen[p['name']],1) for p in r['inputs']]+[(expected[p['name']],p['width']) for p in r['outputs']]+[(ov,1)]:word=(word<<width)|value
            vectors.append(format(word,'x'))
            if not rst:held={p['name']:int(p['reset_hex'],16) for p in r['inputs']};iv=0;core=dict(r['output_reset']);cv=0
            else:
                if iv:core=reference(r,held)
                cv=iv;held.update({n:x[n] for n in held if wen[n]})
                if ivw:iv=ivd
        vp=d/'vectors.hex';vp.write_text('\n'.join(vectors)+'\n');loads.append(f'$readmemh("{vp}",v{i});')
        tb.append(f'reg [{bits-1}:0] v{i}[0:191];reg r{i},ivd{i},ivw{i};wire ov{i};')
        tb.extend(f'reg [{p["width"]-1}:0] in{i}_{p["name"]};reg wen{i}_{p["name"]};' for p in r['inputs'])
        tb.extend(f'wire [{p["width"]-1}:0] out{i}_{p["name"]};' for p in r['outputs'])
        conn=['.clk(clk)',f'.rstn(r{i})',f'.iv_data(ivd{i})',f'.iv_wen(ivw{i})',f'.ov(ov{i})']
        conn += [f'.{p["name"]}_data(in{i}_{p["name"]}),.{p["name"]}_wen(wen{i}_{p["name"]})' for p in r['inputs']]+[f'.{p["name"]}(out{i}_{p["name"]})' for p in r['outputs']]
        tb.append(f'{top} dut{i}('+','.join(conn)+');')
        drive.append('{'+','.join([f'r{i}',f'ivd{i}',f'ivw{i}']+[f'in{i}_{p["name"]}' for p in r['inputs']]+[f'wen{i}_{p["name"]}' for p in r['inputs']])+f'}}=v{i}[j][{bits-1}:{no}];')
        outputs='{'+','.join([f'out{i}_{p["name"]}' for p in r['outputs']]+[f'ov{i}'])+'}'
        check.append(f'if({outputs}!==v{i}[j][{no-1}:0])$fatal(1,"{r["id"]} cycle %0d got%h want%h",j,{outputs},v{i}[j][{no-1}:0]);')
    (out/'all.sv').write_text('\n'.join(modules));(out/'tb.sv').write_text('\n'.join(tb)+'\ninitial begin\n'+'\n'.join(loads)+'\nfor(j=0;j<192;j=j+1)begin clk=0;\n'+'\n'.join(drive)+'\n#5;clk=1;#1;\n'+'\n'.join(check)+'\n#4;end $display("SHARED_RTL_PASS sources='+str(len(rows))+' cycles=192");$finish;end endmodule\n')
    write(out/'structures.json',dict(rows=rows,cycles=192,reference='independent Python integer arithmetic and held-valid/reset cycle recurrence',full_D_ready=False));print('SHARED_PRODUCTS_COVERED sources='+str(len(rows)),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('init','export','products'));p.add_argument('--out',type=Path,required=True);p.add_argument('--tool',type=Path);a=p.parse_args()
    if a.action=='init':init(a.out.resolve())
    elif a.action=='export':export(a.out.resolve(),a.tool.resolve())
    else:products(a.out.resolve())


if __name__=='__main__':main()
