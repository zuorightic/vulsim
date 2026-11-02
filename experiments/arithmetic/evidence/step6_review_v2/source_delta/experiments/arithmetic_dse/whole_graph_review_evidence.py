"""Step6 width-proof correction and bounded backend recheck successor."""
import argparse
import gzip
import hashlib
import json
import math
import tarfile
import tempfile
from pathlib import Path
from .budget import usage,cpu_seconds
from .whole_graph_evidence import read,document,sha,ledger_entries
from .interfaces_evidence import same
from .whole_graph_checks import verify_safe_divisors
from .backend import stage_metrics,mapped_netlist_hash
from .sdc import verify_sdc,rtl_ports

ROOT=Path(__file__).resolve().parents[2]
FREEZE='experiments/arithmetic/whole_graph_freeze_v2.json'

def software(root,e):
    old=document(e/'old_cpp.json');new=document(e/'new_cpp.json')
    same(old['observed_wrong_acceptances'],5,'old real C++ entry reproduced defect')
    same(new['observed_wrong_acceptances'],0,'corrected real C++ entry')
    same(new['historical_reports'],176,'actual C++ historical replay reports')
    same(new['historical_Div_Mod'],186,'actual C++ historical replay Div/Mod')
    same(len(new['tests']),14,'native width proof cases')
    for row in new['tests']:
        same(row['accepted'],row['expected_safe'],'native case '+row['case'])
        if not row['accepted']:same(row['failure_code'],'unsafe_divisor','correct diagnostic')
    # Independently execute the actual-width proof over the original saved
    # BEIR and retained raw vectors, not regenerated substitutes.
    count=reports=0
    for p in (root/'experiments/arithmetic/evidence/step6_graphs_v1/reports').glob('*.json.gz'):
        count+=verify_safe_divisors(document(p));reports+=1
    same((reports,count),(176,186),'portable historical safety replay')
    identities=document(e/'regenerated_identity.json')
    same(len(identities),176,'all regenerated actual reports and RTL')
    for row in identities:
        for extension,key in (('json','report_sha256'),('sv','rtl_sha256')):
            original=root/'experiments/arithmetic/evidence/step6_graphs_v1/reports'/(row['name']+'.'+extension+'.gz')
            same(hashlib.sha256(gzip.decompress(original.read_bytes())).hexdigest(),row[key],'regenerated/old byte identity')
    from regression.arithmetic_divisor import example
    negatives=[example(),example(ne=True),example(branches=(256,1)),example(branches=(256,512),nested=True)]
    for graph in negatives:
        try:verify_safe_divisors(graph)
        except ValueError as error:
            if 'unsafe_divisor' not in str(error):raise
        else:raise ValueError('truncated nonzero proof counterexample accepted')
    for graph in (example(result=16),example(ne=True,result=16),example(branches=(257,1)),example(branches=(257,513),nested=True),example(source=8,extend=True),example(ne=True,source=8,extend=True)):
        same(verify_safe_divisors(graph),1,'safe heterogeneous-width Ite retained')
    from .case_generator import generate_manifest
    audit=document(e/'case-role-audit.json');cases={x['id']:x for x in generate_manifest()['cases']}
    same({x['case_id'] for x in audit['cases_detail']},set(cases),'case role audit covers all 43 cases')
    roles={};atomic_equal=0
    for row in audit['cases_detail']:
        cid=row['case_id'];family=cases[cid]['family']
        role='mul_internal_structure_choice' if family in ('MUL','MAC','DOT2','H_M') else 'atomic_FP_whole_graph' if family in ('F1','F2','H_F1') else 'atomic_integer_whole_graph'
        same(row['role'],role,'actual structure capability role '+cid);roles[role]=roles.get(role,0)+1
        loaded={}
        for group in ('B','C'):
            path=root/'experiments/arithmetic/evidence/step6_graphs_v1/reports'/(cid+'_'+group+'.json.gz')
            same(sha(path),row['archived_B_C_sha256'][group],'role audit consumes actual frozen graph');loaded[group]=document(path)
        b,c=loaded['B'],loaded['C'];nodes_equal=b['graph']['nodes']==c['graph']['nodes'];stages_equal=b['stages']==c['stages']
        same(nodes_equal,row['B_C_nodes_equal'],'actual B/C nodes');same(stages_equal,row['B_C_stage_map_equal'],'actual B/C placement')
        same(c['selection']['evaluated_structures'],row['C_structure_candidates'],'actual candidate count')
        same(sum(x['internally_cuttable'] for x in c['graph']['regions']),row['C_internally_cuttable_regions'],'actual internal boundaries')
        if role!='mul_internal_structure_choice':
            same(row['C_structure_candidates'],1,'atomic graph has one structure');same(row['C_internally_cuttable_regions'],0,'no invented atomic split')
            atomic_equal+=nodes_equal and stages_equal
    same(roles,audit['role_counts'],'case role counts');same(atomic_equal,audit['atomic_cases_with_identical_B_C_nodes_and_stages'],'atomic B/C equality')
    same((audit['cases'],audit['reports_read']),(43,86),'actual audit denominator')
    return {'native_cases':14,'old_wrong_acceptances':5,'new_wrong_acceptances':0,'historical_reports':reports,'historical_Div_Mod':count,'regenerated_byte_identity':176,'case_role_counts':roles,'atomic_B_C_equal':atomic_equal,'existing_functional_traces_inherited':'exact RTL bytes; no new RTL simulation claimed'}

