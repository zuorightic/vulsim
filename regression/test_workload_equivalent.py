"""Independent path arithmetic, inversion failure modes and real owner replay."""
from copy import deepcopy
import json
import math
import random
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse.equivalent_period import InversionConfig,invert_window
from experiments.arithmetic_dse.local_budget import TimingDAG
from experiments.arithmetic_dse.workload_equivalent import (
    CharacterizationAdapter,SearchConfig,optimize,request_at,timing_problem)
from experiments.arithmetic_dse.workload_equivalent_run import DEFAULT,read,assert_reference
from experiments.arithmetic_dse.workload_diagnostic import DiagnosticPrices,evaluate
from experiments.arithmetic_dse.workload_v10_replay import old_structure,retarget
from experiments.arithmetic_dse.workload_demand import Graph
from experiments.arithmetic_dse.sampling_time_contract import canonical,sha,derive_contract


class Inversion(unittest.TestCase):
    def test_owner_receipt_hash_survives_JSON_key_conversion(self):
        value={2:{'query':12.5},11:{'query':25.}}
        self.assertEqual(sha(canonical(value)),sha(canonical(json.loads(canonical(value)))))

    def test_direct_clock_is_body_plus_boundary(self):
        r=invert_window(300,lambda t:[t-80],direct=(1,80))
        self.assertEqual(r['status'],'converted');self.assertEqual(r['roots'][0]['tau_ps'],380)

    def test_other_arithmetic_and_multiple_endpoints(self):
        # min(T-40, .8*T-30-(.1*T+20)) = 100 at T=150/.7.
        r=invert_window(100,lambda t:[t-40,.8*t-30-(.1*t+20)])
        root=r['roots'][0]
        self.assertAlmostEqual(root['tau_ps'],150/.7,delta=.02)
        self.assertLess(abs(root['residual_ps']),.05)
        self.assertGreater(root['endpoint_windows_ps'][0],100)

    def test_nonmonotone_retains_distinct_roots(self):
        c=InversionConfig(min_period_ps=1,max_period_ps=100,scan_intervals=64)
        r=invert_window(100,lambda t:[200-(t-25)**2],c)
        self.assertEqual(len(r['roots']),2)
        self.assertAlmostEqual(r['roots'][0]['tau_ps'],15,delta=.01)
        self.assertAlmostEqual(r['roots'][1]['tau_ps'],35,delta=.01)

    def test_plateau_is_bounded_and_explicit(self):
        c=InversionConfig(min_period_ps=1,max_period_ps=100,max_roots=2)
        r=invert_window(20,lambda t:[min(20,t)],c)
        self.assertEqual(len(r['roots']),2)
        self.assertGreater(r['roots_omitted'],0);self.assertFalse(r['exhaustive_root_claim'])

    def test_quantization_must_recheck_residual(self):
        c=InversionConfig(quantum_ps=10,tolerance_ps=.05)
        r=invert_window(101,lambda t:[t-3],c,direct=(1,3))
        self.assertEqual(r['status'],'conversion_uncovered')
        self.assertEqual(r['rejected'][0]['reason'],'window_residual_exceeds_tolerance')

    def test_no_root_is_not_physical_infeasibility(self):
        r=invert_window(100,lambda t:[20])
        self.assertEqual(r['status'],'conversion_uncovered');self.assertFalse(r['exhaustive_root_claim'])
        self.assertEqual(invert_window(0,lambda t:[t])['status'],'nonpositive_budget')

    def test_nonfinite_endpoint_rejected(self):
        with self.assertRaises(ValueError):invert_window(5,lambda t:[math.nan])


def all_paths(children,i):
    if not children[i]:return [([i],0.)]
    return [(nodes+[i],wire+w) for n,w in children[i] for nodes,wire in all_paths(children,n)]


