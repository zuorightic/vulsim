"""Frozen v10 runtime functions; extracted without numerical edits from workload_platform_entry.py."""
from copy import deepcopy

from . import workload_diagnostic as diagnostic

from .workload_tight_equivalent import optimize

from .platforms import profile

class PlatformRuntime:
    def __init__(self, manifest, prices, contract):
        self.manifest, self.prices, self.contract = manifest, prices, contract

    def check(self, owners):
        if owners['profile_sha256'] != self.prices.selected['profile_sha256']:
            raise ValueError('owner/G platform profile mismatch')
        for row in owners['operators']:
            flow = row['query']['flow_context']
            if flow['target_platform'] != self.manifest['platform'] or flow['profile_sha256'] != owners['profile_sha256']:
                raise ValueError('operator and owner platform differ')

    def evaluate(self, graph, view, state, owners, **kwargs):
        self.check(owners)
        with self.prices.context():
            return diagnostic.evaluate(graph, view, state, owners, self.prices, **kwargs)

    def optimize(self, graph, view, state, owners, **kwargs):
        self.check(owners)
        with self.prices.context():
            return optimize(graph, view, state, owners, self.prices, self.contract, **kwargs)


def rebind_owners(owners, platform):
    """Rebind only exporter metadata, never prices, graph, state, or requests T."""
    selected = profile(platform)
    out = deepcopy(owners)
    out['profile_sha256'] = selected['profile_sha256']
    def visit(value):
        if isinstance(value, dict):
            if 'flow_context' in value:
                value['flow_context'].update(target_platform=platform, profile_sha256=selected['profile_sha256'])
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
    visit(out)
    return out
