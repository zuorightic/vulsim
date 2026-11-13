"""Finite arithmetic and dependency proofs for the common wide Query successor."""
import unittest
from copy import deepcopy
from experiments.arithmetic_dse import wide_arithmetic as a,wide_family_sources as sources,wide_operator_query as q,wide_operator_samples as samples


class WideFamilyContracts(unittest.TestCase):
    def test_exhaustive_carry_and_unsigned_borrow(self):
        for op in ('add','adc','sub','sbb'):
            for wa,wb,w in ((1,1,1),(2,3,3),(3,2,4)):
                status='carry' if op in ('add','adc') else 'borrow'
                p=a.spec(op,wa,wb,w,status=status,control='dynamic' if op in ('adc','sbb') else 'zero')
                for x in range(1<<wa):
                    for y in range(1<<wb):
                        for cin in (0,1):
                            c=cin if op in ('adc','sbb') else 0
                            raw=x+y+c if status=='carry' else x-y-c
                            flag=int(raw>=1<<w) if status=='carry' else int(raw<0)
                            self.assertEqual(a.evaluate(p,x,y,cin),(raw&((1<<w)-1))|(flag<<w))

    def test_high_multiply_keeps_lower_carry_dependencies(self):
        p=a.spec('mul',64,64,128,lo=64,bits=64)
        self.assertEqual(samples.input_demand(p,'lhs'),set(range(64)))
        self.assertEqual(samples.input_demand(p,'rhs'),set(range(64)))
        self.assertEqual(a.evaluate(p,1<<63,1<<63),1<<62)
        self.assertEqual(a.evaluate(p,(1<<64)-1,(1<<64)-1),(1<<64)-2)
        p=a.spec('ult',65,64,65)
        self.assertEqual(len(samples.input_demand(p,'lhs')),65)
        self.assertEqual(a.evaluate(p,1<<64,0),0)

    def test_add_normalization_preserves_connections_sub_is_directional(self):
        for op in ('add','adc'):
            p=a.spec(op,17,31,32,za=15,control='dynamic' if op=='adc' else 'zero')
            swapped=deepcopy(p)
            for n in ('width','zero_hex','one_hex'):swapped['lhs_'+n],swapped['rhs_'+n]=swapped['rhs_'+n],swapped['lhs_'+n]
            self.assertEqual(a.features(p,1373),a.features(swapped,1373))
            for x,y in ((0,1),(12345,987654),(65535,1<<30)):
                self.assertEqual(a.evaluate(p,x,y,1),a.evaluate(swapped,y,x,1))
        p=a.spec('sbb',65,64,65,status='borrow',control='dynamic')
        self.assertEqual(a.permutation(p),[0,1])
        self.assertNotEqual(a.evaluate(p,3,5,1),a.evaluate(p,5,3,1))

    def test_known_result_masks_are_sound_and_aliases_are_semantic(self):
        for op in a.OPERATIONS:
            p=a.spec(op,3,3,6 if op=='mul' else 3,status='none',control='dynamic' if op in ('adc','sbb','mux') else 'zero',za=2,ob=1)
            z,o=a.known_result(p)
            for x in range(8):
                for y in range(8):
                    for c in (0,1):
                        value=a.evaluate(p,x,y,c);self.assertEqual(value&z,0);self.assertEqual(value&o,o)
        for constant in (0,1,4):
            p=a.spec('mul',9,4,13,zb=15^constant,ob=constant)
            self.assertIsNotNone(a.aliases(p))
            for x in (0,1,257,511):self.assertEqual(a.evaluate(p,x,7),x*constant)

    def test_wide_sources_and_fail_closed_query(self):
        rows=sources.sources();qual=sources.qualification_sources()
        self.assertEqual(len(rows),52);self.assertEqual(len(qual),7)
        for row in rows+qual:
            f=row['features'];g=samples.layout(f);self.assertGreater(g['input_bits'],0)
            descriptor=q.descriptor(f,1373,'TEST_ONLY');self.assertTrue(q.features(descriptor))
            self.assertFalse(samples.geometry_contract(f)['mapped_qualified'])
        p=a.spec('add',512,512,513)
        self.assertEqual(a.evaluate(p,(1<<512)-1,1),1<<512)
        descriptor=q.descriptor(sources.local(p),1500,'TEST_ONLY')
        for mutate in (lambda x:x['flow_context'].update(target_period_ps=True,abc_target_ps=True),lambda x:x.update(required_result_bits=[512]),lambda x:x['local_context']['producer'].update(carry='dynamic')):
            bad=deepcopy(descriptor);mutate(bad)
            with self.assertRaises(ValueError):q.features(bad)


if __name__=='__main__':unittest.main()
