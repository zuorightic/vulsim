"""Train-only refit, prospective selection, parameter seal, fresh evaluation."""
from collections import defaultdict
from copy import deepcopy
import math
from pathlib import Path
from statistics import median
from unittest.mock import patch

from . import nangate45_refit_samples as campaign
from .nangate45_samples import ROOT,read,write,sha
from . import nangate45_fit as fit, nangate45_fit_sealed as sealed
from . import nangate45_model as numerical, nangate45_response_features as features
from . import workload_diagnostic as old


def rows(root,roles):
    a=campaign.verify(root);result=[]
    for t in a['tasks']:
        if t['role'] not in roles:continue
        source=next(s for s in a['sources'] if s['id']==t['source'])
        path=root/'runs'/t['id']/'grt-labels.json';label=read(path)
        if (label['admission_sha256']!=sha(root/'admission.json') or label['rtl_sha256']!=t['rtl_sha256'] or
            label['profile_sha256']!=a['profile_sha256'] or label['source_role']!=t['role'] or
            not label['physical_training_label_eligible']):raise ValueError('label identity invalid')
        node=label['nodes']['producer'];slack=label['metrics']['setup_worst_slack_ps'];ratio=slack/t['period_ps']
        result.append(dict(source=t['source'],producer_group=source['producer_group'],family=t['family'],role=t['role'],
            target_ps=t['period_ps'],query=source['query'],requested_region=t['requested_region'],
            observed_region='loose' if ratio>.2 else 'tight' if ratio<-.2 else 'suitable',
            setup_slack_ps=slack,setup_slack_over_T=ratio,label_path=str(path),label_sha256=sha(path),
            delay_ps=node['operator_delay_ps'],area_um2=node['comb_area_um2']))
    return result


def stats(rr,pp,metric='delay_ps'):
    result=sealed.metrics(rr,pp,metric);groups=defaultdict(list)
    for r,p in zip(rr,pp,strict=True):groups[r['source']].append(abs(p/r[metric]-1))
    result['source_mean_APE']=sum(sum(v)/len(v) for v in groups.values())/len(groups)
    result['max_point_APE']=max(max(v) for v in groups.values())
    return result


def freeze(root):
    a=campaign.verify(root)
    if (root/'frozen-model.json').exists() or any((root/'runs'/t['id']).exists() for t in a['tasks'] if t['role']=='test'):
        raise ValueError('freeze once before new test acquisition')
    baseline=read(campaign.BASE/'frozen-model.json');data=read(campaign.BASE/'calibration-data.json')
    fresh=rows(root,('train','validation'));prices=old.DiagnosticPrices(baseline['ASAP7_response'])
    payload=deepcopy(baseline);audit={}
    with patch.object(numerical,'basis',features.basis),patch.object(numerical,'FEATURES',features.FEATURES):
        for family in ('Add','G'):
            tr=[r for r in data+fresh if r['family']==family and r['role']=='train']
            val=[r for r in fresh if r['family']==family and r['role']=='validation']
            protection=[r for r in data if r['family']==family and r['role']=='validation']
            candidates=[dict(candidate_form='frozen_baseline',function=deepcopy(baseline['functions'][family]['delay_ps']))]
            for form in a['candidate_forms'][1:]:
                for ts in a['request_time_scales']:
                    for alpha in (a['ridge_alpha'] if form=='shared_log_feature_ridge' else [None]):
                        candidates.append(dict(candidate_form=form,function=fit.fit_function(tr,family,'delay_ps',form,ts,prices,alpha)))
            for c in candidates:
                c['fresh_validation']=stats(val,fit.predict(c['function'],val,family,'delay_ps',prices))
                c['consumed_validation_protection']=stats(protection,fit.predict(c['function'],protection,family,'delay_ps',prices))
                c['train']=stats(tr,fit.predict(c['function'],tr,family,'delay_ps',prices))
                gates=[c['fresh_validation']['passed'],c['consumed_validation_protection']['passed'],c['fresh_validation']['max_point_APE']<=.35]
                c['gates']=gates
            def rank(i):
                c=candidates[i];v=c['fresh_validation'];p=c['consumed_validation_protection'];g=c['gates']
                return (not all(g),sum(not x for x in g),(v['source_mean_APE']+p['source_mean_APE'])/2,
                        max(v['P95_APE'],p['P95_APE']),v['max_point_APE'],a['candidate_forms'].index(c['candidate_form']),i)
            chosen=min(range(len(candidates)),key=rank)
            payload['functions'][family]['delay_ps']=candidates[chosen]['function']
            audit[family]=dict(chosen=chosen,candidates=candidates,selection_rank=list(rank(chosen)))
    for f,m in (('Mul','delay_ps'),('Mul','area_um2'),('Add','area_um2'),('G','area_um2')):
        if payload['functions'][f][m]!=baseline['functions'][f][m]:raise ValueError('unrequested function changed')
    all_clocks=[t['period_ps'] for t in a['tasks']]+baseline['clock_support_ps']
    payload.update(admission_sha256=sha(root/'admission.json'),clock_support_ps=[min(all_clocks),max(all_clocks)],
        recalibration_version=campaign.VERSION,baseline_model_sha256=sha(campaign.BASE/'frozen-model.json'),
        qualification='pending fresh sealed test; diagnostic arithmetic components only',
        refit_metrics=a['refit_metrics'],unchanged_metrics=a['unchanged_metrics'],
        historical_test_used_for_fitting_or_selection=False)
    write(root/'selection.json',audit);write(root/'calibration-data.json',data+fresh);write(root/'frozen-model.json',payload)
    write(root/'model-freeze.json',dict(model_sha256=sha(root/'frozen-model.json'),selection_sha256=sha(root/'selection.json'),
        admission_sha256=sha(root/'admission.json'),calibration_sha256=sha(root/'calibration-data.json'),
        fresh_test_acquired=False,old_test_used_for_fit_or_selection=False))
    return {f:dict(form=audit[f]['candidates'][audit[f]['chosen']]['candidate_form'],
        validation=audit[f]['candidates'][audit[f]['chosen']]['fresh_validation'],
        protection=audit[f]['candidates'][audit[f]['chosen']]['consumed_validation_protection']) for f in audit}


