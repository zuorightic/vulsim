"""Declared isolated RTL microbenchmarks, grouped splits and bounded collection.

This module never consumes case/holdout PPA. Every bundle and all its target
variants belong to one split. An explicit admission is required by the backend.
"""
import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

from .budget import Ledger, POLICY, usage
from .model_features import features
from .platforms import profile

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = Path(__file__).with_name('configs')/'characterization_v5.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n')


def verify_test_release(admission, selection_freeze, platforms):
    """Check the immutable fitting decision before launching or reading test.

    Historical admissions without deferred tests retain their original rules.
    A deferred interval test requires the actual fitting data and candidates,
    not just a file whose name contains 'freeze'.
    """
    admission=Path(admission);a=json.loads(admission.read_text())
    if not a.get('test_read_after_fit_only'):return None
    if selection_freeze is None:raise ValueError('independent test requires --selection-freeze before launch or extraction')
    path=Path(selection_freeze);f=json.loads(path.read_text())
    if (f.get('version')!='arithmetic-mul-interval-selection-freeze-v1'
        or f.get('admission_sha256')!=sha(admission)
        or f.get('protocol_sha256')!=a['supplemental_protocol']['sha256']
        or f.get('test_consumed') is not False):raise ValueError('independent test selection/admission/protocol mismatch')
    if sha(a['supplemental_protocol']['path'])!=f['protocol_sha256']:raise ValueError('changed independent test protocol')
    for name,digest in f.get('training_sources',{}).items():
        if sha(ROOT/name)!=digest or sha(path.parent/'training-source'/name)!=digest:
            raise ValueError('changed frozen training/evaluation source before independent test')
    data_path=Path(f['fitting_dataset_path'])
    if sha(data_path)!=f['dataset_sha256']:raise ValueError('changed frozen fitting dataset')
    data=json.loads(data_path.read_text())
    if (data.get('admission_sha256')!=sha(admission) or data.get('protocol_sha256')!=f['protocol_sha256']
        or data.get('failures') or not data.get('rows')
        or any(r['split'] not in ('train','validation') for r in data['rows'])):raise ValueError('independent test requires complete train/validation data only')
    models={m['platform']:m for m in f['models']}
    if len(models)!=len(f['models']):raise ValueError('duplicate frozen platform model')
    for platform in platforms:
        if platform not in models:raise ValueError('test platform has no frozen model')
        candidate=path.parent/(platform+'.candidate.json')
        if sha(candidate)!=models[platform]['candidate_sha256']:raise ValueError('changed frozen interval candidate')
        if models[platform].get('fit_report_sha256') and sha(path.parent/(platform+'.fit.json'))!=models[platform]['fit_report_sha256']:
            raise ValueError('changed frozen interval fitting report')
        b=json.loads(candidate.read_text());m=b['stages']['grt']['mul_interval_model']
        if (b['target_platform']!=platform or b.get('quality_status')!='awaiting_independent_test'
            or b.get('interval_fit_dataset_sha256')!=f['dataset_sha256']
            or b.get('interval_fit_protocol_sha256')!=f['protocol_sha256']
            or not m['intervals'] or any(e.get('validation_ready') is not True for e in m['intervals'].values())):
            raise ValueError('independent test requires a frozen validation-ready grt interval model')
        expected={t['rtl_sha256'] for t in a['tasks'] if t['platform']==platform and t['split'] in ('train','validation')}
        actual={r['source_sha256'] for r in data['rows'] if r['platform']==platform}
        if actual!=expected:raise ValueError('incomplete fitting task coverage before independent test')
    return sha(path)


def expression(op, w):
    """Return expression, rhs width, result width and a declared shape."""
    binary = {'add': '+', 'sub': '-', 'mul': '*', 'and': '&', 'or': '|',
              'xor': '^', 'compare_eq': '==', 'compare_rel': '<'}
    if op in binary:
        out = 2*w if op == 'mul' else 1 if op.startswith('compare') else w
        return f'a {binary[op]} b', w, out, 'full_mul' if op == 'mul' else 'boolean' if out == 1 else 'same_width'
    if op == 'mul_low': return 'a * b', w, w, 'low_mul'
    if op == 'addcarry': return "{1'b0,a} + {1'b0,b} + cin", w, w+1, 'carry'
    if op == 'eq_zero': return "a == 0", 0, 1, 'boolean'
    if op in ('not', 'neg'): return ('~a' if op == 'not' else '-a'), 0, w, 'same_width'
    if op in ('reduce_or', 'reduce_and', 'reduce_xor'):
        return {'reduce_or':'|a','reduce_and':'&a','reduce_xor':'^a'}[op], 0, 1, 'boolean'
    if op.startswith('mux'):
        branch = {'mux':'b','mux_zero':"'0",'mux_one':"1",'mux_ones':"'1"}[op]
        return f'cin ? a : {branch}', w if op == 'mux' else 0, w, 'same_width'
    if op in ('shl','shr'): return f'a {"<<" if op == "shl" else ">>"} b', max(1,math.ceil(math.log2(w))), w, 'same_width'
    if op in ('div','mod'):
        # The safe wrapper is before launch Q, so this arithmetic scope prices
        # a genuinely dynamic divisor. OR-ing1 would only sample odd divisors.
        return f'a {"/" if op == "div" else "%"} b', w, w, 'same_width'
    raise ValueError('unregistered characterization operation: '+op)


