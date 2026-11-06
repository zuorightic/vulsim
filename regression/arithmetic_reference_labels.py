"""Independent ownership/timing fixtures and corruption guards; no measured labels."""
import argparse
from collections import Counter
import copy
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_collection import sha,write
from experiments.arithmetic_dse.model_reference_labels import partition,labels
from experiments.arithmetic_dse.model_reference_samples import spec,requests
from experiments.arithmetic_dse.platforms import profile


def worker(out,pins):
    out.mkdir(parents=True,exist_ok=False);cells=json.loads(pins.read_text());p=profile('asap7');prefix=out/'fixture'
    ff=next(n for n,c in cells.items() if c['sequential'] and c['clock_pins'] and c['data_pins'] and len(c['clock_pins'])==1)
    buf=next(n for n,c in cells.items() if c['buffer_or_inverter']);gate=next(n for n,c in cells.items() if not c['sequential'] and not c['buffer_or_inverter'] and sum(v['direction']=='input' for v in c['pins'].values())==2)
    Q=next(k for k,v in cells[ff]['pins'].items() if v['direction']=='output');D=cells[ff]['data_pins'][0];CLK=cells[ff]['clock_pins'][0]
    Y=next(k for k,v in cells[gate]['pins'].items() if v['direction']=='output')
    instance_names=['launch/data_a','launch/valid','capture/data','capture/valid','external/data','external/valid']
    inst={n:ff for n in instance_names};inst.update({'core/logic':gate,'observer/logic':gate,'core/clock_repair':buf,'root_repair':buf})
    def raw(instance_map):
        counts=Counter(instance_map.values());Path(str(prefix)+'_instances.tsv').write_text(''.join(n+'\t'+m+'\t0 0\tR0\n' for n,m in instance_map.items()))
        Path(str(prefix)+'_cells.tsv').write_text(''.join(f'{m}\t{count}\t{cells[m]["area_um2"]}\t0\tCORE\n' for m,count in counts.items()))
        conns=['instance\tpin\tdirection\tnet']
        for name,master in instance_map.items():
            for pin,value in cells[master]['pins'].items():
                if value['direction'] not in ('input','output'):continue
                net='leafclk' if name in instance_names and pin==CLK else name+'_'+pin
                if name=='core/clock_repair':net='leafclk' if value['direction']=='output' else 'clk'
                conns.append('\t'.join([name,pin,value['direction'].upper(),net]))
        Path(str(prefix)+'_reference_connections.tsv').write_text('\n'.join(conns)+'\n')
    raw(inst);area,instances,_=partition(prefix,cells,p,expected={'input_service':2,'native_state':2,'external_state':2})
    if area['owner_cells'].get('shared_clock')!=1 or 'core/clock_repair' not in area['clock_buffer_instances']:
        raise ValueError('clock buffer incorrectly charged to arithmetic by hierarchy prefix')
    if sum(area['owner_cells'].values())!=len(inst):raise ValueError('cell charged more than once')
    fixture_spec=spec('add_u32');rows=['id\tkind\tstart\tend\tstart_arrival\tend_arrival\tdelay\tpoints\tslack\tsetup_margin_s\tclk_skew_s']
    for request in requests(fixture_spec):
        id,kind=request['id'],request['kind']
        ends={'data':'capture/data','native_enable':'capture/data','valid':'capture/valid','external_data':'external/data','external_valid':'external/valid','input_data':'launch/data_a','input_enable':'launch/data_a','input_valid':'launch/valid'}
        starts={'data':'launch/data_a','native_enable':'launch/valid','valid':'launch/valid','external_data':'capture/data','external_valid':'capture/valid'}
        end=ends[id]+'/'+D
        if kind=='port':
            start={'input_data':'a[0]','input_enable':'we_a','input_valid':'iv'}[id];a,b=8100,8150;points=[(start,a),(end,b)];slack=32320
        else:
            start=starts[id]+'/'+Q;a,b=20,(120 if id=='data' else 70)
            points=[(starts[id]+'/'+CLK,0),(start,a)]
            if id=='data':points.append(('core/logic/'+Y,100))
            points.append((end,b));slack=40500-(b-a)-30
        rows.append(f'{id}\t{kind}\t{start}\t{end}\t{a}\t{b}\t{b-a}\t{len(points)}\t{slack}\t1e-11\t2e-11')
        Path(str(prefix)+'_reference_'+id+'_points.tsv').write_text(''.join(f'{pin}\t{value}\n' for pin,value in points))
        Path(str(prefix)+'_reference_'+id+'.rpt').write_text('synthetic reader fixture only, not measured timing\n')
    table=Path(str(prefix)+'_reference_paths.tsv');text='\n'.join(rows)+'\n';table.write_text(text)
    values=labels(prefix,fixture_spec,40500,1,cells,instances)
    data=next(r for r in values if r['id']=='data')
    if (data['reference_data_delay_ps'],data['capture_suffix_ps'],data['clock_capture_term_ps'],data['joint_reference_overhead_ps'])!=(80,20,30,50):
        raise ValueError('reference core/capture/clock decomposition wrong')
    if any(r['clock_capture_term_ps']!=30 for r in values if r['kind']=='port'):raise ValueError('input IO delay not subtracted exactly once')
    rejected=[]
    def refuse(name,action):
        try:action()
        except ValueError:rejected.append(name)
        else:raise ValueError('corrupted fixture accepted: '+name)
    table.write_text(text.replace('20\t120\t100','20\t120\t101'));refuse('wrong-arrival-difference',lambda:labels(prefix,fixture_spec,40500,1,cells,instances));table.write_text(text)
    table.write_text(text.replace('capture/data/'+D,'capture/data/'+CLK));refuse('clock-pin-used-as-D',lambda:labels(prefix,fixture_spec,40500,1,cells,instances));table.write_text(text)
    table.write_text(text.replace('1e-11','nan'));refuse('nonfinite-clock-term',lambda:labels(prefix,fixture_spec,40500,1,cells,instances));table.write_text(text)
    points_path=Path(str(prefix)+'_reference_data_points.tsv');original=points_path.read_text()
    points_path.write_text(original.replace('core/logic/'+Y,'observer/logic/'+Y));refuse('missing-core-output',lambda:labels(prefix,fixture_spec,40500,1,cells,instances));points_path.write_text(original)
    points_path.write_text(original.replace('core/logic/'+Y+'\t100','core/logic/'+Y+'\t130'));refuse('negative-capture-suffix',lambda:labels(prefix,fixture_spec,40500,1,cells,instances));points_path.write_text(original)
    wrong=dict(inst);wrong['unowned_logic']=wrong.pop('core/logic');raw(wrong);refuse('unattributed-functional-cell',lambda:partition(prefix,cells,p));raw(inst)
    refuse('overlapping-owners',lambda:partition(prefix,cells,p,scopes={'core/':'arithmetic','core/logic':'native_state','launch/':'input_service','capture/':'native_state','external/':'external_state','observer/':'observer'}))
    connections=Path(str(prefix)+'_reference_connections.tsv');original_connections=connections.read_text();connections.write_text('\n'.join(line for line in original_connections.splitlines() if not line.startswith('capture/data\t'+CLK+'\t'))+'\n');refuse('missing-state-clock',lambda:partition(prefix,cells,p));connections.write_text(original_connections)
    instance_file=Path(str(prefix)+'_instances.tsv');original_instances=instance_file.read_text();instance_file.write_text(original_instances+original_instances.splitlines()[0]+'\n');refuse('duplicate-physical-cell',lambda:partition(prefix,cells,p));instance_file.write_text(original_instances)
    result={'status':'passed','clock_owner_precedes_hierarchy':True,'all_cells_accounted_once':True,
        'core_capture_clock_decomposition_checked':True,'input_IO_subtracted_once':True,'negative_checks':rejected,
        'Liberty_pin_table_sha256':sha(pins),'producer_sha256':{str(path.relative_to(ROOT)):sha(path) for path in [Path(__file__).resolve(),ROOT/'experiments/arithmetic_dse/model_reference_labels.py']},
        'fixture_timing_is_measured':False,'PPA_calls':0}
    write(out/'proof.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('run','worker'));p.add_argument('--out',type=Path,required=True);p.add_argument('--pins',type=Path,required=True);a=p.parse_args()
    if a.action=='worker':worker(a.out.resolve(),a.pins.resolve())
    else:
        from experiments.arithmetic_dse.budget import Ledger
        from experiments.arithmetic_dse.model_m2_cec import leaf
        out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);ledger=Ledger();ctx={'target_platform':'asap7','admission_id':out.name,'task_id':'reference-cell-and-timing-negative-preflight'}
        with ledger.job(ctx):leaf([sys.executable,'-B',str(Path(__file__).resolve()),'worker','--out',str(out/'software'),'--pins',str(a.pins.resolve())],out,'preflight',300,ledger,ctx)
        print((out/'preflight.log').read_text()[-2500:])
