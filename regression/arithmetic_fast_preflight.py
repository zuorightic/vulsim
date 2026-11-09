"""Independent invariants for source-list P0: provenance, geometry and refusal."""
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.arithmetic_dse import model_fast_preflight as m


def verify(folder):
    index = m.read(folder / 'native/index.json'); cases = []
    for c in index['cases']:
        rows = []
        for entry in c['candidates']:
            path = folder / 'native' / entry['file']
            if m.sha(path) != entry['sha256']: raise ValueError('native export identity changed')
            d = m.read(path)
            movable = sum(not u['fixed'] and not u['constant'] for u in d['units'])
            if d['unit_assignment_trials'] != d['L'] ** movable:
                raise ValueError('assignment enumeration differs from independent Cartesian count')
            rows.append(d)
        cases.append((c['case'], rows))
    primitive, state = m.read(ROOT / m.PRIMITIVES), m.read(ROOT / m.STATE)
    catalog = m.read(folder / 'fitting-feature-catalog.json'); expected = m.read(folder / 'requirements.json')
    replay = m.summarize(cases, primitive, state, catalog)
    if any(expected[k] != v for k, v in replay.items()): raise ValueError('static audit does not reproduce')
    renamed = m.summarize([('unrelated_source_name_' + str(i), rows) for i, (_, rows) in enumerate(cases)], primitive, state, catalog)
    for field in ('operator_shapes', 'load_contexts', 'stage_feature_contexts', 'totals'):
        if renamed[field] != replay[field]: raise ValueError('case identity leaked into semantic requirements')
    if any(e['PPA_calls'] for _, rows in cases for e in rows): raise ValueError('PPA in static audit')
    guards = []
    def reject(name, function):
        try: function()
        except (ValueError, KeyError): guards.append(name)
        else: raise ValueError('guard accepted: ' + name)
    bad = copy.deepcopy(catalog); bad[0]['split'] = 'test'
    reject('consumed_independent_feature_metadata', lambda: m.summarize(cases, primitive, state, bad))
    bad_cases = copy.deepcopy(cases); bad_cases[0][1][0]['exhaustive_unit_assignments_checked'] = False
    reject('partial_search_claimed_complete', lambda: m.summarize(bad_cases, primitive, state, catalog))
    bad_cases = copy.deepcopy(cases); bad_cases[0][1][0]['views'][0]['state']['query']['features']['state_bits'] += 1
    reject('state_count_without_actual_slots', lambda: m.summarize(bad_cases, primitive, state, catalog))
    bad_cases = copy.deepcopy(cases); bad_cases[0][1][0]['PPA_calls'] = 1
    reject('physical_measurement_in_static_scope', lambda: m.summarize(bad_cases, primitive, state, catalog))
    example = cases[0][1][0]; nodes = {n['id']: copy.deepcopy(n) for n in example['nodes']}
    node = next(n for n in nodes.values() if n['operation'] == 'mul' and not n['constant'])
    original = m.operator_shape(node, nodes); data_node = nodes[node['operands'][0]['node']]
    mask = m.bits(data_node['known_zero_hex']) | 1; data_node['known_zero_hex'] = [format(mask & ((1 << 64) - 1), 'x'), format(mask >> 64, 'x')]
    data_node['known_one_hex'] = ['0']
    patterned = m.operator_shape(node, nodes)
    if m.key(original) == m.key(patterned) or 'known_operand_bit_pattern' not in m.reuse_conditions(patterned, primitive)['blockers']:
        raise ValueError('shift/zero geometry ignored by reusable shape')
    data_node['known_one_hex'] = ['1']
    reject('contradictory_known_bits', lambda: m.operator_shape(node, nodes))
    invalid = copy.deepcopy(node); invalid['operands'][0]['billing_width'] = invalid['operands'][0]['width'] + 1
    reject('invalid_operand_provenance_width', lambda: m.operator_shape(invalid, nodes))
    quarter = max((row for _, rows in cases for row in rows), key=lambda row: len(row['nodes']))
    qnodes = {n['id']: n for n in quarter['nodes']}; demanded = m.demanded_bits(qnodes, quarter['ports'])
    if any(n['width'] > 64 and n['operation'] in ('add', 'addcarry') for n in qnodes.values()):
        if any(demanded[n['id']].bit_length() > 64 for n in qnodes.values() if n['operation'] in ('mul', 'add', 'addcarry')):
            raise ValueError('unobserved high carries charged as full-width result')
    bad_nodes = copy.deepcopy(qnodes); wiring = next(n for n in bad_nodes.values() if n.get('wiring_kind') == 'concat');wiring['width'] += 1
    reject('incorrect_concat_bit_demand', lambda: m.demanded_bits(bad_nodes, quarter['ports']))
    config = m.read(m.CONFIG)
    if (config['selection']['epsilon_numerator'], config['selection']['epsilon_denominator']) != (5, 100):
        raise ValueError('user-confirmed speed band changed')
    if config['physical_admission_allowed'] or config['independent_test_allowed']:
        raise ValueError('P0 config unexpectedly authorizes physical or independent tests')
    for case in replay['cases']:
        for row in case['candidates']:
            if row['state_owner_feature_ranges']['external_state/enable_domains'] != [0, 0] or row['state_owner_features_qualified']:
                raise ValueError('legacy gated external projection promoted to public state qualification')
    proof = dict(status='passed', structural_replay=True, case_renaming_invariant=True,
        known_bit_geometry_affects_shape_and_reuse=True, rejections=guards,
        native_candidate_count=sum(len(rows) for _, rows in cases),
        complete_unit_assignment_trials=replay['totals']['assignment_trials'],
        PPA_calls=0, independent_labels_read=False)
    m.write(folder / 'guards.json', proof); print(json.dumps(proof), flush=True)


