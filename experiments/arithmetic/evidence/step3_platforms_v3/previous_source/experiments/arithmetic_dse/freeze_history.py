"""Resolve an explicitly superseded source against its immutable snapshot.

Changed current source must itself match the successor freeze. This does not
turn an old acceptance report into evidence for the new implementation.
"""
import hashlib
import json
import importlib.util
from pathlib import Path

def source_location(root, parent, relative, expected):
    root=Path(root)
    digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    if (root/relative).is_file() and digest(root/relative)==expected:return root/relative
    sdc_revision=root/'experiments/arithmetic/backend_freeze_v6.json'
    if sdc_revision.exists():
        current=json.loads(sdc_revision.read_text())
        active=root/relative
        bound=active.is_file() and current['files_sha256'].get(relative)==digest(active)
        retired=not active.exists() and relative in current.get('retired_active_paths',[])
        if current['historical_freezes'].get(parent)==digest(root/parent) and (bound or retired):
            for source_root in current['historical_source_roots']:
                snapshot=root/source_root/relative
                if snapshot.is_file() and digest(snapshot)==expected:return snapshot
    platform_revision=root/'experiments/arithmetic/backend_freeze_v5.json'
    if platform_revision.exists():
        current=json.loads(platform_revision.read_text())
        active=root/relative
        bound=(active.is_file() and current['files_sha256'].get(relative)==digest(active))
        retired=(not active.exists() and relative in current.get('retired_active_paths',[]))
        if current['historical_freezes'].get(parent)==digest(root/parent) and (bound or retired):
            for source_root in current['historical_source_roots']:
                snapshot=root/source_root/relative
                if snapshot.is_file() and digest(snapshot)==expected:return snapshot
    revised=root/'experiments/arithmetic/step2_freeze_v4.json'
    if revised.exists():
        current=json.loads(revised.read_text())
        if ((root/relative).is_file() and current['historical_freezes'].get(parent)==digest(root/parent)
            and current['files_sha256'].get(relative)==digest(root/relative)):
            for source_root in current['historical_source_roots']:
                snapshot=root/source_root/relative
                if snapshot.is_file() and digest(snapshot)==expected:return snapshot
    successor=root/'experiments/arithmetic/mul_split_freeze_v1.json'
    if not successor.exists():raise ValueError(f'changed source has no versioned successor: {relative}')
    freeze=json.loads(successor.read_text())
    if freeze['parents_sha256'].get(parent)!=digest(root/parent):
        raise ValueError('historical freeze is not bound by the successor')
    if freeze['files_sha256'].get(relative)!=digest(root/relative):
        raise ValueError(f'current successor source mismatch: {relative}')
    snapshot=root/freeze['historical_source_snapshots'][parent]/relative
    if digest(snapshot)!=expected:raise ValueError(f'historical source mismatch: {relative}')
    return snapshot


def historical_case_manifest(root):
    """Old evidence consumes its frozen data, never the active 43-case API."""
    root=Path(root)
    parent='experiments/arithmetic/freeze_v3.json'
    relative='experiments/arithmetic/cases_v1.json'
    freeze=json.loads((root/parent).read_text())
    path=source_location(root,parent,relative,freeze['files_sha256'][relative])
    return json.loads(path.read_text())


def historical_budget(root):
    """Historical forecasts execute their own frozen nine-case formulas only."""
    root=Path(root)
    parent='experiments/arithmetic/backend_freeze_v4.json'
    relative='experiments/arithmetic_dse/budget.py'
    expected=json.loads((root/parent).read_text())['files_sha256'][relative]
    source=source_location(root,parent,relative,expected)
    spec=importlib.util.spec_from_file_location('_vulsim_historical_budget_'+expected[:12],source)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def historical_stage_metrics(root):
    """Reparse old reports with the exact parser bound by backend freeze v4."""
    root=Path(root)
    parent='experiments/arithmetic/backend_freeze_v4.json'
    relative='experiments/arithmetic_dse/backend.py'
    expected=json.loads((root/parent).read_text())['files_sha256'][relative]
    source=source_location(root,parent,relative,expected)
    name=__package__+'._frozen_backend_'+expected[:12]
    spec=importlib.util.spec_from_file_location(name,source)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.stage_metrics
