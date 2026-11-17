"""Backend-disabled platform-entry regression, with external small receipts.

Uses existing prospective graphs and frozen numeric functions. The Nangate45
fixture deliberately keeps identical numbers to test identity plumbing; it is
never a calibrated model, application result, or production package.
"""
import argparse
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from . import prospective_cell_cover as cells
from . import workload_platform_entry as entry
from .nangate45_migration import SCOPE, ROOT, software_root
from .workload_final_selection import BASE
from .workload_final_prices import CachedPrices
from .workload_diagnostic import evaluate
from .workload_demand import Graph
from .workload_tight_equivalent import optimize
from .workload_equivalent import score_key
from .workload_final_software import BINARY
from .platforms import profile


def canonical(doc):
    return json.dumps(doc, sort_keys=True, separators=(',', ':')).encode()


def package(root, platform, bundle, contract):
    root.mkdir(parents=True, exist_ok=True)
    entry.write(root/'response.json', bundle)
    entry.write(root/'characterization.json', contract)
    entry.write(root/'cell-cover.json', dict(profile_sha256=profile(platform)['profile_sha256'],
        area_um2=cells.AREA, role='same-numbers regression fixture; not Nangate45 characterization'))
    doc = dict(schema=entry.SCHEMA, platform=platform,
        profile_sha256=profile(platform)['profile_sha256'], evaluation_stage='grt', status='ready',
        pricing='offline_shared_functions', online_backend_feedback=False, application_PPA_used=False,
        exact_lookup=False, role='test_fixture_only_no_application_emission')
    for name, filename in [('response','response.json'),('characterization','characterization.json'),('cell_cover','cell-cover.json')]:
        doc[name] = dict(path=filename, sha256=entry.sha(root/filename))
    entry.write(root/'package.json', doc)
    return root/'package.json'


def denied(call):
    try:
        call()
    except ValueError:
        return True
    raise AssertionError('identity/contract mismatch was accepted')


def metadata(selection):
    folder = Path(selection['rtl']).parent
    graph = Graph(entry.read(folder/'graph.json'))
    state = entry.read(folder/'state.json')
    owners = entry.read(folder/'owners.json')
    return graph, dict(placement=selection['placement']), state, owners


