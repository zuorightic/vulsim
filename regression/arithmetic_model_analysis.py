"""Mutations of actual native reports, checked without trusting their costs."""
import copy
import hashlib
import json
import sys
from pathlib import Path
from experiments.arithmetic_dse.model_analysis import verify_report,verify_selection,evaluate


def run(models,reports):
    checks=0;positions=0
    for platform in ('asap7','nangate45','sky130hd','gf180'):
        model=json.loads((models/(platform+'.json')).read_text());report=json.loads((reports/(platform+'.report.json')).read_text())
        rtl=(reports/(platform+'.sv')).read_text();verify_report(report,model,rtl);verify_selection(report,model);checks+=2
        variants=[]
        for key in ('final_delay','predicted_comb_area_um2','predicted_state_area_um2','predicted_total_area_um2','model_state_bits','model_state_signals','register_bits','register_count'):
            broken=copy.deepcopy(report);broken['pipeline'][key]+=1;variants.append(broken)
        for key,bad in [('register_bits',True),('model_state_signals','5'),('predicted_total_area_um2','1.0')]:
            broken=copy.deepcopy(report);broken['pipeline'][key]=bad;variants.append(broken)
        broken=copy.deepcopy(report);broken['pipeline']['allowed_stage_delays_ps']=[0]*len(report['stages']);variants.append(broken)
        broken=copy.deepcopy(report);broken['pipeline']['input_data_budget_ps']+=1;variants.append(broken)
        for broken in variants:
            try:verify_report(broken,model,rtl)
            except (ValueError,AssertionError):checks+=1
            else:raise AssertionError('forged physical cost/budget/type accepted')
        broken=copy.deepcopy(report);broken['selection']['candidates'][0]['score'][0]+=1
        try:verify_selection(broken,model)
        except ValueError:checks+=1
        else:raise AssertionError('forged candidate ranking accepted')
        path=reports/(platform+'.positions.json')
        if path.exists():
            feasible=[]
            for row in json.loads(path.read_text()):
                actual=evaluate(report,model,row['stages']);okay=actual['within_absolute_budget'] and actual['within_production_cap']
                if type(row['feasible']) is not bool or row['feasible']!=okay:raise AssertionError('position feasibility flag')
                for key in ('register_bits','register_count','model_state_bits','model_state_signals'):
                    if row[key]!=actual[key]:raise AssertionError('position cost '+key)
                if okay:feasible.append(actual)
                positions+=1
            if len(feasible)<2:raise AssertionError('no evidence of multiple feasible positions')
            if report['pipeline']['predicted_total_area_um2']>min(x['total_area_um2'] for x in feasible)+1e-8:
                raise AssertionError('production loses to declared fixed atomic-Mul local enumeration')
            checks+=1
    result={'status':'passed','native_report_and_mutation_checks':checks,'fixed_structure_positions_recomputed':positions,
            'domain':'actual local Mul/Add graphs; synthetic TEST_ONLY fixture models are mechanism tests, never physical quality evidence',
            'global_position_optimality_claim':False}
    print(json.dumps(result));return result


if __name__=='__main__':run(Path(sys.argv[1]),Path(sys.argv[2]))
