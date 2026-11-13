"""Prospective compression/prefix DAG geometry, independent of mapped prices.

The final merge follows the Brent--Kung topology in Yosys's generic techmap.
Constant-folding and output liveness distinguish short/sparse carries from a
single dense carry-span proxy. These are computable logical work estimates,
not claims about which gates ABC or physical repair will actually instantiate.
"""
import math

VERSION='bit-column-features-v4-live-prefix'


def features(width,terms,target):
    if type(width) is not int or not 1<=width<=4096 or type(target) not in (int,float) or not math.isfinite(target) or target<=0:
        raise ValueError('bounded reduction width and positive numerical T required')
    heights=[0]*width;seen=set()
    if len(terms)<3 or any(not t for t in terms):raise ValueError('at least three nonempty independent terms required')
    for term in terms:
        columns=set()
        for source,bit,col in term:
            if any(type(v) is not int or v<0 for v in (source,bit,col)) or col>=width or col in columns or (source,bit) in seen:
                raise ValueError('invalid/repeated reduction bit')
            columns.add(col);seen.add((source,bit));heights[col]+=1
    total=sum(heights);maximum=max(heights);counters=levels=0
    while max(heights)>2:
        following=[0]*width
        for i,h in enumerate(heights):
            n=h//3;counters+=n;following[i]+=h%3+n
            if i+1<width:following[i+1]+=n
        heights=following;levels+=1
    # Intern symbolic primitive nodes, then prune unused prefix propagates.
    nodes={};intern={};next_id=2
    def leaf():
        nonlocal next_id
        i=next_id;next_id+=1;return i
    def gate(kind,a,b):
        if kind=='and':
            if not a or not b:return 0
            if a==1:return b
            if b==1 or a==b:return a
        elif kind=='or':
            if a==1 or b==1:return 1
            if a==0:return b
            if b==0 or a==b:return a
        elif kind=='xor':
            if not a:return b
            if not b:return a
            if a==b:return 0
        key=(kind,*sorted((a,b)))
        if key not in intern:
            i=leaf();intern[key]=i;nodes[i]=key
        return intern[key]
    aa=[leaf() if h else 0 for h in heights];bb=[leaf() if h==2 else 0 for h in heights]
    initial_p=[gate('xor',a,b) for a,b in zip(aa,bb)];p=initial_p.copy();g=[gate('and',a,b) for a,b in zip(aa,bb)]
    before_prefix=set(nodes)
    for i in range(1,math.ceil(math.log2(width))+1):
        for j in range((1<<i)-1,width,1<<i):
            g[j]=gate('or',g[j],gate('and',p[j],g[j-(1<<(i-1))]));p[j]=gate('and',p[j],p[j-(1<<(i-1))])
    for i in range(math.ceil(math.log2(width)),0,-1):
        for j in range((1<<i)+(1<<(i-1))-1,width,1<<i):
            g[j]=gate('or',g[j],gate('and',p[j],g[j-(1<<(i-1))]));p[j]=gate('and',p[j],p[j-(1<<(i-1))])
    prefix_ids=set(nodes)-before_prefix;outputs=[gate('xor',initial_p[i],g[i-1] if i else 0) for i in range(width)]
    live=set();loads={};depth={0:0,1:0}
    def visit(node):
        loads[node]=loads.get(node,0)+1
        if node not in nodes:return 0
        if node in live:return depth[node]
        live.add(node);kind,a,b=nodes[node];depth[node]=max(visit(a),visit(b))+1;return depth[node]
    for node in outputs:visit(node)
    prefix=live&prefix_ids;xor=sum(nodes[n][0]=='xor' for n in live)
    longest=max((depth.get(n,0) for n in outputs),default=0);span=segments=maxspan=0;carry=False
    for h in heights:
        if h==2:
            if not carry:segments+=1
            carry=True;span+=1
        elif h==1 and carry:span+=1
        else:carry=False;span=0
        maxspan=max(maxspan,span)
    f=dict(one=1.,output_bits=float(width),term_count=float(len(terms)),active_bits=float(total),max_column_height=float(maximum),counter_count=float(counters),compression_levels=float(levels),log2_target=math.log2(target/500.),clock_pressure=1500./target,
           final_live_xor_gates=float(xor),final_live_prefix_and_gates=float(sum(nodes[n][0]=='and' for n in prefix)),final_live_prefix_or_gates=float(sum(nodes[n][0]=='or' for n in prefix)),
           final_live_logic_gates=float(len(live)),final_logic_depth=float(longest),final_max_logical_fanout=float(max(loads.values(),default=0)),final_prefix_carry_segments=float(segments),final_max_carry_span=float(maxspan),log2_final_carry_span=math.log2(maxspan+1.),
           final_pressure_logic=len(live)*1500./target,counter_pressure=counters*1500./target)
    return f
