"""Complete state-pin CTS CEC using the established Yosys/ABC AIG pipeline.

No internal combinational correspondence is assumed. All top ports and every
pin of identical named sequential cells form the complete combinational cut.
Positive ABC CEC plus output/D/CLK corruption controls are required.
"""
import argparse
from collections import Counter
from contextlib import ExitStack
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from .workload_abcd import ROOT,read,write,sha
from .workload_backend_finish import verify as verify_parent
from .model_m2_cec import YOSYS,ABC,quote,cut_boundary,invert_aig_output
from .model_m2_live_cec import check_result
from .model_m2_aig import full_map
from .budget import Ledger,POLICY,BudgetExceeded
from .processes import run_command

VERSION='workload-complete-state-cut-cec-v2'


def pi_census(text):
    """The original Kepler counts also expose constant-cell outputs as PIs."""
    result=[]
    for side in (0,1):
        part=text.split(f'design {side} PI summary by model/term',1)[1].split(f'design {side} PO summary',1)[0]
        counts={}
        for master,pin,n in re.findall(r'^\|\s*(\S+)\s*\|\s*(\S+)\s*\|\s*(\d+)\s*\|',part,re.M):
            counts[master+'/'+pin]=int(n)
        result.append(counts)
    if result[0]!=result[1] or not result[0]:raise ValueError('original PI census differs')
    return result[0]


def reconcile_inputs(design,top,legacy):
    """Keep all real inputs/state outputs; prove every removed PI constant.

    Constant models must contain no cells and output literal 0/1. No logic
    output, unnamed input, or state pin can be removed to match a count.
    """
    modules=design['modules'];module=modules[top];census=Counter();constants=[]
    for name,port in module['ports'].items():
        if port['direction']=='input':census[top+'/'+name]+=len(port['bits'])
    from .model_m2_cec import sequential_model
    for name,cell in module['cells'].items():
        model=modules[cell['type']]
        if sequential_model(model):
            for pin,port in model['ports'].items():
                if port['direction']=='output':census[cell['type']+'/'+pin]+=len(port['bits'])
        elif not model.get('cells') and model['ports'] and all(
                p['direction']=='output' and all(b in ('0','1') for b in p['bits']) for p in model['ports'].values()):
            for pin,port in model['ports'].items():
                census[cell['type']+'/'+pin]+=len(port['bits'])
                constants.append(dict(instance=name,master=cell['type'],pin=pin,literal_bits=port['bits']))
    if dict(census)!=legacy:raise ValueError('full top/state/constant PI census does not reproduce original LEC')
    return sorted(constants,key=lambda v:(v['instance'],v['pin']))


def admit(root,task_id,batch):
    _,parent=verify_parent(root);task=next(t for t in parent['tasks'] if t['id']==task_id)
    source=root/'runs'/task_id;m=read(source/'manifest.json');folder=root/'proofs'/batch
    if folder.exists() or m['status']!='failed' or m.get('failure_code')!='timeout':
        raise ValueError('new exact retained-pair CEC requires a settled timeout')
    text=(source/'logs/asap7/arithmetic_probe/base/4_rsz_lec_check.log').read_text();counts=[]
    for kind in ('PIs','POs'):
        pair=[re.search(rf'size of {kind} in circuit {i}: (\d+)',text) for i in (0,1)]
        if any(v is None for v in pair) or pair[0][1]!=pair[1][1]:raise ValueError('original complete LEC boundary missing')
        counts.append(int(pair[0][1]))
    paths=[source/'results/asap7/arithmetic_probe/base'/n for n in ('4_before_rsz_lec.v','4_after_rsz_lec.v')]
    for p in paths:
        if m['evidence_sha256'].get(str(p.relative_to(source)))!=sha(p):raise ValueError('retained exact netlist changed')
    usage=Ledger().summary();limits=read(POLICY)['resources']
    if usage['walltime_s']+900>limits['max_global_walltime_h']*3600 or usage['CPU_time_s']+3600>limits['max_tool_CPU_time_h']*3600:
        raise ValueError('finite complete CEC envelope unfunded')
    folder.mkdir(parents=True);sources={}
    for name in ('workload_cec.py','model_m2_cec.py','model_m2_live_cec.py','model_m2_aig.py'):
        p=Path(__file__).with_name(name);dest=folder/name;shutil.copy2(p,dest);sources[name]=sha(p)
    a=dict(version=VERSION,id=parent['id']+'-'+batch,task_id=task_id,top=task['top'],
           source=str(source),source_manifest_sha256=sha(source/'manifest.json'),
           before=str(paths[0]),after=str(paths[1]),before_sha256=sha(paths[0]),after_sha256=sha(paths[1]),
           expected_boundary=dict(input=counts[0],output=counts[1]),libraries=m['libraries'],
           original_PI_census=pi_census(text),
           tools={str(p):sha(p) for p in (YOSYS,ABC)},sources=sources,
           timeout_s=900,threads=4,memory_limit_MiB=8192,call_caps=dict(synth=0,grt=0,support=1),
           automatic_retries=0,application_PPA_feedback=False)
    write(folder/'admission.json',a);return a


