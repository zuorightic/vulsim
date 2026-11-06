"""Nine-case D static requirements: shared production candidates, no physical labels."""
import argparse
from collections import Counter,defaultdict
import hashlib
import itertools
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
CASES=('MAC_32','DOT2_16','UDR_16','DIVSEL_32','F1','F2','H_M_32','H_D_32','H_F1')


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def unpack(words):return sum(int(w,16)<<(64*i) for i,w in enumerate(words))


def prepare(folder):
    from .case_generator import generate_manifest
    from .contracts import fixed_latency
    source_manifest=ROOT/'build/step7-native-state-20261105/checks-v5/cases.json'
    previous={c['name']:c for c in read(source_manifest)['cases']}
    definitions={c['id']:c for c in generate_manifest()['cases']}
    sources=ROOT/'experiments/arithmetic/evidence/step7_m2_native_integration_v1/public-source'
    rows=[];reference={}
    for name in CASES:
        c=dict(previous[name]);source=Path(c['source'])
        if sha(source)!=c['generated_source_sha256']:raise ValueError('public generated source differs: '+name)
        if c['N']+1!=fixed_latency(definitions[name]):raise ValueError('public source latency mismatch')
        local=folder/'sources'/(name+'.cpp');local.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,local);c['source']=str(local.resolve())
        c['source_label']=str(ROOT/'build/step7-d-interface-20261105/public-nine-v1/generated'/name/'sim/top.logic.cpp.pipeline_core.cpp')
        for filename,h in c['public_VUL_source_sha256'].items():
            src=sources/name/filename
            if sha(src)!=h:raise ValueError('public VUL source differs')
            dst=folder/'public-source'/name/filename;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        rows.append(c);reference[name]={'L':fixed_latency(definitions[name]),'reference_graph':definitions[name]['reference_graph'],
            'required_labels':sorted({n['primitive'] for n in definitions[name]['reference_graph'] if n['primitive']})}
    write(folder/'cases.json',{'cases':rows,'PPA_calls':0,'source_role':'public_graph_static_requirements_only'})
    write(folder/'reference-requirements.json',{'version':'asap7-m2-target-reference-requirements-v1',
        'rules_sha256':sha(ROOT/'experiments/arithmetic_dse/configs/target_rules_v2.json'),'cases':reference,
        'unique_labels':sorted({key for c in reference.values() for key in c['required_labels']}),
        'numerical_targets_frozen':False,'D_ref_ps':None,'H_ref_ps':None,'T_target_ps':None,
        'missing':['audited same-platform grt reference labels for complete primitive list','joint boundary/IO accounting and qualified H_ref'],
        'prohibitions':['no model prediction or formal/holdout whole-graph PPA as reference labels',
            'no 1500ps diagnostic period promoted to target','no state-bank overhead promoted to joint H_ref'],
        'PPA_calls':0})


def reset_supported(reset,mask,width):
    if reset&~mask:return False
    bits=[(reset>>b)&1 for b in range(width) if (mask>>b)&1]
    if not any(bits) or all(bits):return True
    return any(all(x==int((b+phase)%mod==0) for b,x in enumerate(bits)) for mod in (2,3) for phase in range(mod))


