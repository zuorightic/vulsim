"""Prospective wide-load successor: representative sources, guarded multi-T scan.

Old source roles, physical products, sampler and evidence remain unchanged.
No candidate/view ID is a predictor or a measured-price lookup key.
"""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import math
from pathlib import Path
import shutil
from types import FunctionType, SimpleNamespace

from .model_fast_preflight import read, write, sha, key
from . import operator_collection as parent
from . import operator_stage4 as stages
from . import model_three_region_scan as scan
from . import model_sampling_v2 as samples
from .budget import Ledger, usage

ROOT = Path(__file__).resolve().parents[2]
POLICY = Path(__file__).with_name('configs')/'operator_wide_sampling_v1.json'
FIT_PROTOCOL = Path(__file__).with_name('configs')/'operator_condition_fit_v2.json'
FEATURE_PROTOCOL = Path(__file__).with_name('configs')/'operator_condition_features_v2.json'
AXES = ('lhs_width', 'rhs_width', 'result_width', 'lhs_zero_count', 'rhs_zero_count',
        'consumer_lhs_max', 'consumer_rhs_max', 'consumer_result_max', 'operand0_bindings',
        'operand1_bindings', 'mapped_zero_bits', 'mapped_undemanded_bits', 'mapping_shift_min', 'mapping_shift_max')


def validate_policy(policy):
    if policy.get('version')!='operator-wide-load-sampling-v1':
        raise ValueError('unknown wide sampling policy')
    guards=policy.get('new_source_guard_targets_ps',{})
    if set(guards)!={'train','validation','locked_test'}:
        raise ValueError('wide guard role inventory differs')
    base=scan.policy()
    for role,targets in guards.items():
        if (not isinstance(targets,list) or not targets or len(targets)>13 or
                any(type(t) is not int or not base['minimum_ps']<=t<=base['maximum_ps'] for t in targets)
                or len(set(targets))!=len(targets)):
            raise ValueError('invalid or duplicate clock guard')
        if not {500,1500,3000}<=set(targets):
            raise ValueError('missing preregistered clock guard')
    reserved=policy.get('fitting_reserved_exact_targets_ps')
    if reserved!=[1000] or any(1000 in guards[r] for r in ('train','validation')) or 1000 not in guards['locked_test']:
        raise ValueError('reserved interpolation target leaks into fitting guards')
    return policy


def guarded_next(rows, role, cfg):
    policy = validate_policy(read(POLICY))
    if len(rows) >= 13 or any(r['status'] == 'failed' for r in rows):
        return None
    used = {r['SDC_ps'] for r in rows}
    for target in policy['new_source_guard_targets_ps'][role]:
        if target not in used:
            return dict(SDC_ps=target, ABC_ps=target, proposal='required_domain_clock_probe', reference_ratio=None)
    q = scan._next(rows, role, cfg)
    if not q or role == 'locked_test' or q['SDC_ps'] not in policy['fitting_reserved_exact_targets_ps']:
        return q
    for delta in range(1, 17):
        for sign in (1, -1):
            target = q['SDC_ps'] + sign*delta
            if (target not in used and target not in policy['fitting_reserved_exact_targets_ps'] and
                    cfg['minimum_ps'] <= target <= cfg['maximum_ps'] and all(
                    scan.number(abs(target-t))/min(target,t) >= scan.number(cfg['minimum_relative_target_separation']) for t in used)):
                return dict(q, SDC_ps=target, ABC_ps=target, proposal='reserved_target_nudge')
    return None


def wide_decide(rows, source_id, role):
    namespace = dict(scan.decide.__globals__)
    namespace['_next'] = guarded_next
    decide = FunctionType(scan.decide.__code__, namespace)
    result = decide(rows, source_id, role, scan.policy())
    guards = read(POLICY)['new_source_guard_targets_ps'][role]
    completed = {r['SDC_ps'] for r in rows if r['status']=='completed'}
    result['required_clock_guards_ps'] = guards
    result['missing_clock_guards_ps'] = [t for t in guards if t not in completed]
    return result


