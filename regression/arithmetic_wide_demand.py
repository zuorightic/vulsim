"""Independent arithmetic and demand invariants for numerical price features."""
import unittest
from copy import deepcopy
from experiments.arithmetic_dse import wide_arithmetic as arithmetic,wide_alu_geometry as alu
from experiments.arithmetic_dse import wide_family_sources as sources,wide_operator_query as query,wide_function_model as model
from experiments.arithmetic_dse import wide_function_sampling_v2 as sampling


class DemandedArithmetic(unittest.TestCase):
    def test_domain_sampler_preserves_default_guards_and_reserved_targets(self):
        history=[]
        for period in (1500,500,3000):
            request=sampling.decide(history,'independent-software-fixture','train')['next_request']
            self.assertEqual(request['SDC_ps'],period)
            history.append(dict(request,source_id='independent-software-fixture',role='train',status='completed',
                implementation_id='TEST_ONLY_'+str(period),operator_delay_ps=400.,comb_area_um2=1.,
                data_setup_slack_ps=float(period-400),operator_maximum_covered=True,
                data_through_operator_covered=True,ownership_complete=True))
        result=sampling.decide(history,'independent-software-fixture','train')
        self.assertFalse(result['missing_clock_guards_ps'])
        request=result['next_request']
        if request is not None:
            self.assertTrue(500<=request['SDC_ps']<=3000)
            self.assertNotIn(request['SDC_ps'],(750,1000,1125,1250))
        with self.assertRaises(ValueError):sampling.decide([],'test','locked_test')

    def test_symbolic_graph_matches_finite_arithmetic(self):
        for op in ('add','adc','sub','sbb','ult','ule','eq','mux'):
            for w in (1,2,3,4):
                status='carry' if op=='adc' else 'borrow' if op=='sbb' else 'none'
                p=arithmetic.spec(op,w,w,w,status=status,control='dynamic' if op in ('adc','sbb','mux') else 'zero')
                for a in range(1<<w):
                    for b in range(1<<w):
                        for c in (0,1):self.assertEqual(alu.evaluate(p,a,b,c),arithmetic.evaluate(p,a,b,c))

    def test_known_bits_carry_and_output_slices(self):
        for op in ('add','adc','sub','sbb','eq','mux'):
            p=arithmetic.spec(op,3,4,5 if op!='eq' else 4,lo=1 if op!='eq' else 0,bits=3 if op!='eq' else 1,status='borrow' if op=='sbb' else 'none',control='dynamic' if op in ('adc','sbb','mux') else 'zero',za=2,ob=8)
            for a in range(8):
                for b in range(16):
                    for c in (0,1):self.assertEqual(alu.evaluate(p,a,b,c),arithmetic.evaluate(p,a,b,c))

    def test_truncated_add_counts_only_actual_dependencies(self):
        p=arithmetic.spec('add',193,127,194,bits=129);f=model.features(query.descriptor(sources.local(p),1373,'TEST_ONLY'))
        self.assertEqual(f['lhs_live_bits'],129)
        self.assertEqual(f['rhs_live_bits'],127)
        other=arithmetic.spec('add',129,127,129);g=model.features(query.descriptor(sources.local(other),1373,'TEST_ONLY'))
        for name in ('alu_work','alu_depth','alu_xor','alu_and','alu_or','alu_not','live_input_sum','active_overlap'):
            self.assertEqual(f[name],g[name])

    def test_add_commutation_retains_all_numerical_features(self):
        p=arithmetic.spec('adc',17,31,32,status='carry',control='dynamic',za=15);r=deepcopy(p)
        for n in ('width','zero_hex','one_hex'):r['lhs_'+n],r['rhs_'+n]=r['rhs_'+n],r['lhs_'+n]
        a=query.descriptor(sources.local(p),1373,'TEST_ONLY');b=query.descriptor(sources.local(r),1373,'TEST_ONLY')
        self.assertEqual(model.features(a),model.features(b))

    def test_unmeasured_boundary_is_refused_by_semantic_scope(self):
        q=query.descriptor(sources.local(arithmetic.spec('add',64,64,65)),1500,'TEST_ONLY')
        bad=deepcopy(q);bad['local_context']['captures'][0]['result_bit_map']=list(reversed(range(65)))
        with self.assertRaises(ValueError):model.semantic_scope(bad)
        bad=deepcopy(q);bad['local_context']['producer']['lhs_one_hex']='0x1'
        with self.assertRaises(ValueError):model.semantic_scope(bad)


if __name__=='__main__':unittest.main()
