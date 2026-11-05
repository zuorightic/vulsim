"""Constant outputs stay in the full proof; incomplete nonconstant maps fail."""
import copy
from pathlib import Path
import tempfile
import unittest

from experiments.arithmetic_dse.model_m2_aig import full_map,read_aig


class CompleteAIG(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.aig=self.root/'a.aig';self.mapping=self.root/'a.map'
        self.aig.write_bytes(b'aig 1 1 0 2 0\n2\n0\ni0 a\no0 y\no1 zero\nc\n')
        self.mapping.write_text('input 0 0 a\noutput 0 0 y\n')
        self.flat={'ports':{'a':{'direction':'input','bits':[2]},'y':{'direction':'output','bits':[2]},
                            'zero':{'direction':'output','bits':['0']}},'cells':{}}

    def test_constant_output_omitted_only_from_short_map(self):
        full,constant=full_map(self.aig,self.mapping,self.flat,1,2)
        self.assertEqual(full[-1],['output','1','0','zero'])
        self.assertEqual(constant,[{'index':1,'symbol':'zero','literal':0}])

    def test_nonconstant_omission_rejected(self):
        self.mapping.write_text('input 0 0 a\n')
        with self.assertRaisesRegex(ValueError,'nonconstant boundary'):full_map(self.aig,self.mapping,self.flat,1,2)

    def test_missing_input_rejected(self):
        self.mapping.write_text('output 0 0 y\n')
        with self.assertRaisesRegex(ValueError,'nonconstant boundary'):full_map(self.aig,self.mapping,self.flat,1,2)

    def test_constant_value_disagreement_rejected(self):
        self.aig.write_bytes(self.aig.read_bytes().replace(b'2\n0\ni0',b'2\n1\ni0'))
        with self.assertRaisesRegex(ValueError,'constant AIG output differs'):full_map(self.aig,self.mapping,self.flat,1,2)

    def test_constant_symbol_omission_rejected(self):
        self.aig.write_bytes(self.aig.read_bytes().replace(b'o1 zero\n',b''))
        with self.assertRaisesRegex(ValueError,'incomplete AIG symbol'):full_map(self.aig,self.mapping,self.flat,1,2)

    def test_wrong_constant_name_rejected(self):
        self.aig.write_bytes(self.aig.read_bytes().replace(b'o1 zero',b'o1 other'))
        with self.assertRaisesRegex(ValueError,'unmatched AIG symbol'):full_map(self.aig,self.mapping,self.flat,1,2)

    def test_undefined_port_rejected(self):
        self.flat['ports']['zero']['bits']=['x']
        with self.assertRaisesRegex(ValueError,'undefined AIG port'):full_map(self.aig,self.mapping,self.flat,1,2)

    def test_unknown_cell_rejected(self):
        self.flat['cells']['mystery']={'type':'blackbox','connections':{}}
        with self.assertRaisesRegex(ValueError,'noncombinational AIG cell'):full_map(self.aig,self.mapping,self.flat,1,2)


if __name__=='__main__':unittest.main()
