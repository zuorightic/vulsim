"""Freeze the user-approved nine-case target policy through production contracts.

This is a numerical experiment target, not a qualified cost model or physical
admission. Replay consumes frozen producers; no EDA or fitting occurs here.
"""
import argparse
from fractions import Fraction
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types

ROOT = Path(__file__).resolve().parents[2]
POLICY = Path(__file__).with_name('configs')/'model_asap7_m2_target_policy_v1.json'
OUTPUT = Path(__file__).with_name('configs')/'model_asap7_m2_targets_v1.json'
VERSION = 'asap7-m2-numerical-target-freeze-v1'


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def build(inputs, contracts):
    policy=inputs['policy'];dataset=inputs['reference_data'];proposal=inputs['proposal']
    requirements=inputs['requirements'];cases=inputs['cases'];rules=inputs['target_rules']
    if (policy['version']!='asap7-m2-target-policy-v1' or policy['user_decision']!='采用上述分离口径'
        or policy['additional_numeric_reserve_ps']!=0 or policy['model_qualification_inherited']
        or rules['version']!='arithmetic-targets-v2'
        or rules['period_rule']!='ceil(H_ref[p,case] + (3/2)*D_ref[p,case]/L[case]) ps'
        or dataset['status']!='passed' or dataset['source_role']!='microbenchmark_reference_only'
        or dataset['model_fit_allowed'] or dataset['formal_PPA_read'] or dataset['numerical_targets_frozen']
        or proposal['numeric_targets_frozen'] or proposal['status']!='proposal_pending_research_decision'
        or [c['id'] for c in cases]!=policy['cases']):
        raise ValueError('approved target policy/reference roles differ')
    grt={r['task_id']:r for r in dataset['rows'] if r['stage']=='grt'}
    if set(grt)!=set(requirements['unique_labels']) or len(grt)!=17:
        raise ValueError('complete exact17 grt reference labels required')
    data={key:next(p for p in row['paths'] if p['id']=='data') for key,row in grt.items()}
    bundle={'platform':'asap7','stage':'grt','label_definition':'combinational_data_path_excluding_boundary',
        'reference_set_id':'asap7-m2-reference-v1-ABC1500-SDC40500',
        'settings_sha256':dataset['protocol_sha256'],'source_role':'microbenchmark_only',
        'delays_ps':{key:str(Fraction(str(p['reference_data_delay_ps']))) for key,p in data.items()},
        'actual_data_definition':'launch Q to last core-owned output, including launch wire; capture suffix/clock terms excluded',
        'reference_SDC_ps':40500,'ABC_ps':1500,'IO':'0.2T',
        'reference_manifest_sha256':policy['reference_manifest_sha256'],
        'raw_audit_sha256':policy['reference_raw_audit_sha256']}
    overheads={};rows={}
    for case in cases:
        name=case['id'];req=requirements['cases'][name];ref=dataset['original_DAG_data_references'][name]
        keys=sorted({n['primitive'] for n in case['reference_graph'] if n['primitive']})
        if (case['reference_graph']!=req['reference_graph'] or keys!=req['required_labels']
            or contracts.fixed_latency(case)!=req['L'] or req['L']!=ref['L']):
            raise ValueError('original graph/reference keys/fixed L changed: '+name)
        h=max([Fraction(0)]+[Fraction(str(data[key]['joint_reference_overhead_ps'])) for key in keys])
        arrivals={}
        for node in contracts.topological(case['reference_graph']):
            delay=Fraction(bundle['delays_ps'][node['primitive']]) if node['primitive'] else Fraction(0)
            arrivals[node['id']]=delay+max((arrivals[d] for d in node['deps']),default=Fraction(0))
        d=max(arrivals.values())
        expected=proposal['cases'][name]
        if d!=Fraction(ref['D_ref_ps']) or d!=Fraction(expected['D_ref_ps']) or h!=Fraction(expected['H_ref_ps']):
            raise ValueError('approved proposal does not reproduce: '+name)
        overheads[name]=h
        rows[name]={'L':req['L'],'partition':case['partition'],'D_ref_ps':str(d),'D_ref_decimal_ps':float(d),
            'H_ref_ps':str(h),'H_ref_decimal_ps':float(h),'required_labels':keys,
            'critical_node_path':ref['critical_node_path'],
            'reference_manifest_hashes':{key:grt[key]['manifest_sha256'] for key in keys},
            'H_maximizer_keys':[key for key in keys if Fraction(str(data[key]['joint_reference_overhead_ps']))==h],
            'reference_context_other_path_minimum_period_ps':expected['reference_context_other_path_minimum_period_ps'],
            'other_paths_are_reference_context_diagnostics_not_target_corrections':True}
    batch=contracts.freeze_target_batch(cases,bundle,overheads,platform='asap7')
    for name,row in rows.items():
        period=batch['periods_ps'][name];d=Fraction(row['D_ref_ps']);h=overheads[name]
        if period!=policy['approved_proposed_periods_ps'][name] or period!=proposal['cases'][name]['proposed_T_target_ps']:
            raise ValueError('approved numerical target changed: '+name)
        row.update(T_target_ps=period,target_data_budget_ps=str(Fraction(period)-h),
            target_data_budget_decimal_ps=float(Fraction(period)-h),rho_ref=str((Fraction(period)-h)/d),
            rho_ref_decimal=float((Fraction(period)-h)/d))
    return {'version':VERSION,'status':'numerical_targets_frozen','platform':'asap7','stage':'grt',
        'user_decision':policy['user_decision'],'decision_date':policy['decision_date'],
        'policy':policy,'provenance':inputs['provenance'],'reference_bundle':bundle,'production_batch':batch,
        'cases':rows,'exact_SDC_ps':sorted(set(batch['periods_ps'].values())),
        'ABC_ps':1500,'IO':'0.2T','C_D_candidate_order_unchanged':True,'K':16,
        'numerical_targets_frozen':True,'model_targets_qualified':False,
        'reference_rows_allowed_for_model_fitting':False,'formal_PPA_read':False,'PPA_calls':0,
        'main_36_or_688_admitted':False,'full_D_ready':False}


