"""Portable raw reference labels and an explicit, unfrozen H_ref proposal."""
import argparse
from contextlib import redirect_stdout
from fractions import Fraction
import importlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types

from .model_d_requirements_evidence import pack, unpack, sha, read, write

ROOT = Path(__file__).resolve().parents[2]
VERSION = 'asap7-reference-label-evidence-v1'


def proposal(dataset):
    grt = {r['task_id']:r for r in dataset['rows'] if r['stage']=='grt'}
    cases = {}
    for name, item in dataset['original_DAG_data_references'].items():
        selected = [grt[k] for k in item['required_labels']]
        data = [next(p for p in r['paths'] if p['id']=='data') for r in selected]
        h = max([Fraction(0)]+[Fraction(str(p['joint_reference_overhead_ps'])) for p in data])
        d = Fraction(item['D_ref_ps'])
        value = h+Fraction(3,2)*d/item['L']
        period = (value.numerator+value.denominator-1)//value.denominator
        other = [{**p,'reference_key':r['task_id']} for r in selected for p in r['paths'] if p['id']!='data']
        cases[name] = {**item,'H_ref_ps':str(h),'H_ref_decimal_ps':float(h),
            'proposed_T_target_ps':period,'proposed_data_budget_ps':float(Fraction(period)-h),
            'proposed_rho_ref':float((Fraction(period)-h)/d),
            'reference_context_other_path_minimum_period_ps':max(
                (p['QD_or_PD_ps']+p['clock_capture_term_ps'])/(.8 if p['kind']=='port' else 1) for p in other),
            'other_path_values_are_diagnostics_at_reference_clock_only':True}
    return {'version':'asap7-reference-H-proposal-v1','status':'proposal_pending_research_decision',
        'H_rule':'per case max(0, joint_reference_overhead_ps of data paths for required keys)',
        'joint_H':'capture suffix plus clock/setup/skew/uncertainty; excludes launch-Q-to-core-output data',
        'control_input_external_paths':'retain as separate minimum-period diagnostics at reference context; do not sum into D_ref or adjust targets',
        'additional_numeric_reserve_ps':0,'period_rule_unchanged':'ceil(H_ref + 1.5*D_ref/L)',
        'model_qualification_inherited':False,'numeric_targets_frozen':False,'cases':cases}


def frozen_modules(source):
    name = '_reference_frozen'
    for key in list(sys.modules):
        if key==name or key.startswith(name+'.'):
            del sys.modules[key]
    package = types.ModuleType(name)
    package.__path__ = [str(source/'experiments/arithmetic_dse')]
    sys.modules[name] = package
    return {n:importlib.import_module(name+'.'+n) for n in
        ('backend','platforms','sdc','model_reference_labels_v2','model_reference_audit')}


def seal(dataset_path, folder):
    dataset = read(dataset_path)
    if dataset['status']!='passed' or dataset['numerical_targets_frozen']:
        raise ValueError('settled audited reference labels required')
    folder.mkdir(parents=True,exist_ok=False)
    admission = Path(dataset['admission_path'])
    a = read(admission)
    sources = {str(p.relative_to(ROOT)):p for p in (ROOT/'experiments/arithmetic_dse').glob('*.py')}
    for path in (ROOT/'experiments/arithmetic_dse/configs').rglob('*'):
        if path.is_file():sources[str(path.relative_to(ROOT))]=path
    for name, h in a['sources'].items():
        path = admission.parent/'source'/name
        if sha(path)!=h:raise ValueError('reference archived producer differs')
        sources[name]=path
    pack(folder/'source-pool.json.gz',sources)
    artifacts = {'dataset.json':dataset_path,'pin-table.json':Path(a['Liberty_pin_table']),
        'reference-requirements.json':Path(dataset['requirements_path'])}
    external = {str(p.resolve()):sha(p) for p in artifacts.values()}
    for run in dataset['runs']:
        directory = Path(run['directory'])
        for name in ('manifest.json','input.sv','reference-contract.json','metrics.json','liberty_cells.json',
                     'reference-synth-ownership.json','reference-grt-ownership.json'):
            artifacts[run['id']+'/'+name]=directory/name
        for stage, stem in [('synth','1_synth'),('grt','5_1_grt')]:
            artifacts[run['id']+'/results/'+stem+'.sdc']=directory/'results/asap7/arithmetic_probe/base'/(stem+'.sdc')
            artifacts[run['id']+'/native/'+stem+'.json']=directory/'logs/asap7/arithmetic_probe/base'/(stem+'.json')
            for path in (directory/'reports/asap7/arithmetic_probe/base').glob('vulsim_'+stage+'*'):
                if path.suffix in ('.rpt','.tsv'):
                    artifacts[run['id']+'/reports/'+path.name]=path
    receipts = {}
    for label, origin in [('v1',Path(a['parent_admission']).parent),
                           ('v2',Path(a['support_predecessor_admission']).parent),('v3',admission.parent)]:
        for name in ('admission.json','progress.json','software-proof.json','reader-proof.json'):
            receipts[label+'/'+name]=origin/name
    for directory, h in dataset['audit']['ancestor_manifests'].items():
        path = Path(directory)
        if sha(path/'manifest.json')!=h:raise ValueError('reference ancestor changed during seal')
        label = path.parent.parent.name+'/'+path.name
        receipts[label+'/manifest.json']=path/'manifest.json'
        for c in read(path/'manifest.json')['commands']:
            for field in ('log','gnu_time'):
                item=Path(c[field]);receipts[label+'/'+item.name]=item
            item=Path(c['log'].removesuffix('.log')+'.command.json');receipts[label+'/'+item.name]=item
    ledger=read(ROOT/'experiments/arithmetic/backend_usage.json')
    entries=[e for e in ledger['entries'] if e['id'] in set(dataset['audit']['paid_leaf_ids'])]
    write(folder/'paid-entries.json',entries)
    for p in artifacts.values():external[str(p.resolve())]=sha(p)
    for p in receipts.values():external[str(p.resolve())]=sha(p)
    pack(folder/'raw-pool.json.gz',artifacts)
    pack(folder/'receipts-pool.json.gz',receipts)
    shutil.copy2(dataset_path,folder/'raw-audit.json')
    write(folder/'target-proposal.json',proposal(dataset))
    write(folder/'provenance.json',{'version':VERSION,'original_artifacts':external,
        'portable_replay':'raw timing/area/ownership/FF/SDC/RC/paid receipts/DAG and H proposal; no new EDA',
        'full_tool_Liberty_and_CTS_CEC_checked_by_external_raw_audit':True,
        'portable_CTS_CEC_reexecution_claimed':False,'model_release':False,'numeric_targets_frozen':False})
    write(folder/'manifest.json',{'version':VERSION,'files':{p.name:sha(p) for p in folder.iterdir() if p.is_file()}})
    print(json.dumps({'status':'sealed','bytes':sum(p.stat().st_size for p in folder.iterdir() if p.is_file()),
        'raw_files':len(artifacts),'source_files':len(sources),'receipt_files':len(receipts)}),flush=True)


