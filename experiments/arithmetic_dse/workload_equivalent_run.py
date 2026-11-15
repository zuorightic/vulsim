"""Freeze / run / replay the MAC32 steps 1--3 software experiment, no EDA.

Run inputs are portable repository evidence. Only the explicit freeze command
reads old train labels; run/replay need neither the external artifact tree nor
the stopped physical-comparison reports.
"""
import argparse
import base64
from collections import Counter
from dataclasses import asdict
import gzip
import json
from pathlib import Path
import time

from .sampling_time_contract import (ROOT,canonical,sha,collect_training_receipts,derive_contract)
from .workload_demand import Graph
from .workload_v10_replay import old_structure,retarget,digest
from .workload_diagnostic import DiagnosticPrices,select
from .workload_equivalent import optimize,SearchConfig,VERSION
from .equivalent_period import InversionConfig

DEFAULT=ROOT/'experiments/arithmetic/evidence/workload_equivalent_mac32_v1'
TARGETS=(500,750,1000)
OLD_EVIDENCE=ROOT/'experiments/arithmetic/evidence/workload_diagnostic_stopped_v1'


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(canonical(value)+b'\n')


def compressed(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(gzip.compress(canonical(value),mtime=0))


def read(path):
    path=Path(path);raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def freeze(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    # Extract only frozen software model/reference selections from the old
    # portable payload. Never deserialize its report/PPA labels as model input.
    manifest=read(OLD_EVIDENCE/'manifest.json');parts=[]
    for chunk in manifest['chunks']:
        raw=(OLD_EVIDENCE/chunk['file']).read_bytes()
        if sha(raw)!=chunk['sha256'] or len(raw)!=chunk['bytes']:raise ValueError('old payload changed')
        parts.append(raw)
    raw=b''.join(parts)
    if sha(raw)!=manifest['payload_sha256']:raise ValueError('combined old payload changed')
    payload=json.loads(gzip.decompress(raw));prefix=payload['original_root'];files=payload['files']
    model_raw=base64.b64decode(files[prefix+'/diagnostic-model.json'])
    # The frozen methods metadata binds software identity, not measured PPA.
    methods=json.loads(base64.b64decode(files[prefix+'/methods.json']))
    if sha(model_raw)!=methods['model_sha256']:raise ValueError('baseline model changed')
    (out/'diagnostic-model.json').write_bytes(model_raw)
    selection_freeze=json.loads(base64.b64decode(files[prefix+'/selection-freeze.json']))
    references=[]
    for target in TARGETS:
        path=prefix+f'/diagnostic-scores/mac32/T{target}-L3/model/selection.json'
        # The stopped evidence binds these software selections by hash but
        # does not embed their bytes. Capture those bytes once at freeze time.
        data=base64.b64decode(files[path]) if path in files else Path(path).read_bytes()
        if sha(data)!=selection_freeze['files'][path]:raise ValueError('old software selection changed')
        selection=json.loads(data)
        references.append(dict(target_ps=target,original_selection_sha256=sha(data),
                               selection=selection))
    compressed(out/'baseline-reference.json.gz',references)
    receipts=collect_training_receipts();contract=derive_contract(receipts)
    compressed(out/'characterization-train-receipts.json.gz',receipts)
    write(out/'characterization-contract.json',contract)
    # Inputs are copied from already hashed W2 archives. Each run also checks
    # their parent manifest; no selected-dir metadata enters this experiment.
    structures=[]
    for i in range(4):
        members=old_structure('mac32',i)
        structures.append(dict(structure=i,members_sha256={n:sha(d) for n,d in sorted(members.items())}))
    write(out/'config.json',dict(version=VERSION,case='mac32',targets_ps=TARGETS,L=3,II=1,
        search=asdict(SearchConfig()),inversion=asdict(InversionConfig()),
        frozen_before_batch=True,candidate_set='all four existing W2 structures / all 30 placements',
        source_roles='train boundary audit; application-development software predictions only',
        model_response_refitted=False,EDA_calls=0,new_placements=False,
        baseline_model_raw_sha256=sha(model_raw),old_payload_sha256=manifest['payload_sha256'],
        structures=structures,root_search_exhaustive=False,global_optimum_claimed=False))
    source={str(p.relative_to(ROOT)):p.read_text() for p in sorted((ROOT/'experiments/arithmetic_dse').glob('*.py'))}
    source['regression/test_workload_equivalent.py']=(ROOT/'regression/test_workload_equivalent.py').read_text()
    compressed(out/'software-source.json.gz',source)
    files=['diagnostic-model.json','baseline-reference.json.gz','characterization-train-receipts.json.gz',
           'characterization-contract.json','config.json','software-source.json.gz']
    write(out/'inputs.json',dict(version=VERSION,files={n:sha((out/n).read_bytes()) for n in files},
        parent_archives_manifest_sha256=sha((ROOT/'experiments/arithmetic/evidence/workload_owners_v2/archives.json').read_bytes()),
        baseline_main_commit='672df3e',baseline_rtlzz_commit='28a4f1d',
        baseline_runtime_component_sha256='a1466f0272b55bd20358ea9e3beb84844db8fe8fefe4152e0478224d8f13243d'))
    return dict(status='inputs_frozen',boundary={f:{k:v for k,v in row.items() if k!='source_medians_ps'}
                for f,row in contract['families'].items()},files=len(files))


def verify_inputs(root,*,check_source=True):
    root=Path(root);manifest=read(root/'inputs.json')
    for name,expected in manifest['files'].items():
        if sha((root/name).read_bytes())!=expected:raise ValueError('input identity changed: '+name)
    if sha((ROOT/'experiments/arithmetic/evidence/workload_owners_v2/archives.json').read_bytes())!=manifest['parent_archives_manifest_sha256']:
        raise ValueError('parent archives identity changed')
    if derive_contract(read(root/'characterization-train-receipts.json.gz'))!=read(root/'characterization-contract.json'):
        raise ValueError('train boundary rederivation differs')
    if check_source:
        for name,source in read(root/'software-source.json.gz').items():
            if (ROOT/name).read_text()!=source:raise ValueError('frozen source differs: '+name)
    return read(root/'config.json')


def compact_prediction(p):
    return {k:p[k] for k in ('status','target_met','critical_required_ps','violation_ps','total_area_um2',
                            'comb_area_um2','stages','port_required_ps','owners_count','G_members_not_billed_separately')}


def assert_reference(baseline,expected):
    # Exact frozen function replay, tolerant only of Python float roundoff.
    def close(a,b):
        if isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)):
            return abs(a-b)<=1e-8*max(1,abs(a),abs(b))
        if isinstance(a,dict):return isinstance(b,dict) and all(k in b and close(v,b[k]) for k,v in a.items())
        if isinstance(a,list):return isinstance(b,list) and len(a)==len(b) and all(close(x,y) for x,y in zip(a,b))
        return a==b
    if not close(compact_prediction(baseline),expected):raise ValueError('v10 complete baseline replay changed')


