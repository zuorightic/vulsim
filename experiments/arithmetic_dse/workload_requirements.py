"""Aggregate W1 needs from actual W2 inventories; never grant a support domain."""
from collections import Counter
import gzip
import json
from pathlib import Path
from .workload_contracts import load


def collect(roots):
    expected = {c['id']: c for c in load()['cases']}
    cases, families = [], {}
    for root in map(Path, roots):
        record = json.loads((root / 'inventory.json').read_text())
        case = record['case']
        if case != expected[case['id']]:
            raise ValueError('case contract/structure budget changed; explicit successor required')
        counts, gaps = Counter(), Counter()
        scale = dict(input_service_data_bits=0, native_data_bits=0, native_words=0,
                     max_word_bits=0, max_parallel_words=0, external_data_bits=0,
                     G_output_bits=0, G_terms=0)
        for structure in record['structures']:
            counts['structures'] += 1
            if structure['status'] != 'software_exported':
                gaps[structure['status']] += 1
                continue
            counts['software_exported'] += 1
            counts['cycles'] += sum(v['cycles'] for v in structure.get('functional', []))
            dest = root / structure['directory']
            # Count each actual placement once, not once for every numeric T.
            demand = json.loads(gzip.decompress((dest / structure['demand_files'][0]).read_bytes()))
            for view in demand['views']:
                counts['placements'] += 1
                state = view['state']
                for key in ('input_service_data_bits','native_data_bits','native_words','max_word_bits','external_data_bits'):
                    scale[key] = max(scale[key], state[key])
                scale['max_parallel_words'] = max(scale['max_parallel_words'], max(state['parallel_words_by_stage'].values(), default=0))
                counts['functional_logic_needing_price'] += len(view['functional_logic_needing_separate_price'])
                for row in view['operators']:
                    counts['operator_queries'] += 1
                    counts['represented_predecessor_ABI'] += row['interface_status'] == 'represented'
                    gaps.update(row['interface_gaps'])
                    p = row['query']['local_context']['producer']
                    family = 'add' if p['operation'] in ('add','adc') else 'sub' if p['operation'] in ('sub','sbb') else 'compare' if p['operation'] in ('ult','ule','eq') else p['operation']
                    f = families.setdefault(family, dict(provider='operator_function_successor', queries=0, numeric_ranges={}))
                    f['queries'] += 1
                    for key in ('lhs_width','rhs_width','arithmetic_width','value_width','result_width'):
                        lo,hi = f['numeric_ranges'].get(key, [p[key],p[key]])
                        f['numeric_ranges'][key] = [min(lo,p[key]),max(hi,p[key])]
                for r in view['G']['regions']:
                    counts['proposed_G_regions'] += 1
                    counts['represented_G_geometry'] += r['geometry_status'] == 'represented'
                    scale['G_output_bits'] = max(scale['G_output_bits'],r['output_bits'])
                    scale['G_terms'] = max(scale['G_terms'],len(r['terms']))
        cases.append(dict(id=case['id'], targets=case['formal_targets'], counts=dict(counts),
                          maximum_observed_software_scale=scale, predecessor_ABI_gaps=dict(gaps),
                          price_qualification_granted=False))
    if {c['id'] for c in cases} != set(expected) or len(cases) != len(expected):
        raise ValueError('nine distinct application inventories required')
    return dict(version='nine-workload-observed-requirements-v1', cases=cases,
                operator_families=families, one_provider_per_family_across_widths=True,
                numeric_ranges_are_audit_only_not_support_or_shape_whitelist=True,
                new_model_sources_admitted=0, independent_labels_read=False,
                new_EDA_calls=0, full_D_ready=False)
