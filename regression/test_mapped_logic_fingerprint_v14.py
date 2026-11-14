import copy
import unittest

from experiments.arithmetic_dse.mapped_logic_fingerprint_v14 import fingerprint


def fixture(buffer_name='buf'):
    library = {
        'FF': dict(sequential=True, buffer_or_inverter=False, data_pins=['D'],
            pins={'Q': dict(direction='output', function='IQ'), 'D': dict(direction='input', function=None)}),
        'BUF': dict(sequential=False, buffer_or_inverter=True, data_pins=[],
            pins={'Y': dict(direction='output', function='A'), 'A': dict(direction='input', function=None)},
            timing_arcs=[['A', 'Y']]),
        'AND': dict(sequential=False, buffer_or_inverter=False, data_pins=[],
            pins={'Y': dict(direction='output', function='A*B'), 'A': dict(direction='input', function=None),
                'B': dict(direction='input', function=None)}, timing_arcs=[['A', 'Y'], ['B', 'Y']])}
    instances = {'launch': 'FF', 'capture': 'FF', buffer_name: 'BUF', 'gate': 'AND'}
    nets = {
        'launch/Q': dict(direction='output', net='control'),
        buffer_name+'/A': dict(direction='input', net='control'),
        buffer_name+'/Y': dict(direction='output', net='buffered'),
        'gate/A': dict(direction='input', net='buffered'),
        'gate/B': dict(direction='input', net='reset'),
        'gate/Y': dict(direction='output', net='next'),
        'capture/D': dict(direction='input', net='next')}
    return instances, library, nets


class FingerprintTests(unittest.TestCase):
    def test_buffer_names_and_count_do_not_change_sink_expression(self):
        a = fingerprint('launch/Q', *fixture())
        instances, library, nets = fixture('renamed')
        instances['second'] = 'BUF'
        nets['second/A'] = dict(direction='input', net='buffered')
        nets['second/Y'] = dict(direction='output', net='twice')
        nets['gate/A']['net'] = 'twice'
        b = fingerprint('launch/Q', instances, library, nets)
        self.assertEqual(a['sinks'], b['sinks'])
        self.assertEqual(b['buffer_inverter_cells'], a['buffer_inverter_cells']+1)

    def test_logic_and_sink_mutations_are_visible(self):
        reference = fingerprint('launch/Q', *fixture())
        instances, library, nets = fixture()
        library['AND']['pins']['Y']['function'] = 'A+B'
        changed = fingerprint('launch/Q', instances, library, nets)
        self.assertNotEqual(reference['sinks'], changed['sinks'])
        nets['extra/D'] = copy.deepcopy(nets['capture/D'])
        instances['extra'] = 'FF'
        changed = fingerprint('launch/Q', instances, library, nets)
        self.assertEqual(changed['sink_count'], 2)

    def test_ambiguous_driver_and_missing_arc_rejected(self):
        for mode in ('driver', 'arc'):
            instances, library, nets = fixture()
            if mode == 'driver':
                instances['duplicate'] = 'FF'
                nets['duplicate/Q'] = dict(direction='output', net='control')
            else:
                library['AND']['timing_arcs'] = []
            with self.assertRaises(ValueError):
                fingerprint('launch/Q', instances, library, nets)


if __name__ == '__main__':
    unittest.main()
