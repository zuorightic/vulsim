"""N5/N6 receipts and backend-disabled replay of the six finite D interfaces.

These are integration probes at a software-only clock, not N7 application
targets or application PPA. The frozen compiler and ASAP7 inputs stay read-only.
"""
from collections import Counter, defaultdict
from copy import deepcopy
import gzip
import json
import math
from pathlib import Path
import subprocess
from unittest.mock import patch

from .nangate45_samples import ROOT, read, write, sha
from . import nangate45_pipeline_samples as samples
from . import nangate45_pipeline_runtime as runtime
from . import nangate45_pipeline_fit as fitting
from .workload_demand import Graph
from .nangate45_migration import SCOPE, software_root, verify as verify_baseline
from .workload_software_validation import bench
from .workload_equivalent import request_at

N12 = ROOT.parent/'vulsim-artifacts/nangate45-n12-20261117-v1'


def no_io(*args, **kwargs):
    raise AssertionError('N56 numerical inference attempted file or process access')


def numerical_guard():
    from contextlib import ExitStack
    stack = ExitStack()
    for name in ('builtins.open', 'io.open', 'subprocess.Popen', 'subprocess.run'):
        stack.enter_context(patch(name, no_io))
    return stack


def refused(label, call, rows):
    try:
        call()
    except (ValueError, KeyError):
        rows.append(label)
        return
    raise AssertionError('N56 negative control accepted: '+label)


