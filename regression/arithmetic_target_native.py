"""Independent graph-feature/portable-predictor parity for target-aware native queries."""
import argparse
import copy
import json
import math
from pathlib import Path
import subprocess

from experiments.arithmetic_dse.model_collection import sha,write
from experiments.arithmetic_dse.model_mul_intervals import interval,key
from experiments.arithmetic_dse.model_target_features import features,infer

ROOT=Path(__file__).resolve().parents[1]


def attach(base,local,out,*,test_only=False):
    if out.exists():raise ValueError('preserve existing model artifact')
    b=json.loads(base.read_text());m=json.loads(local.read_text())
    if b['quality_status']!='passed' or m['quality_status']!='passed' or b['platform_profile_sha256']!=m['platform_profile_sha256']:
        raise ValueError('qualified matching local and ordinary models required')
    if b['mapping_abc_target_ps']!=m['abc_target_ps'] or b['target_platform']!=m['target_platform']:
        raise ValueError('mapping/platform identity mismatch')
    for name,scope in b['stages']['grt']['operations'].items():
        if not any(c['abc_target_ps']==1500 and c['sdc_min_ps']<=1500 and c['sdc_max_ps']>=2250 for c in scope['domain']['conditions']):
            raise ValueError('ordinary operation lacks joint target range: '+name)
    model={'version':m['version'],'quality_status':'passed','min_width':8,'max_width':32,
           'abc_target_ps':m['abc_target_ps'],'io_policy':m['io_policy'],'reference':m['reference'],
           'max_operations':m['max_operations'],'max_result_bits':m['max_result_bits'],
           'intervals':m['stages']['grt']['intervals']}
    b['stages']['grt']['mul_interval_model']=model
    b['id']=('TEST_ONLY_TARGET_FEATURES_' if test_only else 'asap7-target-load-local-integration_')+sha(local)[:12]
    b['joint_model_context']={'abc_target_ps':1500,'sdc_min_ps':1500,'sdc_max_ps':2250,
                              'basis':'intersection with existing independently qualified ordinary/state/boundary R..1.5R context',
                              'base_sha256':sha(base),'interval_sha256':sha(local)}
    b['full_step7_complete']=False
    b['release_scope']='local interval integration at existing base target contexts only; no all-domain D claim'
    if test_only:b['data_role']='TEST_ONLY artificial nonconstant target features, not fitted prices'
    write(out,b)


def fixture(base,reference,out):
    b=json.loads(base.read_text());ref=json.loads(reference.read_text());out.mkdir(parents=True,exist_ok=False)
    entries={}
    for name in ref['intervals']:
        entries[name]={'quality_status':'passed','validation_ready':True,'validation_delay_scale':1.05,
                       'delay':{'kind':'linear','features':['width','capture_bits','input_bits','pressure','tightness','width_tightness','reference_delay_ps'],
                                'intercept':5.,'coefficients':[.1,.01,.02,.005,.3,.001,.001]},
                       'area':{'kind':'tree','features':['tightness','width','capture_fanout'],
                               'nodes':[{'feature':0,'threshold':.3,'left':1,'right':2},{'value':3.5},{'value':7.25}]},
                       'domain':{'reference_pressure_min':.01,'period_max_ps':2250,'production_capture_fanout':1}}
    local={'version':'arithmetic-mul-group-interval-target-load-v1','quality_status':'passed',
           'target_platform':'asap7','platform_profile_sha256':b['platform_profile_sha256'],'abc_target_ps':1500,
           'io_policy':'proportional_0.2T','reference':ref,'max_operations':64,'max_result_bits':4096,
           'stages':{'grt':{'intervals':entries}},'data_role':'TEST_ONLY'}
    write(out/'local.json',local);attach(base,out/'local.json',out/'asap7.json',test_only=True)


def verify(model,graphs,report,out):
    b=json.loads(model.read_text());m=b['stages']['grt']['mul_interval_model'];data=json.loads(report.read_text())
    if data['candidate_PPA_calls']!=0:raise ValueError('native inference invoked PPA')
    graphs_by_name={p.name:json.loads(p.read_text()) for p in graphs.glob('*.json')}
    expected=set()
    for name,g in graphs_by_name.items():
        region=g['graph']['regions'][0];width=region['parameters']['lhs_width']
        if not 8<=width<=32:continue
        for first in range(len(region['legal_groups'])):
            for last in range(first,len(region['legal_groups'])):
                for period in (1500.,1875.,2250.,1.,2251.):expected.add((name,first,last,period))
    actual={(r['graph'],r['first'],r['last'],r['period_ps']) for r in data['rows']}
    if actual!=expected or len(actual)!=len(data['rows']):raise ValueError('incomplete or duplicate native graph/interval/target coverage')
    covered=refused=0
    for row in data['rows']:
        graph=graphs_by_name[row['graph']];parameters=graph['graph']['regions'][0]['parameters']
        period=row['period_ps'];joint=b['joint_model_context'];width=parameters['lhs_width']
        okay=joint['sdc_min_ps']<=period<=joint['sdc_max_ps'] and 8<=width<=32 and width%4==0
        f=None
        if okay:
            spec=interval(graph,row['first'],row['last']);spec['fanout']=1;entry=m['intervals'][key(spec)]
            f=features(spec,period,m['reference'])
            okay=f['pressure']>=entry['domain']['reference_pressure_min'] and period<=entry['domain']['period_max_ps']
        if row['covered']!=okay:raise ValueError('native target/width domain mismatch: '+str(row))
        if okay:
            delay=infer(entry['delay'],f)*entry['validation_delay_scale'];area=infer(entry['area'],f)
            if not math.isclose(delay,row['delay_ps'],rel_tol=1e-9,abs_tol=1e-7) or not math.isclose(area,row['comb_area_um2'],rel_tol=1e-9,abs_tol=1e-7):
                raise ValueError('native and independent Python feature/prediction mismatch')
            covered+=1
        else:refused+=1
    result={'model_sha256':sha(model),'queries':len(data['rows']),'covered':covered,'refused':refused,
            'query_report_sha256':sha(report),'graphs_directory':str(graphs.resolve()),
            'graph_sha256':{name:sha(graphs/name) for name in sorted({r['graph'] for r in data['rows']})},
            'candidate_PPA_calls':0,'numeric_model_claim':not b.get('id','').startswith('TEST_ONLY'),
            'scope':'all native registered interval graph queries; not full pipeline/state quality qualification'}
    write(out,result);print(json.dumps(result))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['fixture','attach','verify'])
    for name in ('base','reference','out','local','model','graphs','report'):p.add_argument('--'+name,type=Path)
    a=p.parse_args()
    if a.action=='fixture':fixture(a.base,a.reference,a.out)
    elif a.action=='attach':attach(a.base,a.local,a.out)
    else:verify(a.model,a.graphs,a.report,a.out)