def adapter(folder):
    manifest = read(folder/'manifest.json')
    if manifest['successor_sampling_policy_sha256'] != sha(POLICY):
        raise ValueError('wide-load sampling policy changed')
    new_ids = {r['id'] for r in manifest['sources'] if r.get('sampling_policy') == 'operator-wide-load-sampling-v1'}
    def decide(rows, source_id, role):
        return (wide_decide if source_id in new_ids else scan.decide)(rows, source_id, role)
    proxy_scan = SimpleNamespace(CONFIG=scan.CONFIG, decide=decide)
    namespace = dict(parent.next_request.__globals__)
    namespace['scan'] = proxy_scan
    original_next = FunctionType(parent.next_request.__code__, namespace)
    def next_request(folder,source_id,history,selection_freeze=None):
        row=next(r for r in manifest['sources'] if r['id']==source_id)
        if row['role']=='locked_test':
            verify_selection(folder,selection_freeze)
        return original_next(folder,source_id,history,selection_freeze)
    namespace = dict(parent.execute_next.__globals__)
    namespace.update(next_request=next_request, scan=proxy_scan)
    execute_next = FunctionType(parent.execute_next.__code__, namespace)
    return SimpleNamespace(next_request=next_request, execute_next=execute_next,
                           descriptor=parent.descriptor, operator_query=parent.operator_query)


def verify_selection(folder, selection):
    if selection is None:
        raise ValueError('locked test needs a complete implementation freeze')
    root=folder.parent
    if (root/'independent-evaluation-consumed.json').exists():
        raise ValueError('independent test already consumed')
    freeze=read(selection)
    if (freeze.get('validation_passed') is not True or freeze.get('test_consumed') is not False or
            freeze.get('source_manifest_sha256')!=sha(folder/'manifest.json') or
            freeze.get('fit_dataset_sha256')!=sha(root/'fit-data.json')):
        raise ValueError('test source/dataset/validation freeze differs')
    sources=freeze.get('implementation_sources',{})
    required=set(read(FIT_PROTOCOL)['required_freeze_sources'])
    if not required<=set(sources):
        raise ValueError('incomplete test implementation freeze')
    if not freeze.get('fit_producer') or freeze['fit_producer'] not in sources:
        raise ValueError('fit producer is not included in test freeze')
    for name,h in sources.items():
        path=Path(name)
        if path.is_absolute() or '..' in path.parts or sha(ROOT/path)!=h:
            raise ValueError('frozen test implementation changed: '+name)
    def bound_file(name):
        ref=Path(freeze[name]);return ref if ref.is_absolute() else selection.parent/ref
    model_path=bound_file('model_path');validation_path=bound_file('validation_path')
    if sha(model_path)!=freeze['model_sha256'] or sha(validation_path)!=freeze['validation_sha256']:
        raise ValueError('test candidate or validation receipt changed')
    model=read(model_path);validation=read(validation_path);manifest=read(folder/'manifest.json')
    if (model.get('version')!='operator-condition-function-v1' or model.get('quality_status')!='awaiting_independent'
            or model.get('source_manifest_sha256')!=freeze['source_manifest_sha256']
            or model.get('fit_dataset_sha256')!=freeze['fit_dataset_sha256']
            or model.get('profile_sha256')!=manifest['profile_sha256']
            or model.get('feature_protocol_sha256')!=sha(FEATURE_PROTOCOL)
            or model.get('fit_protocol_sha256')!=sha(FIT_PROTOCOL) or freeze.get('fit_protocol_sha256')!=sha(FIT_PROTOCOL)
            or model.get('full_D_ready') is not False or set(model.get('operations',{}))!={'mul','add'}
            or any(e.get('status')!='awaiting_independent' for e in model['operations'].values())
            or validation.get('status')!='passed' or validation.get('model_sha256')!=freeze['model_sha256']
            or validation.get('source_manifest_sha256')!=freeze['source_manifest_sha256']):
        raise ValueError('candidate quality/feature scope or validation receipt differs')
    if (root/'collection.json').exists():
        ancestor=read(root/'collection.json').get('parent_collection_root')
        if ancestor and (Path(ancestor)/'independent-evaluation-consumed.json').exists():
            raise ValueError('inherited independent sources already consumed')