def integration(root):
    root = Path(root)
    out = root/'software'
    out.mkdir(exist_ok=False)
    package = root/'package/package.json'
    rt = runtime.load_package(package)
    rows = []
    targets = (1733.,)  # Unmeasured request; formal A-derived clocks belong to N7.
    for case, depths in SCOPE.items():
        for depth in depths:
            native = N12/'software-check/native'/f'{case}-L{depth}'
            view = read(native/'inventory.json')['views'][0]
            folder = native/view['directory']
            graph = Graph(read(native/'graph.json'))
            state = read(folder/'state.json')
            owners = runtime.base.rebind(read(folder/'owners.json'))
            for target in targets:
                owners['target_ps'] = target
                state['features']['sdc_period_ps'] = target
                for row in owners['operators']:
                    row['query'] = request_at(row['query'], target)
                for row in owners['G_regions']:
                    row['query'] = request_at(row['query'], target)
                with numerical_guard():
                    result = rt.optimize(graph, view, state, owners)
                    if result['prediction'] is None:
                        raise ValueError(f'N56 uncovered complete score: {case} L{depth}')
                    index = int(result['best_variant_id'].split(':')[0])
                    trace = result['trace'][index]
                    best = next(x for x in trace['variants'] if x['id'] == result['best_variant_id'])
                    replay = rt.evaluate(graph, view, state, owners, owner_queries=best['actual_queries'])
                    if replay != result['prediction']:
                        raise ValueError('selected full numerical replay differs')
                    static = rt.evaluate(graph, view, state, owners, static_cal=True)
                    bindings = []
                    for node, conversion in trace['conversions'].items():
                        chosen = conversion['roots'][best['root_indices'][node]]
                        query = best['actual_queries'][node]
                        if query != chosen['query']:
                            raise ValueError('selected request and conversion differ')
                        price = rt.prices.operator_price(query) if conversion['kind']=='operator' else rt.prices.reduction_price(query)
                        if price != chosen['price']:
                            raise ValueError('selected price and conversion differ')
                        if not math.isfinite(chosen['tau_ps']) or chosen['tau_ps'] <= 0:
                            raise ValueError('nonpositive equivalent request')
                        bindings.append(dict(node=node, kind=conversion['kind'], global_T_ps=target,
                            body_budget_ps=trace['budgets_ps'][node], tau_ps=chosen['tau_ps'],
                            H_char_ps=conversion['H_char_ps'], D_other_char_ps=chosen['D_other_char_ps'],
                            query_sha256=chosen['query_sha256'], query=query, price=price,
                            local_request_met=chosen['local_request_met']))
                    if replay['S']['projection']['target_ps'] != target or any(
                            x['global_T_ps'] != target for x in bindings):
                        raise ValueError('local request leaked into S/global deadline')
                if result['candidate_PPA_calls'] or result['RTL_changed']:
                    raise ValueError('software integration changed RTL or measured a candidate')
                data = json.dumps(result, ensure_ascii=False, separators=(',', ':')).encode()
                trace_file = out/f'{case}-L{depth}-T{int(target)}.json.gz'
                trace_file.write_bytes(gzip.compress(data, mtime=0))
                projection = replay['S']['projection']
                support = rt.manifest['state_support']
                extrapolation = not (support['total_FF_bits'][0] <= projection['total_FF_bits'] <= support['total_FF_bits'][1])
                row = dict(case=case, L=depth, software_probe_T_ps=target, formal_N7_target=False,
                    native=str(native), view=view, state_path=str(folder/'state.json'), owners_path=str(folder/'owners.json'),
                    rtl=str(folder/'workload.sv'), rtl_sha256=sha(folder/'workload.sv'),
                    graph_sha256=sha(native/'graph.json'), state_sha256=sha(folder/'state.json'),
                    owners_sha256=sha(folder/'owners.json'), model_sha256=sha(package),
                    complete_score_replay_equal=True, complete_variants=result['complete_variants'],
                    best_variant_id=result['best_variant_id'], bindings=bindings,
                    stages=replay['stages'], active_arithmetic_stages=sorted({view['placement'][p['node']] for p in replay['owners']
                        if p['delay_ps']>0 or p['area_um2']>0}),
                    total_FF_bits=projection['total_FF_bits'], state_size_extrapolated=extrapolation,
                    requested_budget_window_feasible=result.get('requested_budget_window_feasible', True),
                    critical_required_ps=replay['critical_required_ps'], predicted_area_um2=replay['total_area_um2'],
                    local_requests_unmet=sum(not x['local_request_met'] for x in bindings),
                    G_owners=sum(x['kind']=='G' for x in replay['owners']),
                    G_members_not_billed_separately=replay['G_members_not_billed_separately'],
                    static_same_implementation=static, trace_file=str(trace_file), trace_sha256=sha(trace_file),
                    candidate_PPA_calls=0, file_IO_during_numeric_inference=False)
                rows.append(row)
                write(out/'progress.json', dict(completed=[dict(case=x['case'], L=x['L']) for x in rows]))
                print(f'N56 REPLAY {case} L{depth} owners={len(bindings)} variants={result["complete_variants"]}', flush=True)
                del result, replay, static
            Graph.origins.cache_clear()
            Graph.roots.cache_clear()
    # Fresh identities are mandatory for G as well as arithmetic owners.
    rejected = []
    query = deepcopy(rows[0]['bindings'][0]['query'])
    for key, value in [('target_platform','asap7'), ('profile_sha256','0'*64),
                       ('evaluation_stage','synth'), ('abc_target_ps',13.)]:
        wrong = deepcopy(query)
        wrong['flow_context'][key] = value
        refused('arithmetic '+key, lambda q=wrong: rt.prices.operator_price(q), rejected)
    original = rt.prices.operator_price(query)
    tagged = deepcopy(query)
    tagged.update(source='unseen-source', case='unseen-case', instance='unseen-instance')
    with numerical_guard():
        if rt.prices.operator_price(tagged) != original:
            raise ValueError('source identity selected a price')
    grow = next(x for row in rows for x in row['bindings'] if x['kind']=='G')
    wrong = deepcopy(grow['query'])
    wrong['target_platform'] = 'asap7'
    refused('G platform', lambda: rt.prices.reduction_price(wrong), rejected)
    wrong = deepcopy(grow['query'])
    wrong['profile_sha256'] = '0'*64
    refused('G profile', lambda: rt.prices.reduction_price(wrong), rejected)
    wrong = deepcopy(owners)
    wrong['profile_sha256'] = '0'*64
    refused('owner profile', lambda: rt.check(wrong), rejected)
    wrong = deepcopy(owners)
    if wrong['G_regions']:
        del wrong['G_regions'][0]['query']['target_platform']
        refused('G owner missing platform', lambda: rt.check(wrong), rejected)
    malformed = read(package)
    malformed['state_shared']['sha256'] = '0'*64
    malformed_path = out/'wrong-hash-package.json'
    for key in ('arithmetic','state_shared','characterization','cell_cover'):
        malformed[key]['path'] = str((package.parent/malformed[key]['path']).resolve())
    write(malformed_path, malformed)
    refused('payload hash', lambda: runtime.load_package(malformed_path), rejected)
    result = dict(status='passed', rows=rows, negative_controls=rejected,
        source_identity_ignored=True, candidate_PPA_calls=0, inference_file_IO=False,
        models_loaded_before_inference=True, requested_global_ABC_unchanged=True,
        full_application_search_performed=False, formal_application_PPA_used=False,
        precision_qualification_inherited=False)
    write(out/'integration.json', result)
    return result