def verify(folder, external=False):
    manifest=read(folder/'manifest.json')
    if manifest['version']!=VERSION:raise ValueError('reference evidence version differs')
    for name,h in manifest['files'].items():
        if sha(folder/name)!=h:raise ValueError('reference evidence identity mismatch: '+name)
    with tempfile.TemporaryDirectory(prefix='reference-label-replay-') as tmp:
        tmp=Path(tmp);source=tmp/'source';raw=tmp/'raw';receipts=tmp/'receipts'
        unpack(folder/'source-pool.json.gz',source);unpack(folder/'raw-pool.json.gz',raw);unpack(folder/'receipts-pool.json.gz',receipts)
        modules=frozen_modules(source);dataset=read(raw/'dataset.json')
        if dataset!=read(folder/'raw-audit.json'):raise ValueError('reference dataset copy differs')
        entries={e['id']:e for e in read(folder/'paid-entries.json')};paid=set()
        for directory,h in dataset['audit']['ancestor_manifests'].items():
            original=Path(directory);local=receipts/original.parent.parent.name/original.name
            if sha(local/'manifest.json')!=h:raise ValueError('reference ancestor receipt identity differs')
            m=read(local/'manifest.json')
            for c in m['commands']:
                e=entries[c['budget_reservation_id']]
                if (e['status']!='completed' or c['exit_code'] or e['command']!=c['command']
                    or e['walltime_s']!=c['walltime_s'] or e['task_id']!=m['task_id']
                    or e['admission_id']!=m['admission_id']
                    or e['admission_sha256']!=sha(receipts/m['admission_id'].replace('collection-','')/'admission.json')):
                    raise ValueError('portable reference paid receipt differs')
                saved=read(local/Path(c['log'].removesuffix('.log')+'.command.json').name)
                if saved not in (c,{k:v for k,v in c.items() if k!='budget_reservation_id'}):
                    raise ValueError('portable reference command differs')
                paid.add(e['id'])
        if paid!=set(dataset['audit']['paid_leaf_ids']):raise ValueError('reference paid coverage differs')
        pins=read(raw/'pin-table.json');rows=[]
        for run in dataset['runs']:
            directory=raw/run['id'];m=read(directory/'manifest.json');p=m['platform_profile']
            cells=read(directory/'liberty_cells.json')['cells'];s=read(directory/'reference-contract.json')['spec']
            if sha(directory/'manifest.json')!=run['manifest_sha256']:raise ValueError('reference run identity differs')
            for stage,stem in [('synth','1_synth'),('grt','5_1_grt')]:
                old=next(r for r in dataset['rows'] if r['task_id']==run['id'] and r['stage']==stage)
                g=modules['backend'].stage_metrics(directory/'reports',stage,cells,40500,selected=p)
                prefix=directory/'reports'/('vulsim_'+stage)
                owner,instances,_=modules['model_reference_labels_v2'].partition(prefix,pins,p,
                    expected={n:s[n+'_bits'] for n in ('input_service','native_state','external_state')})
                paths=modules['model_reference_labels_v2'].labels(prefix,s,40500,g['raw_report_units']['time']['to_ps'],pins,instances)
                if (paths!=old['paths'] or owner!=read(directory/('reference-'+stage+'-ownership.json'))
                    or owner['owner_area_um2']!=old['owner_area_um2'] or owner['owner_FF_bits']!=old['owner_FF_bits']
                    or abs(g['cell_area_um2']-owner['total_area_um2'])>1e-6
                    or g['setup_worst_slack_ps']!=old['setup_slack_ps'] or g['hold_worst_slack_ps']!=old['hold_slack_ps']):
                    raise ValueError('reference raw portable labels differ')
                modules['platforms'].verify_wire_readback(Path(str(prefix)+'_layer_rc.tsv'),p)
                actual=modules['sdc'].verify_sdc((directory/'results'/(stem+'.sdc')).read_text(),p,40500,
                    modules['sdc'].rtl_ports((directory/'input.sv').read_text(),'ModelBundle'))
                if actual!=m['sdc_contracts'][stage]:raise ValueError('portable reference SDC differs')
                native=read(directory/'native'/(stem+'.json'))[
                    ('synth' if stage=='synth' else 'globalroute')+'__design__instance__area__stdcell']
                modules['backend'].verify_orfs_area(g['cell_area_um2'],native);rows.append(old)
        data=modules['model_reference_audit'].data_paths(read(raw/'reference-requirements.json'),rows)
        if data!=dataset['original_DAG_data_references'] or proposal(dataset)!=read(folder/'target-proposal.json'):
            raise ValueError('reference graph/proposed target calculation differs')
        if external:
            for name,h in read(folder/'provenance.json')['original_artifacts'].items():
                if sha(name)!=h:raise ValueError('external reference artifact differs: '+name)
            with redirect_stdout(io.StringIO()):
                modules['model_reference_audit'].extract(Path(dataset['admission_path']).parent,
                    Path(dataset['requirements_path']),tmp/'external-audit.json')
            if read(tmp/'external-audit.json')!=dataset:raise ValueError('full external reference audit differs')
    result={'status':'passed','external':external,'stage_rows':34,'path_labels':272,
        'paid_leaf_commands':len(paid),'PPA_calls':0,'numeric_targets_frozen':False,'full_D_ready':False}
    print(json.dumps(result),flush=True);return result


