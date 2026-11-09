"""Actual RTL/generic-FF and synthetic physical-reader corruption checks."""
import argparse
import ast
from collections import Counter
import copy
import gzip
import json
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse import model_fast_measurement as m
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha

CONFIG=ROOT/'experiments/arithmetic_dse/configs/model_fast_probe_v1.json'
YOSYS=Path('/home/zyrv/OpenROAD-flow-scripts/tools/install/yosys/bin/yosys')
PINS=ROOT/'build/step7-reference-20261106/preflight-v4/software/liberty-pin-classes.json'


def prepare(out):
    out.mkdir(parents=True,exist_ok=False);cfg=read(CONFIG)
    evidence=ROOT/'experiments/arithmetic/evidence/step7_fast_samples_v1';pool=json.loads(gzip.decompress((evidence/'text-pool.json.gz').read_bytes()))
    for item in pool.values():
        if __import__('hashlib').sha256(item['text'].encode()).hexdigest()!=item['sha256']:raise ValueError('parent sampling source pool changed')
    original=json.loads(pool['samples.json']['text']);cases=copy.deepcopy(original['cases'])
    base=next(c for c in cases if c['spec'].get('operation')=='mul' and c['spec']['lhs_width']==32 and c['spec']['rhs_width']==32 and c['spec']['result_width']==64)
    extra=copy.deepcopy(base);extra['module']='FourBankSample';extra['spec']['capture_banks']=4;extra['vector_parent']=base['module'];cases.append(extra)
    modules=[];decl=[];assign=[];checks=[];init=[]
    for i,c in enumerate(cases):
        s=c['spec'];name=c['module'];a,b,r=(s[k] for k in ('lhs_width','rhs_width','result_width'));banks=s.get('capture_banks',1);w=a+b+4+2*r
        modules.append(m.source(s,name));(out/(name+'.hex')).write_text(pool['software/'+c.get('vector_parent',name)+'.hex']['text'])
        decl.append(f'reg [{w-1}:0] v{i}[0:95];reg [{a-1}:0] a{i};reg [{b-1}:0] b{i};reg ci{i},ri{i},iv{i};wire [{banks-1}:0] y{i};wire ov{i};wire [{r-1}:0] comb{i};')
        decl.append(f'{name} dut{i}(.clk(clk),.rstn(ri{i}),.iv(iv{i}),.a(a{i}),.b(b{i}),.cin(ci{i}),.y(y{i}),.ov(ov{i}));')
        decl.append(f'{name}Core core{i}(.a(a{i}),.b(b{i}),.cin(ci{i}),.value(comb{i}));')
        assign.append(f'{{a{i},b{i},ci{i},ri{i},iv{i}}}=v{i}[j][{w-1}:{2*r+1}];')
        checks.append(f'if(comb{i}!==v{i}[j][{2*r}:{r+1}])$fatal(1,"core{i} row%0d",j);if(ov{i}!==v{i}[j][0])$fatal(1,"valid{i} row%0d",j);')
        for k in range(banks):
            checks.append(f'if(j>0 && (dut{i}.capture.data{k}!==v{i}[j][{r}:1] || y{i}[{k}]!==( ^v{i}[j][{r}:1])))$fatal(1,"capture{i} bank{k} row%0d",j);')
        init.append(f'$readmemh("{out/(name+".hex")}",v{i});')
    (out/'kernels.sv').write_text('\n'.join(modules))
    (out/'testbench.sv').write_text('module MeasureTb;reg clk=0;integer j;\n'+'\n'.join(decl)+'\ninitial begin\n'+'\n'.join(init)+'\nfor(j=0;j<96;j=j+1)begin clk=0;\n'+'\n'.join(assign)+'\n#5;clk=1;#1;\n'+'\n'.join(checks)+f'\n#4;end\n$display("FAST_MEASUREMENT_PASS kernels={len(cases)} comparisons={len(cases)*96}");$finish;end\nendmodule\n')
    for p in cfg['probes']:
        d=out/p['id'];d.mkdir();(d/'input.sv').write_text(m.source(p['spec']));write(d/'spec.json',p['spec'])
        (d/'geometry.ys').write_text(f'read_verilog -sv {d/"input.sv"}\nhierarchy -check -top ModelBundle\nproc\nopt\ntechmap\nopt\nwrite_json {d/"generic.json"}\n')
    write(out/'sources.json',dict(cases=len(cases),comparisons=len(cases)*96,protocol_sha256=sha(CONFIG),RTL_sources={p['id']:sha(out/p['id']/'input.sv') for p in cfg['probes']}))


