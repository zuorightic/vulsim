"""One explicit continuation after a zero-command ledger-interface failure."""
import json
from pathlib import Path
from experiments.arithmetic_dse.model_collection import sha,write,verify_test_release
root=Path.cwd();out=root/'build/step7-intervals-20261103';batch=root/'build/step7-models-20261102/native-interval-asap7-v4'
selection=out/'asap7-fit-v1/selection-freeze.json';failed=batch/'runs/asap7-test-b000';archived=batch/'runs/asap7-test-b000-preflight-accounting-v1'
m=json.loads((failed/'manifest.json').read_text());ledger=json.loads((root/'experiments/arithmetic/backend_usage.json').read_text())
assert m['status']=='failed' and m['failure_stage']=='preflight'
assert m['failure_reason']=='invalid platform/admission accounting context' and m['commands']==[] and m['metrics']==[]
assert not any(e.get('admission_id')=='native-interval-asap7-v4' and e.get('task_id')=='asap7-test-b000' for e in ledger['entries'])
assert not (selection.parent/'independent-test-consumption.json').exists()
assert not archived.exists()
verify_test_release(batch/'admission.json',selection,['asap7'])
note={'version':'interval-test-preflight-interface-correction-v1','logical_task':'asap7-test-b000',
      'admission_sha256':sha(batch/'admission.json'),'selection_freeze_sha256':sha(selection),
      'candidate_sha256':sha(selection.parent/'asap7.candidate.json'),
      'failed_manifest_sha256':sha(failed/'manifest.json'),'original_failed_directory':str(failed),
      'retained_failed_directory':str(archived),'previous_budget_source_sha256':m['source_sha256']['experiments/arithmetic_dse/budget.py'],
      'corrected_budget_source_sha256':sha(root/'experiments/arithmetic_dse/budget.py'),
      'failed_driver_log_sha256':sha(batch/'asap7-test-b000.driver.log'),
      'reason':'backend already emits selection_freeze_sha256, but Ledger omitted this traceability field from its whitelist; accept and retain it without changing any limit or numerical model',
      'physical_commands_launched':0,'test_measurements_observed':0,'numeric_model_or_margin_changes':False,
      'automatic_retry_added':False,'continuation':'explicit corrected implementation, same unconsumed frozen logical test; preserve failed bytes and driver log at named attempt path, then use canonical task path for first actual measurement'}
write(out/'test-preflight-correction-v1.json',note)
failed.rename(archived)
(batch/'asap7-test-b000.driver.log').rename(batch/'asap7-test-b000-preflight-accounting-v1.driver.log')
assert sha(archived/'manifest.json')==note['failed_manifest_sha256']
print(json.dumps(note,indent=2))