class JointBudget(unittest.TestCase):
    def assert_all_paths(self,problem,budgets):
        d={i:budgets.get(i,problem.fixed.get(i,0.)) for i in problem.children}
        for e in problem.endpoints:
            for nodes,wire in all_paths(problem.children,e['node']):
                self.assertLessEqual(sum(d[n] for n in nodes)+wire,e['deadline_ps']+2e-7)

    def test_serial_reference_delay_is_not_lower_bound(self):
        p=TimingDAG({0:[],1:[(0,2)]},[dict(node=1,deadline_ps=100)],{0,1})
        r=p.allocate({0:800,1:400});b=r['budgets_ps']
        self.assertEqual(r['status'],'allocated');self.assert_all_paths(p,b)
        self.assertAlmostEqual(b[0]/b[1],2,delta=.001)
        self.assertAlmostEqual(sum(b.values()),98,places=5)

    def test_parallel_does_not_divide_by_node_count(self):
        p=TimingDAG({0:[],1:[],2:[(0,0),(1,0)]},[dict(node=2,deadline_ps=100)],{0,1})
        b=p.allocate({0:1,1:1})['budgets_ps']
        self.assertAlmostEqual(b[0],100,places=5);self.assertAlmostEqual(b[1],100,places=5)

    def test_shared_node_obeys_all_captures(self):
        p=TimingDAG({0:[],1:[(0,1)],2:[(0,2)]},
            [dict(node=1,deadline_ps=100),dict(node=2,deadline_ps=60),dict(node=0,deadline_ps=40)],{0,1,2})
        b=p.allocate({0:3,1:1,2:2})['budgets_ps'];self.assert_all_paths(p,b)
        self.assertLessEqual(b[0],40+1e-7)
        bad=dict(b);bad[0]+=10
        self.assertFalse(p.inspect(bad)['feasible'])

    def test_register_cut_and_fixed_logic(self):
        p=TimingDAG({0:[],1:[],2:[(1,3)]},[dict(node=0,deadline_ps=40),dict(node=2,deadline_ps=100)],
                    {0,1},fixed={2:17},groups={0:0,1:1,2:1})
        b=p.allocate({0:100,1:100})['budgets_ps'];self.assert_all_paths(p,b)
        self.assertAlmostEqual(b[0],40,places=5);self.assertAlmostEqual(b[1],80,places=5)

    def test_empty_or_negative_body_window(self):
        self.assertTrue(TimingDAG({0:[]},[dict(node=0,deadline_ps=0)],set()).allocate({})['check']['feasible'])
        p=TimingDAG({0:[]},[dict(node=0,deadline_ps=-1)],{0})
        self.assertEqual(p.allocate({0:1})['status'],'no_positive_joint_window')

    def test_all_paths_on_varied_small_shared_DAGs(self):
        rng=random.Random(168)
        for _ in range(25):
            n=7;children={i:[(j,rng.random()*2) for j in range(i) if rng.random()<.4] for i in range(n)}
            endpoints=[dict(node=i,deadline_ps=30+10*rng.random()) for i in range(n)]
            p=TimingDAG(children,endpoints,set(range(n)))
            b=p.allocate({i:10**rng.uniform(-1,2) for i in range(n)})['budgets_ps']
            self.assert_all_paths(p,b)

    def test_transfer_explores_time_area_trade_beyond_reweighting(self):
        p=TimingDAG({0:[],1:[(0,0)]},[dict(node=1,deadline_ps=100)],{0,1})
        b={0:50.,1:50.}
        # Synthetic response d_v=b_v, area=1000/b0+100/b1. Analytic
        # constrained minimum is b0/b1=sqrt(10), so transfer 1->0 helps.
        proposals=p.proposals(b,b,limit=3)
        improved=[v for reason,v in proposals if reason.startswith('transfer:') and
                  1000/v[0]+100/v[1] < 1000/b[0]+100/b[1]]
        self.assertTrue(improved)
        for v in improved:self.assert_all_paths(p,v)

    def test_cycles_or_orphan_owners_rejected(self):
        with self.assertRaises(ValueError):TimingDAG({0:[(1,0)],1:[(0,0)]},[],{0})
        with self.assertRaises(ValueError):TimingDAG({0:[],1:[]},[dict(node=0,deadline_ps=10)],{1})


