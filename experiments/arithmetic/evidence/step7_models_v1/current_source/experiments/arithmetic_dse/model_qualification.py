"""Predeclared context checks of already frozen numerical stage models."""
import argparse
import copy
import json
from pathlib import Path
from .budget import POLICY
from .model_collection import PROTOCOL,sha,write
from .model_calibration import CALIBRATION
from .model_calibration_fit import quality
from .model_stage_samples import source
from .platforms import profile

QUALIFICATION=Path(__file__).with_name('configs')/'model_context_qualification_v1.json'
BOUNDARY_QUALIFICATION=Path(__file__).with_name('configs')/'model_boundary_qualification_v1.json'


def prepare(out,models):
    out.mkdir(parents=True,exist_ok=False);cfg=json.loads(QUALIFICATION.read_text());protocol=json.loads(PROTOCOL.read_text());tasks=[]
    text,labels=source('test',cfg['capture_fanout']);rtl=out/'input.sv';rtl.write_text(text)
    contract=out/'contract.json';write(contract,{'version':'arithmetic-model-labels-v1','split':'test','source_group':'v5-test-family-fan1-context-qualification',
        'labels':labels,'qualification_protocol_sha256':sha(QUALIFICATION),'base_calibration_protocol_sha256':sha(CALIBRATION)})
    model_refs={}
    for platform in protocol['platform_order']:
        model=models/(platform+'.json');b=json.loads(model.read_text());report=json.loads((models/'calibration-independent-test.json').read_text())
        actual=next(x for x in report['reports'] if x['platform']==platform)
        if actual['stages']['grt']['status']!='passed':raise ValueError('independent grt stage not ready for context qualification')
        model_refs[platform]={'path':str(model.resolve()),'sha256':sha(model),'base_independent_test_sha256':sha(models/'calibration-independent-test.json')}
        p=profile(platform);ref=protocol['reference_abc_ps'][platform]
        for factor in cfg['SDC_reference_multipliers']:
            token=str(factor).replace('.','p')
            tasks.append({'id':platform+'-f1-context-'+token,'platform':platform,'profile_sha256':p['profile_sha256'],
                'rtl':str(rtl.resolve()),'rtl_sha256':sha(rtl),'top':'ModelBundle','period_ps':ref*factor,'abc_target_ps':ref,'stage':'grt',
                'sample_contract':str(contract.resolve()),'sample_contract_sha256':sha(contract),'source_group':'v5-test-family-fan1-context-qualification','split':'test',
                'samples':len(labels),'synth_timeout_s':300,'route_timeout_s':1200,'memory_limit_MiB':8192,
                'capacity_scope':'same independent v5 graph widths<=28 and topology sizes; fanout1 lowers capture count; previous all-platform collection completed'})
    write(out/'admission.json',{'version':'arithmetic-model-collection-admission-v1','id':out.name,'purpose':'arithmetic_model_collection',
        'policy_sha256':sha(POLICY),'protocol_sha256':sha(PROTOCOL),'supplemental_protocol':{'path':str(QUALIFICATION.resolve()),'sha256':sha(QUALIFICATION)},
        'tasks':tasks,'frozen_models':model_refs,'generator_sources_sha256':{str(p):sha(p) for p in (Path(__file__),Path(__file__).with_name('model_stage_samples.py'),Path(__file__).with_name('model_calibration.py'))},
        'automatic_retries':0,'call_caps':{'synth':12,'grt':12,'final':0},'support_walltime_s':7200,
        'worst_case_leaf_walltime_s':12*1860+7200,'later_work_reserved':{'walltime_s':86400,'CPU_time_s':172800,'synth':688,'grt':688},
        'main_matrix_authorized':False,'not_training':True,'storage':'compact original paths/labels/identities; large local ignored artifacts, remote retention unconfirmed'})
    print({'frozen_models':4,'new_tasks':12,'no_physical_calls_started':True})


