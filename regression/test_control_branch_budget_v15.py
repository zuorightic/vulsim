import copy
import unittest
from experiments.arithmetic_dse import control_branch_budget_v15 as audit


def fixture():
    instances = {'launch': 'FF', 'buf': 'BUF', 'gate': 'AND', 'data': 'FF', 'native/valid_2': 'FF'}
    library = {
        'FF': dict(sequential=True, buffer_or_inverter=False, pins={'D': {'direction': 'input'}, 'Q': {'direction': 'output'}}),
        'BUF': dict(sequential=False, buffer_or_inverter=True, pins={'A': {'direction': 'input'}, 'Y': {'direction': 'output'}}, timing_arcs=[['A', 'Y']]),
        'AND': dict(sequential=False, buffer_or_inverter=False, pins={'A': {'direction': 'input'}, 'Y': {'direction': 'output'}}, timing_arcs=[['A', 'Y']]),
    }
    pins = ['launch/Q', 'buf/A', 'buf/Y', 'gate/A', 'gate/Y']
    times = [10., 12., 15., 16., 20.]
    nets = {p: dict(net=['n0', 'n0', 'n1', 'n1', 'n2'][i], direction='output' if p.endswith(('/Q', '/Y')) else 'input') for i, p in enumerate(pins)}
    endpoints, paths = {}, {}
    for end, time in [('data/D', 21.), ('native/valid_2/D', 22.)]:
        nets[end] = dict(net='n2', direction='input')
        endpoints[end] = dict(root_arrival_ps=10., end_arrival_ps=time, required_ps=100., slack_ps=100.-time, budget_ps=90., delay_ps=time-10.)
        paths[end] = [dict(pin=p, arrival_ps=t, required_ps=100., cap_fF=.5 if nets[p]['direction']=='input' else 0.) for p,t in zip(pins+[end], times+[time])]
    return dict(start='launch/Q', instances=instances, library=library, nets=nets, endpoints=endpoints, paths=paths, origins={n:[i*10., i*5.] for i,n in enumerate(instances)}, period_ps=100.)


class BranchBudgetTests(unittest.TestCase):
    def test_shared_branch_budget_and_exact_path_accounting(self):
        value = audit.analyze(**fixture())
        self.assertEqual(value['endpoints'], 2)
        self.assertEqual(value['first_nonbuffer_branches'], 1)
        self.assertEqual(value['branches'][0]['endpoint_count'], 2)
        self.assertEqual(value['branches'][0]['tightest_budget_ps'], 84.)
        self.assertEqual(value['valid_R_ps'], 22.)
        self.assertEqual(value['checked_cell_arcs'], 4)
        self.assertEqual(value['checked_wires'], 6)
        self.assertFalse(value['usable_as_online_price_feature'])

    def test_escaped_origin_aliasing_is_loader_responsibility(self):
        case=fixture()
        case['origins']['data\\'] = case['origins'].pop('data')
        with self.assertRaises(ValueError): audit.analyze(**case)

    def test_disconnected_arc_timing_boundary_and_geometry_mutations(self):
        for kind in ('wire', 'arc', 'timing', 'boundary', 'geometry', 'cap'):
            case=copy.deepcopy(fixture())
            if kind=='wire': case['nets']['buf/A']['net']='different'
            elif kind=='arc': case['library']['BUF']['timing_arcs']=[]
            elif kind=='timing': case['endpoints']['data/D']['budget_ps']+=1
            elif kind=='boundary': case['paths'].pop('data/D')
            elif kind=='geometry': case['origins']['gate'][0]=float('nan')
            else: case['paths']['data/D'][1]['cap_fF']=-1
            with self.assertRaises(ValueError): audit.analyze(**case)

if __name__=='__main__': unittest.main()
