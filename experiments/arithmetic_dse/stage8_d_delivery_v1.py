"""Seal the real function-D prototype and package its unchanged dependencies."""
import argparse
from pathlib import Path
import shutil
from .model_fast_preflight import read,write,sha
from .stage8_d_output_v1 import ROOT,verify

BUNDLE=ROOT/'experiments/arithmetic/models/asap7_function_D_prototype_v1'
CONSUMERS=['rtlzz/src/backend/arithmetic_function_selection.cpp','rtlzz/src/backend/arithmetic_function_selection.hpp','rtlzz/main/arithmetic_d.cpp',
    'experiments/arithmetic_dse/run_function_d.py']


def seal(out,binary):
    a=verify(out)
    if BUNDLE.exists():raise ValueError('preserve D dependency delivery')
    parity=read(out/'parity.json');negative=read(out/'negative.json');partial=read(out/'partial-domain-negative-v2/proof.json');sim=read(ROOT/'build/step8-D-20261111/d8-sim-run-01/commands.json')[0]
    if parity['status']!='passed_real_function_D_selection_parity' or negative['status']!='passed_D_refusal_checks' or partial['covered']==0 or sim['exit_code'] or 'FUNCTION_D_RTL_PASS' not in Path(sim['log']).read_text():raise ValueError('D software acceptance missing')
    BUNDLE.mkdir(parents=True);paths={'operators':Path(a['dependencies']['node']['path']),'S_binding':Path(a['dependencies']['S_binding']['path']),'composition':Path(a['dependencies']['composition']['path'])}
    binding=read(paths['S_binding'])
    for name,key in [('state_model','state_model'),('service_contract','service_contract')]:paths[name]=(paths['S_binding'].parent/binding[key]['path']).resolve()
    destinations=dict(operators='../asap7_conditional_operators_v1/operators.json',S_binding='binding.json',composition='composition.json',state_model=binding['state_model']['path'],service_contract=binding['service_contract']['path'])
    dependencies={}
    for n,p in paths.items():
        dest=(BUNDLE/destinations[n]).resolve()
        if n!='operators':shutil.copy2(p,dest)
        if sha(dest)!=sha(p):raise ValueError('D delivery dependency bytes changed')
        dependencies[n]=dict(path=destinations[n],sha256=sha(dest))
    manifest=dict(version='asap7-function-D-prototype-v1',output_scope=a['output_scope'],dependencies=dependencies,consumer_sources={n:sha(ROOT/n) for n in CONSUMERS},consumer_binary_sha256=sha(binary),
        numerical_T_interval_ps=[500,3000],actual_support='intersection of node, S, shared numerical/semantic domains; refuse incomplete candidate coverage',
        candidate_policy='mul-candidates-v1',arithmetic='unsigned Mul/Add/AddCarry plus exact pure bit wiring',G_delay_ps=0,G_area_um2=0,joint_reserve_ps=50,
        selection='minimum total area among predicted feasible, else minimum worst violation and then area; stable ID tie',
        functional_reset_preserved=True,reset_timing_checked=False,independent_joint_qualified=False,formal_D_selection=False,full_D_ready=False,
        scope_authorization='user explicitly deferred reset timing and requested D RTL output',software_acceptance=dict(query_checks=parity['query_checks'],arc_checks=parity['arc_checks'],target_count=len(parity['cases']),negative_checks=len(negative['checks'])+1))
    write(BUNDLE/'bundle.json',manifest)
    files={str(ROOT/n):sha(ROOT/n) for n in CONSUMERS};files.update({str((BUNDLE/d['path']).resolve()):d['sha256'] for d in dependencies.values()});files[str(binary)]=sha(binary);files[str(BUNDLE/'bundle.json')]=sha(BUNDLE/'bundle.json')
    for n in ('parity.json','negative.json','partial-domain-negative-v2/proof.json','simulation/contract.json','source-request.json','source.cpp'):files[str(out/n)]=sha(out/n)
    for t in a['targets_ps']:
        for n in ('D.sv','D_core.sv','selection.json','selected.pipeline.txt'):files[str(out/'outputs'/('T'+str(t))/n)]=sha(out/'outputs'/('T'+str(t))/n)
    write(out/'delivery-freeze.json',dict(version='D-prototype-delivery-freeze-v1',files=files,model_parameters_changed=False,reset_timing_checked=False,full_D_ready=False))
    print('D_DELIVERY_SEALED real_function_targets='+str(len(parity['cases']))+' nodes='+str(parity['query_checks'])+' EDA=0',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);a=p.parse_args();seal(a.out.resolve(),a.binary.resolve())
