"""Finite v2 work package; physical/support leaves retain shared Ledger fees."""
import argparse
from pathlib import Path
import sys

from .model_fast_preflight import read,write,sha
from . import operator_stage4 as stages
from . import operator_condition_wide as wide

ROOT=Path(__file__).resolve().parents[2]


def run(root,work,training_batches,test_batches):
    if not 1<=training_batches<=9 or not 1<=test_batches<=20:raise ValueError('finite package batch limits required')
    status=root/'v2-work-status.json'
    producer=sha(Path(__file__))
    def state(phase,**values):
        stages.atomic(status,dict(version='operator-v2-work-status-v1',phase=phase,root=str(root),work=str(work),producer_sha256=producer,full_D_ready=False,**values))
        print('V2_WORK '+phase,flush=True)
    def support(name,args,timeout=300):
        return stages.support(work,name,[sys.executable,'-B']+args,timeout)
    if (root/'test-acquisition-v2.json').exists():raise ValueError('test work already started; preserve its exact freeze, do not rerun this pipeline')
    state('bounded_fitting_collection',max_batches=training_batches)
    try:
        wide.run(root,'fitting',max_batches=training_batches)
        if read(root/'progress.json')['phase']!='fitting_collection_complete':
            state('bounded_fitting_still_pending');return
        if sha(Path(__file__))!=producer:raise ValueError('running work controller changed; preserve checkpoint before fitting')
        data=root/'fit-data.json';fit=root/'fit-v2'
        state('full_v2_extract')
        support('v2-final-preflight',['regression/arithmetic_condition_v2.py','preflight','--out',str(root/'v2-fit-preflight.json')],180)
        support('v2-full-extract',['-m','experiments.arithmetic_dse.operator_condition_fit_v2','extract','--root',str(root),'--out',str(data)],900)
        state('v2_fitting')
        support('v2-fit',['-m','experiments.arithmetic_dse.operator_condition_fit_v2','fit','--data',str(data),'--out',str(fit),
            '--witness',str(ROOT/'build/step6-real-boundary-20261110/consumer-v4/real-boundary.json')],300)
        support('v2-response-refusal',['regression/arithmetic_condition_v2.py','diagnostics','--data',str(data),'--folder',str(fit),'--out',str(fit/'response-refusal.json')],180)
        if read(fit/'validation.json')['status']!='passed':
            state('validation_failed_test_locked',validation=str(fit/'validation.json'));return
        state('actual_model_native_parity')
        inference=fit/'inference'
        support('v2-parity-prepare',['regression/arithmetic_condition_model.py','prepare','--root',str(root),
            '--folder',str(inference),'--candidate',str(fit/'candidate.json'),'--data',str(data)],180)
        stages.support(work,'v2-parity-native',[str(ROOT/'build/step4-rtlzz/testv2/operator-condition-infer'),str(inference/'input-0.json'),str(inference/'output-0.json')],180)
        support('v2-parity-verify',['regression/arithmetic_condition_model.py','verify','--folder',str(inference),'--out',str(inference/'verification')],180)
        support('v2-freeze',['-m','experiments.arithmetic_dse.operator_condition_fit_v2','freeze','--data',str(data),'--folder',str(fit)],180)
        selection=fit/'selection-freeze.json'
        write(root/'test-acquisition-v2.json',dict(version='operator-v2-single-frozen-test-acquisition-v1',
            selection_sha256=sha(selection),source_manifest_sha256=sha(root/'corpus/manifest.json'),max_batches=test_batches,
            source_role='locked_test',fitting_or_domain_retuning_now_forbidden=True,all_test_sources_remain_test=True))
        state('frozen_independent_collection',selection=str(selection),max_batches=test_batches)
        wide.run(root,'independent',selection=selection,max_batches=test_batches)
        if read(root/'progress.json')['phase']!='independent_collection_complete':
            state('bounded_independent_still_pending',selection=str(selection));return
        state('independent_extract_and_evaluate_once')
        support('v2-test-extract',['-m','experiments.arithmetic_dse.operator_condition_fit_v2','extract','--root',str(root),'--mode','independent',
            '--selection',str(selection),'--out',str(root/'test-data.json')],900)
        support('v2-test-evaluate',['-m','experiments.arithmetic_dse.operator_condition_fit_v2','test','--data',str(root/'test-data.json'),
            '--selection',str(selection),'--out',str(root/'test-v2')],300)
        report=read(root/'test-v2/independent-test.json')
        state(report['status'],independent_report=str(root/'test-v2/independent-test.json'),model=str(root/'test-v2/tested-model.json'))
    except Exception as error:
        state('stopped_preserve_failure',error=str(error),physical_progress=read(root/'progress.json')['phase'])
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True)
    p.add_argument('--training-batches',type=int,default=9);p.add_argument('--test-batches',type=int,default=20)
    a=p.parse_args();run(a.root.resolve(),a.work.resolve(),a.training_batches,a.test_batches)
