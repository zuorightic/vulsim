"""Portable recalibration delivery and independent receipt/inference audit."""
from collections import Counter
from copy import deepcopy
from datetime import datetime,timezone
import math
from pathlib import Path
import subprocess
from unittest.mock import patch

from . import nangate45_refit_samples as campaign
from .nangate45_samples import ROOT,read,write,sha
from .nangate45_artifacts import load
from .nangate45_model import native_query
from .nangate45_migration import verify as verify_baseline
from .nangate45_cec import verify_proof


def export(root,out):
    a=campaign.verify(root);seal=read(root/'model-freeze.json');evaluation=read(root/'evaluation.json')
    if sha(root/'frozen-model.json')!=seal['model_sha256'] or evaluation['model_sha256']!=seal['model_sha256']:
        raise ValueError('model/evaluation seal differs')
    doc=read(campaign.PACKAGE);payload=read(root/'frozen-model.json');del payload['ASAP7_response']
    doc.update(numerical_payload=payload,external_model_sha256=seal['model_sha256'],
        statistical_contract_sha256=sha(root/'admission.json'),evaluation_sha256=sha(root/'evaluation.json'),
        status='arithmetic_delay_recalibration_evaluated',
        qualification='diagnostic_components_recalibration_gates_passed' if evaluation['recalibration_gates_passed'] else 'diagnostic_components_some_recalibration_gates_failed',
        recalibration_version=campaign.VERSION,baseline_package_sha256=sha(campaign.PACKAGE),
        unchanged_metrics=a['unchanged_metrics'],refit_metrics=a['refit_metrics'],
        measured_support=dict(baseline=doc['measured_support'],new_sources=len(a['sources']),new_points=len(a['tasks']),
            request_ps_range=payload['clock_support_ps'],source_shapes=[dict(family=s['family'],role=s['role'],
                width=(s['query']['output_bits'] if s['family']=='G' else s['query']['local_context']['producer']['lhs_width']),
                clocks_ps=s['reference']['periods_ps']) for s in a['sources']]),
        baseline_role_erratum=a['producer_role_audit']['baseline_erratum'])
    write(out,doc);load(out)
    return dict(path=str(out),bytes=out.stat().st_size,sha256=sha(out))


