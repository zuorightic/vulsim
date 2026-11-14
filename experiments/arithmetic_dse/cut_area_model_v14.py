"""Pure consumption of sealed train-only cut-cover area experiments."""
import math

from . import centered_response as response
from . import flow_structure_features as circuits
from . import prospective_cut_cover_v14 as cut

VERSION = 'cut-reference-area-train-diagnostic-v14'


def work(query, family, table, *, witnesses=False):
    if family == 'Add':
        circuit, outputs = circuits.operator_circuit(query['local_context']['producer'])
    elif family == 'G':
        circuit, outputs, _ = circuits.reduction_circuit(query)
    else:
        raise ValueError('cut-area experiment supports Add and G only')
    mapped = cut.cover(circuit, outputs, table, witnesses=witnesses)
    if witnesses:
        cut.verify(circuit, outputs, mapped, table)
    return mapped


def features(base, mapped):
    if mapped['version'] != cut.VERSION or mapped['area'] <= 0:
        raise ValueError('positive bounded-cut reference required')
    return dict(base, cut_area=mapped['area'], log2_cut_cells=math.log2(1+mapped['cells']),
        cut_shared_root_fraction=mapped['shared_roots']/max(1, mapped['mapped_roots']),
        cut_overlap_gate_fraction=mapped['overlapping_interior_gates']/max(1, mapped['primitive_gates']))


def predict(model, values, *, diagnostic=False):
    if not diagnostic or model['version'] != VERSION:
        raise ValueError('v14 requires explicit train diagnostics')
    reference = values['cut_area']
    synth = reference * response.predict(model['synth'], values)
    second = response.predict(model['second'], values)
    grt = reference * second if model['form'] == 'direct' else synth * second
    ratio = grt/synth
    if not all(math.isfinite(v) and v > 0 for v in (reference, synth, grt, ratio)):
        raise ValueError('nonpositive cut-reference area estimate')
    return dict(predicted_grt_area_um2=grt, predicted_synth_area_um2=synth,
        predicted_grt_synth_ratio=ratio, qualified_for_public_D=False)