def functional(root):
    root = Path(root)
    data = read(root/'software/integration.json')
    out = root/'software/functional'
    out.mkdir(exist_ok=False)
    rows = []
    for row in data['rows']:
        case, depth = row['case'], row['L']
        spec = read(software_root(case, depth)/case/'source/semantics.json')
        text, counts = bench(spec, row['view']['artifact'], depth, cycles=192)
        folder = out/f'{case}-L{depth}'
        folder.mkdir()
        (folder/'tb.sv').write_text(text)
        if sha(row['rtl']) != row['rtl_sha256']:
            raise ValueError('bound integration RTL changed')
        for cmd, name in [(['iverilog','-g2012','-s','tb','-o',str(folder/'sim'),row['rtl'],str(folder/'tb.sv')], 'compile'),
                          (['vvp', str(folder/'sim')], 'simulation')]:
            with (folder/(name+'.log')).open('w') as log:
                subprocess.run(cmd, check=True, stdout=log, stderr=subprocess.STDOUT, timeout=120)
        if 'PASS' not in (folder/'simulation.log').read_text():
            raise ValueError('bound integration RTL failed')
        rows.append(dict(case=case, L=depth, rtl_sha256=row['rtl_sha256'], cycles=192,
            integer_cycle_checks=counts, reset_stall_protocol_checked=True,
            simulation_sha256=sha(folder/'simulation.log')))
    from .nangate45_pipeline_alias_partial import verify as verify_alias
    admission = samples.verify(root)
    source = next(s for s in admission['sources'] if s['id']=='train-mul32-p0')
    mapped_folder = root/'runs/train-mul32-p0-T1500'
    design = read(mapped_folder/'mapped.json')
    pins = read(mapped_folder/'liberty-pins.json')
    contract = read(source['endpoint_contract'])
    semantics = read(Path(source['folder'])/'source.json')
    rtl = Path(source['rtl']).read_text()
    proved = verify_alias(design,pins,contract,semantics,rtl)
    old = "assign mul_tree_10_31[64:64] = '0;"
    if rtl.count(old)!=1:
        raise ValueError('partial-constant negative-control callsite changed')
    rejected = []
    refused('reset/update constant disagreement cannot fill an absent alias',
        lambda: verify_alias(design,pins,contract,semantics,rtl.replace(old,old.replace("'0", "'1"))), rejected)
    wrong = deepcopy(contract)
    slot = next(x for x in wrong['state_slots'] if x['name']=='rtlzz_pipe_17_s1')
    slot['variable_mask_hex'] = ['0']
    slot['variable_bits'] = 0
    refused('compiler mask cannot erase an actual dynamic FF',
        lambda: verify_alias(design,pins,wrong,semantics,rtl), rejected)
    write(out/'receipt.json', dict(status='passed', rows=rows, new_physical_calls=0,
        partial_alias_negative_controls=rejected,
        original_compiler_mask_overcounts=proved['compiler_variable_mask_overcounts'],
        compiler_state_pricing_features_unchanged=True))


def detailed_panels(root):
    """Report component and S errors separately; do not tune any parameter."""
    root = Path(root)
    admission = samples.verify(root)
    evaluation = read(root/'evaluation.json')
    panels = defaultdict(list)
    rows = []
    state_model = read(root/'package/state-shared.json')
    for row in evaluation['rows']:
        t = next(t for t in admission['tasks'] if t['id']==row['task'])
        source = next(s for s in admission['sources'] if s['id']==t['source'])
        owners = read(Path(source['folder'])/'owners.json')
        families = {r['node']:r['query']['local_context']['producer']['operation'] for r in owners['operators']}
        families.update({r['root']:'G' for r in owners['G_regions']})
        labels = read(root/'runs'/t['id']/'pipeline-labels.json')
        prediction = row['point_prediction']
        for p in prediction['owners']:
            actual = labels['nodes']['node_'+str(p['node'])]
            for metric, estimate, measured in [('delay',p['delay_ps'],actual['operator_delay_ps']),
                    ('area',p['area_um2'],actual['comb_area_um2'])]:
                ape = abs(estimate-measured)/max(1e-9,measured)
                key = families[p['node']]+'_embedded_'+metric
                panels[(row['role'],key)].append(dict(source=row['source'], APE=ape))
        controls = defaultdict(list)
        for p in labels['functional_paths']:
            kind = p['path_class']
            if kind in ('native_enable','native_valid','input_valid','external_valid'):
                controls[(kind,p['stage'])].append((.8 if kind=='input_valid' else 1.)*t['period_ps']-p['slack_ps'])
        for control in prediction['S']['controls']:
            kind, stage = control['path_class'], control['stage']
            # The model marks the input interface stage -1; label requests use 0.
            lookup = (kind,0 if kind=='input_valid' else stage)
            if lookup not in controls:
                continue
            estimate = control['required_ps']*(.8 if kind=='input_valid' else 1.)
            actual = max(controls[lookup])
            ape = abs(estimate-actual)/max(1e-9,actual)
            panels[(row['role'],'S_timing/'+kind)].append(dict(source=row['source'], APE=ape))
            rows.append(dict(task=t['id'], source=row['source'], path_class=kind, stage=stage,
                predicted_ps=estimate, actual_ps=actual, APE=ape))
    metrics = {role:{key:fitting.stats(value) for (r,key),value in panels.items() if r==role}
               for role in ('train','validation','test')}
    write(root/'component-panels.json',dict(metrics=metrics, control_rows=rows,
        parameters_changed=False, reset_write_enable_are_frozen_proxies=True,
        data_boundaries_ps=state_model['S']['data_boundary_ps'], reserve_ps=state_model['S']['joint_reserve_ps']))
    return metrics