def fixtures(out,pins):
    from experiments.arithmetic_dse.platforms import profile
    out.mkdir(parents=True);cells=read(pins);p=profile('asap7');prefix=out/'fixture'
    ff=next(n for n,c in cells.items() if c['sequential'] and len(c['clock_pins'])==1 and c['data_pins']);gate=next(n for n,c in cells.items() if not c['sequential'] and not c['buffer_or_inverter'] and sum(v['direction']=='input' for v in c['pins'].values())==2)
    q=next(n for n,v in cells[ff]['pins'].items() if v['direction']=='output');d=cells[ff]['data_pins'][0];clock=cells[ff]['clock_pins'][0];y=next(n for n,v in cells[gate]['pins'].items() if v['direction']=='output')
    instances={name:ff for name in ('launch/storage_a','launch/valid','capture/storage0','capture/valid')};instances.update({'core/gate':gate,'observer/gate':gate})
    Path(str(prefix)+'_instances.tsv').write_text(''.join(n+'\t'+v+'\t0 0\tR0\n' for n,v in instances.items()))
    Path(str(prefix)+'_cells.tsv').write_text(''.join(f'{n}\t{count}\t{cells[n]["area_um2"]}\t0\tCORE\n' for n,count in Counter(instances.values()).items()))
    connections=['instance\tpin\tdirection\tnet']
    for n,master in instances.items():
        for pin,meta in cells[master]['pins'].items():
            if meta['direction'] in ('input','output'):connections.append('\t'.join((n,pin,meta['direction'].upper(),'clk' if pin==clock and master==ff else n+'_'+pin)))
    Path(str(prefix)+'_reference_connections.tsv').write_text('\n'.join(connections)+'\n')
    lines=['id\tkind\tstart\tend\tstart_arrival\tend_arrival\tdelay\tpoints\tslack\tsetup_margin_s\tclk_skew_s']
    for id in ('data0','valid'):
        start=('launch/storage_a' if id=='data0' else 'launch/valid')+'/'+q;end=('capture/storage0' if id=='data0' else 'capture/valid')+'/'+d
        points=[(start,20)]+([('core/gate/'+y,100)] if id=='data0' else [])+[(end,120 if id=='data0' else 70)]
        delta=points[-1][1]-20
        lines.append(f'{id}\tregister\t{start}\t{end}\t20\t{20+delta}\t{delta}\t{len(points)}\t{1500-delta-30}\t1e-11\t2e-11')
        Path(str(prefix)+'_reference_'+id+'_points.tsv').write_text(''.join(n+'\t'+str(v)+'\n' for n,v in points));Path(str(prefix)+'_reference_'+id+'.rpt').write_text('synthetic reader fixture; not measured timing\n')
    table=Path(str(prefix)+'_reference_paths.tsv');raw='\n'.join(lines)+'\n';table.write_text(raw)
    spec=dict(operation='mul',lhs_width=1,rhs_width=1,result_width=1);geom=dict(owner_FF_bits={'input_service':2,'native_state':2},banks={'data0':dict(FF_bits=1)})
    def query():return m.observations(prefix,spec,1500,1,cells,p,geom)
    result=query();data=next(x for x in result['paths'] if x['id']=='data0')
    if (data['data_delay_ps'],data['core_delay_ps'],data['capture_suffix_ps'],data['boundary_H_ps'])!=(100,80,20,30):raise ValueError('clock/core/suffix decomposition differs')
    failures=[]
    def reject(name,action):
        try:action()
        except ValueError:failures.append(name)
        else:raise ValueError('invalid measurement accepted: '+name)
    table.write_text(raw.replace('20\t120\t100','20\t120\t101'));reject('wrong_delay',query);table.write_text(raw)
    table.write_text(raw.replace('capture/storage0/'+d,'capture/storage0/'+clock));reject('clock_pin_as_data',query);table.write_text(raw)
    table.write_text(raw.replace('1e-11','nan'));reject('nonfinite_clock_term',query);table.write_text(raw)
    path=Path(str(prefix)+'_reference_data0_points.tsv');points=path.read_text();path.write_text(points.replace('core/gate/','observer/gate/'));reject('missing_core',query);path.write_text(points)
    path.write_text(points.replace('\t100\n','\t130\n'));reject('negative_capture_suffix',query);path.write_text(points)
    old=geom['banks']['data0']['FF_bits'];geom['banks']['data0']['FF_bits']=2;reject('lost_capture_state',query);geom['banks']['data0']['FF_bits']=old
    ffpath=Path(str(prefix)+'_instances.tsv');old=ffpath.read_text();ffpath.write_text(old+old.splitlines()[0]+'\n');reject('duplicate_instance',query);ffpath.write_text(old)
    return dict(reader_status='passed',negative_checks=failures,synthetic_labels_are_measurements=False)