def validate_sampler_proof(proof):
    if (proof.get('version')!='wide-guarded-sampler-proof-v2' or proof.get('status')!='passed' or
            proof.get('producer_sha256')!=sha(Path(__file__)) or proof.get('policy_sha256')!=sha(POLICY) or
            proof.get('parent_sampler_sha256')!=sha(Path(scan.__file__)) or
            proof.get('parent_sampler_policy_sha256')!=sha(scan.CONFIG) or proof.get('new_EDA_calls')!=0):
        raise ValueError('sampler proof producer/policy identity differs')
    cases=proof.get('cases',[])
    if len(cases)!=3 or {r['role'] for r in cases}!={'train','validation','locked_test'}:
        raise ValueError('sampler proof role coverage incomplete')
    expected={'forged_history_'+r for r in ('train','validation','locked_test')}|{
        'first_failure_stops_'+r for r in ('train','validation','locked_test')}|{
        'duplicate_guard','reserved_fit_target','invalid_guard','missing_test_interpolation'}
    negative=proof.get('negative_checks',[])
    if len(negative)!=len(expected) or set(negative)!=expected:
        raise ValueError('sampler refusal proof incomplete')
    policy=validate_policy(read(POLICY))
    for case in cases:
        targets=case['targets'];guards=policy['new_source_guard_targets_ps'][case['role']]
        if (not isinstance(targets,list) or len(targets)>13 or targets[:len(guards)]!=guards or
                len(set(targets))!=len(targets) or
                (case['role']!='locked_test' and 1000 in targets)):
            raise ValueError('sampler proof clock coverage differs')


def validate_admission(root):
    verify_measurement_sources(root)
    pointer=read(root/'active-software-admission.json')
    relative=Path(pointer['path'])
    if relative.is_absolute() or '..' in relative.parts:raise ValueError('invalid admission reference')
    path=root/relative
    if sha(path)!=pointer['sha256']:
        raise ValueError('software admission changed')
    admission=read(path)
    if (admission.get('version')!='wide-source-software-admission-v2' or admission['status']!='passed' or
            admission['source_manifest_sha256']!=sha(root/'corpus/manifest.json') or
            admission['sampler_policy_sha256']!=sha(POLICY) or admission['producer_sha256']!=sha(Path(__file__)) or
            admission['source_generator_sha256']!=sha(Path(samples.__file__)) or
            admission.get('fit_protocol_sha256')!=sha(FIT_PROTOCOL) or admission.get('feature_protocol_sha256')!=sha(FEATURE_PROTOCOL)):
        raise ValueError('wide-load source software admission missing or changed')
    if admission['sampler_proof'] not in admission['proof_files']:raise ValueError('sampler proof not bound')
    expected,count=bank_proof(root,Path(admission['bank_software_folder']),Path(admission['bank_work']),
                              Path(admission['sampler_proof']),Path(admission['sampler_command_receipt']))
    if admission['proof_files']!=expected or admission.get('software_sources')!=count or admission.get('cycles_each')!=128:
        raise ValueError('wide-load software proof inventory incomplete or changed')
    return admission


def verify_measurement_sources(root):
    cfg=stages.verify_sources(root)
    required=set(parent.measurement_sources())|{str(p.relative_to(ROOT)) for p in (
        Path(__file__),POLICY,FEATURE_PROTOCOL,FIT_PROTOCOL,Path(stages.__file__))}
    if not required<=set(cfg['measurement_sources']):
        raise ValueError('successor freeze omits runtime or protocol producers')
    if cfg.get('fit_protocol_sha256')!=sha(FIT_PROTOCOL) or cfg.get('feature_protocol_sha256')!=sha(FEATURE_PROTOCOL):
        raise ValueError('successor feature/fit protocol not frozen')
    return cfg


def run(root, mode='fitting', selection=None, max_batches=None, pilot=None):
    validate_admission(root)
    proxy = adapter(root/'corpus')
    namespace = dict(stages.decisions.__globals__)
    namespace['collect'] = proxy
    all_decisions = FunctionType(stages.decisions.__code__, namespace)
    if pilot:
        requested=read(pilot)['requests']
        if mode!='fitting' or not 1<=len(requested)<=3:
            raise ValueError('qualification pilot permits one to three fitting requests')
        expected={(r['source_id'],r['SDC_ps']) for r in requested}
        if len(expected)!=len(requested):raise ValueError('duplicate qualification pilot request')
        def decisions(root,roles,selection):
            pending=all_decisions(root,roles,selection)
            chosen=[item for item in pending if (item[1]['id'],item[3]['SDC_ps']) in expected]
            # Return the full remaining inventory after the bounded pilot, so
            # the inherited controller records bounded completion honestly.
            return chosen or pending
        max_batches=1
        first=decisions(root,['train','validation'],selection)
        if {(r['id'],q['SDC_ps']) for _,r,_,q in first}!=expected:
            raise ValueError('pilot differs from actual deterministic next requests')
    else:
        decisions=all_decisions
    namespace = dict(stages.run.__globals__)
    namespace.update(collect=proxy, decisions=decisions)
    execute = FunctionType(stages.run.__code__, namespace)
    return execute(root, mode, selection, max_batches)


