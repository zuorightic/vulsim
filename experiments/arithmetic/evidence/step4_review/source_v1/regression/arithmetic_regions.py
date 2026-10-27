#!/usr/bin/env python3
"""Step4: compiler-owned arithmetic regions and binary32 RTL vs integer oracle.

No Yosys/OpenROAD calls. Run from any directory; --softfloat adds the independent
SoftFloat comparison. Outputs are reproducible with the recorded fixed seed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.reference import f32_mul

CASES=['single','serial','parallel','shared','identical','constant']

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,default=ROOT/'build/step4-regions')
    ap.add_argument('--rtlzz-build',type=Path,default=ROOT/'build/step4-rtlzz')
    ap.add_argument('--skip-build',action='store_true')
    ap.add_argument('--softfloat',type=Path)
    args=ap.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    build=args.rtlzz_build.resolve();commands=[]
    def run(command,stem,timeout=300,input_text=None,cwd=ROOT):
        start=time.monotonic()
        p=subprocess.run(list(map(str,command)),cwd=cwd,input=input_text,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
        (out/f'{stem}.stdout').write_text(p.stdout);(out/f'{stem}.stderr').write_text(p.stderr)
        commands.append({'command':list(map(str,command)),'cwd':str(cwd),'exit_code':p.returncode,'walltime_s':time.monotonic()-start})
        if p.returncode:raise RuntimeError(f'{stem} failed ({p.returncode}):\n{p.stdout[-3000:]}\n{p.stderr[-3000:]}')
        return p.stdout
    if not args.skip_build:
        run(['cmake','-S',ROOT,'-B',ROOT/'build'],'root-configure')
        run(['cmake','--build',ROOT/'build','-j2'],'root-build',600)
        run(['cmake','-S',ROOT/'rtlzz','-B',build,'-DCMAKE_BUILD_TYPE=Release'],'configure')
        run(['cmake','--build',build,'--target','arithmetic-region-test','pipeline-test','pipeline-reset-test','pipeline-valid-test','-j2'],'build',600)
    if not shutil.which('circt-opt'):
        raise RuntimeError('Existing pipeline-test requires circt-opt on PATH; add your CIRCT bin directory.')
    check=run([build/'testv2/arithmetic-region-test',ROOT/'vullib',out],'regions',180)
    for name in ['pipeline-test','pipeline-reset-test','pipeline-valid-test']:
        run([build/'testv2'/name],name,180,cwd=ROOT/'rtlzz')
    run(['c++','-std=c++20','-O2','-I'+str(ROOT/'vullib'),ROOT/'regression/arithmetic_regions/host.cpp','-o',out/'host'],'host-build')
    seed=20261027;rng=random.Random(seed)
    edges=[0,0x80000000,1,2,3,0x007ffffe,0x007fffff,0x00800000,0x00800001,
           0x3effffff,0x3f000000,0x3f7fffff,0x3f800000,0x3f800001,0x40000000,
           0x7f7fffff,0xff7fffff,0x7f800000,0xff800000,0x7fc12345,0x7f812345,0xff812345]
    pairs=[(a,b) for a in edges for b in edges]
    pairs += [(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(20000)]
    packed=lambda a,b: (lambda f:f.bits|(f.flags<<32))(f32_mul(a,b))
    host=run([out/'host'],'host',input_text=''.join(f'{a:x} {b:x}\n' for a,b in pairs)).splitlines()
    assert len(host)==len(pairs)
    for (a,b),value in zip(pairs,host):assert int(value,16)==packed(a,b),(hex(a),hex(b),value,f32_mul(a,b))
    softfloat=None
    if args.softfloat:
        from experiments.arithmetic_dse.softfloat_oracle import SoftFloatOracle
        oracle=SoftFloatOracle(args.softfloat,out/'oracle.so')
        for a,b in pairs:
            expected=oracle.multiply(a,b)
            f=f32_mul(a,b)
            assert (f.bits,f.flags)==expected,(a,b,f,expected)
        softfloat={'vectors':len(pairs),'source':str(args.softfloat),'command':oracle.command,'source_sha256':oracle.source_hashes}
    wrapper='`timescale 1ns/1ps\nmodule RegionRegression(input logic [31:0] a,b,c,d,input logic iv,rstn,clk,output logic [36:0] y[0:5],z[0:5],py[0:5],pz[0:5],output logic [5:0] ov);\n'
    for i,name in enumerate(CASES):
        wrapper+=f'{name} c{i}(.a(a),.b(b),.c(c),.d(d),.iv(iv),.ov(),.y(y[{i}]),.z(z[{i}]));\n'
        wrapper+=f'{name}_pipe p{i}(.a(a),.b(b),.c(c),.d(d),.iv(iv),.ov(ov[{i}]),.y(py[{i}]),.z(pz[{i}]),.clk(clk),.rstn(rstn));\n'
    wrapper+='endmodule\n';(out/'wrapper.sv').write_text(wrapper)
    run(['verilator','--cc','--exe','--build','-j','2','--top-module','RegionRegression','--Mdir',out/'obj',out/'wrapper.sv',
         *[out/(name+suffix+'.sv') for name in CASES for suffix in ['', '_pipe']],ROOT/'regression/arithmetic_regions/rtl_driver.cpp'],'verilator',300)
    def values(a,b,c,d):
        first=packed(a,b);second=packed(first&0xffffffff,c)
        return [(first,first),(first,second),(first,packed(c,d)),(first,packed(a,c)),(first,first),(0x40000000,0x40000000)]
    rows=[]
    # Every host vector is also driven through real RTL, including random NaNs.
    for i,(a,b) in enumerate(pairs):
        c,d=rng.getrandbits(32),rng.getrandbits(32)
        valid=int(i%7 not in (1,2));reset=int(i%257!=0)
        rows.append((a,b,c,d,valid,reset))
    output=run([out/'obj/VRegionRegression'],'rtl-run',input_text=''.join(' '.join(f'{x:x}' for x in row)+'\n' for row in rows)).splitlines()
    assert len(output)==len(rows)
    history=[];reset_values=values(0x7f800000,0,0x3f800000,0)
    comb_checks=pipe_checks=reset_checks=0;bubbles=resets=0
    for i,(row,line) in enumerate(zip(rows,output)):
        a,b,c,d,valid,rstn=row;actual=list(map(lambda x:int(x,16),line.split()));assert len(actual)==25
        expected=values(a,b,c,d)
        if not rstn:history=[];resets+=1;valid_out=False
        else:history.append((valid,expected));valid_out=len(history)>=3 and history[-3][0]
        assert actual[-1]==(63 if valid_out else 0),(i,'valid',actual[-1],valid_out)
        for j,(y,z) in enumerate(expected):
            assert actual[4*j:4*j+2]==[y,z],(i,CASES[j],'comb',row,actual[4*j:4*j+2],(y,z));comb_checks+=2
            if not rstn:
                assert actual[4*j+2:4*j+4]==list(reset_values[j]),(i,CASES[j],'reset',actual[4*j+2:4*j+4],reset_values[j]);reset_checks+=2
            elif valid_out:
                assert actual[4*j+2:4*j+4]==list(history[-3][1][j]),(i,CASES[j],'pipe',actual[4*j+2:4*j+4],history[-3][1][j]);pipe_checks+=2
        if rstn and not valid:bubbles+=1
    vul_results=[]
    for backend,tool,extra in [('sim','vulsimgen',[]),('native','vulrtlgen',[]),('circt','vulrtlgen',['--circt'])]:
        target=out/('vul-'+backend)
        run([ROOT/'build'/tool,'-m',ROOT/'regression/arithmetic_regions/vul/Main.utb','-f','-o',target,*extra],'vul-'+backend+'-generate',180)
        log=run([target/'run.sh'],'vul-'+backend+'-run',180)
        result=next(line for line in log.splitlines() if 'FP REGION VUL PASS' in line)
        vul_results.append({'backend':backend,'result':result})
    report={'version':'arithmetic-regions-regression-v1','seed':seed,'cases':CASES,'region_checks':check.strip(),
            'FP_semantics':'binary32 RNE, tininess-after, canonicalNaN, per-operation flags',
            'host_vectors':len(pairs),'softfloat':softfloat,'VUL_end_to_end':vul_results,'RTL_cycles':len(rows),'RTL_combinational_output_checks':comb_checks,
            'RTL_valid_pipeline_output_checks':pipe_checks,'RTL_reset_output_checks':reset_checks,'bubble_cycles':bubbles,'reset_events':resets,
            'pipeline_register_stages':3,'physical_calls':{'synth':0,'grt':0,'final':0},
            'commands':commands,'artifacts_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [out/'regions.txt',*[out/(n+s+'.sv') for n in CASES for s in ['','_pipe']]]}}
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['commands','artifacts_sha256']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
