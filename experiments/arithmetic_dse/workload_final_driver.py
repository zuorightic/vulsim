"""Finite staged measurement driver for the authorized steps 6--8 run.

Calibration results select clocks under the preregistered rule only. The
software selector gets a frozen target list, never application measurements.
All physical jobs, including failed jobs, retain the common ledger history.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import gzip
import math
from pathlib import Path
import shutil
import time
from unittest.mock import patch

from .sampling_time_contract import ROOT,canonical
from .workload_abcd import read,write,sha
from .workload_contracts import load
from .workload_demand import Graph
from .workload_diagnostic import DiagnosticPrices,evaluate
from .workload_final_selection import select_case,BASE
from . import workload_final_backend as physical
from .budget import Ledger

DEFAULT=ROOT.parent/'vulsim-artifacts/workload-equivalent-steps678-v1'


def wait_batch(root):
    while read(root/'progress.json')['status']!='batch_settled':time.sleep(10)
    p=read(root/'progress.json')
    if p['errors']:raise RuntimeError('retained physical failures require review: '+str(p['errors']))


def drive(batches):
    tasks=[];progress={}
    for root in batches:
        a=physical.verify(root);p=read(root/'progress.json')
        if p['status']=='batch_settled':continue
        if p['active']:raise ValueError('already running physical batch')
        attempted=set(p['completed'])|{e['task'] for e in p['errors']}
        pending=[t for t in a['tasks'] if t['id'] not in attempted]
        p.update(status='running',active=[t['id'] for t in pending]);progress[root]=p
        write(root/'progress.json',p);tasks.extend((root,t) for t in pending)
    with patch.object(physical.predecessor,'verify_admission',physical.verify_admission):
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures={pool.submit(physical.run_task,r,t):(r,t) for r,t in tasks}
            for f in as_completed(futures):
                root,t=futures[f];p=progress[root]
                try:f.result();p['completed'].append(t['id']);print('PHYSICAL_PASS '+t['id'],flush=True)
                except Exception as e:p['errors'].append(dict(task=t['id'],reason=str(e)));print('PHYSICAL_FAIL '+t['id']+' '+str(e),flush=True)
                p['active'].remove(t['id'])
                if not p['active']:p['status']='batch_settled'
                write(root/'progress.json',p)
    return {str(r):read(r/'progress.json') for r in batches}


def calibration(root,ids):
    tasks=[];prices=DiagnosticPrices(read(BASE/'diagnostic-model.json'))
    for cid in ids:
        c=read(root/'software'/cid/'static-pool.json')['C'];f=Path(c['folder']);g=Graph(read(c['graph']))
        p=evaluate(g,dict(placement=c['placement']),read(f/'state.json'),read(f/'owners.json'),prices)
        T=max(1000,math.ceil(p['critical_required_ps']/100)*100)
        tasks.append(dict(id=cid+'-clock-probe',case=cid,method='C',rtl=str(f/'workload.sv'),period_ps=T,
            simulation_status='passed',simulation_receipt=str(f/'functional-receipt.json'),large=True,
            software_complete_period_ps=p['critical_required_ps']))
        Graph.origins.cache_clear();Graph.roots.cache_clear()
    folder=root/'calibration-last-two'
    if not folder.exists():physical.admit(folder,tasks,'clock_calibration')
    return folder


def freeze_available_targets(root):
    targets=root/'targets';targets.mkdir(exist_ok=True);cases={c['id']:c for c in load()['cases']}
    for batch in ('calibration-add512','calibration-first-five','calibration-last-two'):
        if not (root/batch/'admission.json').exists():continue
        a=physical.verify(root/batch)
        for task in a['tasks']:
            p=root/batch/'runs'/task['id']/'clock-readout/result.json'
            if not p.exists():continue
            r=read(p);t=r['full_setup_minimum_period_ps']
            value=dict(case=task['case'],L=cases[task['case']]['formal_targets'][0]['L'],
                targets_ps=[math.ceil(k*t/100)*100 for k in (1.05,1.45)],anchor_ps=t,
                clock_readout_sha256=sha(p),role='clock_calibration_only',application_PPA_for_D_selection=False)
            out=targets/(task['case']+'.json')
            if out.exists() and read(out)!=value:raise ValueError('clock target freeze changed')
            if not out.exists():write(out,value)


def freeze_targets(root):
    freeze_available_targets(root);targets=root/'targets'
    rows=[read(targets/(c['id']+'.json')) for c in load()['cases']]
    write(root/'target-matrix.json',dict(version='nine-case-calibrated-clock-matrix-v1',rows=rows,
        groups=sum(len(r['targets_ps']) for r in rows),rule=read(root/'software/protocol.json')['calibration_rule'],
        calibration_labels_for_model=False,final_D_labels_for_target=False))
    print('TARGET_MATRIX '+str([(r['case'],r['targets_ps']) for r in rows]),flush=True)
    return rows


def final_tasks(root,ids,name):
    rows=[];tasks={}
    for cid in ids:
        result=read(root/'software'/cid/'final-selections.json')
        for r in result['records']:
            row=dict(case=cid,target=r['target'],methods={})
            for method,m in r['methods'].items():
                identity=m['rtl_sha256']+'-'+str(r['target']['T_ps'])
                task_id=cid+'-T'+str(r['target']['T_ps'])+'-'+m['rtl_sha256'][:12]
                row['methods'][method]=dict(m,task_id=task_id)
                if identity not in tasks:
                    tasks[identity]=dict(id=task_id,case=cid,rtl=m['rtl'],period_ps=r['target']['T_ps'],
                        simulation_status='passed',simulation_receipt=m['simulation_receipt'],
                        large=cid not in ('mac32','add512'),shared_methods=[])
                tasks[identity]['shared_methods'].append(method)
            rows.append(row)
    folder=root/name
    value=dict(records=rows,physical_batch=str(folder),main_methods=4*len(rows),attribution_methods=len(rows),
        unique_tasks=len(tasks),same_RTL_T_profile_deduplicated=True,application_PPA_for_selection=False)
    methods=root/(name+'-methods.json')
    if methods.exists() and read(methods)!=value:raise ValueError('final method selection changed')
    if not methods.exists():write(methods,value)
    inputs=[methods,BASE/'diagnostic-model.json',root/'software/characterization-contract.json',root/'software/protocol.json']
    for cid in ids:
        inputs.extend([root/'targets'/(cid+'.json'),root/'software'/cid/'final-selections.json'])
        inputs.extend(p for p in (root/'software/selected'/cid).rglob('*') if p.is_file())
    inputs.extend(ROOT/'experiments/arithmetic_dse'/n for n in (
        'workload_final_adapter.py','workload_final_selection.py','workload_final_software.py','workload_final_prices.py',
        'workload_tight_equivalent.py','workload_equivalent.py','equivalent_period.py','local_budget.py','workload_diagnostic.py','workload_abcd.py'))
    freeze=root/(name+'-selection-freeze.json');identity=dict(version='nine-case-complete-selection-freeze-v1',
        files={str(p):sha(p) for p in inputs},application_PPA_for_selection=False,
        model_refitted=False,qualified=False,cases=ids,frozen_before_final_measurement=True)
    if freeze.exists() and read(freeze)!=identity:raise ValueError('complete selection freeze changed')
    if not freeze.exists():write(freeze,identity)
    for task in tasks.values():task.update(complete_selection_freeze=str(freeze),complete_selection_freeze_sha256=sha(freeze))
    if not folder.exists():physical.admit(folder,list(tasks.values()),'final_evaluation')
    return folder


def report(root,batch_names=('final-mac-add','final-remaining-seven')):
    records=[];failures=[]
    for name in batch_names:
        p=root/(name+'-methods.json')
        if not p.exists():continue
        doc=read(p);batch=Path(doc['physical_batch'])
        for row in doc['records']:
            for method,m in row['methods'].items():
                out=batch/'runs'/m['task_id'];p=out/'clock-readout/result.json'
                entry=dict(case=row['case'],target_ps=row['target']['T_ps'],L=m['L'],II=1,
                    additional_input_service_cycles=1,method=method,task_id=m['task_id'],rtl_sha256=m['rtl_sha256'],
                    grammar=m['grammar'],prediction=m['prediction'],qualification='diagnostic_only')
                if p.exists():
                    r=read(p);metric=read(out/'manifest.json')['metrics'][-1];t=r['full_setup_minimum_period_ps'];a=r['area_um2']
                    entry.update(status='measured_grt',area_um2=a,Tmin_ps=t,frequency_MHz=1e6/t,
                        sequential_area_um2=metric['sequential_area_um2'],sequential_cells=metric['sequential_cells'],
                        combinational_and_buffer_area_um2=metric['functional_cell_area_um2']-metric['sequential_area_um2'],
                        physical_only_area_um2=metric['physical_only_area_um2'],
                        area_breakdown_scope='functional combinational includes shared buffers; shared is not separately attributed in mapped area',
                        setup_met=t<=entry['target_ps'],hold_WNS_ps=r['hold_WNS_ps'],hold_met=r['hold_WNS_ps']>=0,
                        hold_review_required=r['hold_review_required'],timing_coverage_complete=metric['timing_coverage_complete'],
                        period_error=m['prediction']['critical_required_ps']/t-1,
                        area_error=m['prediction']['total_area_um2']/a-1,clock_readout_sha256=sha(p))
                else:
                    manifest=read(out/'manifest.json') if (out/'manifest.json').exists() else {}
                    entry.update(status=manifest.get('status','not_measured'),failure_reason=manifest.get('failure_reason'))
                    failures.append(dict(case=entry['case'],T=entry['target_ps'],method=method,status=entry['status'],reason=entry['failure_reason']))
                records.append(entry)
    main=[r for r in records if r['method'] in ('A','B','C','D')];measured=[r for r in main if r['status']=='measured_grt']
    summary=dict(version='equivalent-nine-case-ABCD-grt-v1',main_records=len(main),main_measured=len(measured),
        required_main_records=76,physical_comparison_complete=len(main)==len(measured)==76,
        qualification='diagnostic_only',precision_qualified=False,records=records,failures=failures,
        final_PPA_for_model_or_selection=False,ledger=Ledger().summary(),
        targets=read(root/'target-matrix.json') if (root/'target-matrix.json').exists() else None)
    write(root/'comparison.json',summary)
    text=['# 九例等效预算版本 ABCD 后端比较','',
        f"主表已实测 {len(measured)}/76；模型保持诊断身份。工艺 ASAP7 RVT TT，post-CTS grt 估计 RC；setup 使用完整 RR／IR／RO 最小周期，hold 单独报告。",'',
        '| 案例 | T / L | 方法 | 块宽 / limb | 面积 µm² | Tmin ps | MHz | setup | hold WNS ps | 周期 / 面积误差 |',
        '| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- |']
    for r in records:
        if r['status']=='measured_grt':
            cells=[r['case'],f"{r['target_ps']} / {r['L']}",r['method'],' / '.join(map(str,r['grammar'])),
                f"{r['area_um2']:.2f}",f"{r['Tmin_ps']:.2f}",f"{r['frequency_MHz']:.2f}",str(r['setup_met']),
                f"{r['hold_WNS_ps']:.3f}",f"{r['period_error']:+.2%} / {r['area_error']:+.2%}"]
        else:cells=[r['case'],f"{r['target_ps']} / {r['L']}",r['method'],' / '.join(map(str,r['grammar'])),'—','—','—',r['status'],'—','—']
        text.append('| '+' | '.join(cells)+' |')
    text+=['','`same_policy_static` 是相同候选池、相同搜索额度和完整评分器下的静态价格归因，不替换正式 C。',
        '','边界外推：Sub／Compare 使用训练源均衡池化的公共 H；功能消费者绑定实际 Boolean-cover 所有者。原四类 H 和响应参数不变；S／shared／嵌入资格缺口保留。',
        '','实际映射仍使用整机 T。等效 T 用于复用单算子预测函数，没有施加逐算子 ABC 约束。面积为排除 filler、包含 taps 的标准单元总面积。']
    (root/'comparison.md').write_text('\n'.join(text)+'\n');return summary


def run(root):
    root=Path(root).resolve();write(root/'driver-start.json',dict(source_sha256=sha(__file__),starting_ledger=Ledger().summary(),
        authorized_steps=[6,7,8],finite_cases=9,targets=19,automatic_physical_retries=0))
    wait_batch(root/'calibration-first-five')
    last=calibration(root,['montgomery256','ntt8x64'])
    mac=final_tasks(root,['mac32','add512'],'final-mac-add')
    freeze_available_targets(root)
    def early_selection():
        for cid in ('mul128','dot16','horner64','barrett64','karatsuba256'):
            r=read(root/'targets'/(cid+'.json'));select_case(root/'software',cid,r['targets_ps'])
    with ThreadPoolExecutor(max_workers=1) as software:
        early=software.submit(early_selection)
        drive([last,mac]);wait_batch(last);early.result()
    matrix=freeze_targets(root)
    # Final target matrix is now immutable; no final D result exists for these
    # seven cases. Only the pure selector receives these target numbers.
    for r in matrix:
        if r['case'] in ('mac32','add512'):continue
        select_case(root/'software',r['case'],r['targets_ps'])
    remaining=final_tasks(root,[r['case'] for r in matrix if r['case'] not in ('mac32','add512')],'final-remaining-seven')
    drive([remaining]);summary=report(root)
    print('FINAL_STATUS '+str({k:summary[k] for k in ('main_records','main_measured','physical_comparison_complete')}),flush=True)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['run','report']);p.add_argument('--root',type=Path,default=DEFAULT)
    a=p.parse_args();print(run(a.root) if a.action=='run' else report(a.root))
