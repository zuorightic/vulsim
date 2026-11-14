"""W1 application contracts. Registration never grants model or data admission."""
import argparse
import json
from pathlib import Path

DEFAULT = Path(__file__).parent / 'configs/general_workloads_v1.json'
CASE_IDS = {'mac32', 'add512', 'mul128', 'dot16', 'horner64', 'barrett64',
            'karatsuba256', 'montgomery256', 'ntt8x64'}


def load(path=DEFAULT):
    doc = json.loads(Path(path).read_text())
    if doc['version'] != 'nine-workload-contracts-v1' or doc['II'] != 1:
        raise ValueError('wrong workload contract or II')
    cases = doc['cases']
    if len(cases) != 9 or {c['id'] for c in cases} != CASE_IDS:
        raise ValueError('exactly nine distinct application contracts required')
    if doc['new_model_sources']:
        raise ValueError('model sources require separate immutable role admission')
    for case in cases:
        targets = case['formal_targets']
        if targets is not None:
            if not targets or len(targets) > 16:
                raise ValueError('finite nonempty target list required')
            for row in targets:
                if set(row) != {'T_ps', 'L'} or type(row['T_ps']) not in (int, float) or not 0 < row['T_ps'] < 1e9 or type(row['L']) is not int or not 1 <= row['L'] <= 256:
                    raise ValueError('invalid formal target')
        if case['semantic_status'].startswith('confirmed') and case['semantics'] is None:
            raise ValueError('confirmed semantics missing')
        if case['semantic_status'] == 'pending' and not case['unresolved']:
            raise ValueError('pending semantics need explicit decisions')
    mac = next(c for c in cases if c['id'] == 'mac32')
    if mac['formal_targets'] != [dict(T_ps=t, L=3) for t in (500, 750, 1000)]:
        raise ValueError('confirmed MAC32 targets changed')
    return doc


def readiness(doc):
    return dict(version='nine-workload-readiness-v1', cases=[dict(
        id=c['id'], semantics=c['semantic_status'], formal_targets=c['formal_targets'],
        ready_for_application_freeze=(c['semantic_status'].startswith('confirmed')
                                      and c['formal_targets'] is not None and not c['unresolved']),
        unresolved=c['unresolved'], requirements=c['requirements'],
        software_source=c['software_source']) for c in doc['cases']],
        full_D_ready=False, new_model_sources_admitted=0, new_EDA_calls=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contracts', type=Path, default=DEFAULT)
    args = parser.parse_args()
    print(json.dumps(readiness(load(args.contracts)), ensure_ascii=False, indent=2))
