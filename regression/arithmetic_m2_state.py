"""Drive strengths may differ; sequential behavior must remain identical."""
import copy
import unittest
from experiments.arithmetic_dse.model_m2_state import compare_interfaces


class StateGraphs(unittest.TestCase):
    def fixture(self):
        model={'attributes':{'area':'1'},'ports':{'C':{'direction':'input','bits':[2]},'D':{'direction':'input','bits':[3]},'Q':{'direction':'output','bits':[4]}},
            'cells':{'auto1':{'type':'$_DFF_P_','parameters':{},'attributes':{},'port_directions':{'C':'input','D':'input','Q':'output'},'connections':{'C':[2],'D':[3],'Q':[4]}}},
            'netnames':{'internal':{'bits':[4],'attributes':{'capacitance':'1'}}}}
        states={'ff':{'type':'x1','parameters':{},'pins':model['ports'],'model':model}}
        return ({'full':'pins'},states,{'input':1,'output':2})

    def test_drive_change_requires_actual_graph_identity(self):
        a=self.fixture();b=copy.deepcopy(a);b[1]['ff']['type']='x2';m=b[1]['ff']['model'];m['attributes']['area']='2'
        m['netnames']['internal']['attributes']['capacitance']='2';m['cells']['renamed']=m['cells'].pop('auto1')
        proof=compare_interfaces(a,b);self.assertEqual(len(proof['drive_master_changes']),1)

    def test_clock_edge_change_rejected(self):
        a=self.fixture();b=copy.deepcopy(a);b[1]['ff']['model']['cells']['auto1']['type']='$_DFF_N_'
        with self.assertRaisesRegex(ValueError,'logical graph'):compare_interfaces(a,b)

    def test_data_connectivity_change_rejected(self):
        a=self.fixture();b=copy.deepcopy(a);b[1]['ff']['model']['cells']['auto1']['connections']['D']=[2]
        with self.assertRaises(ValueError):compare_interfaces(a,b)

    def test_output_correspondence_change_rejected(self):
        a=self.fixture();b=copy.deepcopy(a);b[1]['ff']['model']['ports']['Q']['bits']=[5]
        with self.assertRaises(ValueError):compare_interfaces(a,b)

    def test_initial_state_metadata_not_silently_ignored(self):
        a=self.fixture();b=copy.deepcopy(a);b[1]['ff']['model']['netnames']['internal']['attributes']['init']='1'
        with self.assertRaises(ValueError):compare_interfaces(a,b)


if __name__=='__main__':unittest.main()
