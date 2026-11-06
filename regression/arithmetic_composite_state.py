"""Production component binding and independent numerical replay; no fitting or EDA."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

MANIFEST=ROOT/'experiments/arithmetic_dse/configs/model_asap7_d_components_v1.json'


def read(path):
    return json.loads(Path(path).read_text())


def write(path,value):
    Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')


def verify(folder,manifest=MANIFEST):
    manifest=Path(manifest)
    m=read(manifest)
    for ref in m['components'].values():
        path=manifest.parent/ref['path']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=ref['sha256']:
            raise ValueError('component identity differs')
    state=read(manifest.parent/m['components']['native_state']['path'])
    data=read(folder/'native/queries.json')
    if data['PPA_calls'] or data['full_D_ready'] or len(data['rows'])!=175:
        raise ValueError('incomplete production state price exercise')
    coefficients=state['stages']['grt']['area_model']['coefficients']
    boundary=state['stages']['grt']['boundary_model']
    maximum_delta=0.;materialized=0;negative_budget=0
    for row in data['rows']:
        q,p=row['query'],row['price'];slots=q['slots']
        unpack=lambda s,key:sum(int(v,16)<<(64*i) for i,v in enumerate(s[key]))
        d=[s for s in slots if not s['valid'] and s['variable_bits']]
        v=[s for s in slots if s['valid']]
        for s in slots:
            if unpack(s,'variable_mask_hex').bit_count()!=s['variable_bits']:
                raise ValueError('actual slot variable mask/count mismatch')
        db=sum(s['variable_bits'] for s in d);vb=sum(s['variable_bits'] for s in v)
        f=dict(state_bits=db+vb,state_signals=len(d)+len(v),data_bits=db,data_signals=len(d),
            valid_bits=vb,valid_signals=len(v),enable_domains=len({s['enable_stage'] for s in d}),
            reset_one_bits=sum((unpack(s,'variable_mask_hex')&unpack(s,'reset_hex')).bit_count() for s in d),
            max_declared_width=max(s['declared_width'] for s in d),min_variable_width=min(s['variable_bits'] for s in d),
            sdc_period_ps=q['features']['sdc_period_ps'])
        if f!=q['features'] or p['bits']!=f['state_bits'] or p['signals']!=f['state_signals']:
            raise ValueError('independent native state geometry differs')
        expected=dict(area_um2=coefficients[0]*f['state_bits']+coefficients[1]*f['state_signals'],
            input_budget_ps=f['sdc_period_ps']*(1-boundary['io_delay_fraction'])-boundary['input_overhead_ps'],
            register_budget_ps=f['sdc_period_ps']-boundary['register_overhead_ps'])
        for k,x in expected.items():
            maximum_delta=max(maximum_delta,abs(x-p[k]))
            if not math.isclose(x,p[k],rel_tol=1e-12,abs_tol=1e-10):
                raise ValueError('native/Python frozen price or boundary differs')
        if (p['model_sha256']!=m['components']['native_state']['sha256'] or
            p['layout_sha256']!=q['layout_sha256'] or p['joint_arithmetic_boundary_qualified']):
            raise ValueError('wrong model/layout/scope binding')
        materialized+=row['materialized_price_checked']
        negative_budget+=p['input_budget_ps']<=0
    if materialized!=168 or not negative_budget:
        raise ValueError('actual register/negative budget coverage missing')
    diagnostic=read(folder/'native/D-diagnostic.json');selection=diagnostic['selection']
    candidates=selection['candidates']
    if (diagnostic['failure_code']!='cost_uncovered' or selection['candidate_PPA_calls'] or selection['formal_D_selection']
        or [c['id'].split('/')[-1] for c in candidates]!=['original','half','quarter']
        or any(c['failure_code']!='cost_uncovered' for c in candidates)):
        raise ValueError('production D refusal trace/order lost')
    if len({x['test'] for x in data['rejections']})<25:
        raise ValueError('domain/identity guards missing')
    public=[]
    if (folder/'native/public-bank-coverage.json').exists():
        audit=read(folder/'native/public-bank-coverage.json');public=audit['rows']
        if (len(public)!=12 or len({r['case'] for r in public})!=12 or audit['PPA_calls'] or audit['full_D_ready']
            or audit['formal_target_qualification'] or any(not r['query']['materialized_checked'] or
                r['status']!='cost_uncovered' or not r['reason'] or r['all_D_candidates_or_moves_checked'] for r in public)):
            raise ValueError('public original-core bank audit scope/refusals differ')
    result=dict(status='passed',state_queries=len(data['rows']),materialized_queries=materialized,
        maximum_native_Python_delta=maximum_delta,guard_rejections=len(data['rejections']),
        negative_input_budget_queries=negative_budget,trial_move_refresh=True,
        state_component_price_binding_qualified=True,joint_arithmetic_boundary_qualified=False,
        public_original_banks_checked=len(public),public_original_banks_covered=0,full_D_ready=False,PPA_calls=0)
    write(folder/'parity.json',result)
    print(json.dumps(result),flush=True)
    return result


def run(folder,build,binding_only=False,public_manifest=None):
    from experiments.arithmetic_dse.budget import Ledger
    from experiments.arithmetic_dse.model_m2_cec import leaf
    folder.mkdir(parents=True,exist_ok=False)
    ledger=Ledger();context=dict(target_platform='asap7',admission_id=folder.name,task_id='composite-native-state-production-binding')
    commands=[]
    targets=['arithmetic-composite-state-test','arithmetic-published-primitives-test','arithmetic-model-test',
             'pipeline-test','pipeline-reset-test','pipeline-valid-test']
    with ledger.job(context):
        def execute(cmd,stem,timeout=300):
            record=leaf(cmd,folder,stem,timeout,ledger,context);commands.append(record);write(folder/'commands.json',commands)
            print(Path(record['log']).read_text()[-2500:],flush=True)
        if not binding_only:
            execute(['cmake','-S',str(ROOT/'rtlzz'),'-B',str(build),'-DCMAKE_BUILD_TYPE=Release'],'configure')
        execute(['cmake','--build',str(build),'--target',*(targets[:1] if binding_only else targets),'-j4'],'build',1800)
        execute([str(build/'testv2/arithmetic-composite-state-test'),str(ROOT),str(MANIFEST),str(folder/'native')]+
                ([str(public_manifest)] if public_manifest else []),'native',900)
        execute([sys.executable,'-B',str(Path(__file__).resolve()),'verify','--out',str(folder)],'parity')
        if not binding_only:
            model=ROOT/'experiments/arithmetic/evidence/step7_m2_mux_static_v1/asap7-primitives.json'
            execute([str(build/'testv2/arithmetic-published-primitives-test'),str(ROOT),str(model),str(folder/'primitives/native')],'primitives',600)
            execute([sys.executable,'-B',str(ROOT/'regression/arithmetic_published_primitives.py'),'verify',
                     '--out',str(folder/'primitives')],'primitive-parity')
            execute([str(build/'testv2/arithmetic-model-test'),str(ROOT),str(ROOT/'experiments/arithmetic/evidence/step7_models_v1/models'),str(folder/'ordinary')],'ordinary',900)
            circt=Path('/home/zyrv/circt/circt-full-shared-linux-x64/firtool-1.162.0/bin')
            for name in ('pipeline-test','pipeline-reset-test','pipeline-valid-test'):
                execute(['env','--chdir='+str(ROOT/'rtlzz'),'PATH='+str(circt)+os.pathsep+os.environ.get('PATH',''),
                         str(build/'testv2'/name),str(folder/name)],name)
    write(folder/'resource-summary.json',ledger.summary())


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('run','verify'))
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--build',type=Path,default=ROOT/'build/step4-rtlzz')
    parser.add_argument('--binding-only',action='store_true',help='incremental binding test; requires existing configured target')
    parser.add_argument('--public-manifest',type=Path,help='optional existing public-core layout fixtures; not PPA data')
    args=parser.parse_args()
    if args.action=='run':run(args.out.resolve(),args.build.resolve(),args.binding_only,args.public_manifest.resolve() if args.public_manifest else None)
    else:verify(args.out.resolve())
