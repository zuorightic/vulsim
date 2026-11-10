"""Real-snapshot regression for missing ordinary Liberty cell arcs; no EDA."""
import argparse
from copy import deepcopy
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse import model_qualification_labels as labels
from experiments.arithmetic_dse import model_physical_path_v2 as timing
from regression.arithmetic_physical_label_contract import packet,verify as original_checks

SOURCE_NAMES=['experiments/arithmetic_dse/model_physical_labels_v2.py',
    'experiments/arithmetic_dse/model_physical_path_v2.py',
    'experiments/arithmetic_dse/model_qualification_labels.py',
    'regression/arithmetic_physical_label_contract.py',
    'regression/arithmetic_liberty_arc_contract.py']


def freeze(out):
    out.mkdir(parents=True,exist_ok=False)
    for name in SOURCE_NAMES:
        dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
    write(out/'source-sha256.json',{name:sha(ROOT/name) for name in SOURCE_NAMES})


def witness(raw,kind):
    paths=([points for node in raw['nodes'].values() for points in node['output_paths'].values()]
        if kind=='independent_node' else [row['points'] for row in raw['data_paths'].values()])
    found=[]
    for points in paths:
        for (a,_),(b,_) in zip(points,points[1:]):
            ca,pa=a.rsplit('/',1);cb,pb=b.rsplit('/',1)
            if ca!=cb:continue
            master=raw['instances'][ca];cell=raw['liberty'][master]
            if cell['sequential'] or cell['pins'][pa]['direction']!='input' or cell['pins'][pb]['direction']!='output':continue
            arc=[pa,pb]
            if arc not in cell.get('timing_arcs',[]):raise ValueError('unmodified actual path already lacks Liberty arc')
            found.append(dict(master=master,arc=arc,from_pin=a,to_pin=b))
    if not found:raise ValueError('no real ordinary cell-arc witness')
    return next((w for w in found if w['master']=='BUFx2_ASAP7_75t_R' and w['arc']==['A','Y']),found[0])


def remove_arc(raw,w):
    broken=deepcopy(raw);arcs=broken['liberty'][w['master']]['timing_arcs'];arcs.remove(w['arc'])
    if w['arc'] in arcs:raise ValueError('duplicate Liberty arc')
    return broken


def through_data(raw,c):
    """Exercise the Q-to-D reader independently of the node-maximum reader."""
    canonical=labels.canonical
    instances={canonical(k):v for k,v in raw['instances'].items()}
    nets={canonical(k):dict(v,net=canonical(v['net'])) for k,v in raw['connections'].items()}
    return [timing.decompose([(canonical(p),t) for p,t in row['points']],canonical(row['start']),canonical(row['end']),
        instances,raw['liberty'],nets,c['nodes'],raw['time_to_ps']) for row in raw['data_paths'].values()]


def check(folder,out,reproduce=False):
    freeze(out);admission=read(folder/'admission.json');rows=[];mutations=[]
    if not reproduce:original_checks(folder,out/'original-eight-checks')
    for task in admission['tasks']:
        if reproduce and task['id']!='mul-load-1500':continue
        location=Path(task['inherit_completed']['directory']) if task.get('inherit_completed') else folder/'runs'/task['id']
        for stage in (('synth',) if reproduce else ('synth','grt')):
            raw,c=packet(location,stage);baseline=labels.extract(raw,c['nodes'],c['banks']);saved=read(location/(stage+'-labels.json'))
            if any(saved[k]!=v for k,v in baseline.items()):raise ValueError('unmodified saved labels changed')
            decomposed=through_data(raw,c)
            if decomposed!=baseline['path_decompositions']:raise ValueError('direct through-data read differs')
            rows.append(dict(task=task['id'],stage=stage,operator_delay_ps=baseline['operator_delay_ps'],comb_area_um2=baseline['comb_area_um2'],
                data_setup_slack_ps=baseline['data_setup_slack_ps'],all_saved_label_fields_unchanged=True))
            for kind in ('independent_node','through_data'):
                w=witness(raw,kind);broken=remove_arc(raw,w)
                try:
                    value=labels.extract(broken,c['nodes'],c['banks']) if kind=='independent_node' else through_data(broken,c)
                except ValueError as e:
                    if reproduce:raise ValueError('claimed acceptance not reproduced') from e
                    if 'actual Liberty timing arc' not in str(e):raise ValueError('negative failed for an unrelated reason') from e
                    outcome='rejected';error=str(e)
                else:
                    if not reproduce:raise ValueError('missing ordinary Liberty timing arc accepted '+task['id']+'/'+stage+'/'+kind)
                    expected=baseline if kind=='independent_node' else decomposed
                    if value!=expected:raise ValueError('accepted mutation unexpectedly changed label')
                    outcome='accepted_with_unchanged_labels';error=None
                mutations.append(dict(task=task['id'],stage=stage,path_kind=kind,deleted_only_one_master_arc=True,**w,outcome=outcome,error=error))
    direction_checks=[]
    if not reproduce:
        # Explicit but direction-invalid arcs must still fail the path-kind rule.
        for a,b in [('A','B'),('Y','A')]:
            cell=dict(sequential=False,pins={'A':dict(direction='input'),'B':dict(direction='input'),'Y':dict(direction='output')},timing_arcs=[[a,b]])
            try:timing.verify_combinational_arc(cell,a,b)
            except ValueError as e:
                if 'invalid combinational cell timing step' not in str(e):raise
                direction_checks.append([a,b])
            else:raise ValueError('direction-invalid explicit arc accepted')
    proof=dict(status='reproduced' if reproduce else 'passed',points=len({r['task'] for r in rows}),stages=len(rows),rows=rows,
        single_arc_mutations=mutations,invalid_direction_arcs_rejected=direction_checks,
        original_eight_checks_replayed=not reproduce,source_role='not_training',new_EDA_calls=0,new_training_rows=0,
        physical_measurements_reused=True,saved_label_values_unchanged=True)
    write(out/'proof.json',proof)
    print(dict(status=proof['status'],stages=len(rows),single_arc_mutations=len(mutations),invalid_direction_arcs_rejected=len(direction_checks)),flush=True)
    return proof


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('reproduce','verify'));p.add_argument('--folder',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    check(a.folder.resolve(),a.out.resolve(),a.action=='reproduce')