def prepare(parent_root, witness, root):
    if root.exists():
        raise ValueError('preserve previous wide-load successor')
    old_cfg = stages.verify_sources(parent_root)
    if read(parent_root/'progress.json')['phase'] != 'fitting_collection_complete':
        raise ValueError('settled fitting parent required')
    old_manifest = read(parent_root/'corpus/manifest.json')
    old_roles = {r['source_group']: r['role'] for r in old_manifest['sources']}
    report = read(witness)
    local = {}
    for view in report['runs'][1]['candidates']:
        for node in view['node_prices']:
            features = parent.canonical_features(node['descriptor']['local_context'])
            signature = key(features)
            if features['consumers'] and signature not in old_roles:
                samples.geometry_contract(features)
                row = dict(id='s'+signature[:16], source_group=signature, features=features,
                           boundary_policy='unsigned-op-hierarchy-v1', sampling_policy='operator-wide-load-sampling-v1')
                row['vector'] = [parent.operator_query.features(parent.descriptor(row,1500))[n] for n in AXES]
                local[signature] = row
    from regression.arithmetic_target_round1 import capacity_sources
    forbidden = {key(parent.canonical_features(r['features'])) for r in capacity_sources()}
    if set(local) & forbidden:
        raise ValueError('diagnostic context must retain its excluded role')
    new = []
    for op in ('mul','add'):
        candidates = sorted([r for r in local.values() if r['features']['producer']['operation']==op], key=lambda r:r['source_group'])
        original_train = [r for r in old_manifest['sources'] if r['role']=='train' and r['features']['producer']['operation']==op]
        train_vectors = [[parent.operator_query.features(parent.descriptor(r,1500))[n] for n in AXES] for r in original_train]
        all_vectors = train_vectors+[r['vector'] for r in candidates]
        scales = [max(1.,max(v[i] for v in all_vectors)-min(v[i] for v in all_vectors)) for i in range(len(AXES))]
        def distance(a,b):
            return math.sqrt(sum(((x-y)/s)**2 for x,y,s in zip(a,b,scales,strict=True)))
        def novelty(row, vectors, k=1):
            return sorted(distance(row['vector'],v) for v in vectors)[min(k,len(vectors))-1]
        # Include the full-width pressure corner, then choose complementary
        # width/mask/connection contexts without consulting measured prices.
        first = max(candidates, key=lambda r:(r['features']['producer']['lhs_width']*r['features']['producer']['rhs_width'],sum(r['vector'][5:8]),r['source_group']))
        candidates.remove(first)
        chosen = [first]
        train_vectors.append(first['vector'])
        for _ in range(3):
            row = max(candidates, key=lambda r:(novelty(r,train_vectors),r['source_group']))
            candidates.remove(row); chosen.append(row); train_vectors.append(row['vector'])
        for row in chosen:
            new.append(dict(row, role='train', purpose='representative wide/shifted Add load; numerical selection, shared predictor'))
        validation = []
        for _ in range(2):
            row = max(candidates, key=lambda r:(novelty(r,train_vectors,3),r['source_group']))
            candidates.remove(row); validation.append(row)
            new.append(dict(row, role='validation', purpose='held-out wide-load connection; no source-ID price function'))
        reference = train_vectors+[r['vector'] for r in validation]
        for _ in range(2):
            row = max(candidates, key=lambda r:(novelty(r,reference),r['source_group']))
            candidates.remove(row); reference.append(row['vector'])
            new.append(dict(row, role='locked_test', purpose='new wide-load independent source; includes reserved 1000ps probe after freeze'))
    root.mkdir(parents=True)
    for name in ('raw','restore','archives'):
        (root/name).mkdir()
    corpus = root/'corpus'; (corpus/'sources').mkdir(parents=True)
    rows = deepcopy(old_manifest['sources'])
    for row in rows:
        (corpus/'sources'/row['id']).symlink_to((parent_root/'corpus/sources'/row['id']).resolve(), target_is_directory=True)
        if row['role'] != 'locked_test':
            (root/'raw'/row['id']).symlink_to((parent_root/'raw'/row['id']).resolve(), target_is_directory=True)
    for row in new:
        row.pop('vector')
        directory = corpus/'sources'/row['id']; directory.mkdir()
        (directory/'input.sv').write_text(samples.source(row['features']))
        write(directory/'contract.json', samples.geometry_contract(row['features']))
        row.update(rtl_sha256=sha(directory/'input.sv'), contract_sha256=sha(directory/'contract.json'), predecessor_role=None)
        rows.append(row)
    protocol = read(parent_root/'corpus/protocol.json')
    counts = dict(Counter(r['role'] for r in rows))
    protocol.update(version='arithmetic-operator-wide-load-protocol-v1', revision=1, source_counts=counts,
                    parent_protocol_sha256=sha(parent_root/'corpus/protocol.json'),
                    successor_sampling_policy=read(POLICY), scope='shared function wide-load extension; no per-view physical price table')
    write(corpus/'protocol.json',protocol)
    manifest = dict(old_manifest, sources=rows, protocol_sha256=sha(corpus/'protocol.json'),
                    successor_sampling_policy_sha256=sha(POLICY), parent_source_manifest_sha256=sha(parent_root/'corpus/manifest.json'))
    write(corpus/'manifest.json',manifest)
    write(root/'new-sources.json',dict(sources=new, physical_labels_read=False, source_choice='unlabeled numerical width/mask/connection coverage',
                                      axes=list(AXES), D_descriptor_witness_sha256=sha(witness)))
    freeze = root/'measurement-source'; hashes = dict(old_cfg['measurement_sources'])
    for name in (str(Path(__file__).relative_to(ROOT)),str(POLICY.relative_to(ROOT)),
                 str(FIT_PROTOCOL.relative_to(ROOT)),str(FEATURE_PROTOCOL.relative_to(ROOT))):
        hashes[name] = sha(ROOT/name)
    for name,h in hashes.items():
        destination = freeze/name; destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/name,destination)
        if sha(destination)!=h:
            raise ValueError('physical producer drift during preparation')
    write(root/'source-freeze.json',hashes)
    shutil.copy2(FIT_PROTOCOL,root/'fit-protocol.json')
    ledger = read(Ledger().path)
    prefix_end=next((i for i,e in enumerate(ledger['entries']) if e['status']=='reserved'),len(ledger['entries']))
    settled_prefix=ledger['entries'][:prefix_end]
    cfg = dict(old_cfg, id=root.name, created_at=datetime.now(timezone.utc).isoformat(),
               source_manifest_sha256=sha(corpus/'manifest.json'), protocol_sha256=sha(corpus/'protocol.json'),
               fit_protocol_sha256=sha(FIT_PROTOCOL),feature_protocol_sha256=sha(FEATURE_PROTOCOL),
               measurement_sources=hashes, source_freeze_directory='measurement-source', source_counts=counts,
               baseline_entries=len(settled_prefix), baseline_usage=usage(settled_prefix), baseline_entries_sha256=key(settled_prefix),
               target_ceiling=13*len(rows), parent_collection_root=str(parent_root),
               parent_fitting_data_sha256=sha(parent_root/'fit-data.json'), inherited_valid_points=405,
               new_source_counts=dict(Counter(r['role'] for r in new)), new_fitting_target_ceiling=12*13,
               new_test_target_ceiling=4*13, original_test_sources_still_locked=True, physical_admission_allowed=False)
    cfg.pop('inherit_synth_by_source',None)
    write(root/'collection.json',cfg)
    write(root/'progress.json',dict(phase='prepared',batches=[],completed_points=405,errors=[],independent_test_started=False))
    (root/'README.md').write_text('# Retained wide-load successor\n\nParent products and roles remain unchanged. '
        'Only new representative local sources are measured. Keep raw data and restored archives until explicit user cleanup. '
        'No view ID is a price feature. Test sources stay locked before a new qualified freeze.\n')
    stages.archive(root,[corpus,freeze,root/'source-freeze.json',root/'fit-protocol.json',root/'collection.json',root/'new-sources.json',root/'README.md'],
                   'initial-source-freeze.tar.gz')
    print(dict(status='prepared',parent_valid_points=405,new_sources=len(new),new_counts=cfg['new_source_counts'],
               guards=read(POLICY)['new_source_guard_targets_ps'],full_D_ready=False),flush=True)


