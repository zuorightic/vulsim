"""Frozen v10 runtime functions; extracted without numerical edits from platforms.py."""
import hashlib

import json

from pathlib import Path

PROFILES = Path(__file__).resolve().parents[2]/'vullib/models/autopipe/profiles'


def profile(platform):
    if platform not in ('asap7','nangate45','sky130hd','gf180'):
        raise ValueError(f'unsupported platform: {platform}')
    path=PROFILES/(platform+'.json')
    data=json.loads(path.read_text())
    if data['platform'] != platform or data['schema'] != 'arithmetic-platform-v1':
        raise ValueError('platform profile identity mismatch')
    data['profile_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    return data