def run(out):
    out = Path(out).resolve()
    if out.is_relative_to(ROOT) or (out/'software-check.json').exists():
        raise ValueError('new external check output required')
    out.mkdir(parents=True, exist_ok=True)
    bundle = entry.read(BASE/'diagnostic-model.json')
    contract = entry.read(software_root('mac32',2)/'characterization-contract.json')
    asap_package = package(out/'asap7-regression-package', 'asap7', bundle, contract)
    runtime = entry.load_package(asap_package, 'asap7')
    # No subprocess or file access is allowed during numerical consumption.
    no_io = dict(side_effect=AssertionError('online I/O forbidden during prediction'))
    rows = []
    for case, depths in SCOPE.items():
        for depth in depths:
            selection_path = software_root(case, depth)/case/'final-selections.json'
            selected = entry.read(selection_path)['records'][0]['methods']['D']
            g,v,s,o = metadata(selected)
            legacy_prices = CachedPrices(bundle)
            with patch('subprocess.Popen', **no_io), patch('builtins.open', **no_io), patch('io.open', **no_io):
                old = evaluate(g,v,s,o,legacy_prices)
                new = runtime.evaluate(g,v,s,o)
                if old != new:
                    raise AssertionError('same input/model full scoring differs')
                # Recompute the full finite budget/inversion response for the
                # actual selected implementation; this includes S/shared/G.
                result = runtime.optimize(g,v,s,o)
            actual = result['prediction']
            expected = selected['prediction']
            for name in ('critical_required_ps','total_area_um2','violation_ps','target_met'):
                if isinstance(expected[name], bool):
                    assert actual[name] == expected[name]
                elif abs(actual[name]-expected[name]) > 1e-7 * max(1,abs(expected[name])):
                    raise AssertionError('selected frozen budget replay differs: '+case+' '+name)
            rows.append(dict(case=case,L=depth,T_ps=selected['T_clk_ps'],
                rtl_sha256=selected['rtl_sha256'], selection_file=str(selection_path),
                selection_sha256=entry.sha(selection_path), full_score_exact_equal=True,
                selected_full_budget_replay_matches=True, complete_variants=result['complete_variants'],
                result_sha256=hashlib.sha256(canonical(result)).hexdigest()))
            del result, g, old, new, legacy_prices
            runtime.prices.cache.clear(); runtime.prices.cover_cache.clear()
            Graph.origins.cache_clear(); Graph.roots.cache_clear()
            print(f'REPLAY {case} L{depth}', flush=True)
    # Re-rank all existing common pools without opening full score traces.
    rankings = []
    for case, depths in SCOPE.items():
        for depth in depths:
            soft = software_root(case,depth)
            selection = entry.read(soft/case/'final-selections.json')
            for group in selection['records']:
                target = group['target']['T_ps']
                summary = soft/case/f'scores-T{target}'/'pool-summary.json.gz'
                if not summary.exists():
                    # MAC L3 is the immutable step45 pool and its score IDs.
                    from .workload_steps45_package import replay_data
                    from .workload_final_selection import PREVIOUS
                    data,_ = replay_data(PREVIOUS)
                    scored = [r for r in data['rows'] if r['target_ps']==target]
                    model = min((r for r in scored if r['model'] is not None), key=lambda r:score_key(r['model'])+(r['id'],))
                    del data
                else:
                    scored = json.loads(gzip.decompress(summary.read_bytes()))
                    model = min((r for r in scored if r['model'] is not None), key=lambda r:score_key(r['model'])+(r['id'],))
                assert model['id'] == group['search']['selected_id']
                rankings.append(dict(case=case,L=depth,T_ps=target,candidates=len(scored),selected_id=model['id'],
                    scope='rerank frozen complete predictions; not all-candidate numerical replay'))
                del scored
    # Same numbers on the new platform, strictly a plumbing fixture.
    selected = entry.read(software_root('mac32',2)/'mac32/final-selections.json')['records'][0]['methods']['D']
    g,v,s,o = metadata(selected)
    ng_bundle = deepcopy(bundle)
    def reprofile(value):
        if isinstance(value, dict):
            for name,item in value.items():
                if name in ('profile_sha256','operator_profile_sha256'):
                    value[name]=profile('nangate45')['profile_sha256']
                else: reprofile(item)
        elif isinstance(value,list):
            for item in value:reprofile(item)
    reprofile(ng_bundle)
    ng_contract = deepcopy(contract); ng_contract['profile_sha256']=profile('nangate45')['profile_sha256']
    ng_package = package(out/'nangate45-plumbing-fixture', 'nangate45', ng_bundle, ng_contract)
    ng = entry.load_package(ng_package, 'nangate45')
    rebound = entry.rebind_owners(o,'nangate45')
    with patch('subprocess.Popen', **no_io), patch('builtins.open', **no_io), patch('io.open', **no_io):
        new = ng.optimize(g,v,s,rebound)
        old = runtime.optimize(g,v,s,o)
        assert new['prediction'] == old['prediction']
    rejected = dict(wrong_platform_package=denied(lambda:entry.load_package(asap_package,'nangate45')),
        wrong_owner_profile=denied(lambda:ng.evaluate(g,v,s,o)),
        pending_production_model=denied(lambda:entry.load_package(ROOT/'experiments/arithmetic_dse/configs/nangate45_frozen_d_v1.json','nangate45')))
    bad = deepcopy(ng.manifest);bad['characterization'] = entry.read(asap_package)['characterization']
    bad['characterization']['path']=str(asap_package.parent/'characterization.json')
    entry.write(ng_package.parent/'bad-package.json',bad)
    rejected['sampling_contract_profile']=denied(lambda:entry.load_package(ng_package.parent/'bad-package.json','nangate45'))
    query=deepcopy(rebound['operators'][0]['query']);query['flow_context']['target_platform']='asap7'
    rejected['operator_platform_even_matching_hash']=denied(lambda:ng.prices.operator_price(query))
    bad=deepcopy(ng.manifest);bad['response']['sha256']='0'*64
    entry.write(ng_package.parent/'bad-hash-package.json',bad)
    rejected['response_hash']=denied(lambda:entry.load_package(ng_package.parent/'bad-hash-package.json','nangate45'))
    # Actual native frontend tests use no backend tool, no response bundle.
    exports=[]
    for case,depths in SCOPE.items():
        for depth in depths:
            soft=software_root(case,depth)
            pool=entry.read(soft/case/'static-pool.json')
            block,limb=pool['grammar'][1]
            dest=out/'native'/f'{case}-L{depth}'
            entry.native_export(BINARY,soft/case/'source/request.json',dest,
                platform='nangate45',L=depth,limb=limb,block=block,target_ps=3000)
            inv=entry.read(dest/'inventory.json')
            for view in inv['views']:
                owner=entry.read(dest/view['directory']/'owners.json')
                assert owner['profile_sha256']==profile('nangate45')['profile_sha256']
                assert all(r['query']['flow_context']['target_platform']=='nangate45' for r in owner['operators'])
            exports.append(dict(case=case,L=depth,block=block,limb=limb,views=len(inv['views']),
                receipt=str(dest/'platform-entry.json'),receipt_sha256=entry.sha(dest/'platform-entry.json')))
    receipt=dict(version='nangate45-N12-software-check-v1',status='passed',
        same_model_full_score_replays=rows,selected_full_budget_replays=len(rows),rankings=rankings,
        rejected=rejected,native_platform_exports=exports,
        backend_disabled_during_consumption=True,file_IO_disabled_during_consumption=True,
        NGA_fixture='identical ASAP7 numbers; identity plumbing only, not a fitted Nangate45 model',
        production_NGA_model_ready=False,candidate_PPA_calls=0,all_pool_numerical_replay=False)
    entry.write(out/'software-check.json',receipt)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();r=run(a.out)
    print(json.dumps({k:v for k,v in r.items() if k not in ('same_model_full_score_replays','rankings','native_platform_exports')},indent=2))