def verify(out):
    cfg=read(CONFIG);sources=read(out/'software/sources.json');log=(out/'simulate.log').read_text()
    if f'FAST_MEASUREMENT_PASS kernels={sources["cases"]} comparisons={sources["comparisons"]}' not in log or '%Warning' in (out/'verilator.log').read_text():raise ValueError('measurement wrapper RTL incomplete or warning')
    geometries={}
    for p in cfg['probes']:
        geom=m.generic_geometry(read(out/'software'/p['id']/'generic.json'),'ModelBundle',p['spec']);geometries[p['id']]=geom
        if sha(out/'software'/p['id']/'input.sv')!=sources['RTL_sources'][p['id']]:raise ValueError('measurement RTL changed')
    guards=fixtures(out/'reader-fixtures',PINS)
    names=[Path(__file__),Path(m.__file__),Path(m.samples.__file__),CONFIG]
    proof=dict(status='passed',version=m.VERSION,protocol_sha256=sha(CONFIG),producer_sha256={str(p.relative_to(ROOT)):sha(p) for p in names},
        generic_geometry=geometries,RTL_sources=sources['RTL_sources'],kernels=sources['cases'],arithmetic_comparisons=sources['comparisons'],
        reset_bubbles_unconditional_capture=True,Liberty_pin_table_sha256=sha(PINS),source_role='not_training',PPA_calls=0,**guards)
    write(out/'proof.json',proof);print(json.dumps(proof),flush=True)


def reader_successor(parent,out):
    from experiments.arithmetic_dse.platforms import profile
    from experiments.arithmetic_dse import model_fast_sdc
    a=read(parent/'admission.json');old=read(parent/'software-proof.json');out.mkdir(parents=True,exist_ok=False)
    old_file=parent/'source/experiments/arithmetic_dse/model_fast_measurement.py'
    if sha(old_file)!=old['producer_sha256']['experiments/arithmetic_dse/model_fast_measurement.py']:raise ValueError('original software producer not preserved')
    old_ast=ast.parse(old_file.read_text());new_ast=ast.parse(Path(m.__file__).read_text())
    for name in ('source','known_result','live_operand','generic_geometry'):
        before=next(n for n in old_ast.body if isinstance(n,ast.FunctionDef) and n.name==name)
        after=next(n for n in new_ast.body if isinstance(n,ast.FunctionDef) and n.name==name)
        if ast.dump(before,include_attributes=False)!=ast.dump(after,include_attributes=False):raise ValueError('reader successor changed arithmetic/geometry semantics')
    guards=fixtures(out/'fixtures',PINS);pins=read(PINS);rows=[]
    progress=read(parent/'progress.json')
    names=progress['completed']+[e['task_id'] for e in progress['errors']]
    for name in names:
        task=next(t for t in a['tasks'] if t['id']==name);d=Path(task['inherit_completed']['directory']) if task.get('inherit_completed') else parent/'runs'/task['id'];manifest=read(d/'manifest.json')
        for name,h in manifest.get('evidence_sha256',{}).items():
            if sha(d/name)!=h:raise ValueError('saved physical snapshot changed')
        prefix=d/'reports/asap7/arithmetic_probe/base/vulsim_synth'
        row=dict(task_id=task['id'],manifest_sha256=sha(d/'manifest.json'))
        if Path(str(prefix)+'_instances.tsv').exists():
            ownership,instances,_=m.partition(prefix,pins,profile('asap7'),expected=task['geometry']['owner_FF_bits'])
            row.update(mapped_FF_bits=ownership['owner_FF_bits'],capture_bindings=m.capture_bank_bindings(m.canonical_instances(instances),task['geometry'],pins))
        ports=model_fast_sdc.rtl_ports((d/'input.sv').read_text(),'ModelBundle');raw=(d/'results/asap7/arithmetic_probe/base/1_synth.sdc').read_text()
        actual=model_fast_sdc.verify_sdc(raw,profile('asap7'),task['period_ps'],ports)
        rejected=False
        try:model_fast_sdc.verify_sdc(raw.replace('get_ports {y}', 'get_ports {unregistered_y}'),profile('asap7'),task['period_ps'],ports)
        except ValueError:rejected=True
        if 'get_ports {y}' in raw and not rejected:raise ValueError('scalar spelling adapter accepted missing actual port')
        row.update(SDC_actual_port_coverage_checked=True,unregistered_output_rejected=rejected,SDC_adapter=model_fast_sdc.VERSION)
        rows.append(row)
    proof=copy.deepcopy(old);proof.update(reader_status='passed',negative_checks=guards['negative_checks'],reader_version=m.READER_VERSION,
        predecessor_software_sha256=sha(parent/'software-proof.json'),saved_synth_alias_bindings=rows,
        arithmetic_and_geometry_AST_unchanged=True,no_new_synthesis_or_routing=True,
        producer_sha256={str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),Path(m.__file__),Path(m.samples.__file__),CONFIG,Path(model_fast_sdc.__file__))})
    write(out/'proof.json',proof);print(json.dumps(dict(status='passed',reader_version=m.READER_VERSION,bindings=rows,PPA_calls=0)),flush=True)


