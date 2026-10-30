"""Audit the four-platform connection freeze without build or EDA tools."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from .backend import stage_metrics,verify_orfs_area
from .budget import usage,usage_by,cpu_seconds
from .characterization import mapped_netlist_hash
from .platforms import unit_scale
from .sdc import verify_sdc,rtl_ports

ROOT=Path(__file__).resolve().parents[2]
FREEZE='experiments/arithmetic/backend_freeze_v6.json'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def same(actual,expected,label):
    if isinstance(actual,float) or isinstance(expected,float):
        equal=isinstance(actual,(int,float)) and isinstance(expected,(int,float)) and math.isclose(actual,expected,rel_tol=1e-10,abs_tol=1e-9)
    else:
        equal=actual==expected
    if not equal:raise ValueError(f'evidence mismatch: {label}: {actual!r} != {expected!r}')


def verify(root=ROOT,verify_external=False):
    root=Path(root)
    freeze=json.loads((root/FREEZE).read_text())
    directory=root/freeze['evidence_directory']
    for relative,expected in freeze['files_sha256'].items():
        same(digest(root/relative),expected,relative)
        same(digest(root/freeze['validated_source_snapshot']/relative),expected,'snapshot '+relative)
    for relative,expected in freeze['historical_freezes'].items():
        same(digest(root/relative),expected,'historical freeze '+relative)
    for relative in freeze['retired_active_paths']:
        if (root/relative).exists():raise ValueError('retired active implementation remains: '+relative)
    same(digest(root/freeze['evidence_index']),freeze['evidence_index_sha256'],'evidence index')
    index=json.loads((root/freeze['evidence_index']).read_text())
    for relative,expected in index['files_sha256'].items():same(digest(root/relative),expected,relative)
    previous=json.loads((root/freeze['supersedes']['path']).read_text())
    same(digest(root/previous['evidence_index']),previous['evidence_index_sha256'],'previous evidence index')
    previous_index=json.loads((root/previous['evidence_index']).read_text())
    for relative,expected in previous_index['files_sha256'].items():same(digest(root/relative),expected,'previous '+relative)
    audit=json.loads((directory/'previous_acceptance_audit.json').read_text())
    same(audit['previous_freeze_sha256'],digest(root/freeze['supersedes']['path']),'invalidated previous freeze')
    rejected_stages=0
    for item in audit['runs']:
        previous_run=root/previous['evidence_directory']/'runs'/item['task_id']
        m=json.loads((previous_run/'manifest.json').read_text())
        for stage in item['stages']:
            path=root/stage['path']
            same(digest(path),stage['sha256'],'original SDC retained')
            text=gzip.decompress(path.read_bytes()).decode()
            try:
                verify_sdc(text,m['platform_profile'],m['period_ps'],rtl_ports((previous_run/'input.sv').read_text()))
            except ValueError as error:
                same(stage['status'],'invalid_sdc_contract','previous SDC invalidation')
                same(stage['reason'],str(error),'previous SDC rejection reason')
                rejected_stages+=1
            else:
                same(stage['status'],'valid_unaffected','unaffected previous SDC')
        if item['stages']:
            same(item['acceptance_status'],'unaffected' if m['target_platform']=='asap7' else 'invalid_sdc_contract',
                 'previous run acceptance classification')
    if not rejected_stages:raise ValueError('missing invalidated ns SDC evidence')
    before=json.loads((directory/'usage_before.json').read_text())
    after=json.loads((directory/'usage_after.json').read_text())
    same(after['entries'][:len(before['entries'])],before['entries'],'immutable historical charges')
    extra=after['entries'][len(before['entries']):]
    if usage(after['entries'])['pending']:raise ValueError('pending backend reservation')
    if len({e['id'] for e in after['entries']})!=len(after['entries']):raise ValueError('duplicate charges')
    admissions={}
    for path in (directory/'admissions').glob('*.json'):
        admitted=json.loads(path.read_text())
        if (admitted['automatic_retries'] or admitted['main_case_targets']
                or admitted['later_bulk_or_model_work_authorized']):
            raise ValueError('connection admission expanded to unreviewed work')
        admissions[admitted['id']]=(admitted,path)
    for admitted,path in admissions.values():
        if admitted.get('parent_admission'):
            parent=admitted['parent_admission']
            same(digest(admissions[parent['id']][1]),parent['sha256'],'archived parent admission')
    seen=[]
    for entry in extra:
        if entry['stage'] is None:continue
        admitted,path=admissions[entry['admission_id']]
        same(entry['admission_sha256'],digest(path),'charged admission')
        task=next(t for t in admitted['tasks'] if t['id']==entry['task_id'])
        same(task['platform'],entry['target_platform'],'charged platform')
        related=admitted.get('related_admission_ids',[admitted['id']])
        seen.append(entry)
        for stage,cap in admitted['call_caps'].items():
            if sum(e['stage']==stage and e['admission_id'] in related for e in seen)>cap:
                raise ValueError('connection lineage exceeded its predeclared call envelope')
    resources=json.loads((directory/'resources.json').read_text())
    same(resources['new_usage'],usage(extra),'incremental resources')
    same(resources['cumulative_usage'],usage(after['entries']),'cumulative resources')
    same(resources['new_by_platform'],usage_by(extra,'target_platform'),'platform accounting')
    receipts=json.loads((directory/'command_index.json').read_text())
    if {r['id'] for r in receipts}!={e['id'] for e in extra}:raise ValueError('incomplete command receipts')
    for item in receipts:
        entry=next(e for e in extra if e['id']==item['id'])
        record=json.loads((root/item['record']).read_text())
        same(record['walltime_s'],entry['walltime_s'],'leaf walltime')
        same(record['exit_code'],entry['exit_code'],'leaf status')
        same(cpu_seconds(root/item['CPU_report']),entry['CPU_time_s'],'GNU time charge')
        if (record['cleanup']['remaining_live_pids'] or record['unexpected_live_descendants']
                or record['timed_out'] or record['memory_limit_exceeded'] or record['CPU_limit_exceeded']):
            raise ValueError('unclean or resource-limited leaf requires explicit failed-scope acceptance')
    summary=json.loads((directory/'summary.json').read_text())
    platforms={}
    common_multiplier_hashes=set()
    checked_sdc_stages=0
    for item in summary['runs']:
        run=root/item['artifact_directory'] if item.get('artifact_directory') else directory/'runs'/item['task_id']
        manifest=json.loads((run/'manifest.json').read_text())
        same(manifest['status'],item['status'],'run outcome')
        p=manifest['platform_profile']
        if item.get('carried_forward_unaffected') and p['platform']!='asap7':
            raise ValueError('only the unaffected ASAP7 platform may be carried forward')
        if manifest['status']=='failed':
            if not manifest.get('failure_stage') or not manifest.get('failure_reason'):
                raise ValueError('failure lacks stage/reason')
        if not manifest.get('mapping_context'):continue
        context=manifest['mapping_context']
        context_hash=hashlib.sha256(json.dumps(context,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        same(context_hash,manifest['mapping_context_sha256'],'mapping context')
        same(context['platform'],p['platform'],'platform identity')
        same(context['sdc_period_ps'],manifest['period_ps'],'separate SDC axis')
        same(context['abc_target_ps'],manifest['abc_target_ps'],'separate ABC axis')
        if any(lib['voltage_V']!=p['voltage_V'] or lib['temperature_C']!=p['temperature_C']
               or lib['time_to_ps']!=unit_scale(1,p['time_unit'],kind='time')
               or lib['capacitance_to_fF']!=unit_scale(1,p['capacitance_unit'],kind='capacitance')
               for lib in manifest['libraries']):raise ValueError('selected library PVT/unit mismatch')
        script=(run/'abc_speed.script').read_text()
        same(digest(run/'abc_speed.script'),context['abc_script_sha256'],'rendered ABC script')
        for line in script.splitlines():
            words=line.split()
            if words and words[0] in ('&nf','upsize','dnsize'):
                if '-D' not in words or float(words[words.index('-D')+1])!=manifest['abc_target_ps']:
                    raise ValueError('ABC target is not bound to mapping')
        cells=json.loads((run/'liberty_cells.json').read_text())['cells']
        for measured in manifest['metrics']:
            stage=measured['stage']
            sdc_file={'synth':'1_synth.sdc.gz','grt':'5_1_grt.sdc.gz','final':'6_final.sdc.gz'}[stage]
            sdc_check=verify_sdc(gzip.decompress((run/sdc_file).read_bytes()).decode(),p,manifest['period_ps'],
                rtl_ports((run/'input.sv').read_text()),io_delay_max_ps=manifest['io_delay_max_ps'])
            checked_sdc_stages+=1
            if not item.get('carried_forward_unaffected'):
                same(manifest['sdc_contracts'][stage],sdc_check,'live and portable SDC contract')
            actual=stage_metrics(run/'reports',stage,cells,manifest['period_ps'],selected=p)
            for key,value in actual.items():
                if key!='raw_reports_prefix':same(measured[key],value,f'{item["task_id"]}/{stage}/{key}')
            verify_orfs_area(actual['cell_area_um2'],measured['orfs_stdcell_area_um2'])
            if stage=='synth':
                mapped=gzip.decompress((run/'1_2_yosys.v.gz').read_bytes()).decode()
                same(mapped_netlist_hash(mapped),measured['mapped_netlist_sha256'],'mapped netlist identity')
            if stage=='final':
                route=json.loads((run/'logs/5_2_route.json').read_text())
                same(route['detailedroute__route__drc_errors'],measured['detailed_route_drc_errors'],'route DRC')
                spef=gzip.decompress((run/'6_final.spef.gz').read_bytes())
                same(hashlib.sha256(spef).hexdigest(),item['extracted_spef_sha256'],'actual extracted SPEF')
                if '*SPEF' not in spef[:200].decode(errors='replace'):raise ValueError('invalid SPEF header')
                if measured['measured_feasibility'] and (not measured['sta_feasibility'] or measured['detailed_route_drc_errors']):
                    raise ValueError('false final feasibility')
        current_profile=freeze['files_sha256']['experiments/arithmetic_dse/configs/platforms/'+p['platform']+'.json']
        if manifest['status']=='completed' and p['profile_sha256']==current_profile:
            if item['kernel']=='mul_u32':
                same([m['stage'] for m in manifest['metrics']],['synth','grt','final'],'complete multiplier chain')
                common_multiplier_hashes.add(digest(run/'input.sv'))
                if manifest.get('source_sha256'):
                    platforms.setdefault(p['platform'],{})['multiplier_final']=item['task_id']
            elif item['kernel']=='add_u32':
                same([m['stage'] for m in manifest['metrics']],['synth','grt'],'complete small-probe chain')
                platforms.setdefault(p['platform'],{})['small_probe_grt']=item['task_id']
        for relative,expected in manifest.get('source_sha256',{}).items():
            same(digest(run/'source'/relative),expected,'execution source '+relative)
    if set(platforms)!={'asap7','nangate45','sky130hd','gf180'} or len(common_multiplier_hashes)!=1:
        raise ValueError('missing platform or non-common multiplier RTL')
    for p in platforms:
        if 'multiplier_final' not in platforms[p] or (p!='asap7' and 'small_probe_grt' not in platforms[p]):
            raise ValueError('platform connection gate incomplete: '+p)
    if verify_external:
        for path,expected in freeze['external_files_sha256'].items():same(digest(path),expected,'external '+path)
    return {'status':'passed','freeze':freeze['version'],'platforms':platforms,
            'source_files':len(freeze['files_sha256']),'portable_evidence_files':len(index['files_sha256']),
            'retained_failed_runs':sum(r['status']=='failed' for r in summary['runs'])+sum(r['original_status']=='failed' for r in audit['runs']),
            'new_failed_runs':sum(r['status']=='failed' for r in summary['runs']),
            'accepted_stage_SDC_checks':checked_sdc_stages,
            'invalidated_previous_runs':sum(r['acceptance_status']=='invalid_sdc_contract' for r in audit['runs']),
            'previous_four_platform_acceptance':'revoked_due_to_integer_division',
            'invalidated_previous_SDC_stages':rejected_stages,
            'ASAP7_carried_forward':'actual_SDC_all_stages_checked; unaffected; no_physical_rerun',
            'new_usage':resources['new_usage'],'cumulative_usage':resources['cumulative_usage'],
            'requires_build_directory':False,'external_verification':verify_external,
            'training_or_main_matrix_executed':False,'multi_corner_signoff':False}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=ROOT)
    ap.add_argument('--verify-external',action='store_true')
    args=ap.parse_args()
    print(json.dumps(verify(args.root,args.verify_external),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
