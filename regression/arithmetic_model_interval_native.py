"""Nonconstant interval predictors through the native public three-candidate path.

These deliberately artificial prices test the inference ABI only. The output
retains TEST_ONLY identity and is never accepted as trained-model evidence.
"""
import argparse
import json
import subprocess
from pathlib import Path
from experiments.arithmetic_dse.model_collection import write
from experiments.arithmetic_dse.model_mul_intervals import interval, key
from experiments.arithmetic_dse.model_analysis import verify_report, verify_selection

ROOT=Path(__file__).resolve().parents[1]


def run(base, graphs, out, executable):
    models=out/'models';models.mkdir(parents=True,exist_ok=False)
    entries={}
    for path in sorted(graphs.glob('w8_*.json')):
        graph=json.loads(path.read_text());groups=graph['graph']['regions'][0]['legal_groups']
        for first in range(len(groups)):
            for last in range(first,len(groups)):
                spec=interval(graph,first,last)
                entries[key(spec)]={'quality_status':'passed','validation_delay_scale':1.05,
                    'delay':{'kind':'linear','features':['width','capture_bits','input_bits'],
                             'intercept':float(5*(last-first+1)),'coefficients':[1.,.05,.01]},
                    'area':{'kind':'tree','features':['capture_bits','width'],
                            'nodes':[{'feature':0,'threshold':16.,'left':1,'right':2},
                                     {'value':1.5}, {'feature':1,'threshold':12.,'left':3,'right':4},
                                     {'value':3.25},{'value':8.5}]}}
    if not entries:raise ValueError('missing native interval graphs')
    platforms=('asap7','nangate45','sky130hd','gf180')
    for platform in platforms:
        bundle=json.loads((base/(platform+'.json')).read_text())
        bundle['id']='TEST_ONLY_NONCONSTANT_INTERVAL_'+platform
        bundle['data_role']='artificial nonconstant linear/tree inference check, not a fitted model'
        bundle['stages']['grt']['mul_interval_model']={'version':'arithmetic-mul-group-interval-model-v1',
            'quality_status':'passed','min_width':8,'max_width':32,'sdc_period_ps':bundle['mapping_abc_target_ps'],
            'abc_target_ps':bundle['mapping_abc_target_ps'],'max_operations':64,'max_result_bits':4096,'intervals':entries}
        write(models/(platform+'.json'),bundle)
    native=out/'native'
    subprocess.run([str(executable.resolve()),str(ROOT),str(models.resolve()),str(native.resolve())],cwd=ROOT,check=True)
    checked=[]
    for platform in platforms:
        bundle=json.loads((models/(platform+'.json')).read_text());report=json.loads((native/(platform+'.report.json')).read_text())
        verify_report(report,bundle,(native/(platform+'.sv')).read_text());verify_selection(report,bundle)
        checked.append({'platform':platform,'candidate_count':report['selection']['evaluated_structures'],
                        'candidate_PPA_calls':report['selection']['candidate_PPA_calls'],
                        'selected':report['selection']['selected_candidate']})
    result={'role':'TEST_ONLY nonconstant interval inference parity','platforms':checked,'fitted_quality_claim':False}
    write(out/'result.json',result);print(json.dumps(result))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('base','graphs','out','executable'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();run(args.base,args.graphs,args.out,args.executable)
