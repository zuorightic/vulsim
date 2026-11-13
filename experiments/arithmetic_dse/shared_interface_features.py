"""Shared clock/physical/interface descriptors with exclusive ownership.

The functional footprint must come from semantic primitives and prospective
node/S functions. A measured functional area is not accepted as an argument.
"""
import math

VERSION = 'shared-interface-control-features-v2'


def features(owner_features, control, predicted_functional_area_um2):
    owners=('input_service','native_state','external_state')
    if set(owner_features)!=set(owners):
        raise ValueError('three exclusive state owners required')
    if (not math.isfinite(predicted_functional_area_um2)
            or predicted_functional_area_um2 < 0):
        raise ValueError('prospective semantic functional footprint required')
    total=sum(owner_features[o]['data_bits']+owner_features[o]['valid_bits'] for o in owners)
    return dict(one=1.,total_FF_bits=float(total),
                input_data_bits=float(owner_features['input_service']['data_bits']),
                reset_one_bits=float(sum(owner_features[o]['reset_one_bits'] for o in owners)),
                predicted_functional_area_um2=float(predicted_functional_area_um2),
                service_enable_domains=control['service_enable_domains'],
                service_enable_max_load=control['service_enable_max_load'],
                log2_reset_load=math.log2(control['root_reset_logical_load']+1.),
                clock_pressure=owner_features['input_service']['clock_pressure'])
