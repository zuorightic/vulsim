"""Separate native-valid launch response from service-valid response.

The source kind is part of the prospective register/control contract, not an
instance identifier. One common numerical function uses source-kind/load
interactions. It does not use a bank ID or actual mapped driver/capacitance.
"""
from .state_control_response import features as previous_features

VERSION='per-source-control-response-features-v2-native-launch'


def features(control_query):
    f=previous_features(control_query)
    native=float(control_query['control_source']=='native_valid')
    f.update(native_launch=native,native_logical_load=native*f['log2_logical_sinks'],native_pressure_logical_load=native*f['pressure_logical_sinks'])
    return f
