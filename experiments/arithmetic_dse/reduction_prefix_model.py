"""Independently qualified intrinsic G prices for registered reduction regions.

G owns the fused region's internal arithmetic cells/wires and replaces its
internal Add prices. State, external edges and shared repair remain outside.
"""
import hashlib
import json
import math
from pathlib import Path
from . import reduction_prefix_features as area,reduction_merge_features as delay
from . import conditional_function_support_v2 as support
from .platforms import profile

VERSION='asap7-G-prefix-functions-v1'


def load(folder):
    folder=Path(folder);bundle=json.loads((folder/'model.json').read_text())
    if bundle['version']!=VERSION or bundle['quality_status']!='passed_independent':raise ValueError('G package lacks independent qualification')
    for name in ('parameters','evaluation'):
        item=bundle[name];path=folder/item['path']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('G package evidence/parameter mismatch')
        bundle['_'+name]=json.loads(path.read_text())
    if bundle['_evaluation']['status']!='passed_independent':raise ValueError('G independent test failed')
    for filename,digest in bundle['feature_source_sha256'].items():
        path=Path(__file__).with_name(filename)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('G feature implementation changed')
    return bundle


def predict(bundle,width,terms,target,*,capture_banks=1,consumer_count=0,launch_type='register'):
    try:
        if bundle['version']!=VERSION or bundle['quality_status']!='passed_independent':raise ValueError('G function is not independently qualified')
        if bundle['profile_sha256']!=profile('asap7')['profile_sha256']:raise ValueError('G platform profile mismatch')
        if type(capture_banks) is not int or capture_banks!=1 or type(consumer_count) is not int or consumer_count!=0 or launch_type!='register':raise ValueError('unqualified G boundary/load context')
        m=bundle['_parameters'];af=area.features(width,terms,target);df=delay.features(width,terms,target)
        verdict=support.check(m['support'],af,target)
        if verdict['status']!='structurally_supported':return verdict
        def evaluate(fit,features):
            names=fit['features'];coeff=fit['coefficients']
            if len(names)!=len(coeff) or len(set(names))!=len(names):raise ValueError('G parameter/feature mismatch')
            value=fit.get('intercept',0.)+sum(features[n]*c for n,c in zip(names,coeff,strict=True))
            if not math.isfinite(value) or value<=0:raise ValueError('invalid G intrinsic price')
            return value
        return dict(status='covered',operator_delay_ps=evaluate(m['delay'],df),comb_area_um2=evaluate(m['area'],af),
                    replaces_internal_Add_costs=True,additional_G_residual_delay_ps=0.,additional_G_residual_area_um2=0.,
                    S_or_full_stage_qualification=False,full_D_ready=False)
    except (KeyError,ValueError,TypeError,OverflowError) as e:return dict(status='cost_uncovered',reason=str(e))