def binding(folder):
    a=read(folder/'admission.json')
    if a['version']!=VERSION:raise ValueError('wrong complete CEC admission')
    for name,h in a['sources'].items():
        if sha(Path(__file__).with_name(name))!=h or sha(folder/name)!=h:raise ValueError('complete CEC producer changed')
    if sha(Path(a['source'])/'manifest.json')!=a['source_manifest_sha256']:raise ValueError('CEC source manifest changed')
    for key in ('before','after'):
        if sha(a[key])!=a[key+'_sha256']:raise ValueError('CEC exact input changed')
    for name,h in a['tools'].items():
        if sha(name)!=h:raise ValueError('CEC binary changed')
    for lib in a['libraries']:
        if sha(lib['path'])!=lib['sha256']:raise ValueError('CEC Liberty changed')
    return a


def prove(folder):
    a=binding(folder);out=folder/'result';out.mkdir(exist_ok=False)
    p=dict(version=VERSION,status='running',admission_path=str(folder/'admission.json'),
           admission_sha256=sha(folder/'admission.json'),before_sha256=a['before_sha256'],after_sha256=a['after_sha256'],
           top=a['top'],tools=a['tools'],libraries=a['libraries'],commands=[])
    def execute(command,stem):
        with (out/(stem+'.log')).open('x') as stream:
            rec=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,timeout=900)
        p['commands'].append(dict(command=command,exit_code=rec.returncode))
        if rec.returncode:raise ValueError('complete CEC command failed: '+stem)
    try:
        libcmd=['read_liberty -ignore_miss_func '+quote(lib['path']) for lib in a['libraries']]
        interfaces=[];maps=[];constants=[];input_constants=[]
        for side,path in (('gold',a['before']),('gate',a['after'])):
            script=out/(side+'-read.ys');script.write_text('\n'.join(libcmd+[
                'read_verilog '+quote(path),'hierarchy -check -top '+a['top'],
                'write_json '+quote(out/(side+'-hier.json'))])+'\n')
            execute([str(YOSYS),'-T','-s',str(script)],side+'-read')
            design=read(out/(side+'-hier.json'))
            reconciled=reconcile_inputs(design,a['top'],a['original_PI_census']);input_constants.append(reconciled)
            b,s,c=cut_boundary(design,a['top']);interfaces.append((b,s,c))
            expected=dict(a['expected_boundary']);expected['input']-=sum(len(r['literal_bits']) for r in reconciled)
            if c!=expected:raise ValueError('full state cut differs from reconciled complete LEC boundary')
            write(out/(side+'-cut.json'),design)
            script=out/(side+'-aig.ys');script.write_text('\n'.join([
                'read_json '+quote(out/(side+'-cut.json')),'hierarchy -check -top '+a['top'],
                'flatten -noscopeinfo','proc','opt','techmap','opt','check -assert','aigmap','check -assert',
                'write_json '+quote(out/(side+'-flat.json')),
                'write_aiger -symbols -map '+str(out/(side+'.map'))+' '+quote(out/(side+'.aig'))])+'\n')
            execute([str(YOSYS),'-T','-s',str(script)],side+'-aig')
            flat=read(out/(side+'-flat.json'))['modules'][a['top']]
            if any(cell['type'] not in ('$_AND_','$_NOT_') for cell in flat['cells'].values()):
                raise ValueError('unknown or stateful cell left in full combinational AIG')
            with (out/(side+'.aig')).open('rb') as stream:header=stream.readline().decode().split()
            if header[0]!='aig' or list(map(int,header[2:5]))!=[c['input'],0,c['output']]:raise ValueError('incomplete CEC AIG')
            mapping,const=full_map(out/(side+'.aig'),out/(side+'.map'),flat,c['input'],c['output'])
            maps.append(mapping);constants.append(const)
        if interfaces[0]!=interfaces[1] or maps[0]!=maps[1] or input_constants[0]!=input_constants[1]:
            raise ValueError('full state models, constant sources, interfaces or AIG port order differ')
        p['boundary']=interfaces[0][2]
        p['constant_PI_reconciliation']=input_constants[0]
        write(out/'complete-boundary.json',dict(pins=interfaces[0][0],sequential_cells=interfaces[0][1],map=maps[0],constant_outputs=constants))
        execute([str(ABC),'-c','cec -n '+str(out/'gold.aig')+' '+str(out/'gate.aig')],'cec')
        check_result((out/'cec.log').read_text(),True)
        controls=dict(top_output=lambda name:not name.startswith('cec_state_'),
                      register_D=lambda name:name.startswith('cec_state_') and bytes.fromhex(name[10:]).endswith(b'\0D'),
                      register_CLK=lambda name:name.startswith('cec_state_') and bytes.fromhex(name[10:]).endswith(b'\0CLK'))
        if constants[1]:
            symbol=constants[1][0]['symbol'];controls['constant_register_D']=lambda name:name==symbol
        p['negative_controls']=[]
        for name,predicate in controls.items():
            index=next(int(v[1]) for v in maps[1] if v[0]=='output' and predicate(v[3]))
            mutated=out/(name+'.aig');invert_aig_output(out/'gate.aig',mutated,index)
            execute([str(ABC),'-c','cec -n '+str(out/'gold.aig')+' '+str(mutated)],'negative-'+name)
            check_result((out/('negative-'+name+'.log')).read_text(),False);p['negative_controls'].append(name)
        p['status']='passed'
    except Exception as e:p.update(status='failed',failure_reason=str(e));raise
    finally:
        p['artifacts']={f.name:sha(f) for f in out.iterdir() if f.is_file() and f.name!='proof.json'}
        write(out/'proof.json',p)


