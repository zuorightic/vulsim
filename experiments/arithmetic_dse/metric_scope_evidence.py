"""Explain saved STA metrics without rerunning synthesis or physical tools."""
import argparse,gzip,hashlib,json,math,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
FREEZE='experiments/arithmetic/mul_templates_freeze_v3.json'
EVIDENCE='experiments/arithmetic/evidence/step5_metric_scope_v1'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):
 path=Path(path);raw=path.read_bytes()
 return (gzip.decompress(raw) if path.suffix=='.gz' else raw).decode()

def paths(text):
 result=[]
 for block in re.split(r'^Startpoint: ',text,flags=re.M)[1:]:
  header=block.split('Fanout',1)[0];start,end=header.split('Endpoint: ',1)
  def clock(section):return re.search(r'clocked by ([^\s)]+)',section)[1]
  slack=re.search(r'^\s*([-+\d.]+)\s+slack \(',block,re.M)
  def value(label):
   match=re.search(r'^\s*([-+\d.]+)\s+'+label+r'\s*$',block,re.M)
   if not match:raise ValueError('missing path '+label)
   return float(match[1])
  result.append({'startpoint':start.split()[0],'endpoint':end.split()[0],
   'launch_clock':clock(start),'capture_clock':clock(end),
   'path_group':re.search(r'Path Group: (\S+)',header)[1],
   'input_port': '(input port ' in start,'output_port':'(output port ' in end,
   'input_external_delay_ps':float(re.search(r'([-+\d.]+)\s+[-+\d.]+\s+[\^v]\s+input external delay',block)[1]) if 'input external delay' in block else None,
   'output_external_delay_ps':-float(re.search(r'([-+\d.]+)\s+[-+\d.]+\s+output external delay',block)[1]) if 'output external delay' in block else None,
   'arrival_ps':value('data arrival time'),'required_ps':value('data required time'),
   'slack_ps':float(slack[1])})
 if not result:raise ValueError('missing saved max paths')
 return result

def analyze(root=ROOT):
 root=Path(root);rows=[]
 for label,directory,stage in [('W64_synth','step5_mul_capacity_v1/W64','synth'),('W64_grt','step5_mul_capacity_v1/W64','grt'),('W128_grt','step5_mul_capacity_v2','grt')]:
  base=root/'experiments/arithmetic/evidence'/directory;reports=base/'reports/asap7/arithmetic_probe/base'
  manifest=json.loads(load(base/'manifest.json.gz'));metric=next(x for x in manifest['metrics'] if x['stage']==stage)
  selected={name:reports/f'vulsim_{stage}_{name}.rpt.gz' for name in ('period','setup','paths_max')}
  period=float(re.search(r'core_clk period_min = ([-+\d.]+)',load(selected['period']))[1]);worst=float(re.search(r'worst slack max ([-+\d.]+)',load(selected['setup']))[1])
  saved=paths(load(selected['paths_max']));critical=min(saved,key=lambda p:p['slack_ps'])
  if worst!=metric['setup_worst_slack_ps'] or period!=metric['minimum_clock_period_ps'] or worst!=critical['slack_ps']:raise ValueError('saved metric/path mismatch')
  for p in saved:
   if not math.isclose(p['required_ps']-p['arrival_ps'],p['slack_ps'],abs_tol=0.001,rel_tol=0):raise ValueError('saved path arithmetic mismatch')
  if critical['launch_clock']!='io_clk' or critical['capture_clock']!='core_clk' or not critical['input_port'] or critical['output_port']:raise ValueError('unexpected critical path classification')
  if critical['input_external_delay_ps']!=300 or critical['output_external_delay_ps'] is not None:raise ValueError('critical input path does not pay both I/O delays')
  bindings={str(p.relative_to(root)):sha(p) for p in selected.values()}
  rows.append({'case_stage':label,'period_ps':manifest['period_ps'],'setup_worst_slack_ps':worst,'core_same_clock_min_period_ps':period,'core_same_clock_slack_approx_ps':manifest['period_ps']-period,'same_clock_slack_scope':'derived from 2-decimal rounded core_clk period_min; eligible same-clock paths at this fixed STA context; not overall interface slack or a new frequency sweep','worst_path':critical,'saved_path_group_summaries':saved,'source_reports_sha256':bindings})
 return {'version':'saved-STA-metric-scope-v1','rows':rows,'minimum_period_command':'report_clock_min_period -include_port_paths','minimum_period_filter':'same launch/capture clock object; same transition; max check/output_delay; no multicycle; port flag does not include distinct-clock paths','setup_command':'report_worst_slack -max -digits 6','admission_rule':'use actual full constrained setup/hold and coverage in the same stage; core period_min is diagnostic only; no release from target_period > core period_min','physical_calls':0,'original_results_changed':False}

