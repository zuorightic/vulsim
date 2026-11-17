"""Finite, producer-grouped three-pressure N4 delay recalibration campaign."""
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import shutil

from . import budget, workload_nine_runtime as runtime
from . import nangate45_samples as original
from .nangate45_samples import ROOT, read, write, sha
from . import wide_arithmetic as arithmetic, wide_family_sources as families
from . import wide_operator_samples as wide, wide_operator_query as queries
from . import reduction_wide_sampling as reduction
from .nangate45_artifacts import load
from .nangate45_model import native_query
from .platforms import profile

VERSION = 'nangate45-N4-three-pressure-refit-v1'
BASE = ROOT.parent/'vulsim-artifacts/nangate45-n34-20261117-v9'
PACKAGE = ROOT/'experiments/arithmetic/evidence/nangate45_n34_v1/model.json'


def group(query):
    """Load/clock variants share producer semantics, never a pricing key."""
    if 'local_context' in query:
        p = deepcopy(query['local_context']['producer']); p.pop('capture_banks', None)
        # Addition operand order is semantically symmetric.
        sides = sorted([(p[k+'_width'], p[k+'_zero_hex'], p[k+'_one_hex']) for k in ('lhs', 'rhs')])
        for k, (w,z,o) in zip(('lhs','rhs'), sides):
            p.update({k+'_width':w,k+'_zero_hex':z,k+'_one_hex':o})
    else:
        roots={}; terms=[]
        for term in query['terms']:
            row=[]
            for root,bit,col in term:
                if root not in roots: roots[root]=len(roots)
                row.append([roots[root],bit,col])
            terms.append(sorted(row))
        p=dict(output_bits=query['output_bits'],terms=terms)
    return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def definitions():
    s=arithmetic.spec
    return [
        ('train','Add','wide-3298c0400abe1442',None),
        ('train','Add','wide-3bb63c8fddd959f2',None),
        ('train','G','repair/G-b48ff980e300bb37',None),
        ('train','G','G-aca48b1fead906bf',None),
        ('validation','Add','fresh-add192x160-consumer256',families.local(s('add',192,160,193),consumer_width=256,shift=17)),
        ('validation','Add','fresh-adc96-one',families.local(s('adc',96,96,96,status='carry',control='one'))),
        ('validation','G','repair/G-25498c3ee85ce20e',None),
        ('test','Add','fresh-add384x320-consumer512',families.local(s('add',384,320,385),consumer_width=512,shift=29)),
        ('test','Add','fresh-adc160-one-two-banks',families.local(s('adc',160,160,160,status='carry',control='one'),banks=2)),
        ('test','G','fresh-G192-seven',dict(output_bits=192,terms=[[[0,b,b] for b in range(192)]]+
            [[[i,b,b+23*i] for b in range(41)] for i in range(1,7)],consumers=[],target_ps=1500))]


def reference(query,family,prices,p):
    def delay(q,f):
        q=native_query(q,'nangate45',p['profile_sha256'],1500)
        if f=='G':q.update(target_platform='nangate45',profile_sha256=p['profile_sha256'])
        return (prices.reduction_price(q) if f=='G' else prices.operator_price(q))['delay_ps']
    d=delay(query,family); consumer=0.
    if family=='Add':
        for c in query['local_context']['consumers']:
            cq=queries.descriptor(families.local(c['spec']),1500,'reference-only')
            consumer=max(consumer,delay(cq,'Add'))
    # Prospective engineering estimate only: neither measured shell Tmin nor
    # an inverse slack formula (I/O delays scale with T).
    ref=25*math.ceil(max(600.,d+consumer+180.)/25)
    return dict(producer_prediction_ps=d,dependent_consumer_prediction_ps=consumer,
                boundary_allowance_ps=180,reference_ps=ref,
                periods_ps={name:25*math.ceil(factor*ref/25) for name,factor in
                            (('tight',.75),('suitable',1.05),('loose',2.))})


