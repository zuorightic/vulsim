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
    if digest(root/relative)==expected:return root/relative
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