def legacy(folder, previous):
    current = m.read(folder / 'legacy-native/index.json'); old = m.read(previous / 'index.json')
    if (current['exhaustive_unit_assignments_checked'] or current['candidate_count'] != old['candidate_count']
            or current['view_count'] != old['view_count']): raise ValueError('old bounded source-list semantics changed')
    for actual, expected in zip(current['cases'], old['cases'], strict=True):
        for field in ('case', 'production_C_candidate_order', 'production_C_selected'):
            if actual[field] != expected[field]: raise ValueError('old production C selection changed')
        a = [(r['id'], r['shape_sha256'], r['views']) for r in actual['candidates']]
        b = [(r['id'], r['shape_sha256'], r['views']) for r in expected['candidates']]
        if a != b: raise ValueError('old candidate graph/order/view scope changed')
    proof = dict(status='passed', legacy_cases=len(current['cases']), candidates=current['candidate_count'],
                 legal_views=current['view_count'], ordered_graphs_and_C_selection_unchanged=True, PPA_calls=0)
    m.write(folder / 'legacy-parity.json', proof);print(json.dumps(proof), flush=True)


def isolated(evidence):
    with tempfile.TemporaryDirectory(prefix='fast-preflight-isolated-') as td:
        temp = Path(td); local = temp / 'evidence'; source = temp / 'source';shutil.copytree(evidence, local)
        for name, item in json.loads(m.gzip.decompress((local / 'source-pool.json.gz').read_bytes())).items():
            if Path(name).is_absolute() or '..' in Path(name).parts: raise ValueError('unsafe frozen source path')
            target = source / name;target.parent.mkdir(parents=True, exist_ok=True);target.write_text(item['text'])
        code = '''import builtins,io,os,runpy,subprocess,sys
from pathlib import Path
source,evidence,original=sys.argv[1:]
def guard(fn):
 def checked(path,*a,**kw):
  if isinstance(path,(str,bytes,os.PathLike)) and Path(path).resolve().is_relative_to(original):raise RuntimeError('original project read forbidden')
  return fn(path,*a,**kw)
 return checked
builtins.open=guard(builtins.open);io.open=guard(io.open)
def deny(*a,**kw):raise RuntimeError('replay subprocess forbidden')
subprocess.Popen=deny
sys.path.insert(0,source);sys.argv=['frozen','verify','--out',evidence]
runpy.run_module('experiments.arithmetic_dse.model_fast_preflight',run_name='__main__')
'''
        env = os.environ.copy();env.update(PATH='', PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONPATH', None)
        cmd = [sys.executable, '-B', '-c', code, str(source), str(local), str(ROOT)]
        result = subprocess.run(cmd, cwd=temp, env=env, capture_output=True, text=True)
        if result.returncode: raise ValueError('isolated preflight replay failed: ' + result.stderr[-2000:])
        for name in ('replay-inputs.json.gz', 'source-pool.json.gz', 'requirements.json'):
            path = local / name;original = path.read_bytes();changed = bytearray(original);changed[len(changed) // 2] ^= 1;path.write_bytes(changed)
            result = subprocess.run(cmd, cwd=temp, env=env, capture_output=True, text=True);path.write_bytes(original)
            if result.returncode == 0 or 'preflight evidence identity mismatch' not in result.stderr:
                raise ValueError('isolated tamper guard did not reject: ' + name)
        print(json.dumps(dict(status='passed', original_project_build_ledger_forbidden=True, PATH_empty=True,
            replay_subprocess_forbidden=True, semantic_replay=True, tamper_rejections=3, PPA_calls=0)), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser();p.add_argument('--out', type=Path);p.add_argument('--legacy', type=Path);p.add_argument('--isolated-evidence', type=Path);a = p.parse_args()
    if a.isolated_evidence: isolated(a.isolated_evidence)
    elif not a.out: p.error('--out required')
    elif a.legacy: legacy(a.out, a.legacy)
    else: verify(a.out)
