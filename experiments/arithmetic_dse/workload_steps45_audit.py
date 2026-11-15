"""Supplemental control/shared gates and deterministic portable step4/5 replay."""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path

from .sampling_time_contract import canonical,sha
from .workload_equivalent_run import read,write,compressed
from .workload_reuse_validation import DEFAULT,error_metrics


def publish_selection(root=DEFAULT):
    """Publish the best fully scored union candidate; preserve own-search arms.

    Both strategies' independent selections remain in the frozen experiment.
    Once both pools have been evaluated, the actual fallback must include every
    known complete candidate. This final union uses the preregistered common
    pool, with both price functions evaluated on exactly that same pool.
    """
    from .workload_guided_search import best,selected_variant
    from .workload_steps45_package import replay_data,artifact_files
    from .workload_equivalent_run import compact_prediction
    root=Path(root);data,input_sha=replay_data(root);files=artifact_files(root,data['rows'])
    output=root/'selected';output.mkdir(exist_ok=False);targets=[]
    for target in (500,750,1000):
        rows=[r for r in data['rows'] if r['target_ps']==target];winner=best(rows,'model');dest=output/f'T{target}-L3';dest.mkdir()
        prefix=winner['path'].removeprefix('search/')+'/'+winner['view']['directory']+'/'
        for name in ('workload.sv','tb.sv','state.json','owners.json','equivalent-requests.json','functional-receipt.json'):
            (dest/name).write_bytes(files[prefix+name])
        write(dest/'graph.json',winner['graph'])
        receipt=read(dest/'functional-receipt.json');simulation=receipt['directory'].removeprefix('search/')+'/simulation.log'
        (dest/'simulation.log').write_bytes(files[simulation])
        if sha((dest/'simulation.log').read_bytes())!=receipt['log_sha256']:
            raise ValueError('selected simulation receipt changed')
        e,v=selected_variant(winner['result'])
        identity=dict(candidate_id=winner['id'],scope='union of both preregistered equal-credit search arms',
            T_clk_ps=target,L=3,II=1,grammar=winner['grammar'],RTL_sha256=winner['rtl_sha256'],
            graph_sha256=sha(canonical(winner['graph'])),state_sha256=sha(canonical(winner['state'])),
            owner_plan_sha256=sha(canonical(winner['owners'])),budget_sha256=e['budget_sha256'],
            equivalent_queries_sha256=v['owner_queries_sha256'],
            model_sha256=sha((root/'diagnostic-model.json').read_bytes()),
            contract_sha256=sha((root/'characterization-contract.json').read_bytes()),
            protocol_sha256=sha((root/'protocol.json').read_bytes()),replay_inputs_sha256=input_sha,
            qualified=False,implementation='whole-design T; no local ABC constraints applied')
        write(dest/'identity.json',identity)
        old=best([r for r in rows if r['origin']=='fixed_seed'],'model')
        static=best(rows,'static')
        targets.append(dict(T_clk_ps=target,candidate_id=winner['id'],grammar=winner['grammar'],origin=winner['origin'],
            unique_candidates=len(rows),fixed_equivalent=compact_prediction(old['model']),
            final_common_pool=compact_prediction(winner['model']),
            static_common_pool=dict(candidate_id=static['id'],grammar=static['grammar'],prediction=compact_prediction(static['static'])),
            identity_sha256=sha(canonical(identity))))
    summary=dict(status='common_pool_selection_frozen',qualified=False,targets=targets,
        per_arm_per_target=dict(structure_credits=3,placement_credits=6,seed_views=30),
        actual_scored_scope='all 175 complete candidates, grouped by target',
        own_strategy_selections_preserved='search/summary.json',EDA_calls=0,application_PPA_read=False,
        selection_rule='feasible: minimum total area; otherwise minimum complete violation, area, stable ID',
        final_ABCD_physical_comparison_pending=True)
    write(output/'summary.json',summary)
    write(output/'manifest.json',dict(files={str(p.relative_to(output)):sha(p.read_bytes())
        for p in sorted(output.rglob('*')) if p.is_file()},replay_inputs_sha256=input_sha))
    return summary


