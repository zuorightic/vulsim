"""Preserve the frozen evaluator's exact Boolean-wire rule at N4 adapters."""
from . import flow_structure_features as circuits


def is_wire(query):
    spec=query['local_context']['producer']
    if spec['operation'] not in ('add','adc'):return False
    circuit,outputs=circuits.operator_circuit(spec)
    return circuit.work(outputs)['work']==0


def zero_price():
    return dict(delay_ps=0.,area_um2=0.,qualified=False,full_D_ready=False,
        source='frozen exact Boolean constant/wire certificate; no log response queried',flags=['constant_folded_Boolean_wire'])
