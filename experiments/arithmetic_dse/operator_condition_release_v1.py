"""Step-5 bounded node-function release, preserving all ancestor verdicts.

No fitting or physical optimization. Coefficients, trees, knots, semantic
support, neighbourhood and reserves are inherited unchanged. The released
target interval is the user requirement [500,3000] intersected with the frozen
support; it is a numerical interval, never a shape/view/source whitelist.
"""
import argparse
from copy import deepcopy
import json
import math
from pathlib import Path
import shutil

from .model_fast_preflight import read,write,sha,key
from . import operator_condition_model as inference,operator_collection as collection
from . import operator_condition_fit as fitting,operator_ownership_replay_v1 as physical
from . import model_logical_ownership_v2 as ownership,model_logical_labels_v1 as logical
from . import model_fast_sdc_v3 as sdc,backend
from .model_mapped_contract import mapped_contract,operator_port_contract
from .model_m2_live_cec_v3 import verify_proof
from .platforms import profile,verify_wire_readback

ROOT=Path(__file__).resolve().parents[2]
TARGETS=(500,1000,1500,3000)
RANGE=(500,3000)


def metrics(rows,entry):
    return {name:fitting.metrics(rows,entry[name],label,floor) for name,label,floor in
        (('delay','operator_delay_ps',10.),('area','comb_area_um2',.01))}


def restore_functional_identity(candidate,released):
    old,new=deepcopy(candidate),deepcopy(released)
    for bundle in (old,new):bundle.pop('quality_status',None);bundle.pop('release',None)
    for op in old['operations']:
        old['operations'][op].pop('status');new['operations'][op].pop('status')
        for name in ('target_period_ps','abc_target_ps','log2_target_ps'):
            if name in old['operations'][op]['domain']['numeric_support']:
                new['operations'][op]['domain']['numeric_support'][name]=old['operations'][op]['domain']['numeric_support'][name]
    if old!=new:raise ValueError('release changed coefficients, semantics, support or reserves')


