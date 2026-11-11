"""Revalidate every original fitting label without physical optimization."""
import argparse
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse import operator_ownership_replay_v1 as replay,model_logical_ownership_v2 as ownership


def run(data_path,out):
    if out.exists():raise ValueError('preserve earlier dataset qualification')
    data=read(data_path);checks=[];cached={}
    assert data['mode']=='fitting'
    for row in data['rows']:
        folder=Path(row['measurement_path']);stage=row['stage'];path=folder/(stage+'-labels.json');old=read(path)
        if sha(path)!=row['label_sha256']:raise ValueError('old label changed')
        if str(folder) not in cached:cached[str(folder)]=(read(folder/'query-contract.json'),read(folder/'liberty-pins.json'))
        contract,base_pins=cached[str(folder)];pins=dict(base_pins)
        for line in (folder/'reports'/replay.SUFFIX/('vulsim_'+stage+'_cells.tsv')).read_text().splitlines():
            n,count,area,filler,kind=line.split('\t')
            if n not in pins:pins[n]=dict(sequential=False,buffer_or_inverter=False,physical_only=True,data_pins=[],pins={},area_um2=0 if filler=='1' else float(area))
        task=dict(target_ps=row['target_ps']);packet=replay.packet_at(folder/'reports'/replay.SUFFIX/('context_'+stage),task,pins,contract)
        normalized=ownership.normalize(packet,contract['nodes'],contract['banks'])
        # These are already accepted old snapshots with no unowned logic. No
        # recovery occurs, so no top-port census is inferred or used to admit a
        # new owner. Recovered stages use the actual ODB BTerm census instead.
        cert=ownership.resolve(normalized,contract['nodes'],{})
        if cert['recovered'] or not cert['complete']:raise ValueError('old accepted stage now needs recovery')
        label=ownership.extract(packet,contract['nodes'],contract['banks'],{},cert)
        for key in ('nodes','operator_delay_ps','comb_area_um2','data_setup_slack_ps','owner_area_um2','total_cell_area_um2','path_decompositions'):
            if label[key]!=old[key]:raise ValueError('accepted physical label changed '+row['id']+'/'+key)
        checks.append(dict(row=row['id'],source=row['source_id'],stage=stage,role=row['role'],label_sha256=row['label_sha256'],unchanged=True))
        if len(checks)%100==0:print('OWNERSHIP_VALID_DATASET stages='+str(len(checks)),flush=True)
    write(out,dict(status='passed_all_fitting_labels_unchanged',dataset_sha256=sha(data_path),stages=len(checks),points=sum(r['stage']=='grt' for r in data['rows']),
        checks=checks,roles_unchanged=True,independent_test_labels_read=False,new_synth=0,new_grt=0,full_D_ready=False))
    print(dict(status='passed_all_fitting_labels_unchanged',stages=len(checks)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.data.resolve(),a.out.resolve())
