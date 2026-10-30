"""Verify step5 source, archived RTL/STA and all new ledger charges without EDA."""
import gzip
import hashlib
import json
from pathlib import Path
from .backend import stage_metrics
from .budget import usage,cpu_seconds
from .characterization import mapped_netlist_hash
from .timing_evidence import critical_path,master_inventory

ROOT=Path(__file__).resolve().parents[2]
def verify(root=ROOT):
    root=Path(root);relative='experiments/arithmetic/mul_split_freeze_v1.json'
    freeze=json.loads((root/relative).read_text())
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    def check(rel,expected):
        if digest(root/rel)!=expected:raise ValueError(f'SHA-256 mismatch: {rel}')
    for rel,expected in freeze['files_sha256'].items():check(rel,expected)
    for rel,expected in freeze['parents_sha256'].items():check(rel,expected)
    check(freeze['evidence_index'],freeze['evidence_index_sha256'])
    index=json.loads((root/freeze['evidence_index']).read_text())
    for item in index['files']:check(item['path'],item['sha256'])
    ev=root/freeze['evidence_directory']
    # Historical evidence remains history; its source is explicitly preserved.
    from .evidence import verify_backend_evidence
    from .regions_evidence import verify as verify_regions
    backend=verify_backend_evidence(root);regions=verify_regions(root)
    config=json.loads((root/'experiments/arithmetic_dse/configs/step5_pilot_v1.json').read_text())
    study=json.loads((ev/'physical_study.json').read_text())
    check('experiments/arithmetic_dse/configs/step5_pilot_v1.json',study['study_sha256'])
    for item in [config['functional_report'],*config['rtl'].values()]:check(item['path'],item['sha256'])
    for rel,expected in config['source_sha256'].items():
        check(str(Path(freeze['measurement_generator_snapshot'])/rel),expected)
    before=json.loads((ev/'usage_before.json').read_text());after=json.loads((ev/'usage_checkpoint.json').read_text())
    if after['entries'][:len(before['entries'])]!=before['entries']:raise ValueError('historical charges changed')
    new=after['entries'][len(before['entries']):];total=usage(after['entries'])
    calls={k:sum(e['stage']==k for e in new) for k in ['synth','grt','final']}
    if calls!={'synth':2,'grt':2,'final':0} or total['pending']:raise ValueError('unexpected calls or unsettled reservation')
    if total!=after['usage']:raise ValueError('ledger aggregate mismatch')
    resources=json.loads((ev/'resources.json').read_text())
    acceptance=json.loads((ev/'acceptance.json').read_text())
    support=sum(e['stage'] is None for e in new)
    for summary in [resources,acceptance]:
        if (summary['cumulative_usage']!=total or summary['new_support_calls']!=support):
            raise ValueError('acceptance/resource summary differs from ledger')
    if resources['new_experimental_leaf_usage']!=usage(new):raise ValueError('incremental resource summary mismatch')
    if root.joinpath('experiments/arithmetic/backend_usage.json').exists():
        live=json.loads((root/'experiments/arithmetic/backend_usage.json').read_text())
        if live['entries'][:len(after['entries'])]!=after['entries']:raise ValueError('live ledger dropped archived charges')
    audit=after['migrations'][-1]
    if (audit['to_policy_sha256']!=digest(root/'experiments/arithmetic_dse/configs/backend_policy_v5.json')
        or audit['to_checkpoint_sha256']!=digest(ev/'usage_before.json')):raise ValueError('migration binding mismatch')
    commands={item['id']:item for item in json.loads((ev/'command_index.json').read_text())}
    if len(commands)!=len(new):raise ValueError('incomplete leaf command index')
    for e in new:
        item=commands[e['id']];record=json.loads((root/item['command']).read_text())
        if (e['status']!='completed' or e['exit_code']!=record['exit_code']
            or e['walltime_s']!=record['walltime_s'] or record['cleanup']['remaining_live_pids']
            or abs(cpu_seconds(root/item['resources'])-e['CPU_time_s'])>1e-8):
            raise ValueError('leaf command/resource settlement mismatch')
    report=json.loads((ev/'functional_latest/regression.json').read_text())
    if (report['status']!='passed' or report['cycles']!=21197 or report['valid_checks']!=42394
        or report['valid_product_checks']!=30930 or report['bubble_hold_checks']!=11452 or report['reset_checks']!=12
        or report['C_choice_before_PPA']!='mul32_split16'):raise ValueError('incomplete functional evidence')
    for name,expected in report['artifacts_sha256'].items():
        path=ev/'functional_latest'/name
        if digest(path)!=expected:raise ValueError('final functional artifact mismatch')
    for candidate in config['candidates']:
        if (ev/'functional_latest'/(candidate+'.sv')).read_bytes()!=(ev/(candidate+'.sv')).read_bytes():
            raise ValueError('final compiler changed the measured RTL')
    text=(ev/'functional_latest/schedule.txt').read_text()
    if ('baseline bits=48 final bits=32' not in text or 'mul_kernel/mul/0/group0' not in text
        or 'cap=17.000000' not in text):raise ValueError('group-move/diagnostic evidence missing')
    comparison=json.loads((ev/'physical_comparison.json').read_text());cells=json.loads((ev/'liberty_cells.json').read_text())['cells']
    if comparison['status']!='completed' or study['status']!='completed':raise ValueError('incomplete physical pair')
    identities=[]
    for point in comparison['points']:
        candidate=point['candidate'];d=ev/'physical'/candidate;manifest=json.loads((d/'manifest.json').read_text())
        context=manifest['mapping_context'];identities.append(context)
        if hashlib.sha256(json.dumps(context,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=manifest['mapping_context_sha256']:
            raise ValueError('mapping identity mismatch')
        if context['sdc_period_ps']!=1500 or context['abc_target_ps']!=1500:raise ValueError('unexpected measured target')
        if point['input_rtl_sha256']!=config['rtl'][candidate]['sha256']:raise ValueError('physical RTL differs from frozen candidate')
        metrics=json.loads((d/'metrics.json').read_text())
        if metrics!=point['metrics'] or metrics!=manifest['metrics']:raise ValueError('manifest/report metrics differ')
        for m in metrics:
            stage=m['stage'];parsed=stage_metrics(d,stage,cells,1500)
            for key,value in parsed.items():
                if key!='raw_reports_prefix' and m[key]!=value:raise ValueError(f'STA extraction differs: {candidate}/{stage}/{key}')
            if critical_path((d/f'vulsim_{stage}_paths_max.rpt').read_text())!=point['paths'][stage]:raise ValueError('critical path extraction mismatch')
            if master_inventory((d/f'vulsim_{stage}_cells.tsv').read_text())!=point['master_inventory'][stage]:raise ValueError('cell inventory mismatch')
        netlist=gzip.decompress((d/'1_2_yosys.v.gz').read_bytes()).decode()
        if mapped_netlist_hash(netlist)!=metrics[0]['mapped_netlist_sha256']:raise ValueError('mapped netlist hash mismatch')
        rel='experiments/arithmetic_dse/budget.py'
        expected=[value for name,value in manifest['files_sha256'].items() if name.endswith('/'+rel)]
        if len(expected)!=1 or digest(ev/'backend_measurement_source'/rel)!=expected[0]:
            raise ValueError('budget source used for measurement was not preserved')
    if len(identities)!=2 or identities[0]!=identities[1]:raise ValueError('physical control contexts differ')
    compatibility=json.loads((ev/'compatibility/summary.json').read_text())
    if compatibility['status']!='passed' or any(r['exit_code'] for r in compatibility['commands']):raise ValueError('compatibility regression failed')
    for scenario,enabled in [('enabled',True),('disabled',False)]:
        r=json.loads((ev/f'compatibility/regions-{scenario}.json').read_text())
        if r['CIRCT']['enabled']!=enabled or r['region_checks']!='PASS arithmetic regions checks=55':raise ValueError('region/CIRCT compatibility evidence differs')
        if {x['backend']:x['status'] for x in r['VUL_end_to_end']}!={'sim':'passed','native':'passed','circt':'passed' if enabled else 'skipped'}:
            raise ValueError('end-to-end execution/skip evidence differs')
    return {'status':'passed','freeze':freeze['version'],'source_files':len(freeze['files_sha256']),
            'portable_evidence_files':len(index['files']),'functional_cycles_per_candidate':report['cycles'],
            'new_calls':calls,'new_support_calls':sum(e['stage'] is None for e in new),'cumulative_usage':total,
            'historical_backend':backend['freeze'],'historical_regions':regions['freeze'],
            'requires_build_directory':False,'requires_EDA_tools':False,'budget_scope':'pilot funded; bulk actual collection manifest/capacity review pending'}

if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))
