"""Independent saved-graph certificate, without a generator or NodeId fixtures."""
from copy import deepcopy
import gzip,json,unittest
from pathlib import Path
from experiments.arithmetic_dse.block_tree_evidence import verify_block_trees

R=Path(__file__).resolve().parents[1]
E=R/'experiments/arithmetic/evidence/step5_mul_templates_v1'
def report(name):return json.loads(gzip.decompress((E/'reports'/(name+'.json.gz')).read_bytes()))
class BlockEvidenceTests(unittest.TestCase):
 def test_all_saved_graphs(self):
  reports=regions=blocked=0
  for item in json.loads((E/'report_index.json').read_text()):
   r=json.loads(gzip.decompress((R/item['report']).read_bytes()))
   reports+=1;regions+=len(r['graph']['regions']);blocked+=verify_block_trees(r)
  self.assertEqual((reports,regions),(129,219));self.assertGreater(blocked,0)
 def test_saved_graph_mutations(self):
  original=report('w8_full_1');region=original['graph']['regions'][0]
  def high(r):
   return next(n for n in r['graph']['nodes'] if n['id'] in region['members'] and n['kind']==14 and n['lo']==4 and n['operands'][0]['node']==region['inputs'][0]['node'])
  r=deepcopy(original);high(r).update(lo=0,hi=3)
  with self.assertRaisesRegex(ValueError,'duplicate'):verify_block_trees(r)
  r=deepcopy(original);high(r)['operands'][0]['node']=region['inputs'][1]['node']
  with self.assertRaisesRegex(ValueError,'wrong original'):verify_block_trees(r)
  r=deepcopy(original);n=next(n for n in r['graph']['nodes'] if n['id'] in region['members'] and n['kind']==2);n['operands'][1]=deepcopy(n['operands'][0])
  with self.assertRaisesRegex(ValueError,'omitted/repeated'):verify_block_trees(r)
  r=deepcopy(original);n=next(n for n in r['graph']['nodes'] if n['id'] in region['members'] and n['kind']==18 and n['operands'][1]['width']==8);n['operands'][1]['width']=4
  with self.assertRaisesRegex(ValueError,'shift disagrees'):verify_block_trees(r)
  r=report('w13_full_1');n=next(n for n in r['graph']['nodes'] if n['kind']==14 and n['lo']==12);n.update(lo=11,hi=11)
  with self.assertRaisesRegex(ValueError,'coordinate/tail'):verify_block_trees(r)
if __name__=='__main__':unittest.main()
