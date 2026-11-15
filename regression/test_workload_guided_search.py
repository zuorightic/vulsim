"""Independent scheduling legality, source roles, and native rejection guards."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from experiments.arithmetic_dse.workload_guided_search import canonical_move,BINARY
from experiments.arithmetic_dse.workload_reuse_validation import (
    DEFAULT,query_v2,wide_spec,error_metrics,quantile)
from experiments.arithmetic_dse.workload_equivalent_run import read,write
from experiments.arithmetic_dse.sampling_time_contract import ROOT,sha
from experiments.arithmetic_dse import wide_arithmetic as arithmetic


class ProposalLegality(unittest.TestCase):
    def setUp(self):
        # Input -> mul -> transparent wire -> add -> output, plus constant ov.
        self.raw=dict(nodes=[dict(id=i,operation=op,constant=constant,
            operands=[dict(node=n) for n in parents]) for i,(op,constant,parents) in enumerate([
                ('input',False,[]),('mul',False,[0]),('wire',False,[1]),
                ('add',False,[2]),('wire',False,[3]),('wire',True,[])])])
        self.units=[dict(members=[i],fixed=i in (0,4,5),constant=i==5) for i in range(6)]

    def test_constant_output_remains_fixed_and_transparent_successor_follows(self):
        result,status=canonical_move(self.raw,self.units,[0,0,0,2,2,2],1,1,3)
        self.assertEqual(status,'legal_proposal');self.assertEqual(result,[0,1,1,2,2,2])

    def test_consumer_before_new_producer_is_rejected(self):
        result,status=canonical_move(self.raw,self.units,[0,0,0,0,2,2],1,1,3)
        self.assertIsNone(result);self.assertEqual(status,'dependency_violation')

    def test_new_stage_outside_L_rejected(self):
        result,status=canonical_move(self.raw,self.units,[0,0,0,2,2,2],1,-1,3)
        self.assertIsNone(result);self.assertEqual(status,'stage_out_of_range')

    def test_indivisible_members_move_together(self):
        units=[self.units[0],dict(members=[1,2],fixed=False,constant=False),*self.units[3:]]
        stages,_=canonical_move(self.raw,units,[0,0,0,2,2,2],1,1,3)
        self.assertEqual(stages[1:3],[1,1])
        with self.assertRaises(ValueError):canonical_move(self.raw,units,[0,0,1,2,2,2],1,1,3)


class ValidationStatistics(unittest.TestCase):
    def test_sources_equal_weight_not_number_of_clock_variants(self):
        rows=[dict(source='a',err=.1)]*20+[dict(source='b',err=.3)]
        m=error_metrics(rows,'err');self.assertAlmostEqual(m['source_median_APE'],.2)
        self.assertFalse(m['gate_pass']);self.assertEqual(m['sources'],2)

    def test_quantile_interpolates_and_empty_is_explicit(self):
        self.assertAlmostEqual(quantile([.1,.2,.3],.95),.29)
        self.assertIsNone(quantile([],.95))

    def test_old_modulo_query_preserves_maps_masks_and_arithmetic(self):
        old=dict(operation='add',lhs_width=8,rhs_width=16,result_width=17,
            lhs_zero_hex='0x80',lhs_one_hex='0x1',rhs_zero_hex='0x0',rhs_one_hex='0x0',carry='zero',capture_banks=2)
        spec=wide_spec(old)
        for a,b in [(0,0),(255,65535),(7,21)]:
            self.assertEqual(arithmetic.evaluate(spec,a,b),((a&0x7f)|1)+b)
        q=dict(version='arithmetic-operator-query-v1',local_context=dict(producer=old,
            captures=[dict(banks=2,result_bit_map=[0,'0',1])],consumers=[dict(spec=old,
                bindings=[dict(operand_index=1,result_bit_map=['0',0,1])])]),flow_context={})
        updated=query_v2(q)
        self.assertEqual(updated['local_context']['captures'],q['local_context']['captures'])
        self.assertEqual(updated['local_context']['consumers'][0]['bindings'][0]['result_bit_map'],['0',0,1])
        self.assertNotIn('role',q['local_context']['consumers'][0]['bindings'][0])


@unittest.skipUnless(BINARY.exists(),'native compiler not built')
class NativeExplicitGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The probe is produced by this step's bounded scheduler, not a new
        # manually invented RTL implementation.
        cls.probe=DEFAULT/'search/native/T500-mul8-limb0-beam'
        cls.temporary=None
        if not cls.probe.exists():
            from experiments.arithmetic_dse.workload_steps45_package import artifact_files
            files=artifact_files(DEFAULT,[])
            cls.temporary=tempfile.TemporaryDirectory(prefix='vulsim-native-probe-')
            cls.probe=Path(cls.temporary.name)
            for name in ('graph.json','inventory.json','scheduling-units.json'):
                (cls.probe/name).write_bytes(files['native/T500-mul8-limb0-beam/'+name])
        cls.graph=read(cls.probe/'graph.json');cls.units=read(cls.probe/'scheduling-units.json')['units']
        cls.placement=read(cls.probe/'inventory.json')['views'][0]['placement']

    @classmethod
    def tearDownClass(cls):
        if cls.temporary:cls.temporary.cleanup()

    def run_document(self,mutate):
        with tempfile.TemporaryDirectory(prefix='vulsim-explicit-guard-') as tmp:
            root=Path(tmp);doc=dict(version='workload-explicit-schedules-v1',L=3,T_clk_ps=500,
                graph_export_sha256=sha((self.probe/'graph.json').read_bytes()),placements=[self.placement.copy()])
            mutate(doc);write(root/'schedule.json',doc)
            sentinel=root/'no-eda';sentinel.mkdir()
            for name in ('yosys','abc','yosys-abc','openroad','opensta','sta'):
                p=sentinel/name;p.write_text('#!/bin/sh\nexit 97\n');p.chmod(0o755)
            env=dict(os.environ,PATH=str(sentinel)+os.pathsep+os.environ['PATH'])
            result=subprocess.run([str(BINARY),str(ROOT),str(DEFAULT/'source/request.json'),'3','0','4','100000',
                str(root/'native'),'8','500','owned',str(DEFAULT/'model-bindings.json'),str(root/'schedule.json')],
                env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=120)
            return result.returncode,result.stdout

    def test_legal_explicit_placement_accepted(self):
        code,text=self.run_document(lambda d:None);self.assertEqual(code,0,text)

    def test_graph_and_target_identity_required(self):
        for key,value in [('graph_export_sha256','0'*64),('T_clk_ps',750),('L',4)]:
            with self.subTest(key=key):
                code,text=self.run_document(lambda d:d.update({key:value}));self.assertNotEqual(code,0,text)

    def test_duplicate_width_and_range_rejected(self):
        mutations=[lambda d:d['placements'].append(d['placements'][0].copy()),
            lambda d:d['placements'][0].pop(),lambda d:d['placements'][0].__setitem__(0,3)]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                code,text=self.run_document(mutate);self.assertNotEqual(code,0,text)

    def test_fixed_ports_and_split_groups_rejected(self):
        output=next(p['nodes'][0] for p in self.graph['ports'] if p['name']=='ov')
        group=next(u['members'] for u in self.units if len(u['members'])>1)
        for node in (output,group[0]):
            with self.subTest(node=node):
                code,text=self.run_document(lambda d:d['placements'][0].__setitem__(node,(self.placement[node]+1)%3))
                self.assertNotEqual(code,0,text)


if __name__=='__main__':unittest.main()