def test(data,admission,out):
    if out.exists():raise ValueError('qualification already evaluated; use a new explicit protocol rather than retesting')
    out.mkdir(parents=True);a=json.loads(admission.read_text());dataset=json.loads(data.read_text());reports=[]
    if a['supplemental_protocol']['sha256']!=sha(QUALIFICATION) or dataset['admission_sha256']!=sha(admission):raise ValueError('changed qualification identities')
    for platform,ref in a['frozen_models'].items():
        model=Path(ref['path'])
        if sha(model)!=ref['sha256']:raise ValueError('numerical model changed before context test')
        if sha(model.parent/'calibration-independent-test.json')!=ref['base_independent_test_sha256']:raise ValueError('changed base independent qualification')
        bundle=json.loads(model.read_text());contexts=[];ready=True
        for period in sorted({r['period_ps'] for r in dataset['rows'] if r['platform']==platform}):
            row={'period_ps':period,'stages':{}}
            for stage in ('synth','grt'):
                rows=[r for r in dataset['rows'] if r['platform']==platform and r['stage']==stage and r['period_ps']==period]
                row['stages'][stage]=quality(bundle,stage,rows)
                actual_h=max(r['boundary_overhead_ps'] for r in rows)
                control=max(r['delay_ps'] for r in rows if r['spec']['role']=='state');boundary=bundle['stages'][stage]['boundary_model']
                required=actual_h+control;covered=min(boundary['register_overhead_ps'],boundary['input_overhead_ps'])+1e-6>=required
                row['stages'][stage]['boundary_qualification']={'maximum_measured_H_ps':actual_h,'measured_capture_control_path_ps':control,
                    'required_without_extra_reserve_ps':required,'frozen_register_overhead_ps':boundary['register_overhead_ps'],
                    'frozen_input_overhead_ps':boundary['input_overhead_ps'],'covered':covered}
            ready &= row['stages']['grt']['status']=='passed' and row['stages']['grt']['boundary_qualification']['covered'];contexts.append(row)
        if len(contexts)!=3:raise ValueError('incomplete declared target contexts')
        result={'platform':platform,'grt_domain_status':'passed' if ready else 'failed','frozen_source_model_sha256':ref['sha256'],'contexts':contexts}
        reports.append(result)
        if ready:
            # Only qualification metadata and domain bounds change. Every
            # numerical predictor/state/boundary coefficient remains frozen.
            released=copy.deepcopy(bundle);released['stages']={'grt':released['stages']['grt']};released['id']=platform+'-local-grt-qualified-v1';released['quality_status']='passed'
            for operation in released['stages']['grt']['operations'].values():
                for condition in operation['domain']['conditions']:
                    condition['sdc_min_ps']=released['mapping_abc_target_ps'];condition['sdc_max_ps']=released['mapping_abc_target_ps']*1.5
            released['release_scope']='grt local dynamic Mul/Add/AddCarry and independent single-output synthetic trees only; original stage/node/state domains still apply; no full candidate or five-width readiness'
            released['qualified_source_model_sha256']=ref['sha256'];released['qualification_protocol_sha256']=sha(QUALIFICATION);released['qualification_dataset_sha256']=sha(data);released['boundary_qualification_protocol_sha256']=sha(BOUNDARY_QUALIFICATION)
            released['support_status']='qualified local grt domain only; synth including Sky failed result remains in the source package'
            write(out/(platform+'.json'),released)
    write(out/'qualification-test.json',{'version':'frozen-model-context-qualification-result-v1','admission_sha256':sha(admission),'dataset_sha256':sha(data),
        'protocol_sha256':sha(QUALIFICATION),'boundary_protocol_sha256':sha(BOUNDARY_QUALIFICATION),'reports':reports,'no_numerical_changes':True,'main_matrix_authorized':False})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','test']);p.add_argument('--out',type=Path,required=True);p.add_argument('--models',type=Path);p.add_argument('--data',type=Path);p.add_argument('--admission',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare(a.out,a.models)
    else:test(a.data,a.admission,a.out)