class ActualOwners(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle=read(DEFAULT/'diagnostic-model.json')
        cls.contract=read(DEFAULT/'characterization-contract.json')

    def tearDown(self):
        Graph.origins.cache_clear();Graph.roots.cache_clear()

    def inputs(self,structure=0,index=3,target=750):
        members=old_structure('mac32',structure);inv=json.loads(members['inventory.json']);view=inv['views'][index]
        owners=retarget(json.loads(members[view['directory']+'/owners.json']),target)
        state=json.loads(members[view['directory']+'/state.json']);state['features']['sdc_period_ps']=target
        return Graph(json.loads(members['graph.json'])),view,state,owners

    def test_real_serial_model_calls_and_complete_rescore_no_EDA(self):
        graph,view,state,owners=self.inputs();original=deepcopy(owners)
        with patch('subprocess.Popen',side_effect=AssertionError('backend forbidden')):
            prices=DiagnosticPrices(self.bundle)
            r=optimize(graph,view,state,owners,prices,self.contract,search=SearchConfig(rounds=1))
        self.assertEqual(owners,original);self.assertEqual(r['status'],'diagnostic_complete')
        self.assertEqual(r['prediction']['target_ps'],750)
        best,rank=map(int,r['best_variant_id'].split(':'));entry=r['trace'][best]
        variant=next(v for v in entry['variants'] if v['id']==r['best_variant_id'])
        actual={p['node']:p for p in variant['prediction']['owners']}
        for i,c in entry['conversions'].items():
            root=c['roots'][variant['root_indices'][i]]
            self.assertNotEqual(root['tau_ps'],750)
            self.assertEqual(prices.operator_price(root['query'])['delay_ps'],actual[i]['delay_ps'])
            self.assertLess(abs(root['window_ps']-entry['budgets_ps'][i]),.05)
        self.assertEqual(variant['prediction']['S']['projection']['target_ps'],750)
        self.assertEqual(variant['prediction']['S']['projection'],r['baseline']['S']['projection'])
        self.assertEqual(variant['prediction']['S']['controls'],r['baseline']['S']['controls'])
        self.assertNotEqual(variant['prediction']['comb_area_um2'],r['baseline']['comb_area_um2'])
        self.assertNotEqual(variant['prediction']['S']['area_owners_um2'],r['baseline']['S']['area_owners_um2'])

    def test_overrides_cannot_change_shape_carry_consumer_or_coverage(self):
        graph,view,state,owners=self.inputs();prices=DiagnosticPrices(self.bundle)
        q={r['node']:request_at(r['query'],400) for r in owners['operators']}
        for how in ('missing','shape','consumer','abc'):
            bad=deepcopy(q);i=next(iter(bad))
            if how=='missing':del bad[i]
            elif how=='shape':bad[i]['local_context']['producer']['carry']='one'
            elif how=='consumer':bad[i]['local_context']['captures']=[]
            else:bad[i]['flow_context']['abc_target_ps']=750
            with self.assertRaises(ValueError):evaluate(graph,view,state,owners,prices,owner_queries=bad)
        stale=deepcopy(state);stale['features']['sdc_period_ps']=500
        with self.assertRaises(ValueError):evaluate(graph,view,stale,owners,prices,owner_queries=q)

    def test_G_is_unique_and_virtual_consumer_is_explicit(self):
        graph,view,state,owners=self.inputs(structure=2,index=1)
        prices=DiagnosticPrices(self.bundle);base=evaluate(graph,view,state,owners,prices)
        adapter=CharacterizationAdapter(owners,prices,self.contract)
        gcons=[(i,c) for i,cs in adapter.consumers.items() for c in cs if c['kind']=='G']
        self.assertTrue(gcons)
        i,c=gcons[0];result=adapter.convert(i,200)
        self.assertEqual(result['status'],'converted')
        self.assertEqual(result['other_arithmetic'][0]['context'],'diagnostic_virtual_G_consumer')
        self.assertEqual(len([r for r in base['owners'] if r['kind']=='G']),len(owners['G_regions']))
        allmembers={i for g in owners['G_regions'] for i in g['members']}
        self.assertFalse({r['node'] for r in base['owners'] if r['kind']=='operator'} & allmembers)
        problem=timing_problem(graph,view,state,owners,base,self.bundle)
        budget=problem.allocate({i:next(r['delay_ps'] for r in base['owners'] if r['node']==i)
                                 for i in problem.variables})
        self.assertTrue(budget['check']['feasible'])

    def test_frozen_reference_reproduces_actual_default_query(self):
        graph,view,state,owners=self.inputs();base=evaluate(graph,view,state,owners,DiagnosticPrices(self.bundle))
        refs=read(DEFAULT/'baseline-reference.json.gz')
        ref=next(c for row in refs if row['target_ps']==750 for c in row['selection']['candidates']
                 if c['structure']==0 and c['view']==view['directory'])
        assert_reference(base,ref['prediction'])


class SamplingReceipts(unittest.TestCase):
    def test_train_boundary_rederived_without_external_label_access(self):
        receipts=read(DEFAULT/'characterization-train-receipts.json.gz')
        with patch('pathlib.Path.open',side_effect=AssertionError('external data access')):
            contract=derive_contract(receipts)
        self.assertEqual(contract,read(DEFAULT/'characterization-contract.json'))
        self.assertEqual(len(contract['audit']),177)
        self.assertEqual(sum(r['status']=='excluded' for r in contract['audit']),15)
        self.assertTrue(all(r['actual_ABC_ps']==r['target_ps']==r['actual_SDC_ps'] for r in contract['audit']))
        self.assertFalse(contract['virtual_register_area_added'])

    def test_independent_operator_maximum_is_not_paired_with_path_slack(self):
        import base64
        receipts=read(DEFAULT/'characterization-train-receipts.json.gz')
        before=derive_contract(receipts)
        row=next(r for r in receipts['rows'] if r['family']=='Add')
        label=json.loads(base64.b64decode(receipts['raw_labels_base64'][row['label_sha256']]))
        label['operator_delay_ps']+=10000
        label['nodes']['producer']['operator_delay_ps']+=10000
        raw=canonical(label);row['label_sha256']=sha(raw)
        receipts['raw_labels_base64'][sha(raw)]=base64.b64encode(raw).decode()
        after=derive_contract(receipts)
        self.assertEqual(before['families'],after['families'])

    def test_wrong_actual_ABC_is_rejected_even_with_valid_support_hash(self):
        import base64
        receipts=read(DEFAULT/'characterization-train-receipts.json.gz');row=receipts['rows'][0]
        raw=base64.b64decode(receipts['sampling_support_base64'][row['support_sha256']['synth.command.json']])
        data=json.loads(raw)
        data['command']=[s if not s.startswith('ABC_CLOCK_PERIOD_IN_PS=') else 'ABC_CLOCK_PERIOD_IN_PS=1' for s in data['command']]
        changed=canonical(data);row['support_sha256']['synth.command.json']=sha(changed)
        receipts['sampling_support_base64'][sha(changed)]=base64.b64encode(changed).decode()
        with self.assertRaisesRegex(ValueError,'ABC target differs'):derive_contract(receipts)


if __name__=='__main__':unittest.main()
