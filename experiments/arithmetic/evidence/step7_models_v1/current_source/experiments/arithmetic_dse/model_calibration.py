"""Independent synthetic graph and reset/enable calibration task generator."""
import argparse
import json
from pathlib import Path
from .budget import POLICY,Ledger
from .model_collection import PROTOCOL,sha,write
from .platforms import profile

CALIBRATION=Path(__file__).with_name('configs')/'model_calibration_v5.json'


def source(split):
    if 'primitive_operations' in json.loads(CALIBRATION.read_text()):
        from .model_stage_samples import source as mixed_source
        return mixed_source(split)
    cfg=json.loads(CALIBRATION.read_text());fan=cfg['splits'][split]['fanout']
    modules=[];ports=['input wire clk,rstn,iv','output reg ov'];instances=[];labels=[]
    specs=[('state',w,0) for w in cfg['state_widths']]
    if split=='test':specs += [('tree',w,5) for w in cfg['context_multiply_widths']]
    else:specs += [('chain',w,n) for w in cfg['context_multiply_widths'] for n in cfg['splits'][split]['chain_lengths']]
    for i,(kind,w,n) in enumerate(specs):
        name=f's{i:03d}';result=w if kind=='state' else 2*w
        if kind=='state':input_widths=[w];nodes=[];expr='x0'
        elif kind=='chain':
            input_widths=[w,w]+[result]*(n-1);nodes=[{'operation':'mul','lhs_width':w,'rhs_width':w,'result_width':result,'inputs':[]}]
            expr='wire ['+str(result-1)+':0] v0=x0*x1;\n'
            for k in range(1,n):
                expr+=f'wire [{result-1}:0] v{k}=v{k-1}+x{k+1};\n';nodes.append({'operation':'add','lhs_width':result,'rhs_width':result,'result_width':result,'inputs':[k-1]})
            expr+=f'assign value=v{n-1};'
        else:
            input_widths=[w]*6;nodes=[];expr=''
            for k in range(3):
                expr+=f'wire [{result-1}:0] v{k}=x{2*k}*x{2*k+1};\n';nodes.append({'operation':'mul','lhs_width':w,'rhs_width':w,'result_width':result,'inputs':[]})
            expr+=f'wire [{result-1}:0] v3=v0+v1;\nassign value=v3+v2;'
            nodes += [{'operation':'add','lhs_width':result,'rhs_width':result,'result_width':result,'inputs':[0,1]},
                      {'operation':'add','lhs_width':result,'rhs_width':result,'result_width':result,'inputs':[3,2]}]
        arguments=[f'input wire [{width-1}:0] in{k}' for k,width in enumerate(input_widths)]
        module=f'(* keep_hierarchy=1 *) module Cell_{name}(input wire clk,rstn,iv,'+','.join(arguments)+f',output wire [{fan*result-1}:0] y);\n'
        coreports=[]
        for k,width in enumerate(input_widths):
            module+=f'(* keep *) reg [{width-1}:0] src{k};\nalways @(posedge clk) if(!rstn)src{k}<=0;else if(iv)src{k}<=in{k};\n'
            coreports.append(f'input wire [{width-1}:0] x{k}')
        if kind=='state':
            value='src0'
        else:
            modules.append(f'(* keep_hierarchy=1 *) module Core_{name}('+','.join(coreports)+f',output wire [{result-1}:0] value);\n'+expr+'\nendmodule\n')
            module+=f'wire [{result-1}:0] value;Core_{name} core('+','.join(f'.x{k}(src{k})' for k in range(len(input_widths)))+',.value(value));\n';value='value'
        for branch in range(fan):
            # Process keep is transferred to DFF cells by proc_dff. Registers
            # with identical D remain real independent loads, checked after map.
            module+=f'(* keep *) reg [{result-1}:0] dst{branch};\n(* keep *) always @(posedge clk) '
            if kind=='state':module+=f'if(!rstn)dst{branch}<=0;else if(iv)dst{branch}<={value};\n'
            else:module+=f'dst{branch}<={value};\n'
            module+=f'assign y[{branch*result} +: {result}]=dst{branch};\n'
        modules.append(module+'endmodule\n');connections=['.clk(clk)','.rstn(rstn)','.iv(iv)']
        for k,width in enumerate(input_widths):ports.append(f'input wire [{width-1}:0] x{i}_{k}');connections.append(f'.in{k}(x{i}_{k})')
        ports.append(f'output wire [{fan*result-1}:0] y{i}');connections.append(f'.y(y{i})');instances.append(f'Cell_{name} {name}('+','.join(connections)+');')
        labels.append({'id':name,'source_cells':name+'/src*','target_cells':[name+'/y*',name+'/dst*'],'instance_scope':name+'/',
                       'arithmetic_scope':name+'/core/','role':'state' if kind=='state' else 'synthetic_context','topology':kind,
                       'lhs_width':w,'result_width':result,'fanout':fan,'graph_nodes':nodes,
                       'no_formal_or_holdout_case_replication':True,'state_reset':'synchronous_zero','state_enable':True})
    text='\n'.join(modules)+'\nmodule ModelBundle('+',\n'.join(ports)+');\nalways @(posedge clk)if(!rstn)ov<=0;else ov<=iv;\n'+'\n'.join(instances)+'\nendmodule\n'
    return text,labels


