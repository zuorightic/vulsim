"""Generic source-list audit for reusable fast operator, state and stage models.

P0 consumes actual native graphs and fitting-side feature metadata only. It does
not qualify prices, fit parameters, read independent labels or launch EDA.
"""
import argparse
from collections import Counter, defaultdict
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
CONFIG = Path(__file__).with_name('configs') / 'model_fast_prototype_v1.json'
PRIMITIVES = 'experiments/arithmetic/evidence/step7_m2_mux_static_v1/asap7-primitives.json'
STATE = 'experiments/arithmetic/evidence/step7_general_state_v1/asap7-general-state.json'
FITTING = 'build/step7-m2-models-20261104/fitting-data-v2.json'
VERSION = 'arithmetic-fast-preflight-v3'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def key(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def bits(words):
    return sum(int(v, 16) << (64 * i) for i, v in enumerate(words))


def operand_shape(operand, nodes):
    width = operand['width']; billing = operand.get('billing_width', width)
    if not 0 < billing <= width:
        raise ValueError('invalid semantic/declared operand width')
    mask = (1 << billing) - 1
    if operand['kind'] == 'symbol':
        n = nodes[operand['node']]
        if n['width'] != width:
            raise ValueError('operand/reference width differs')
        zero, one = bits(n['known_zero_hex']) & mask, bits(n['known_one_hex']) & mask
        if zero & one:
            raise ValueError('contradictory known bits')
        literal = None
    elif operand['kind'] == 'literal':
        literal = bits(operand['limbs_hex']) & mask
        zero, one = mask ^ literal, literal
    else:
        raise ValueError('arithmetic operand must be typed symbol or literal')
    return dict(declared_width=width, billing_width=billing, known_zero_hex=hex(zero),
                known_one_hex=hex(one), known_zero_bits=zero.bit_count(), known_one_bits=one.bit_count(),
                literal_hex=None if literal is None else hex(literal), signed=operand['signed'])


def demanded_bits(nodes, ports):
    """Backward bit demand for the registered unsigned scalar operator subset.

    Addition/multiplication low output bits never depend on higher input bits.
    Slice and concat are exact wiring, so unused high carries are not sampled
    as independently observed full-width results.
    """
    demand = {n: 0 for n in nodes}; pending = []
    def add(at, mask):
        mask &= (1 << nodes[at]['width']) - 1
        if mask & ~demand[at]: demand[at] |= mask;pending.append(at)
    for port in ports:
        if port['direction'] == 'output':
            for at in port['nodes']: add(at, (1 << nodes[at]['width']) - 1)
    while pending:
        at = pending.pop();n = nodes[at];mask = demand[at];op = n['operation'];args = n['operands']
        if n['constant'] or op == 'input': continue
        def feed(index, value):
            a = args[index]
            if a['kind'] == 'symbol': add(a['node'], value)
        if op in ('mul', 'add', 'addcarry'):
            low = (1 << mask.bit_length()) - 1
            for index in range(len(args)): feed(index, low)
        elif op == 'wire':
            kind = n.get('wiring_kind')
            if kind == 'concat':
                offset = 0
                for index in reversed(range(len(args))):
                    feed(index, (mask >> offset) & ((1 << args[index]['width']) - 1));offset += args[index]['width']
                if offset != n['width']: raise ValueError('concat width contract differs')
            elif kind == 'slice':
                if n['lo'] < 0 or n['hi'] - n['lo'] + 1 != n['width']: raise ValueError('slice shape differs')
                feed(0, mask << n['lo'])
            elif kind == 'bit_select':
                if n['bit'] < 0: raise ValueError('dynamic selection needs a registered demand rule')
                feed(0, 1 << n['bit'])
            elif kind in ('assign', 'cast', 'zext', 'trunc'):
                feed(0, mask)
            else: raise ValueError('unregistered wiring bit-demand semantics')
        else: raise ValueError('unregistered operator bit-demand semantics: ' + op)
    return demand


def operator_shape(node, nodes, demanded=None):
    op = node['operation']; operands = node['operands']
    if op not in ('mul', 'add', 'addcarry') or len(operands) != (3 if op == 'addcarry' else 2):
        raise ValueError('unregistered operator shape: ' + op)
    data = [operand_shape(a, nodes) for a in operands[:2]]
    carry = operand_shape(operands[2], nodes) if op == 'addcarry' else None
    effective = 'add' if carry and carry['literal_hex'] == '0x0' else op
    mask = (1 << node['width']) - 1 if demanded is None else demanded[node['id']]
    return dict(operation=effective, native_operation=op, result_width=mask.bit_length(),
                declared_result_width=node['width'], required_result_mask_hex=hex(mask), operands=data,
                carry=carry, result_known_zero_hex=hex(bits(node['known_zero_hex'])),
                result_known_one_hex=hex(bits(node['known_one_hex'])))


def reuse_conditions(shape, primitive):
    operands = shape['operands']; domain = primitive['stages']['grt']['operations'].get(shape['operation'])
    reasons = []
    if any(a['signed'] for a in operands): reasons.append('signed_operands')
    if any(a['literal_hex'] is not None for a in operands): reasons.append('literal_data')
    if any(a['known_zero_bits'] or a['known_one_bits'] for a in operands): reasons.append('known_operand_bit_pattern')
    width = tuple(a['billing_width'] for a in operands) + (shape['result_width'],)
    matches = [] if not domain else [d for d in domain['joint_domain']
        if (d['lhs_width'], d['rhs_width'], d['result_width']) == width]
    if not matches: reasons.append('width_or_result_shape')
    return dict(existing_shape_price_available=not reasons, blockers=reasons,
                registered_SDC_ps=sorted({d['sdc_period_ps'] for d in matches}),
                registered_capture_banks=sorted({d['production_capture_fanout'] for d in matches}),
                fast_regime_or_internal_load_qualified=False)


def fitting_catalog(dataset):
    if (dataset.get('mode') != 'fitting' or not dataset.get('rows')
            or dataset.get('old_test_labels_used') or not dataset.get('full_collection_complete')):
        raise ValueError('explicit fitting-side dataset required')
    if any(r['split'] not in ('train', 'validation') for r in dataset['rows']):
        raise ValueError('independent/reference/diagnostic rows forbidden in fitting reuse')
    # No delay/area/slack values enter this catalog or select a new algorithm.
    return [dict(id=r['id'], split=r['split'], operation=r['operation'], stage=r['stage'],
                 features=r['features']) for r in dataset['rows'] if r['stage'] == 'grt']


def summarize(candidates, primitive, state, catalog):
    if any(r['split'] not in ('train', 'validation') for r in catalog):
        raise ValueError('consumed independent metadata entered reuse inventory')
    shapes = {}; loads = {}; stages = {}; case_rows = []; totals = Counter()
    for case, exports in candidates:
        rows = []
        for d in exports:
            if d['PPA_calls'] or d['D_selection_completed'] or not d['exhaustive_unit_assignments_checked']:
                raise ValueError('complete static-only assignment audit required')
            nodes = {n['id']: n for n in d['nodes']}; demand = demanded_bits(nodes, d['ports']); operators = {}
            for n in nodes.values():
                if n['constant'] or n['operation'] in ('input', 'wire'): continue
                if not demand[n['id']]: continue
                shape = operator_shape(n, nodes, demand); signature = key(shape); operators[n['id']] = signature
                if signature not in shapes:
                    reuse = reuse_conditions(shape, primitive)
                    a, b = (o['billing_width'] for o in shape['operands'])
                    eligible = [r for r in catalog if r['operation'] == shape['operation']
                        and (r['features']['lhs_width'], r['features']['rhs_width'], r['features']['result_width'])
                        == (a, b, shape['result_width'])] if reuse['existing_shape_price_available'] else []
                    shapes[signature] = dict(shape=shape, reuse=reuse,
                        fitting_rows_by_role=dict(Counter(r['split'] for r in eligible)), occurrences=0)
                shapes[signature]['occurrences'] += 1
            children = defaultdict(list)
            for n in nodes.values():
                for i, a in enumerate(n['operands']):
                    if a['kind'] == 'symbol': children[a['node']].append((n['id'], i))
            def upstream(at, inside, seen=frozenset()):
                if at in seen or at not in inside: return set()
                if at in operators: return {at}
                return set().union(*(upstream(a['node'], inside, seen | {at})
                    for a in nodes[at]['operands'] if a['kind'] == 'symbol'))
            state_ranges = {}; stage_count = 0
            for view in d['views']:
                q = view['state']['query']; slots = q['slots']
                if sum(s['variable_bits'] for s in slots) != q['features']['state_bits']:
                    raise ValueError('state mask/feature accounting differs')
                for s in slots:
                    if bits(s['variable_mask_hex']).bit_count() != s['variable_bits']:
                        raise ValueError('native state variable mask differs')
                for owner, selected in [('native_state', [s for s in slots if not s['external_capture']]),
                                        ('external_state', [s for s in slots if s['external_capture']])]:
                    data = [s for s in selected if not s['valid']]
                    f = dict(data_bits=sum(s['variable_bits'] for s in data), data_signals=len(data),
                        valid_bits=sum(s['variable_bits'] for s in selected if s['valid']),
                        enable_domains=(0 if owner == 'external_state' else len({s['enable_stage'] for s in data if s['enable_stage'] >= 0})),
                        reset_one_bits=sum((bits(s['variable_mask_hex']) & bits(s['reset_hex'])).bit_count() for s in data))
                    for name, value in f.items():
                        bounds = state_ranges.setdefault(owner + '/' + name, [value, value]);bounds[0] = min(bounds[0], value);bounds[1] = max(bounds[1], value)
                for stage in view['stages']:
                    inside = set(stage['semantic_members']); paid = inside & operators.keys()
                    edges = {(parent, n) for n in paid for a in nodes[n]['operands'] if a['kind'] == 'symbol'
                             for parent in upstream(a['node'], inside)}
                    hist = dict(sorted(Counter(nodes[n]['operation'] for n in paid).items()))
                    descriptor = dict(operation_histogram=hist, arithmetic_edges=len(edges),
                        result_bits=sum(nodes[n]['width'] for n in paid),
                        demanded_result_bits=sum(demand[n].bit_count() for n in paid),
                        capture_bits=sum(c['declared_width'] * c['banks'] for c in stage['captures']),
                        capture_count=sum(c['banks'] for c in stage['captures']))
                    stages.setdefault(key(descriptor), dict(features=descriptor, occurrences=0))['occurrences'] += 1
                    stage_count += 1
                    for n in paid:
                        consumers = []; walk = set()
                        def descend(at):
                            if at in walk: return
                            walk.add(at)
                            for child, operand in children[at]:
                                if child not in inside: continue
                                if child in paid: consumers.append((operators[child], operand))
                                else: descend(child)
                        descend(n)
                        captures = [c for c in stage['captures'] if n in upstream(c['value'], inside)]
                        load = dict(operator_shape_id=operators[n],
                            internal_consumers=[dict(shape_id=k, operand_index=i) for k, i in sorted(set(consumers))],
                            semantic_consumer_edges=len(consumers),
                            direct_capture_banks=sum(c['banks'] for c in stage['captures'] if c['value'] == n),
                            through_wiring_capture_banks=sum(c['banks'] for c in captures))
                        loads.setdefault(key(load), dict(features=load, occurrences=0))['occurrences'] += 1
            trials = d['unit_assignment_trials']; views = len(d['views']); totals.update(candidates=1, assignment_trials=trials, legal_views=views)
            rows.append(dict(candidate=d['candidate'], shape_sha256=d['policy_shape_sha256'],
                arithmetic_nodes=len(operators), assignment_trials=trials, legal_views=views,
                maximum_declared_arithmetic_width=max(nodes[n]['width'] for n in operators),
                maximum_required_result_width=max(demand[n].bit_length() for n in operators),
                stage_queries=stage_count, state_owner_feature_ranges=state_ranges,
                external_capture_policy='public output unconditional; legacy projection enable metadata is not a public protocol proof',
                state_owner_features_qualified=False,
                actual_C_final_state_materialization_checked=d['actual_C_final_state_materialization_checked'],
                input_service_projection='requires_public_wrapper_binding; not included in native core query'))
        case_rows.append(dict(case=case, candidates=rows))
    domains = [set(v['reuse']['registered_SDC_ps']) for v in shapes.values() if v['reuse']['existing_shape_price_available']]
    common = set(state['exact_SDC_ps']) & set.intersection(*domains) if domains else set()
    return dict(version=VERSION, status='static_requirements_complete', cases=case_rows, totals=dict(totals),
        operator_shapes=shapes, load_contexts=loads, stage_feature_contexts=stages,
        state_primitive_common_registered_SDC_ps=sorted(common),
        reused_fitting_rows=len(catalog), fitting_roles=dict(Counter(r['split'] for r in catalog)),
        independent_labels_read=False, new_fitted_parameters=False, PPA_calls=0,
        model_shape_hashes_are_identity_not_prediction_features=True,
        remaining=['near-speed-limit and internal-load qualification', 'actual service/native/external S binding and joint source qualification',
                   'G complete topology/connectivity qualification; static aggregate features alone do not qualify a stage',
                   'scan/quality/partition/resource admission', 'D selection/RTL/physical evaluation'], full_D_ready=False)


def prepare(out, source_manifest, cases):
    config = read(CONFIG); prior = read(source_manifest)
    selected = [copy.deepcopy(c) for c in prior['cases'] if c['name'] in cases]
    if len(selected) != len(cases) or len(set(cases)) != len(cases): raise ValueError('unknown or repeated source list')
    for c in selected:
        source = Path(c['source'])
        if sha(source) != c['generated_source_sha256']: raise ValueError('public source identity differs')
        target = out / 'sources' / (c['name'] + '.cpp'); target.parent.mkdir(parents=True, exist_ok=True);shutil.copy2(source, target);c['source'] = str(target.resolve())
        for filename, digest in c.get('public_VUL_source_sha256', {}).items():
            public = ROOT / 'experiments/arithmetic/evidence/step7_m2_native_integration_v1/public-source' / c['name'] / filename
            if sha(public) != digest: raise ValueError('public VUL source identity differs')
            target = out / 'public-source' / c['name'] / filename;target.parent.mkdir(parents=True, exist_ok=True);shutil.copy2(public, target)
    write(out / 'cases.json', dict(cases=selected, exhaustive_assignment_limit=config['preflight']['exhaustive_assignment_limit_per_candidate']))
    inputs = [CONFIG, Path(__file__), ROOT / 'rtlzz/testv2/arithmetic_d_requirements_export.cpp', ROOT / PRIMITIVES, ROOT / STATE]
    inputs += [ROOT / 'regression/arithmetic_fast_preflight.py', ROOT / 'rtlzz/CMakeLists.txt']
    inputs += sorted(p for p in (ROOT / 'rtlzz/src').rglob('*') if p.is_file())
    write(out / 'source-freeze.json', dict(version=VERSION, protocol_sha256=sha(CONFIG),
        files={str(p.relative_to(ROOT)): sha(p) for p in inputs},
        public_manifest_sha256=sha(source_manifest), physical_admission_allowed=False))


def analyze(out):
    freeze = read(out / 'source-freeze.json')
    if any(sha(ROOT / p) != h for p, h in freeze['files'].items()): raise ValueError('preflight source/model changed')
    index = read(out / 'native/index.json'); candidates = []
    if not index['exhaustive_unit_assignments_checked']: raise ValueError('missing bounded exhaustive native export')
    for c in index['cases']:
        exports = []
        for row in c['candidates']:
            path = out / 'native' / row['file']
            if sha(path) != row['sha256']: raise ValueError('native candidate identity changed')
            exports.append(read(path))
        candidates.append((c['case'], exports))
    catalog = fitting_catalog(read(ROOT / FITTING)); write(out / 'fitting-feature-catalog.json', catalog)
    result = summarize(candidates, read(ROOT / PRIMITIVES), read(ROOT / STATE), catalog)
    result.update(protocol_sha256=sha(CONFIG), native_index_sha256=sha(out / 'native/index.json'),
                  fitting_source=dict(path=FITTING, sha256=sha(ROOT / FITTING), numerical_labels_used_for_fitting=False))
    write(out / 'requirements.json', result)
    print(json.dumps(dict(status=result['status'], **result['totals'], operator_shapes=len(result['operator_shapes']),
        load_contexts=len(result['load_contexts']), stage_contexts=len(result['stage_feature_contexts']), PPA_calls=0)), flush=True)


def package(out, folder):
    if folder.exists(): raise ValueError('preserve previous preflight evidence')
    freeze = read(out / 'source-freeze.json')
    if any(sha(ROOT / name) != digest for name, digest in freeze['files'].items()): raise ValueError('preflight producer changed before packaging')
    index = read(out / 'native/index.json')
    payload = dict(version=VERSION, config=read(CONFIG), primitive=read(ROOT / PRIMITIVES), state=read(ROOT / STATE),
        catalog=read(out / 'fitting-feature-catalog.json'),
        cases=[(c['case'], [read(out / 'native' / row['file']) for row in c['candidates']]) for c in index['cases']])
    folder.mkdir(parents=True)
    (folder / 'replay-inputs.json.gz').write_bytes(gzip.compress(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode(), mtime=0))
    for name in ('requirements.json', 'guards.json', 'source-freeze.json'):
        shutil.copy2(out / name, folder / name)
    sources = {name: dict(sha256=sha(ROOT / name), text=(ROOT / name).read_text()) for name in (
        str(Path(__file__).relative_to(ROOT)), str(CONFIG.relative_to(ROOT)),
        'regression/arithmetic_fast_preflight.py', 'rtlzz/testv2/arithmetic_d_requirements_export.cpp')}
    (folder / 'source-pool.json.gz').write_bytes(gzip.compress(json.dumps(sources, sort_keys=True, separators=(',', ':')).encode(), mtime=0))
    public = {'cases.json': dict(sha256=sha(out / 'cases.json'), text=(out / 'cases.json').read_text())}
    for directory in ('sources', 'public-source'):
        for path in (out / directory).rglob('*'):
            if path.is_file(): public[str(path.relative_to(out))] = dict(sha256=sha(path), text=path.read_text())
    (folder / 'public-source-pool.json.gz').write_bytes(gzip.compress(json.dumps(public, sort_keys=True, separators=(',', ':')).encode(), mtime=0))
    write(folder / 'capabilities.json', dict(version=VERSION, static_requirements_only=True, actual_native_execution=True,
        source_list_parameterized=True, complete_bounded_group_placements=True,
        portable_numerical_replay=True, fresh_Cpp_compile_in_portable_verify=False,
        independent_labels_read=False, physical_admission_allowed=False, full_D_ready=False, PPA_calls=0))
    (folder / 'README.md').write_text(('''# 近速度极限模型原型：P0静态需求与复用审计

真实公共源码经当前RTLzz生产候选／调度组重新导出，穷举有界的可动组级分配并由生产evaluateSchedule检查。当前先导为MAC32，导出器及审计按源码清单和图特征工作，不以案例名查价格。

复核：`python3 -B -m experiments.arithmetic_dse.model_fast_preflight verify --out experiments/arithmetic/evidence/EVIDENCE_NAME`

便携核验重算冻结图上的形状、负载、组合及状态需求和旧模型形状／精确周期交集；不重新编译C++、不运行EDA、不拟合、不读取独立物理标签。四份改变的生产／检查源在source-pool中，其余RTLzz生产源身份及原模型由source-freeze追溯；全部源码仍由项目仓库提供。

requirements保留旧拟合侧几何特征匹配数量，不将匹配数量当成近极限或级内负载资格。S的native／external投影计数与公开外部无条件捕获策略明确分开；输入service仍需从外壳绑定。G的聚合静态描述不是完整拓扑资格或阶段模型。PPA0，full_D_ready=false。

源角色及旧测试隔离保持；独立测试、参考和not_training诊断未进入新拟合。实际命令、日志、资源及旧九例兼容复核在build/step7-fast-prototype-20261109的对应P0后继目录；publication-closure.json另绑定全部本轮support收据和结清资源，不将封包之后的核验费用回填到此前前缀。
''').replace('EVIDENCE_NAME', folder.name))
    write(folder / 'manifest.json', dict(version=VERSION,
        files={p.name: sha(p) for p in sorted(folder.iterdir()) if p.is_file()}))
    print(json.dumps(dict(status='sealed', files=len(list(folder.iterdir())), bytes=sum(p.stat().st_size for p in folder.iterdir()), PPA_calls=0)), flush=True)


def verify_package(folder):
    manifest = read(folder / 'manifest.json')
    if manifest['version'] != VERSION or any(sha(folder / name) != digest for name, digest in manifest['files'].items()):
        raise ValueError('preflight evidence identity mismatch')
    payload = json.loads(gzip.decompress((folder / 'replay-inputs.json.gz').read_bytes()))
    if (payload['version'] != VERSION or payload['config']['physical_admission_allowed']
            or payload['config']['selection']['epsilon_numerator'] != 5 or payload['config']['selection']['epsilon_denominator'] != 100):
        raise ValueError('wrong preflight scope or user speed band')
    result = summarize(payload['cases'], payload['primitive'], payload['state'], payload['catalog'])
    expected = read(folder / 'requirements.json')
    if any(expected[k] != v for k, v in result.items()): raise ValueError('preflight semantic replay differs')
    source = json.loads(gzip.decompress((folder / 'source-pool.json.gz').read_bytes()))
    for name, item in source.items():
        if hashlib.sha256(item['text'].encode()).hexdigest() != item['sha256']: raise ValueError('preflight frozen source differs')
    public = json.loads(gzip.decompress((folder / 'public-source-pool.json.gz').read_bytes()))
    for item in public.values():
        if hashlib.sha256(item['text'].encode()).hexdigest() != item['sha256']: raise ValueError('public source snapshot differs')
    print(json.dumps(dict(status='passed', **result['totals'], original_build_ledger_EDA_not_needed=True,
        independent_labels_read=False, PPA_calls=0, full_D_ready=False)), flush=True)


def run(out, source_manifest, cases, build, evidence):
    from .budget import Ledger, POLICY, usage
    from .processes import run_command
    out.mkdir(parents=True, exist_ok=False); ledger = Ledger(); config = read(CONFIG)
    before = read(ledger.path); current = usage(before['entries']); limits = read(POLICY)['resources']; later = config['later_work_reserved']
    allowance = config['preflight']['support_walltime_envelope_s']
    if (current['walltime_s'] + allowance + later['walltime_s'] > limits['max_global_walltime_h'] * 3600
            or current['CPU_time_s'] + 4 * allowance + later['CPU_time_s'] > limits['max_tool_CPU_time_h'] * 3600
            or current['synth'] + later['synth'] > limits['max_synthesis_calls']
            or current['grt'] + later['grt'] > limits['max_global_route_calls']
            or shutil.disk_usage(out).free < later['storage_bytes'] + 268435456):
        raise ValueError('preflight and explicitly reserved later work not funded')
    write(out / 'usage-before-prefix.json', dict(entries=len(before['entries']), sha256=sha(ledger.path), usage=current))
    ctx = dict(target_platform=config['platform'], admission_id=out.name, task_id='P0-source-list-preflight'); commands = []
    env = os.environ.copy(); env.update(PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4')
    with ledger.job(ctx):
        def execute(command, name, timeout):
            r = ledger.reserve(None, timeout, 4, 'fast_model_prototype_preflight', command, out / name, context=ctx)
            record = run_command(command, out, name, timeout, env, 8192, cpu_limit_s=r['CPU_time_s']);ledger.finish(r, record)
            commands.append({**record, 'budget_reservation_id': r['id']});write(out / 'commands.json', commands)
            if record['exit_code']: raise RuntimeError(name + ' failed: ' + record['log'])
            print(name + ': ' + Path(record['log']).read_text()[-900:], flush=True)
        execute([sys.executable, '-B', '-m', 'experiments.arithmetic_dse.model_fast_preflight', 'prepare', '--out', str(out), '--source-manifest', str(source_manifest), '--cases', *cases], 'prepare', 120)
        execute(['cmake', '--build', str(build), '--target', 'arithmetic-d-requirements-export', '-j4'], 'build', 1800)
        execute([str(build / 'testv2/arithmetic-d-requirements-export'), str(ROOT), str(out / 'cases.json'), str(out / 'native')], 'native', 1800)
        execute([sys.executable, '-B', '-m', 'experiments.arithmetic_dse.model_fast_preflight', 'analyze', '--out', str(out)], 'analyze', 300)
        execute([sys.executable, '-B', str(ROOT / 'regression/arithmetic_fast_preflight.py'), '--out', str(out)], 'guards', 300)
        # The old source list still uses the original bounded C-neighbour audit.
        execute([str(build / 'testv2/arithmetic-d-requirements-export'), str(ROOT), str(source_manifest), str(out / 'legacy-native')], 'legacy-native', 300)
        execute([sys.executable, '-B', str(ROOT / 'regression/arithmetic_fast_preflight.py'), '--out', str(out), '--legacy', str(source_manifest.parent / 'native')], 'legacy-parity', 300)
        execute([sys.executable, '-B', '-m', 'experiments.arithmetic_dse.model_fast_preflight', 'package', '--out', str(out), '--evidence', str(evidence)], 'package', 300)
        execute([sys.executable, '-B', str(ROOT / 'regression/arithmetic_fast_preflight.py'), '--isolated-evidence', str(evidence)], 'isolated', 300)
    after = read(ledger.path); write(out / 'resource-increment.json', dict(before_entries=len(before['entries']),
        entries=after['entries'][len(before['entries']):], usage=usage(after['entries']), PPA_calls=0))
    write(evidence / 'publication-closure.json', dict(version=VERSION, manifest_sha256=sha(evidence / 'manifest.json'),
        resource_increment_sha256=sha(out / 'resource-increment.json'),
        entries=after['entries'][len(before['entries']):], usage=usage(after['entries']),
        pending=usage(after['entries'])['pending'], physical_calls_added=0, git_actions=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__);parser.add_argument('action', choices=('prepare', 'analyze', 'run', 'package', 'verify'))
    parser.add_argument('--out', type=Path, required=True);parser.add_argument('--source-manifest', type=Path)
    parser.add_argument('--cases', nargs='+');parser.add_argument('--build', type=Path, default=ROOT / 'build/step4-rtlzz')
    parser.add_argument('--evidence', type=Path)
    a = parser.parse_args(); out = a.out.resolve()
    if a.action in ('prepare', 'run') and (not a.source_manifest or not a.cases): parser.error('explicit source manifest and case list required')
    if a.action in ('package', 'run') and not a.evidence: parser.error('explicit new evidence directory required')
    if a.action == 'prepare': prepare(out, a.source_manifest.resolve(), a.cases)
    elif a.action == 'analyze': analyze(out)
    elif a.action == 'package': package(out, a.evidence.resolve())
    elif a.action == 'verify': verify_package(out)
    else: run(out, a.source_manifest.resolve(), a.cases, a.build.resolve(), a.evidence.resolve())


if __name__ == '__main__': main()
