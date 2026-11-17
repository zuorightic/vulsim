"""Independent software/receipt checks for the finite N3/N4 deliverable."""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import subprocess
from unittest.mock import patch

from .nangate45_samples import ROOT,read,write,sha,verify
from .nangate45_artifacts import load,ArithmeticPrices
from . import nangate45_model as model
from . import nangate45_fit as fit
from . import nangate45_fit_sealed as sealed
from .nangate45_migration import verify as verify_N12


def software(root,package):
    a=verify(root);seal=read(root/'model-freeze.json');payload=read(root/'frozen-model.json')
    evaluation=read(root/'evaluation.json');predictions=read(root/'predictions.json')
    if sha(root/'frozen-model.json')!=seal['model_sha256'] or evaluation['model_sha256']!=seal['model_sha256']:
        raise ValueError('frozen model/evaluation hash differs')
    if read(root/'statistical-contract.json')['implementation_sha256']!=sha(sealed.__file__):raise ValueError('statistics implementation drift')
    if seal['test_labels_read'] or not seal['fit_parameters_final']:raise ValueError('seal did not precede test consumption')
    prices=load(package);tests=[]
    def refused(label,fn):
        try:fn()
        except (ValueError,KeyError):tests.append(label)
        else:raise ValueError('negative control accepted: '+label)
    probe=next(s for s in a['sources'] if s['family']=='Mul')
    q=model.native_query(probe['query'],'nangate45',a['profile_sha256'],1700.)
    original=prices.operator_price(q)
    wrong=deepcopy(q);wrong['flow_context']['target_platform']='asap7'
    refused('platform mismatch',lambda:prices.operator_price(wrong))
    wrong=deepcopy(q);wrong['flow_context']['profile_sha256']='0'*64
    refused('profile mismatch',lambda:prices.operator_price(wrong))
    wrong=deepcopy(q);wrong['flow_context']['abc_target_ps']=500
    refused('request ABC mismatch',lambda:prices.operator_price(wrong))
    wrong=deepcopy(q);wrong['flow_context']['evaluation_stage']='synth'
    refused('stage mismatch',lambda:prices.operator_price(wrong))
    wrong=deepcopy(q);wrong['flow_context']['target_period_ps']=wrong['flow_context']['abc_target_ps']=-1
    refused('nonpositive clock',lambda:prices.operator_price(wrong))
    g=next(s for s in a['sources'] if s['family']=='G')['query']
    refused('G missing explicit profile',lambda:prices.reduction_price(g))
    g=deepcopy(g);g.update(target_platform='nangate45',profile_sha256=a['profile_sha256'],target_ps=1700.)
    q['source']='never_measured_source';q['workload']='not_in_campaign';q['instance']='unseen-instance'
    if prices.operator_price(q)!=original:raise ValueError('source/case/instance metadata changes a price')
    # Exercise interpolation at an unmeasured clock, and a width/shape which
    # occurs in none of the paired sources. This checks a numerical function;
    # it explicitly grants no accuracy qualification to that extrapolation.
    from . import wide_arithmetic as arithmetic
    s=deepcopy(probe['query']['local_context']['producer'])
    s.update(lhs_width=12,rhs_width=20,arithmetic_width=32,value_width=32,result_width=32,result_lo=0)
    arithmetic.validate(s)
    unseen=deepcopy(q);unseen['declared_result_width']=32;unseen['required_result_bits']=list(range(32))
    unseen['local_context']=dict(producer=s,consumers=[],captures=[dict(banks=1,declared_width=32,result_bit_map=list(range(32)))])
    alias=deepcopy(unseen);alias['local_context']['producer']['lhs_zero_hex']=hex((1<<12)-1)
    # All data is preloaded. File and process access are disabled during real
    # numerical consumption, including the never-sampled width and clock.
    checks=0
    def no_io(*args,**kwargs):raise AssertionError('inference attempted I/O or a process')
    with patch('builtins.open',no_io),patch.object(Path,'open',no_io),patch.object(subprocess,'Popen',no_io),patch.object(subprocess,'run',no_io):
        for fn,query in ((prices.operator_price,q),(prices.operator_price,unseen),(prices.reduction_price,g)):
            p=fn(query);assert all(math.isfinite(p[n]) and p[n]>0 for n in ('delay_ps','area_um2'));checks+=1
        zero=prices.operator_price(alias)
        if zero['delay_ps']!=0 or zero['area_um2']!=0 or 'proven_constant_or_wire_alias' not in zero['flags']:
            raise ValueError('semantic constant/wire arithmetic is not zero')
        checks+=1
        for item in predictions:
            source=next(s for s in a['sources'] if s['id']==item['source'])
            query=model.native_query(source['query'],'nangate45',a['profile_sha256'],item['target_ps'])
            if item['family']=='G':query.update(target_platform='nangate45',profile_sha256=a['profile_sha256'])
            p=(prices.reduction_price(query) if item['family']=='G' else prices.operator_price(query))[item['metric']]
            if not math.isclose(p,item['prediction'],rel_tol=1e-12,abs_tol=1e-8):raise ValueError('portable inference differs from sealed prediction')
            checks+=1
    # Verify source-macro aggregation with unequal clocks per source; row
    # replication must not alter its weight or the nearest-rank P95.
    rows=[dict(source='a',x=100.)]*8+[dict(source='b',x=100.)]
    stats=sealed.metrics(rows,[110.]*8+[140.],'x')
    if not (math.isclose(stats['median_APE'],.1) and math.isclose(stats['P95_APE'],.4) and not stats['passed']):
        raise ValueError('source macro/protection statistics changed')
    selection=read(root/'selection.json')
    for family,metrics in selection.items():
        for metric,entry in metrics.items():
            picked=entry['candidates'][entry['chosen']]['function']
            if picked!=payload['functions'][family][metric]:raise ValueError('selected parameters changed after validation')
    old=verify_N12(ROOT.parent/'vulsim-artifacts/nangate45-n12-20261117-v1')
    return dict(status='passed',numerical_checks_without_IO=checks,negative_controls=tests,
                unmeasured_clock_ps=1700,unmeasured_mul_shape='12x20 full32 (software only)',
                source_keys_ignored=True,semantic_zero_alias_checked=True,source_macro_statistics_checked=True,frozen_N12=old,
                test_parameters_unchanged=True,full_D_ready=False)


