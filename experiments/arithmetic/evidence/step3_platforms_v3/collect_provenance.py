from pathlib import Path
import hashlib,json,gzip,re
root=Path.cwd();e=root/'experiments/arithmetic/evidence/step3_platforms_v3';dec=root/'experiments/arithmetic_dse/configs/platform_parameter_decisions_v1.md';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
basis=json.loads((e/'parameter_source_excerpts.json').read_text());profiles={};orfs=Path('/home/zyrv/OpenROAD-flow-scripts')
for platform in ('asap7','nangate45','sky130hd','gf180'):
 path=root/'experiments/arithmetic_dse/configs/platforms'/(platform+'.json');p=json.loads(path.read_text())
 run=(root/'experiments/arithmetic/evidence/step3_platforms_v1/runs/asap7-mul-finalinterface' if platform=='asap7' else root/'experiments/arithmetic/evidence/step3_platforms_v2/runs'/(platform+'-mul-sdcfix'))
 m=json.loads((run/'manifest.json').read_text())
 for library in m['libraries']:
  lib=Path(library['path']);text=gzip.open(lib,'rt').read() if lib.suffix=='.gz' else lib.read_text()
  cell=re.search(r'\bcell\s*\(\s*"?'+re.escape(p['driver_cell'])+r'"?\s*\)\s*\{',text)
  if cell:break
 assert cell
 lines=text.splitlines();following=re.search(r'\bcell\s*\([^)]*\)\s*\{',text[cell.end():]);body=text[cell.end():cell.end()+following.start()] if following else text[cell.end():]
 pin=re.search(r'\bpin\s*\(\s*"?'+re.escape(p['driver_pin'])+r'"?\s*\)',body);assert pin
 start=cell.end()+pin.start();first=text.count('\n',0,start)+1
 snippet='\n'.join(lines[first-1:first+12]);assert re.search(r'direction\s*:\s*"?output',snippet)
 libkey=str(lib.relative_to(orfs));basis['sources'][libkey]={'path':str(lib),'sha256':sha(lib),'excerpts':[{'first_line':first,'last_line':first+12,'text':snippet,'line_basis':'decompressed Liberty'}]}
 entries={}
 def row(key,value,unit,category,reason,section,extra_refs=(),impact='measurement_environment_change_requires_domain_review_and_admitted_revalidation'):
  entries[key]={'value':value,'unit':unit,'source_category':category,'basis':[{'path':str(dec.relative_to(root)),'sha256':sha(dec),'section':section},*extra_refs],
   'selection_reason':reason,'applicability':'TT/typical platform connection probes only; not automatically training or formal evaluation','change_impact':impact}
 config=orfs/'flow/platforms'/platform/'config.mk';cfg={'path':str(config),'sha256':sha(config),'locator':'ABC_DRIVER_CELL / ABC_LOAD_IN_FF'}
 old=root/'experiments/arithmetic/evidence/step3_closure/source_v4/experiments/arithmetic_dse/backend/constraints.sdc';oldref={'path':str(old.relative_to(root)),'sha256':sha(old),'locator':'clock uncertainty / transition / IO / driver / load'}
 for key in ('setup_uncertainty_ps','hold_uncertainty_ps','clock_transition_ps'):
  row(key,p[key],'ps','inherited_experiment' if platform=='asap7' else 'engineering_convention','Preserve the predeclared probe clock assumptions; no independently calibrated PDK jitter/slew claim.','D1',([oldref] if platform=='asap7' else []))
 row('io_delay_min_ps',0,'ps','inherited_experiment','Common virtual-I/O shell includes reset/valid/data.','D2',[oldref])
 row('io_delay_max_period_fraction',0.2,'dimensionless','inherited_experiment','Default max IO delay is 20% of each requested period; explicit absolute request is separately identified.','D2',[oldref])
 for key in ('driver_cell','driver_pin'):
  row(key,p[key],'cell_name' if key=='driver_cell' else 'pin_name','ORFS_default' if key=='driver_cell' else 'selected_Liberty_interface','Use the platform driver and its actual output pin as a declared input-environment assumption.','D2',[cfg,{'path':str(lib),'sha256':sha(lib),'locator':f'{p["driver_cell"]}/{p["driver_pin"]} direction output'}])
 for key in ('output_load_fF','abc_load_fF'):
  row(key,p.get(key,p['output_load_fF']),'fF','engineering_override' if platform=='gf180' else 'ORFS_default','Keep STA output and ABC load explicit in fF; GF180 13.43 is the project override, ORFS raw default is 0.01343.' if platform=='gf180' else 'Preserve the platform default load for bounded connection probes.','D2',[cfg])
 row('trial_period_ps',p['trial_period_ps'],'ps','inherited_experiment' if platform=='asap7' else 'engineering_convention','Predeclared connection target, not best frequency, main-case target or model domain.','D3')
 row('hold_review_margin_ps',p['hold_review_margin_ps'],'ps','inherited_experiment' if platform=='asap7' else 'engineering_convention','Report a review trigger separately from feasibility; not a calibrated noise floor.','D1',impact='recompute_review_flags; no_EDA_if_reporting_only; retain_historical_flags')
 profiles[platform]={'profile_path':str(path.relative_to(root)),'profile_sha256':sha(path),'parameters':entries}
(e/'parameter_source_excerpts.json').write_text(json.dumps(basis,ensure_ascii=False,indent=2)+'\n')
data={'schema':'platform-parameter-provenance-v1','effective_parameters_changed':False,'measurement_freeze':{'path':'experiments/arithmetic/backend_freeze_v6.json','sha256':sha(root/'experiments/arithmetic/backend_freeze_v6.json')},'source_excerpt_archive':{'path':str((e/'parameter_source_excerpts.json').relative_to(root)),'sha256':sha(e/'parameter_source_excerpts.json')},'profiles':profiles,'unresolved':['Engineering clock/hold-review assumptions have no independent noise calibration; valid only in declared probe scope.','GF180 13.43fF is a project choice; no PDK mandate is claimed.','GF180 wire RC calibration command, data and output units remain unresolved; see D5.']}
(root/'experiments/arithmetic_dse/configs/platform_parameter_sources_v1.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print('recorded',sum(len(x['parameters']) for x in profiles.values()),'parameter rows; profiles unchanged')
