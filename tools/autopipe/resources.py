"""Load versioned inference resources without training or a physical backend."""
import hashlib
import json
from pathlib import Path
from statistics import median

from .workload_final_prices import CachedPrices
from . import workload_diagnostic

ROOT = Path(__file__).resolve().parents[2]
MODELS = ROOT / 'vullib/models/autopipe'
EXAMPLES = ROOT / 'example/autopipe'


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_models():
    manifest = read(MODELS / 'manifest.json')
    if manifest['schema'] != 'autopipe-frozen-v10-resources-v1':
        raise ValueError('unsupported model manifest')
    for relative, expected in manifest['files_sha256'].items():
        path = (MODELS / relative).resolve()
        if not path.is_relative_to(MODELS.resolve()) or sha(path) != expected:
            raise ValueError('frozen model resource changed: ' + relative)
    return manifest


def asap7_characterization():
    contract = read(MODELS / 'asap7/characterization.json')
    families = contract['families']
    # The diagnostic Sub/Compare shell uses the pooled train-source median.
    # Each source contributes once, even if present in multiple families.
    source_boundaries = {}
    for family in families.values():
        for source, boundary in family['source_medians_ps'].items():
            source_boundaries.setdefault(source, []).append(boundary)
    pooled = median(median(boundaries) for boundaries in source_boundaries.values())
    for family in ('Sub', 'Compare'):
        families[family] = dict(H_char_ps=pooled, alpha=contract['direct_capture_alpha'],
                                sources=len(source_boundaries), qualified=False,
                                boundary_role='train-source-pooled cross-family extrapolation; no family-specific shell observations')
    return contract


class Asap7Runtime:
    def __init__(self):
        self.prices = CachedPrices(read(MODELS / 'asap7/response.json'))
        self.contract = asap7_characterization()

    def evaluate(self, graph, view, state, owners, **kwargs):
        return workload_diagnostic.evaluate(graph, view, state, owners, self.prices, **kwargs)

    def optimize(self, graph, view, state, owners, **kwargs):
        from .workload_tight_equivalent import optimize
        return optimize(graph, view, state, owners, self.prices, self.contract, **kwargs)


def runtime(platform):
    verify_models()
    if platform == 'asap7':
        return Asap7Runtime()
    if platform == 'nangate45':
        from .nangate45_pipeline_runtime import load_package
        return load_package(MODELS / 'nangate45/package.json')
    raise ValueError('supported models: asap7, nangate45')
