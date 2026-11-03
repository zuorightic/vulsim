import json
from pathlib import Path
from experiments.arithmetic_dse.model_collection import write
out=Path('build/step7-intervals-20261103')
r=json.loads((out/'asap7-independent-test-v1/independent-test.json').read_text())['platforms']['asap7']
fit=json.loads((out/'asap7-fit-v1/asap7.fit.json').read_text())
data=json.loads((out/'asap7-test-data-v1.json').read_text());by_id={row['id']:row for row in data['rows']}
summary={'status':r['quality_status'],'test_used_for_fitting':False,'stages':{}}
for stage,report in r['stages'].items():
    failures=[]
    for name,value in report['intervals'].items():
        if value['status']=='passed':continue
        failure={'interval':name,'result':value,'delay_algorithm':fit[stage]['intervals'][name]['selection']['delay']['algorithm'],
                 'area_algorithm':fit[stage]['intervals'][name]['selection']['area']['algorithm'],
                 'frozen_margin_scale':fit[stage]['model']['intervals'][name]['validation_delay_scale'],
                 'observations':[{'width':by_id[p['id']]['features']['width'],'delay_actual':by_id[p['id']]['delay_ps'],
                                  'delay_predicted':p['delay_ps'],'area_actual':by_id[p['id']]['comb_area_um2'],
                                  'area_predicted':p['comb_area_um2']} for p in value['predictions']]}
        failures.append(failure)
    summary['stages'][stage]={'status':report['status'],'aggregate':report['aggregate'],'ranking':report['ranking'],
                              'passed_classes':len(report['intervals'])-len(failures),'failed_classes':failures}
write(out/'asap7-independent-failure-analysis-v1.json',summary)
for stage,report in summary['stages'].items():
    print(stage,'passed_classes',report['passed_classes'],'aggregate',json.dumps(report['aggregate']))
    for f in report['failed_classes']:
        q=f['result'];print('FAILED',f['interval'],'false_feasible',q['false_feasible'],'/',q['denominator'],
            'delay_med_p95',q['delay']['median_relative_error'],q['delay']['p95_relative_error'],
            'area_med_p95',q['area']['median_relative_error'],q['area']['p95_relative_error'],
            'algorithms',f['delay_algorithm'],f['area_algorithm'],'margin',f['frozen_margin_scale'],'observations',f['observations'])
    print('ranking',report['ranking']['matching_pairs'],'/',report['ranking']['denominator'])
