"""Final acceptance against compact evidence and every local archive byte."""
from pathlib import Path
import json,sys
R=Path.cwd();sys.path.insert(0,str(R));B=R/'build/step6-review-20261102'
from experiments.arithmetic_dse.whole_graph_review_evidence import verify

portable=json.loads((B/'portable_checks.json').read_text())
assert portable['status']=='passed' and len(portable['negative_checks'])==11
result=verify(R,external=True,parents=True)
assert result['status']=='passed' and result['parent_status']=='passed' and result['backend_completion']
assert result['normalized_netlists_recomputed']==5
assert result['software']['atomic_B_C_equal']==23
reg=R/'build/step6-relaxed-clock-20261102/final-regression.log'
assert 'Ran 85 tests' in reg.read_text() and '\nOK\n' in reg.read_text()
report={'status':'passed','step6_acceptance':'whole_graph_safety_and_declared_finite_capacity',
    'software':result['software'],'backend_completion':result['backend_completion'],
    'UDR_100ns':result['UDR_100ns'],'F2_original_target_status':'flow complete; setup fails at1500ps',
    'parent_chain':result['parent_status'],'full_artifacts_verified':True,
    'normalized_netlists_recomputed':result['normalized_netlists_recomputed'],
    'remote_durable_retention_confirmed':False,'isolated_portable_verification':True,
    'semantic_negative_cases':len(portable['negative_checks']),'software_regressions':85,
    'current_freeze_usage':result['cumulative_usage'],
    'scope_boundaries':['no_D_model_or_training','no_Div_Mod_or_FP_internal_splitting',
        'capacity_diagnostics_not_training_or_formal_targets','two_old_UDR_synth_controls_not_run',
        'other_platform_capacity_and_688_main_records_remain_step7_8'],
    'statistics_timing':'verification candidate before final support settlement; final index and resource table are subsequently refreshed without changing source or numerical measurements'}
(B/'final_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
