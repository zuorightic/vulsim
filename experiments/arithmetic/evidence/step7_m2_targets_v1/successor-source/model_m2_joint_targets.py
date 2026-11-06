"""Bind the numerical target freeze to successor S/G/I requirements, without EDA admission."""
import argparse
import copy
import json
from pathlib import Path

from .model_m2_targets import ROOT, read, sha, write, verify as verify_targets

BASE=ROOT/'experiments/arithmetic_dse/configs/model_asap7_m2_joint_requirements_v1.json'
BASE_SHA='270e0e448eeabe6a4c9001d36695d364095c910c44fcc47526527ae3be5a98df'
TARGETS=ROOT/'experiments/arithmetic_dse/configs/model_asap7_m2_targets_v1.json'
OUTPUT=ROOT/'experiments/arithmetic_dse/configs/model_asap7_m2_joint_requirements_v2.json'
EVIDENCE=ROOT/'experiments/arithmetic/evidence/step7_m2_targets_v1'


def build(base,targets,identities):
    if (base['version']!='asap7-m2-joint-model-requirements-v1'
        or targets['version']!='asap7-m2-numerical-target-freeze-v1'
        or not targets['numerical_targets_frozen'] or targets['model_targets_qualified']
        or base['policy']!={'K':16,'same_ordered_C_D_candidates':True,'search_PPA_calls':0,'Div_FP_remain_atomic':True}):
        raise ValueError('joint requirements/target freeze identity mismatch')
    result=copy.deepcopy(base)
    result.update(version='asap7-m2-joint-model-requirements-v2',
        status='numerical_targets_frozen_synthetic_source_and_sampling_admission_pending',
        predecessor=identities,source_sha256=sha(Path(__file__)))
    result['target_reference'].update(reference_settings_frozen=True,reference_labels_complete=True,
        numerical_targets_frozen=True,
        H_ref='per-case max data capture suffix plus clock/setup/skew/uncertainty across required reference keys; other full paths diagnostic separately',
        numerical_target_file=identities['target_file'],numerical_target_sha256=identities['target_sha256'],
        production_batch_sha256=targets['production_batch']['batch_sha256'],additional_numeric_reserve_ps=0)
    result['target_contexts']=[{'case_id':name,'platform':'asap7','stage':'grt','ABC_ps':1500,
        'SDC_ps':targets['cases'][name]['T_target_ps'],'IO':'0.2T','L':targets['cases'][name]['L'],
        'D_ref_ps':targets['cases'][name]['D_ref_ps'],'H_ref_ps':targets['cases'][name]['H_ref_ps'],
        'target_data_budget_ps':targets['cases'][name]['target_data_budget_ps'],
        'rho_ref':targets['cases'][name]['rho_ref']} for name in targets['policy']['cases']]
    result['physical_identity'].update(formal_SDC_ps=targets['exact_SDC_ps'],
        target_clock_grid_for_training_frozen=False,reference_SDC_ps=40500)
    result['cost_ownership'].update(physical_label_partition_implemented_and_verified=True,
        partition_verification_scope='17 isolated reference shells only; future S/G/I sources must independently prove complete ownership',
        public_capture_protocol='input service independently enabled; native internal data uses previous-stage valid; public external output unconditional',
        isolated_state_total_area_is_direct_joint_addend=False)
    for package in result['work_packages']:
        if package['id']=='R':
            package.update(status='complete_reference_and_user_approved_numerical_target_freeze',
                reference_model_fitting_allowed=False)
        elif package['id'] in ('S','G','I'):
            package.update(status='synthetic_source_preflight_and_sampling_admission_pending',
                required_target_contexts_ref='target_contexts',
                precise_collection_grid_and_complete_tasks_frozen=False,
                existing_qualified_clock_domain_inherited=False,
                target_expansion_from_formal_PPA_allowed=False)
    result['sampling_preconditions']={
        'source_and_context_rules':'synthetic semantic sources independent of formal/holdout complete graphs; all source/clock/stage variants share one split',
        'software_preflight':'reset/bubbles/previous-valid/external-unconditional/known-mask/source-relation semantics; full-state RTL simulation and unmapped geometry',
        'raw_labels':'actual ownership/FF/path/SDC/RC/CEC checks under each family; reference partition alone does not qualify unseen templates',
        'test':'fresh locked independent sources registered before collection; freeze parameters/domain/reserve before release; preserve all consumed tests',
        'capacity_and_budget':'exact source/platform/stage probes and complete task grid, shared residual wall/CPU/calls/storage envelope before physical launch',
        'mapping_reuse':'only explicit byte-exact compatible mapping ancestry; fresh target SDC/ODB, every actual leaf paid',
        'quality':'original family gates; no automatic refit/margin/clock change from independent or whole-graph PPA'}
    result['missing_for_admission']=[
        'executable S/G/I synthetic sources, exact source relation/reset/mask/capture and topology support grammar',
        'full source preflight, separate native/internal and service/external ownership, complete grouped train/validation/locked-test manifests',
        'exact collection clock grid and prospective qualification of the formal target domain',
        'per-source/stage capacity probes and complete residual wall/CPU/calls/support/storage budget']
    result.update(physical_admission_allowed=False,model_target_domains_qualified=False,full_D_ready=False,
        formal_36_complete=False,PPA_calls=0)
    return result


def prepare(output):
    verify_targets(EVIDENCE,external=True)
    if output.exists():raise ValueError('preserve existing joint target successor')
    if sha(BASE)!=BASE_SHA:raise ValueError('static requirements predecessor changed')
    identities={'requirements_file':str(BASE.relative_to(ROOT)),'requirements_sha256':sha(BASE),
        'target_file':str(TARGETS.relative_to(ROOT)),'target_sha256':sha(TARGETS),
        'target_evidence_manifest_sha256':sha(EVIDENCE/'manifest.json')}
    result=build(read(BASE),read(TARGETS),identities);write(output,result)
    print(json.dumps({'status':result['status'],'formal_target_contexts':len(result['target_contexts']),
        'sha256':sha(output),'physical_admission_allowed':False,'PPA_calls':0}),flush=True)


def verify(output):
    result=read(output);p=result['predecessor']
    for name,key in [('requirements_file','requirements_sha256'),('target_file','target_sha256')]:
        if sha(ROOT/p[name])!=p[key]:raise ValueError('joint target predecessor changed')
    if sha(EVIDENCE/'manifest.json')!=p['target_evidence_manifest_sha256']:
        raise ValueError('joint target freeze evidence changed')
    if result!=build(read(ROOT/p['requirements_file']),read(ROOT/p['target_file']),p):
        raise ValueError('joint target requirements do not reproduce')
    print(json.dumps({'status':'passed','formal_target_contexts':9,'physical_admission_allowed':False,'PPA_calls':0}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('prepare','verify'))
    parser.add_argument('--output',type=Path,default=OUTPUT);args=parser.parse_args()
    if args.action=='prepare':prepare(args.output.resolve())
    else:verify(args.output.resolve())