def capacity(root,e,parent_directory=None):
    a=document(e/'admission.json');outcome=document(e/'outcome.json')
    thread_fix=a.get('correction_kind')=='yosys_thread_limit'
    completion=a.get('execution_mode')=='complete_initial_backend'
    relaxation=a.get('purpose')=='arithmetic_clock_relaxation_only'
    expected_caps={'synth':1,'grt':1,'final':0} if relaxation else {'synth':3,'grt':1,'final':0} if thread_fix else {'synth':6,'grt':2,'final':0}
    same(a['call_caps'],expected_caps,'bounded correction scope')
    same(a['memory_limit_MiB'],32768,'explicit 32 GiB exception')
    same(a['synthesis_timeout_s'],300 if relaxation else 7200 if completion else 1800 if thread_fix else 900,'bounded synth time')
    same(a['post_synthesis_through_grt_timeout_s'],14400 if completion or relaxation else 3600,'bounded complete post-synth chain')
    same(a['automatic_retries'],0,'no automatic retry')
    policy=root/'experiments/arithmetic_dse/configs/backend_policy_v5.json'
    same(sha(policy),a['policy_sha256'],'unchanged shared policy identity')
    global_limits=document(policy)['resources'];start=a['starting_usage_live']
    wall=a['call_caps']['synth']*a['synthesis_timeout_s']+a['call_caps']['grt']*a['post_synthesis_through_grt_timeout_s']+a['support_envelope']['walltime_s']
    same(a['worst_case_walltime_s'],wall,'complete physical and support launch envelope')
    same(a['CPU_envelope_s'],2*wall,'complete CPU launch envelope')
    if (start['pending'] or start['walltime_s']+wall>global_limits['max_global_walltime_h']*3600
            or start['CPU_time_s']+2*wall>global_limits['max_tool_CPU_time_h']*3600):
        raise ValueError('physical completion/recheck launch envelope not funded')
    for stage,key in [('synth','max_synthesis_calls'),('grt','max_global_route_calls'),('final','max_detailed_route_calls')]:
        if start[stage]+a['call_caps'][stage]>global_limits[key]:raise ValueError('launch calls exceed shared funding')
    parent_admission=(parent_directory/'admission.json') if thread_fix or relaxation else root/'experiments/arithmetic/evidence/step6_capacity_v1/admission.json'
    same(sha(parent_admission),a['parent_admission']['sha256'],'original task lineage')
    oldtasks={t['id']:t for t in document(parent_admission)['tasks']}
    tasks={t['id']:t for t in a['tasks']};same(set(tasks),{r['task_id'] for r in outcome['runs']},'all six results or explicit paused tasks')
    rows=[]
    for row in outcome['runs']:
        t=tasks[row['task_id']];old=oldtasks[t['supersedes_task_id']]
        for k in ('rtl_sha256','top','abc_target_ps','stage','L','II'):same(t[k],old[k],'unchanged recheck condition '+k)
        if relaxation:
            same((old['period_ps'],t['period_ps'],t['abc_target_ps'],t['io_delay_max_ps']),(1500,100000,1500,300),'one named SDC relaxation with fixed mapping/IO')
        else:same(t['period_ps'],old['period_ps'],'unchanged recheck SDC')
        if row['status']=='not_run':
            same(row['physical_calls'],0,'paused control has no call')
            rows.append({'task_id':t['id'],'status':'not_run'});continue
        run=e/'runs'/t['id'];m=document(run/'manifest.json.gz')
        same(m['task_id'],t['id'],'actual task identity')
        same(m['admission_id'],a['id'],'actual admission identity')
        same(m['period_ps'],t['period_ps'],'actual SDC request')
        same(m['abc_target_ps'],t['abc_target_ps'],'actual ABC request')
        same(m['platform_profile']['profile_sha256'],t['profile_sha256'],'actual platform profile')
        same(row['status'],m['status'],'outcome and raw manifest')
        same(m['memory_limit_MiB'],32768,'actual memory enforcement')
        if thread_fix or relaxation:
            same(m['effective_environment']['YOSYS_MAX_THREADS'],'2','effective Make Yosys thread limit')
            same(m['tool_thread_controls']['YOSYS_MAX_THREADS'],2,'actual process Yosys thread control')
            if not all('YOSYS_MAX_THREADS=2' in command['command'] for command in m['commands']):
                raise ValueError('actual tool invocation omitted Yosys thread cap')
        if relaxation:
            source=parent_directory/'runs'/old['id']/'manifest.json.gz';previous=document(source)
            same(hashlib.sha256(gzip.decompress(source.read_bytes())).hexdigest(),t['source_manifest_sha256'],'reused source manifest identity')
            same((previous['status'],previous['failure_stage'],previous['failure_code']),('failed','grt','timeout'),'original timeout retained')
            reuse=m['checkpoint_reuse'];same(reuse['reused'],['Yosys_ABC_mapping_only'],'only mapped graph reused')
            same(reuse['old_ODB_or_old_SDC_copied'],False,'fresh SDC and complete physical chain')
            same(reuse['source_manifest_sha256'],t['source_manifest_sha256'],'mapping provenance')
            source_metric=next(x for x in previous['metrics'] if x['stage']=='synth')
            same(reuse['normalized_mapped_netlist_sha256'],source_metric['mapped_netlist_sha256'],'mapping graph unchanged')
            same(reuse['source_netlist_file_sha256'],t['mapped_netlist_file_sha256'],'mapped checkpoint file identity')
            netlist='results/asap7/arithmetic_probe/base/1_2_yosys.v'
            same(m['evidence_sha256'][netlist],previous['evidence_sha256'][netlist],'actual mapped bytes unchanged')
            same(m['evidence_sha256'][netlist],t['mapped_netlist_file_sha256'],'actual mapped bytes bound by admission')
            same(next(x for x in m['metrics'] if x['stage']=='synth')['mapped_netlist_sha256'],source_metric['mapped_netlist_sha256'],'new synthesized graph identity')
        if completion:
            checkpoint=m['observational_checkpoint']
            original=read(run/'base_synth.tcl.gz');executed=read(run/'executed_synth.tcl.gz')
            same(hashlib.sha256(original.encode()).hexdigest(),checkpoint['source_script_sha256'],'original synth script')
            same(hashlib.sha256(executed.encode()).hexdigest(),checkpoint['executed_script_sha256'],'actual checkpoint script')
            inserted='  write_rtlil $::env(RESULTS_DIR)/1_1_pre_abc.rtlil\n'
            same(executed.count(inserted),1,'one observational checkpoint')
            same(executed.replace(inserted,''),original,'all original synthesis passes preserved')
        same(hashlib.sha256(read(run/'input.sv.gz').encode()).hexdigest(),t['rtl_sha256'],'actual RTL identity')
        cells=document(run/'liberty_cells.json.gz')['cells'];metrics=[]
        for metric in m['metrics']:
            stage=metric['stage'];sdc={'synth':'1_synth','grt':'5_1_grt'}[stage]
            checked_sdc=verify_sdc(read(run/(sdc+'.sdc.gz')),m['platform_profile'],t['period_ps'],rtl_ports(read(run/'input.sv.gz'),t['top']),io_delay_max_ps=300 if relaxation else None)
            same(checked_sdc,m['sdc_contracts'][stage],'runtime/offline SDC agreement')
            with tempfile.TemporaryDirectory(prefix='step6-recheck-reports-') as tmp:
                reports=Path(tmp)
                for p in (run/'reports').glob('vulsim_'+stage+'*'):(reports/p.name.removesuffix('.gz')).write_text(read(p))
                recomputed=stage_metrics(reports,stage,cells,t['period_ps'],selected=m['platform_profile'])
            for key,value in recomputed.items():
                if key!='raw_reports_prefix':same(value,metric[key],'actual '+stage+' metric '+key)
            same(metric['abc_target_ps'],t['abc_target_ps'],'actual ABC target')
            metrics.append(metric)
        for command in m['commands']:
            same(command['cleanup']['remaining_live_pids'],[],'all task descendants cleaned')
            same(command['unexpected_live_descendants'],False,'no live descendants')
        if m['status']=='completed':
            same([x['stage'] for x in metrics],['synth','grt'] if t['stage']=='grt' else ['synth'],'complete requested stages')
        else:
            same(row['failure_code'],m['failure_code'],'retained failure classification')
        rows.append({'task_id':t['id'],'status':m['status'],'failure_code':m.get('failure_code'),'metrics':[{k:x[k] for k in ('stage','cell_area_um2','setup_worst_slack_ps','hold_worst_slack_ps','minimum_clock_period_ps','timing_coverage_complete','measured_feasibility','hold_feasible_at_TT')} for x in metrics]})
    return rows