def prepare(out):
    out.mkdir(parents=True,exist_ok=False);tasks=[];cfg=json.loads(PROTOCOL.read_text())
    for split in ('train','validation','test'):
        directory=out/split;directory.mkdir();rtl,labels=source(split);(directory/'input.sv').write_text(rtl)
        write(directory/'contract.json',{'version':'arithmetic-model-labels-v1','split':split,'source_group':'calibration-'+split,'labels':labels,'calibration_protocol_sha256':sha(CALIBRATION)})
        for platform in cfg['platform_order']:
            p=profile(platform);ref=cfg['reference_abc_ps'][platform]
            tasks.append({'id':platform+'-calibration-'+split,'platform':platform,'profile_sha256':p['profile_sha256'],
                'rtl':str((directory/'input.sv').resolve()),'rtl_sha256':sha(directory/'input.sv'),'top':'ModelBundle','period_ps':ref,'abc_target_ps':ref,'stage':'grt',
                'sample_contract':str((directory/'contract.json').resolve()),'sample_contract_sha256':sha(directory/'contract.json'),
                'source_group':'calibration-'+split,'split':split,'samples':len(labels),'synth_timeout_s':300,'route_timeout_s':1200,'memory_limit_MiB':8192,
                'capacity_scope':'<=35 primitive/state fixtures and <=8 synthetic small DAGs; multiply inputs<=32; bounded by completed primitive W32 collections; no formal/holdout replicas'})
    a={'version':'arithmetic-model-collection-admission-v1','id':out.name,'purpose':'arithmetic_model_collection','policy_sha256':sha(POLICY),'protocol_sha256':sha(PROTOCOL),
       'supplemental_protocol':{'path':str(CALIBRATION.resolve()),'sha256':sha(CALIBRATION)},'tasks':tasks,'automatic_retries':0,
       'call_caps':{'synth':12,'grt':12,'final':0},'support_walltime_s':7200,'worst_case_leaf_walltime_s':12*1860+7200,
       'later_work_reserved':{'walltime_s':86400,'CPU_time_s':172800,'synth':688,'grt':688},'main_matrix_authorized':False,
       'storage':'full logs/ODB local ignored; deterministic compressed paths/identities/labels and models in portable successor; remote not yet confirmed'}
    write(out/'admission.json',a);print({'prepared_calibration_tasks':12,'no_physical_calls_started':True})


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);prepare(ap.parse_args().out)
