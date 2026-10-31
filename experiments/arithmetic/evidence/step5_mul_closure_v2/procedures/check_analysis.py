from pathlib import Path
import gzip,hashlib,json,sys
R=Path.cwd();sys.path.insert(0,str(R))
from experiments.arithmetic_dse.step5_analysis import position_analysis,verify_position_analysis,sensitivity,validate_selection
from experiments.arithmetic_dse.exact_analysis import check_sensitivity
B=R/'build/step5-closure-20261031';E=R/'experiments/arithmetic/evidence/step5_mul_templates_v1';new=Path(sys.argv[1]) if len(sys.argv)>1 else B/'generated';data={};checked=0
for item in json.loads((E/'report_index.json').read_text()):
 old=json.loads(gzip.decompress((R/item['report']).read_bytes()));current=json.loads((new/(item['name']+'.json')).read_text());raw=gzip.decompress((R/item['rtl']).read_bytes());assert (new/(item['name']+'.sv')).read_bytes()==raw
 for key in ('graph','stages','protocol','graph_sha256','schedule_sha256','rtl_sha256','selection'):assert old[key]==current[key],(item['name'],key)
 checked+=validate_selection(current);data[item['name']]=old
position=position_analysis(data['w8_full_1'],json.loads((E/'positions.json').read_text())['placements']);verify_position_analysis(data['w8_full_1'],position);s=sensitivity(data);check_sensitivity(s)
(B/'positions_v2.json').write_text(json.dumps(position,indent=2)+'\n');(B/'sensitivity_v2.json').write_text(json.dumps(s,indent=2)+'\n')
summary={'status':'passed','actual_archived_graphs_compared':len(data),'regions':sum(len(v['graph']['regions']) for v in data.values()),'new_graph_schedule_RTL_and_candidate_choices_unchanged':True,'outer_C_candidates_recomputed':checked,'actual_feasible_positions':position['feasible_count'],'local_feasible_bits':[x['register_bits'] for x in position['placements'] if x['within_production_cap']],'production_bits':position['production']['register_bits'],'production_comb':position['production']['comb'],'position_scope':position['production']['scope'],'sensitivity_structures':s['structures'],'sensitivity_contexts':s['contexts'],'sensitivity_selection_changes':s['selected_changes'],'graph_for_retest_unchanged':data['w128_full_3']['graph_sha256'],'schedule_for_retest_unchanged':data['w128_full_3']['schedule_sha256'],'RTL_for_retest_unchanged':data['w128_full_3']['rtl_sha256']}
(B/'software_checks.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