def verify_proof(path,before,after):
    path=Path(path);p=read(path);folder=path.parent;a=binding(Path(p['admission_path']).parent)
    if (p['version']!=VERSION or p['status']!='passed' or sha(before)!=p['before_sha256']
            or sha(after)!=p['after_sha256'] or sha(p['admission_path'])!=p['admission_sha256']):
        raise ValueError('complete structural CEC does not prove this exact pair')
    for n,h in p['artifacts'].items():
        if sha(folder/n)!=h:raise ValueError('CEC proof artifact changed')
    expected=dict(a['expected_boundary']);expected['input']-=sum(len(r['literal_bits']) for r in p['constant_PI_reconciliation'])
    if p['boundary']!=expected:raise ValueError('CEC boundary changed')
    check_result((folder/'cec.log').read_text(),True)
    if not {'top_output','register_D','register_CLK'}<=set(p['negative_controls']):raise ValueError('missing CEC corruption controls')
    for name in p['negative_controls']:check_result((folder/('negative-'+name+'.log')).read_text(),False)
    print('WORKLOAD_CEC_EXACT_COMPLETE_PAIR_VERIFIED',flush=True)
    return p


def run(root,batch):
    verify_parent(root);folder=root/'proofs'/batch;a=binding(folder);ledger=Ledger()
    if any(e.get('admission_id')==a['id'] for e in read(ledger.path)['entries']):raise ValueError('CEC already attempted')
    command=[sys.executable,'-B','-m','experiments.arithmetic_dse.workload_cec','prove','--root',str(root),'--batch',batch]
    ctx=dict(target_platform='asap7',admission_id=a['id'],task_id=a['task_id'])
    env=dict(os.environ,OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',YOSYS_MAX_THREADS='4',PYTHONDONTWRITEBYTECODE='1')
    with ExitStack() as stack:
        deadline=time.monotonic()+1800
        while True:
            try:stack.enter_context(ledger.job(ctx));break
            except BudgetExceeded as error:
                if str(error)!='all backend job slots occupied' or time.monotonic()>=deadline:raise
                time.sleep(2)
        reservation=ledger.reserve(None,900,4,'final_evaluation',command,folder/'proof',context=ctx)
        record=run_command(command,folder,'proof-driver',900,env,8192,cpu_limit_s=reservation['CPU_time_s'])
        ledger.finish(reservation,record);write(folder/'command.json',dict(record,budget_reservation_id=reservation['id']))
    if record['exit_code']:raise ValueError('complete CEC failed; retained '+record['log'])
    return verify_proof(folder/'result/proof.json',a['before'],a['after'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('admit','run','prove'))
    p.add_argument('--root',type=Path,required=True);p.add_argument('--batch',required=True);p.add_argument('--task')
    a=p.parse_args();root=a.root.resolve()
    print(admit(root,a.task,a.batch) if a.action=='admit' else run(root,a.batch) if a.action=='run' else prove(root/'proofs'/a.batch))
