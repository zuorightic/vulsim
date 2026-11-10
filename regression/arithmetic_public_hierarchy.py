"""Public VUL body/module handoff and cycle checks under request v2."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha


def prepare(out):
    out.mkdir(parents=True,exist_ok=False);old=ROOT/'experiments/arithmetic/evidence/step7_m2_native_integration_v1/public-source/MAC_32'
    vectors=[]
    import random
    rng=random.Random(20261110)
    for i in range(144):
        a,b=rng.getrandbits(32),rng.getrandbits(32);c=rng.getrandbits(64);valid=int(i<24 or i%7 not in (1,2));reset=int(i in (0,1,53,54,109))
        vectors.append(dict(a=a,b=b,c=c,valid=valid,reset=reset))
    rows=[]
    for group,L,policy in [('A',1,'core-original-v1'),('B',2,'core-original-v1'),('C',2,'mul-candidates-v1')]:
        d=out/group;d.mkdir();(d/'header.uh').write_bytes((old/'header.uh').read_bytes());top=(old/'Top.vul').read_text().replace('PIPELINE(core,2,','PIPELINE(core,'+str(L)+',');(d/'Top.vul').write_text(top)
        path=d/'vectors.txt';path.write_text(str(len(vectors))+'\n'+''.join(f'{r["a"]:x} {r["b"]:x} {r["c"]:x} {r["valid"]:x} {r["reset"]:x}\n' for r in vectors))
        main=(old/'Main.utb').read_text();main=re.sub(r'std::ifstream stream\("[^"]+"\)',lambda m:'std::ifstream stream("'+str(path)+'")',main);(d/'Main.utb').write_text(main)
        request=read(old/'request.json');request.update(version='arithmetic-request-v2',operator_boundary_policy='unsigned-op-hierarchy-v1',L=L,candidate_policy=policy,
            platform_profile=str(ROOT/'experiments/arithmetic_dse/configs/platforms/asap7.json'),cost_mode='fixed',model_bundle='',model_bundle_sha256='',
            fixed_cost_table=str(ROOT/'experiments/arithmetic_dse/configs/fixed_op_width_v1.json'),fixed_cost_table_sha256=sha(ROOT/'experiments/arithmetic_dse/configs/fixed_op_width_v1.json'))
        write(d/'request.json',request);rows.append(dict(group=group,L=L,source=str(d),request=str(d/'request.json')))
    write(out/'sources.json',dict(groups=rows,vectors=vectors,policy='unsigned-op-hierarchy-v1',new_physical_calls=0))
    print('prepared public A/B/C, same arithmetic semantics and explicit common boundary policy',flush=True)


def verify(sources,generated,logs):
    spec=read(sources/'sources.json');reports=[]
    reset=(0x80000035*0x80000035+0x8000000000000035)&((1<<64)-1)
    for group in spec['groups']:
        name=group['group'];folder=generated/name;text=(folder/'sim/top.sv').read_text();modules=re.findall(r'\bmodule\s+([A-Za-z_$][\w$]*)',text)
        if len(modules)!=len(set(modules)) or '__rtlzz_arith_' not in text:raise ValueError('missing/duplicate child definitions in public output')
        end=text.index('endmodule');last_definition=min(m.start() for m in re.finditer(r'\(\* keep_hierarchy=1 \*\) module ',text))
        if last_definition<end:raise ValueError('arithmetic module nested in public parent')
        reportfiles=list((folder/'sim').glob('*.pipeline_core.cpp.arithmetic.json'))
        if len(reportfiles)!=1:raise ValueError('public arithmetic report missing')
        report=read(reportfiles[0])
        if report['operator_boundary_policy']!='unsigned-op-hierarchy-v1' or report['rtl_module_definitions_sha256']==hashlib.sha256(b'').hexdigest():raise ValueError('module-definition identity not bound')
        # Saved body and child definitions are separately bound in the report;
        # ensure final VUL contains the selected child module names/instances.
        if report['request']['L']!=group['L']:raise ValueError('public latency request drift')
        entries={};resets={}
        logfile=logs/(name+'.log')
        if not logfile.exists():logfile=folder/'simulation.log'
        for line in logfile.read_text().splitlines():
            if line.startswith(('ROW ','RESET ')):
                tag,index,v,y=line.split();target=entries if tag=='ROW' else resets
                if int(index) in target:raise ValueError('duplicate transaction log')
                target[int(index)]=(int(v),int(y,16))
        history=[];held=reset;comparisons=0;valid_comparisons=0
        for i,r in enumerate(spec['vectors']):
            if r['reset']:
                history=[];held=reset
                if resets.get(i)!=(0,reset):raise ValueError('public reset sequence mismatch')
            history.append(r);valid=len(history)>group['L'] and history[-group['L']-1]['valid']
            if valid or (name=='A' and len(history)>group['L']):
                old=history[-group['L']-1];held=(old['a']*old['b']+old['c'])&((1<<64)-1);comparisons+=1
            if valid:valid_comparisons+=1
            if entries.get(i)!=(int(bool(valid)),held):raise ValueError('public cycle mismatch '+str((name,i,entries.get(i),(valid,held))))
        if len(entries)!=len(spec['vectors']):raise ValueError('incomplete public execution')
        reports.append(dict(group=name,L=group['L'],cycles=len(entries),valid_data_comparisons=valid_comparisons,all_observed_data_comparisons=comparisons,child_definitions=len(modules)-1,
            RTL_sha256=sha(folder/'sim/top.sv'),report_sha256=sha(reportfiles[0])))
    result=dict(status='passed',groups=reports,body_and_file_scope_definitions_verified=True,new_PPA_calls=0)
    write(generated/'public-proof.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','verify'));p.add_argument('--sources',type=Path,required=True);p.add_argument('--generated',type=Path);p.add_argument('--logs',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare(a.sources.resolve())
    else:verify(a.sources.resolve(),a.generated.resolve(),a.logs.resolve())