def state_requirements(query,sources,domain):
    """Independent, accumulating diagnostic; never changes production acceptance."""
    failures=defaultdict(list);slots=query['slots'];data=[s for s in slots if not s['valid']]
    captures=query['internal_stages']+int(query['external_outputs_included'])
    if captures>domain['max_capture_stage']:failures['capture_stage_capacity'].append(captures)
    for feature,limit in [('state_bits','max_state_bits'),('state_signals','max_state_signals')]:
        if query['features'][feature]>domain[limit]:failures[limit].append(query['features'][feature])
    if query['input_variable_bits']>domain['max_input_bits']:failures['max_input_bits'].append(query['input_variable_bits'])
    chains=defaultdict(list)
    for slot in data:
        origin=str(slot['origin']);info=sources[origin];mask=unpack(slot['variable_mask_hex']);reset=unpack(slot['reset_hex']);width=slot['declared_width']
        if mask.bit_count()!=slot['variable_bits'] or mask>>width:raise ValueError('invalid exported state mask')
        if width not in domain['word_widths'] or not slot['variable_bits']:failures['data_width_or_mask'].append(slot['origin'])
        if not reset_supported(reset,mask,width):failures['semantic_reset_pattern'].append(slot['origin'])
        if unpack(info['known_one_hex']):failures['known_one_data'].append(slot['origin'])
        zeros=[b for b in range(width) if not (mask>>b)&1]
        high_padding=mask==(1<<slot['variable_bits'])-1
        if not high_padding and len(zeros)!=1:failures['known_zero_pattern'].append(slot['origin'])
        if slot['enable_stage']!=slot['stage']-1:failures['enable_protocol'].append(slot['origin'])
        chains[info['channel_root']].append(slot)
    if len(chains)>domain['max_parallel_words']:failures['max_parallel_words'].append(len(chains))
    roots={};full=False
    for root,chain in chains.items():
        chain.sort(key=lambda s:s['stage']);first=chain[0]
        if [s['stage'] for s in chain]!=list(range(first['stage'],first['stage']+len(chain))):failures['channel_overlap_or_lifetime'].append(root)
        if len({(s['declared_width'],tuple(s['variable_mask_hex'])) for s in chain})>1:failures['channel_shape_change'].append(root)
        full|=chain[0]['stage']==1 and chain[-1]['stage']==captures
        info=sources[str(first['origin'])];leaves=set(info['input_sources'])
        for previous,old in roots.items():
            common=leaves&old
            if common:failures['dependent_channels'].append({'roots':[previous,root],'shared_inputs':sorted(common)})
        roots[root]=leaves
    if not full:failures['no_full_channel_chain'].append(True)
    valid=[s for s in slots if s['valid']]
    valid_origins={s['origin'] for s in valid}
    for root,leaves in roots.items():
        if leaves&valid_origins:failures['data_depends_on_valid'].append(root)
    if any(unpack(s['reset_hex']) for s in valid):failures['valid_reset'].append(True)
    return {k:v for k,v in sorted(failures.items())}