def materialize(root,target,structure,view,members,state,owners,result,identity):
    """Never deduplicate owners/state by RTL hash across different targets."""
    dest=root/f'T{target}-L3'/'selected';dest.mkdir(parents=True,exist_ok=True)
    for name in ('workload.sv','tb.sv','simulation.log'):
        (dest/name).write_bytes(members[view['directory']+'/'+name])
    write(dest/'graph.json',json.loads(members['graph.json']))
    write(dest/'state.json',state);write(dest/'owners.json',owners)
    entry_index,rank=map(int,result['best_variant_id'].split(':'))
    entry=result['trace'][entry_index]
    variant=next(v for v in entry['variants'] if v['id']==result['best_variant_id'])
    write(dest/'equivalent-requests.json',dict(identity=identity,target_ps=target,
        budget_sha256=entry['budget_sha256'],budgets_ps=entry['budgets_ps'],
        actual_queries=variant['actual_queries'],root_indices=variant['root_indices'],
        owner_queries_sha256=variant['owner_queries_sha256'],prediction=variant['prediction']))
    write(dest/'functional-inheritance.json',dict(identity=identity,
        status='inherited_identical_RTL_and_testbench',structure=structure,view=view['directory'],
        new_RTL_generated=False,new_simulation=False,
        files={n:sha(members[view['directory']+'/'+n]) for n in ('workload.sv','tb.sv','simulation.log')},
        qualification='preserves parent function/cycle/reset/stall receipt; no new physical claim'))