def load_frozen(folder):
    name='_m2_targets_frozen'
    for key in list(sys.modules):
        if key==name or key.startswith(name+'.'):del sys.modules[key]
    package=types.ModuleType(name);package.__path__=[str(folder/'source/experiments/arithmetic_dse')]
    sys.modules[name]=package
    return importlib.import_module(name+'.model_m2_targets'),importlib.import_module(name+'.contracts')


def freeze(reference,folder,output):
    from . import contracts
    from .case_generator import generate_manifest
    if folder.exists() or output.exists():raise ValueError('preserve existing targets/evidence')
    policy=read(POLICY);manifest=reference/'manifest.json'
    if sha(manifest)!=policy['reference_manifest_sha256'] or sha(reference/'raw-audit.json')!=policy['reference_raw_audit_sha256']:
        raise ValueError('approved reference evidence identity changed')
    for name,h in read(manifest)['files'].items():
        if sha(reference/name)!=h:raise ValueError('reference evidence content changed: '+name)
    verified=read(reference/'verification.json')
    if not all(verified[k] for k in ('portable_raw_replay_passed','full_external_tool_Liberty_CTS_CEC_and_raw_replay_passed',
        'isolated_original_tree_denied','raw_pool_tamper_rejected')):
        raise ValueError('complete reference verification required')
    dataset=read(reference/'raw-audit.json');requirements=Path(dataset['requirements_path'])
    rules=Path(__file__).with_name('configs')/'target_rules_v2.json'
    if sha(requirements)!=dataset['requirements_sha256'] or sha(rules)!=read(requirements)['rules_sha256']:
        raise ValueError('original reference DAG or target rules changed')
    definitions={c['id']:c for c in generate_manifest()['cases']}
    inputs={'policy':policy,'reference_data':dataset,'proposal':read(reference/'target-proposal.json'),
        'requirements':read(requirements),'target_rules':read(rules),'cases':[definitions[n] for n in policy['cases']],
        'provenance':{'reference_evidence':str(reference),'reference_manifest_sha256':sha(manifest),
            'reference_verification_sha256':sha(reference/'verification.json'),'raw_audit_sha256':sha(reference/'raw-audit.json'),
            'proposal_sha256':sha(reference/'target-proposal.json'),'requirements_sha256':sha(requirements),
            'target_rules_sha256':sha(rules),'policy_sha256':sha(POLICY)}}
    result=build(inputs,contracts)
    folder.mkdir(parents=True)
    for name in ('model_m2_targets.py','contracts.py','case_generator.py'):
        src=Path(__file__).with_name(name);dst=folder/'source/experiments/arithmetic_dse'/name
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    write(folder/'inputs.json',inputs);write(folder/'targets.json',result);write(output,result)
    write(folder/'manifest.json',{'version':VERSION,'files':{str(p.relative_to(folder)):sha(p) for p in folder.rglob('*') if p.is_file()},
        'active_target_output':str(output),'active_target_sha256':sha(output)})
    print(json.dumps({'status':'frozen','cases':len(result['cases']),'periods_ps':result['production_batch']['periods_ps'],
        'target_sha256':sha(output),'production_batch_sha256':result['production_batch']['batch_sha256'],'PPA_calls':0}),flush=True)


