"""Mux-only fitting from eligible source groups; independent cohorts stay sealed."""
import argparse
from collections import Counter
import copy
from importlib.metadata import version
import json
import os
from pathlib import Path
import shutil
import sys

from .budget import Ledger
from .model_collection import sha,write
from .model_features import features,infer
from .model_m2_evaluate import measurement_identity
from .model_m2_fit_v4 import verify_fit as verify_parent,predict,quality,target_key,width_key
from .model_m2_mux_collection import verify as verify_collection,CONFIG
from .model_m2_mux_labels import read_labels,verify_capture_banks
from .model_training import algorithms

ROOT=Path(__file__).resolve().parents[2]
SUFFIX=Path('asap7/arithmetic_probe/base')


def read(path):return json.loads(Path(path).read_text())


def exclusive(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')


def verify_run(directory,t,a,admission_path,entries):
    from .backend import stage_metrics
    from .platforms import verify_wire_readback
    from .sdc import verify_sdc,rtl_ports
    from .model_m2_live_cec_v3 import verify_proof
    m=read(directory/'manifest.json')
    if (m['status']!='completed' or m['task_id']!=t['id'] or m['admission_id']!=a['id'] or m['mux_admission_sha256']!=sha(admission_path)
        or m['platform_profile']['profile_sha256']!=t['profile_sha256'] or m['period_ps']!=t['period_ps'] or m['abc_target_ps']!=1500
        or m['io_delay_max_ps'] is not None or m['threads_per_tool']!=4 or m['budget_purpose']!='characterization'
        or sha(directory/'input.sv')!=t['rtl_sha256'] or sha(directory/'sample-contract.json')!=t['sample_contract_sha256']):
        raise ValueError('Mux actual measurement differs from registered fitting task')
    if len(m['metrics'])!=2 or {s['stage'] for s in m['metrics']}!={'synth','grt'}:raise ValueError('Mux stage coverage incomplete')
    if len({c['log'] for c in m['commands']})!=len(m['commands']):raise ValueError('Mux command log overwritten')
    for c in m['commands']:
        e=entries[c['budget_reservation_id']]
        if (e['status']!='completed' or c['exit_code'] or c['cleanup']['remaining_live_pids'] or e['command']!=c['command']
            or e.get('admission_sha256')!=sha(admission_path) or e.get('task_id')!=t['id']):raise ValueError('Mux fitting leaf not paid/bound')
    for key in ('evidence_sha256','initial_synth_observation_sha256'):
        for name,h in m.get(key,{}).items():
            if sha(directory/name)!=h:raise ValueError('changed Mux raw evidence: '+name)
    reuse=m.get('checkpoint_reuse')
    if reuse:
        source=Path(reuse['source_run']);old=read(source/'manifest.json');net=Path('results')/SUFFIX/'1_2_yosys.v'
        if (sha(source/'manifest.json')!=reuse['source_manifest_sha256'] or reuse['old_ODB_or_SDC_copied']
            or sha(source/net)!=reuse['source_netlist_sha256'] or sha(directory/net)!=reuse['source_netlist_sha256']
            or sha(source/'input.sv')!=t['rtl_sha256'] or old['status']!='completed'):
            raise ValueError('changed Mux exact mapping ancestor')
    cells=read(directory/'liberty_cells.json')['cells'];specs=read(directory/'sample-contract.json')['labels'];rows=[];diagnostics=[]
    for stored in m['metrics']:
        stage=stored['stage'];reports=directory/'reports'/SUFFIX;prefix=reports/('vulsim_'+stage)
        parsed=stage_metrics(reports,stage,cells,t['period_ps'],selected=m['platform_profile'])
        if any(value!=stored[key] for key,value in parsed.items() if key!='raw_reports_prefix'):raise ValueError('Mux actual stage differs')
        labels=read_labels(prefix,directory/'sample-contract.json',parsed['raw_report_units']['time']['to_ps'])
        banks=verify_capture_banks(prefix,directory/'sample-contract.json',cells)
        if labels!=stored['model_labels'] or banks!=stored.get('model_capture_banks',{}):raise ValueError('Mux QD/bank witnesses differ')
        if 'wire_RC_readback' in stored and verify_wire_readback(reports/('vulsim_'+stage+'_layer_rc.tsv'),m['platform_profile'])!=stored['wire_RC_readback']:
            raise ValueError('Mux physical RC differs')
        sdc=directory/'results'/SUFFIX/({'synth':'1_synth','grt':'5_1_grt'}[stage]+'.sdc')
        verify_sdc(sdc.read_text(),m['platform_profile'],t['period_ps'],rtl_ports((directory/'input.sv').read_text(),t['top']))
        instances=[line.split('\t')[:2] for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines()];by_id={v['id']:v for v in labels}
        for s in specs:
            label=by_id[s['id']]
            area=sum(cells[master]['area_um2'] for name,master in instances if master in cells and not cells[master]['sequential'] and name.startswith(s['arithmetic_scope']))
            if area<=0:raise ValueError('missing Mux core area')
            rid=t['id']+'/'+s['id']+'/'+stage
            rows.append({'id':rid,'task_id':t['id'],'source_group':t['source_group'],'source_sha256':t['rtl_sha256'],
                'split':t['split'],'stage':stage,'operation':'mux','rtl_operation':'mux','spec':s,
                'features':features(s['lhs_width'],s['rhs_width'],s['result_width'],s['fanout'],1500,t['period_ps']),
                'delay_ps':label['data_delay_ps'],'comb_area_um2':area,'period_ps':t['period_ps'],
                'observed_H_ps':t['period_ps']-label['data_delay_ps']-label['slack_ps'],'path_slack_ps':label['slack_ps'],
                'whole_setup_slack_ps':stored['setup_worst_slack_ps'],'whole_hold_slack_ps':stored['hold_worst_slack_ps'],
                'manifest_sha256':sha(directory/'manifest.json'),'bank_counts':banks.get(s['id']),'source_context':'new_parallel_mux'})
            diagnostics.append({'row_id':rid,'all_input_start_pin':label['start_pin'],
                'arcs':{arc:by_id[s['id']+'_'+arc] for arc in ('select','data_a','data_b')},'diagnostic_only':True})
    proof=directory/'logs'/SUFFIX/'structural_cec/proof.json'
    verify_proof(proof,directory/'results'/SUFFIX/'4_before_rsz_lec.v',directory/'results'/SUFFIX/'4_after_rsz_lec.v')
    request=read(read(proof)['request_path'])
    if request['collection_plan_sha256']!=sha(admission_path):raise ValueError('Mux CEC proof request not bound')
    return rows,diagnostics,m


def extract(folder,out):
    from .model_m2_collection import extract_rows,verify_plan,run_directory
    a=verify_collection(folder);p=read(folder/'progress.json');f=verify_parent(Path(a['parent_selection']))
    if p['phase']!='fitting_collection_complete' or p['errors'] or p['waiting'] or len(p['completed'])!=120:raise ValueError('complete120 fitting tasks required')
    legacy=read(f['dataset_path']);parent_plan=verify_plan(Path(a['parent_plan']))
    ids={t['id'] for t in parent_plan['tasks'] if t['split'] in ('train','validation') and t['family']=='control'}
    replay=extract_rows(Path(a['parent_plan']).parent,ids)
    rows=[r for r in replay['rows'] if r['operation']=='mux'];original={r['id']:r for r in legacy['rows'] if r['operation']=='mux'}
    if len(rows)!=144 or {r['id'] for r in rows}!=set(original) or any(r!=original[r['id']] for r in rows):raise ValueError('legacy Mux raw replay differs from frozen eligible dataset')
    for r in rows:r.update(source_group=r['task_id'].rsplit('-t',1)[0],source_context='legacy_mixed_control')
    entries={e['id']:e for e in read(Ledger().path)['entries']};runs=[];diagnostics=[];static=set()
    reference=next(t for t in parent_plan['tasks'] if t['id'] in ids)
    expected_identity=measurement_identity(read(run_directory(Path(a['parent_plan']).parent,reference)/'manifest.json'))
    tasks=[t for t in a['tasks'] if t['split'] in ('train','validation')]
    for t in tasks:
        d=folder/'runs'/t['id'];extra,observed,m=verify_run(d,t,a,folder/'admission.json',entries)
        rows.extend(extra);diagnostics.extend(observed);static.add(measurement_identity(m))
        runs.append({'task_id':t['id'],'directory':str(d),'manifest_sha256':sha(d/'manifest.json'),
            'peak_RSS_MiB':max(c['sampled_process_tree_peak_rss_KiB'] for c in m['commands'])/1024})
    if len(rows)!=768 or len(diagnostics)!=624 or static!={expected_identity}:raise ValueError('Mux fitting sample or physical identity coverage incomplete')
    exclusive(out,{'version':'asap7-m2-mux-fitting-data-v1','mode':'fitting','admission_path':str((folder/'admission.json').resolve()),
        'admission_sha256':sha(folder/'admission.json'),'protocol_sha256':sha(CONFIG),'parent_selection_path':a['parent_selection'],
        'parent_selection_sha256':a['parent_selection_sha256'],'legacy_fitting_data_sha256':f['dataset_sha256'],
        'inherited11_path':str((folder/'inherited11.json').resolve()),'inherited11_sha256':a['inherited11_sha256'],
        'measurement_static_identity_sha256':next(iter(static)),'rows':sorted(rows,key=lambda r:r['id']),'diagnostics':diagnostics,
        'runs':runs,'legacy_runs':replay['runs'],'failures':[],'old_independent_mux_labels_read':False,'new_independent_labels_read':False})
    print(json.dumps({'status':'extracted','new_tasks':120,'eligible_legacy_mux_tasks':72,'fitting_rows':len(rows),
        'by_split':dict(Counter(r['split'] for r in rows)),'arc_observation_parents':len(diagnostics),'test_locked':True}),flush=True)


def validate_data(path):
    d=read(path)
    if (d.get('version')!='asap7-m2-mux-fitting-data-v1' or d.get('mode')!='fitting' or d['failures']
        or d['old_independent_mux_labels_read'] or d['new_independent_labels_read'] or any(r['split'] not in ('train','validation') or r['operation']!='mux' for r in d['rows'])):
        raise ValueError('Mux fit requires only eligible train/validation')
    a=verify_collection(Path(d['admission_path']).parent);verify_parent(Path(d['parent_selection_path']))
    if sha(d['admission_path'])!=d['admission_sha256'] or sha(CONFIG)!=d['protocol_sha256'] or sha(d['inherited11_path'])!=d['inherited11_sha256']:
        raise ValueError('changed Mux fitting identity')
    if len(d['rows'])!=768 or len({r['id'] for r in d['rows']})!=768 or len(d['runs'])!=120:raise ValueError('Mux fitting coverage incomplete')
    groups={}
    for r in d['rows']:
        h=r['source_sha256']
        if h in groups and groups[h]!=r['split']:raise ValueError('complete source crosses fitting partitions')
        groups[h]=r['split']
        s=r['spec']
        if r['features']!=features(s['lhs_width'],s['rhs_width'],s['result_width'],s['fanout'],1500,r['period_ps']):raise ValueError('nonstatic Mux features')
    return d,a


def choose_component(rows,field):
    import numpy as np
    if any(r['split'] not in ('train','validation') for r in rows):raise ValueError('independent row supplied to Mux fitting')
    train=[r for r in rows if r['split']=='train'];val=[r for r in rows if r['split']=='validation'];delay=field=='delay_ps';floor=1.5 if delay else 1e-4
    if not train or not val:raise ValueError('both fitting partitions required')
    raw=dict(algorithms(train,field,floor));folds={}
    if delay:
        for held in sorted({r['source_sha256'] for r in train}):
            fitting=[r for r in train if r['source_sha256']!=held]
            if not fitting:raise ValueError('complete source crossfit has no fitting data')
            folds[held]=dict(algorithms(fitting,field,floor))
    models={};candidates=[]
    for name,predictor in raw.items():
        options=[('none',1.,0.)]
        if delay:
            margin=float(np.quantile([max(0,r[field]-infer(predictor,r['features'])) for r in val],.95))+1.5
            vr=max([1.]+[r[field]/max(1.5,infer(predictor,r['features'])) for r in val])
            cr=max([1.]+[r[field]/max(1.5,infer(folds[r['source_sha256']][name],r['features'])) for r in train])
            options=[('validation_positive_p95',1.,margin),('complete_source_ratio',max(vr,cr)*1.05,1.5)]
        for reserve,scale,margin in options:
            key=name+'/'+reserve;model={'kind':'pooled','predictor':predictor,'delay_scale':scale,'delay_margin_ps':margin,'algorithm':name,'calibration':reserve}
            q=quality(val,model,'delay' if delay else 'area');models[key]=model
            candidates.append({'algorithm':name,'calibration':reserve,'key':key,'quality':q,'delay_scale':scale,'delay_margin_ps':margin})
    best=min(candidates,key=lambda c:(c['quality']['status']!='passed',c['quality']['MAE'],c['quality']['p95_relative_error'],len(json.dumps(models[c['key']])),c['key']))
    return models[best['key']],{'selected':best['key'],'quality':best['quality'],'candidates':candidates,'training_sources':len({r['source_sha256'] for r in train}),
        'validation_sources':len({r['source_sha256'] for r in val}),'train_rows':len(train),'validation_rows':len(val)}


def choose(rows,field,baseline):
    quantity='delay' if field=='delay_ps' else 'area';val=[r for r in rows if r['split']=='validation']
    pooled,pr=choose_component(rows,field);by_width={'kind':'exact_width_slices','slices':{}};wr={}
    for key in sorted({width_key(r) for r in rows}):
        m,detail=choose_component([r for r in rows if width_key(r)==key],field);by_width['slices'][key]=m;wr[key]=detail
    joint={'kind':'exact_width_target_slices','slices':{}};jr={}
    for key in sorted({target_key(r) for r in rows}):
        m,detail=choose_component([r for r in rows if target_key(r)==key],field);joint['slices'][key]=m;jr[key]=detail
    choices=[('frozen_v4',copy.deepcopy(baseline)),('pooled',pooled),('exact_width',by_width),('exact_width_target',joint)]
    candidates=[(name,m,quality(val,m,quantity)) for name,m in choices]
    selected=min(candidates,key=lambda c:(c[2]['status']!='passed',c[2]['MAE'],c[2]['p95_relative_error'],len(json.dumps(c[1])),c[0]))
    return selected[1],{'selected':selected[0],'quality':selected[2],'partitions':{name:q for name,_,q in candidates},'pooled':pr,'widths':wr,'width_targets':jr}


def fit(data_path,out):
    d,a=validate_data(data_path);out.mkdir(parents=True,exist_ok=False)
    baseline=read(Path(d['parent_selection_path']).parent/'candidate.json');inherited=read(d['inherited11_path'])
    if 'mux' in inherited['operations'] or len(inherited['operations'])!=11 or any(v['independent_quality']['status']!='passed' for v in inherited['operations'].values()):
        raise ValueError('unchanged11 qualification invalid')
    candidate={'version':'asap7-m2-mux-composite-candidate-v1','quality_status':'awaiting_independent_test','target_platform':'asap7',
        'ABC_ps':1500,'IO':'0.2T','stages':{},'inherited11_sha256':d['inherited11_sha256'],'full_D_ready':False}
    report={'version':'asap7-m2-mux-fit-report-v1','stages':{},'independent_mux_labels_read':False,
        'environment':{'python':sys.version,'numpy':version('numpy'),'scikit-learn':version('scikit-learn'),'seed':20261102,
            'threads':{k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')}}}
    for stage in ('synth','grt'):
        rows=[r for r in d['rows'] if r['stage']==stage];old=baseline['stages'][stage]['operations']['mux']
        delay,dr=choose(rows,'delay_ps',old['delay']);area,ar=choose(rows,'comb_area_um2',old['area']);ready=dr['quality']['status']==ar['quality']['status']=='passed'
        mux={'delay':delay,'area':area,'joint_domain':copy.deepcopy(old['joint_domain']),'validation_ready':ready,'quality_status':'awaiting_independent_test' if ready else 'failed_validation'}
        ops={'mux':mux}
        if stage=='grt':ops.update({op:copy.deepcopy(v['model']) for op,v in inherited['operations'].items()})
        candidate['stages'][stage]={'operations':ops,'validation_ready':ready}
        report['stages'][stage]={'mux':{'delay':dr,'area':ar},'mux_validation_ready':ready,
            'unchanged_qualified_operations':11 if stage=='grt' else 0,'counts':dict(Counter(r['split'] for r in rows))}
    write(out/'candidate.json',candidate);write(out/'fit-report.json',report)
    sources={}
    for path in (Path(__file__),CONFIG,Path(__file__).with_name('model_training.py'),Path(__file__).with_name('model_features.py'),
                 Path(__file__).with_name('model_m2_fit_v4.py'),Path(__file__).with_name('model_m2_fit_v3.py'),Path(__file__).with_name('model_m2_fit.py')):
        name=str(path.relative_to(ROOT));dst=out/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst);sources[name]=sha(path)
    f={'version':'asap7-m2-mux-fit-freeze-v1','dataset_path':str(data_path.resolve()),'dataset_sha256':sha(data_path),'protocol_sha256':sha(CONFIG),
        'admission_path':d['admission_path'],'admission_sha256':d['admission_sha256'],'parent_selection_path':d['parent_selection_path'],
        'parent_selection_sha256':d['parent_selection_sha256'],'inherited11_path':d['inherited11_path'],'inherited11_sha256':d['inherited11_sha256'],
        'candidate_sha256':sha(out/'candidate.json'),'fit_report_sha256':sha(out/'fit-report.json'),'sources':sources,
        'grt_validation_ready':candidate['stages']['grt']['validation_ready'],'test_consumed':False}
    write(out/'fit-freeze.json',f)
    if f['grt_validation_ready']:write(out/'selection-freeze.json',{**f,'version':'asap7-m2-mux-selection-v1'})
    print(json.dumps({'stages':{s:{'mux_validation_ready':v['mux_validation_ready'],'delay':v['mux']['delay']['quality'],'area':v['mux']['area']['quality']} for s,v in report['stages'].items()},
        'new_independent_test_eligible':f['grt_validation_ready'],'unchanged_qualified_operations':11}),flush=True)


def verify_fit(path):
    f=read(path);folder=Path(path).parent
    if f['version'] not in ('asap7-m2-mux-fit-freeze-v1','asap7-m2-mux-selection-v1') or f['test_consumed'] is not False:raise ValueError('wrong Mux fit freeze')
    if (sha(f['dataset_path'])!=f['dataset_sha256'] or sha(CONFIG)!=f['protocol_sha256'] or sha(f['parent_selection_path'])!=f['parent_selection_sha256']
        or sha(f['inherited11_path'])!=f['inherited11_sha256']):raise ValueError('changed Mux frozen inputs')
    for name,h in f['sources'].items():
        if sha(ROOT/name)!=h or sha(folder/'source'/name)!=h:raise ValueError('changed Mux fitter source')
    for name,key in (('candidate.json','candidate_sha256'),('fit-report.json','fit_report_sha256')):
        if sha(folder/name)!=f[key]:raise ValueError('changed frozen Mux predictor/report')
    d,a=validate_data(Path(f['dataset_path']));c=read(folder/'candidate.json');r=read(folder/'fit-report.json');inherited=read(f['inherited11_path'])
    for op,value in inherited['operations'].items():
        if c['stages']['grt']['operations'][op]!=value['model']:raise ValueError('changed inherited operation numbers/domain')
    for stage,value in c['stages'].items():
        model=value['operations']['mux'];rows=[v for v in d['rows'] if v['stage']==stage and v['split']=='validation']
        for q in ('delay','area'):
            if quality(rows,model[q],q)!=r['stages'][stage]['mux'][q]['quality']:raise ValueError('Mux validation does not recompute')
        ready=r['stages'][stage]['mux']['delay']['quality']['status']==r['stages'][stage]['mux']['area']['quality']['status']=='passed'
        if model['validation_ready']!=ready or value['validation_ready']!=ready:raise ValueError('wrong Mux validation status')
    if f['grt_validation_ready']!=c['stages']['grt']['validation_ready'] or Path(path).name=='selection-freeze.json' and not f['grt_validation_ready']:
        raise ValueError('unready Mux selection')
    return f


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['extract','fit','verify','reproduce'])
    for name in ('folder','out','data','selection'):ap.add_argument('--'+name,type=Path)
    a=ap.parse_args()
    if a.action=='extract':extract(a.folder.resolve(),a.out.resolve())
    elif a.action=='fit':fit(a.data.resolve(),a.out.resolve())
    elif a.action=='verify':print(json.dumps({'status':'verified','ready':verify_fit(a.selection)['grt_validation_ready']}))
    else:
        f=verify_fit(a.selection);fit(Path(f['dataset_path']),a.out.resolve())
        for name,key in (('candidate.json','candidate_sha256'),('fit-report.json','fit_report_sha256')):
            if sha(a.out/name)!=f[key]:raise ValueError('Mux refit differs')
        write(a.out/'reproduction.json',{'status':'passed','parent_fit_sha256':sha(a.selection),'independent_labels_read':False})


if __name__=='__main__':main()
