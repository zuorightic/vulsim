"""Independent grouped stage/cost and predeclared sensitivity evaluator."""
from fractions import Fraction
from itertools import combinations_with_replacement
import copy,hashlib,json,math

def evaluate(report,stages=None,square=False):
 nodes={n['id']:n for n in report['graph']['nodes']};stages=stages or report['stages'];N=report['request']['L']-1
 live={i for p in report['graph']['ports'] for i in p['nodes']}|{i for r in report['graph']['regions'] for i in r['outputs']}|{v['node'] for r in report['graph']['regions'] for v in r['inputs'] if v['node']!='literal'}
 stack=list(live)
 while stack:
  for v in nodes[stack.pop()]['operands']:
   if v['kind']==0 and v['node'] not in live:live.add(v['node']);stack.append(v['node'])
 order=[];pending=set(live)
 while pending:
  ready=sorted(i for i in pending if all(v['kind']!=0 or v['node'] in order for v in nodes[i]['operands']))
  if not ready:raise ValueError('cycle or dangling graph')
  pending.difference_update(ready);order+=ready
 users={i:[] for i in live};arrivals={};delays=[Fraction(0)]*(N+1);comb=Fraction(0);bits=count=0
 for i in order:
  n=nodes[i];s=stages[int(i)]
  if type(s) is not int or s<0 or s>N:raise ValueError('stage range')
  for v in n['operands']:
   if v['kind']==0:
    users[v['node']].append(i)
    if not nodes[v['node']]['transaction_constant'] and stages[int(v['node'])]>s:raise ValueError('backwards dependency')
  if n['kind']==1 and s!=0:raise ValueError('input stage')
  if n['transaction_constant']:arrivals[i]=Fraction(0);continue
  arrivals[i]=Fraction(n['delay'])+max((arrivals[v['node']] for v in n['operands'] if v['kind']==0 and stages[int(v['node'])]==s and not nodes[v['node']]['transaction_constant']),default=Fraction(0));delays[s]=max(delays[s],arrivals[i])
  cost=Fraction(n['comb'])
  if square and n['kind']==4 and n['opcode']==3:
   bucket=next(b for b in (1,2,4,8,16,32,64,128) if b>=n['billing_width']);cost=Fraction(bucket*bucket,64)
  comb+=cost
 for p in report['graph']['ports']:
  if p['direction']==1:
   for i in p['nodes']:
    if stages[int(i)]!=N:raise ValueError('output stage')
 for region in report['graph']['regions']:
  for group in region['legal_groups'] if region['internally_cuttable'] else [region['members']]:
   if len({stages[int(i)] for i in group})!=1:raise ValueError('cut group')
 valid_name=report['protocol']['input_valid_name'];valids={i for p in report['graph']['ports'] if p['name']==valid_name for i in p['nodes']}
 for i in order:
  n=nodes[i]
  if n['transaction_constant']:continue
  end=max([stages[int(i)],*[stages[int(u)] for u in users[i]]]);end=N if i in valids else end
  length=end-stages[int(i)];bits+=length*n['width']*math.prod(n['dims']);count+=length
 return {'stage_delays':delays,'maximum_delay':max(delays),'comb':comb,'register_bits':bits,'register_count':count}