def run(out):
    from experiments.arithmetic_dse.budget import Ledger,POLICY,usage
    from experiments.arithmetic_dse.processes import run_command
    out.mkdir(parents=True,exist_ok=False);ledger=Ledger();before=read(ledger.path);cfg=read(CONFIG);limits=read(POLICY)['resources'];u=usage(before['entries']);later=cfg['later_work_reserved']
    envelope=cfg['resources']['support_walltime_envelope_s']+len(cfg['probes'])*len(cfg['SDC_ps'])*cfg['resources']['per_task_walltime_envelope_s']
    if (u['walltime_s']+envelope+later['walltime_s']>limits['max_global_walltime_h']*3600 or u['CPU_time_s']+4*envelope+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600):raise ValueError('measurement preflight, finite probes and later work not funded')
    ctx=dict(target_platform='asap7',admission_id=out.name,task_id='fast-measurement-software')
    env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4');commands=[]
    with ledger.job(ctx):
        def execute(cmd,name,timeout):
            reservation=ledger.reserve(None,timeout,4,'fast_measurement_software_preflight',cmd,out/name,context=ctx);record=run_command(cmd,out,name,timeout,env,8192,cpu_limit_s=reservation['CPU_time_s']);ledger.finish(reservation,record)
            commands.append({**record,'budget_reservation_id':reservation['id']});write(out/'commands.json',commands)
            if record['exit_code']:raise RuntimeError(name+' failed; see '+record['log'])
            print(name+': '+Path(record['log']).read_text()[-500:],flush=True)
        execute([sys.executable,'-B',str(Path(__file__)),'prepare','--out',str(out/'software')],'prepare',120)
        execute(['verilator','--binary','--timing','--top-module','MeasureTb','--Mdir',str(out/'obj'),'-j','4',str(out/'software/kernels.sv'),str(out/'software/testbench.sv')],'verilator',600)
        execute([str(out/'obj/VMeasureTb')],'simulate',120)
        for p in read(CONFIG)['probes']:execute([str(YOSYS),'-s',str(out/'software'/p['id']/'geometry.ys')],'geometry-'+p['id'],120)
        execute([sys.executable,'-B',str(Path(__file__)),'verify','--out',str(out)],'verify',120)
    after=read(ledger.path);write(out/'resource-increment.json',dict(entries=after['entries'][len(before['entries']):],usage=usage(after['entries']),PPA_calls=0))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','verify','run','reader-successor'));p.add_argument('--out',type=Path,required=True);p.add_argument('--parent',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare(a.out.resolve())
    elif a.action=='verify':verify(a.out.resolve())
    elif a.action=='reader-successor':
        if not a.parent:p.error('--parent required')
        reader_successor(a.parent.resolve(),a.out.resolve())
    else:run(a.out.resolve())
