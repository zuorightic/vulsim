"""Recompute G raw labels, fit optimality, held-out metrics and D scores; no EDA."""
from pathlib import Path
from collections import Counter
from copy import deepcopy
import hashlib,io,json,math,sys,tarfile,tempfile
HERE=Path(__file__).resolve().parent
index=json.loads((HERE/'index.json').read_text())
def digest(b):return hashlib.sha256(b).hexdigest()
raw=b''.join((HERE/n).read_bytes() for n in index['parts'])
if digest(raw)!=index['archive_sha256']:raise ValueError('portable archive identity differs')
with tempfile.TemporaryDirectory(prefix='G-portable-replay-') as temp:
    root=Path(temp)
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tar:
        for member in tar:
            if not member.isfile() or Path(member.name).is_absolute() or '..' in Path(member.name).parts:raise ValueError('unsafe evidence member')
            data=tar.extractfile(member).read()
            if digest(data)!=index['files'][member.name]:raise ValueError('evidence member hash differs')
            p=root/member.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    sys.path.insert(0,str(root))
    from experiments.arithmetic_dse import model_qualification_labels as reader
    from experiments.arithmetic_dse.reduction_function_v2 import predict,features
    from regression.arithmetic_fused_d import audit
    def read(p):return json.loads(p.read_text())
    proofs=read(root/'proofs.json');packets=0
    for packet in proofs['packets']:
        d=root/packet['directory'];pins=read(root/packet['pins']);meta=read(d/'label.json');q=read(d/'query-contract.json');prefix=d/packet['prefix']
        for line in (d/'cells.tsv').read_text().splitlines():
            n,count,area,filler,kind=line.split('\t')
            if n not in pins:pins[n]=dict(sequential=False,buffer_or_inverter=False,physical_only=True,data_pins=[],pins={},area_um2=0 if filler=='1' else float(area))
        labels=reader.read_snapshot(prefix,packet['target_ps'],meta['metrics']['raw_report_units']['time']['to_ps'],pins,q['nodes'],q['banks'])
        for name in ('operator_delay_ps','comb_area_um2','data_setup_slack_ps','total_cell_area_um2'):
            if not math.isclose(labels[name],meta[name],rel_tol=1e-10,abs_tol=1e-7):raise ValueError('raw physical label differs: '+name)
        if not labels['ownership_complete'] or not labels['operator_maximum_covered']:raise ValueError('incomplete raw labels')
        if packet.get('negative_arc'):
            arc=packet['negative_arc'];bad=deepcopy(pins);bad[arc['master']]['timing_arcs'].remove(arc['arc'])
            try:reader.read_snapshot(prefix,packet['target_ps'],1.,bad,q['nodes'],q['banks'])
            except ValueError:pass
            else:raise ValueError('deleted real Liberty arc accepted')
        packets+=1
    model=read(root/'experiments/arithmetic/models/asap7_G_reduction_v1/reduction.json');candidate=read(root/'fit/candidate.json')
    for k,v in candidate.items():
        if k!='quality_status' and model[k]!=v:raise ValueError('published parameters/domain differ from frozen candidate')
    def quant(v,q):
        v=sorted(v);x=(len(v)-1)*q;i=int(x);return v[i]+(v[min(i+1,len(v)-1)]-v[i])*(x-i)
    dataset={}
    for role in ('train','validation','independent'):
        rows=read(root/('fit/'+role+'-data.json'))['rows'];dataset[role]=rows
        summary=read(root/('fit/'+('train-quality' if role=='train' else role)+'.json'))
        for label,key in [('delay_ps','delay'),('area_um2','area')]:
            errors=[]
            for row in rows:
                f=features(row['query']['output_bits'],row['query']['terms'],row['target_ps'])
                for n,v in row['features'].items():
                    if not math.isclose(v,f[n],rel_tol=1e-10,abs_tol=1e-8):raise ValueError('prediction-time G features differ')
                p=predict(model,row['query']['output_bits'],row['query']['terms'],row['target_ps'])
                errors.append(abs(p[label]-row[label])/row[label])
                raw_label=read(root/proofs['labels'][row['physical_label_sha256']])
                if row['delay_ps']!=raw_label['operator_delay_ps'] or row['area_um2']!=raw_label['comb_area_um2']:raise ValueError('dataset label differs from physical packet')
            for name,q in [('median',.5),('P95',.95)]:
                if not math.isclose(quant(errors,q),summary['metrics'][key][name],rel_tol=1e-9,abs_tol=1e-10):raise ValueError('held-out metric differs')
        if summary['status']!='passed':raise ValueError('failed function published')
    if any(row['target_ps'] in (1000,1250) for role in ('train','validation') for row in dataset[role]):raise ValueError('unseen exact T consumed before independent test')
    for label in ('delay_ps','area_um2'):
        m=model[label];rows=dataset['train'];counts=Counter(r['source'] for r in rows)
        for j,(name,co) in enumerate(zip(m['features'],m['coefficients'])):
            gradient=0.;scale=max(r['features'][name] for r in rows) or 1.
            for r in rows:
                p=sum(r['features'][n]*c for n,c in zip(m['features'],m['coefficients']))
                gradient+=(p-r[label])*r['features'][name]/r[label]**2/counts[r['source']]
            gradient*=scale
            if co<0 or (co>1e-12 and abs(gradient)>1e-6) or (co<=1e-12 and gradient < -1e-6):raise ValueError('train NNLS optimum/KKT differs')
    bundle_path=root/'experiments/arithmetic/models/asap7_fused_D_prototype_v1/bundle.json';bundle=read(bundle_path);source=read(root/'source-request.json')['source'];targets=[]
    for path in sorted((root/'outputs').glob('*/selection.json')):
        r=read(path);targets.append(audit(r,source,bundle,bundle_path.parent))
        if digest((path.parent/'D.sv').read_bytes())!=r['artifact']['rtl_sha256']:raise ValueError('D RTL identity differs')
    rp=root/'reuse/output/selection.json'
    if rp.exists():
        rr=read(rp);reuse=audit(rr,read(root/'reuse/request.json')['source'],bundle,bundle_path.parent)
        if reuse['counts']['candidates']==44 or reuse['counts']['G_queries']==0:raise ValueError('new-graph reuse not exercised')
    for q,c in zip(read(root/'production-parity/queries.json'),read(root/'production-parity/cpp.json'),strict=True):
        try:p=predict(model,q['output_bits'],q['terms'],q['target_ps'])
        except ValueError:
            if c['status']!='cost_uncovered':raise ValueError('published C++ rejected-domain difference')
            continue
        if c['status']!='covered' or any(not math.isclose(p[k],c[k],rel_tol=1e-10,abs_tol=1e-8) for k in ('delay_ps','area_um2')):raise ValueError('published C++ numerical difference')
    for p in proofs['simulation_logs']:
        if 'FUNCTION_D_RTL_PASS' not in (root/p).read_text():raise ValueError('actual RTL success receipt absent')
    print('G_PORTABLE_REPLAY_PASS packets='+str(packets)+' D_targets='+str(len(targets))+' NNLS_KKT=passed no_EDA_or_compiler=True')