def bundle_source(specs, fanout):
    modules=[];ports=['input wire clk,rstn,iv','output reg ov'];instances=[];labels=[]
    for i, (op,w) in enumerate(specs):
        sample=f's{i:03d}';expr,rhs,out,shape=expression(op,w)
        # Unconditional, reset-free data boundary DFFs. Reset/enable is measured
        # separately, never accidentally charged as arithmetic combinational area.
        divisor=op in ('div','mod')
        core=f'''(* keep_hierarchy = 1 *) module Core_{sample}(input wire [{w-1}:0] a,input wire [{max(rhs,1)-1}:0] b,input wire cin,output wire [{out-1}:0] value);
assign value = {expr};
endmodule
'''
        text=f'''(* keep_hierarchy = 1 *) module Cell_{sample}(input wire clk,rstn,iv,
input wire [{w-1}:0] in_a,input wire [{max(rhs,1)-1}:0] in_b,input wire in_c,
output wire [{fanout*out-1}:0] y);
(* keep *) reg [{w-1}:0] src_a;
(* keep *) reg [{max(rhs,1)-1}:0] src_b;
(* keep *) reg src_c;
wire [{w-1}:0] a=src_a;
wire [{max(rhs,1)-1}:0] b=src_b;
wire cin=src_c;
always @(posedge clk) begin
if(!rstn)begin src_a<=0;src_b<={1 if divisor else 0};src_c<=0;end
else if(iv)begin src_a<=in_a;src_b<={'(in_b==0 ? 1 : in_b)' if divisor else 'in_b'};src_c<=in_c;end
end
wire [{out-1}:0] value;
Core_{sample} core(.a(a),.b(b),.cin(cin),.value(value));
'''
        for branch in range(fanout):
            text+=f'(* keep, dont_touch *) reg [{out-1}:0] dst{branch};\n(* keep *) always @(posedge clk) dst{branch} <= value;\nassign y[{branch*out} +: {out}] = dst{branch};\n'
        modules.append(core+text+'endmodule\n')
        ports += [f'input wire [{w-1}:0] a{i}',f'input wire [{max(rhs,1)-1}:0] b{i}',f'input wire c{i}',f'output wire [{fanout*out-1}:0] y{i}']
        instances.append(f'Cell_{sample} {sample}(.clk(clk),.rstn(rstn),.iv(iv),.in_a(a{i}),.in_b(b{i}),.in_c(c{i}),.y(y{i}));')
        labels.append({'id':sample,'operation':'mul' if op=='mul_low' else op,
                       'source_cells':sample+'/a*','target_cells':[sample+'/y*',sample+'/dst*'],
                       'instance_scope':sample+'/', 'arithmetic_scope':sample+'/core/', 'lhs_width':w,'rhs_width':rhs,
                       'result_width':out,'fanout':fanout,'result_shape':shape,
                       'rtl_operation':op,'boundary':'capture_unconditional_DFF; launch_reset_enable_before_Q_excluded_from_data_path'})
        # Include all dynamic operand launch flops, not just a. Wildcard matches
        # a,b,cin banks; destination banks have the distinct dst prefix.
        labels[-1]['source_cells']=sample+'/src*'
    top='module ModelBundle('+',\n'.join(ports)+');\nalways @(posedge clk) if(!rstn) ov<=0; else ov<=iv;\n'+'\n'.join(instances)+'\nendmodule\n'
    return '\n'.join(modules)+top,labels


