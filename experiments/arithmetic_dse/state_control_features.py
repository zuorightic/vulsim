"""Logical control fanout from retained bank/state structure, before mapping.

Each domain lists its enabled data bits. Counts are logical proxies; mapping
may distribute them among inverters, muxes and buffers. No electrical or
arithmetic qualification is implied by successful extraction.
"""
import math
from .common_state_features import bank_features as previous_bank_features

VERSION = 'state-control-load-features-v2'


def control_loads(input_widths, stage_enabled_data_bits, external_data_bits,
                  service_mode=0):
    if (not input_widths or any(type(w) is not int or w <= 0 for w in input_widths)
            or not stage_enabled_data_bits
            or any(type(w) is not int or w < 0 for w in stage_enabled_data_bits)
            or type(external_data_bits) is not int or external_data_bits < 0
            or service_mode not in (0, 1, 2)):
        raise ValueError('explicit state control domains required')
    # Launch valid enables stage1 data and propagates to the first native valid.
    launch_valid = stage_enabled_data_bits[0] + 1
    # Each native valid drives the following stage enable and next valid, or
    # just the final unconditional external valid FF.
    native_valid = [w + 1 for w in stage_enabled_data_bits[1:]] + [1]
    service = [sum(input_widths) + 1] if service_mode == 1 else list(input_widths)
    if service_mode == 0:
        service.append(1)
    return dict(service_enable_max_load=float(max(service)),
                service_enable_domains=float(len(service)),
                launch_valid_logical_load=float(launch_valid),
                native_valid_max_logical_load=float(max(native_valid)),
                native_valid_total_logical_load=float(sum(native_valid)),
                native_enable_max_logical_load=float(max(stage_enabled_data_bits)),
                native_enable_domains=float(len(stage_enabled_data_bits)),
                control_log2_launch_load=math.log2(launch_valid + 1.),
                control_log2_native_valid_load=math.log2(max(native_valid) + 1.),
                external_valid_logical_load=1.,
                root_reset_logical_load=float(sum(input_widths) + 1 +
                                             sum(stage_enabled_data_bits) +
                                             len(stage_enabled_data_bits) + external_data_bits + 1))


def bank_features(spec, target):
    f = previous_bank_features(spec, target)
    stages = [sum(s['variable_bits'] for s in spec['slots'] if s['stage'] == k)
              for k in range(1, spec['depth'] + 1)]
    loads = control_loads([r['width'] for r in spec['roots']], stages,
                         sum(spec['words'][i]['variable_bits'] for i in spec['external_words']),
                         spec['service_mode'])
    for owner, values in f.items():
        values.update(loads)
        values['pressure_native_valid_load'] = loads['native_valid_max_logical_load'] * values['clock_pressure']
        values['pressure_service_enable_load'] = loads['service_enable_max_load'] * values['clock_pressure']
    return f


def query_control_loads(state_query, input_widths, service_mode=0):
    """The same proxy from materialized native state, with explicit domains."""
    if not state_query.get('materialized_checked'):
        raise ValueError('materialized state query required')
    depth = state_query['internal_stages']
    if depth < 1:
        raise ValueError('explicit native control stages required')
    slots = state_query['slots']
    stages = [0] * depth
    external = 0
    for slot in slots:
        if slot['valid']:
            continue
        if slot['external_capture']:
            external += slot['variable_bits']
            continue
        stage = slot['stage']
        if not 1 <= stage <= depth or slot['enable_stage'] != stage - 1:
            raise ValueError('unsupported native enable semantics')
        stages[stage - 1] += slot['variable_bits']
    return dict(features=control_loads(input_widths, stages, external, service_mode),
                stage_enabled_data_bits=stages, external_data_bits=external,
                graph_sha256=state_query['graph_sha256'],
                layout_sha256=state_query['layout_sha256'],
                mapped_capacitance_qualified=False, actual_arithmetic_S_qualified=False)