def verify(root=ROOT,external=False,parents=True):
    root=Path(root);f=document(root/FREEZE);e=root/f['evidence_directory'];c=root/f['capacity_directory']
    from .freeze_history import source_location,MUTABLE_DOCUMENTATION
    drift=[]
    for path,h in f['files_sha256'].items():
        same(sha(source_location(root,FREEZE,path,h)),h,'current source or explicit frozen documentation '+path)
        same(sha(root/f['source_snapshots'][path]),h,'source snapshot '+path)
        if path in MUTABLE_DOCUMENTATION and (not (root/path).exists() or sha(root/path)!=h):drift.append(path)
    for path,h in f['historical_freezes'].items():same(sha(root/path),h,'historical freeze unchanged')
    for path,h in document(root/f['preservation']).items():same(sha(root/path),h,'historical payload unchanged')
    for package in f['packages']:
        index=root/package['index'];same(sha(index),package['sha256'],'new index')
        sizes=[]
        for path,h in document(index)['files_sha256'].items():same(sha(root/path),h,'new evidence');sizes.append((root/path).stat().st_size)
        sizes.append(index.stat().st_size)
        if package['role']=='software':sizes.append((root/FREEZE).stat().st_size)
        if max(sizes)>1048576 or sum(sizes)>5242880:raise ValueError('new evidence storage target exceeded')
    s=software(root,e);p=capacity(root,c)
    thread_results=capacity(root,c/'thread_correction',c)
    completion_results=capacity(root,c/'completion',c/'thread_correction')
    clock_results=capacity(root,c/'clock_relaxation',c/'completion')
    d=document(e/'usage_delta.json');same(sha(root/d['prefix']),d['prefix_sha256'],'ledger prefix')
    entries=ledger_entries(root,e/'usage_delta.json');r=document(e/'resources.json')
    same(usage(entries),r['cumulative_usage'],'cumulative charges');same(usage(d['entries']),r['new_usage'],'new charges')
    same(usage(entries)['pending'],0,'no unsettled charges')
    receipts=document(e/'receipts.json.gz');same({x['id'] for x in receipts},{x['id'] for x in d['entries']},'all leaf receipts')
    for row in receipts:
        charge=next(x for x in d['entries'] if x['id']==row['id']);record=row['record']
        same(record['walltime_s'],charge['walltime_s'],'actual walltime');same(record['exit_code'],charge['exit_code'],'actual outcome')
        same(record['cleanup']['remaining_live_pids'],[],'cleanup')
        if charge.get('CPU_accounting')=='full_reservation_missing_CPU_evidence':same(charge['CPU_time_s'],record['CPU_limit_s'],'conservative CPU')
        else:
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'time';path.write_text(row['GNU_time']);same(cpu_seconds(path),charge['CPU_time_s'],'GNU actual CPU')
    live=root/'experiments/arithmetic/backend_usage.json'
    if live.exists():same(document(live)['entries'][:len(entries)],entries,'live immutable prefix')
    checked_netlists=0
    if external:
        for artifact in document(c/'artifact_catalog.json.gz'):
            path=root/artifact['location']
            if not path.is_file():raise ValueError('artifact_unavailable: '+artifact['location'])
            same(sha(path),artifact['stored_sha256'],'actual full archive')
            with tarfile.open(path,'r:gz') as tar:
                same(tar.getnames(),[x['relative_member_path'] for x in artifact['members']],'archive inventory')
                for item in artifact['members']:
                    stream=tar.extractfile(item['relative_member_path']);h=hashlib.sha256();size=0
                    member=Path(item['relative_member_path']);netlist=(member.name=='1_2_yosys.v');chunks=[]
                    while chunk:=stream.read(1024*1024):
                        h.update(chunk);size+=len(chunk)
                        if netlist:chunks.append(chunk)
                    same(h.hexdigest(),item['sha256'],'archive member');same(size,item['content_size_bytes'],'archive member size')
                    if netlist:
                        sub={'physical':c,'physical-threads':c/'thread_correction','physical-complete':c/'completion','clock_relaxation':c/'clock_relaxation'}[member.parts[0]]
                        manifest=document(sub/'runs'/member.parts[1]/'manifest.json.gz')
                        metric=next((x for x in manifest['metrics'] if x['stage']=='synth'),None)
                        if metric is not None:
                            same(mapped_netlist_hash(b''.join(chunks).decode()),metric['mapped_netlist_sha256'],'actual normalized mapped netlist')
                            checked_netlists+=1
    parent=None
    if parents:
        from .whole_graph_evidence import verify_original
        parent=verify_original(root,external,True)['status']
    return {'status':'passed','scope':'step6 whole-graph/safety and declared finite capacity acceptance; D/training/main matrix remain step7/8','backend_completion':all(row['status']=='completed' for row in clock_results) and all(row['status']=='completed' for row in p if 'fp32_serial' in row['task_id']),
            'software':s,'initial_recheck':p,'thread_corrected_UDR':thread_results,'completion_UDR_original_clock':completion_results,'UDR_100ns':clock_results,'documentation_drift':drift,'parent_status':parent,'new_usage':r['new_usage'],'cumulative_usage':r['cumulative_usage'],'normalized_netlists_recomputed':checked_netlists,'external_artifacts':'actual local bytes read; remote retention unconfirmed' if external else 'not requested; compact evidence only'}

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT);a.add_argument('--verify-external',action='store_true');a.add_argument('--no-parents',action='store_true');n=a.parse_args();print(json.dumps(verify(n.root,n.verify_external,not n.no_parents),indent=2))
