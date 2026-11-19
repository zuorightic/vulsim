"""Frozen v10 runtime functions; extracted without numerical edits from workload_final_software.py."""
def balanced(raw,units,L,weights):
    """Contract units, then find the smallest greedy per-stage capacity.

    Internal weighted longest paths define indivisible unit work. Dependent
    units may share a stage; a capacity overflow starts the next stage.
    Fixed port placement takes precedence over constant/wiring treatment.
    """
    nodes=raw['nodes'];membership={n:k for k,u in enumerate(units) for n in u['members']}
    dependencies=[];work=[]
    for k,u in enumerate(units):
        members=set(u['members']);cache={}
        def local(i):
            if i not in cache:
                cache[i]=weights.get(i,0.)+max((local(a['node']) for a in nodes[i]['operands'] if a['node'] in members),default=0.)
            return cache[i]
        dependencies.append(sorted({membership[a['node']] for n in members for a in nodes[n]['operands']
            if a['node'] is not None and a['node'] not in members}))
        if any(d>=k for d in dependencies[-1]):raise ValueError('native units are not dependency ordered')
        work.append(max(map(local,members),default=0.))
    def schedule(cap):
        stages=[];ends=[]
        for k,u in enumerate(units):
            ds=dependencies[k];s=max((stages[d] for d in ds),default=0)
            start=max((ends[d] for d in ds if stages[d]==s),default=0.)
            if u['fixed']:
                s=0 if all(nodes[n]['operation']=='input' for n in u['members']) else L-1
                start=max((ends[d] for d in ds if stages[d]==s),default=0.)
            elif u['constant']:s=0;start=0.
            elif work[k]>0 and start+work[k]>cap+1e-8:
                s+=1;start=0.
            stages.append(s);ends.append(start+work[k])
        return stages
    low=max(work,default=0.);high=sum(work)+1.
    for _ in range(48):
        mid=(low+high)/2;s=schedule(mid)
        if max(s,default=0)<L:high=mid
        else:low=mid
    results=[]
    for scale in (1.,1.08,1.25):
        s=schedule(high*scale+1e-6);placement=[0]*len(nodes)
        for k,u in enumerate(units):
            for n in u['members']:placement[n]=s[k]
        if max(placement,default=0)>=L:raise ValueError('balanced placement exceeds L')
        if placement not in results:results.append(placement)
    return results