def prepare(out, platforms, widths, operations, stage='grt'):
    out.mkdir(parents=True,exist_ok=False)
    protocol=json.loads(PROTOCOL.read_text());tasks=[]
    specs=[(op,w) for op in operations for w in widths]
    # Different fanout boundary graphs are separate complete source families.
    # No bundle is split between fitting/validation/test, even across targets.
    partitions=protocol['context_partitions']
    for split,fans in [('train',partitions['train_fanouts']),('validation',partitions['validation_fanouts']),('test',partitions['test_fanouts'])]:
        for fan in fans:
            for chunk in range(0,len(specs),12):
                name=f'{split}-f{fan}-b{chunk//12:02d}';folder=out/name;folder.mkdir()
                rtl,labels=bundle_source(specs[chunk:chunk+12],fan)
                (folder/'input.sv').write_text(rtl)
                write(folder/'contract.json',{'version':'arithmetic-model-labels-v1','split':split,'source_group':name,'labels':labels})
                for platform in platforms:
                    p=profile(platform);ref=protocol['reference_abc_ps'][platform]
                    tasks.append({'id':platform+'-'+name,'platform':platform,'profile_sha256':p['profile_sha256'],
                                  'rtl':str((folder/'input.sv').resolve()),'rtl_sha256':sha(folder/'input.sv'),
                                  'top':'ModelBundle','period_ps':ref,'abc_target_ps':ref,'stage':stage,
                                  'sample_contract':str((folder/'contract.json').resolve()),'sample_contract_sha256':sha(folder/'contract.json'),
                                  'source_group':name,'split':split,'samples':len(labels),'capacity_scope':'bounded_microbenchmark_bundle_max12_samples; widths<=32',
                                  'synth_timeout_s':300,'route_timeout_s':1200,'memory_limit_MiB':8192})
    a={'version':'arithmetic-model-collection-admission-v1','id':out.name,'purpose':'arithmetic_model_collection',
       'policy_sha256':sha(POLICY),'protocol_sha256':sha(PROTOCOL),'tasks':tasks,'automatic_retries':0,
       'call_caps':{'synth':len(tasks),'grt':len(tasks) if stage=='grt' else 0,'final':0},
       'support_walltime_s':7200,'worst_case_leaf_walltime_s':len(tasks)*(300+(1200 if stage=='grt' else 0)+360)+7200,
       'stops':['tool_failure','unexpected_label_or_units','pending_ledger','resource_limit'],
       'later_work_reserved':{'walltime_s':86400,'CPU_time_s':172800,'synth':688,'grt':688,'purpose':'future domains/matrix, not launched by this admission'},
       'storage':{'full':'local ignored build plus catalog/hash; remote retention unconfirmed','portable':'compressed labels, source contracts, raw path points, manifests, models'},
       'data_exclusions':'all formal/holdout/previous capacity/label probes excluded; this admission creates new isolated microbenchmarks only',
       'scope':'stage model; unsupported widths/templates/constant patterns explicitly uncovered'}
    write(out/'admission.json',a)
    print(json.dumps({'tasks':len(tasks),'samples_per_platform':sum(t['samples'] for t in tasks if t['platform']==platforms[0]),'admission':str(out/'admission.json')}))


def verify_admission(args,p,rtl,ledger):
    a=json.loads(args.admission.read_text());matches=[t for t in a['tasks'] if t['id']==args.task_id]
    if a['purpose']!='arithmetic_model_collection' or a['id']!=args.admission_id or len(matches)!=1 or a['policy_sha256']!=sha(POLICY) or a['protocol_sha256']!=sha(PROTOCOL) or a['automatic_retries']!=0:raise ValueError('invalid frozen collection admission')
    t=matches[0]
    if t['split']=='test':verify_test_release(args.admission,getattr(args,'selection_freeze',None),[t['platform']])
    if a.get('supplemental_protocol') and sha(a['supplemental_protocol']['path'])!=a['supplemental_protocol']['sha256']:raise ValueError('changed supplemental sampling protocol')
    if (t['platform']!=p['platform'] or t['profile_sha256']!=p['profile_sha256'] or t['rtl_sha256']!=sha(rtl)
        or t['top']!=args.top or t['period_ps']!=args.period_ps or t['abc_target_ps']!=args.abc_target_ps or t['stage']!=args.stage
        or args.threads!=2 or args.memory_limit_mib!=t['memory_limit_MiB'] or args.synth_timeout_s!=t['synth_timeout_s']
        or args.route_timeout_s!=t['route_timeout_s'] or args.resume_synth_from or args.io_delay_max_ps is not None
        or not args.sample_contract or sha(args.sample_contract)!=t['sample_contract_sha256'] or args.budget_purpose!='characterization'):raise ValueError('collection differs from frozen task')
    entries=json.loads(ledger.path.read_text())['entries'];total=usage(entries)
    if total['pending'] or any(e.get('admission_id')==a['id'] and e.get('task_id')==t['id'] for e in entries):raise ValueError('pending or previously attempted collection task')
    previous=[e for e in entries if e.get('admission_id')==a['id']];limits=json.loads(POLICY.read_text())['resources'];reserved=a['later_work_reserved']
    for s,key in [('synth','max_synthesis_calls'),('grt','max_global_route_calls'),('final','max_detailed_route_calls')]:
        if total[s]+a['call_caps'][s]-sum(e['stage']==s for e in previous)+reserved.get(s,0)>limits[key]:raise ValueError('collection/future calls not funded')
    remaining=a['worst_case_leaf_walltime_s']-sum(e['walltime_s'] for e in previous)
    if total['walltime_s']+remaining+reserved['walltime_s']>limits['max_global_walltime_h']*3600 or total['CPU_time_s']+2*remaining+reserved['CPU_time_s']>limits['max_tool_CPU_time_h']*3600:raise ValueError('collection/future time not funded')
    return sha(args.admission)


