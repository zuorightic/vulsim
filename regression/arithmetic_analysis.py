"""Independent feasibility, local production preference and exact JSON types."""
from copy import deepcopy
from fractions import Fraction
import gzip,json,unittest
from pathlib import Path
from experiments.arithmetic_dse.step5_analysis import position_analysis,verify_position_analysis,sensitivity
from experiments.arithmetic_dse.exact_analysis import encode,decode,score_key,check_sensitivity
R=Path(__file__).resolve().parents[1];E=R/'experiments/arithmetic/evidence/step5_mul_templates_v1'
class AnalysisTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.report=json.loads(gzip.decompress((E/'reports/w8_full_1.json.gz').read_bytes()));cls.old=json.loads((E/'positions.json').read_text());cls.raw=cls.old['placements'];cls.position=position_analysis(cls.report,cls.raw)
 def test_real_positions_and_production_preference(self):
  result=verify_position_analysis(self.report,self.position);self.assertEqual(result['feasible_count'],4);self.assertEqual(result['production']['register_bits'],130);self.assertEqual(decode(result['production']['comb']),22)
  self.assertEqual(sorted(x['register_bits'] for x in result['placements'] if x['within_production_cap']),[130,144,146,162]);self.assertIn('not full position space',result['context']['enumeration_scope'])
 def test_two_over_budget_falsely_claim_feasible(self):
  rows=deepcopy(self.raw[:2]);self.assertTrue(all(x['maximum_delay']>2.1 for x in rows))
  for x in rows:x['within_production_cap']=True
  from experiments.arithmetic_dse.freeze_history import historical_step5_analysis
  old=historical_step5_analysis(R).position_analysis(self.report,rows)
  self.assertEqual(sum(x['within_production_cap'] for x in old['placements']),2)
  with self.assertRaisesRegex(ValueError,'feasibility disagrees'):position_analysis(self.report,rows)
 def test_cap_and_reverse_flags(self):
  bad=deepcopy(self.position);bad['cap']=encode(100)
  with self.assertRaisesRegex(ValueError,'cap mismatch'):verify_position_analysis(self.report,bad)
  for i in range(len(self.raw)):
   rows=deepcopy(self.raw);rows[i]['within_production_cap']=not rows[i]['within_production_cap']
   with self.assertRaisesRegex(ValueError,'feasibility disagrees'):position_analysis(self.report,rows)
 def test_strict_counts_flags_and_context(self):
  for value in (1,0,'true',None):
   rows=deepcopy(self.raw);rows[0]['within_production_cap']=value
   with self.assertRaisesRegex(ValueError,'requires boolean'):position_analysis(self.report,rows)
  for value in ('130',130.0,True):
   rows=deepcopy(self.raw);rows[0]['register_bits']=value
   with self.assertRaisesRegex(ValueError,'JSON integer'):position_analysis(self.report,rows)
   doc=deepcopy(self.position);doc['production']['register_bits']=value
   with self.assertRaisesRegex(ValueError,'JSON integer'):verify_position_analysis(self.report,doc)
  rows=deepcopy(self.raw);rows[0]['stages']=[]
  with self.assertRaisesRegex(ValueError,'complete stage map'):position_analysis(self.report,rows)
  doc=deepcopy(self.position);doc['context']['L']=4
  with self.assertRaisesRegex(ValueError,'context mismatch'):verify_position_analysis(self.report,doc)
  doc=deepcopy(self.position);doc['production']['stages'][0]=False
  with self.assertRaisesRegex(ValueError,'JSON integer'):verify_position_analysis(self.report,doc)
 def test_false_production_and_optimality_claims(self):
  bad=deepcopy(self.report);bad['pipeline']['register_bits']=129
  with self.assertRaisesRegex(ValueError,'production map/report'):position_analysis(bad,self.raw)
  doc=deepcopy(self.position);doc['production']['minimum_bits_at_equal_delay_and_comb']=129
  with self.assertRaisesRegex(ValueError,'summary mismatch'):verify_position_analysis(self.report,doc)
  # A feasible but more expensive saved map is no longer the production report.
  bad=deepcopy(self.report);row=next(x for x in self.raw if x['within_production_cap'] and x['register_bits']==144);bad['stages']=row['stages'];bad['pipeline'].update(final_delay=row['maximum_delay'],register_bits=row['register_bits'],register_count=row['register_count'])
  with self.assertRaisesRegex(ValueError,'minimum state'):position_analysis(bad,self.raw)
 def test_exact_roundtrip_and_numeric_sort(self):
  for value in (Fraction(1,64),Fraction(1,16),Fraction(1,4),Fraction(22),Fraction(2**63+1,3)):
   self.assertEqual(decode(json.loads(json.dumps(encode(value)))),value)
  self.assertLess(decode(encode(2)),decode(encode(10)))
  for bad in ({'numerator':1,'denominator':0},{'numerator':True,'denominator':1},{'numerator':1,'denominator':-1},{'numerator':'1','denominator':2},{'numerator':1,'denominator':2.0},{'numerator':2,'denominator':4},'1/64',0.25):
   with self.assertRaises(ValueError):decode(bad)
 def test_sensitivity_same_selection_exact_types(self):
  data={p.stem.removesuffix('.json'):json.loads(gzip.decompress(p.read_bytes())) for p in (E/'reports').glob('sensitivity*.json.gz')}
  result=sensitivity(data);check_sensitivity(result);self.assertEqual(result['structures'],30);self.assertEqual(result['contexts'],10);self.assertEqual(result['selected_changes'],0)
  for row in result['rows']:
   for variant in row['structures']:
    score_key(variant['linear_score']);score_key(variant['square_score'])
  bad=deepcopy(result);bad['rows'][0]['structures'][0]['linear_rank']=True
  with self.assertRaisesRegex(ValueError,'JSON integer'):check_sensitivity(bad)
if __name__=='__main__':unittest.main()
