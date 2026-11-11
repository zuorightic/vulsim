"""Successor fitting lifecycle: frozen physical labels, shared numerical f(x,T)."""
import argparse
from collections import Counter
from copy import deepcopy
import json
import math
from pathlib import Path
import shutil
from types import FunctionType

from .model_fast_preflight import read,write,sha,key
from . import operator_condition_fit as base
from . import operator_condition_model as model
from . import operator_condition_wide as wide
from . import operator_collection as collect

ROOT=Path(__file__).resolve().parents[2]
CONFIG=wide.FIT_PROTOCOL
FEATURE=wide.FEATURE_PROTOCOL
DOMAIN=Path(__file__).with_name('configs')/'operator_condition_domain_v6.json'
DOMAIN_PARENT=DOMAIN.with_name('operator_condition_domain_v5.json')
DOMAIN_BASE=DOMAIN.with_name('operator_condition_domain_v3.json')
DOMAIN_ANCESTOR=DOMAIN.with_name('operator_condition_domain_v2.json')


def policy():
    result={}
    for version in range(3,7):result.update(read(DOMAIN.with_name('operator_condition_domain_v'+str(version)+'.json')))
    return result


def source_names():
    required=set(read(CONFIG)['required_freeze_sources'])
    required.update(str(p.relative_to(ROOT)) for p in (Path(__file__),DOMAIN,DOMAIN_PARENT,DOMAIN_BASE,DOMAIN_ANCESTOR,Path(wide.__file__),wide.POLICY,collect.scan.CONFIG,Path(collect.scan.__file__)))
    required.add(str(DOMAIN.with_name('operator_condition_domain_v4.json').relative_to(ROOT)))
    required.add('regression/arithmetic_condition_v2.py')
    required.add('experiments/arithmetic_dse/operator_condition_v2_run.py')
    return sorted(required)


def extract(root,out,mode='fitting',selection=None):
    if out.exists():raise ValueError('preserve prior dataset snapshot')
    if mode!='fitting':wide.verify_selection(root/'corpus',selection)
    namespace=dict(base.extract.__globals__)
    namespace.update(CONFIG=CONFIG,FEATURE_CONFIG=FEATURE,collect=wide.adapter(root/'corpus'))
    fn=FunctionType(base.extract.__code__,namespace)
    result=fn(root,out,mode,selection)
    result.update(extraction_implementation='operator-condition-extract-v2',extraction_producer_sha256=sha(Path(__file__)),
        domain_protocol_sha256=sha(DOMAIN),diagnostic_partial=False,
        history_sha256={r['source_id']:sha(root/'raw'/r['source_id']/'history.json') for r in result['coverage']})
    sources={s['id']:s for s in read(root/'corpus/manifest.json')['sources']}
    for row in result['coverage']:
        source=sources[row['source_id']];history=read(root/'raw'/source['id']/'history.json')
        guards=read(wide.POLICY)['new_source_guard_targets_ps'][source['role']] if source.get('sampling_policy')=='operator-wide-load-sampling-v1' else []
        measured={p['SDC_ps'] for p in history if p['status']=='completed'}
        row.update(required_clock_guards_ps=guards,missing_clock_guards_ps=[t for t in guards if t not in measured])
    write(out,result);return result


