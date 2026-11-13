"""Meaningful invariants for structural support and commutative Add contracts."""
import unittest
from copy import deepcopy
from experiments.arithmetic_dse import conditional_function_support_v2 as support
from experiments.arithmetic_dse import canonical_add


def rows(values):
    return [dict(role='train',source='source'+str(i),features=dict(work=v)) for i,v in enumerate(values)]


class DistinctGeometrySupport(unittest.TestCase):
    def test_duplicate_source_geometry_does_not_hide_training_structures(self):
        model=support.derive(rows([0,0,0,1,1,1,2,2,2]),['work'],k=2)
        self.assertEqual(model['distinct_geometries'],3)
        self.assertGreater(model['radius'],0)
        for v in (0,1,2):
            self.assertEqual(support.check(model,dict(work=v),1500)['status'],'structurally_supported')

    def test_source_and_period_replication_cannot_change_membership(self):
        base=rows([0,1,2,4]);copies=rows([0]*9+[1]*3+[2]*7+[4]*2)
        copies += [dict(r) for r in copies]
        a=support.derive(base,['work']);b=support.derive(copies,['work'])
        for field in ('bounds','scales','anchors','k','radius'):
            self.assertEqual(a[field],b[field])
        for v in (-1,0,.5,1,2,3,4,5):
            for t in (499,500,1000,1373,3000,3001):
                self.assertEqual(support.check(a,dict(work=v),t),support.check(b,dict(work=v),t))

    def test_small_geometry_population_is_explicit(self):
        for values in ([2]*9,[0,0,1,1]):
            m=support.derive(rows(values),['work'],k=2)
            for v in set(values):self.assertEqual(support.check(m,dict(work=v),1000)['status'],'structurally_supported')
        self.assertEqual(support.check(m,dict(work=99),1000)['status'],'cost_uncovered')

    def test_roles_and_invalid_calibration_rejected(self):
        bad=rows([0,1,2]);bad[0]['role']='validation'
        with self.assertRaises(ValueError):support.derive(bad,['work'])
        with self.assertRaises(ValueError):support.derive(rows([0,1,2]),['work'],k=0)
        with self.assertRaises(ValueError):support.derive(rows([0,1,2]),['work'],radius_factor=float('nan'))


def add_query(a,b,r,za=0,zb=0):
    return dict(version='arithmetic-operator-query-v1',semantics='unsigned-modulo-v1',
                declared_result_width=r,required_result_bits=list(range(r)),
                local_context=dict(producer=dict(operation='add',lhs_width=a,rhs_width=b,
                    result_width=r,lhs_zero_hex=hex(za),rhs_zero_hex=hex(zb),
                    lhs_one_hex='0x0',rhs_one_hex='0x0',carry='zero',capture_banks=1),
                    consumers=[],captures=[dict(banks=1,declared_width=r,result_bit_map=list(range(r)))]),
                flow_context=dict(target_platform='asap7',evaluation_stage='grt',target_period_ps=1000,
                    abc_target_ps=1000,profile_sha256='TEST_ONLY',boundary_policy='TEST_ONLY'),
                topology=dict(operand_shared_input_roots=0,same_stage_remaining_depth=1))


def commute(query):
    q=deepcopy(query);p=q['local_context']['producer']
    for field in ('width','zero_hex','one_hex'):
        p['lhs_'+field],p['rhs_'+field]=p['rhs_'+field],p['lhs_'+field]
    return q


class CanonicalAddContracts(unittest.TestCase):
    def test_commutation_and_idempotence_preserve_every_feature(self):
        for q in (add_query(8,8,9,0,15),add_query(15,21,22,2047),add_query(32,9,12,255),add_query(5,7,4)):
            a=canonical_add.normalize(q);b=canonical_add.normalize(commute(q))
            self.assertEqual(a['descriptor'],b['descriptor'])
            self.assertEqual(canonical_add.features(q),canonical_add.features(commute(q)))
            self.assertEqual(canonical_add.normalize(a['descriptor'])['descriptor'],a['descriptor'])
            self.assertEqual(a['descriptor']['flow_context']['boundary_policy'],canonical_add.BOUNDARY_POLICY)
            self.assertFalse(a['physical_mapping_equivalence_qualified'])

    def test_result_loads_and_capture_maps_are_not_reordered(self):
        q=add_query(9,25,26,7)
        consumer=dict(spec=dict(operation='add',lhs_width=96,rhs_width=64,result_width=96,
                              lhs_zero_hex='0x0',lhs_one_hex='0x0',rhs_zero_hex=hex(((1<<64)-1)^(((1<<26)-1)<<17)),rhs_one_hex='0x0',carry='zero',capture_banks=1),
                      bindings=[dict(operand_index=1,result_bit_map=['0']*17+list(range(26))+['0']*21)],
                      other_dynamic_inputs='independent_launch; source correlations require G validation')
        q['local_context']['consumers']=[consumer];normalized=canonical_add.normalize(q)
        self.assertEqual(normalized['descriptor']['local_context']['consumers'],q['local_context']['consumers'])
        self.assertEqual(normalized['descriptor']['local_context']['captures'],q['local_context']['captures'])
        self.assertEqual(canonical_add.features(q),canonical_add.features(commute(q)))

    def test_unregistered_arithmetic_contract_rejected(self):
        q=add_query(8,12,13);q['local_context']['producer']['carry']='dynamic'
        with self.assertRaises(ValueError):canonical_add.normalize(q)


if __name__=='__main__':unittest.main()
