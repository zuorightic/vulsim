from pathlib import Path
import hashlib,importlib.util,json,sys
R=Path.cwd();sys.path.insert(0,str(R));B=R/'build/step6-integration-20261031'
from experiments.arithmetic_dse.sdc import rtl_ports,verify_sdc
from experiments.arithmetic_dse.budget import usage
A=json.loads((B/'capacity-admission.json').read_text());rows=[]
for t in A['tasks']:
 run=B/'physical'/t['id'];manifest=run/'manifest.json'
 if not manifest.exists():rows.append({'task_id':t['id'],'status':'not_run','physical_calls':0,'reason':'baseline capacity task did not complete; dependent sensitivity domain paused'});continue
 m=json.loads(manifest.read_text());c=json.loads((run/'synth.command.json').read_text());assert not c['cleanup']['remaining_live_pids'] and not c['unexpected_live_descendants']
 rows.append({'task_id':t['id'],'status':'failed','failure_stage':m['failure_stage'],'failure_code':m['failure_code'],'failure_reason':m['failure_reason'],'actual_synth_command_exit':c['exit_code'],'actual_walltime_s':c['walltime_s'],'peak_tree_RSS_KiB':c['sampled_process_tree_peak_rss_KiB'],'CPU_settlement':next(e['CPU_accounting'] for e in json.loads((R/'experiments/arithmetic/backend_usage.json').read_text())['entries'] if e.get('task_id')==t['id'] and e['stage']=='synth'),'stored_rtl_sha256':hashlib.sha256(__import__('gzip').compress((run/'input.sv').read_bytes(),mtime=0)).hexdigest()})
run=B/'physical/asap7-step6-fp32_serial-capacity-v1';m=json.loads((run/'manifest.json').read_text());old=run/'source/experiments/arithmetic_dse/sdc.py'
assert hashlib.sha256(old.read_bytes()).hexdigest()==m['source_sha256']['experiments/arithmetic_dse/sdc.py']
spec=importlib.util.spec_from_file_location('experiments.arithmetic_dse._step6_actual_old_sdc',old);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
try:module.rtl_ports((run/'input.sv').read_text());raise AssertionError('old reader unexpectedly accepted')
except ValueError as error:before=str(error)
ports=rtl_ports((run/'input.sv').read_text(),'Step6FP2');checked=verify_sdc((run/'results/asap7/arithmetic_probe/base/1_synth.sdc').read_text(),m['platform_profile'],1500,ports)
post={'version':'step6-capacity-postmortem-v1','old_scoped_reader_error':before,'cause':'single-module reader combined child and top port declarations; comma-shared ports were also incomplete','corrected_static_SDC_check':checked,'original_manifest_modified':False,'accepted_PPA_metrics':0,'new_STA_or_physical_calls':0,'grt_capacity':'not measured; paused after original failure; no automatic retry','physical_followup':'any checkpoint continuation or corrective physical run requires a new explicit finite admission; no change to L/II, circuit, clock or global budget in this closure'}
(B/'physical-postmortem.json').write_text(json.dumps(post,indent=2)+'\n');(B/'physical-outcome.json').write_text(json.dumps({'version':'step6-capacity-outcome-v1','runs':rows,'scope':'two attempted baselines, four paused controls; no training labels or main matrix records'},indent=2)+'\n');print(json.dumps(post,indent=2))
