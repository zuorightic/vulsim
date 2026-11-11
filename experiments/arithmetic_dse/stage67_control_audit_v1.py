"""Expose every non-arithmetic timing class and frozen guard ownership.

No area/timing fit. A class without a dedicated guard stays explicit, even
when the complete measured shell happens to pass its setup constraint.
"""
import argparse
from collections import defaultdict
from pathlib import Path
from .model_fast_preflight import read,write


def audit(root,out):
    a=read(root/'admission.json');points=[];groups=defaultdict(list);missing=set();class_false=[]
    for t in a['tasks']:
        export=read(Path(t['input_directory'])/'export.json');v=next(v for v in export['variants'] if v['id']==t['placement'])
        target=next(x for x in v['targets'] if x['target_ps']==t['period_ps']);checks=target['diagnostics']['nonarithmetic_checks']
        label=read(root/'analysis-v1'/(t['id']+'-grt-labels.json'));paths=defaultdict(list)
        for p in label['functional_paths']:paths[p['path_class'],p['stage']].append(p)
        rows=[]
        for (name,stage),pp in sorted(paths.items()):
            if name in ('native_data','external_data'):continue
            guards=[x for x in checks if x['path_class']==name and x['stage']==stage]
            observed=min(x['slack_ps'] for x in pp);entry=dict(path_class=name,stage=stage,dynamic_endpoints=len(pp),worst_setup_slack_ps=observed,
                dedicated_guard_present=bool(guards),predicted_guard_violation_ps=max((x['violation_ps'] for x in guards),default=None))
            if not guards:missing.add(name)
            elif entry['predicted_guard_violation_ps']<=0 and observed<0:class_false.append(dict(task=t['id'],**entry))
            groups[name].append(entry);rows.append(entry)
        points.append(dict(task=t['id'],target_ps=t['period_ps'],classes=rows))
    result=dict(version='nonarithmetic-guard-audit-v1',status='measured_classes_audited_explicit_guard_gaps_preserved' if missing else 'all_measured_classes_have_guards',points=points,
        classes={name:dict(banks=len(rows),dynamic_endpoints=sum(x['dynamic_endpoints'] for x in rows),worst_setup_slack_ps=min(x['worst_setup_slack_ps'] for x in rows)) for name,rows in groups.items()},
        classes_without_dedicated_guard=sorted(missing),class_false_feasible=class_false,
        meaning='complete-shell false feasibility is separately evaluated; absent dedicated reset/control price never receives inferred zero delay',
        no_parameter_or_guard_change=True,full_D_ready=False)
    write(out,result);print({k:result[k] for k in ('status','classes_without_dedicated_guard','class_false_feasible')},flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();audit(a.root.resolve(),a.out.resolve())
