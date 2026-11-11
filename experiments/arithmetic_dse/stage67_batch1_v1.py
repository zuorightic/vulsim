"""Exactly four predeclared parallel/bypass validation measurements at 1500ps.

Physical producers, predictions and roles are frozen before collection. No
independent test, reserve calibration, parameter fitting or automatic retry.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import re
import shutil
from types import FunctionType,SimpleNamespace

from .model_fast_preflight import read,write,sha
from .budget import Ledger,POLICY,usage
from . import stage67_physical_probe_v1 as physical
from . import stage67_mapped_state_v2 as mapped
from .operator_condition_model import query,features

ROOT=Path(__file__).resolve().parents[2]
PREP=Path('/home/zyrv/vulsim-artifacts/stage7-physical-preparation-20261110-v5')
PARENT=Path('/home/zyrv/vulsim-artifacts/stage67-joint-20261111-v1')
OWNED=Path('/home/zyrv/vulsim-artifacts/stage67-accounting-20261111-v1')
NODE=ROOT/'experiments/arithmetic/models/asap7_conditional_operators_v1/operators.json'
BINDING=Path('/home/zyrv/vulsim-artifacts/conditional-boundary-20261110-v3/binding-candidate.json')
TIMING=OWNED/'validation-initial/candidate-calibrated.json'


def audit_demands(native,model):
    proof_path=Path('/home/zyrv/vulsim-artifacts/operator-condition-release-20261111-v1/public-consumer-v2/proof.json')
    proof=read(proof_path)
    if proof['published_model_sha256']!=sha(NODE) or proof['view_count']!=44:raise ValueError('MAC32 demand regression identity differs')
    descriptors=[p['descriptor'] for target in proof['targets'] for view in target['views'] for p in view['node_prices']]
    mac_features=[features(q) for q in descriptors]
    if any(query(model,q)['status']!='covered' for q in descriptors):raise ValueError('minimum MAC32 domain regressed')
    rows=[]
    for s in native['sources']:
        for v in s['variants']:
            target=next(t for t in v['targets'] if t['target_ps']==1500)
            for q in target['queries']:
                value=query(model,q['descriptor'])
                if value['status']=='covered':continue
                f=features(q['descriptor']);op=q['descriptor']['local_context']['producer']['operation'];domain=model['operations'][op]['domain']
                outside={k:dict(value=f[k],support=bounds,MAC32_range=[min(x[k] for x in mac_features if x['operation_'+op]),max(x[k] for x in mac_features if x['operation_'+op])])
                    for k,bounds in domain['numeric_support'].items() if not bounds[0]<=f[k]<=bounds[1]}
                rows.append(dict(source=s['source'],placement=v['id'],node=q['trace']['node'],reason=value['reason'],
                    producer=q['descriptor']['local_context']['producer'],numeric_gaps=outside,
                    disposition='retain refusal; outside currently needed MAC32 query domain; no support relaxation or per-view price'))
    return dict(version='stage67-minimum-demand-audit-v1',minimum_MAC32_queries=len(descriptors),minimum_views=44,
        exact_targets_ps=[t['T_ps'] for t in proof['targets']],minimum_queries_covered=True,MAC32_proof_sha256=sha(proof_path),
        refused_validation_queries_at_1500=rows,role='demand regression only, never shape whitelist',
        caveat='covered inventory proves these existing placements; larger reuse claims require their own evidence',
        new_node_fit_required_for_first_four_tasks=False,locked_test_labels_read=False,full_D_ready=False)


def admit(root):
    if root.exists():raise ValueError('preserve batch admission attempt')
    policy=read(TIMING);native_path=OWNED/'native-final/native.json';native=read(native_path);model=read(NODE)
    if sha(TIMING)!='1489c9caf94f1c9c676c5f5b439d09baefb77495154e6b7cfdb36d0262a59b07' or native['policy_sha256']!=sha(TIMING):raise ValueError('frozen owned timing identity changed')
    if native['model_sha256']!=sha(NODE) or sha(NODE)!=policy['operator_model_sha256'] or sha(BINDING)!=policy['S_binding_sha256']:raise ValueError('model/S dependency changed')
    later=dict(synth=688,grt=688,walltime_s=86400,CPU_time_s=172800,storage_bytes=30*1024**3)
    budget=dict(synth=4,grt=4,support=128,walltime_s=4*(300+1200)+128*120,CPU_time_s=4*(4*(300+1200)+128*120),storage_bytes=4*1024**3)
    state=read(Ledger().path);used=usage(state['entries']);limits=read(POLICY)['resources']
    # Admission itself runs in one paid support lease; its reservation is
    # included above. Ledger has already checked live kernel locks.
    if any(j['status']=='unsettled' for j in state.get('jobs',[])):raise ValueError('settle unfinished work before batch admission')
    if used['synth']+budget['synth']+later['synth']>limits['max_synthesis_calls'] or used['grt']+budget['grt']+later['grt']>limits['max_global_route_calls']:raise ValueError('physical calls not funded')
    if used['walltime_s']+budget['walltime_s']+later['walltime_s']>limits['max_global_walltime_h']*3600 or used['CPU_time_s']+budget['CPU_time_s']+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600:raise ValueError('time not funded')
    if shutil.disk_usage(root.parent).free<later['storage_bytes']+budget['storage_bytes']:raise ValueError('storage reserve not funded')
    demand=audit_demands(native,model);manifest=read(PREP/'structures.json');tasks=[]
    root.mkdir(parents=True);write(root/'demand-audit.json',demand)
    for kind in ('parallel','bypass'):
        source=read(PREP/'sources'/kind/'request.json');export=read(PARENT/'software'/kind/'export.json');actual=next(s for s in native['sources'] if s['source']==kind)
        if source['role']!='combination_validation':raise ValueError('locked source forbidden')
        for v in actual['variants']:
            target=next(t for t in v['targets'] if t['target_ps']==1500);score=target['owned_timing']
            if score['status']!='candidate_covered' or score['G_delay_ps']!=0 or score['full_D_ready']:raise ValueError('uncovered or qualified price cannot enter batch')
            row=next(r for r in manifest['rows'] if r['source']==kind and r['placement']==v['id'])
            text=(PREP/row['rtl']).read_text();tops=re.findall(r'\bmodule\s+(Stage7_\w+)\s*\(',text)
            if len(tops)!=1 or sha(PREP/row['rtl'])!=row['rtl_sha256']:raise ValueError('prepared RTL changed')
            old=next(x for x in export['variants'] if x['id']==v['id'])
            if old['placement']!=v['placement'] or row['graph_sha256']!=v['graph']['graph_sha256']:raise ValueError('real graph/placement changed')
            task_id=kind+'-'+v['id']+'-T1500';directory=root/'inputs'/task_id;directory.mkdir(parents=True)
            rtl=directory/'input.sv';rtl.write_text(text.replace('module '+tops[0]+'(','module ModelBundle('));contract=directory/'endpoints.json';shutil.copy2(PREP/row['endpoint_contract'],contract)
            write(directory/'source.json',source);write(directory/'export.json',export)
            prices=[dict(node=q['trace']['node'],**query(model,q['descriptor'])) for q in target['queries']]
            write(directory/'prediction.json',dict(version='stage67-frozen-premeasurement-v1',source=kind,placement=v['id'],target_ps=1500,
                model_sha256=sha(NODE),S_binding_sha256=sha(BINDING),timing_policy_sha256=sha(TIMING),prices=prices,owned_timing=score,
                graph=v['graph'],cuts=v['cuts'],state=v['state'],queries=target['queries'],placement_selected_before_prices=True,
                reserve_fixed_ps=50,parameters_calibrated_from_batch=False,full_D_ready=False))
            tasks.append(dict(id=task_id,source=kind,placement=v['id'],source_role='combination_validation',period_ps=1500,
                rtl=str(rtl),rtl_sha256=sha(rtl),prepared_rtl_sha256=row['rtl_sha256'],top_rename_only=True,
                endpoint_contract=str(contract),endpoint_sha256=sha(contract),input_directory=str(directory),prediction_sha256=sha(directory/'prediction.json')))
    if len(tasks)!=4:raise ValueError('exact four tasks required')
    from .operator_collection import measurement_sources
    names=set(measurement_sources())|{str(p.relative_to(ROOT)) for p in (Path(__file__),Path(physical.__file__),Path(mapped.__file__))}
    names|={'experiments/arithmetic_dse/stage67_mapped_state_v1.py','experiments/arithmetic_dse/stage67_state_semantics_v1.py',
        'experiments/arithmetic_dse/stage67_physical_readout_v1.py','experiments/arithmetic_dse/stage67_analyze_v1.py',
        'experiments/arithmetic_dse/reference_assets/stage67_context_v1.tcl','experiments/arithmetic_dse/reference_assets/stage7_readout_v1.tcl'}
    hashes={}
    for name in sorted(names):
        destination=root/'source'/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,destination);hashes[name]=sha(destination)
    write(root/'timing-policy.json',policy)
    write(root/'admission.json',dict(version='stage67-combination-validation-batch1-v1',id=root.name,tasks=tasks,created_at=datetime.now(timezone.utc).isoformat(),
        model=dict(path=str(NODE),sha256=sha(NODE)),S_binding=dict(path=str(BINDING),sha256=sha(BINDING)),
        timing_policy=dict(path=str(TIMING),sha256=sha(TIMING)),native_prediction=dict(path=str(native_path),sha256=sha(native_path)),
        sources=hashes,synth_max=4,grt_max=4,support_max=128,synth_timeout_s=300,grt_timeout_s=1200,
        automatic_retries=0,parallel_jobs=1,threads=4,memory_limit_MiB=8192,later_work_reserved=later,batch_budget=budget,
        parent=str(PARENT),preparation=str(PREP),point_error_gates=dict(median=.15,P95=.35,per_class_P95=.50),
        area_error_gates=dict(median=.15,P95=.35),false_feasible_max=0,rank_tie_area_relative=.05,rank_tie_violation_ps=5,
        hold='separately report; TT setup-only grt ranking inherited; negative or below5ps marks review_required',
        reserve_update_allowed=False,locked_joint_tests_unlocked=False,full_D_ready=False))
    write(root/'progress.json',dict(phase='admitted',completed=[],errors=[],active=None))
    print(dict(status='admitted_exact_batch1',tasks=[t['id'] for t in tasks],synth_max=4,grt_max=4,support_max=128,
        MAC32_covered_queries=demand['minimum_MAC32_queries'],refused_validation_queries=len(demand['refused_validation_queries_at_1500']),new_node_fit=False,full_D_ready=False),flush=True)


class BatchLedger(physical.PilotLedger):
    def reserve(self,stage,*args,**kwargs):
        a=read(self.root/'admission.json')
        for key in ('timing_policy','native_prediction'):
            if sha(a[key]['path'])!=a[key]['sha256']:raise ValueError('frozen candidate changed before measurement')
        if sha(Path(self.task['input_directory'])/'prediction.json')!=self.task['prediction_sha256'] or sha(self.task['endpoint_contract'])!=self.task['endpoint_sha256']:raise ValueError('prediction/endpoints changed')
        return super().reserve(stage,*args,**kwargs)


def run(root):
    a=read(root/'admission.json');progress=read(root/'progress.json')
    if progress['errors']:raise ValueError('preserve failed batch; no automatic retry')
    for task in a['tasks']:
        if task['id'] in progress['completed']:continue
        if (root/'runs'/task['id']).exists():raise ValueError('prior physical attempt cannot repeat')
        progress.update(phase='running',active=task['id']);write(root/'progress.json',progress)
        try:
            def verify(d,pins,c,s):return mapped.verify(d,pins,c,s,Path(task['rtl']).read_text())
            namespace=dict(physical.point.__globals__);namespace.update(mapped=SimpleNamespace(verify=verify),PilotLedger=BatchLedger)
            FunctionType(physical.point.__code__,namespace)(root,task)
        except Exception as error:
            progress['errors'].append(dict(task=task['id'],reason=str(error)));progress.update(phase='stopped_on_error',active=None);write(root/'progress.json',progress);raise
        progress['completed'].append(task['id']);progress.update(phase='point_settled',active=None);write(root/'progress.json',progress)
    progress['phase']='physical_batch_complete';write(root/'progress.json',progress)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('admit','run'));p.add_argument('--root',type=Path,required=True);a=p.parse_args()
    if a.action=='admit':admit(a.root.resolve())
    else:run(a.root.resolve())
