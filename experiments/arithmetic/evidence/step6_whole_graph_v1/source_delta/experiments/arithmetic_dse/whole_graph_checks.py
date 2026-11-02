"""Independent cost, grouping and safe-divisor checks over actual saved BEIR."""
def verify_safe_divisors(report):
 nodes={n['id']:n for n in report['graph']['nodes']}
 def canonical(v):
  seen=set()
  while v['kind']==0 and v['node'] not in seen:
   seen.add(v['node']);n=nodes[v['node']]
   if n['kind'] not in (0,8,11) or len(n['operands'])!=1 or n['operands'][0]['width']>v['width']:break
   v=n['operands'][0]
  return v
 def literal(v):return sum(int(x)<<(64*k) for k,x in enumerate(v['limbs']))
 def nonzero(v,seen):
  v=canonical(v)
  if v['kind']==1:return literal(v)!=0
  if v['kind']!=0 or v['node'] in seen:return False
  seen=seen|{v['node']};n=nodes[v['node']]
  if n['kind']!=9 or len(n['operands'])!=3:return False
  cond,a,b=n['operands']
  if nonzero(a,seen) and nonzero(b,seen):return True
  cond=canonical(cond)
  if cond['kind']!=0:return False
  condition=nodes[cond['node']]
  if condition['kind']!=4 or condition['opcode'] not in (11,12):return False
  tested=None
  for i in range(2):
   zero=canonical(condition['operands'][1-i])
   if zero['kind']==1 and literal(zero)==0:tested=canonical(condition['operands'][i]);break
  if tested is None:return False
  index=2 if condition['opcode']==11 else 1;branch=canonical(n['operands'][index])
  return tested['kind']==0 and branch['kind']==0 and tested['node']==branch['node'] and tested['width']==branch['width'] and nonzero(n['operands'][3-index],seen)
 count=0
 for n in nodes.values():
  if n['kind']==4 and n['opcode'] in (4,5):
   if not nonzero(n['operands'][1],set()):raise ValueError('unsafe_divisor in saved graph')
   count+=1
 return count