def fresh_replay(fresh):
    a=read(fresh/'admission.json');report=read(fresh/'independent-result.json');progress=read(fresh/'progress.json')
    if report['status']!='passed_fresh_reader_function_check' or progress['failures'] or len(progress['completed'])!=16:
        raise ValueError('new independent collection not passed')
    if read(fresh/'resource-closure.json')['usage']['pending']:raise ValueError('fresh costs unsettled')
    for name,h in a['source_sha256'].items():
        if sha(ROOT/name)!=h or sha(fresh/'source'/name)!=h:raise ValueError('fresh frozen dependency changed '+name)
    manifest={r['id']:r for r in read(fresh/'sources.json')['sources']};rows=[];proofs=[]
    for task in a['tasks']:
        folder=fresh/'runs'/task['id'];c=read(folder/'query-contract.json');m=read(folder/'manifest.json');base=read(folder/'liberty-pins.json')
        if sha(Path(task['rtl']))!=task['rtl_sha256']:raise ValueError('fresh RTL changed')
        if mapped_contract(read(folder/'mapped.json'),task['features'],base)!=read(folder/'mapped-contract.json'):raise ValueError('FF bank proof differs')
        if operator_port_contract(read(folder/'mapped.json'),task['features'],base)!=read(folder/'operator-port-contract.json'):raise ValueError('operator port proof differs')
        verify_proof(folder/'logs'/physical.SUFFIX/'structural_cec/proof.json',folder/'results'/physical.SUFFIX/'4_before_rsz_lec.v',folder/'results'/physical.SUFFIX/'4_after_rsz_lec.v')
        for lib in m['libraries']:
            if sha(Path(lib['path']))!=lib['sha256']:raise ValueError('physical Liberty changed')
        for stage,stem in (('synth','1_synth'),('grt','5_1_grt')):
            label=read(folder/(stage+'-labels.json'));pins=dict(base)
            for line in (folder/'reports'/physical.SUFFIX/('vulsim_'+stage+'_cells.tsv')).read_text().splitlines():
                n,count,area,filler,kind=line.split('\t')
                if n not in pins:pins[n]=dict(sequential=False,buffer_or_inverter=False,physical_only=True,data_pins=[],pins={},area_um2=0 if filler=='1' else float(area))
            d=folder/('logical-'+stage);cert=read(d/'ownership-certificate.json');ports=read(d/'top-ports.json')
            replay=logical.read_snapshot(d/'context',task['period_ps'],1,pins,c['nodes'],c['banks'],top_ports=ports,ownership_certificate=cert)
            for k in ('nodes','operator_delay_ps','comb_area_um2','data_setup_slack_ps','owner_area_um2','total_cell_area_um2','path_decompositions'):
                if replay[k]!=label[k]:raise ValueError('fresh physical label replay differs '+task['id']+'/'+stage+'/'+k)
            if not label['physical_training_label_eligible'] or label['source_role']!='locked_test':raise ValueError('fresh eligibility or role differs')
            if label['CTS_CEC_sha256']!=sha(folder/'logs'/physical.SUFFIX/'structural_cec/proof.json'):raise ValueError('CEC identity changed')
            check=sdc.verify_sdc((folder/'results'/physical.SUFFIX/(stem+'.sdc')).read_text(),profile('asap7'),task['period_ps'],sdc.rtl_ports((folder/'input.sv').read_text(),'ModelBundle'),serialization_stage=stage)
            verify_wire_readback(folder/'reports'/physical.SUFFIX/('vulsim_'+stage+'_layer_rc.tsv'),profile('asap7'))
            if abs(replay['total_cell_area_um2']-label['metrics']['cell_area_um2'])>1e-5:raise ValueError('area ownership not conserved')
            proofs.append(dict(task=task['id'],stage=stage,label_sha256=sha(folder/(stage+'-labels.json')),owner_certificate_sha256=sha(d/'ownership-certificate.json'),
                recovered_cells=[dict(instance=r['instance'],owner=r['owner']) for r in cert['recovered']],stored_SDC_verified=True,CEC_verified=True,area_conserved=True))
        label=read(folder/'grt-labels.json');descriptor=collection.descriptor(manifest[task['source_id']],task['period_ps'])
        rows.append(dict(source_id=task['source_id'],target_ps=task['period_ps'],operation=descriptor['local_context']['producer']['operation'],role='locked_test',
            descriptor=descriptor,features=inference.features(descriptor),operator_delay_ps=label['operator_delay_ps'],comb_area_um2=label['comb_area_um2'],
            measurement_path=str(folder),label_sha256=sha(folder/'grt-labels.json')))
    for index in (fresh/'archives').glob('*.index.json'):
        d=read(index)
        if d['status']!='passed' or not d['actual_restore_and_every_member_hash_checked'] or sha(Path(d['archive']))!=d['archive_sha256']:
            raise ValueError('fresh artifact archive identity/restore differs')
    return rows,proofs


