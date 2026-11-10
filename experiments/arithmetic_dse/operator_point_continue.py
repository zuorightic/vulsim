"""Explicit metadata/source-guard continuation of saved successful stages.

Never repeats synthesis or grt. Finished grt points use only saved reports or
read-only report queries. Synth-only checkpoints are returned for guarded
first-time grt continuation. Original failed histories/partial labels survive.
"""
from pathlib import Path
import os
import shutil
import sys
from types import FunctionType

from .model_fast_preflight import read,write,sha,key
from . import model_fast_sdc_v3 as sdc
from . import model_qualification_labels as labels
from . import backend
from .platforms import profile,verify_wire_readback
from .model_m2_live_cec_v3 import verify_proof
from .processes import run_command

SUFFIX=Path('asap7/arithmetic_probe/base')


def continue_points(root,number,progress,old):
    sources={r['id']:r for r in read(root/'corpus/manifest.json')['sources']};recoveries=dict(old.get('inherit_synth_by_source',{}));receipts=[];completed=0
    for source,state in [(sources[p.name],p) for p in (root/'raw').iterdir() if p.name in sources]:
        history_path=state/'history.json'
        if not history_path.exists():continue
        history=read(history_path)
        if not history or history[-1]['status']!='failed':continue
        failed=history[-1];t=failed['SDC_ps'];task=source['id']+'-T'+str(t);point=state/('target-'+str(t));folder=point/'runs'/task
        synth_path=folder/'synth.command.json'
        if not synth_path.exists() and (folder/'manifest.json').exists():
            inherited=read(folder/'manifest.json').get('checkpoint_reuse',{})
            if inherited.get('directory'):synth_path=Path(inherited['directory'])/'synth.command.json'
        if not synth_path.exists():continue
        synth=read(synth_path)
        if synth['exit_code']!=0:continue # A genuine failed physical stage stays failed.
        if (folder/'grt.command.json').exists() and read(folder/'grt.command.json')['exit_code']!=0:continue
        if not (folder/'grt.command.json').exists():
            # Preserve this exact paid synth and its failed history, then let
            # the ordinary guarded executor perform grt for the first time.
            m=read(folder/'manifest.json');before={str(p.relative_to(folder)):sha(p) for p in (folder/'results'/SUFFIX).iterdir() if p.is_file()}
            if sha(folder/'input.sv')!=source['rtl_sha256']:raise ValueError('continuation RTL changed')
            sdc.verify_sdc((folder/'results'/SUFFIX/'1_synth.sdc').read_text(),profile('asap7'),t,sdc.rtl_ports((folder/'input.sv').read_text(),'ModelBundle'),serialization_stage='synth')
            stop=root/'reader-stops'/('continuation-'+str(number)+'-'+task);stop.parent.mkdir(exist_ok=True);point.rename(stop)
            saved=stop/'failed-history.json';history_path.rename(saved);write(history_path,history[:-1]);parent=stop/'runs'/task
            recoveries[source['id']]=dict(directory=str(parent),manifest_sha256=sha(parent/'manifest.json'),files_sha256=before,original_failed_history_sha256=sha(saved),
                source_role=source['role'],target_ps=t,reason='explicit successful synth checkpoint after metadata/source guard stop; first grt only')
            receipts.append(dict(source=source['id'],target_ps=t,mode='synth_reused_first_grt_pending',physical_stages_repeated=0));continue
        # Everything below is read-only with respect to the saved circuit.
        # The enclosing admitted support command accounts these query children.
        m=read(folder/'manifest.json');pins=read(folder/'liberty-pins.json');contract=read(folder/'query-contract.json');commands=[]
        base=m.get('continuation_base_command')
        if not base:base=next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'))
        def query(command,name):
            env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',QT_QPA_PLATFORM='offscreen')
            record=run_command(command,folder,name,120,env,8192);commands.append(record)
            if record['exit_code']:raise ValueError('saved grt read-only query failed '+record['log'])
        reports=folder/'reports'/SUFFIX
        if not (reports/'vulsim_grt_cells.tsv').exists():query(base+['run','RUN_SCRIPT='+str(backend.ASSETS/'snapshot.tcl'),'RUN_LOG_NAME_STEM=continuation_grt','VULSIM_EVAL_STAGE=grt','VULSIM_EVAL_DB=5_1_grt.odb','VULSIM_EVAL_SDC=5_1_grt.sdc'],'continuation-grt-snapshot')
        if not (reports/'context_grt_node_paths.tsv').exists():query(base+['run','RUN_SCRIPT='+str(folder/'read-context.tcl'),'RUN_LOG_NAME_STEM=continuation_context_grt','VULSIM_EVAL_STAGE=grt','VULSIM_EVAL_DB=5_1_grt.odb','VULSIM_EVAL_SDC=5_1_grt.sdc'],'continuation-context-grt')
        verify_proof(folder/'logs'/SUFFIX/'structural_cec/proof.json',folder/'results'/SUFFIX/'4_before_rsz_lec.v',folder/'results'/SUFFIX/'4_after_rsz_lec.v')
        metadata=[]
        for stage,stem in [('synth','1_synth'),('grt','5_1_grt')]:
            metrics=backend.stage_metrics(reports,stage,read(folder/'liberty_cells.json')['cells'],t,selected=profile('asap7'))
            all_pins=dict(pins)
            for line in (reports/('vulsim_'+stage+'_cells.tsv')).read_text().splitlines():
                name,count,area,filler,kind=line.split('\t')
                if name not in all_pins:all_pins[name]=dict(sequential=False,buffer_or_inverter=False,physical_only=True,data_pins=[],pins={},area_um2=0 if filler=='1' else float(area))
            result=labels.read_snapshot(reports/('context_'+stage),t,metrics['raw_report_units']['time']['to_ps'],all_pins,contract['nodes'],contract['banks'])
            check=sdc.verify_sdc((folder/'results'/SUFFIX/(stem+'.sdc')).read_text(),profile('asap7'),t,sdc.rtl_ports((folder/'input.sv').read_text(),'ModelBundle'),serialization_stage=stage)
            if abs(result['total_cell_area_um2']-metrics['cell_area_um2'])>1e-5:raise ValueError('continued area ownership does not conserve')
            label_path=folder/(stage+'-labels.json')
            if label_path.exists():
                saved=read(label_path)
                if any(saved[k]!=v for k,v in result.items() if k!='physical_training_label_eligible'):raise ValueError('continued numerical label differs')
                backup=folder/(stage+'-labels.before-continuation-'+str(number)+'.json');shutil.copy2(label_path,backup)
                result=saved
            else:
                result.update(stage=stage,source_role=source['role'],metrics=metrics,mapped_contract_sha256=sha(folder/'mapped-contract.json'),stored_SDC_check=check,
                    wire_RC_check=verify_wire_readback(reports/('vulsim_'+stage+'_layer_rc.tsv'),profile('asap7')))
            result.update(physical_training_label_eligible=True,CTS_CEC_sha256=sha(folder/'logs'/SUFFIX/'structural_cec/proof.json'))
            write(label_path,result);metadata.append(dict(stage=stage,label_sha256=sha(label_path),SDC_check=check))
        saved_history=point/('failed-history-before-continuation-'+str(number)+'.json');history_path.rename(saved_history)
        q={k:failed[k] for k in ('SDC_ps','ABC_ps','proposal','reference_ratio')};label=read(folder/'grt-labels.json')
        observed=dict(**q,status='completed',source_id=source['id'],role=source['role'],implementation_id=sha(folder/'grt-labels.json'),
            operator_delay_ps=label['operator_delay_ps'],comb_area_um2=label['comb_area_um2'],data_setup_slack_ps=label['data_setup_slack_ps'],
            operator_maximum_covered=True,data_through_operator_covered=True,ownership_complete=True)
        write(history_path,history[:-1]+[observed]);completed+=1
        receipt=dict(source=source['id'],target_ps=t,mode='saved_grt_readback_only',new_synth=0,new_grt=0,metadata=metadata,read_only_commands=commands,
            old_failed_history_sha256=sha(saved_history),continuation_source_sha256=sha(Path(__file__)))
        write(point/('reader-continuation-'+str(number)+'.json'),receipt);receipts.append(receipt)
    return recoveries,receipts,completed


if __name__=='__main__':
    from .operator_stage4 import DEFAULT
    root=Path(os.environ.get('OPERATOR_STAGE4_ROOT',str(DEFAULT))).resolve()
    progress=read(root/'progress.json');active=root/'active-collection.json';old=read(root/read(active)['path']) if active.exists() else read(root/'collection.json')
    recoveries,receipts,completed=continue_points(root,7,progress,old)
    index=0
    while (root/('continuation-report-'+str(index)+'.json')).exists():index+=1
    write(root/('continuation-report-'+str(index)+'.json'),dict(status='passed',recoveries=recoveries,receipts=receipts,completed=completed,new_synth=0,new_grt=0))
    print(dict(status='passed',completed=completed,new_synth=0,new_grt=0),flush=True)
