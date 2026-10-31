"""Execute the frozen step5 pair once; backend leaf commands own all charges."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from .backend import ROOT,sha256,write_json
from .budget import Ledger,POLICY,STAGE_LIMITS

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--study',type=Path,default=ROOT/'experiments/arithmetic_dse/configs/step5_pilot_v1.json')
    args=parser.parse_args();config=json.loads(args.study.read_text());out=args.out.resolve()
    if out.exists():parser.error('output must be a new directory')
    if config['calls']!={'synth':2,'grt':2,'final':0,'retry':0,'automatic_retry':False}:
        raise ValueError('unexpected pilot call envelope')
    settings=config['settings'];ledger=Ledger();before=ledger.summary();resources=json.loads(POLICY.read_text())['resources']
    reserve=config['budget_reserve']
    if (before['pending'] or any(before[s]+reserve[s]>resources[k] for s,k in STAGE_LIMITS.items())
        or before['walltime_s']+reserve['walltime_s']>resources['max_global_walltime_h']*3600
        or before['CPU_time_s']+reserve['CPU_time_s']>resources['max_tool_CPU_time_h']*3600):
        raise ValueError('insufficient shared pilot budget')
    for item in [config['functional_report'],*config['rtl'].values()]:
        if sha256(ROOT/item['path'])!=item['sha256']:raise ValueError('pilot input hash mismatch')
    functional=json.loads((ROOT/config['functional_report']['path']).read_text())
    if functional['status']!='passed' or functional['C_choice_before_PPA']!='mul32_split16':
        raise ValueError('functional precondition failed')
    out.mkdir(parents=True)
    study={'version':'step5-pilot-result-v1','status':'running','study_sha256':sha256(args.study),
           'usage_before':before,'admission':'bounded_pair_only','points':[],'automatic_retries':0}
    write_json(out/'study.json',study)
    for candidate in config['candidates']:
        directory=out/candidate
        cmd=[sys.executable,'-m','experiments.arithmetic_dse.backend','--rtl',str(ROOT/config['rtl'][candidate]['path']),
             '--top',candidate,'--out',str(directory),'--period-ps',str(settings['period_ps']),
             '--abc-target-ps',str(settings['abc_target_ps']),'--stage','grt','--threads','2','--budget-purpose','prototype']
        with (out/(candidate+'.driver.log')).open('w') as log:
            process=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        manifest=json.loads((directory/'manifest.json').read_text())
        study['points'].append({'candidate':candidate,'command':cmd,'exit_code':process.returncode,
            'status':manifest['status'],'failure_stage':manifest.get('failure_stage'),'failure_reason':manifest.get('failure_reason'),
            'metrics':manifest['metrics'],'mapping_context':manifest.get('mapping_context'),
            'mapping_context_sha256':manifest.get('mapping_context_sha256')})
        write_json(out/'study.json',study)
    study['status']='completed' if all(p['status']=='completed' for p in study['points']) else 'incomplete'
    study['usage_after']=ledger.summary()
    delta={stage:study['usage_after'][stage]-before[stage] for stage in STAGE_LIMITS}
    study['actual_calls']=delta
    # A failure before grt consumes its real synth attempt and zero grt calls.
    # The declared envelope is an upper bound, not a fabricated failure charge.
    if (any(delta[s]>config['calls'][s] for s in STAGE_LIMITS) or study['usage_after']['pending']
        or (study['status']=='completed' and delta!={'synth':2,'grt':2,'final':0})):
        raise ValueError('pilot accounting differs from declared envelope')
    write_json(out/'study.json',study)
    print(json.dumps(study,ensure_ascii=False,indent=2))
    return 0 if study['status']=='completed' else 1
if __name__=='__main__':raise SystemExit(main())