def evaluate(root):
    a=campaign.verify(root);seal=read(root/'model-freeze.json')
    if sha(root/'frozen-model.json')!=seal['model_sha256'] or (root/'evaluation.json').exists():raise ValueError('sealed model/evaluation guard')
    payload=read(root/'frozen-model.json');baseline=read(campaign.BASE/'frozen-model.json')
    fresh=rows(root,('train','validation','test'));consumed=read(campaign.BASE/'evaluation-data.json')
    prices=old.DiagnosticPrices(payload['ASAP7_response']);report={};predictions=[]
    with patch.object(numerical,'basis',features.basis):
        for family in ('Add','G'):
            report[family]={}
            for metric in ('delay_ps','area_um2'):
                report[family][metric]={}
                panels={role:[r for r in fresh if r['family']==family and r['role']==role] for role in ('train','validation','test')}
                panels.update({'consumed_'+role:[r for r in consumed if r['family']==family and r['role']==role]
                               for role in ('train','validation','test')})
                for name,rr in panels.items():
                    pp=fit.predict(payload['functions'][family][metric],rr,family,metric,prices)
                    bp=fit.predict(baseline['functions'][family][metric],rr,family,metric,prices)
                    result=dict(recalibrated=stats(rr,pp,metric),baseline=stats(rr,bp,metric))
                    for region_key in ('requested_region','observed_region'):
                        result[region_key]={}
                        for region in ('tight','suitable','loose'):
                            inds=[i for i,r in enumerate(rr) if r.get(region_key)==region]
                            if inds:result[region_key][region]=stats([rr[i] for i in inds],[pp[i] for i in inds],metric)
                    report[family][metric][name]=result
                    predictions.extend(dict(source=r['source'],family=family,panel=name,metric=metric,target_ps=r['target_ps'],
                        actual=r[metric],prediction=p,baseline_prediction=b,error_fraction=abs(p/r[metric]-1),
                        requested_region=r.get('requested_region'),observed_region=r.get('observed_region'),
                        setup_slack_ps=r.get('setup_slack_ps')) for r,p,b in zip(rr,pp,bp,strict=True))
    selected=read(root/'selection.json')
    qualified={f:dict(fresh_validation=all(selected[f]['candidates'][selected[f]['chosen']]['gates']),
                     fresh_test=report[f]['delay_ps']['test']['recalibrated']['passed'],
                     consumed_test_regression=report[f]['delay_ps']['consumed_test']['recalibrated']['passed']) for f in report}
    result=dict(version=campaign.VERSION,model_sha256=seal['model_sha256'],stats=report,qualification=qualified,
        recalibration_gates_passed=all(q['fresh_validation'] and q['fresh_test'] and q['consumed_test_regression'] for q in qualified.values()),
        full_D_ready=False,fresh_test_returned_to_fit=False,old_test_is_consumed_regression=True,
        baseline_erratum=a['producer_role_audit']['baseline_erratum'],
        region_note='prospective request classes; measured slack/T separately reported; shell has T-dependent IO; no Tmin inferred',
        remaining=['N5 S/shared and G embedding','N6 H_char, complete model and integration','N7/N8 three application cases'])
    write(root/'evaluation-data.json',fresh);write(root/'predictions.json',predictions);write(root/'evaluation.json',result)
    return result