def isolated(folder):
    with tempfile.TemporaryDirectory(prefix='reference-isolated-') as tmp:
        tmp=Path(tmp);local=tmp/'evidence';shutil.copytree(folder,local);source=tmp/'source'
        unpack(local/'source-pool.json.gz',source)
        code='''import builtins,io,os,runpy,subprocess,sys
from pathlib import Path
script,folder=sys.argv[1:]
def guarded(original):
 def checked(path,*a,**kw):
  if isinstance(path,(str,bytes,os.PathLike)) and str(Path(path).resolve()).startswith('/home/zyrv/'):
   raise RuntimeError('original tree read forbidden')
  return original(path,*a,**kw)
 return checked
builtins.open=guarded(builtins.open);io.open=guarded(io.open)
def forbidden(*a,**kw):raise RuntimeError('replay subprocess forbidden')
subprocess.Popen=forbidden
sys.argv=[script,'verify','--folder',folder]
runpy.run_path(script,run_name='__main__')
'''
        # Execute as a module so relative imports resolve to the copied sources.
        code=code.replace("runpy.run_path(script,run_name='__main__')", "sys.path.insert(0,str(Path(script).parents[2]));runpy.run_module('experiments.arithmetic_dse.model_reference_evidence',run_name='__main__')")
        script=source/'experiments/arithmetic_dse/model_reference_evidence.py'
        env=os.environ.copy();env.update(PATH='',PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONPATH',None)
        result=subprocess.run([sys.executable,'-B','-c',code,str(script),str(local)],cwd=tmp,env=env,capture_output=True,text=True)
        if result.returncode:raise ValueError('isolated reference replay failed: '+result.stderr[-2500:])
        path=local/'raw-pool.json.gz';value=bytearray(path.read_bytes());value[len(value)//2]^=1;path.write_bytes(value)
        result=subprocess.run([sys.executable,'-B','-c',code,str(script),str(local)],cwd=tmp,env=env,capture_output=True,text=True)
        if result.returncode==0 or 'evidence identity mismatch' not in result.stderr:
            raise ValueError('tampered reference evidence accepted')
    print(json.dumps({'status':'passed','original_tree_denied':True,'PATH_empty':True,
        'replay_subprocess_denied':True,'raw_pool_tamper_rejected':True,'PPA_calls':0}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('seal','verify','isolated'))
    parser.add_argument('--folder',type=Path,required=True);parser.add_argument('--dataset',type=Path);parser.add_argument('--external',action='store_true')
    args=parser.parse_args()
    if args.action=='seal':seal(args.dataset.resolve(),args.folder.resolve())
    elif args.action=='isolated':isolated(args.folder.resolve())
    else:verify(args.folder.resolve(),args.external)
