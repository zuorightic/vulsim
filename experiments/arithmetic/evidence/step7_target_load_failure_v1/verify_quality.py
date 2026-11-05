"""Standalone compact-label replay; original raw-measurement audit is separate."""
from collections import defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path


def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
def same(actual,expected):
    if isinstance(actual,(int,float)) and not isinstance(actual,bool):
        assert math.isclose(actual,expected,rel_tol=1e-10,abs_tol=1e-8),(actual,expected)
    elif isinstance(actual,dict):
        assert actual.keys()==expected.keys()
        for key in actual:same(actual[key],expected[key])
    elif isinstance(actual,list):
        assert len(actual)==len(expected)
        for a,b in zip(actual,expected):same(a,b)
    else:assert actual==expected,(actual,expected)


def predict(model,values):
    x=[values[k] for k in model['features']]
    if model['kind']=='linear':
        y=model['intercept']
        for c,v in zip(model['coefficients'],x,strict=True):y+=c*v
    else:
        assert model['kind']=='tree';i=0;seen=set();nodes=model['nodes']
        while 'value' not in nodes[i]:
            assert i not in seen;seen.add(i);n=nodes[i]
            i=n['left'] if x[n['feature']]<=n['threshold'] else n['right']
        y=nodes[i]['value']
    assert math.isfinite(y)
    return max(0.,y)


def metrics(actual,estimated,floor):
    errors=[abs(a-p) for a,p in zip(actual,estimated,strict=True)]
    relative=sorted(e/max(abs(a),floor) for e,a in zip(errors,actual))
    def quantile(q):
        pos=(len(relative)-1)*q;i=int(pos)
        return relative[i]+(relative[min(i+1,len(relative)-1)]-relative[i])*(pos-i)
    return {'n':len(actual),'MAE':sum(errors)/len(errors),'median_relative_error':quantile(.5),
            'p95_relative_error':quantile(.95),'max_relative_error':max(relative),'relative_error_floor':floor}


def verify(folder):
    summary=json.loads((folder/'checkpoint.json').read_text());raw=(folder/'quality-labels.json.gz').read_bytes()
    assert sha(raw)==summary['quality_labels_sha256']
    p=json.loads(gzip.decompress(raw));g=p['protocol']['quality_gates'];ratios=p['protocol']['feasibility_ratios']
    same(sha(encoded(p['candidate'])),p['selection']['candidate_sha256'])
    same(sha(encoded(p['fit_report'])),p['selection']['fit_report_sha256'])
    same(sha(encoded(p['protocol'])),p['selection']['protocol_sha256'])
    same(sha(encoded(p['selection'])),summary['selection_sha256'])
    same(sha(encoded(p['result'])),summary['independent_result_sha256'])
    phases={}
    for phase,rows in [('validation',[r for r in p['fitting_rows'] if r['split']=='validation']),('test',p['test_rows'])]:
        phases[phase]={}
        for stage in ('synth','grt'):
            count=0;false_total=0;den_total=0
            for name,model in p['candidate']['stages'][stage]['intervals'].items():
                subset=[r for r in rows if r['stage']==stage and r['interval_key']==name]
                assert subset and len({r['id'] for r in subset})==len(subset)
                passed=True;actual_false=0
                stored=p['fit_report']['stages'][stage]['intervals'][name]['quality'] if phase=='validation' else p['result']['stages'][stage]['intervals'][name]
                for quantity,field,floor in [('delay','delay_ps',1.5),('area','comb_area_um2',1e-4)]:
                    actual=[r[field] for r in subset]
                    estimated=[predict(model[quantity],r['features'])*(model['validation_delay_scale'] if quantity=='delay' else 1) for r in subset]
                    met=metrics(actual,estimated,floor);same(met,stored[quantity]['metrics'])
                    false=sum(v<=y*k<y for y,v in zip(actual,estimated) for k in ratios) if quantity=='delay' else 0
                    den=len(subset)*len(ratios) if quantity=='delay' else 0
                    same(false,stored[quantity]['false_feasible']);same(den,stored[quantity]['denominator'])
                    violation=max(met[k+'_relative_error']/g[quantity+'_'+k+'_relative_error_max'] for k in ('median','p95'))
                    if quantity=='delay':
                        violation=max(violation,false/den/g['false_feasible_fraction_max']);false_total+=false;den_total+=den
                        actual_false=sum(v<=r['period_ps']-r['observed_H_ps']<y for r,y,v in zip(subset,actual,estimated))
                    status='passed' if violation<=1 else 'failed'
                    same(status,stored[quantity]['status']);same(violation,stored[quantity]['gate_violation_ratio'])
                    passed&=status=='passed'
                same('passed' if passed else 'failed',stored['status']);same(actual_false,stored['actual_target_false_feasible'])
                count+=int(passed)
            expected=p['fit_report']['stages'][stage] if phase=='validation' else p['result']['stages'][stage]
            same(count,expected['passing_intervals'])
            phases[phase][stage]={'passing_intervals':count,'false_feasible':false_total,'denominator':den_total}
    assert p['result']['quality_status']==summary['quality_status']=='failed'
    assert phases['test']['grt']['passing_intervals']==41
    assert p['release']['published']==summary['published']==[]
    return {'status':'passed','quality_status':'failed','published':0,'phases':phases,
            'scope':'compact labels and numeric quality decision; raw reports, source execution and external artifacts require the separate full archive'}


if __name__=='__main__':print(json.dumps(verify(Path(__file__).resolve().parent),indent=2))
