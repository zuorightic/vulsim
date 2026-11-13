import unittest
from copy import deepcopy
from experiments.arithmetic_dse import reduction_wide_features as wide,reduction_merge_features as old
from experiments.arithmetic_dse import reduction_wide_sampling as sampling,reduction_sampling_v2 as old_sampling
from experiments.arithmetic_dse import operator_function_successor as operator,wide_arithmetic as arithmetic,wide_operator_query as query,wide_family_sources as shells
from experiments.arithmetic_dse.state_control_cones import trace


class SuccessorContracts(unittest.TestCase):
    def test_old_delay_geometry_is_preserved_including_sparse_carries(self):
        for width in (5,16,64,129,257):
            for count in (3,7,17):
                terms=[[(i,b,b) for b in range(width) if (b+i)%5!=0] for i in range(count)]
                for T in (500,1373,3000):self.assertEqual(wide.features(width,terms,T)['delay'],old.features(width,terms,T))

    def test_wide_geometry_is_independent_of_names_and_term_order(self):
        for width in (132,256,512,513,1024):
            terms=[[(i,b,b) for b in range(width)] for i in range(3)]
            renamed=[[(i+999,b+1000,c) for i,b,c in reversed(t)] for t in reversed(terms)]
            self.assertEqual(wide.features(width,terms,1373),wide.features(width,renamed,1373))

    def test_correlated_bits_and_invalid_dimensions_remain_rejected(self):
        terms=[[(i,b,b) for b in range(8)] for i in range(3)]
        bad=deepcopy(terms);bad[1][0]=bad[0][0]
        with self.assertRaises(ValueError):wide.features(512,bad,1500)
        with self.assertRaises(ValueError):wide.features(4097,terms,1500)
        with self.assertRaises(ValueError):wide.features(512,terms,0)

    def test_wide_emitter_keeps_old_bytes_and_independent_integer_arithmetic(self):
        for width in (32,129,512,513):
            terms=[[(i,b,b) for b in range(width)] for i in range(3)];q=dict(output_bits=width,terms=terms,consumers=[])
            if width<=257:self.assertEqual(sampling.source(q),old_sampling.source(q))
            g=sampling.geometry(q)
            for values in ((0,0,0),((1<<width)-1,1,1),(17,29,255)):
                packed=sum(((v>>b)&1)<<g['offsets'][i,b] for i,v in enumerate(values) for b in range(width))
                self.assertEqual(sampling.evaluate(q,packed),sum(values)&((1<<width)-1))

    def test_comparison_work_is_disjoint_and_width_is_numeric(self):
        for width in (33,64,137,256):
            for op in ('eq','ult','ule'):
                q=query.descriptor(shells.local(arithmetic.spec(op,width,width,width)),1373,'TEST_ONLY')
                f=operator.features(q);self.assertEqual(f['compare_order_work']+f['compare_eq_work'],width)
                self.assertEqual(f['compare_order_work'],0 if op=='eq' else width)

    def test_control_cone_handles_reconvergence_and_rejects_missing_arcs(self):
        ff=dict(sequential=True,buffer_or_inverter=False,data_pins=['D'],pins={'Q':dict(direction='output'),'D':dict(direction='input')})
        buf=dict(sequential=False,buffer_or_inverter=True,data_pins=[],pins={'A':dict(direction='input'),'Y':dict(direction='output')},timing_arcs=[['A','Y']])
        gate=dict(sequential=False,buffer_or_inverter=False,data_pins=[],pins={'A':dict(direction='input'),'B':dict(direction='input'),'Y':dict(direction='output')},timing_arcs=[['A','Y'],['B','Y']])
        cells={'FF':ff,'BUF':buf,'AND':gate};instances={'root':'FF','a':'BUF','b':'BUF','join':'AND','sink':'FF'}
        nets={p:dict(direction=d,net=n) for p,d,n in [('root/Q','output','r'),('a/A','input','r'),('b/A','input','r'),('a/Y','output','a'),('b/Y','output','b'),('join/A','input','a'),('join/B','input','b'),('join/Y','output','j'),('sink/D','input','j')]}
        r=trace('root/Q',instances,cells,nets);self.assertEqual(r['sequential_sink_pins'],['sink/D']);self.assertEqual(r['max_cell_depth'],2);self.assertEqual(r['reconvergent_pins'],1)
        bad=deepcopy(cells);bad['AND']['timing_arcs'].remove(['A','Y'])
        with self.assertRaises(ValueError):trace('root/Q',instances,bad,nets)


if __name__=='__main__':unittest.main()