def prepare(root):
    root=Path(root).resolve()
    if root.exists() or root.is_relative_to(ROOT):raise ValueError('new external root required')
    old=original.verify(BASE);data,indexes=original.catalogs();p=profile('nangate45');prices=load(PACKAGE)
    files={str(x):sha(x) for x in (*indexes,BASE/'admission.json',BASE/'frozen-model.json',PACKAGE)}
    sources=[];tasks=[];old_groups=defaultdict(set)
    for s in old['sources']:old_groups[group(s['query'])].add(s['role'])
    for role,family,name,features in definitions():
        provenance={'historical_role':None,'fresh_producer':features is not None}
        if features is None:
            rows=[r for r in data[family] if r['source']==name]
            if not rows or any(r['role']!='train' for r in rows):raise ValueError('historical training metadata only')
            r=next(r for r in rows if r['target_ps']==3000)
            query=deepcopy(r['query']);label=Path(r.get('label_path',r.get('physical_label_path')))
            directory=Path(r['directory']) if r.get('directory') else label.parent
            rtl=directory/'input.sv';files[str(rtl)]=sha(rtl);text=rtl.read_text()
            provenance.update(historical_role='train',source_rtl=str(rtl),source_rtl_sha256=sha(rtl))
        elif family=='Add':
            query=queries.descriptor(features,1500,'fresh-refit-source')
            text=wide.source(features)
        else:
            query=deepcopy(features);reduction.geometry(query);text=reduction.source(query)
        producer_group=group(query)
        if producer_group in old_groups:raise ValueError('new source collides with consumed baseline role')
        dest=root/'sources'/name.replace('/','--')/'input.sv';dest.parent.mkdir(parents=True);dest.write_text(text)
        ref=reference(query,family,prices,p)
        source=dict(id=name,family=family,role=role,query=query,local_context=query.get('local_context'),
                    producer_group=producer_group,rtl=str(dest),rtl_sha256=sha(dest),reference=ref,**provenance)
        sources.append(source)
        for region,t in ref['periods_ps'].items():
            tasks.append(dict(id=name.replace('/','--')+'-T'+str(t),source=name,family=family,role=role,
                              rtl=str(dest),rtl_sha256=sha(dest),period_ps=t,requested_region=region))
    roles=defaultdict(set)
    for s in sources:roles[s['producer_group']].add(s['role'])
    if any(len(r)!=1 for r in roles.values()) or len(roles)!=len(sources):raise ValueError('producer grouping collision')
    tasks.sort(key=lambda t:({'train':0,'validation':1,'test':2}[t['role']],t['family'],t['source'],t['period_ps']))
    paths=[*(ROOT/'experiments/arithmetic_dse').glob('*.py'),*(ROOT/'experiments/arithmetic_dse/reference_assets').glob('*.tcl'),
           runtime.POLICY,runtime.BRIDGE,budget.POLICY,budget.CHECKPOINT,ROOT/'experiments/arithmetic_dse/configs/platforms/nangate45.json']
    files.update({str(x):sha(x) for x in paths})
    used=budget.usage(read(budget.LEDGER)['entries']);limits=read(runtime.POLICY)['resources'];n=len(tasks);wall=n*(300+1200+10*120)
    if (used['walltime_s']+wall>3600*limits['max_global_walltime_h'] or
        used['CPU_time_s']+2*wall>3600*limits['max_tool_CPU_time_h'] or
        used['synth']+n>limits['max_synthesis_calls'] or used['grt']+n>limits['max_global_route_calls'] or
        shutil.disk_usage(root.parent).free<20*1024**3):raise ValueError('insufficient finite budget/storage')
    erratum=dict(previous_claim='same producer load variants do not cross roles',correct=False,
        groups=[dict(group=g,roles=sorted(r),sources=[s['id'] for s in old['sources'] if group(s['query'])==g])
                for g,r in old_groups.items() if len(r)>1],
        treatment='retain old results; consumed validation is development protection; all old test labels are consumed regression only, never fitting/selection')
    a=dict(version=VERSION,id='matrix-nangate45-N4-refit-v1',platform='nangate45',profile_sha256=p['profile_sha256'],
        baseline=str(BASE),sources=sources,tasks=tasks,files=files,producer_role_audit=dict(new_groups=len(roles),cross_role_groups=0,baseline_erratum=erratum),
        call_caps=dict(synth=n,grt=n,final=0,support=10*n),serial_workers=1,threads=2,memory_limit_MiB=4096,minimum_available_MiB=12288,
        synth_timeout_s=300,grt_timeout_s=1200,support_timeout_s=120,worst_case_leaf_walltime_s=wall,CPU_envelope_s=2*wall,
        starting_usage=used,automatic_retries=0,sampling_layout_overrides=old['sampling_layout_overrides'],
        refit_metrics=['Add.delay_ps','G.delay_ps'],unchanged_metrics=['Mul.delay_ps','Mul.area_um2','Add.area_um2','G.area_um2'],
        candidate_forms=['frozen_baseline','family_scale','family_affine','shared_log_feature_ridge'],
        request_time_scales=[.5,1.,2.],ridge_alpha=[.1,1.,10.],
        error_contract=dict(median_APE=.15,P95_APE=.35,maximum_source_median_APE=.35,quantile='nearest rank',
                            fresh_validation_max_point_APE=.35),
        selection=['all fresh and consumed-validation gates pass','number of failed gates','equal-source mean APE across the two panels',
                   'worst panel P95','fresh max point APE','form complexity','stable index'],
        clock_selection='baseline function + dependent consumer +180ps; floor600ps; quantize25ps; factors .75/1.05/2; freeze before any new labels',
        region_review='report measured setup slack/T; suitable abs(slack/T)<=.2, loose>.2, tight<-.2; descriptive only; no clock retuning from tests',
        full_D_ready=False,R1_R5_modified=False,application_PPA_used=False)
    write(root/'admission.json',a);write(root/'progress.json',dict(completed=[],phase='admitted',errors=[]))
    return dict(sources=len(sources),tasks=n,roles=dict(Counter(t['role'] for t in tasks)),references={s['id']:s['reference'] for s in sources})


def verify(root):
    a=read(Path(root)/'admission.json')
    if a['version']!=VERSION:raise ValueError('unknown refit admission')
    for path,h in a['files'].items():
        if sha(path)!=h:raise ValueError('frozen campaign dependency drift: '+path)
    for s in a['sources']:
        if sha(s['rtl'])!=s['rtl_sha256'] or group(s['query'])!=s['producer_group']:raise ValueError('source changed')
    if a['profile_sha256']!=profile('nangate45')['profile_sha256']:raise ValueError('profile changed')
    return a
