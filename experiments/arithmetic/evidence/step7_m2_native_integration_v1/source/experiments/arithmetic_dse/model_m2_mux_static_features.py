"""Mux-only pre-mapping context ABI with explicit semantic boundaries."""
import math
from .model_features import FEATURES as BASE_FEATURES,infer as numeric_infer
from .model_m2_fit_v4 import predict as old_predict,target_key,width_key

VERSION='arithmetic-mux-static-features-v1'
EXTRA=('context_operation_count','context_dynamic_mux_count','context_constant_mux_count','context_boolean_count',
       'context_launch_bits','context_capture_bits','context_result_bits','selector_fanout_bits')
FEATURES=BASE_FEATURES+EXTRA
ALLOWED=('mux','mux_zero','mux_one','mux_ones','eq_zero','or')


def descriptor(labels):
    """Reconstruct a logical cut from registered semantics, not source names.

    IDs identify wires/captures solely to prove uniqueness. Their spelling and
    the order of operations do not enter a numeric feature.
    """
    operations=[]
    for s in labels:
        op=s['operation'];w=s['lhs_width'];sid=s['id']
        if op not in ALLOWED:raise ValueError('unqualified operation in Mux context')
        operands=[{'id':sid+':a','width':w,'role':'data'}]
        if op in ('mux','or'):operands.append({'id':sid+':b','width':w,'role':'data'})
        if op.startswith('mux'):operands.append({'id':sid+':select','width':1,'role':'select'})
        operations.append({'id':sid,'operation':op,'result_width':s['result_width'],'operands':operands,'capture_banks':s['fanout']})
    return {'version':'arithmetic-mux-static-cut-v1','operations':operations}


def context_features(cut,query):
    if not isinstance(cut,dict) or cut.get('version')!='arithmetic-mux-static-cut-v1':raise ValueError('missing or unknown Mux static context')
    ops=cut.get('operations')
    if not isinstance(ops,list) or not ops or len(ops)>6:raise ValueError('unqualified Mux context cardinality')
    if len({o['id'] for o in ops})!=len(ops):raise ValueError('duplicate Mux context operation')
    def positive(value):
        if type(value) is not int or not 1<=value<=2048:raise ValueError('invalid static context count')
        return value
    seen=set();launch=capture=result=dynamic=constant=boolean=0;target=None;types=[];widths=set();bank_counts=set()
    for o in ops:
        op=o['operation'];bits=positive(o['result_width']);banks=positive(o['capture_banks'])
        if op not in ALLOWED or banks>3:raise ValueError('outside qualified control context')
        operands=o['operands'];data=[v for v in operands if v['role']=='data'];select=[v for v in operands if v['role']=='select']
        if len(data)!=(2 if op in ('mux','or') else 1) or len(select)!=(1 if op.startswith('mux') else 0) or len(operands)!=len(data)+len(select):
            raise ValueError('Mux context semantic operand mismatch')
        for v in operands:
            if v['id'] in seen:raise ValueError('shared inputs/select are outside this Mux context qualification')
            seen.add(v['id']);launch+=positive(v['width'])
        if select and select[0]['width']!=1:raise ValueError('Mux selector must be one bit')
        if len({v['width'] for v in data})!=1 or (bits!=1 if op=='eq_zero' else bits!=data[0]['width']):
            raise ValueError('unqualified control shape')
        widths.add(data[0]['width']);bank_counts.add(banks)
        types.append('mux_one' if op=='mux_ones' and data[0]['width']==1 else op)
        if any(v['id'] in {x['id'] for x in ops} for v in operands):raise ValueError('connected context not qualified')
        result+=bits;capture+=banks*bits;dynamic+=op=='mux';constant+=op in ('mux_zero','mux_one','mux_ones');boolean+=op in ('eq_zero','or')
        if o['id']==query:target=o
    if target is None or target['operation']!='mux':raise ValueError('query is not a dynamic Mux member')
    if launch>640 or capture>2048:raise ValueError('static context outside capacity')
    expected=['mux','mux_zero','mux_one','mux_ones','eq_zero','or']
    if widths=={1}:expected=['mux_one' if op=='mux_ones' else op for op in expected]
    if len(widths)!=1 or len(bank_counts)!=1 or not ((dynamic==len(ops) and 2<=dynamic<=4) or sorted(types)==sorted(expected)):
        raise ValueError('unqualified parallel control composition')
    return dict(zip(EXTRA,(len(ops),dynamic,constant,boolean,launch,capture,result,target['result_width'])))


def features(base,cut,query):
    if any(k not in base for k in BASE_FEATURES):raise ValueError('incomplete base Mux features')
    extra=context_features(cut,query);values={**base,**extra}
    if any(isinstance(values[k],bool) or not isinstance(values[k],(int,float)) or not math.isfinite(values[k]) for k in FEATURES):
        raise ValueError('nonfinite Mux static feature')
    return values


def predict(model,row,quantity):
    if quantity=='area' or model.get('kind')=='legacy12':return old_predict(model['model'] if model.get('kind')=='legacy12' else model,row,quantity)
    entry=model
    if model['kind']=='exact_width_slices':entry=model['slices'][width_key(row)]
    elif model['kind']=='exact_width_target_slices':entry=model['slices'][target_key(row)]
    values=row.get('static_features')
    if not isinstance(values,dict) or any(k not in values for k in FEATURES):raise ValueError('Mux query lacks explicit static context features')
    value=numeric_infer(entry['predictor'],values,feature_names=FEATURES)
    scale=entry.get('delay_scale',1.);margin=entry.get('delay_margin_ps',0.)
    if not math.isfinite(scale) or not math.isfinite(margin) or scale<1 or margin<0:raise ValueError('invalid Mux calibration')
    return value*scale+margin
