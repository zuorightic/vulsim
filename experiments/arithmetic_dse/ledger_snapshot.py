"""Portable compressed accounting; a missing live ledger never resets history."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile

VERSION = 'physical-backend-ledger-snapshot-v1'


def metadata_path(snapshot):
    return Path(snapshot).with_suffix('').with_suffix('.meta.json')


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _validate(state, policy, checkpoint):
    from .budget import checkpoint_data, digest, usage
    if (state['policy_sha256'] != digest(policy)
            or state['checkpoint_sha256'] != digest(checkpoint)):
        raise ValueError('published ledger policy/checkpoint identity mismatch')
    previous = checkpoint_data(checkpoint)['entries']
    if state['entries'][:len(previous)] != previous:
        raise ValueError('published ledger lost checkpoint history')
    if state['usage'] != usage(state['entries']):
        raise ValueError('published ledger usage does not match its entries')
    if state['usage']['pending'] or any(j['status'] != 'released' for j in state.get('jobs', [])):
        raise ValueError('publish only settled backend accounting')


def load_snapshot(snapshot, policy, checkpoint):
    snapshot = Path(snapshot)
    metadata = json.loads(metadata_path(snapshot).read_text())
    packed = snapshot.read_bytes()
    if metadata['version'] != VERSION or _sha(packed) != metadata['compressed_sha256']:
        raise ValueError('published ledger compressed snapshot identity mismatch')
    raw = gzip.decompress(packed)
    if _sha(raw) != metadata['uncompressed_sha256']:
        raise ValueError('published ledger uncompressed identity mismatch')
    state = json.loads(raw)
    _validate(state, policy, checkpoint)
    if len(state['entries']) != metadata['entry_count'] or state['usage'] != metadata['usage']:
        raise ValueError('published ledger metadata differs from accounting')
    return state


def _atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def export_snapshot(ledger, snapshot):
    # The transaction takes the same lock as all accounting mutations.
    with ledger._transaction() as state:
        _validate(state, ledger.policy, ledger.checkpoint)
        raw = (json.dumps(state, ensure_ascii=False, indent=2)+'\n').encode()
        packed = gzip.compress(raw, mtime=0)
        metadata = dict(version=VERSION, compressed_sha256=_sha(packed),
                        uncompressed_sha256=_sha(raw), uncompressed_bytes=len(raw),
                        compressed_bytes=len(packed), entry_count=len(state['entries']),
                        jobs=len(state.get('jobs', [])), usage=state['usage'],
                        policy_sha256=state['policy_sha256'], checkpoint_sha256=state['checkpoint_sha256'])
        _atomic(snapshot, packed)
        _atomic(metadata_path(snapshot), (json.dumps(metadata, indent=2)+'\n').encode())
    return metadata


def main():
    from .budget import Ledger, SNAPSHOT, POLICY, CHECKPOINT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('export', 'verify'))
    args = parser.parse_args()
    if args.action == 'export':
        result = export_snapshot(Ledger(), SNAPSHOT)
        print(json.dumps(result, indent=2))
    else:
        state = load_snapshot(SNAPSHOT, POLICY, CHECKPOINT)
        print(json.dumps(dict(status='passed', entries=len(state['entries']), usage=state['usage']), indent=2))


if __name__ == '__main__':
    main()
