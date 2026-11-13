"""Prospective control-source queries, with hold and propagation kept explicit.

This is a software successor contract. It contains no mapped cell counts,
measured capacitance, source IDs or boundary prices.
"""
import math

VERSION='semantic-control-source-queries-v1'


def queries(input_widths,stage_data_bits,service_mode,target):
    if (not input_widths or any(type(w) is not int or w<=0 for w in input_widths)
            or not stage_data_bits or any(type(w) is not int or w<0 for w in stage_data_bits)
            or service_mode not in (0,1,2) or not math.isfinite(target) or target<=0):
        raise ValueError('explicit prospective control structure and numerical T required')
    total=sum(input_widths);depth=len(stage_data_bits);held=service_mode!=2
    result=[]
    def append(path,source,stage,data_sinks,valid_sinks,self_hold,capture_hold,enable_load=0):
        outgoing=data_sinks+valid_sinks
        result.append(dict(path_class=path,control_source=source,stage=stage,
            features=dict(one=1.,target_ps=float(target),log2_target=math.log2(target/500.),clock_pressure=1500./target,
                enabled_data_sinks=float(data_sinks),valid_propagation_sinks=float(valid_sinks),self_hold_sinks=float(self_hold),
                total_logical_sinks=float(outgoing+self_hold),log2_logical_sinks=math.log2(outgoing+self_hold+1.),
                launch_is_service=float(source=='service_valid'),launch_has_hold=float(self_hold>0),capture_has_hold=float(capture_hold),
                capture_enable_logical_sinks=float(enable_load),log2_capture_enable_load=math.log2(enable_load+1.)),
            mapped_capacitance_qualified=False,price_qualification_granted=False))
    # Input iv is the data input of the service valid FF; we_iv enables it.
    service_enable=total+1 if service_mode==1 else 1 if held else 0
    append('input_valid','port_iv',0,0,1,0,held,service_enable)
    for stage,data in enumerate(stage_data_bits):
        source='service_valid' if stage==0 else 'native_valid'
        for path in ('native_valid','native_enable'):
            append(path,source,stage,data,1,int(stage==0 and held),False)
    append('external_valid','native_valid',depth,0,1,0,False)
    return result


def bank_queries(spec,target):
    stages=[sum(s['variable_bits'] for s in spec['slots'] if s['stage']==i)
            for i in range(1,spec['depth']+1)]
    return queries([r['width'] for r in spec['roots']],stages,spec['service_mode'],target)


def materialized_queries(state_query,input_widths,service_mode,target):
    if not state_query.get('materialized_checked'):raise ValueError('actual materialized state required')
    depth=state_query['internal_stages'];stages=[0]*depth
    for slot in state_query['slots']:
        if slot['valid'] or slot['external_capture']:continue
        if not 1<=slot['stage']<=depth or slot['enable_stage']!=slot['stage']-1:raise ValueError('unregistered native enable semantics')
        stages[slot['stage']-1]+=slot['variable_bits']
    return dict(version=VERSION,graph_sha256=state_query['graph_sha256'],layout_sha256=state_query['layout_sha256'],
                controls=queries(input_widths,stages,service_mode,target),actual_arithmetic_S_qualified=False)
