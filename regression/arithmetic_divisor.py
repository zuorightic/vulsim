"""Actual-width safety certificates, including legal heterogeneous Ite."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import unittest
from experiments.arithmetic_dse.whole_graph_checks import verify_safe_divisors

ROOT=Path(__file__).resolve().parents[1]

def example(ne=False,source=16,result=8,branches=None,extend=False,nested=False,branch_width=16):
    nodes=[]
    def ref(i):return {'kind':0,'node':str(i),'width':nodes[i]['width']}
    def literal(w,x):return {'kind':1,'width':w,'limbs':[str((x>>(64*i))&((1<<64)-1)) for i in range((w+63)//64)]}
    def node(w,kind,args=(),opcode=0):
        i=len(nodes);nodes.append({'id':str(i),'width':w,'kind':kind,'opcode':opcode,'operands':list(args)})
        return ref(i)
    a=node(result,1);d=node(source,1);c=node(1,1)
    if branches is None:
        if extend:d=node(16,11,[d])
        z=node(1,4,[d,literal(d['width'],0)],12 if ne else 11)
        vals=[z,d,literal(d['width'],1)] if ne else [z,literal(d['width'],1),d]
    else:vals=[c,literal(branch_width,branches[0]),literal(branch_width,branches[1])]
    safe=node(16 if nested else result,9,vals)
    if nested:safe=node(result,9,[c,safe,literal(16,1)])
    node(result,4,[a,safe],4)
    return {'graph':{'nodes':nodes}}

class DivisorContracts(unittest.TestCase):
    def test_Eq_Ne_truncated_unknown_input_rejected(self):
        for ne in (False,True):
            with self.subTest(ne=ne),self.assertRaisesRegex(ValueError,'unsafe_divisor'):
                verify_safe_divisors(example(ne=ne))
            self.assertEqual(256 & ((1<<8)-1),0)

    def test_nonzero_branches_and_nested_select_must_survive_truncation(self):
        for branches,nested in [((256,1),False),((256,512),True)]:
            with self.subTest(branches=branches),self.assertRaisesRegex(ValueError,'unsafe_divisor'):
                verify_safe_divisors(example(branches=branches,nested=nested))

    def test_legal_mixed_width_and_safe_wrappers_are_retained(self):
        for r in (example(branches=(257,1)),example(branches=(257,513),nested=True),
                  example(result=16),example(ne=True,result=16),
                  example(source=8,extend=True),example(ne=True,source=8,extend=True)):
            self.assertEqual(verify_safe_divisors(r),1)

    def test_existing_176_actual_graphs(self):
        reports=divmod=0
        for path in sorted((ROOT/'experiments/arithmetic/evidence/step6_graphs_v1/reports').glob('*.json.gz')):
            divmod+=verify_safe_divisors(json.loads(gzip.decompress(path.read_bytes())));reports+=1
        self.assertEqual((reports,divmod),(176,186))

    def test_128_to_64_limb_boundary(self):
        with self.assertRaisesRegex(ValueError,'unsafe_divisor'):
            verify_safe_divisors(example(result=64,branches=(1<<65,1),branch_width=128))
        self.assertEqual(verify_safe_divisors(example(result=64,branches=((1<<65)|1,1),branch_width=128)),1)

if __name__=='__main__':unittest.main()
