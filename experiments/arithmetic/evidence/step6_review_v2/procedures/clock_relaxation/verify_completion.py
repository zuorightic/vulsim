"""Read actual completed artifacts; no EDA invocation or new physical run."""
from pathlib import Path
import gzip,hashlib,json,re,sys

R=Path.cwd();sys.path.insert(0,str(R))
from experiments.arithmetic_dse.backend import stage_metrics
from experiments.arithmetic_dse.budget import cpu_seconds
from experiments.arithmetic_dse.platforms import library_data,profile
from experiments.arithmetic_dse.sdc import verify_sdc,rtl_ports
from experiments.arithmetic_dse.case_generator import generate_manifest

B=R/'build/step6-relaxed-clock-20261102';run=B/'run';m=json.loads((run/'manifest.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert m['status']=='completed' and m['stages_requested']=='grt' and len(m['metrics'])==2
for path,h in m['evidence_sha256'].items():assert sha(run/path)==h,path
for path,h in m['source_sha256'].items():assert sha(run/'source'/path)==h,path
p=profile('asap7');assert p['profile_sha256']==m['platform_profile']['profile_sha256']
for lib in m['libraries']:assert sha(Path(lib['path']))==lib['sha256']
libs,cells=library_data([Path(x) for x in m['effective_environment']['LIB_FILES'].split()],p)
sub=Path('asap7/arithmetic_probe/base');results=run/'results'/sub;reports=run/'reports'/sub
for f in ['1_synth.odb','2_floorplan.odb','3_place.odb','4_cts.odb','5_1_grt.odb']:
    assert (results/f).is_file(),f
ports=rtl_ports((run/'input.sv').read_text(),'Step6UDR128');stages=[]
for stage,sdc in [('synth','1_synth.sdc'),('grt','5_1_grt.sdc')]:
    contract=verify_sdc((results/sdc).read_text(),p,100000,ports,io_delay_max_ps=300)
    actual=stage_metrics(reports,stage,cells,100000,selected=p)
    original=next(x for x in m['metrics'] if x['stage']==stage)
    for key,value in actual.items():assert value==original[key],(stage,key,value,original[key])
    stages.append({'stage':stage,'sdc_sha256':sha(results/sdc),'sdc_contract':contract,
                   'metrics_recomputed':True,'metrics':{k:actual[k] for k in ['cell_area_um2','setup_worst_slack_ps','hold_worst_slack_ps','minimum_clock_period_ps','timing_coverage_complete','hold_review_required']}})
commands=[]
for c in m['commands']:
    recorded=json.loads(Path(c['log'].removesuffix('.log')+'.command.json').read_text())
    assert recorded['exit_code']==0 and not any(recorded[k] for k in ['timed_out','CPU_limit_exceeded','memory_limit_exceeded','unexpected_live_descendants'])
    assert not recorded['cleanup']['remaining_live_pids']
    commands.append({'log':str(Path(c['log']).relative_to(R)),'walltime_s':c['walltime_s'],'CPU_time_s':cpu_seconds(c['gnu_time'])})
children=[]
for path in sorted((run/'logs'/sub).glob('[1-5]*.log')):
    v=re.findall(r'Elapsed time: (?:(\d+):)?(\d+):(\d+(?:\.\d+)?)\[h:\]min:sec\. CPU time: user ([\d.]+) sys ([\d.]+)',path.read_text())
    if v:
        h,mins,secs,user,system=v[-1]
        children.append({'stage_log':path.name,'walltime_s':int(h or 0)*3600+int(mins)*60+float(secs),'CPU_time_s':float(user)+float(system),'precision':'ORFS child GNU-time log rounding; not additional charges'})
verification={'version':'step6-clock100ns-completion-verification-v1','status':'passed',
    'manifest':str((run/'manifest.json').relative_to(R)),'manifest_sha256':sha(run/'manifest.json'),
    'evidence_files_checked':len(m['evidence_sha256']),'source_snapshots_checked':len(m['source_sha256']),
    'completed_at':m['finished_at'],'stages':stages,'commands':commands,'child_stage_times':children,
    'physical_chain':{'walltime_s':commands[3]['walltime_s'],'CPU_time_s':commands[3]['CPU_time_s'],
        'sampled_process_tree_peak_rss_KiB':m['commands'][3]['sampled_process_tree_peak_rss_KiB'],
        'sampled_process_tree_peak_threads':m['commands'][3]['sampled_process_tree_peak_threads'],
        'thread_scope':'requested OpenROAD workers2; total sampled threads29 includes other pools/wrappers; not a hard OS-thread cap'},
    'scope':'grt estimated parasitics TT only; no final/SPEF/DRC/multicorner claim; mapping inherited'}
(B/'completion-verification.json').write_text(json.dumps(verification,indent=2)+'\n')

archived=R/'experiments/arithmetic/evidence/step6_graphs_v1/reports';rows=[]
for case in generate_manifest()['cases']:
    cid=case['id'];loaded={};hashes={}
    for group in ('B','C'):
        path=archived/(cid+'_'+group+'.json.gz');loaded[group]=json.loads(gzip.decompress(path.read_bytes()));hashes[group]=sha(path)
    b,c=loaded['B'],loaded['C'];s=c['selection'];regions=c['graph']['regions']
    internal=any(r['internally_cuttable'] for r in regions)
    role='mul_internal_structure_choice' if case['family'] in ('MUL','MAC','DOT2','H_M') else 'atomic_FP_whole_graph' if case['family'] in ('F1','F2','H_F1') else 'atomic_integer_whole_graph'
    if role!='mul_internal_structure_choice':assert not internal and s['evaluated_structures']==1
    rows.append({'case_id':cid,'family':case['family'],'role':role,'L':c['request']['L'],
        'report_source':'actual archived compressed BEIR; not regenerated',
        'archived_B_C_sha256':hashes,'C_structure_candidates':s['evaluated_structures'],
        'C_selected':s['selected_candidate'],'C_internally_cuttable_regions':sum(r['internally_cuttable'] for r in regions),
        'B_C_nodes_equal':b['graph']['nodes']==c['graph']['nodes'],'B_C_ports_equal':b['graph']['ports']==c['graph']['ports'],
        'B_C_stage_map_equal':b['stages']==c['stages'],'B_C_register_bits':[b['pipeline']['register_bits'],c['pipeline']['register_bits']],
        'region_templates':[r['template_id'] for r in regions]})
counts={role:sum(x['role']==role for x in rows) for role in sorted({x['role'] for x in rows})}
audit={'version':'step6-case-interpretation-audit-v1','cases':len(rows),'reports_read':len(rows)*2,
       'role_counts':counts,'atomic_cases_with_identical_B_C_nodes_and_stages':sum(x['role']!='mul_internal_structure_choice' and x['B_C_nodes_equal'] and x['B_C_stage_map_equal'] for x in rows),
       'D_evaluated':False,'interpretation':'candidate availability and actual scheduled graphs, not D benefit or exhaustive position-space proof',
       'cases_detail':rows}
(B/'case-role-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps({'completion':'passed','artifact_files':verification['evidence_files_checked'],'physical_chain':verification['physical_chain'],
    'stage_times':children,'role_counts':counts,'atomic_B_C_equal':audit['atomic_cases_with_identical_B_C_nodes_and_stages']},indent=2))