def audit(root,package):
    a=campaign.verify(root);seal=read(root/'model-freeze.json');progress=read(root/'progress.json')
    if len(progress['completed'])!=len(a['tasks']) or progress['errors']:raise ValueError('sampling incomplete')
    payload=read(root/'frozen-model.json');base=read(campaign.BASE/'frozen-model.json')
    for f,m in (('Mul','delay_ps'),('Mul','area_um2'),('Add','area_um2'),('G','area_um2')):
        if payload['functions'][f][m]!=base['functions'][f][m]:raise ValueError('unchanged metric modified')
    if sha(root/'frozen-model.json')!=seal['model_sha256'] or sha(root/'selection.json')!=seal['selection_sha256']:
        raise ValueError('parameters/selection changed')
    selection=read(root/'selection.json')
    for f,v in selection.items():
        if v['candidates'][v['chosen']]['function']!=payload['functions'][f]['delay_ps']:raise ValueError('selected function differs')
    predictions=read(root/'predictions.json');sources={s['id']:s for s in a['sources']}
    sources.update({s['id']:s for s in read(campaign.BASE/'admission.json')['sources']})
    prices=load(package);probes=[]
    for row in predictions:
        q=native_query(sources[row['source']]['query'],'nangate45',a['profile_sha256'],row['target_ps'])
        if row['family']=='G':q.update(target_platform='nangate45',profile_sha256=a['profile_sha256'])
        probes.append((row,q))
    negative=[]
    def refused(label,fn):
        try:fn()
        except (ValueError,KeyError):negative.append(label)
        else:raise ValueError('negative control accepted: '+label)
    q=deepcopy(next(q for row,q in probes if row['family']=='Add'))
    for key,value in [('target_platform','asap7'),('profile_sha256','0'*64),('abc_target_ps',-1),('evaluation_stage','synth')]:
        wrong=deepcopy(q);wrong['flow_context'][key]=value;refused(key,lambda:prices.operator_price(wrong))
    g=deepcopy(next(q for row,q in probes if row['family']=='G'));g.pop('profile_sha256')
    refused('G profile missing',lambda:prices.reduction_price(g))
    def forbidden(*args,**kwargs):raise AssertionError('numerical consumption attempted IO/process')
    with patch('builtins.open',forbidden),patch.object(Path,'open',forbidden),patch.object(subprocess,'Popen',forbidden),patch.object(subprocess,'run',forbidden):
        for row,q in probes:
            predict=prices.reduction_price if row['family']=='G' else prices.operator_price
            value=predict(q)[row['metric']]
            if not math.isclose(value,row['prediction'],rel_tol=1e-12,abs_tol=1e-8):raise ValueError('portable numerical result differs')
        q=deepcopy(next(q for row,q in probes if row['family']=='Add'));expected=prices.operator_price(q)
        q.update(source='never-sampled',case='arbitrary',instance='arbitrary')
        if prices.operator_price(q)!=expected:raise ValueError('inference consumes source identity')
        q['flow_context']['target_period_ps']=q['flow_context']['abc_target_ps']=1777.25
        if not all(math.isfinite(v) and v>0 for k,v in prices.operator_price(q).items() if k in ('delay_ps','area_um2')):raise ValueError('continuous request failed')
    receipts=[]
    for t in a['tasks']:
        d=root/'runs'/t['id'];l=read(d/'grt-labels.json');status=read(d/'collection-status.json');m=read(d/'manifest.json')
        if sha(d/'grt-labels.json')!=status['label_sha256'] or l['rtl_sha256']!=t['rtl_sha256'] or sha(d/'input.sv')!=t['rtl_sha256']:
            raise ValueError('label/RTL receipt differs')
        if l['admission_sha256']!=sha(root/'admission.json') or m['platform_profile']['profile_sha256']!=a['profile_sha256']:
            raise ValueError('admission/profile receipt differs')
        if l['metrics']['raw_report_units']['time']['to_ps']!=1000 or abs(l['total_cell_area_um2']-l['metrics']['cell_area_um2'])>1e-5:
            raise ValueError('units/area conservation invalid')
        if not read(d/'logical-v2-grt/ownership-certificate.json')['complete']:raise ValueError('ownership incomplete')
        proof=Path(l['CTS_CEC_path'])
        if sha(proof)!=l['CTS_CEC_sha256']:raise ValueError('CEC proof drift')
        verify_proof(proof,d/'results/nangate45/arithmetic_probe/base/4_before_rsz_lec.v',d/'results/nangate45/arithmetic_probe/base/4_after_rsz_lec.v')
        for r in read(d/'collection-commands.json'):
            if r['exit_code'] or r['cleanup']['remaining_live_pids']:raise ValueError('leaf not cleaned up')
        receipts.append(dict(source=t['source'],role=t['role'],target_ps=t['period_ps'],requested_region=t['requested_region'],
            label_sha256=status['label_sha256'],setup_slack_ps=l['metrics']['setup_worst_slack_ps'],hold_slack_ps=l['metrics']['hold_worst_slack_ps']))
    state=read(ROOT/'experiments/arithmetic/backend_usage.json');entries=[e for e in state['entries'] if e.get('admission_id')==a['id']]
    jobs=[j for j in state['jobs'] if j.get('admission_id')==a['id']]
    if any(e['status'] in ('reserved','unsettled') for e in entries) or any(j['status']!='released' for j in jobs):raise ValueError('own resources unsettled')
    first_test=min(datetime.fromisoformat(e['reserved_at']).timestamp() for e in entries if any(t['id']==e.get('task_id') and t['role']=='test' for t in a['tasks']))
    if (root/'model-freeze.json').stat().st_mtime>=first_test:raise ValueError('seal does not precede fresh test')
    return dict(status='passed',numerical_checks_without_IO=len(probes)+2,negative_controls=negative,
        unchanged_metric_functions=4,test_parameters_unchanged=True,test_freeze_precedes_acquisition=True,
        strict_labels=len(receipts),receipts=receipts,own_calls=dict(Counter(e['stage'] or 'support' for e in entries)),
        failed_entries=[e['id'] for e in entries if e['status']=='failed'],all_own_jobs_released=True,
        walltime_s=sum(e['walltime_s'] for e in entries),CPU_time_s=sum(e['CPU_time_s'] for e in entries),
        frozen_N12=verify_baseline(ROOT.parent/'vulsim-artifacts/nangate45-n12-20261117-v1'),
        archive_sha256=__import__('hashlib').sha256((ROOT/'mission/lxy-plan-fix.md').read_bytes().split(b'<a id="W1-W8-archive"></a>',1)[1]).hexdigest(),
        full_D_ready=False)
