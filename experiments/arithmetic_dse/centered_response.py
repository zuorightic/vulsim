"""Stable, portable inference for centered numerical response functions.

Training removes constant columns within each fold. Inference retains the
training centers and scales, so export does not create a large raw intercept
whose cancellation depends on the order of evaluation. No fitting or backend
operation occurs here.
"""
import math

VERSION = 'centered-numerical-response-v1'


def predict(model, features):
    if model['version'] != VERSION:
        raise ValueError('centered response identity mismatch')
    names = model['features']
    arrays = [model[k] for k in ('centers', 'scales', 'coefficients')]
    if (len(names) != len(set(names)) or any(len(a) != len(names) for a in arrays)
            or model['link'] not in ('linear', 'positive_log_linear')):
        raise ValueError('centered response dimensions or link')
    terms = [model['intercept']]
    for name, center, scale, coefficient in zip(names, *arrays, strict=True):
        value = features[name]
        if (not all(math.isfinite(x) for x in (value, center, scale, coefficient))
                or scale <= 0):
            raise ValueError('finite centered features and positive scales required')
        terms.append(((value - center) / scale) * coefficient)
    latent = math.fsum(terms)
    result = math.exp(latent) if model['link'] == 'positive_log_linear' else latent
    if not math.isfinite(result):
        raise ValueError('nonfinite centered response')
    return result
