"""Frozen v10 runtime functions; extracted without numerical edits from nangate45_samples.py."""
import hashlib

import json

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())