def preflight(out):
    results = [];negatives=[]
    policy=validate_policy(read(POLICY))
    for role in ('train','validation','locked_test'):
        rows = []
        for index in range(13):
            q = wide_decide(rows,'software-wide-'+role,role)['next_request']
            if q is None:
                break
            rows.append(dict(q,source_id='software-wide-'+role,role=role,status='completed',
                             implementation_id=key([role,q['SDC_ps']]),operator_delay_ps=500.,comb_area_um2=2.,
                             data_setup_slack_ps=q['SDC_ps']-900.,operator_maximum_covered=True,
                             data_through_operator_covered=True,ownership_complete=True))
        decision = wide_decide(rows,'software-wide-'+role,role)
        expected = read(POLICY)['new_source_guard_targets_ps'][role]
        if [r['SDC_ps'] for r in rows[:len(expected)]] != expected or decision['next_request'] is not None:
            raise ValueError('guard order or bounded stop differs')
        if role != 'locked_test' and any(r['SDC_ps']==1000 for r in rows):
            raise ValueError('reserved interpolation target used in fit')
        bad = deepcopy(rows);bad[0]['SDC_ps']+=1
        try:
            wide_decide(bad,'software-wide-'+role,role)
        except ValueError:
            negatives.append('forged_history_'+role)
        else:
            raise ValueError('forged deterministic history accepted')
        results.append(dict(role=role,targets=[r['SDC_ps'] for r in rows],stop_reason=decision['stop_reason']))
        first=dict(rows[0]);first={k:v for k,v in first.items() if k in ('SDC_ps','ABC_ps','proposal','reference_ratio','source_id','role')}
        first.update(status='failed',failure_reason='software qualification failure')
        stopped=wide_decide([first],'software-wide-'+role,role)
        if stopped['next_request'] is not None:raise ValueError('failed source continued')
        negatives.append('first_failure_stops_'+role)
    for name,change in (
        ('duplicate_guard',lambda p:p['new_source_guard_targets_ps']['train'].append(1500)),
        ('reserved_fit_target',lambda p:p['new_source_guard_targets_ps']['validation'].append(1000)),
        ('invalid_guard',lambda p:p['new_source_guard_targets_ps']['train'].append(0)),
        ('missing_test_interpolation',lambda p:p['new_source_guard_targets_ps']['locked_test'].remove(1000))):
        bad=deepcopy(policy);change(bad)
        try:validate_policy(bad)
        except ValueError:negatives.append(name)
        else:raise ValueError('invalid guard policy accepted: '+name)
    write(out,dict(version='wide-guarded-sampler-proof-v2',status='passed',cases=results,negative_checks=negatives,
          producer_sha256=sha(Path(__file__)),policy_sha256=sha(POLICY),parent_sampler_sha256=sha(Path(scan.__file__)),
          parent_sampler_policy_sha256=sha(scan.CONFIG),source_roles_immutable=True,max_targets=13,new_EDA_calls=0))
    print('WIDE_GUARDED_SAMPLER_PREFLIGHT_PASS',flush=True)