def receipts(root):
    root = Path(root)
    a = samples.verify(root)
    p = read(root/'progress.json')
    if len(p['completed'])!=len(a['tasks']) or p['errors']:
        raise ValueError('N56 collection incomplete')
    seal = read(root/'model-freeze.json')
    for name, expected in seal['files'].items():
        if sha(name)!=expected:
            raise ValueError('frozen parameter drift')
    rows = []
    for t in a['tasks']:
        folder = root/'runs'/t['id']
        d = read(folder/'pipeline-labels.json')
        status = read(folder/'pipeline-status.json')
        if sha(folder/'pipeline-labels.json')!=status['label_sha256']:
            raise ValueError('label seal drift')
        if d['role']!=t['role'] or d['profile_sha256']!=a['profile_sha256']:
            raise ValueError('label role/profile mismatch')
        if not d['area_and_path_increments_owned_once']:
            raise ValueError('nonexclusive composition ownership')
        if abs(d['total_area_um2']-d['whole_shell_metrics']['cell_area_um2'])>1e-5:
            raise ValueError('physical area not conserved')
        proof = folder/'logs/nangate45/arithmetic_probe/base/structural_cec/proof.json'
        if sha(proof)!=d['CTS_CEC_sha256']:
            raise ValueError('CTS proof changed')
        for command in folder.glob('*.command.json'):
            rec = read(command)
            if rec['exit_code'] or rec.get('cleanup',{}).get('remaining_live_pids'):
                # Report-only failed readers are explicitly preserved attempts.
                if not command.name.startswith(('readout.', 'readout-v2.')):
                    raise ValueError('unfinished physical/support leaf: '+str(command))
        mapped_state = read(folder/'mapped-state.json')
        rows.append(dict(task=t['id'], role=t['role'], label_sha256=status['label_sha256'],
            setup_slack_ps=d['whole_shell_metrics']['setup_worst_slack_ps'],
            hold_slack_ps=d['whole_shell_metrics']['hold_worst_slack_ps'],
            exact_wire_owners=d['exact_Boolean_wire_owners'], CTS_CEC_verified=True,
            exclusive_area_verified=True, functional_path_count=len(d['functional_paths']),
            compiler_variable_mask_overcounts=mapped_state.get('compiler_variable_mask_overcounts', [])))
    ledger = read(ROOT/'experiments/arithmetic/backend_usage.json')
    own = [x for x in ledger['entries'] if str(x.get('admission_id','')).startswith('matrix-nangate45-n56-')]
    jobs = [x for x in ledger.get('jobs',[]) if str(x.get('admission_id','')).startswith('matrix-nangate45-n56-')]
    if any(x['status'] in ('reserved','unsettled') for x in own) or any(x['status']!='released' for x in jobs):
        raise ValueError('N56 accounting has active/unsettled work')
    baseline = verify_baseline(N12)
    result = dict(status='passed', rows=rows, frozen_baseline=baseline,
        own_calls=dict(Counter(x['stage'] or 'support' for x in own)),
        walltime_s=sum(x.get('walltime_s',0) for x in own), CPU_time_s=sum(x.get('CPU_time_s',0) for x in own),
        failed_entries=[dict(id=x['id'], task=x.get('task_id'), stage=x['stage']) for x in own if x['status']=='failed'],
        all_own_leaves_settled=True, all_own_jobs_released=True,
        physical_setup_unmet_points=sum(x['setup_slack_ps']<0 for x in rows),
        physical_hold_negative_points=sum(x['hold_slack_ps']<0 for x in rows),
        physical_hold_review_points=sum(x['hold_slack_ps']<5 for x in rows),
        application_PPA_calls=0, ASAP7_configuration_or_processes_modified=False)
    write(root/'receipt-verification.json',result)
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('action', choices=('integration','functional','panels','receipts'))
    args = parser.parse_args()
    actions = dict(integration=integration, functional=functional, panels=detailed_panels, receipts=receipts)
    result = actions[args.action](args.root.resolve())
    if result is not None:
        print(json.dumps({k:v for k,v in result.items() if k!='rows'}, ensure_ascii=False, indent=2))
