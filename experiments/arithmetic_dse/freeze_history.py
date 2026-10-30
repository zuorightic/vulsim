"""Resolve an explicitly superseded source against its immutable snapshot.

Changed current source must itself match the successor freeze. This does not
turn an old acceptance report into evidence for the new implementation.
"""
import hashlib
import json
from pathlib import Path

def source_location(root, parent, relative, expected):
    root=Path(root)
    digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    if (root/relative).is_file() and digest(root/relative)==expected:return root/relative
    revised=root/'experiments/arithmetic/step2_freeze_v4.json'
    if revised.exists():
        current=json.loads(revised.read_text())
        if (current['historical_freezes'].get(parent)==digest(root/parent)
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