def prepare(out,node,fresh,recovery):
    if out.exists():raise ValueError('preserve release attempt')
    out.mkdir(parents=True)
    freeze=read(node/'fit-v2/selection-freeze.json');candidate=read(node/'fit-v2/candidate.json');old=read(node/'test-v2/independent-test.json')
    if sha(node/'fit-v2/candidate.json')!=freeze['model_sha256'] or sha(fresh/'frozen-function.json')!=freeze['model_sha256']:raise ValueError('numerical parent freeze differs')
    if read(recovery/'qualification.json')['status']!='passed_saved_snapshot_qualification' or read(recovery/'all-fitting-labels.json')['points']!=524:
        raise ValueError('ownership and complete fitting inheritance missing')
    if read(node/'v2-evidence-status.json')['phase']!='evidence_replay_and_resource_closure_passed':raise ValueError('ancestor evidence not settled')
    rows,proofs=fresh_replay(fresh)
    model=deepcopy(candidate);model['quality_status']='isolated_functions_passed'
    for op,e in model['operations'].items():
        e['status']='passed_independent';support=e['domain']['numeric_support']
        for name,interval in [('target_period_ps',RANGE),('abc_target_ps',RANGE),('log2_target_ps',tuple(math.log2(t) for t in RANGE))]:
            if name in support:support[name]=[max(support[name][0],interval[0]),min(support[name][1],interval[1])]
    model['release']=dict(version='operator-condition-node-release-v1',scope='ASAP7 unsigned Mul/Add node functions; existing semantic/numerical/joint-neighbour support intersect target interval',
        target_interval_ps=list(RANGE),qualified_exact_independent_targets_ps=list(TARGETS),parent_candidate_sha256=freeze['model_sha256'],
        ownership_reader='arithmetic-logical-ownership-v2-closed-islands',old_protocol_status=old['status'],
        full_ancestor_domain_qualified=False,stage_or_S_G_qualification=False,view_source_or_shape_whitelist=False)
    restore_functional_identity(candidate,model)
    inherited=read(node/'test-data.json')['rows'];independent=[r for r in inherited if r['stage']=='grt'];reports={}
    for op,e in model['operations'].items():
        group=[r for r in rows if r['operation']==op];stats=metrics(group,e);exact=metrics([r for r in group if r['target_ps']==1000],e)
        for k in ('delay','area'):
            if not stats[k]['passed'] or not exact[k]['passed']:raise ValueError('new independent quality failed')
            if stats[k]!=read(fresh/'independent-result.json')['operations'][op][k]:raise ValueError('fresh source-macro statistics changed')
        refused=[r for r in group if inference.query(model,r['descriptor'])['status']!='covered']
        if refused or len(group)!=8:raise ValueError('fresh release coverage incomplete')
        prior=[r for r in independent if r['operation']==op and RANGE[0]<=r['target_ps']<=RANGE[1]]
        if any(inference.query(model,r['descriptor'])['status']!='covered' for r in prior):raise ValueError('historical in-scope query rejected')
        reports[op]=dict(status='passed_bounded_node_release',fresh=stats,exact1000ps=exact,fresh_sources=2,fresh_points=8,
            fresh_refused=0,ancestor_full_verdict=old['operations'][op]['status'],ancestor_in_release_interval=dict(points=len(prior),**metrics(prior,e)),
            reserve_underpredictions=sum(inference.query(model,r['descriptor'])['conservative_operator_delay_ps']<r['operator_delay_ps'] for r in prior+group),
            reserve_is_empirical_not_a_proven_upper_bound=True)
    write(out/'operators.json',model);write(out/'fresh-data.json',dict(rows=rows,source_role='locked_test',never_fit_or_select=True))
    write(out/'physical-replay.json',dict(status='passed',stages=32,points=16,checks=proofs))
    write(out/'acceptance.json',dict(version='step5-node-release-acceptance-v1',status='passed_bounded_node_release',operations=reports,
        original_candidate_sha256=freeze['model_sha256'],released_model_sha256=sha(out/'operators.json'),target_interval_ps=list(RANGE),
        unchanged_predictors_reserves_semantic_and_joint_support=True,target_support_intersection_only=True,
        original_failed_independent_verdict_retained=True,all_prior_outcomes_in_denominator=True,
        historical_acquisition_failures=[dict(source='s32e03528a3472a5c',T=500,status='failed_in_ancestor_recovered_in_successor',
            fresh_repair_validation='new independent clones successfully processed without rule changes')],
        historical_out_of_domain=[dict(source=r['source_id'],T=r['target_ps'],reason=inference.query(candidate,r['descriptor'],True).get('reason','outside release interval'))
            for r in independent if not RANGE[0]<=r['target_ps']<=RANGE[1]],
        limited_four_source_new_independent_scope=True,no_new_full_domain_or_pipeline_claim=True,
        T_interpolation='continuous numeric query inside [500,3000] and unchanged joint support; four exact independent clocks validate interpolation, not every possible context',
        S_G_joint_qualified=False,full_D_ready=False))
    dependencies={str(p):sha(p) for p in [node/'fit-v2/candidate.json',node/'fit-v2/selection-freeze.json',node/'test-v2/independent-test.json',
        fresh/'admission.json',fresh/'independent-result.json',fresh/'resource-closure.json',recovery/'qualification.json',recovery/'all-fitting-labels.json']}
    write(out/'provenance.json',dict(version='operator-condition-node-release-provenance-v1',dependencies=dependencies,
        sources={n:sha(ROOT/n) for n in sorted(set(freeze['implementation_sources'])|{'experiments/arithmetic_dse/operator_condition_release_v1.py'})},
        raw_artifacts_retained=[str(node),str(fresh),str(recovery)],off_machine_backup=False,full_D_ready=False))
    # Continuous-clock software probes include an exact target absent from all
    # physical datasets, with no new physical label involved in selection.
    pool=[r for r in read(node/'fit-data.json')['rows'] if r['stage']=='grt']+independent+rows
    vectors=[dict(descriptor=r['descriptor'],allow_candidate=False,role=r['role'],target_ps=r['target_ps']) for r in pool]
    seen={r['target_ps'] for r in pool};unseen=next(t for t in range(1703,1900) if t not in seen)
    for r in rows:
        d=deepcopy(r['descriptor']);d['flow_context'].update(target_period_ps=unseen,abc_target_ps=unseen)
        vectors.append(dict(descriptor=d,allow_candidate=False,role='software_unseen_exact_T',target_ps=unseen))
    negatives=[];base=deepcopy(rows[0]['descriptor'])
    for t in (499,3001,3389,12000):
        d=deepcopy(base);d['flow_context'].update(target_period_ps=t,abc_target_ps=t);negatives.append(dict(name='outside_release_T_'+str(t),descriptor=d,allow_candidate=False))
    for name,change in [('incompatible_boundary',lambda d:d['flow_context'].update(boundary_policy='wrong')),
        ('wrong_profile',lambda d:d['flow_context'].update(profile_sha256='0'*64)),('posterior_feature',lambda d:d.update(slack_ps=0)),
        ('nonmatching_ABC',lambda d:d['flow_context'].update(abc_target_ps=777)),
        ('unknown_operation',lambda d:d['local_context']['producer'].update(operation='div')),
        ('too_many_consumers',lambda d:d['local_context']['consumers'].append(deepcopy(d['local_context']['consumers'][0]))),
        ('interior_known_zero',lambda d:d['local_context']['producer'].update(lhs_zero_hex='0x4'))]:
        d=deepcopy(base);change(d);negatives.append(dict(name=name,descriptor=d,allow_candidate=False))
    if any(inference.query(model,r['descriptor'])['status']!='cost_uncovered' for r in negatives):raise ValueError('release negative accepted')
    write(out/'native-input.json',dict(model=model,queries=vectors+negatives));write(out/'inference-manifest.json',dict(physical_vectors=len(pool),unseen_exact_target_ps=unseen,
        unseen_physical_labels_used=False,software_interpolation_vectors=len(rows),negative_controls=len(negatives),full_D_ready=False))
    print(dict(status='prepared_bounded_release',target_interval_ps=RANGE,fresh_physical_replay_stages=32,vectors=len(vectors)+len(negatives),full_D_ready=False),flush=True)