def audit(root=DEFAULT):
    root=Path(root);inputs=read(root/'reuse-inputs.json.gz')
    components=read(root/'validation/components.json.gz');combinations=read(root/'validation/combinations.json.gz')
    control=[];area=[];stage=[];flow=[]
    raw={r['task']:r for r in inputs['combinations']}
    mappings={'input_valid':'input_valid','input_write_enable_proxy':'input_enable',
              'reset_port_proxy':'reset','native_enable':'native_enable',
              'native_valid':'native_valid','external_valid':'external_valid',
              'input_data_boundary_proxy':'input_data','output_port_boundary_proxy':'output_data'}
    for row in combinations['rows']:
        item=raw[row['task']];label=item['label'];p=row['equivalent_prediction'];paths=label['functional_paths']
        for c in p['S']['controls']:
            kind=mappings[c['path_class']]
            eligible=[v for v in paths if v['path_class']==kind and
                      (c['stage']<0 or c['stage']>=p['L'] or v['stage']==c['stage'])]
            if not eligible:continue
            # Whole-clock requirement under the original .2*T input/output
            # delays. Never compare I/O Q->D delay against an RR clock.
            alpha=.8 if kind in ('input_valid','input_enable','reset','input_data','output_data') else 1.
            actual=max((1500-v['slack_ps']-(1-alpha)*1500)/alpha for v in eligible)
            if actual<=0:raise ValueError('invalid complete control requirement')
            # Per-port proxies have no old path-to-port index in this archive;
            # their comparison uses the complete bank maximum, explicitly.
            control.append(dict(source=row['kind'],task=row['task'],path_class=c['path_class'],stage=c['stage'],
                actual_ps=actual,predicted_ps=c['required_ps'],error=c['required_ps']/actual-1,
                matching='bank max; per-port correspondence unavailable' if kind=='input_enable' else 'path class and stage',
                diagnostic_reserve_excluded=True,alpha=alpha))
        for owner,predicted in p['S']['area_owners_um2'].items():
            if owner in label['owner_area_um2'] and label['owner_area_um2'][owner]>0:
                actual=label['owner_area_um2'][owner]
                area.append(dict(source=row['kind'],task=row['task'],owner=owner,
                    actual_um2=actual,predicted_um2=predicted,error=predicted/actual-1))
        for s in row['stages']:
            stage.append(dict(source=row['kind'],task=row['task'],
                error=s['equivalent_predicted_ps']/s['measured_data_required_ps']-1,**s))
        metrics=label['whole_shell_metrics'];sdc=metrics.get('stored_SDC')
        flow.append(dict(task=row['task'],profile_sha256=metrics['platform_profile_sha256'],
            timing_coverage_complete=metrics['timing_coverage_complete'],
            strict_actual_Liberty_arcs=label['strict_actual_Liberty_arcs'],
            stored_SDC_status=sdc['status'] if sdc else 'not_embedded_in_legacy_serial_label',
            actual_ABC_target_receipt='archived original query; no new independent ABC readback',
            limitation='legacy hierarchy/timing adapter; new v2 embedded flow not certified'))
    response={}
    for metric in ('delay_ps','area_um2'):
        pairs=[p for p in components['response_pairs'] if p['metric']==metric]
        status=Counter('actual_tie' if p['actual_tie'] else 'predicted_tie' if p['predicted_tie'] else
                       'correct' if p['actual_response']*p['predicted_response']>0 else 'wrong' for p in pairs)
        response[metric]=dict(pairs=len(pairs),classification=dict(status),
            rule='5% band on both actual and predicted response; predicted ties are unresolved, not correct')
    gates={}
    for name in sorted({c['path_class'] for c in control}):
        gates['control/'+name]=error_metrics([c for c in control if c['path_class']==name],'error')
    for owner in sorted({a['owner'] for a in area}):
        gates['area/'+owner]=error_metrics([a for a in area if a['owner']==owner],'error')
    gates['complete_data_stage']=error_metrics(stage,'error')
    result=dict(status='supplementary_gates_complete',qualified=False,controls=control,area_owners=area,
        stages=stage,flow_compatibility=flow,response=response,gates=gates,
        failed_gates=[k for k,v in gates.items() if not v['gate_pass']],
        original_v10_failures_preserved=True,application_PPA_read=False,model_refitted=False)
    compressed(root/'validation/detail-gates.json.gz',result)
    write(root/'validation/detail-summary.json',dict(status=result['status'],qualified=False,
        failed_gates=result['failed_gates'],gates=gates,response=response,flow_compatibility=flow))
    return dict(status=result['status'],failed_gates=result['failed_gates'],response=response)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',nargs='?',default='audit',choices=['audit','publish'])
    p.add_argument('--root',type=Path,default=DEFAULT)
    args=p.parse_args();print(json.dumps(audit(args.root) if args.action=='audit' else publish_selection(args.root),ensure_ascii=False,indent=2))
