"""One numerical G function across narrow and wide word-compression geometry."""
from . import reduction_structural_graph as geometry
from . import conditional_function_support_v2 as support, wide_function_model as linear

VERSION = 'common-word-reduction-functions-v2'


def predict(model, query, *, diagnostic=False):
    try:
        if model['version'] != VERSION or model['feature_version'] != geometry.VERSION:
            raise ValueError('word-G model identity')
        if not diagnostic:
            raise ValueError('word-G candidate lacks public qualification')
        if (query.get('launch_type', 'register') != 'register'
                or query.get('capture_banks', 1) != 1 or query.get('consumer_count', 0) != 0):
            raise ValueError('unqualified word-G boundary')
        T = query['target_ps']
        f = geometry.features(query['output_bits'], query['terms'], T)
        verdict = support.check(model['support'], f['area'], T)
        if verdict['status'] != 'structurally_supported':
            return verdict
        delay = linear.linear(model['delay'], f['delay'])
        area = linear.linear(model['area'], f['area'])
        if delay <= 0 or area <= 0:
            raise ValueError('nonpositive word-G price')
        return dict(status='diagnostic_estimate', operator_delay_ps=delay,
                    comb_area_um2=area, qualified_for_public_D=False)
    except (KeyError, ValueError, TypeError, OverflowError) as error:
        return dict(status='cost_uncovered', reason=str(error))