def analyze(folder):
    index=read(folder/'native/index.json');parent=read(ROOT/'experiments/arithmetic/evidence/step7_m2_native_integration_v1/public-nine/coverage.json')
    historical={c['case']:c for c in parent['cases']};state=read(ROOT/'experiments/arithmetic/evidence/step7_native_state_v1/asap7-native-state.json')
    cap=read(folder/'native/K16.json')
    if cap['K']!=16 or cap['unique']!=16 or cap['candidate_order']!=['candidate/'+('/'.join(x)) for x in list(itertools.product(('original','half','quarter'),repeat=4))[:16]]:
        raise ValueError('production K16 ordering differs from independent registry enumeration')
    cases=[];all_faults=Counter();stage_shapes={};interval_sets={};interval_envelope={};operations=Counter();envelopes=defaultdict(float);ranges={};word_widths=set();masks={}
    if [c['case'] for c in index['cases']]!=list(CASES) or index['candidate_count']!=21 or index['PPA_calls']:raise ValueError('wrong static candidate scope')
    for case in index['cases']:
        expected=historical[case['case']]
        if [c['id'] for c in case['candidates']]!=expected['candidate_order']:raise ValueError('production candidate order changed')
        if not case['production_C_shape_parity_checked'] or case['production_C_candidate_order']!=expected['candidate_order']:
            raise ValueError('shared enumeration not checked against production C selection')
        old=read(ROOT/'experiments/arithmetic/evidence/step7_m2_native_integration_v1/public-nine'/expected['report'])
        old_shapes={c['id']:c['shape_sha256'] for c in old['selection']['candidates']}
        candidate_rows=[]
        for candidate in case['candidates']:
            path=folder/'native'/candidate['file']
            if sha(path)!=candidate['sha256']:raise ValueError('native candidate artifact changed')
            if candidate['shape_sha256']!=old_shapes[candidate['id']]:raise ValueError('production graph shape changed')
            d=read(path);nodes={n['id']:n for n in d['nodes']};counts=Counter(n['operation'] for n in nodes.values() if not n['constant'] and n['operation'] not in ('wire','input'))
            for region in d['regions']:
                if region['template']!='mul-block-tree-v1':continue
                group_of={node:i for i,group in enumerate(region['legal_cut_groups']) for node in group}
                dependencies={(group_of[a['node']],group_of[node]) for node in group_of for a in nodes[node]['operands']
                    if a['kind']=='symbol' and a['node'] in group_of and group_of[a['node']]!=group_of[node]}
                n=len(region['legal_cut_groups'])
                if not all((g,g+1) in dependencies for g in range(n-1)):
                    raise ValueError('interval envelope needs general group DAG analysis; registered level chain changed')
                # Every legal placement of this chain is nondecreasing. The
                # envelope deliberately keeps all such group assignments;
                # whole-graph ports/dependencies may further restrict them.
                for assignment in itertools.combinations_with_replacement(range(d['L']),n):
                    for at in set(assignment):
                        group_ids=[g for g in range(n) if assignment[g]==at]
                        key=json.dumps([sorted(region['parameters'].items()),group_ids],sort_keys=True)
                        interval_envelope.setdefault(key,{'parameters':region['parameters'],'groups':group_ids,'contiguous':True,
                            'ordered_chain_proven_from_actual_group_dependencies':True,
                            'scope':'conservative envelope over monotone stage assignments; graph boundary checks still required'})
            operations.update(counts);fault_counts=Counter();stage_families=Counter();template_ranges=[];view_faults=[]
            for view in d['views']:
                placement=view['placement'];query=view['state']['query'];faults=state_requirements(query,d['state_source_info'],state['domain'])
                view_faults.append({'layout_sha256':query['layout_sha256'],'roles':view['roles'],'conditions':faults})
                for k in faults:fault_counts[k]+=1;all_faults[k]+=1
                for k,v in query['features'].items():
                    envelopes[k]=max(envelopes[k],v);bounds=ranges.setdefault(k,[v,v]);bounds[0]=min(bounds[0],v);bounds[1]=max(bounds[1],v)
                for slot in query['slots']:
                    if slot['valid']:continue
                    word_widths.add(slot['declared_width']);mask=unpack(slot['variable_mask_hex'])
                    masks.setdefault((slot['declared_width'],mask),{'declared_width':slot['declared_width'],'variable_bits':slot['variable_bits'],
                        'variable_mask_hex':slot['variable_mask_hex']})
                envelopes['input_variable_bits']=max(envelopes['input_variable_bits'],query['input_variable_bits'])
                for stage in view['stages']:
                    at=stage['index'];members=[nodes[n] for n in stage['semantic_members'] if n in nodes and not nodes[n]['constant'] and nodes[n]['operation'] not in ('wire','input')]
                    hist=Counter(n['operation'] for n in members)
                    family='wiring_only' if not members else 'single_atom' if len(members)==1 else 'mux_arithmetic' if hist['mux'] else 'arithmetic_composition'
                    stage_families[family]+=1
                    paid={n['id']:i for i,n in enumerate(members)}
                    def upstream(node,seen):
                        if node in seen:return set()
                        seen=seen|{node}
                        if placement[node]!=at:return set()
                        if node in paid:return {node}
                        if node not in nodes:return set()
                        return set().union(*(upstream(a['node'],seen) for a in nodes[node]['operands'] if a['kind']=='symbol'))
                    edges=sorted({(paid[parent],paid[n['id']]) for n in members for a in n['operands'] if a['kind']=='symbol'
                        for parent in upstream(a['node'],set())})
                    signature=json.dumps({'operations':sorted((n['operation'],n['width']) for n in members),
                        'connectivity':edges,'ordered_node_shapes':[(n['operation'],n['width']) for n in members],
                        'capture_widths':sorted((c['declared_width'],c['banks']) for c in stage['captures'])},sort_keys=True)
                    shape=stage_shapes.setdefault(signature,{'family':family,'operations':dict(hist),'operation_widths':sorted({(n['operation'],n['width']) for n in members}),
                        'connectivity':edges,'ordered_node_shapes':[(n['operation'],n['width']) for n in members],
                        'capture_widths':sorted((c['declared_width'],c['banks']) for c in stage['captures']),'occurrences':0,'requires_topology_qualification':True})
                    shape['occurrences']+=1
                    for r in d['regions']:
                        if r['template']!='mul-block-tree-v1':continue
                        group_ids=[g for g,group in enumerate(r['legal_cut_groups']) if group and placement[group[0]]==at]
                        if not group_ids:continue
                        contiguous=group_ids==list(range(group_ids[0],group_ids[-1]+1));parameters=r['parameters']
                        key=json.dumps([sorted(parameters.items()),group_ids],sort_keys=True)
                        interval_sets.setdefault(key,{'parameters':parameters,'groups':group_ids,'contiguous':contiguous,'occurrences':0})['occurrences']+=1
                        template_ranges.append(contiguous)
            primitive=d['primitive_C_final_coverage'];reasons=Counter(n['reason'] for n in primitive['nodes'] if n['status']=='cost_uncovered')
            candidate_rows.append({'id':candidate['id'],'shape_sha256':candidate['shape_sha256'],'views':len(d['views']),
                'operations':dict(counts),'state_uncovered_conditions':dict(fault_counts),'stage_families':dict(stage_families),
                'view_state_conditions':view_faults,
                'template_stage_sets':len(template_ranges),'noncontiguous_template_stage_sets':sum(not c for c in template_ranges),
                'primitive_C_final_uncovered_reasons':dict(reasons),'actual_C_final_state_materialization_checked':d['actual_C_final_state_materialization_checked']})
        cases.append({'case':case['case'],'L':case['L'],'candidates':candidate_rows})
    result={'version':'asap7-D-static-gap-audit-v1','status':'static_audit_complete','cases':cases,
        'candidate_count':index['candidate_count'],'view_count':index['view_count'],'illegal_move_proposals':index['illegal_move_proposals'],
        'state_condition_view_counts':dict(all_faults),'state_feature_maxima':dict(envelopes),'state_feature_ranges':ranges,
        'observed_state_word_widths':sorted(word_widths),'observed_state_masks':list(masks.values()),'semantic_operation_inventory':dict(operations),
        'stage_shape_count':len(stage_shapes),'stage_shapes':list(stage_shapes.values()),'template_group_sets':list(interval_sets.values()),
        'template_interval_envelope':list(interval_envelope.values()),
        'placement_scope':index['placement_scope'],'production_C_graph_and_order_parity':True,'independent_K16_order_checked':True,
        'all_future_D_placements_covered':False,'PPA_calls':0,'formal_targets_frozen':False,'full_D_ready':False}
    write(folder/'gap-audit.json',result)
    references=read(folder/'reference-requirements.json')
    if len(references['unique_labels'])!=17 or references['numerical_targets_frozen']:
        raise ValueError('reference requirements or role changed')
    write(folder/'next-protocol.json',{'version':'asap7-m2-joint-model-requirements-v1',
        'status':'static_requirements_and_accounting_frozen_measurement_admission_pending',
        'static_audit_sha256':sha(folder/'gap-audit.json'),'reference_requirements_sha256':sha(folder/'reference-requirements.json'),
        'current_delivery':'ASAP7 nine cases /36 final A-B-C-D records','other_platforms_deferred':True,
        'policy':{'K':16,'same_ordered_C_D_candidates':True,'search_PPA_calls':0,'Div_FP_remain_atomic':True},
        'physical_identity':{'platform':'asap7','stage':'grt','ABC_ps':1500,'IO':'0.2T on declared external path classes',
            'diagnostic_SDC_ps':1500,'diagnostic_SDC_is_formal_target':False},
        'target_reference':{'rules':'target_rules_v2','required_labels':references['unique_labels'],
            'D_ref':'same-platform grt microbenchmark labels on original graph longest dependency path',
            'H_ref':'qualified joint boundary with explicit nonoverlapping clock/setup/uncertainty/IO terms',
            'state_bank_803ps_is_joint_H_ref':False,'reference_settings_frozen':False,'reference_labels_complete':False,
            'numerical_targets_frozen':False,'formal_PPA_or_model_predictions_as_reference':False},
        'cost_ownership':{
            'whole_stage':'all owned functional combination and internal data-net repair, one stage price; no additive node prices',
            'template_interval':'real blocked-Mul leaf/reduction interval price when explicitly consumed; not ordinary Mul and not charged again inside owning whole-stage price',
            'native_state':'deduplicated logical data/valid chains and owned hold/reset/control overhead; explicit external capture inclusion',
            'input_service_wrapper':'separate explicit query/owner; not zero and not silently included in core bank',
            'clock_tap_and_unassigned_repair':'one shared physical owner; isolated bank labels include these, so joint stage labels must exclude or reconcile them',
            'boundary_time':'clkQ/setup/skew/uncertainty once; Q-D label excludes these; IO only for actual external path class',
            'unattributed_cells_or_paths':'block label acceptance; never silently ignore',
            'physical_label_partition_implemented_and_verified':False},
        'work_packages':[
            {'id':'R','scope':'freeze reference microbenchmark source/settings and capacity, collect17 label keys plus joint boundary evidence; freeze D_ref/H_ref/targets before model target grid',
             'depends_on':['static_requirements','physical_label_partition_and_reference_preflight']},
            {'id':'S','scope':'native synthetic banks with general reset distributions, related sources, no-full-chain layouts, shifted zero-padding and needed nonpower intermediate widths',
             'observed_word_widths':result['observed_state_word_widths'],'observed_feature_ranges':ranges,
             'old_coefficients':'immutable baseline candidate; no automatic refit or domain extension','depends_on':['R']},
            {'id':'G','scope':'independent bounded synthetic whole-stage topology model; single atoms/serial/mux/multiple branches and exits; joint state/boundary qualification',
             'formal_or_holdout_graphs_copied_into_training':False,'depends_on':['R','physical_label_partition_and_reference_preflight']},
            {'id':'I','scope':'real half/quarter intervals; retain old failure and test exclusion; reuse matching train/validation only',
             'observed_group_sets':len(interval_sets),'observed_noncontiguous_group_sets':sum(not x['contiguous'] for x in interval_sets.values()),
             'conservative_monotone_group_interval_envelope':len(interval_envelope),
             'observed_sets_exhaust_all_future_D_positions':False,'depends_on':['R']},
            {'id':'C','scope':'whole-stage consumer ownership; initial/trial/final complete queries, safe partial-stage bounds, unified budget and typed state validation',
             'can_progress_while_collection_runs':True,'formal_D_release_depends_on':['S','G','I','joint_boundary_qualification']},
            {'id':'F','scope':'all-candidate D coverage, actual selection and RTL transaction/reset/L-II closure, then freeze36 final physical jobs and step9 audit',
             'depends_on':['C','qualified_joint_domains']}],
        'independence':{'all_previous_consumed_tests_excluded':True,'same_source_all_clock_and_stage_variants_one_split':True,
            'new_train_validation_sources_and_test_lock_before_collection':True,'freeze_parameters_domain_reserve_before_independent_test':True,
            'quality_gates_changed':False,'no_formal_or_holdout_PPA_for_fitting_or_target_feedback':True},
        'resources':{'parallel_jobs':4,'threads_per_job':4,'memory_limit_MiB':8192,'shared_ledger':True,'automatic_retries':0},
        'physical_admission_allowed':False,'missing_for_admission':['executable synthetic sources and complete task/split manifests',
            'raw cell/path ownership extractor and software preflight','reference settings/capacity and exact tasks/budget/storage reservation'],
        'full_D_ready':False,'formal_36_complete':False,'PPA_calls':0})
    print(json.dumps({k:result[k] for k in ('status','candidate_count','view_count','state_condition_view_counts','state_feature_maxima','stage_shape_count','PPA_calls','full_D_ready')}),flush=True)
    return result


