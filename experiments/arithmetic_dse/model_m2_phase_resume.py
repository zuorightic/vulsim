"""Resume a preserved LEC proof and replay the exact CTS circuit from placement."""
import json
from pathlib import Path
import re
import shutil
import sys

CONFIG=Path(__file__).with_name('configs')/'model_asap7_m2_phase_resume_v1.json'
SUFFIX=Path('asap7/arithmetic_probe/base')
CHECKPOINTS=('1_2_yosys.v','1_2_yosys.sdc','1_synth.odb','1_synth.sdc','3_place.odb','3_place.sdc',
             '4_before_rsz_lec.v','4_after_rsz_lec.v')


def read(path):return json.loads(Path(path).read_text())


def spec(predecessor,tasks):
    from .model_m2_collection import sha,run_directory
    cfg=read(CONFIG);prior=read(predecessor);old_by_id={t['id']:t for t in prior['tasks']}
    if prior['id']!=cfg['parent_plan_id'] or cfg['automatic_retries']!=0:raise ValueError('unregistered phase continuation')
    attempts=[]
    for tid in cfg['failed_task_ids']:
        old=old_by_id[tid];source=run_directory(predecessor.parent,old);m=read(source/'manifest.json')
        commands=[c for c in m['commands'] if c['log'].endswith('/grt.log')]
        if (m['status']!='failed' or m.get('failure_code')!='timeout' or len(commands)!=1
                or not commands[0]['timed_out'] or commands[0]['cleanup']['remaining_live_pids']):
            raise ValueError('phase continuation requires the preserved settled timeout')
        checkpoints={}
        for name in CHECKPOINTS:
            path=source/'results'/SUFFIX/name;h=sha(path)
            if m['evidence_sha256'].get(str(path.relative_to(source)))!=h:raise ValueError('changed continuation checkpoint: '+name)
            checkpoints[name]=h
        lec=source/'logs'/SUFFIX/'4_rsz_lec_check.log'
        if 'Starting solver' not in lec.read_text() or 'Circuits are IDENTICAL' in lec.read_text():raise ValueError('not the unresolved LEC stage')
        attempts.append({'task_id':tid,'directory':str(source.resolve()),'manifest_sha256':sha(source/'manifest.json'),
                         'lec_log_sha256':sha(lec),'checkpoint_sha256':checkpoints,'lec_executable_sha256':sha(cfg['lec_executable'])})
    expected={t['id'] for t in tasks if t['split'] in ('train','validation') and t['family']=='divrem' and t['width']==32 and t['period_ps'] in (4500,1500)}
    if set(cfg['extended_task_ids'])!=expected or len(attempts)!=1:raise ValueError('phase continuation resource domain changed')
    for t in tasks:
        old=old_by_id[t['id']]
        if t.get('phase_resume') and t['id']!=attempts[0]['task_id']:raise ValueError('unregistered phase-resume task')
        for key in ('rtl_sha256','sample_contract_sha256','split','period_ps','abc_target_ps','profile_sha256','mapping_source_task'):
            if t[key]!=old[key]:raise ValueError('phase continuation changed measurement identity: '+key)
        if t['id'] in expected:t['route_timeout_s']=cfg['route_timeout_s']
        if t['id']==attempts[0]['task_id']:t['phase_resume']=attempts[0]
    return {'path':str(CONFIG.resolve()),'sha256':sha(CONFIG),'failed_attempts':attempts,
            'priority_task_ids':cfg['failed_task_ids'],'reason':cfg['reason'],'rolling_fitting':True,'priority_wave_limit':cfg['max_fitting_tasks']}


def render_observational_cts(original):
    marker='    run_lec_test 4_rsz 4_before_rsz_lec.v 4_after_rsz_lec.v'
    if original.count(marker)!=1:raise ValueError('unsupported CTS LEC checkpoint insertion')
    return original.replace(marker,
        '    orfs_write_db $::env(RESULTS_DIR)/4_1_post_repair_pre_lec.odb\n'
        '    orfs_write_sdc $::env(RESULTS_DIR)/4_1_post_repair_pre_lec.sdc\n'+marker)


def validate_lec(log,inputs,outputs):
    if 'SAT solver finished: UNSAT' not in log or 'Circuits are IDENTICAL' not in log or 'Found difference' in log:
        raise ValueError('LEC did not produce an explicit complete equivalence result')
    for design in (0,1):
        for kind,count in (('PIs',inputs),('POs',outputs)):
            if not re.search(rf'size of {kind} in circuit {design}: {count}(?!\d)',log):raise ValueError('LEC boundary coverage mismatch')
        for kind in ('inputs','outputs'):
            if not re.search(rf'size of diff{design} {kind}: 0(?!\d)',log):raise ValueError('LEC boundary mismatch')


def validate_replayed_pair(proof_path,before,after):
    from .model_m2_collection import sha
    p=read(proof_path)
    if p['status']!='passed' or p['command_exit_code']!=0:raise ValueError('LEC proof not passed')
    if sha(p['log_path'])!=p['log_sha256']:raise ValueError('changed LEC proof log')
    validate_lec(Path(p['log_path']).read_text(),p['boundary']['primary_inputs'],p['boundary']['primary_outputs'])
    for actual,key in ((before,'before_sha256'),(after,'after_sha256')):
        if sha(actual)!=p[key]:raise ValueError('replayed CTS circuit differs from proved netlist')
    if sha(p['executable'])!=p['executable_sha256']:raise ValueError('changed LEC proof executable')
    for lib in p['libraries']:
        if sha(lib['path'])!=lib['sha256']:raise ValueError('changed LEC proof library')
    print('LEC_RESUME_VERIFIED exact pre/post netlists and complete boundaries')


