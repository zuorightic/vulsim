"""Qualify exact pure-bit state aliases using actual matching Liberty models.

Sequential Liberty functions are reusable cell definitions, not implementation
state. A pre-route proof view borrows only those definitions from a successful
same-library run; all cells/nets remain from the stopped synthesis snapshot.
"""
import argparse
from copy import deepcopy
from pathlib import Path
from .model_fast_preflight import read,write,sha
from .stage67_pure_alias_v2 import verify,semantics


def run(root,out):
    if out.exists():raise ValueError('preserve pure-alias qualification')
    out.mkdir(parents=True)
    bank=root/'shared-probe';a=read(bank/'admission.json');task=next(t for t in a['tasks'] if t['placement']=='placement-0')
    d=bank/'runs'/task['id'];success=bank/'runs'/'shared-alias-placement-1-T1500'
    for n,h in a['sources'].items():
        if sha(Path(__file__).resolve().parents[2]/n)!=h:raise ValueError('probe producer drift')
    if sha(task['rtl'])!=task['rtl_sha256'] or sha(task['endpoint_contract'])!=task['endpoint_sha256']:raise ValueError('original source/contract changed')
    libs=read(d/'manifest.json')['libraries'];other=read(success/'manifest.json')['libraries']
    if libs!=other:raise ValueError('sequential library definitions differ')
    for lib in libs:
        if sha(lib['path'])!=lib['sha256']:raise ValueError('actual Liberty file drift')
    pins=read(d/'liberty-pins.json');design=read(d/'mapped.json');contract=read(task['endpoint_contract']);source=read(Path(task['input_directory'])/'source.json');rtl=Path(task['rtl']).read_text()
    state=verify(design,pins,contract,source,rtl)
    write(out/'mapped-state.json',state)
    models=read(success/'logs/asap7/arithmetic_probe/base/structural_cec/gold-hier.json')['modules']
    view=out/'proof-view';write(view/'mapped.json',design);write(view/'liberty-pins.json',pins)
    write(view/'logs/asap7/arithmetic_probe/base/structural_cec/gold-hier.json',dict(modules={n:models[n] for n in pins}))
    proof=semantics(view,state,rtl,contract);write(out/'state-semantics.json',proof)
    missing=state['pure_bit_alias_proof'][0]['word'];negatives=[]
    def reject(name,fn):
        try:fn()
        except (ValueError,KeyError) as e:negatives.append(dict(name=name,rejected=True,reason=str(e)))
        else:raise ValueError('invalid alias accepted: '+name)
    for field,value in [('stage',9),('enable_stage','different_enable')]:
        c=deepcopy(contract);next(s for s in c['state_slots'] if s['name']==missing)[field]=value
        reject(field,lambda c=c:verify(design,pins,c,source,rtl))
    old=missing+" <= 41'h0";new=missing+" <= 41'h200"
    if rtl.count(old)!=1:raise ValueError('negative reset callsite changed')
    reject('reset_bit',lambda:verify(design,pins,contract,source,rtl.replace(old,new)))
    # Remove all actual surviving native witnesses, leaving the deleted word.
    mutant=deepcopy(design)
    for mod in mutant['modules'].values():
        for name,row in list(mod.get('netnames',{}).items()):
            if name in ('product','rtlzz_pipe_3_s1','rtlzz_pipe_12_s1'):row['bits']=['0']*len(row['bits'])
        for cell in mod.get('cells',{}).values():
            if cell['type'] not in pins and 'a0' in cell.get('connections',{}) and len(cell['connections']['a0'])==41:cell['connections']['a0']=['0']*41
    reject('no_surviving_FF_witness',lambda:verify(mutant,pins,contract,source,rtl))
    bad=deepcopy(state);word=next(w for w in bad['words'] if w['name']=='core/'+missing);row=next(r for r in word['rows'] if 'cell' in r)
    row['logical_output_inverted']=not row['logical_output_inverted']
    reject('logical_FF_polarity',lambda:semantics(view,bad,rtl,contract))
    bad=deepcopy(state);word=next(w for w in bad['words'] if w['name']=='core/'+missing);word['enable']='rstn'
    reject('Boolean_enable',lambda:semantics(view,bad,rtl,contract))
    write(out/'qualification.json',dict(status='passed_exact_alias_state_qualification_not_joint',logical_references=state['logical_FF_bit_references'],
        unique_physical_FF=state['unique_physical_FF_bits'],alias_groups=len(state['physical_alias_groups']),Boolean_checks=proof['checked_FF_bits'],negatives=negatives,
        inputs={str(f):sha(f) for f in (d/'mapped.json',d/'liberty-pins.json',Path(task['rtl']),Path(task['endpoint_contract']),success/'logs/asap7/arithmetic_probe/base/structural_cec/gold-hier.json')},
        borrowed_models='same SHA-verified Liberty cell definitions only; no state/nets borrowed',CEC='required after resumed route',model_support_changed=False,full_D_ready=False))
    print('PURE_ALIAS_EXACT_PROOF_PASS logical='+str(state['logical_FF_bit_references'])+' physical='+str(state['unique_physical_FF_bits'])+' negatives='+str(len(negatives)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.root.resolve(),a.out.resolve())
