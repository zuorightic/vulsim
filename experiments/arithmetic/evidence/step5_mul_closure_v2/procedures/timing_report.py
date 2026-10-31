"""Extract measured ORFS substage timings; complete grt leaf stays authoritative."""
from pathlib import Path
import json,re,sys
R=Path.cwd();B=R/'build/step5-closure-20261031'
def collect(root):
 manifest=json.loads((root/'manifest.json').read_text());rows=[]
 for p in sorted((root/'logs/asap7/arithmetic_probe/base').glob('*.log')):
  if not re.match(r'[2345]_\d_.*\.log$',p.name):continue
  text=p.read_text();matches=list(re.finditer(r'Elapsed time:\s*(\d+):(\d+)(?:\.(\d+))?\[h:\]min:sec\. CPU time: user ([\d.]+) sys ([\d.]+)',text))
  if not matches:continue
  m=matches[-1];elapsed=int(m[1])*60+int(m[2])+(float('0.'+m[3]) if m[3] else 0);cpu=float(m[4])+float(m[5]);rows.append({'stage':p.stem,'walltime_s':elapsed,'CPU_time_s':cpu,'source':str(p.relative_to(R)),'source_scope':'ORFS tool footer, rounded by its logger; not an independently charged leaf'})
 grt=next((c for c in manifest['commands'] if c['command'][-1]=='grt' or (c['log'].endswith('/grt.log'))),None)
 assert grt
 previous=sum(x['walltime_s'] for x in rows if not x['stage'].startswith('5_1_'));route=[x for x in rows if x['stage']=='5_1_grt']
 logs=root/'logs/asap7/arithmetic_probe/base';partial=list(logs.glob('5_1_grt*.log'));groups=[]
 for file in partial:groups += [int(v) for v in re.findall(r'Complete (\d+) groups',file.read_text())]
 cpu_record=json.loads(Path(grt['log'].removesuffix('.log')+'.command.json').read_text())
 try:
  from experiments.arithmetic_dse.budget import cpu_seconds
  cpu=cpu_seconds(grt['gnu_time']);cpu_kind='GNU_time_actual'
 except ValueError:cpu=cpu_record['CPU_limit_s'];cpu_kind='full_reservation_conservative; missing_GNU_time'
 return {'status':manifest['status'],'failure_code':manifest.get('failure_code'),'full_post_synthesis_to_grt':{'walltime_s':grt['walltime_s'],'CPU_time_s':cpu,'CPU_accounting':cpu_kind,'sampled_CPU_s':cpu_record['sampled_process_tree_CPU_s'],'RSS_peak_KiB':cpu_record['sampled_process_tree_peak_rss_KiB'],'cleanup':cpu_record['cleanup']},'substage_footers':rows,'completed_pre_grt_substage_sum_s':previous,'separate_5_1_grt':route if route else {'status':'incomplete; no final stage footer','last_logged_groups':max(groups) if groups else None,'total_groups_known':False,'percentage':None},'substage_sum_scope':'footers omit Make and Python overhead; never replace complete leaf walltime or sum reused old stages into new run','source_manifest':str((root/'manifest.json').relative_to(R))}
if __name__=='__main__':
 sys.path.insert(0,str(R));old=collect(R/'build/step5-parameterized-20261031/capacity128');new=collect(B/'capacity-retest');result={'version':'capacity-full-chain-timing-v1','old':old,'retest':new,'same_physical_circuit_and_timing_conditions':True,'one_new_full_post_synthesis_chain':True,'stitched_historical_time_used':False,'original_comparison_or_split_attribution':False};(B/'timing.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