def receipts(root):
    a=verify(root);progress=read(root/'progress.json')
    if len(progress['completed'])!=len(a['tasks']) or progress['errors']:raise ValueError('finite collection incomplete')
    flow=read(root/'paired-ASAP7-flow-audit.json')
    if flow['clock_identity_mismatches'] or len(flow['rows'])!=len(a['tasks']):raise ValueError('paired flow audit incomplete')
    tools=flow['rows'][0]['tools']
    for row in flow['rows']:
        if sha(row['manifest_path'])!=row['manifest_sha256'] or any(row['tools'][k]['sha256']!=tools[k]['sha256'] for k in tools):
            raise ValueError('paired ASAP7 manifest/tool identity drift')
    rows=[];setup_unmet=hold_negative=hold_review=0
    for t in a['tasks']:
        p=root/'runs'/t['id'];l=read(p/'grt-labels.json');status=read(p/'collection-status.json')
        if sha(p/'grt-labels.json')!=status['label_sha256'] or l['rtl_sha256']!=t['rtl_sha256']:
            raise ValueError('completed source/label hash differs')
        if l['metrics']['raw_report_units']['time']['to_ps']!=1000:raise ValueError('native ns scaling changed')
        if abs(l['total_cell_area_um2']-l['metrics']['cell_area_um2'])>1e-5:raise ValueError('area conservation differs')
        if sha(l['CTS_CEC_path'])!=l['CTS_CEC_sha256']:raise ValueError('CEC receipt changed')
        cert=read(p/'logical-v2-grt/ownership-certificate.json')
        if not cert['complete']:raise ValueError('unresolved owner in eligible label')
        manifest=read(p/'manifest.json')
        if any(manifest['tools'][k]['sha256']!=tools[k]['sha256'] for k in tools):raise ValueError('cross-backend tool versions differ')
        if manifest['platform_profile']['profile_sha256']!=a['profile_sha256']:raise ValueError('sample profile differs')
        setup_unmet+=l['metrics']['setup_worst_slack_ps']<0
        hold_negative+=l['metrics']['hold_worst_slack_ps']<0
        hold_review+=l['metrics']['hold_worst_slack_ps']<5
        for record in read(p/'collection-commands.json'):
            if record['exit_code'] or record['cleanup']['remaining_live_pids']:raise ValueError('unfinished leaf')
        rows.append(dict(source=t['source'],role=t['role'],target_ps=t['period_ps'],
                         label_sha256=status['label_sha256'],ownership_sha256=sha(p/'logical-v2-grt/ownership-certificate.json')))
    state=read(ROOT/'experiments/arithmetic/backend_usage.json')
    own=[e for e in state['entries'] if str(e.get('admission_id','')).startswith('matrix-nangate45-N34-paired-')]
    jobs=[j for j in state.get('jobs',[]) if str(j.get('admission_id','')).startswith('matrix-nangate45-N34-paired-')]
    if any(e['status'] in ('reserved','unsettled') for e in own) or any(j['status']!='released' for j in jobs):
        raise ValueError('N34 leaves/jobs not settled')
    return dict(status='passed',strict_labels=len(rows),paired_sources=len(a['sources']),native_time_to_ps=1000,
                source_roles=dict(Counter(t['role'] for t in a['tasks'])),labels=rows,
                all_ownership_complete=True,all_CTS_proofs_bound=True,all_exclusive_areas_conserved=True,
                all_paired_tool_hashes_equal=True,paired_ASAP7_manifest_hashes_rechecked=True,
                physical_setup_target_unmet_points=setup_unmet,physical_hold_negative_points=hold_negative,physical_hold_review_points=hold_review,
                own_calls=dict(Counter(e['stage'] or 'support' for e in own)),
                walltime_s=sum(e.get('walltime_s',0) for e in own),CPU_time_s=sum(e.get('CPU_time_s',0) for e in own),
                all_own_leaves_settled=True,all_own_jobs_released=True,
                failed_entries=[dict(id=e['id'],task_id=e.get('task_id'),stage=e['stage'],admission_id=e['admission_id']) for e in own if e['status']=='failed'],
                active_ASAP7_jobs_observed=[dict(admission_id=j['admission_id'],task_id=j['task_id']) for j in state.get('jobs',[]) if j['status']=='active' and not str(j['admission_id']).startswith('matrix-nangate45')])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--package',type=Path,required=True);a=p.parse_args()
    root=a.root.resolve();result=dict(software=software(root,a.package),receipts=receipts(root));write(root/'verification.json',result)
    print(json.dumps({k:{n:v for n,v in x.items() if n!='labels'} for k,x in result.items()},indent=2))