def verify(out):
    inputs=read(out/'native-input.json');native=read(out/'native-output.json');model=inputs['model'];m=read(out/'inference-manifest.json')
    if len(native)!=len(inputs['queries']):raise ValueError('native output missing')
    covered=0
    for q,a in zip(inputs['queries'],native,strict=True):
        p=inference.query(model,q['descriptor'],False)
        if p['status']!=a['status']:raise ValueError('Python/C++ coverage mismatch')
        if p['status']=='covered':
            covered+=1
            for key in ('operator_delay_ps','delay_reserve_ps','conservative_operator_delay_ps','comb_area_um2'):
                if not math.isclose(a[key],p[key],rel_tol=1e-10,abs_tol=1e-8):raise ValueError('Python/C++ price mismatch')
    if any(r['status']!='cost_uncovered' for r in native[-m['negative_controls']:]):raise ValueError('native negative accepted')
    write(out/'native-parity.json',dict(status='passed',queries=len(native),covered=covered,negative_rejections=m['negative_controls'],
        actual_release_model_sha256=sha(out/'operators.json'),candidate_permission_used=False,**m))
    print(dict(status='passed_release_native_parity',queries=len(native),covered=covered),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','verify'));p.add_argument('--out',type=Path,required=True)
    for n in ('node','fresh','recovery'):p.add_argument('--'+n,type=Path)
    a=p.parse_args()
    if a.action=='prepare':prepare(a.out.resolve(),a.node.resolve(),a.fresh.resolve(),a.recovery.resolve())
    else:verify(a.out.resolve())