def snapshot(root,out):
    """Settled-prefix diagnosis, explicitly unable to authorize independent test."""
    if out.exists():raise ValueError('preserve diagnostic snapshot')
    if read(root/'progress.json')['phase']=='running':raise ValueError('settled snapshot required')
    manifest=read(root/'corpus/manifest.json');rows=[];coverage=[];failures=[];hashes={};histories={}
    proxy=wide.adapter(root/'corpus')
    for source in manifest['sources']:
        if source['role']=='locked_test':continue
        path=root/'raw'/source['id']/'history.json'
        if not path.exists():raise ValueError('source not started; use diagnostic snapshot after first coverage batch')
        history=read(path);hashes[source['id']]=sha(path);histories[source['id']]=history
        d=proxy.next_request(root/'corpus',source['id'],history)['decision']
        coverage.append(dict(source_id=source['id'],role=source['role'],operation=source['features']['producer']['operation'],
            regions=d['regions'],stop_reason=d['stop_reason'],coverage_shortfall=d['coverage_shortfall'],pending=d['next_request'] is not None))
        for point in history:
            if point['status']=='failed':failures.append(point);continue
            folder=path.parent/('target-'+str(point['SDC_ps']))/'runs'/(source['id']+'-T'+str(point['SDC_ps']))
            if sha(folder/'grt-labels.json')!=point['implementation_id']:raise ValueError('saved point changed')
            q=collect.descriptor(source,point['SDC_ps']);f=model.features(q)
            for stage in ('synth','grt'):
                label=read(folder/(stage+'-labels.json'))
                if label['source_role']!=source['role'] or not label['physical_training_label_eligible']:raise ValueError('saved qualification or role changed')
                rows.append(dict(id=source['id']+'/T'+str(point['SDC_ps'])+'/'+stage,source_id=source['id'],source_group=source['source_group'],
                    role=source['role'],operation=source['features']['producer']['operation'],stage=stage,target_ps=point['SDC_ps'],
                    features=f,descriptor=q,operator_delay_ps=label['operator_delay_ps'],comb_area_um2=label['comb_area_um2'],
                    data_setup_slack_ps=label['data_setup_slack_ps'],label_sha256=sha(folder/(stage+'-labels.json')),measurement_path=str(folder)))
    result=dict(version='operator-conditional-dataset-v1',mode='fitting',collection_root=str(root),source_manifest_sha256=sha(root/'corpus/manifest.json'),
        protocol_sha256=sha(root/'corpus/protocol.json'),fit_protocol_sha256=sha(CONFIG),feature_protocol_sha256=sha(FEATURE),
        feature_producer_sha256=sha(Path(model.__file__)),domain_protocol_sha256=sha(DOMAIN),rows=rows,coverage=coverage,failures=failures,
        history_sha256=hashes,history_prefixes=histories,diagnostic_partial=True,raw_labels_replayed=False,independent_labels_read=False)
    write(out,result);print(dict(status='diagnostic_snapshot',points=len(rows)//2,pending_sources=sum(r['pending'] for r in coverage)),flush=True)


def validate(data,mode):
    if (data['fit_protocol_sha256']!=sha(CONFIG) or data['feature_protocol_sha256']!=sha(FEATURE)
        or data.get('domain_protocol_sha256')!=sha(DOMAIN)):
        raise ValueError('v2 dataset protocol differs')
    root=Path(data['collection_root'])
    if data.get('diagnostic_partial') and data.get('history_prefixes'):
        prefixes={root/'raw'/sid/'history.json':history for sid,history in data['history_prefixes'].items()}
        for path,history in prefixes.items():
            if read(path)[:len(history)]!=history:raise ValueError('diagnostic history prefix changed')
        namespace=dict(base.validate_snapshot.__globals__)
        namespace['read']=lambda path:prefixes[Path(path)] if Path(path) in prefixes else read(path)
        check=FunctionType(base.validate_snapshot.__code__,namespace);check(data,mode)
        return
    base.validate_snapshot(data,mode)
    for sid,h in data['history_sha256'].items():
        if sha(root/'raw'/sid/'history.json')!=h:raise ValueError('dataset histories changed after snapshot')


def tags(row,new_ids):
    f=row['features']
    return dict(wide_consumer=max(f['consumer_lhs_max'],f['consumer_rhs_max'],f['consumer_result_max'])>f['result_width']+1,
        shifted_connection=f['mapping_shift_min']!=0 or f['mapping_shift_max']!=0,
        new_source=row['source_id'] in new_ids,low_result=bool(f['low_result']),capture=bool(f['capture_banks']),
        unseen_training_shape=row.get('unseen_training_shape',False),unseen_fitting_shape=row.get('unseen_fitting_shape',False))


def subsets(rows,entry,new_ids):
    result={}
    for name in ('wide_consumer','shifted_connection','new_source','low_result','capture','unseen_training_shape','unseen_fitting_shape'):
        local=[r for r in rows if tags(r,new_ids)[name]]
        result[name]=dict(rows=len(local),sources=len({r['source_id'] for r in local}),
            delay=base.metrics(local,entry['delay'],'operator_delay_ps',10.),
            area=base.metrics(local,entry['area'],'comb_area_um2',.01))
    return result


def clock_statistics(rows,entry):
    return {str(t):dict(rows=sum(r['target_ps']==t for r in rows),
        delay=base.metrics([r for r in rows if r['target_ps']==t],entry['delay'],'operator_delay_ps',10.),
        area=base.metrics([r for r in rows if r['target_ps']==t],entry['area'],'comb_area_um2',.01)) for t in (500,1000,1500,3000)}


def choose(train,validation,field,names,floor,new_ids,allow_groups=True):
    trials=[]
    def score(name,predictor):
        quality=base.metrics(validation,predictor,field,floor)
        critical={tag:base.metrics([r for r in validation if tags(r,new_ids)[tag]],predictor,field,floor)
            for tag in policy()['critical_validation_subdomains']}
        passed=quality['passed'] and all(q['passed'] for q in critical.values() if q['sources']>=2)
        rank=(not passed,quality['source_macro_normalized_absolute_error'],len(json.dumps(predictor)),len(trials))
        trials.append(dict(name=name,predictor=predictor,quality=quality,critical_quality=critical,rank=rank))
    for name,p in base.candidates(train,field,names,floor):score(name,p)
    selected=min(trials,key=lambda t:t['rank'])
    if selected['rank'][0] and allow_groups:
        groups={}
        for group,small in (('small',True),('large',False)):
            tr=[r for r in train if (max(r['features']['lhs_width'],r['features']['rhs_width'])<=16)==small]
            va=[r for r in validation if (max(r['features']['lhs_width'],r['features']['rhs_width'])<=16)==small]
            if len({r['source_id'] for r in tr})<3 or len({r['source_id'] for r in va})<2:break
            chosen,_=choose(tr,va,field,names,floor,new_ids,False)
            groups[group]=chosen['predictor']
        if len(groups)==2:
            score('validated-width-groups-16',dict(kind='width_grouped',split=16,groups=groups))
            selected=min(trials,key=lambda t:t['rank'])
    return selected,[{k:v for k,v in t.items() if k!='rank'} for t in trials]


def domain(entry,train,valid,kind):
    cfg=policy();group=train+valid
    names=cfg['intrinsic_numeric_features'][:]
    if kind!='legacy_narrow_load':names+=cfg['consumer_numeric_features']
    numeric={n:[min(r['features'][n] for r in train),max(r['features'][n] for r in train)] for n in names}
    for n in ('consumer_count','capture_banks'):
        numeric[n]=[min(r['features'][n] for r in train),max(r['features'][n] for r in train)]
    if kind!='legacy_narrow_load':
        for n in cfg['one_bit_padding_features']:numeric[n][1]+=1
        for pair in (('consumer_lhs_max','consumer_rhs_max'),('consumer_lhs_active_bits','consumer_rhs_active_bits')):
            maximum=max(numeric[n][1] for n in pair)
            for n in pair:numeric[n][1]=maximum
        width=max(numeric[n][1] for n in ('consumer_lhs_max','consumer_rhs_max','consumer_result_max'))
        for n in ('consumer_lhs_zero_lsb_run','consumer_rhs_zero_lsb_run','consumer_lhs_zero_msb_run','consumer_rhs_zero_msb_run','consumer_add_overlap_bits'):
            numeric[n]=[0,width]
        numeric['consumer_add_carry_span']=[0,numeric['consumer_result_max'][1]]
        for n in ('mapping_shift_min','mapping_shift_max'):
            numeric[n][0]-=1;numeric[n][1]+=1
    numeric['target_period_ps']=[min(r['target_ps'] for r in group),max(r['target_ps'] for r in group)]
    result=dict(numeric_support=numeric,semantics='unsigned modulo; contiguous live intervals, zero carry; one Add consumer or direct capture',
        support_method=kind,domain_protocol_sha256=sha(DOMAIN))
    if kind=='legacy_narrow_load':
        result['local_load_family']='legacy: at most result width plus one; at most two direct banks'
        distance=['lhs_width','rhs_width','result_width','lhs_zero_count','rhs_zero_count','consumer_count','capture_banks']
    else:distance=cfg['joint_features'][:]
    point_clock=kind in ('joint_requested_clock','joint_clock_source_radius','physical_load_joint_clock')
    if kind=='physical_load_joint_clock':distance=cfg['physical_load_joint_clock']['joint_features'][:]
    if point_clock:distance.append('log2_target_ps')
    scales=[max(1.,max(r['features'][n] for r in train)-min(r['features'][n] for r in train)) for n in distance]
    vectors=[];anchors=[]
    if point_clock:
        for row in sorted(group,key=lambda r:(r['source_id'],r['target_ps'])):
            vector=[row['features'][n] for n in distance]
            anchors.append(dict(vector=vector,clock_ratio_min=0.,clock_ratio_max=numeric['target_period_ps'][1]/10.))
            if row['role']=='train':vectors.append(vector)
    for sid in sorted({r['source_id'] for r in group}):
        if point_clock:break
        local=[r for r in group if r['source_id']==sid];f=local[0]['features'];vector=[f[n] for n in distance]
        ref=dict(f,target_period_ps=1500.,abc_target_ps=1500.,log2_target_ps=math.log2(1500.))
        d=max(10.,model.infer(entry['delay'],ref));ratios=[r['target_ps']/d for r in local]
        anchors.append(dict(vector=vector,clock_ratio_min=min(ratios),clock_ratio_max=max(ratios)))
        if local[0]['role']=='train':vectors.append(vector)
    k=min(cfg['joint_k'],len(vectors));radius=0.
    for row in valid:
        def measure(vector):return math.sqrt(sum(((row['features'][n]-v)/s)**2 for n,v,s in zip(distance,vector,scales,strict=True)))
        if kind in ('joint_clock_source_radius','physical_load_joint_clock'):
            ds=sorted(min(measure([r['features'][n] for n in distance]) for r in train if r['source_id']==sid) for sid in {r['source_id'] for r in train})
        else:ds=sorted(measure(vector) for vector in vectors)
        radius=max(radius,ds[k-1])
    # Repeated numerical witnesses are harmless but contain no source identity.
    result['joint_support']=dict(features=distance,scales=scales,k=k,radius=radius,anchors=anchors,
        reference_target_ps=1500.,reference_floor_ps=10.,basis=cfg['joint_radius']+'; numerical witnesses only, no measured prices')
    if kind in ('joint_clock_source_radius','physical_load_joint_clock'):result['joint_support']['basis']=cfg['joint_clock_source_radius']['radius_calibration']
    return result


def coverage(bundle,rows):
    accepted=[];reasons=Counter()
    for r in rows:
        a=model.query(bundle,r['descriptor'],True)
        if a['status']=='covered':accepted.append(r)
        else:reasons[a['reason']]+=1
    return dict(total=len(rows),accepted=len(accepted),refused=len(rows)-len(accepted),refusal_reasons=dict(reasons),
        errors_on_accepted={op:{label:base.metrics([r for r in accepted if r['operation']==op],bundle['operations'][op][label],field,floor)
            for label,field,floor in (('delay','operator_delay_ps',10.),('area','comb_area_um2',.01))} for op in bundle['operations']})


def demand(bundle,witness):
    report=read(witness);targets=[]
    # Existing actual candidate graph queries only audit demand; no labels.
    source=report['runs'][1]
    for t in policy()['demand_checks_ps']:
        contexts={};views=[];reasons=Counter()
        for view in source['candidates']:
            missing=[]
            for node in view['node_prices']:
                q=deepcopy(node['descriptor']);q['flow_context'].update(target_period_ps=t,abc_target_ps=t)
                a=model.query(bundle,q,True);contexts[key(q['local_context'])]=a['status']=='covered'
                if a['status']!='covered':missing.append(dict(node=node['node'],reason=a['reason']));reasons[a['reason']]+=1
            views.append(dict(view=view['view'],covered=not missing,missing=missing))
        targets.append(dict(target_ps=t,contexts=len(contexts),covered_contexts=sum(contexts.values()),views=len(views),
            covered_views=sum(v['covered'] for v in views),reasons=dict(reasons),view_diagnostics=views))
    return dict(status='passed' if all(t['covered_contexts']==t['contexts'] for t in targets) else 'missing_coverage',
        targets=targets,source_sha256=sha(witness),queries_are_not_training_or_white_list=True)


def fit(data_path,out,witness):
    data=read(data_path);validate(data,'fitting')
    if (Path(data['collection_root'])/'test-acquisition-v2.json').exists():raise ValueError('independent acquisition has started; no fitting or domain retuning')
    if out.exists():raise ValueError('preserve candidate attempt')
    out.mkdir(parents=True)
    sources={n:sha(ROOT/n) for n in source_names()}
    for n in sources:
        destination=out/'execution-source'/n;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,destination)
    write(out/'execution-source.json',sources)
    rows=[r for r in data['rows'] if r['stage']=='grt'];root=Path(data['collection_root'])
    shapes={key(r['descriptor']['local_context']['producer']) for r in rows if r['role']=='train'}
    rows=[dict(r,unseen_training_shape=key(r['descriptor']['local_context']['producer']) not in shapes) for r in rows]
    new_ids={r['id'] for r in read(root/'new-sources.json')['sources']};protocol=read(root/'corpus/protocol.json')
    schema=sorted(set(rows[0]['features'])-set(protocol['feature_schema']['excluded_from_operator_predictor']))
    ops={};report={}
    for op in ('add','mul'):
        tr=[r for r in rows if r['role']=='train' and r['operation']==op];va=[r for r in rows if r['role']=='validation' and r['operation']==op]
        names=[n for n in schema if len({r['features'][n] for r in tr})>1]
        d,ds=choose(tr,va,'operator_delay_ps',names,10.,new_ids);a,ars=choose(tr,va,'comb_area_um2',names,.01,new_ids)
        ops[op]=dict(status='awaiting_independent',delay=d['predictor'],area=a['predictor'],
            delay_reserve_ps=max([0.]+[r['operator_delay_ps']-model.infer(d['predictor'],r['features']) for r in va]))
        report[op]=dict(delay=d['quality'],area=a['quality'],selected_delay=d['name'],selected_area=a['name'],
            delay_candidates=ds,area_candidates=ars,source_counts=dict(train=len({r['source_id'] for r in tr}),validation=len({r['source_id'] for r in va})),
            validation_subdomains=subsets(va,ops[op],new_ids),clock_validation=clock_statistics(va,ops[op]))
    bundle=dict(version=model.VERSION,profile_sha256=read(root/'corpus/manifest.json')['profile_sha256'],
        operator_boundary_policy='unsigned-op-hierarchy-v1',quality_status='awaiting_independent',operations=ops,
        fit_dataset_sha256=sha(data_path),source_manifest_sha256=data['source_manifest_sha256'],
        fit_protocol_sha256=sha(CONFIG),feature_protocol_sha256=sha(FEATURE),domain_protocol_sha256=sha(DOMAIN),full_D_ready=False)
    choices=[]
    for kind in policy()['candidates']:
        b=deepcopy(bundle)
        for op,e in b['operations'].items():
            tr=[r for r in rows if r['role']=='train' and r['operation']==op];va=[r for r in rows if r['role']=='validation' and r['operation']==op]
            e['domain']=domain(e,tr,va,kind)
        c=coverage(b,[r for r in rows if r['role']=='validation']);q=demand(b,witness)
        choices.append(dict(kind=kind,bundle=b,validation_coverage=c,demand=q))
    selected=min(choices,key=lambda c:(c['validation_coverage']['refused']>0,c['demand']['status']!='passed',
        c['validation_coverage']['refused'],sum(t['contexts']-t['covered_contexts'] for t in c['demand']['targets']),len(json.dumps(c['bundle']))))
    bundle=selected['bundle']
    quality=all(r['delay']['passed'] and r['area']['passed'] for r in report.values())
    subquality=all(v[label]['passed'] for r in report.values() for name,v in r['validation_subdomains'].items()
        if name in policy()['critical_validation_subdomains'] and v['sources']>=2 for label in ('delay','area'))
    ready=quality and subquality and not selected['validation_coverage']['refused'] and selected['demand']['status']=='passed' and not data.get('diagnostic_partial',False)
    checks_passed=quality and subquality and not selected['validation_coverage']['refused'] and selected['demand']['status']=='passed'
    bundle['fitting_collection_complete']=not data.get('diagnostic_partial',False)
    bundle['quality_status']='awaiting_independent' if ready else 'failed_validation'
    for e in bundle['operations'].values():e.update(status=bundle['quality_status'],validation_ready=ready)
    write(out/'candidate.json',bundle)
    write(out/'validation.json',dict(status='passed' if ready else 'failed',model_sha256=sha(out/'candidate.json'),
        source_manifest_sha256=data['source_manifest_sha256'],operations=report,quality_passed=quality,critical_subdomains_passed=subquality,
        all_validation_checks_passed=checks_passed,diagnostic_partial=data.get('diagnostic_partial',False),
        selected_support=selected['kind'],validation_coverage=selected['validation_coverage'],demand=selected['demand'],
        support_comparison=[{k:v for k,v in c.items() if k!='bundle'} for c in choices],independent_labels_read=False,full_D_ready=False))
    # Keep the mandatory same-strategy static calibration in the same units.
    fixed=read(ROOT/'experiments/arithmetic_dse/configs/fixed_op_width_v1.json');train=[r for r in rows if r['role']=='train'];counts=Counter(r['source_id'] for r in train)
    def proxy(r,field):
        if r['operation']=='add':return 1.
        bucket=next(b for b in fixed['width_buckets'] if b>=max(r['features']['lhs_width'],r['features']['rhs_width']))
        return float(fixed['operations']['Mul']['delay_weight' if field=='operator_delay_ps' else 'comb_weight'][str(bucket)])
    alpha={field:max(0,sum(proxy(r,field)*r[field]/counts[r['source_id']] for r in train)/sum(proxy(r,field)**2/counts[r['source_id']] for r in train)) for field in ('operator_delay_ps','comb_area_um2')}
    write(out/'static-unit-bridge.json',dict(version='fixed-cost-global-unit-bridge-v1',train_only=True,source_equal=True,
        fixed_table_sha256=sha(ROOT/'experiments/arithmetic_dse/configs/fixed_op_width_v1.json'),alpha=alpha,fit_dataset_sha256=sha(data_path)))
    print(dict(status=bundle['quality_status'],diagnostic_partial=data.get('diagnostic_partial',False),quality=quality,critical_subdomains=subquality,
        support=selected['kind'],validation_refused=selected['validation_coverage']['refused'],
        demand=[{k:t[k] for k in ('target_ps','contexts','covered_contexts','covered_views')} for t in selected['demand']['targets']],
        errors={op:{k:r[k] for k in ('delay','area','selected_delay','selected_area')} for op,r in report.items()}),flush=True)


def freeze(data_path,folder):
    data=read(data_path);validate(data,'fitting');candidate=read(folder/'candidate.json');v=read(folder/'validation.json')
    if data.get('diagnostic_partial'):raise ValueError('partial diagnosis cannot freeze independent model')
    if candidate['quality_status']!='awaiting_independent' or v['status']!='passed' or sha(folder/'candidate.json')!=v['model_sha256']:
        raise ValueError('full validation not passed')
    parity=folder/'inference/verification/proof.json';response=folder/'response-refusal.json'
    native_input=folder/'inference/input-0.json'
    if (read(parity).get('status')!='passed' or read(parity).get('actual_frozen_candidate') is not True
        or read(native_input)['model']!=candidate or len(read(response).get('negative_probes',[]))!=10
        or read(response).get('model_sha256')!=sha(folder/'candidate.json')):
        raise ValueError('actual model parity or refusal qualification missing')
    path=folder/'selection-freeze.json'
    if path.exists():raise ValueError('preserve freeze')
    required=source_names();sources=read(folder/'execution-source.json')
    if set(required)!=set(sources) or any(sha(ROOT/n)!=h or sha(folder/'execution-source'/n)!=h for n,h in sources.items()):
        raise ValueError('fit implementation changed before freeze')
    frozen=dict(version='operator-condition-selection-freeze-v2',validation_passed=True,test_consumed=False,
        source_manifest_sha256=data['source_manifest_sha256'],fit_dataset_sha256=sha(data_path),
        model_path='candidate.json',model_sha256=sha(folder/'candidate.json'),validation_path='validation.json',validation_sha256=sha(folder/'validation.json'),
        fit_protocol_sha256=sha(CONFIG),domain_protocol_sha256=sha(DOMAIN),feature_protocol_sha256=sha(FEATURE),
        qualification_files={str(p.resolve()):sha(p) for p in (parity,response,native_input,folder/'inference/output-0.json')},
        fit_producer=str(Path(__file__).relative_to(ROOT)),implementation_sources=sources)
    write(path,frozen);wide.verify_selection(Path(data['collection_root'])/'corpus',path)
    print(dict(status='frozen',implementation_sources=len(required),model_sha256=frozen['model_sha256']),flush=True)


def test(data_path,selection,out):
    data=read(data_path);root=Path(data['collection_root']);wide.verify_selection(root/'corpus',selection);validate(data,'independent')
    freeze=read(selection);folder=selection.parent
    for name,h in freeze['qualification_files'].items():
        if sha(Path(name))!=h:raise ValueError('pre-test numerical/refusal qualification changed')
    if out.exists():raise ValueError('preserve independent evaluation')
    out.mkdir(parents=True)
    parent=Path(read(root/'collection.json')['parent_collection_root'])
    if (parent/'independent-evaluation-consumed.json').exists():raise ValueError('parent tests already consumed')
    marker=dict(selection_sha256=sha(selection),dataset_sha256=sha(data_path),output=str(out),permanently_excluded_from_future_fitting_or_selection=True)
    for destination,value in ((root/'independent-evaluation-consumed.json',marker),
            (parent/'independent-evaluation-consumed.json',dict(marker,inherited_test_sources_consumed_by=str(root)))):
        with destination.open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    candidate=read(folder/'candidate.json');rows=[r for r in data['rows'] if r['stage']=='grt'];reports={}
    new_ids={r['id'] for r in read(root/'new-sources.json')['sources']};fit=read(root/'fit-data.json')
    training_shapes={key(r['descriptor']['local_context']['producer']) for r in fit['rows'] if r['role']=='train'}
    fitting_shapes={key(r['descriptor']['local_context']['producer']) for r in fit['rows']}
    rows=[dict(r,unseen_training_shape=key(r['descriptor']['local_context']['producer']) not in training_shapes,
        unseen_fitting_shape=key(r['descriptor']['local_context']['producer']) not in fitting_shapes) for r in rows]
    for op,e in candidate['operations'].items():
        group=[r for r in rows if r['operation']==op];stats={label:base.metrics(group,e[label],field,floor) for label,field,floor in (('delay','operator_delay_ps',10.),('area','comb_area_um2',.01))}
        c=coverage(candidate,group);subs=subsets(group,e,new_ids)
        fresh=[r for r in group if r['source_id'] in new_ids and r['target_ps']==1000]
        fresh_stats={label:base.metrics(fresh,e[label],field,floor) for label,field,floor in (('delay','operator_delay_ps',10.),('area','comb_area_um2',.01))}
        failed=any(r['operation']==op and r['source_id'] in {f['source_id'] for f in data['failures']} for r in data['coverage'])
        expected={r['source_id'] for r in data['coverage'] if r['operation']==op}
        subpass=all(v[label]['passed'] for name,v in subs.items() if name in policy()['critical_validation_subdomains'] and v['sources']>=2 for label in ('delay','area'))
        passed=all(s['passed'] for s in stats.values()) and not c['refused'] and not failed and subpass and len(fresh)>=2 and all(s['passed'] for s in fresh_stats.values()) and {r['source_id'] for r in group}==expected
        reports[op]=dict(status='passed' if passed else 'failed',**stats,coverage=c,subdomains=subs,
            clock_statistics=clock_statistics(group,e),
            exact1000ps=dict(rows=len(fresh),sources=len({r['source_id'] for r in fresh}),**fresh_stats),
            acquisition_failed=failed,reserve_underpredictions=sum(model.infer(e['delay'],r['features'])+e['delay_reserve_ps']<r['operator_delay_ps'] for r in group))
        e['status']='passed_independent' if passed else 'failed_independent'
    candidate['quality_status']='isolated_functions_passed' if all(r['status']=='passed' for r in reports.values()) else 'failed_independent'
    write(out/'tested-model.json',candidate);write(out/'independent-test.json',dict(status=candidate['quality_status'],operations=reports,
        model_sha256=freeze['model_sha256'],selection_sha256=sha(selection),parameters_changed=False,full_D_ready=False))
    print(dict(status=candidate['quality_status'],operations={op:dict(status=r['status'],delay=r['delay'],area=r['area'],coverage=r['coverage']['accepted'],exact1000ps=r['exact1000ps']) for op,r in reports.items()}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('extract','snapshot','fit','freeze','test'))
    for n in ('root','out','data','witness','selection','folder'):p.add_argument('--'+n,type=Path)
    p.add_argument('--mode',choices=('fitting','independent'),default='fitting');a=p.parse_args()
    if a.action=='extract':extract(a.root.resolve(),a.out.resolve(),a.mode,a.selection.resolve() if a.selection else None)
    elif a.action=='snapshot':snapshot(a.root.resolve(),a.out.resolve())
    elif a.action=='fit':fit(a.data.resolve(),a.out.resolve(),a.witness.resolve())
    elif a.action=='freeze':freeze(a.data.resolve(),a.folder.resolve())
    else:test(a.data.resolve(),a.selection.resolve(),a.out.resolve())
