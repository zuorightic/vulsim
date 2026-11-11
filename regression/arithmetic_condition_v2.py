"""v2 fitting gates and numerical diagnostics, charged by the caller."""
import argparse
from copy import deepcopy
from pathlib import Path
from types import FunctionType,SimpleNamespace
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse import operator_condition_fit_v2 as fit
from experiments.arithmetic_dse import operator_condition_model as model


def preflight(out):
    rows=[];new_ids={'new0','new1'}
    for i in range(52):
        new=i>=50;sid='new'+str(i-50) if new else 'old'+str(i)
        f=dict(lhs_width=16 if new else 8,consumer_lhs_max=0,consumer_rhs_max=0,consumer_result_max=0,
            result_width=16,mapping_shift_min=0,mapping_shift_max=0,low_result=0,capture_banks=1)
        rows.append(dict(source_id=sid,features=f,operator_delay_ps=100.))
    predictors=[('globally_better_but_new_load_wrong',dict(kind='linear',features=['lhs_width'],coefficients=[-6.25],intercept=150.)),
        ('passes_new_load',dict(kind='linear',features=['lhs_width'],coefficients=[-.375],intercept=106.))]
    # The independent arithmetic is exact: old predictions100/103, new50/100.
    namespace=dict(fit.choose.__globals__)
    namespace['base']=SimpleNamespace(candidates=lambda *a:predictors,metrics=fit.base.metrics)
    choose=FunctionType(fit.choose.__code__,namespace)
    selected,trials=choose(rows,rows,'operator_delay_ps',['lhs_width'],10.,new_ids,False)
    if not trials[0]['quality']['passed'] or trials[0]['critical_quality']['new_source']['passed']:
        raise ValueError('critical gate fixture lost its distinguishing property')
    if selected['name']!='passes_new_load':raise ValueError('critical subgroup lost to aggregate score')
    write(out,dict(status='passed',critical_gate_precedes_aggregate_score=True,
        fixture_only=True,physical_labels_read=False,new_EDA_calls=0,
        producer_sha256=sha(Path(fit.__file__)),domain_protocol_sha256=sha(fit.DOMAIN)))
    print('V2_CRITICAL_SUBDOMAIN_SELECTION_PREFLIGHT_PASS',flush=True)


def diagnostics(data,folder,out):
    rows=[r for r in read(data)['rows'] if r['stage']=='grt'];bundle=read(folder/'candidate.json');responses=[]
    for sid in sorted({r['source_id'] for r in rows}):
        local=[r for r in rows if r['source_id']==sid];entry=bundle['operations'][local[0]['operation']]
        def span(values):return dict(min=min(values),max=max(values),range=max(values)-min(values))
        responses.append(dict(source_id=sid,role=local[0]['role'],operation=local[0]['operation'],
            target_ps=span([r['target_ps'] for r in local]),
            measured_delay_ps=span([r['operator_delay_ps'] for r in local]),
            measured_area_um2=span([r['comb_area_um2'] for r in local]),
            predicted_delay_ps=span([model.infer(entry['delay'],r['features']) for r in local]),
            predicted_area_um2=span([model.infer(entry['area'],r['features']) for r in local])))
    negative=[]
    if bundle['quality_status']=='awaiting_independent':
        # Start from an actually covered fitted query, then mutate one property.
        base=next(r['descriptor'] for r in rows if r['descriptor']['local_context']['consumers'] and model.query(bundle,r['descriptor'],True)['status']=='covered')
        def refuse(name,change):
            q=deepcopy(base);change(q);answer=model.query(bundle,q,True)
            if answer['status']!='cost_uncovered':raise ValueError('domain accepted '+name)
            negative.append(dict(name=name,reason=answer['reason']))
        refuse('unsupported_operation',lambda q:q['local_context']['producer'].update(operation='div'))
        refuse('nonzero_carry',lambda q:q['local_context']['producer'].update(carry='one'))
        refuse('producer_known_one',lambda q:q['local_context']['producer'].update(lhs_zero_hex='0x0',lhs_one_hex='0x1'))
        refuse('interior_zero_mask',lambda q:q['local_context']['producer'].update(lhs_zero_hex='0x4',lhs_one_hex='0x0'))
        refuse('multiple_consumers',lambda q:q['local_context']['consumers'].append(deepcopy(q['local_context']['consumers'][0])))
        def oversize(q):
            c=q['local_context']['consumers'][0];c['spec'].update(lhs_width=257,rhs_width=257,result_width=257)
            for binding in c['bindings']:binding['result_bit_map']+=['0']*(257-len(binding['result_bit_map']))
        refuse('oversized_consumer',oversize)
        refuse('clock_below_support',lambda q:q['flow_context'].update(target_period_ps=1,abc_target_ps=1))
        refuse('foreign_profile',lambda q:q['flow_context'].update(profile_sha256='foreign'))
        refuse('source_id_injected',lambda q:q.update(source_id='case-price'))
        refuse('view_id_injected',lambda q:q.update(view_id='view42'))
    def unclamped(p,f):
        if p['kind']=='linear':return p['intercept']+sum(c*f[n] for n,c in zip(p['features'],p['coefficients'],strict=True))
        if p['kind']=='segmented':return unclamped(p['segments'][sum(f['log2_target_ps']>k for k in p['knots'])],f)
        if p['kind']=='width_grouped':return unclamped(p['groups']['small' if max(f['lhs_width'],f['rhs_width'])<=p['split'] else 'large'],f)
        return model.infer(p,f)
    negatives={op:{label:sum(unclamped(bundle['operations'][op][label],r['features'])<0 for r in rows if r['operation']==op) for label in ('delay','area')} for op in bundle['operations']}
    write(out,dict(status='reported',responses=responses,negative_probes=negative,unclamped_negative_predictions=negatives,
        model_sha256=sha(folder/'candidate.json'),fit_dataset_sha256=sha(data),
        flat_response_not_forced_monotonic=True,exact1000ps_prices_not_read=True,
        physical_test_labels_read=False,full_D_ready=False))
    print(dict(status='reported',source_responses=len(responses),refusal_checks=len(negative)),flush=True)


def rebase(data,out):
    if out.exists():raise ValueError('preserve diagnostic protocol version')
    snapshot=read(data)
    if not snapshot.get('diagnostic_partial') or not snapshot.get('history_prefixes'):
        raise ValueError('only an immutable diagnostic prefix can be requalified')
    snapshot.update(parent_diagnostic_sha256=sha(data),domain_protocol_sha256=sha(fit.DOMAIN),
        requalification_reason='successor domain rule only; original features, roles and physical labels unchanged')
    fit.validate(snapshot,'fitting');write(out,snapshot)
    print(dict(status='diagnostic_protocol_successor',points=len(snapshot['rows'])//2,physical_labels_changed=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('preflight','diagnostics','rebase'))
    for n in ('out','data','folder'):p.add_argument('--'+n,type=Path)
    a=p.parse_args()
    if a.action=='preflight':preflight(a.out.resolve())
    elif a.action=='diagnostics':diagnostics(a.data.resolve(),a.folder.resolve(),a.out.resolve())
    else:rebase(a.data.resolve(),a.out.resolve())
