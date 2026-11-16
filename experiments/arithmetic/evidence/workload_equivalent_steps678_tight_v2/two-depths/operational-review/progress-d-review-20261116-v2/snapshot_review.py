"""Read frozen receipts and publish an independent audit snapshot; no EDA."""
import collections
import datetime
import gzip
import hashlib
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path('/home/zyrv/vulsim')
sys.path.insert(0, str(ROOT))
from experiments.arithmetic_dse import workload_reference_A as reference
from experiments.arithmetic_dse import workload_montgomery_reference_retest as montgomery
from experiments.arithmetic_dse.workload_equivalent import score_key

LIVE = ROOT.parent / 'vulsim-artifacts/workload-equivalent-two-depths-v1'
OUT = pathlib.Path(__file__).resolve().parent
REVIEW = OUT.parent
CURRENT = REVIEW.parent / 'original-A-reference-v1'


def read(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(name, doc):
    (OUT / name).write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n')


def summary(p):
    return {k: p[k] for k in ('critical_required_ps', 'total_area_um2', 'target_met', 'violation_ps')}


def main():
    prior = read(REVIEW / 'd-split-placement-review-20261116-v1.json')
    sources = [pathlib.Path(p) for p in prior['frozen_sources_sha256']]
    sources += [pathlib.Path(reference.__file__), pathlib.Path(montgomery.__file__)]
    sources += [ROOT / 'rtlzz/src/backend' / n for n in ('arithmetic_state.cpp', 'mul_split.cpp', 'beir.cpp')]
    before = {str(p): sha(p) for p in sources}
    reference.publish(LIVE)
    montgomery.publish(LIVE)
    for name in ('comparison.md', 'comparison.json', 'comparison.csv', 'A-references.json', 'A-references.csv'):
        shutil.copyfile(CURRENT / name, OUT / name)
    comparison = read(OUT / 'comparison.json')
    selected = []
    pools = []
    for plan in sorted((LIVE / 'plans').glob('*.json')):
        doc = read(plan)
        selpath = pathlib.Path(doc['selection'])
        for group in read(selpath)['records']:
            m = group['methods']['D']
            T = group['target']['T_ps']
            folder = pathlib.Path(m['rtl']).parent
            tracepath = folder / 'complete-budget-trace.json.gz'
            trace = json.loads(gzip.decompress(tracepath.read_bytes()))
            p = trace['prediction']
            ix = int(trace['best_variant_id'].split(':')[0])
            entry = trace['trace'][ix]
            best = next(v for v in entry['variants'] if v['id'] == trace['best_variant_id'])
            taus = [q.get('target_ps', q.get('flow_context', {}).get('target_period_ps'))
                    for q in best['actual_queries'].values()]
            positive = collections.Counter(m['placement'][o['node']] for o in p['owners'] if o['delay_ps'] > 0)
            sim = read(folder / 'functional-receipt.json')
            row = dict(case=doc['case'], L=m['L'], T_ps=T, grammar=m['grammar'], rtl=str(folder / 'workload.sv'),
                rtl_sha256=m['rtl_sha256'], selection_file=str(selpath), selection_sha256=sha(selpath),
                trace_sha256=sha(tracepath), prediction=summary(p), stages=p['stages'],
                stage_data_bits=[sum(w) for w in p['S']['projection']['stage_words']],
                empty_priced_stages=[i for i in range(m['L']) if positive[i] == 0],
                functional_receipt_valid=(sim['status'] == 'passed' and sim['rtl_sha256'] == sha(folder / 'workload.sv') == m['rtl_sha256']),
                prediction_matches_receipt=all(abs(p[k] - m['prediction'][k]) < 1e-8
                    for k in ('critical_required_ps', 'total_area_um2')),
                local_requests_unmet=best['local_requests_unmet'], dynamic_queries=len(taus),
                equivalent_T_range_ps=[min(taus), max(taus)] if taus else [],
                equivalent_T_equal_global_count=sum(t == T for t in taus))
            selected.append(row)
            poolpath = selpath.parents[1] / doc['case'] / f'scores-T{T}' / 'pool-summary.json.gz'
            if not poolpath.exists():
                pools.append(dict(case=doc['case'], L=m['L'], T_ps=T,
                    status='Inherited MAC32 L3 step45 selection; prior common-pool audit retained'))
                continue
            candidates = json.loads(gzip.decompress(poolpath.read_bytes()))
            valid = [c for c in candidates if c['model']]
            winner = min(valid, key=lambda c: score_key(c['model']) + (c['id'],))
            baselines = {}
            for name in ('B', 'C'):
                matching = [c for c in valid if c['rtl_sha256'] == group['methods'][name]['rtl_sha256']]
                baselines[name] = [dict(id=c['id'], origin=c['origin'], prediction=summary(c['model'])) for c in matching]
            pools.append(dict(case=doc['case'], L=m['L'], T_ps=T, pool_file=str(poolpath), pool_sha256=sha(poolpath),
                pool_matches_frozen_hash=(sha(poolpath) == group['search']['pool_summary_sha256']),
                candidates=len(candidates), complete=len(valid), feasible=sum(c['model']['target_met'] for c in valid),
                selected_id=group['search']['selected_id'],
                score_order_correct=(winner['id'] == group['search']['selected_id']),
                selected_RTL_matches=(winner['rtl_sha256'] == m['rtl_sha256']), baseline_same_RTL_candidates=baselines))
    active = []
    for job in comparison['active_jobs']:
        batch = LIVE / ('reference-successors' if job['admission_id'] == 'matrix-montgomery-A-retest-v1' else 'backend') / job['admission_id']
        run = batch / 'runs' / job['task_id']
        manifest = read(run / 'manifest.json')
        logs = sorted((run / 'logs').rglob('*.log'), key=lambda p: p.stat().st_mtime, reverse=True)
        leaf = logs[0] if logs else run / 'grt.log'
        active.append(dict(job, manifest_status=manifest['status'], latest_leaf=str(leaf),
            latest_leaf_mtime=datetime.datetime.fromtimestamp(leaf.stat().st_mtime, datetime.timezone.utc).isoformat(),
            leaf_tail=leaf.read_text(errors='replace').splitlines()[-10:],
            completed_commands=[{k: c.get(k) for k in ('log','walltime_s','exit_code','sampled_process_tree_peak_rss_KiB')}
                                for c in manifest.get('commands',[])]))
    failures = []
    for r in comparison['BCD_records']:
        if r['status'] != 'failed':
            continue
        run = pathlib.Path(r['measurement']['run'])
        log = run / 'grt.log'
        errors = [line for line in log.read_text(errors='replace').splitlines()
                  if any(k in line for k in ('[ERROR','Signal ','invalid chunk','Segmentation','malloc'))] if log.exists() else []
        failures.append(dict(case=r['case'],L=r['L'],T_ps=r['T_ps'],method=r['method'],
            reason=r['failure_reason'],run=str(run),error_lines=errors[-5:]))
    nttlog = LIVE.parent / 'workload-equivalent-two-depths-v1-controller.log'
    nttlines = [line for line in nttlog.read_text(errors='replace').splitlines()
                if 'MATRIX_SOFTWARE_DONE' in line and 'ntt8x64' in line]
    ntt = dict(controller_log=str(nttlog), exit_records=nttlines,
        state='software_failed_without_ready_receipt', published_placeholder='software_pending',
        current_software_workers=read(LIVE / 'original-A-reference-v1/controller-progress.json')['software_active'],
        software_log_tail=(LIVE / 'software-logs/ntt8x64-L8.log').read_text(errors='replace').splitlines()[-6:])
    montpath = LIVE / 'reference-successors/matrix-montgomery-A-retest-v1'
    save('montgomery-progress.json', dict(progress=read(montpath / 'progress.json'),
        manifest=read(montpath / 'runs/montgomery256-A-reference-T27000/manifest.json')))
    measured = [r for r in comparison['BCD_records'] if r['status'] == 'measured_grt']
    stats = dict(BCD_statuses=comparison['BCD_statuses'], A_measured=comparison['A_reference_measured'],
        BCD_measured=len(measured), independent_measured_BCD_runs=len({r['measurement']['run'] for r in measured}),
        setup_met_by_method=dict(collections.Counter(r['method'] for r in measured if r['setup_met'])),
        setup_and_hold_met_by_method=dict(collections.Counter(r['method'] for r in measured if r['setup_met'] and r['hold_met'])),
        hold_violations=[{k:r[k] for k in ('case','L','T_ps','method','hold_WNS_ps')} for r in measured if not r['hold_met']],
        selected_D=len(selected), local_pool_checks=sum('candidates' in p for p in pools),
        local_pool_candidates=sum(p.get('candidates',0) for p in pools),
        functional_receipts_valid=sum(r['functional_receipt_valid'] for r in selected),
        prediction_receipts_match=sum(r['prediction_matches_receipt'] for r in selected),
        dynamic_queries=sum(r['dynamic_queries'] for r in selected),
        equivalent_T_equal_global=sum(r['equivalent_T_equal_global_count'] for r in selected),
        D_with_unmet_local_request=sum(bool(r['local_requests_unmet']) for r in selected))
    after = {str(p): sha(p) for p in sources}
    assert before == after, 'Frozen sources changed during audit'
    assert all(r['functional_receipt_valid'] and r['prediction_matches_receipt'] for r in selected)
    assert all(all(p[k] for k in ('pool_matches_frozen_hash','score_order_correct','selected_RTL_matches'))
               for p in pools if 'candidates' in p)
    output = dict(version='progress-D-review-20261116-v2', at=comparison['at'],
        new_EDA_calls=0,new_model_fits=0,live_queue_modified=False, frozen_sources_unchanged=True,
        source_sha256=before, stats=stats, selected_D=selected, pool_checks=pools,
        active_physical_tasks=active, backend_failures=failures, ntt_L8_software=ntt,
        qualification='diagnostic_only; analysis is not model refit, D reselection or final model qualification')
    save('review.json',output)
    lines=['# 当前D的冻结选择与流水阶段（预测）','',comparison['at'],'',
        '以下是模型预测，不能作为后端实测。功能收据和RTL哈希逐项核对；不新增候选、不重选D。','',
        '| 案例 | L/T ps | grammar | 完整周期ps | 逐级周期ps | 逐级数据变量位 | 空正价算术级（0起） |',
        '| --- | --- | --- | ---: | --- | --- | --- |']
    for r in selected:
        lines.append('| '+' | '.join([r['case'],f'{r["L"]}/{r["T_ps"]}',str(r['grammar']),
            f'{r["prediction"]["critical_required_ps"]:.3f}',
            ' / '.join(f'{s["required_ps"]:.1f}' for s in r['stages']),
            ' / '.join(str(n) for n in r['stage_data_bits']), str(r['empty_priced_stages'])])+' |')
    (OUT / 'D-stage-review.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(stats,ensure_ascii=False,indent=2))
    print('NTT',json.dumps(ntt,ensure_ascii=False))


if __name__ == '__main__':
    main()
