"""Pure multiplication of predicted mapping area and physical area ratio.

The two positive functions are trained offline on separate saved quantities.
Neither function receives a measured area or another model's fitted value.
This experimental consumer grants no component or public-D qualification.
"""
import math
from . import centered_response as response

VERSION = 'factorized-mapping-physical-area-v12'


def predict(entry, features):
    if entry['version'] != VERSION or entry['price_status'] != 'train_diagnostic_only':
        raise ValueError('explicit factorized train diagnostic required')
    mapping = response.predict(entry['mapping'],features)*features[entry['mapping_reference']]
    ratio = response.predict(entry['physical_ratio'],features)
    area = mapping*ratio
    if any(not math.isfinite(value) or value<=0 for value in (mapping,ratio,area)):
        raise ValueError('nonpositive factorized area')
    return dict(predicted_synth_area_um2=mapping,predicted_grt_synth_ratio=ratio,
        predicted_grt_area_um2=area,qualified_for_public_D=False)
