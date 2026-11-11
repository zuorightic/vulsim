"""Exactly nine structurally selected alternate-placement measurements.

Admitted only after the inherited nine full-stage validation gate passes.
Node/S/shared coefficients, support, reserve and selector remain frozen.
"""
import argparse
from copy import deepcopy
from datetime import datetime,timezone
import inspect
import math
from pathlib import Path
import re
import shutil
from types import FunctionType

from .model_fast_preflight import read,write,sha
from .budget import Ledger,POLICY,usage
from . import stage67_shared_collect_v1 as shared
from . import stage67_paired_prepare_v1 as prepare
from . import stage67_multiclock_v1 as stage


def admit(root,first):
    if root.exists():raise ValueError('preserve paired physical admission')
    initial=read(first/'analysis-v1/validation.json')
    if initial['status']!='passed_full_stage_validation_pending_ranking' or initial['failures'] or initial['false_feasible_count']:raise ValueError('first full-stage gate did not pass')
    software=first/'paired-software';simulation=read(software/'simulation.json');native=read(first/'paired-native/native.json');parity=read(first/'paired-parity/parity.json')
    if simulation['status']!='passed' or parity['counts']!={'candidate_covered':21}:raise ValueError('alternate software coverage/simulation missing')
    for n,h in read(stage.FREEZE)['files'].items():
        if sha(n)!=h:raise ValueError('frozen model/inference drift '+n)
    root.mkdir(parents=True);protocol=read(software/'protocol.json');tasks=[];later=read(first/'admission.json')['later_work_reserved']
    for row in read(software/'structures.json')['rows']:
        r=read(software/'sources'/row['source']/'request.json');source=next(s for s in native['sources'] if s['source']==row['source']);variant=source['variants'][0]
        if r['role']!='validation' or variant['id']!='placement-1':raise ValueError('only three existing validation sources alternate placement allowed')
        for t in (500,1500,3000):
            ident=row['source']+'-placement-1-T'+str(t);d=root/'inputs'/ident;d.mkdir(parents=True)
            text=Path(row['rtl']).read_text();tops=re.findall(r'\bmodule\s+(Stage7_\w+)\s*\(',text)
            if len(tops)!=1 or sha(row['rtl'])!=row['rtl_sha256']:raise ValueError('prepared RTL drift')
            rtl=d/'input.sv';rtl.write_text(text.replace('module '+tops[0]+'(','module ModelBundle('))
            original=Path(row['native'])
            for name in ('export.json','features.json','endpoints.json'):shutil.copy2(original/name,d/name)
            write(d/'source.json',r);target=next(x for x in variant['targets'] if x['target_ps']==t)
            if target['owned_timing']['status']!='candidate_covered':raise ValueError('uncovered alternate price')
            v=stage.complete_variant(variant['graph'],variant)
            prices=[dict(node=q['trace']['node'],**stage.query(read(stage.NODE),q['descriptor'])) for q in target['queries']]
            pred=dict(source=r['id'],role='validation',placement='placement-1',target_ps=t,graph=v['graph'],cuts=v['cuts'],state=v['state'],queries=target['queries'],prices=prices,
                owned_timing=target['owned_timing'],model_sha256=sha(stage.NODE),S_binding_sha256=sha(stage.BINDING),policy_sha256=sha(stage.POLICY_PATH),
                placement_selected_before_prices=True,full_D_ready=False)
            prediction=d/'prediction.json';write(prediction,pred)
            tasks.append(dict(id=ident,source=r['id'],source_role='validation',placement='placement-1',period_ps=t,rtl=str(rtl),rtl_sha256=sha(rtl),
                endpoint_contract=str(d/'endpoints.json'),endpoint_sha256=sha(d/'endpoints.json'),input_directory=str(d),prediction=str(prediction),prediction_sha256=sha(prediction)))
    if len(tasks)!=9:raise ValueError('exact nine preregistered requests required')
    budget=dict(synth=9,grt=9,support=144,walltime_s=9*1500+144*120,CPU_time_s=4*(9*1500+144*120),storage_bytes=3*1024**3)
    used=usage(read(Ledger().path)['entries']);limits=read(POLICY)['resources']
    if used['synth']+9+688>limits['max_synthesis_calls'] or used['grt']+9+688>limits['max_global_route_calls'] or used['walltime_s']+budget['walltime_s']+86400>limits['max_global_walltime_h']*3600 or used['CPU_time_s']+budget['CPU_time_s']+172800>limits['max_tool_CPU_time_h']*3600 or shutil.disk_usage(root).free<later['storage_bytes']+budget['storage_bytes']:raise ValueError('alternate batch and later reserve not funded')
    from .operator_collection import measurement_sources
    names=set(measurement_sources())|{str(Path(m.__file__).relative_to(stage.ROOT)) for m in (shared,prepare,stage)}
    names|={str(Path(__file__).relative_to(stage.ROOT)),'experiments/arithmetic_dse/model_m2_live_cec_v4.py',
        'experiments/arithmetic_dse/stage67_physical_probe_v1.py','experiments/arithmetic_dse/stage67_mapped_state_v1.py','experiments/arithmetic_dse/stage67_mapped_state_v2.py','experiments/arithmetic_dse/stage67_mapped_state_v3.py',
        'experiments/arithmetic_dse/stage67_shared_fit_v1.py','experiments/arithmetic_dse/stage7_physical_prepare.py',
        'experiments/arithmetic_dse/stage67_state_semantics_v1.py','experiments/arithmetic_dse/stage67_state_semantics_v2.py',
        'experiments/arithmetic_dse/reference_assets/stage67_context_v1.tcl','experiments/arithmetic_dse/reference_assets/stage7_readout_v1.tcl'}
    hashes={}
    for n in sorted(names):
        p=root/'source'/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(stage.ROOT/n,p);hashes[n]=sha(p)
    write(root/'admission.json',dict(version='frozen-paired-stage-physical-v1',id=root.name,tasks=tasks,sources=hashes,
        model=dict(path=str(stage.NODE),sha256=sha(stage.NODE)),S_binding=dict(path=str(stage.BINDING),sha256=sha(stage.BINDING)),
        protocol_path=str(software/'protocol.json'),protocol_sha256=sha(software/'protocol.json'),freeze_path=str(stage.FREEZE),freeze_sha256=sha(stage.FREEZE),
        first_stage_gate_path=str(first/'analysis-v1/validation.json'),first_stage_gate_sha256=sha(first/'analysis-v1/validation.json'),
        synth_max=9,grt_max=9,support_max=144,synth_timeout_s=300,grt_timeout_s=1200,automatic_retries=0,threads=4,parallel_jobs=4,memory_limit_MiB=8192,
        batch_budget=budget,later_work_reserved=later,parameters_changed=False,reserve_ps=50,independent_tests_unlocked=False,full_D_ready=False,created_at=datetime.now(timezone.utc).isoformat()))
    write(root/'progress.json',dict(phase='admitted',completed=[],errors=[],active=[]));print('ALTERNATE_PHYSICAL_ADMITTED requests=9 new_sources=0 first_gate=passed',flush=True)


class PairedLedger(shared.SharedLedger):
    def reserve(self,stage_name,*args,**kwargs):
        a=read(self.root/'admission.json')
        if sha(a['first_stage_gate_path'])!=a['first_stage_gate_sha256'] or sha(self.task['prediction'])!=self.task['prediction_sha256']:raise ValueError('first-stage gate or frozen alternate prediction drift')
        return super().reserve(stage_name,*args,**kwargs)


def point(root,task):
    # Same reviewed numerical-T physical producer; only the task and Ledger
    # dependencies change. No fit or alternative physical mapping strategy.
    text=inspect.getsource(shared.point).replace('PilotLedger=SharedLedger','PilotLedger=PairedLedger')
    ns=dict(shared.point.__globals__);ns['PairedLedger']=PairedLedger
    exec(compile(text,__file__,'exec'),ns);ns['point'](root,task)


def run(root):
    ns=dict(shared.run.__globals__);ns['point']=point;FunctionType(shared.run.__code__,ns)(root)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('admit','run'));p.add_argument('--root',type=Path,required=True);p.add_argument('--first',type=Path);a=p.parse_args()
    if a.action=='admit':admit(a.root.resolve(),a.first.resolve())
    else:run(a.root.resolve())