def verify(folder,external=False):
    manifest=read(folder/'manifest.json')
    if manifest['version']!=VERSION:raise ValueError('target evidence version differs')
    for name,h in manifest['files'].items():
        if sha(folder/name)!=h:raise ValueError('target evidence identity mismatch: '+name)
    producer,contracts=load_frozen(folder);inputs=read(folder/'inputs.json');targets=read(folder/'targets.json')
    if producer.build(inputs,contracts)!=targets:raise ValueError('frozen numerical targets do not reproduce')
    definitions={c['id']:c for c in importlib.import_module(contracts.__package__+'.case_generator').generate_manifest()['cases']}
    if [definitions[n] for n in targets['policy']['cases']]!=inputs['cases']:
        raise ValueError('frozen original case definitions do not reproduce')
    if sha(folder/'targets.json')!=manifest['active_target_sha256']:raise ValueError('target output copy differs')
    if external:
        if sha(manifest['active_target_output'])!=manifest['active_target_sha256']:raise ValueError('active numerical target changed')
        p=targets['provenance'];ref=Path(p['reference_evidence'])
        for name,key in [('manifest.json','reference_manifest_sha256'),('verification.json','reference_verification_sha256'),
                         ('raw-audit.json','raw_audit_sha256'),('target-proposal.json','proposal_sha256')]:
            if sha(ref/name)!=p[key]:raise ValueError('target reference parent changed: '+name)
    result={'status':'passed','external':external,'cases':9,'numerical_targets_frozen':True,
        'production_contracts_replayed':True,'model_targets_qualified':False,'PPA_calls':0}
    print(json.dumps(result),flush=True);return result


def isolated(folder):
    with tempfile.TemporaryDirectory(prefix='m2-targets-isolated-') as tmp:
        tmp=Path(tmp);local=tmp/'evidence';shutil.copytree(folder,local)
        code='''import builtins,io,os,runpy,subprocess,sys
from pathlib import Path
script,folder=sys.argv[1:]
def guard(original):
 def checked(path,*a,**kw):
  if isinstance(path,(str,bytes,os.PathLike)) and str(Path(path).resolve()).startswith('/home/zyrv/'):
   raise RuntimeError('original tree read forbidden')
  return original(path,*a,**kw)
 return checked
builtins.open=guard(builtins.open);io.open=guard(io.open)
def forbidden(*a,**kw):raise RuntimeError('replay subprocess forbidden')
subprocess.Popen=forbidden
sys.argv=[script,'verify','--folder',folder];runpy.run_path(script,run_name='__main__')
'''
        script=local/'source/experiments/arithmetic_dse/model_m2_targets.py'
        env=os.environ.copy();env.update(PATH='',PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONPATH',None)
        result=subprocess.run([sys.executable,'-B','-c',code,str(script),str(local)],cwd=tmp,env=env,capture_output=True,text=True)
        if result.returncode:raise ValueError('isolated target replay failed: '+result.stderr[-2500:])
        path=local/'targets.json';data=read(path);data['cases']['MAC_32']['T_target_ps']+=1;write(path,data)
        result=subprocess.run([sys.executable,'-B','-c',code,str(script),str(local)],cwd=tmp,env=env,capture_output=True,text=True)
        if result.returncode==0 or 'target evidence identity mismatch' not in result.stderr:
            raise ValueError('tampered numerical target accepted')
    print(json.dumps({'status':'passed','original_tree_denied':True,'PATH_empty':True,
        'replay_subprocess_denied':True,'target_tamper_rejected':True,'PPA_calls':0}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('freeze','verify','isolated'))
    parser.add_argument('--folder',type=Path,required=True);parser.add_argument('--reference',type=Path)
    parser.add_argument('--output',type=Path,default=OUTPUT);parser.add_argument('--external',action='store_true');args=parser.parse_args()
    if args.action=='freeze':freeze(args.reference.resolve(),args.folder.resolve(),args.output.resolve())
    elif args.action=='isolated':isolated(args.folder.resolve())
    else:verify(args.folder.resolve(),args.external)