def run(out,splits=None,max_tasks=None,selection_freeze=None):
    if max_tasks is not None and (type(max_tasks) is not int or max_tasks<1):raise ValueError('positive task bound required')
    admission=(out/'admission.json').resolve();a=json.loads(admission.read_text());rows=[]
    if splits is None and a.get('test_read_after_fit_only'):splits=['train','validation']
    selected=[t for t in a['tasks'] if splits is None or t['split'] in splits]
    test_platforms={t['platform'] for t in selected if t['split']=='test'}
    if test_platforms:verify_test_release(admission,selection_freeze,test_platforms)
    for t in a['tasks']:
        if splits is not None and t['split'] not in splits:continue
        if (out/'PAUSE').exists():
            print('PAUSED between tasks; no physical process left by this runner',flush=True);return
        directory=Path(t['reuse_directory']) if t.get('reuse_directory') else out/'runs'/t['id']
        if directory.exists():
            m=json.loads((directory/'manifest.json').read_text())
            if m['status']!='completed':raise ValueError('previous failure stops this batch; explicit successor required')
            if t.get('reuse_directory'):
                if sha(directory/'manifest.json')!=t['reuse_manifest_sha256'] or sha(directory/'input.sv')!=t['rtl_sha256'] or m['platform_profile']['profile_sha256']!=t['profile_sha256']:
                    raise ValueError('changed inherited collection measurement')
        else:
            print('START',t['id'],flush=True)
            cmd=[sys.executable,'-m','experiments.arithmetic_dse.backend','--platform',t['platform'],'--admission',str(admission),'--admission-id',a['id'],'--task-id',t['id'],
                 '--rtl',t['rtl'],'--top',t['top'],'--out',str(directory),'--period-ps',str(t['period_ps']),'--abc-target-ps',str(t['abc_target_ps']),
                 '--stage',t['stage'],'--budget-purpose','characterization','--sample-contract',t['sample_contract']]
            if selection_freeze is not None:cmd+=['--selection-freeze',str(Path(selection_freeze).resolve())]
            directory.parent.mkdir(exist_ok=True)
            with (out/(t['id']+'.driver.log')).open('x') as log:code=subprocess.call(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            m=json.loads((directory/'manifest.json').read_text());print('DONE',t['id'],m['status'],m.get('failure_reason'),flush=True)
            if code:raise RuntimeError('collection stopped: '+t['id']+' '+str(m.get('failure_reason')))
        rows.append({'task_id':t['id'],'status':m['status'],'manifest_sha256':sha(directory/'manifest.json')})
        write(out/'outcome.json',rows)
        if max_tasks is not None and len(rows)>=max_tasks:
            print('STOP at requested successful task bound; no further launches',flush=True);return


def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','run']);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--platforms',nargs='+',default=['asap7','nangate45','sky130hd','gf180']);ap.add_argument('--widths',nargs='+',type=int,default=[8,16,32])
    ap.add_argument('--operations',nargs='+',default=['mul','mul_low','add','sub','mux','compare_eq','compare_rel','and','or','xor','shl','shr','eq_zero','mux_one','addcarry'])
    ap.add_argument('--splits',nargs='+',choices=['train','validation','test'])
    ap.add_argument('--max-tasks',type=int)
    ap.add_argument('--selection-freeze',type=Path,help='frozen validation-ready interval candidates required for deferred test')
    args=ap.parse_args()
    if args.action=='prepare':prepare(args.out,args.platforms,args.widths,args.operations)
    else:run(args.out,args.splits,args.max_tasks,args.selection_freeze)


if __name__=='__main__':main()
