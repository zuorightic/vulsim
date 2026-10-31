"""Static independent counterpart of the registered block-tree certificate.

Works on actual saved combinational report fields; never regenerates a template
or infers coordinates from node names. Native historical replay is separately
performed through arithmetic::validate and retained as execution evidence.
"""
def verify_block_trees(report):
 nodes={n['id']:n for n in report['graph']['nodes']};checked=0
 def canonical(v):
  seen=set()
  while v['kind']==0:
   i=v['node']
   if i in seen:raise ValueError('block provenance cycle')
   seen.add(i);n=nodes[i]
   if n['kind'] not in (0,8,11) or len(n['operands'])!=1:break
   child=n['operands'][0]
   if v['signed'] or child['signed'] or child['constant_signed'] or child['width']>v['width'] or child['dims']:break
   v=child
  return v
 def source(v):
  v=canonical(v)
  if v['kind']==0:return ('node',v['node'],v['width'],tuple(v['dims']))
  if v['kind']==1:return ('literal',v['width'],sum(int(w)<<(64*k) for k,w in enumerate(v['limbs'])))
  raise ValueError('unsupported block source')
 def ref(i):return {'kind':0,'node':i,'width':nodes[i]['width'],'dims':nodes[i]['dims'],'signed':False,'constant_signed':False}
 def boundary(v):
  if v['node']=='literal':return {'kind':1,'width':v['width'],'dims':[],'signed':v['signed_view'],'constant_signed':v['constant_signed'],'limbs':v['constant_limbs']}
  return {'kind':0,'node':v['node'],'width':v['width'],'dims':nodes[v['node']]['dims'],'signed':v['signed_view'],'constant_signed':v['constant_signed']}
 def zero(v):return v['kind']==1 and not v['constant_signed'] and all(int(w)==0 for w in v['limbs'])
 for r in report['graph']['regions']:
  if r['template_id']!='mul-block-tree-v1':continue
  t=r['parameters'];aw,bw,b,R=t['lhs_width'],t['rhs_width'],t['block_width'],t['result_width'];coords={};expected={(a,c) for a in range(0,aw,b) for c in range(0,bw,b)};covered=set()
  if len(r['inputs'])!=2:raise ValueError('two ordered block inputs required')
  roots=[source(boundary(v)) for v in r['inputs']]
  if any(root[2 if root[0]=='node' else 1]!=width for root,width in zip(roots,(aw,bw))):raise ValueError('block parameters disagree with original operand widths')
  for i in r['members']:
   n=nodes[i]
   if n['kind']!=4 or n['opcode']!=3:continue
   point=[]
   for axis,width in enumerate((aw,bw)):
    v=canonical(n['operands'][axis])
    if v['kind']!=0:raise ValueError('partial operand missing input slice')
    sl=nodes[v['node']];lo=sl['lo']
    if sl['kind']!=14 or len(sl['operands'])!=1 or source(sl['operands'][0])!=roots[axis]:raise ValueError('block uses wrong original source')
    if lo<0 or lo>=width or lo%b or sl['hi']!=lo+min(b,width-lo)-1 or v['width']!=min(b,width-lo):raise ValueError('block coordinate/tail mismatch')
    point.append(lo)
   xy=tuple(point)
   if xy in covered:raise ValueError('duplicate block coordinate')
   covered.add(xy);coords[i]=xy
  if covered!=expected:raise ValueError('block Cartesian coverage mismatch')
  uses={};visiting=set()
  def term(v,shift=0):
   v=canonical(v)
   if v['kind']!=0:raise ValueError('non-product reduction term')
   i=v['node'];n=nodes[i]
   if i in visiting:raise ValueError('reduction cycle')
   visiting.add(i)
   if i in coords:
    if shift!=sum(coords[i]):raise ValueError('partial shift disagrees with block coordinate')
    uses[i]=uses.get(i,0)+1
   elif n['kind']==18:
    args=n['operands']
    if len(args)!=2 or not zero(args[1]) or args[1]['width']<=0:raise ValueError('bad block shift form')
    first=canonical(args[0])
    if first['kind']!=0 or first['node'] not in coords:raise ValueError('shift source is not a partial product')
    term(args[0],shift+args[1]['width'])
   elif n['kind']==2:
    if shift or len(n['operands'])!=3 or not zero(n['operands'][2]):raise ValueError('shifted sum or nonzero carry')
    term(n['operands'][0]);term(n['operands'][1])
   else:raise ValueError('unsupported block reduction connection')
   visiting.remove(i)
  output=ref(r['outputs'][0]);n=nodes[output['node']]
  if n['kind']==14:
   if n['lo']!=0 or n['hi']!=R-1 or len(n['operands'])!=1:raise ValueError('wrong final truncation')
   output=n['operands'][0]
  term(output)
  if set(uses)!=set(coords) or any(n!=1 for n in uses.values()):raise ValueError('partial omitted/repeated by reduction')
  checked+=1
 return checked