def verify(root=ROOT,parents=True):
 root=Path(root);f=json.loads((root/FREEZE).read_text());e=root/EVIDENCE
 for path,h in f['files_sha256'].items():
  if sha(root/path)!=h or sha(root/f['source_snapshots'][path])!=h:raise ValueError('metric note source mismatch '+path)
 for path,h in f['historical_freezes'].items():
  if sha(root/path)!=h:raise ValueError('historical freeze changed '+path)
 if sha(root/f['evidence_index'])!=f['evidence_index_sha256']:raise ValueError('metric note index changed')
 for path,h in json.loads((root/f['evidence_index']).read_text())['files_sha256'].items():
  if sha(root/path)!=h:raise ValueError('metric note evidence changed '+path)
 for path,h in json.loads(load(e/'preservation.json.gz')).items():
  if sha(root/path)!=h:raise ValueError('old payload changed '+path)
 if json.loads((e/'analysis.json').read_text())!=analyze(root):raise ValueError('STA scope interpretation mismatch')
 source=json.loads((e/'tool_source.json').read_text());excerpt=(e/'MinPeriodEndVisitor.cc.txt').read_text()
 if hashlib.sha256(excerpt.encode()).hexdigest()!=source['excerpt_sha256']:raise ValueError('STA source excerpt mismatch')
 for guard in ('src_edge->clock() == clk_','tgt_edge->clock() == clk_','src_edge->transition() == tgt_edge->transition()','path_end->multiCyclePath() == nullptr','clk_->period() - delayAsFloat(slack'):
  if guard not in excerpt:raise ValueError('missing documented STA filter '+guard)
 from .budget import usage,cpu_seconds
 d=json.loads((e/'usage_delta.json').read_text());old=root/d['prefix']
 if sha(old)!=d['prefix_sha256']:raise ValueError('usage prefix mismatch')
 def entries(path):
  value=json.loads(path.read_text());return (entries(root/value['prefix']) if 'prefix' in value else [])+value['entries']
 cumulative=entries(e/'usage_delta.json');resources=json.loads((e/'resources.json').read_text())
 if usage(cumulative)!=resources['cumulative_usage'] or usage(d['entries'])!=resources['new_usage']:raise ValueError('metric note resource mismatch')
 if usage(d['entries'])['pending'] or any(x['stage'] is not None for x in d['entries']):raise ValueError('metric note may not include physical calls')
 receipts=json.loads((e/'command_index.json').read_text())
 if {r['id'] for r in receipts}!={entry['id'] for entry in d['entries']}:raise ValueError('missing metric note command receipt')
 for row in receipts:
  record=json.loads((root/row['record']).read_text());charge=next(x for x in d['entries'] if x['id']==row['id'])
  if record['walltime_s']!=charge['walltime_s'] or cpu_seconds(root/row['CPU_report'])!=charge['CPU_time_s'] or record['cleanup']['remaining_live_pids']:raise ValueError('metric note command receipt mismatch')
 if (root/'experiments/arithmetic/backend_usage.json').exists() and json.loads((root/'experiments/arithmetic/backend_usage.json').read_text())['entries'][:len(cumulative)]!=cumulative:raise ValueError('live prefix changed')
 parent=None
 if parents:
  from .closure_evidence import verify as inherited
  parent=inherited(root)['status']
 return {'status':'passed','scope':'documentation and saved-report interpretation; no new STA/physical run','reports_checked':3,'parent_status':parent,'new_usage':resources['new_usage'],'cumulative_usage':resources['cumulative_usage']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args();print(json.dumps(verify(a.root),indent=2))
if __name__=='__main__':main()