def seed(args,out,results,environment,command,tools,execute,manifest):
    from .model_m2_collection import task,sha
    from .sdc import verify_sdc,rtl_ports
    _,_,t=task(args);binding=t['phase_resume'];source=Path(binding['directory']);old=read(source/'manifest.json');cfg=read(CONFIG)
    if sha(source/'manifest.json')!=binding['manifest_sha256'] or args.resume_synth_from.resolve()!=source.resolve():raise ValueError('changed phase resume source')
    for name,tool in tools.items():
        if tool['sha256']!=old['tools'][name]['sha256']:raise ValueError('changed continuation physical tool')
    for name in ('LIB_FILES','TECH_LEF','SC_LEF','CORNER','ASAP7_USE_VT','LIB_MODEL','TC_TEMPERATURE','ABC_DRIVER_CELL','ABC_LOAD_IN_FF','YOSYS_MAX_THREADS'):
        if environment.get(name)!=old['effective_environment'].get(name):raise ValueError('changed continuation environment: '+name)
    for name,h in old['files_sha256'].items():
        path=Path(name)
        if path.is_relative_to(args.orfs.resolve()) or path.is_relative_to(Path(__file__).with_name('backend')):
            if sha(path)!=h:raise ValueError('changed continuation physical asset: '+name)
    for lib in old['libraries']:
        if sha(lib['path'])!=lib['sha256']:raise ValueError('changed continuation library')
    results.mkdir(parents=True,exist_ok=True)
    if any(results.iterdir()):raise ValueError('continuation requires fresh results')
    for name,h in binding['checkpoint_sha256'].items():
        original=source/'results'/SUFFIX/name
        if sha(original)!=h:raise ValueError('changed continuation checkpoint')
        shutil.copy2(original,results/name)
    verify_sdc((results/'3_place.sdc').read_text(),old['platform_profile'],args.period_ps,rtl_ports((out/'input.sv').read_text(),args.top))
    native=out/'logs'/SUFFIX/'1_synth.json';native.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source/'logs'/SUFFIX/'1_synth.json',native)
    for name in ('1_2_yosys.v','1_2_yosys.sdc','1_synth.odb','1_synth.sdc','3_place.odb','3_place.sdc'):
        command.append('--assume-old='+str(results/name))
    proof_dir=out/'logs'/SUFFIX/'lec_resume';proof_dir.mkdir()
    before,after=results/'4_before_rsz_lec.v',results/'4_after_rsz_lec.v'
    # These two exact files are immutable proof inputs; CTS replay writes new copies later.
    for p in (before,after):shutil.copy2(p,proof_dir/p.name)
    before,after=proof_dir/before.name,proof_dir/after.name
    log=proof_dir/'solver.log';config=proof_dir/'request.yml'
    config.write_text(json.dumps({'format':'verilog','verification':'lec','input_paths':[str(before),str(after)],
                                 'liberty_files':[lib['path'] for lib in old['libraries']],
                                 'solver':cfg['lec_solver'],'log_file':str(log)},indent=2)+'\n')
    if sha(cfg['lec_executable'])!=binding['lec_executable_sha256']:raise ValueError('changed continuation LEC binary')
    manifest['active_stage']='lec_resume'
    record=execute([cfg['lec_executable'],'--config',str(config)],'lec-resume',cfg['lec_timeout_s'])
    validate_lec(log.read_text(),cfg['expected_LEC_boundary']['primary_inputs'],cfg['expected_LEC_boundary']['primary_outputs'])
    proof=proof_dir/'proof.json';proof.write_text(json.dumps({'status':'passed','command_exit_code':record['exit_code'],
         'reservation_id':record['budget_reservation_id'],'request_sha256':sha(config),'log_path':str(log),'log_sha256':sha(log),
         'before_sha256':sha(before),'after_sha256':sha(after),'boundary':cfg['expected_LEC_boundary'],
         'executable':cfg['lec_executable'],'executable_sha256':sha(cfg['lec_executable']),'libraries':old['libraries']},indent=2)+'\n')
    wrapper=out/'verify-lec-resume.py'
    wrapper.write_text('import sys\nfrom pathlib import Path\nsys.path.insert(0,'+repr(str(Path(__file__).resolve().parents[2]))+')\n'
                       'from experiments.arithmetic_dse.model_m2_phase_resume import validate_replayed_pair\n'
                       'validate_replayed_pair(*map(Path,sys.argv[1:]))\n')
    cts=out/'flow-scripts/cts.tcl';original=cts.read_text();marker='    run_lec_test 4_rsz 4_before_rsz_lec.v 4_after_rsz_lec.v'
    if original.count(marker)!=1:raise ValueError('unsupported CTS continuation marker')
    cts.unlink();cts.write_text(original.replace(marker,
        f'    exec {{{sys.executable}}} -B {{{wrapper}}} {{{proof}}} $::env(RESULTS_DIR)/4_before_rsz_lec.v $::env(RESULTS_DIR)/4_after_rsz_lec.v\n'
        '    puts "Repair timing output passed lec test: exact netlists reuse completed standalone proof"'))
    manifest['files_sha256'].update({str(path):sha(path) for path in (cts,wrapper,proof,config)})
    return {'mode':'placement_checkpoint_CTS_replay_with_exact_LEC_proof','source_manifest_sha256':binding['manifest_sha256'],
            'source_run':str(source),'checkpoint_sha256':binding['checkpoint_sha256'],'proof_path':str(proof),'proof_sha256':sha(proof),
            'reused_stages':['synthesis','floorplan','placement'],'executed_stages':['complete_LEC','CTS_replay','global_route'],
            'SAT_memory_resumed':False,'physical_clock_or_optimization_changed':False,
            'timing_scope':'new leaf durations only; failed ancestor costs retained separately, no stitched cold-flow runtime claim'}