def bank_proof(root, software, work, sampler, sampler_receipt):
    proof = read(sampler)
    validate_sampler_proof(proof)
    rows = read(root/'new-sources.json')['sources']
    prepared = read(software/'sources.json')
    if prepared['source_role']!='software_only_no_physical_test_labels' or prepared['rows']!=rows:
        raise ValueError('new source software inventory differs')
    if prepared['source_sha256']!=sha(Path(samples.__file__)):
        raise ValueError('new source software generator differs')
    if (software/'kernels.sv').read_text()!='\n'.join(samples.source(r['features'],'Observe'+str(i)) for i,r in enumerate(rows)):
        raise ValueError('compiled bank kernels differ from the declared sources')
    proof_files = {str(sampler):sha(sampler),str(software/'sources.json'):sha(software/'sources.json')}
    preparer=work/'software-prepare-v1/source/regression/arithmetic_steps123.py'
    if sha(preparer)!=sha(ROOT/'regression/arithmetic_steps123.py'):
        raise ValueError('bank vector producer changed')
    proof_files[str(preparer)]=sha(preparer)
    for row in rows:
        path = software/'sources'/row['id']/'input.sv'
        if sha(path)!=row['rtl_sha256']:
            raise ValueError('simulated new source differs from planned RTL')
        proof_files[str(path)]=sha(path)
    ledger={e['id']:e for e in read(Ledger().path)['entries']}
    receipts=[work/name/'commands.json' for name in ('software-prepare-v1','software-iverilog-v1','software-run-v1')]+[sampler_receipt]
    for commands in receipts:
        record = read(commands)[0]
        entry=ledger.get(record['budget_reservation_id'],{})
        if (record['exit_code'] or record['cleanup']['remaining_live_pids'] or entry.get('status')!='completed'
                or entry.get('command')!=record['command']):
            raise ValueError('new source software command failed')
        proof_files[str(commands)] = sha(commands)
        if commands.parent.name=='software-run-v1' and ('INDEPENDENT_OBSERVERS_PASS sources='+str(len(rows))+' cycles=128') not in Path(record['log']).read_text():
            raise ValueError('new source numerical/valid/reset/observer proof missing')
        if commands.parent.name=='software-iverilog-v1':
            command=record['command']
            if (Path(command[0]).name!='iverilog' or '-o' not in command or
                    Path(command[command.index('-o')+1]).resolve()!=software/'sim' or
                    {Path(c).resolve() for c in command if c.endswith('.sv')}!={software/'kernels.sv',software/'tb.sv'}):
                raise ValueError('compiled bank inputs differ')
        if commands.parent.name=='software-run-v1':
            command=record['command']
            if len(command)!=2 or Path(command[0]).name!='vvp' or Path(command[1]).resolve()!=software/'sim':
                raise ValueError('simulated bank binary differs')
        if commands==sampler_receipt:
            command=record['command']
            if 'preflight' not in command or '--out' not in command or Path(command[command.index('--out')+1]).resolve()!=sampler:
                raise ValueError('sampler receipt does not bind this proof')
    proof_files.update({str(software/n):sha(software/n) for n in ('kernels.sv','tb.sv','sim')})
    return proof_files,len(rows)