def run(folder,build):
    from .budget import Ledger
    from .model_m2_cec import leaf
    folder.mkdir(parents=True,exist_ok=False);ledger=Ledger();context={'target_platform':'asap7','admission_id':folder.name,'task_id':'D-all-candidate-static-requirements'}
    with ledger.job(context):
        commands=[('prepare',[sys.executable,'-B','-m','experiments.arithmetic_dse.model_d_requirements','prepare','--folder',str(folder)],300),
            ('configure',['cmake','-S',str(ROOT/'rtlzz'),'-B',str(build),'-DCMAKE_BUILD_TYPE=Release'],300),
            ('build',['cmake','--build',str(build),'--target','arithmetic-d-requirements-export','arithmetic-published-primitives-test','arithmetic-composite-state-test','-j4'],1800),
            ('native',[str(build/'testv2/arithmetic-d-requirements-export'),str(ROOT),str(folder/'cases.json'),str(folder/'native')],1200),
            ('analyze',[sys.executable,'-B','-m','experiments.arithmetic_dse.model_d_requirements','analyze','--folder',str(folder)],300)]
        for name,cmd,timeout in commands:
            leaf(cmd,folder,name,timeout,ledger,context);print((folder/(name+'.log')).read_text()[-3500:],flush=True)
    write(folder/'resource-summary.json',ledger.summary())


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','analyze','run'));p.add_argument('--folder',type=Path,required=True)
    p.add_argument('--build',type=Path,default=ROOT/'build/step4-rtlzz');a=p.parse_args();folder=a.folder.resolve()
    if a.action=='prepare':prepare(folder)
    elif a.action=='analyze':analyze(folder)
    else:run(folder,a.build.resolve())
