"""Verify the independent step5 placement acceptance without build or EDA."""
import hashlib
import json
from pathlib import Path
from .budget import usage, cpu_seconds
from .freeze_history import historical_placement_analyzer

ROOT=Path(__file__).resolve().parents[2]


def verify(root=ROOT):
    root=Path(root)
    freeze=json.loads((root/'experiments/arithmetic/placement_freeze_v1.json').read_text())
    def check(relative,expected):
        path=root/relative
        if not path.is_file():
            from .freeze_history import source_location
            path=source_location(root,'experiments/arithmetic/placement_freeze_v1.json',relative,expected)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise ValueError(f'SHA-256 mismatch: {relative}')
    for relative,expected in freeze['files_sha256'].items():
        from .freeze_history import source_location
        path=source_location(root,'experiments/arithmetic/placement_freeze_v1.json',relative,expected)
        check(str(path.relative_to(root)),expected)
    parent=freeze['parent'];check(parent['path'],parent['sha256'])
    from .mul_split_evidence import verify as verify_parent
    historical=verify_parent(root)
    check(freeze['evidence_index'],freeze['evidence_index_sha256'])
    index=json.loads((root/freeze['evidence_index']).read_text())
    for item in index['files']:check(item['path'],item['sha256'])
    ev=root/freeze['evidence_directory']
    study_source=source_location(root,'experiments/arithmetic/placement_freeze_v1.json',freeze['study'],freeze['files_sha256'][freeze['study']])
    config=json.loads(study_source.read_text())
    report=json.loads((ev/'regression.json').read_text())
    check(str(study_source.relative_to(root)),report['study_sha256'])
    for name,expected in report['artifacts_sha256'].items():check(str((ev/name).relative_to(root)),expected)
    graph=json.loads((ev/'graph.json').read_text())
    analysis=historical_placement_analyzer(root)(graph,config)
    if analysis!=json.loads((ev/'analysis.json').read_text()):raise ValueError('independent analysis differs')
    if report['status']!='passed' or report['evidence_type']!=analysis['evidence_type']:
        raise ValueError('acceptance classification differs')
    if set(report['negative_checks_rejected'])!={'materialized_width','cost','reported_stage_delay'}:
        raise ValueError('missing negative checks')
    if report['preference_selection_demonstrated'] or any(report['new_PPA_calls'].values()):
        raise ValueError('unsupported preference claim or unexpected PPA')
    if (ev/'mul32_split16.sv').read_bytes()!=(root/'experiments/arithmetic/evidence/step5/mul32_split16.sv').read_bytes():
        raise ValueError('production RTL differs from original frozen run')
    rows=[tuple(int(v,16) for v in line.split()) for line in (ev/'vectors.txt').read_text().splitlines()]
    observed=(ev/'rtl.log').read_text().splitlines()
    if len(rows)!=len(observed) or len(rows)!=report['cycles']:raise ValueError('incomplete functional trace')
    history=[];last=0;products=bubbles=resets=0
    for cycle,((a,b,iv,rst),line) in enumerate(zip(rows,observed)):
        if not rst:history=[];valid=0;last=0;resets+=1
        else:
            history.append((iv,a*b));valid=int(len(history)>=3 and history[-3][0])
            if valid:last=history[-3][1];products+=1
            else:bubbles+=1
        if [int(v,16) for v in line.split()]!=[last,valid]:raise ValueError(f'functional mismatch at {cycle}')
    if (report['valid_checks']!=len(rows) or report['valid_product_checks']!=products
        or report['bubble_hold_checks']!=bubbles or report['reset_checks']!=resets):
        raise ValueError('functional aggregate differs')
    before=json.loads((ev/'usage_before.json').read_text());after=json.loads((ev/'usage_checkpoint.json').read_text())
    if after['entries'][:len(before['entries'])]!=before['entries']:raise ValueError('historical charges changed')
    new=after['entries'][len(before['entries']):]
    if len(new)!=len(report['commands']) or any(e['stage'] is not None or e['status']!='completed' for e in new):
        raise ValueError('unexpected or unsettled leaf charges')
    commands={item['id']:item for item in json.loads((ev/'command_index.json').read_text())}
    if set(commands)!={e['id'] for e in new}:raise ValueError('incomplete command index')
    for e in new:
        item=commands[e['id']];record=json.loads((root/item['command']).read_text())
        if (record['exit_code'] or e['exit_code']!=record['exit_code'] or e['walltime_s']!=record['walltime_s']
            or record['cleanup']['remaining_live_pids'] or abs(cpu_seconds(root/item['resources'])-e['CPU_time_s'])>1e-8):
            raise ValueError('command/resource settlement mismatch')
    total=usage(after['entries'])
    if total!=after['usage'] or total['pending'] or report['usage_before']!=usage(before['entries']) or report['usage_after']!=total:
        raise ValueError('ledger summaries differ')
    resources=json.loads((ev/'resources.json').read_text())
    if resources['cumulative_usage']!=total or resources['new_usage']!=usage(new):
        raise ValueError('resource summary differs from leaf ledger')
    live=root/'experiments/arithmetic/backend_usage.json'
    if live.exists() and json.loads(live.read_text())['entries'][:len(after['entries'])]!=after['entries']:
        raise ValueError('live ledger dropped archived charges')
    return {'status':'passed','freeze':freeze['version'],'parent':historical['freeze'],
            'source_files':len(freeze['files_sha256']),'evidence_files':len(index['files']),
            'production_evidence_type':analysis['evidence_type'],
            'preference_selection_demonstrated':False,'schedule_trials':analysis['schedule_trials'],
            'dependency_legal_trials':analysis['dependency_legal_trials'],
            'default_feasible_count':analysis['default_feasible_count'],
            'diagnostic_feasible_count':analysis['diagnostic']['feasible_count'],
            'functional_cycles':len(rows),'new_support_calls':len(new),
            'new_PPA_calls':report['new_PPA_calls'],'cumulative_usage':total,
            'requires_build_directory':False,'requires_EDA_tools':False}


if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))
