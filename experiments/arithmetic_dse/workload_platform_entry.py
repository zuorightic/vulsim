"""Explicit platform binding around the frozen D evaluator and native exporter.

The compiler's graph, schedules, state, arithmetic ownership and RTL stay intact.
Native export has no price model. Its historical ASAP7 metadata is rebound by
this adapter, with both identities recorded; stale native price reports are not
accepted by this interface. Offline response payloads use the frozen function
schema. Training and backend execution are deliberately absent from this module.
"""
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import subprocess
from unittest.mock import patch

from . import prospective_cell_cover as cells
from . import workload_diagnostic as diagnostic
from .workload_final_prices import CachedPrices
from .workload_tight_equivalent import optimize
from .platforms import profile

SCHEMA = 'frozen-D-platform-package-v1'
ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


class PlatformPrices(CachedPrices):
    def __init__(self, bundle, selected, cover_area):
        # The function implementation is inherited verbatim. Package hashes,
        # platform, scope, and readiness replace the legacy hardcoded model SHA.
        if bundle['version'] != diagnostic.VERSION or bundle['profile_sha256'] != selected['profile_sha256']:
            raise ValueError('response schema/profile mismatch')
        self.bundle = bundle
        self.selected = selected
        self.cover_area = cover_area
        self.v10 = bundle['v10']
        centered = self.v10['inherited_flow']['inherited_centered']
        if centered['operator_profile_sha256'] != selected['profile_sha256']:
            raise ValueError('embedded operator profile mismatch')
        self.operator = centered['semantic_operator_model']
        if self.operator['profile_sha256'] != selected['profile_sha256']:
            raise ValueError('embedded semantic response profile mismatch')
        self.cache = {}
        self.geometry_cache = {}
        self.cover_function = diagnostic.operator_cover_features
        self.cover_cache = {}
        self.cover_hits = 0

    def operator_price(self, query):
        flow = query['flow_context']
        if flow['target_platform'] != self.selected['platform'] or flow['profile_sha256'] != self.selected['profile_sha256']:
            raise ValueError('query platform/profile mismatch')
        if flow['evaluation_stage'] != 'grt' or flow['target_period_ps'] != flow['abc_target_ps']:
            raise ValueError('equivalent sampling stage/ABC contract mismatch')
        with self.context():
            return super().operator_price(query)

    @contextmanager
    def context(self):
        # Each selector is a single process, as in the frozen caller. This also
        # binds functional-cover and virtual-consumer area, not just operators.
        with patch.object(cells, 'AREA', self.cover_area):
            yield


def load_package(path, platform):
    path = Path(path).resolve()
    doc = read(path)
    selected = profile(platform)
    if (doc['schema'] != SCHEMA or doc['platform'] != platform or
            doc['profile_sha256'] != selected['profile_sha256'] or doc['evaluation_stage'] != 'grt'):
        raise ValueError('model package platform/profile/stage mismatch')
    if doc['status'] != 'ready':
        raise ValueError('platform model pending offline calibration: ' + doc['status'])
    if (doc['pricing'] != 'offline_shared_functions' or doc['online_backend_feedback'] or
            doc['application_PPA_used'] or doc['exact_lookup']):
        raise ValueError('offline shared-function contract required')
    payloads = {}
    for name in ('response', 'characterization', 'cell_cover'):
        item = doc[name]
        member = (path.parent / item['path']).resolve()
        if sha(member) != item['sha256']:
            raise ValueError('package payload hash mismatch: ' + name)
        payloads[name] = read(member)
    bundle, contract, cell = (payloads[n] for n in ('response', 'characterization', 'cell_cover'))
    if contract['profile_sha256'] != selected['profile_sha256']:
        raise ValueError('sampling contract profile mismatch')
    if contract['application_PPA_used'] or contract['operator_response_refitted']:
        raise ValueError('equivalent-T requires immutable offline response during selection')
    if cell['profile_sha256'] != selected['profile_sha256'] or set(cell['area_um2']) != set(cells.AREA):
        raise ValueError('complete platform cell-cover binding required')
    if not all(math.isfinite(v) and v > 0 for v in cell['area_um2'].values()):
        raise ValueError('invalid cell-cover areas')
    return PlatformRuntime(doc, PlatformPrices(bundle, selected, cell['area_um2']), contract)


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


def native_export(binary, source_request, out, *, platform, L, limb, block, target_ps, placements=None):
    """Run the frozen frontend with empty models, then bind prospective queries.

    The empty-model provider reports missing prices; final D uses PlatformRuntime.
    No existing export, binary, source request, or model file is modified.
    """
    out = Path(out).resolve()
    if out.exists() or out.is_relative_to(ROOT):
        raise ValueError('new external output required')
    out.parent.mkdir(parents=True, exist_ok=True)
    command = [str(binary), str(ROOT), str(source_request), str(L), str(limb), '1', '200000',
               str(out), str(block), str(target_ps), 'owned']
    if placements is not None:
        empty = out.with_suffix('.empty-models.json')
        write(empty, {})
        command.extend([str(empty), str(placements)])
    with out.with_suffix('.log').open('w') as log:
        subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT, timeout=600)
    inventory = read(out / 'inventory.json')
    original = inventory['profile_sha256']
    receipts = []
    for view in inventory['views']:
        folder = out / view['directory']
        owner_path = folder / 'owners.json'
        before = sha(owner_path)
        write(owner_path, rebind_owners(read(owner_path), platform))
        # Native reports are explicitly unavailable; never relabel ASAP7 prices.
        for name in ('costs-public.json', 'costs-diagnostic.json'):
            report = folder / name
            write(report, dict(status='cost_uncovered', reason='export_only_empty_model',
                platform=platform, model_selection_performed=False, candidate_PPA_calls=0))
        receipts.append(dict(view=view['directory'], original_owners_sha256=before,
            rebound_owners_sha256=sha(owner_path), rtl_sha256=sha(folder/'workload.sv'),
            state_sha256=sha(folder/'state.json')))
    inventory['profile_sha256'] = profile(platform)['profile_sha256']
    write(out / 'inventory.json', inventory)
    write(out / 'platform-entry.json', dict(version='frozen-D-native-platform-adapter-v1',
        platform=platform, profile_sha256=inventory['profile_sha256'], native_export_profile_sha256=original,
        compiler_sha256=sha(binary), source_request_sha256=sha(source_request),
        graph_sha256=sha(out/'graph.json'), views=receipts,
        graph_state_RTL_unchanged_by_binding=True, empty_native_price_models=True,
        candidate_PPA_calls=0, model_selection_performed=False))
    return out
