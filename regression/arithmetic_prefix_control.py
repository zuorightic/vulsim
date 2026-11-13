"""Generic graph invariants for prefix G and per-source S query features."""
import unittest
from experiments.arithmetic_dse import reduction_prefix_features as g,state_control_queries as s,state_control_response as response


def terms(columns):return [[(i,j,c) for j,c in enumerate(row)] for i,row in enumerate(columns)]


class CommonGeometry(unittest.TestCase):
    def test_wiring_does_not_create_arithmetic_gates(self):
        f=g.features(513,terms([[0,1],[200,201],[511,512]]),1373)
        self.assertEqual(f['counter_count'],0)
        self.assertEqual(f['final_live_logic_gates'],0)

    def test_identity_and_term_order_are_not_price_features(self):
        t=terms([list(range(16)),list(range(8,32)),list(range(2,15)),[20,21]])
        renamed=[[(900-i,bit+100,column) for i,bit,column in row] for row in reversed(t)]
        self.assertEqual(g.features(64,t,1500),g.features(64,renamed,1500))
        self.assertNotEqual(g.features(64,t,500)['final_pressure_logic'],g.features(64,t,3000)['final_pressure_logic'])
        with self.assertRaises(ValueError):g.features(64,[t[0],t[0],t[1]],1500)

    def test_sparse_segments_remain_visible_and_width_is_numerical(self):
        narrow=g.features(64,terms([[0,1,2],[0,1,2],[15,16,17]]),1500)
        wide=g.features(1024,terms([[0,1,2],[0,1,2],[15,16,17]]),1500)
        for name in ('counter_count','final_live_logic_gates','final_logic_depth'):
            self.assertEqual(narrow[name],wide[name])

    def test_source_specific_loads_and_hold_capture_are_separate(self):
        q=s.queries([32,64],[900,7],1,1500)
        valid=[x for x in q if x['path_class']=='native_valid']
        self.assertEqual([x['features']['enabled_data_sinks'] for x in valid],[900,7])
        self.assertEqual([x['features']['launch_has_hold'] for x in valid],[1,0])
        port=next(x for x in q if x['path_class']=='input_valid')
        self.assertEqual(port['features']['capture_enable_logical_sinks'],97)
        models={'native_valid':dict(function=dict(features=['enabled_data_sinks'],coefficients=[1],intercept=0),reserve_ps=5)}
        self.assertEqual(response.aggregate(models,q,'native_valid')['guarded_required_ps'],905)
        self.assertFalse(response.aggregate(models,q,'native_valid')['price_qualification_granted'])


if __name__=='__main__':unittest.main()
