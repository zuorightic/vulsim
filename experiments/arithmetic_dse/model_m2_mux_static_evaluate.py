"""Once-only P4 Mux qualification and explicit unchanged11 composition."""
import argparse
import copy
import fcntl
from itertools import combinations
import json
from pathlib import Path
import shutil

from .budget import Ledger
from .model_collection import sha,write
from .model_m2_mux_fit import verify_run
from .model_m2_mux_static_fit import verify_fit,digest,validate as validate_fit,quality
from .model_m2_mux_static_features import descriptor,features,predict,VERSION
from .model_m2_mux_static_tests import verify as verify_admission
from .model_m2_evaluate import measurement_identity
from .model_training import metric

ROOT=Path(__file__).resolve().parents[2]
SUFFIX=Path('asap7/arithmetic_probe/base')


def read(path):return json.loads(Path(path).read_text())


def exclusive(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')


def extract(folder,out):
    a=verify_admission(folder);f=verify_fit(Path(a['selection_path']));fit,_=validate_fit(Path(f['dataset_path']));p=read(folder/'progress.json')
    tasks={t['id']:t for t in a['tasks']}
    if p['phase']!='test_collection_complete' or len(p['completed'])!=48 or set(p['completed'])!=set(tasks) or p['waiting'] or p['errors']:
        raise ValueError('all48 independent Mux tasks must complete')
    entries={e['id']:e for e in read(Ledger().path)['entries']};rows=[];diagnostics=[];runs=[];contexts={}
    for t in a['tasks']:
        d=folder/'runs'/t['id'];m=read(d/'manifest.json')
        if t['split']!='test' or not m.get('mux_static_independent') or m['selection_freeze_sha256']!=a['selection_sha256']:
            raise ValueError('Mux test not bound to chosen static model')
        if any(entries[c['budget_reservation_id']].get('selection_freeze_sha256')!=a['selection_sha256'] for c in m['commands']):
            raise ValueError('Mux test selection not bound to paid commands')
        if measurement_identity(m)!=fit['measurement_static_identity_sha256']:raise ValueError('independent Mux physical identity differs from fitting')
        values,observed,m=verify_run(d,t,a,folder/'admission.json',entries);cut=descriptor(read(t['sample_contract'])['labels']);h=digest(cut);contexts[h]=cut
        for row in values:
            row.update(static_context_sha256=h,static_features=features(row['features'],cut,row['spec']['id']))
            rows.append(row)
        diagnostics.extend(observed);runs.append({'task_id':t['id'],'directory':str(d),'manifest_sha256':sha(d/'manifest.json'),
            'peak_RSS_MiB':max(c['sampled_process_tree_peak_rss_KiB'] for c in m['commands'])/1024,
            'proof_sha256':sha(d/'logs'/SUFFIX/'structural_cec/proof.json')})
    if len(rows)!=384 or {r['source_sha256'] for r in rows}&{r['source_sha256'] for r in fit['rows']}:
        raise ValueError('Mux independent label/source coverage mismatch')
    data={'version':'asap7-m2-mux-static-independent-data-v1','mode':'test','admission_path':str((folder/'admission.json').resolve()),
        'admission_sha256':sha(folder/'admission.json'),'selection_path':a['selection_path'],'selection_sha256':a['selection_sha256'],
        'candidate_sha256':a['candidate_sha256'],'feature_schema':VERSION,'rows':sorted(rows,key=lambda r:r['id']),
        'diagnostics':diagnostics,'runs':runs,'static_contexts':contexts,'failures':[],'old_independent_mux_labels_read':False,
        'prospective_release_scope':a['prospective_release_scope'],'measurement_static_identity_sha256':fit['measurement_static_identity_sha256']}
    validate_data(data,a);exclusive(out,data);print(json.dumps({'status':'extracted','independent_tasks':48,'rows':384,'diagnostic_parents':len(diagnostics)}),flush=True)


def validate_data(d,a):
    if d.get('version')!='asap7-m2-mux-static-independent-data-v1' or d['mode']!='test' or d['failures'] or d['old_independent_mux_labels_read']:
        raise ValueError('wrong static Mux independent data role')
    tasks={t['id']:t for t in a['tasks']};specs={t['id']:{s['id']:s for s in read(t['sample_contract'])['labels']} for t in a['tasks']}
    expected={tid+'/'+sid+'/'+stage for tid,values in specs.items() for sid in values for stage in ('synth','grt')}
    if (len(tasks)!=48 or len(d['runs'])!=48 or len(d['rows'])!=384 or len({r['id'] for r in d['rows']})!=384
        or {r['id'] for r in d['rows']}!=expected or {r['task_id'] for r in d['runs']}!=set(tasks)):raise ValueError('incomplete fixed P4 cohort')
    for r in d['rows']:
        t=tasks[r['task_id']];s=specs[t['id']][r['spec']['id']];cut=d['static_contexts'][r['static_context_sha256']]
        if (r['split']!='test' or r['operation']!='mux' or r['period_ps']!=t['period_ps'] or r['source_sha256']!=t['rtl_sha256']
            or r['spec']!=s or r['static_context_sha256']!=digest(cut) or r['static_features']!=features(r['features'],cut,s['id'])):
            raise ValueError('independent Mux feature/source/target changed')
    if d['prospective_release_scope']!=a['prospective_release_scope']:raise ValueError('posterior independent scope change')


def report(rows,candidate):
    result={}
    for stage,value in candidate['stages'].items():
        model=value['operations']['mux'];subset=[r for r in rows if r['stage']==stage]
        if not subset:raise ValueError('missing independent Mux stage')
        delay=quality(subset,model['delay'],'delay');area=quality(subset,model['area'],'area');pred=[]
        for r in subset:pred.append({'id':r['id'],'delay_ps':predict(model['delay'],r,'delay'),'comb_area_um2':predict(model['area'],r,'area')})
        groups={};indexed={v['id']:v for v in pred};ranking=[]
        for r in subset:groups.setdefault((r['source_sha256'],r['spec']['id']),[]).append(r)
        for key,values in sorted(groups.items()):
            for x,y in combinations(sorted(values,key=lambda r:r['period_ps']),2):
                for field in ('delay_ps','comb_area_um2'):
                    observed=(x[field]>y[field])-(x[field]<y[field]);px=indexed[x['id']][field];py=indexed[y['id']][field];predicted=(px>py)-(px<py)
                    ranking.append({'row_a':x['id'],'row_b':y['id'],'field':field,'observed_order':observed,'predicted_order':predicted,'matches':observed==predicted})
        result[stage]={'status':'passed' if delay['status']==area['status']=='passed' else 'failed','delay':delay,'area':area,'predictions':pred,
            'coverage':{'tasks':len({r['task_id'] for r in subset}),'rows':len(subset),'widths':sorted({r['spec']['lhs_width'] for r in subset}),
                'capture_banks':sorted({r['spec']['fanout'] for r in subset}),'static_families':['parallel_dynamic_mux'],
                'independence':'new complete P4 source/packing contexts at exposed widths/loads; rows within a source are correlated'},
            'actual_target_conservative_rejections':sum(r['delay_ps']<=r['period_ps']-r['observed_H_ps']<p['delay_ps'] for r,p in zip(subset,pred)),
            'ranking':{'scope':'same source/Mux/width/load at different exact targets only; not full-candidate ranking',
                'matching_pairs':sum(x['matches'] for x in ranking),'denominator':len(ranking),'records':ranking}}
    return result


def evaluate(data_path,selection,out):
    f=verify_fit(selection);d=read(data_path);a=verify_admission(Path(d['admission_path']).parent);validate_data(d,a)
    if sha(selection)!=d['selection_sha256'] or f['candidate_sha256']!=d['candidate_sha256'] or sha(d['admission_path'])!=d['admission_sha256']:
        raise ValueError('independent Mux not bound to frozen inputs')
    candidate=read(selection.parent/'candidate.json');inherit=read(f['inherited11_path'])
    if len(inherit['operations'])!=11 or 'mux' in inherit['operations']:raise ValueError('invalid unchanged11 composition')
    for op,value in inherit['operations'].items():
        if value['independent_quality']['status']!='passed' or candidate['stages']['grt']['operations'][op]!=value['model']:
            raise ValueError('independently qualified component changed')
    with (selection.parent/'mux-static-independent-evaluation.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if out.exists():raise ValueError('preserve previous independent Mux result')
        exclusive(selection.parent/'mux-static-independent-evaluation.json',{'dataset_sha256':sha(data_path),'selection_sha256':sha(selection),'result_path':str((out/'result.json').resolve())})
        out.mkdir(parents=True);stages=report(d['rows'],candidate);combined=stages['grt']['status']=='passed'
        paths=[Path(__file__)]+[ROOT/name for name in f['sources']];sources={}
        for path in paths:
            name=str(path.relative_to(ROOT));dst=out/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst);sources[name]=sha(path)
        r={'version':'asap7-m2-mux-static-independent-result-v1','dataset_path':str(data_path.resolve()),'dataset_sha256':sha(data_path),
            'selection_path':str(selection.resolve()),'selection_sha256':sha(selection),'candidate_sha256':f['candidate_sha256'],
            'stages':stages,'quality_status':'passed' if combined else 'failed','unchanged_qualified_operations':11,
            'combined_passing_operations':12 if combined else 11,'combined_required_operations':12,'inherited11_sha256':f['inherited11_sha256'],
            'prospective_release_scope':d['prospective_release_scope'],'sources':sources,'full_D_ready':False,'old_F5_overall_result_changed':False}
        write(out/'result.json',r);print(json.dumps({'quality_status':r['quality_status'],'combined_passing_operations':r['combined_passing_operations'],
            'stages':{s:{k:v for k,v in r.items() if k not in ('predictions','ranking')} for s,r in stages.items()}}),flush=True)


def verify_result(path):
    r=read(path);f=verify_fit(Path(r['selection_path']))
    if sha(r['selection_path'])!=r['selection_sha256'] or sha(r['dataset_path'])!=r['dataset_sha256'] or f['candidate_sha256']!=r['candidate_sha256']:
        raise ValueError('changed static independent inputs')
    for name,h in r['sources'].items():
        if sha(ROOT/name)!=h or sha(path.parent/'source'/name)!=h:raise ValueError('changed independent evaluator source')
    d=read(r['dataset_path']);a=verify_admission(Path(d['admission_path']).parent);validate_data(d,a);c=read(Path(r['selection_path']).parent/'candidate.json')
    actual=report(d['rows'],c)
    if actual!=r['stages'] or r['quality_status']!=actual['grt']['status'] or r['combined_passing_operations']!=(12 if actual['grt']['status']=='passed' else 11):
        raise ValueError('static independent result does not recompute')
    receipt=read(Path(r['selection_path']).parent/'mux-static-independent-evaluation.json')
    if receipt!={'dataset_sha256':r['dataset_sha256'],'selection_sha256':r['selection_sha256'],'result_path':str(path.resolve())}:raise ValueError('wrong independent evaluation owner')
    return r


def publish(result_path,out):
    r=verify_result(result_path);out.mkdir(parents=True,exist_ok=False);published=[]
    if r['quality_status']=='passed':
        f=verify_fit(Path(r['selection_path']));d=read(r['dataset_path']);fit=read(f['dataset_path']);c=read(Path(r['selection_path']).parent/'candidate.json')
        c.update(version='asap7-m2-primitives-static-composite-qualified-v1',quality_status='passed',full_D_ready=False,
            independent_result_sha256=sha(result_path),platform_profile_sha256=read(d['admission_path'])['tasks'][0]['profile_sha256'],
            measurement_static_identity_sha256=d['measurement_static_identity_sha256'],native_full_D_selection_ready=False)
        c['stages']={'grt':c['stages']['grt']}
        for m in c['stages']['grt']['operations'].values():m['quality_status']='passed'
        mux=c['stages']['grt']['operations']['mux'];mux['context_domain']['independently_qualified_families']=['parallel_dynamic_mux']
        mux['context_domain']['legacy_mixed_control_status']='fitting_validation_only_not_independently_qualified_by_P4'
        c['qualification_components']={'unchanged11':{'manifest_sha256':r['inherited11_sha256'],'same_numbers_margins_and_domains':True},
            'new_mux':{'result_sha256':sha(result_path),'feature_schema':VERSION,'qualified_family':'parallel_dynamic_mux'}}
        write(out/'asap7-primitives.json',c);published=[{'file':'asap7-primitives.json','sha256':sha(out/'asap7-primitives.json')}]
    write(out/'publication.json',{'version':'asap7-m2-mux-static-composite-publication-v1','result_sha256':sha(result_path),'quality_status':r['quality_status'],
        'published':published,'combined_passing_operations':r['combined_passing_operations'],'required_operations':12,'full_D_ready':False,
        'scope':r['prospective_release_scope'],'old_F5_overall_result_changed':False,
        'remaining':['production stage-boundary adapter and state/composition qualification','mixed/arithmetic Mux contexts','real half/quarter interval successor','formal targets and nine-case D closure']})
    print(json.dumps({'quality_status':r['quality_status'],'combined_passing_operations':r['combined_passing_operations'],'published':published}),flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['extract','evaluate','verify','publish'])
    for name in ('folder','out','data','selection','result'):ap.add_argument('--'+name,type=Path)
    a=ap.parse_args()
    if a.action=='extract':extract(a.folder.resolve(),a.out.resolve())
    elif a.action=='evaluate':evaluate(a.data.resolve(),a.selection.resolve(),a.out.resolve())
    elif a.action=='publish':publish(a.result.resolve(),a.out.resolve())
    else:print(json.dumps({'status':'verified','quality_status':verify_result(a.result.resolve())['quality_status']}))


if __name__=='__main__':main()