def validate_selection(report):
 selection=report['selection'];ranked=[];queries=0
 for row in selection['candidates']:
  if row['status']!='scheduled':continue
  data=row['computation'];assert data['stages']==row['final_stages']
  initial=evaluate(data,row['initial_stages']);moving=list(row['initial_stages']);current=initial
  group_map={}
  owned=set()
  for region in data['graph']['regions']:
   groups=region['legal_groups'] if region['internally_cuttable'] else [region['members']]
   for k,group in enumerate(groups):group_map[region['id']+('/group'+str(k) if region['internally_cuttable'] else '/atomic')]=group;owned.update(group)
  for node in data['graph']['nodes']:
   if node['id'] not in owned:group_map['node#'+node['id']]=[node['id']]
  for move in row['moves']:
   if not move['accepted']:continue
   group=group_map[move['group']]
   if any(moving[int(i)]!=move['from'] for i in group):raise ValueError('move start mismatch')
   for i in group:moving[int(i)]=move['to']
   after=evaluate(data,moving)
   if after['register_bits']>=current['register_bits'] or after['maximum_delay']>data['pipeline']['allowed_delay']:raise ValueError('invalid accepted group improvement')
   current=after
  if moving!=row['final_stages']:raise ValueError('move trace does not reproduce final map')
  cost=evaluate(data);score=[float(cost['maximum_delay']),int(cost['comb'])+cost['register_bits'],cost['register_bits'],cost['register_count'],row['id']]
  if score!=row['score']:raise ValueError('candidate score disagreement')
  for move in row['moves']:
   if move['accepted'] and move['reason']!='accepted_state_improvement':raise ValueError('unexplained accepted move')
  ranked.append((score,row['id']));queries+=1
 if not ranked or min(ranked)[1]!=selection['selected_candidate']:raise ValueError('C did not choose declared minimum')
 if selection['candidate_PPA_calls']!=0 or len(ranked)>16:raise ValueError('selection scope')
 return queries

def position_analysis(report,placements):
 results=[]
 for item in placements:
  c=evaluate(report,item['stages']);converted={k:[float(v) for v in x] if isinstance(x,list) else float(x) if isinstance(x,Fraction) else x for k,x in c.items()}
  for k in ('stage_delays','maximum_delay','register_bits','register_count'):
   if converted[k]!=item[k]:raise ValueError('C++/Python position mismatch '+k)
  results.append({**item,'comb':str(c['comb'])})
 if sum(x['within_production_cap'] for x in results)<2:raise ValueError('missing two feasible positions')
 return {'classification':'multiple_cap_feasible_placements; production_moves_reported_separately','placements':results,'cap':report['pipeline']['allowed_delay'],'production_initial_stages':report['selection']['candidates'][0]['initial_stages'],'production_final_stages':report['stages'],'production_moves':report['selection']['candidates'][0]['moves']}

def sensitivity(reports):
 rows=[];changes=0
 for w in (8,16,32,64,128):
  for family in (0,1):
   variants=[]
   for mode,name in enumerate(('original','half','quarter')):
    r=reports[f'sensitivity_{w}_{family}_{mode}'];a=evaluate(r);b=evaluate(r,square=True)
    assert a['maximum_delay']==b['maximum_delay'] and a['register_bits']==b['register_bits']
    score=lambda c:[c['maximum_delay'],c['comb']+c['register_bits'],c['register_bits'],c['register_count'],name]
    variants.append({'structure':name,'graph_sha256':r['graph_sha256'],'schedule_sha256':r['schedule_sha256'],'stage_delays':[str(x) for x in a['stage_delays']],'register_bits':a['register_bits'],'register_count':a['register_count'],'linear_comb':str(a['comb']),'square_comb':str(b['comb']),'linear_score':score(a),'square_score':score(b)})
   linear=sorted(variants,key=lambda x:x['linear_score']);square=sorted(variants,key=lambda x:x['square_score']);changed=linear[0]['structure']!=square[0]['structure'];changes+=changed
   for x in variants:
    x['linear_rank']=next(i+1 for i,v in enumerate(linear) if v is x);x['square_rank']=next(i+1 for i,v in enumerate(square) if v is x)
    x['linear_score']=[str(v) for v in x['linear_score']];x['square_score']=[str(v) for v in x['square_score']]
   rows.append({'W':w,'family':'MAC' if family else 'MUL','structures':variants,'linear_selected':linear[0]['structure'],'square_selected':square[0]['structure'],'selected_changed':changed})
 return {'version':'mul-comb-sensitivity-v1','status':'passed','structures':30,'contexts':10,'selected_changes':changes,'exact_rational':True,'only_changed':'Mul.comb_weight=bucket_width^2/64','schedules_reused':True,'physical_calls':0,'rows':rows}
