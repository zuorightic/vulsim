#!/usr/bin/env python3
"""Step4: real public request/region/cost paths, RTL scoreboards and rejection cases.

All builds/generation/simulations are charged software leaves. No physical tools
or model training are called. A new output directory is required.
"""
import argparse,copy,hashlib,json,os,random,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.budget import Ledger,usage
from experiments.arithmetic_dse.processes import run_command
from experiments.arithmetic_dse.reference import f32_mul
from experiments.arithmetic_dse.fixed_cost import node_cost
WIDTHS=[8,16,32,64,128,12,24,48,96]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--rtlzz-build',type=Path,default=ROOT/'build/step4-rtlzz');ap.add_argument('--skip-build',action='store_true');ap.add_argument('--circt-bin',type=Path)
    args=ap.parse_args();out=args.out.resolve();build=args.rtlzz_build.resolve()
    if out.exists():ap.error('use a new output directory')
    out.mkdir(parents=True);ledger=Ledger();before=json.loads(ledger.path.read_text());write(out/'usage_before.json',before);commands=[]
    env=os.environ.copy()
    if args.circt_bin:env['PATH']=str(args.circt_bin.resolve())+os.pathsep+env.get('PATH','')
    enabled=env.get('VUL_REGRESSION_CIRCT','1')!='0'
    if enabled and not shutil.which('circt-opt',path=env.get('PATH','')):ap.error('CIRCT enabled but tool unavailable; supply --circt-bin or explicitly set VUL_REGRESSION_CIRCT=0')
    sources=[*ROOT.joinpath('rtlzz/src').rglob('*.cpp'),*ROOT.joinpath('rtlzz/src').rglob('*.hpp'),*ROOT.joinpath('rtlzz/src').rglob('*.h'),Path(__file__),ROOT/'rtlzz/testv2/arithmetic_interface_test.cpp',ROOT/'regression/arithmetic_interfaces/rtl_driver.cpp']
    write(out/'execution_source_sha256.json',{str(p.relative_to(ROOT)):sha(p) for p in sources})
    def run(command,stem,timeout=300,expected=0,cwd=ROOT):
        r=ledger.reserve(None,timeout,2,'step4_interface_validation',command,out/stem,context={'target_platform':'common','admission_id':'step4-software-v1','task_id':stem,'model_version':'not_applicable_step4'})
        # run_command inherits cwd from this process; all paths are absolute.
        old=Path.cwd();os.chdir(cwd)
        try:record=run_command(command,out,stem,timeout,env,8192,cpu_limit_s=r['CPU_time_s'])
        finally:os.chdir(old)
        ledger.finish(r,record);record['budget_reservation_id']=r['id'];record['expected_exit_code']=expected;commands.append(record);write(out/'commands.json',commands)
        if record['exit_code']!=expected:raise RuntimeError(stem+': '+Path(record['log']).read_text()[-2000:])
        return Path(record['log']).read_text()
    if not args.skip_build:
        run(['cmake','--build',str(ROOT/'build'),'--target','vulrtlgen','vulsimgen','-j2'],'root-build',900)
        run(['cmake','-S',str(ROOT/'rtlzz'),'-B',str(build),'-DCMAKE_BUILD_TYPE=Release'],'configure')
        run(['cmake','--build',str(build),'--target','arithmetic-interface-test','predicate-expand','arithmetic-region-test','pipeline-test','pipeline-reset-test','pipeline-valid-test','-j2'],'compiler-build',900)
    generation=run([str(build/'testv2/arithmetic-interface-test'),str(ROOT),str(out/'generated')],'public-core',300)
    assert 'PASS arithmetic interfaces checks=' in generation
    generated=out/'generated'
    # Independent Python cost contract consumes real compiler-region billing widths.
    cost_checks=0
    for w in WIDTHS:
        report=json.loads((generated/f'mul{w}.json').read_text())
        assert report['request']['cost_source_sha256']==sha(ROOT/'experiments/arithmetic_dse/configs/fixed_op_width_v1.json')
        for region in report['graph']['regions']:
            widths=[v['billing_width'] for v in region['inputs']];assert widths==[w,w]
            c=node_cost('Mul',widths,2*w);assert (region['delay'],region['comb'])==(c.delay_weight,c.comb_weight);cost_checks+=1
        identity=report['graph_identity_text'];assert json.loads(identity)==report['graph'];assert hashlib.sha256(identity.encode()).hexdigest()==report['graph_sha256']
        assert hashlib.sha256((report['graph_sha256']+report['schedule_identity_text']).encode()).hexdigest()==report['schedule_sha256']
        assert sha(generated/f'mul{w}.sv')==report['rtl_sha256']
    wrapper='''`timescale 1ns/1ps
module ArithmeticInterfaces(input logic clk,rstn,iv,input logic [127:0] a,b,c,
output logic [255:0] ys[0:8],zs[0:8],output logic [8:0] ovs,
output logic fov,output logic [36:0] fy,fz,fcy,fcz,output logic [63:0] fm,fcm);
'''
    for i,w in enumerate(WIDTHS):
        wrapper+=f'''wire [{2*w-1}:0] y{i},z{i};wire v{i};
mul{w} u{i}(.clk(clk),.rstn(rstn),.iv(iv),.ov(v{i}),.a(a[{w-1}:0]),.b(b[{w-1}:0]),.c(c[{w-1}:0]),.y(y{i}),.z(z{i}));
always_ff @(posedge clk) begin
if(!rstn) begin ovs[{i}]<=0;ys[{i}]<=256'd35;zs[{i}]<=256'd55;end
else begin ovs[{i}]<=v{i};if(v{i})begin ys[{i}]<=256'(y{i});zs[{i}]<=256'(z{i});end end
end
'''
    def pack(a,b):r=f32_mul(a,b);return r.bits|(r.flags<<32)
    resetfp=[pack(0x7f800000,0),pack(0x7f800000,0x3f800000),0]
    wrapper+=f'''wire [36:0] fy0,fz0;wire [63:0] fm0;wire fv0;
top fp(.clk(clk),.rstn(rstn),.iv(iv),.ov(fv0),.a(a[31:0]),.b(b[31:0]),.c(c[31:0]),.y(fy0),.z(fz0),.m(fm0));
fp_comb comb(.iv(iv),.ov(),.a(a[31:0]),.b(b[31:0]),.c(c[31:0]),.y(fcy),.z(fcz),.m(fcm));
always_ff @(posedge clk) begin
if(!rstn)begin fov<=0;fy<=37'd{resetfp[0]};fz<=37'd{resetfp[1]};fm<=64'd0;end
else begin fov<=fv0;if(fv0)begin fy<=fy0;fz<=fz0;fm<=fm0;end end
end
endmodule
'''
    (out/'wrapper.sv').write_text(wrapper)
    run(['verilator','--cc','--exe','--build','-j','2','--top-module','ArithmeticInterfaces','--Mdir',str(out/'obj'),str(out/'wrapper.sv'),*[str(generated/f'mul{w}.sv') for w in WIDTHS],str(generated/'mixed_fp.sv'),str(generated/'mixed_fp_comb.sv'),str(ROOT/'regression/arithmetic_interfaces/rtl_driver.cpp')],'verilator',600)
    rng=random.Random(20261030);pairs=[(0,0),(1,(1<<128)-1),((1<<128)-1,(1<<128)-1),(1<<127,2)]
    pairs += [(1<<i,1<<j) for i in (0,7,15,31,63,95,127) for j in (0,7,15,31,63,95,127)]
    fp_edges=[0,0x80000000,1,0x007fffff,0x00800000,0x3f7fffff,0x3f800000,0x3f800001,0x40000000,0x7f7fffff,0xff7fffff,0x7f800000,0xff800000,0x7fc12345,0x7f812345]
    pairs += [(a,b) for a in fp_edges for b in fp_edges]
    pairs += [(rng.getrandbits(128),rng.getrandbits(128)) for _ in range(2000)]
    rows=[(a,b,rng.getrandbits(128),int(i<128 or i%7 not in (1,2)),int(i not in (0,1,300,301,900,1600))) for i,(a,b) in enumerate(pairs)]
    rows += [(0,0,0,0,1)]*4
    def limbs(n):return ' '.join(f'{(n>>(32*i))&0xffffffff:x}' for i in range(4))
    (out/'vectors.txt').write_text(''.join(f'{limbs(a)} {limbs(b)} {limbs(c)} {iv:x} {rst:x}\n' for a,b,c,iv,rst in rows))
    actual=run([str(out/'obj/VArithmeticInterfaces'),str(out/'vectors.txt')],'rtl-run').splitlines();assert len(actual)==len(rows)
    history=[];held=[35,55]*9;heldfp=resetfp;counts={'cycles':len(rows),'valid_checks':0,'data_checks':0,'reset_checks':0,'bubble_hold_checks':0,'comb_fp_checks':0}
    for cycle,(row,line) in enumerate(zip(rows,actual)):
        a,b,c,iv,rst=row;values=[int(v,16) for v in line.split()];assert len(values)==26
        if not rst:history=[];valid=False;held=[35,55]*9;heldfp=resetfp;counts['reset_checks']+=21
        else:
            history.append(row);valid=len(history)>=3 and bool(history[-3][3])
            if valid:
                x,y,z=history[-3][:3];held=[]
                for w in WIDTHS:mask=(1<<w)-1;held += [(x&mask)*(y&mask),(x&mask)*(z&mask)]
                heldfp=[pack(x&0xffffffff,y&0xffffffff),pack(x&0xffffffff,z&0xffffffff),(x&0xffffffff)*(y&0xffffffff)];counts['data_checks']+=21
            else:counts['bubble_hold_checks']+=21
        assert values[0]==(511 if valid else 0) and values[1]==valid,(cycle,'valid',values[:2],valid);counts['valid_checks']+=10
        assert values[2:20]==held,(cycle,'integer data',row,values[2:20],held)
        assert values[20:23]==heldfp,(cycle,'binary32 pipeline',row,values[20:23],heldfp)
        expected=[pack(a&0xffffffff,b&0xffffffff),pack(a&0xffffffff,c&0xffffffff),(a&0xffffffff)*(b&0xffffffff)]
        assert values[23:26]==expected,(cycle,'binary32 combinational',row,values[23:26],expected);counts['comb_fp_checks']+=3
    cli_source=out/'cli.logic.cpp';cli_source.write_text('#include <fixint.hpp>\nInt<32> a,b;Int<64> y;\n#pragma input_port a\n#pragma input_port b\n#pragma output_port y\nvoid top(){y=a*b;}\n')
    def request(platform='asap7',L=3):
        profile=ROOT/f'experiments/arithmetic_dse/configs/platforms/{platform}.json';table=ROOT/'experiments/arithmetic_dse/configs/fixed_op_width_v1.json'
        return {'version':'arithmetic-request-v1','target_platform':platform,'platform_profile':str(profile),'platform_profile_sha256':sha(profile),'cost_mode':'fixed','fixed_cost_table':str(table),'fixed_cost_table_sha256':sha(table),'candidate_policy':'core-original-v1','semantic_profile':'arithmetic-semantics-v2','L':L,'II':1,'target_period_ps':1500,'template_parameters':{}}
    hashes=set();requests={}
    for platform in ('asap7','nangate45','sky130hd','gf180'):
        req=out/(platform+'.request.json');write(req,request(platform));requests[platform]=req;target=out/(platform+'.sv');report=out/(platform+'.report.json')
        run([str(build/'predicate-expand'),'--input',str(cli_source),'--top','top','--vullib',str(ROOT/'vullib'),'--release','--arithmetic-request',str(req),'--arithmetic-report',str(report),'-o',str(target)],'cli-'+platform)
        data=json.loads(report.read_text());assert data['request']['target_platform']==platform;assert data['request']['platform_profile_sha256']==sha(ROOT/f'experiments/arithmetic_dse/configs/platforms/{platform}.json');hashes.add(data['graph_sha256'])
    assert len(hashes)==1
    negative=[]
    for label,patch,code in [('unknown_field',{'rounding':'magic'},'invalid_request'),('signed_profile',{'semantic_profile':'fixed_point'},'template_ineligible'),('split_not_implemented',{'candidate_policy':'mul_half'},'template_ineligible'),('L_mismatch',{'L':4},'invalid_request'),('II_unsupported',{'II':2},'invalid_request'),('wrong_profile',{'target_platform':'gf180'},'invalid_request'),('missing_model',{'cost_mode':'backend-model'},'cost_uncovered'),('unknown_template_parameter',{'template_parameters':{'W':32}},'template_ineligible')]:
        data=request();data.update(patch);path=out/(label+'.request.json');write(path,data);report=out/(label+'.failure.json')
        command=[str(build/'predicate-expand'),'--input',str(cli_source),'--top','top','--vullib',str(ROOT/'vullib'),'--release','--arithmetic-request',str(path),'--arithmetic-report',str(report),'-o',str(out/(label+'.sv'))]
        if label=='L_mismatch':command += ['--latency','2']
        log=run(command,'reject-'+label,expected=1);assert code in log
        assert json.loads(report.read_text())['failure_code']==code;negative.append({'case':label,'code':code,'report':report.name})
    circt={'status':'skipped','reason':'VUL_REGRESSION_CIRCT=0'}
    if enabled:
        run([str(build/'testv2/arithmetic-interface-test'),str(ROOT),str(out/'circt-generated'),'--circt'],'circt-public-core',300)
        native=json.loads((generated/'mul32.json').read_text());other=json.loads((out/'circt-generated/mul32.json').read_text());assert native['graph_sha256']==other['graph_sha256'];assert native['schedule_sha256']==other['schedule_sha256']
        circt={'status':'passed','tool':shutil.which('circt-opt',path=env['PATH']),'graph_and_schedule_match_native':True}
    # Existing generator probe: request L=2 matches the PIPELINE declaration;
    # its pre-existing service/valid wrapper is observed at tick+3.
    vulreq=out/'vul.request.json';write(vulreq,request(L=2))
    for backend,tool in [('native','vulrtlgen'),('software','vulsimgen')]:
        dest=out/('vul-'+backend);command=[str(ROOT/'build'/tool),'-m',str(ROOT/'experiments/arithmetic/backend_probe/Main.utb'),'-f','-o',str(dest)]
        if backend=='native':command += ['--arithmetic-request',str(vulreq)]
        run(command,'vul-'+backend+'-generate');log=run(['bash',str(dest/'run.sh')],'vul-'+backend+'-validate',600);assert 'backend probe passed: 10000 cycles' in log
    report_files=list((out/'vul-native').rglob('*.arithmetic.json'));assert report_files
    for p in report_files:assert json.loads(p.read_text())['request']['L']==2
    after=json.loads(ledger.path.read_text());write(out/'usage_after.json',after)
    result={'version':'arithmetic-interface-regression-v1','status':'passed','cost_cross_checks':cost_checks,'native_cpp_checks':generation.strip(),'functional':counts,'L':3,'II':1,'standalone_N':2,'native_wrapper':'one explicit external output capture; queue history[-L]','negative_requests':negative,'platform_request_graph_hashes_identical':True,'circt':circt,'VUL_bridge':{'request_L':2,'observed_probe_wrapper_ticks':3,'cycles':10000,'reports':[str(p.relative_to(out)) for p in report_files]},'new_usage':usage(after['entries'][len(before['entries']):]),'commands':commands,'new_PPA_calls':{'synth':0,'grt':0,'final':0}}
    write(out/'regression.json',result);print(json.dumps({k:v for k,v in result.items() if k!='commands'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