def run(root,*,verify_source=True,progress=True,output=None):
    root=Path(root);config=verify_inputs(root,check_source=verify_source)
    output=Path(output or root/'run');output.mkdir(parents=True,exist_ok=False)
    contract=read(root/'characterization-contract.json');bundle=read(root/'diagnostic-model.json')
    prices=DiagnosticPrices(bundle);references=read(root/'baseline-reference.json.gz')
    search=SearchConfig(**config['search']);inversion=InversionConfig(**config['inversion'])
    frozen={r['target_ps']:{(c['structure'],c['view']):c for c in r['selection']['candidates']} for r in references}
    summary=[];files={};counts=Counter();started=time.monotonic()
    for target in config['targets_ps']:
        candidates=[];baselines=[];selected_inputs={};target_start=time.monotonic()
        for structure in config['structures']:
            number=structure['structure'];members=old_structure('mac32',number)
            if {n:sha(d) for n,d in sorted(members.items())}!=structure['members_sha256']:
                raise ValueError('MAC32 candidate input changed')
            graph=Graph(json.loads(members['graph.json']));inventory=json.loads(members['inventory.json'])
            for view in inventory['views']:
                directory=view['directory'];owners=retarget(json.loads(members[directory+'/owners.json']),target)
                state=json.loads(members[directory+'/state.json']);state['features']['sdc_period_ps']=target
                if 'PASS' not in members[directory+'/simulation.log'].decode():raise ValueError('missing inherited functional pass')
                result=optimize(graph,view,state,owners,prices,contract,search=search,inversion=inversion)
                ref=frozen[target][number,directory]
                assert_reference(result['baseline'],ref['prediction'])
                if sha(members[directory+'/workload.sv'])!=ref['rtl_sha256']:
                    raise ValueError('original baseline RTL identity differs')
                best_entry=(result['trace'][int(result['best_variant_id'].split(':')[0])] if result['best_variant_id'] else None)
                best_variant=(next(v for v in best_entry['variants'] if v['id']==result['best_variant_id']) if best_entry else None)
                identity=dict(version=VERSION,case='mac32',structure=number,view=directory,T_clk_ps=target,L=3,II=1,
                    graph_sha256=owners['graph_sha256'],layout_sha256=owners['layout_sha256'],
                    RTL_sha256=sha(members[directory+'/workload.sv']),testbench_sha256=sha(members[directory+'/tb.sv']),
                    state_sha256=digest(state),global_owner_plan_sha256=digest(owners),
                    model_raw_sha256=config['baseline_model_raw_sha256'],
                    config_sha256=sha(canonical(config)),contract_sha256=sha(canonical(contract)),
                    budget_sha256=best_entry['budget_sha256'] if best_entry else None,
                    equivalent_queries_sha256=best_variant['owner_queries_sha256'] if best_variant else None,
                    actual_implementation_flow='unchanged whole-design asap7; local ABC targets not applied')
                identity['artifact_sha256']=sha(canonical(identity));result['identity']=identity
                name=f'T{target}-L3/structure-{number}-view-{directory}.json.gz'
                compressed(output/name,result);files[name]=sha((output/name).read_bytes())
                counts['candidates']+=1;counts['complete_variants']+=result['complete_variants']
                counts['baseline_operator_queries']+=len(owners['operators']);counts['baseline_G_queries']+=len(owners['G_regions'])
                counts['conversion_uncovered_proposals']+=sum(e.get('status')=='conversion_uncovered' for e in result['trace'])
                counts['transfer_proposals']+=sum(e.get('proposal','').startswith('transfer:') for e in result['trace'])
                counts['cost_uncovered_candidates']+=result['status']!='diagnostic_complete'
                counts['accepted_feedback_variants']+=sum(v['accepted_as_best'] and e['round']>0
                    for e in result['trace'] for v in e.get('variants',[]))
                counts['budgets_different_from_initial']+=bool(best_entry and
                    best_entry['budget_sha256']!=result['trace'][0].get('budget_sha256'))
                if result['status']=='diagnostic_complete':
                    candidates.append(dict(structure=number,view=directory,prediction=result['prediction'],
                                           artifact_sha256=identity['artifact_sha256'],receipt=name))
                baselines.append(dict(structure=number,view=directory,prediction=result['baseline']))
                selected_inputs[number,directory]=(view,state,owners,result,identity)
                if progress:
                    print(f'MAC32 T={target} structure={number} view={directory}: {result["status"]}, '
                          f'{result["complete_variants"]} complete variants, {result["stop_reason"]}',flush=True)
            Graph.origins.cache_clear();Graph.roots.cache_clear()
        if len(baselines)!=30 or set(frozen[target])!={(c['structure'],c['view']) for c in baselines}:
            raise ValueError('fixed candidate denominator changed')
        old=select(baselines);new=select(candidates) if candidates else dict(status='cost_uncovered')
        new.update(declared_candidates=30,cost_uncovered_candidates=30-len(candidates),
                   coverage_complete=len(candidates)==30)
        row=dict(T_clk_ps=target,L=3,baseline=old,equivalent=new)
        if candidates:
            key=(new['selected']['structure'],new['selected']['view']);v,s,o,r,i=selected_inputs[key]
            materialize(output,target,key[0],v,old_structure('mac32',key[0]),s,o,r,i)
            row['selected_artifact_sha256']=i['artifact_sha256']
        summary.append(row)
        write(output/f'T{target}-L3/selection.json',dict(row,candidates=[dict(c,prediction=compact_prediction(c['prediction'])) for c in candidates]))
        if progress:print(f'T={target} finished in {time.monotonic()-target_start:.2f}s; {new}',flush=True)
    report=dict(version=VERSION,status='software_steps_1_3_complete' if not counts['cost_uncovered_candidates'] else 'software_coverage_incomplete',
        qualified=False,model_reuse_precision_validated=False,targets=summary,counts=dict(counts),
        reference_replays=counts['candidates'],all_existing_candidates_scored=counts['candidates']==90,
        EDA_calls=0,operator_response_refits=0,new_RTL_generated=False,nine_case_ABCD_complete=False,
        actual_global_targets_preserved=True,budget_and_request_identity_bound=True,
        source_sha256=read(root/'inputs.json')['files']['software-source.json.gz'])
    write(output/'summary.json',report)
    # Bind target-specific materialized metadata, not just per-candidate scores.
    for path in sorted(output.rglob('*')):
        if path.is_file():files[str(path.relative_to(output))]=sha(path.read_bytes())
    write(output/'manifest.json',dict(version=VERSION,inputs_sha256=sha((root/'inputs.json').read_bytes()),
        files=files,wall_seconds=time.monotonic()-started))
    return report


def replay(root,output=None):
    root=Path(root);original=root/'run';manifest=read(original/'manifest.json')
    if sha((root/'inputs.json').read_bytes())!=manifest['inputs_sha256']:raise ValueError('input manifest changed')
    for name,expected in manifest['files'].items():
        if sha((original/name).read_bytes())!=expected:raise ValueError('stored result changed: '+name)
    result=run(root,progress=False,output=output)
    # Deterministic traces and complete scores, not just a copied summary.
    dest=Path(output or root/'run');recomputed=read(dest/'manifest.json')
    if manifest['files']!=recomputed['files']:raise ValueError('complete software replay differs')
    return dict(status='complete_replay_passed',files=len(manifest['files']),candidates=result['counts']['candidates'],
                new_EDA_calls=0,external_artifact_tree_needed=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('freeze','run','replay'))
    parser.add_argument('--root',type=Path,default=DEFAULT)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.action=='freeze':value=freeze(args.root)
    elif args.action=='run':value=run(args.root,output=args.output)
    else:
        if args.output is None:parser.error('replay requires a fresh --output directory')
        value=replay(args.root,args.output)
    print(json.dumps(value,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