def admit(root, software, work, sampler, sampler_receipt):
    verify_measurement_sources(root)
    proof_files,count=bank_proof(root,software,work,sampler,sampler_receipt)
    path=root/'software-admission-v2.json'
    if path.exists():raise ValueError('preserve previous software admission')
    write(path,dict(version='wide-source-software-admission-v2',status='passed',source_manifest_sha256=sha(root/'corpus/manifest.json'),
          sampler_policy_sha256=sha(POLICY),proof_files=proof_files,software_sources=count,cycles_each=128,
          producer_sha256=sha(Path(__file__)),source_generator_sha256=sha(Path(samples.__file__)),sampler_proof=str(sampler),
          bank_software_folder=str(software),bank_work=str(work),sampler_command_receipt=str(sampler_receipt),
          fit_protocol_sha256=sha(FIT_PROTOCOL),feature_protocol_sha256=sha(FEATURE_PROTOCOL),
          parent_admission_sha256=sha(root/'software-admission.json'),
          old_test_physical_labels_read=False,physical_parameters_or_roles_changed=False,
          new_fitting_max_unique_targets=12*13,new_test_still_locked=True,full_D_ready=False))
    write(root/'active-software-admission.json',dict(path=path.name,sha256=sha(path)))
    print('WIDE_SOURCE_SOFTWARE_ADMITTED sources='+str(count),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('prepare','run','preflight','admit'))
    for name in ('root','parent','witness','out','selection','software','work','sampler','sampler-receipt','pilot'):
        p.add_argument('--'+name,type=Path)
    p.add_argument('--mode',choices=('fitting','independent'),default='fitting')
    p.add_argument('--max-batches',type=int)
    a=p.parse_args()
    if a.action=='prepare':prepare(a.parent.resolve(),a.witness.resolve(),a.root.resolve())
    elif a.action=='preflight':preflight(a.out.resolve())
    elif a.action=='admit':admit(a.root.resolve(),a.software.resolve(),a.work.resolve(),a.sampler.resolve(),a.sampler_receipt.resolve())
    else:run(a.root.resolve(),a.mode,a.selection.resolve() if a.selection else None,a.max_batches,a.pilot.resolve() if a.pilot else None)
