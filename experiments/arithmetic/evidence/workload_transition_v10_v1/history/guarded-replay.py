import builtins
import io
import json
from pathlib import Path
import sys
from unittest.mock import patch
sys.path.insert(0, str(Path.cwd()))
from experiments.arithmetic_dse.workload_v10_replay import replay
opens = (builtins.open, io.open)
blocked = []
def guarded(original):
    def wrapped(file, *args, **kwargs):
        if not isinstance(file, int):
            name = str(Path(file).absolute())
            if name.startswith('/home/zyrv/vulsim-artifacts/'):
                blocked.append(name)
                raise AssertionError('external artifact access forbidden: ' + name)
        return original(file, *args, **kwargs)
    return wrapped
with patch('builtins.open', guarded(opens[0])), patch('io.open', guarded(opens[1])), patch('subprocess.Popen', side_effect=AssertionError('replay subprocess forbidden')):
    result = replay()
result['external_artifact_guard'] = True
result['external_artifact_attempts'] = len(blocked)
print(json.dumps(result, indent=2))
