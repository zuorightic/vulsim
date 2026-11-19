"""Frozen v10 runtime functions; extracted without numerical edits from sampling_time_contract.py."""
import hashlib

import json

def sha(raw):return hashlib.sha256(raw).hexdigest()


def canonical(value):
    # JSON object keys are strings on disk. Normalize BEFORE sorting so an
    # owner-keyed receipt hashes identically before and after JSON round-trip.
    def normalize(v):
        if isinstance(v,dict):return {str(k):normalize(x) for k,x in v.items()}
        if isinstance(v,(tuple,list)):return [normalize(x) for x in v]
        return v
    return json.dumps(normalize(value),sort_keys=True,separators=(',',':'),allow_nan=False).encode()
