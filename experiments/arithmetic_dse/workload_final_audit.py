"""Check every selected implementation against fresh native owner metadata.

This is an evaluation audit, never an input to candidate prices or ranking.
It checks the final A/B/C/D and attribution artifacts after target changes,
including the expanded grammar. Native emission and Python owner/semantics
checks are independent of the selected implementation's functional receipt.
"""
import argparse
import os
from pathlib import Path

from .workload_abcd import read,write,sha
from .workload_contracts import load
from .workload_demand import Graph
from .workload_final_software import export,ENV
from .workload_owned import verify_plan
from .workload_v10 import binding,Prices


def audit(root):
    root=Path(root).resolve();cases={c['id']:c for c in load()['cases']};rows=[]
    sentinel=root/'no-eda-bin'
    if sentinel.exists():ENV['PATH']=str(sentinel)+os.pathsep+os.environ['PATH']
    binding_doc=binding();prices=Prices(binding_doc)
    for p in sorted((root/'selected').glob('*/T*/*/selection.json')):
        m=read(p);cid=m['case'];block,limb=m['grammar'];T=m['T_clk_ps'];L=m['L']
        native=root/cid/f"final-{m['method']}-b{block}-w{limb}-T{T}-L{L}"
        if not (native/'inventory.json').exists():
            native=export(root,cases[cid],block,limb,T,L,[m['placement']],tag='audit-'+m['method'])
        view=read(native/'inventory.json')['views'][0];folder=native/view['directory']
        for name in ('workload.sv','graph.json','owners.json','state.json'):
            source=native/name if name=='graph.json' else folder/name
            same=(sha(source)==sha(p.parent/name) if name=='workload.sv' else read(source)==read(p.parent/name))
            if not same:raise ValueError('selected/native artifact differs: '+str(p.parent/name))
        graph=Graph(read(native/'graph.json'))
        result=verify_plan(native,view,graph,binding_doc,
            predictor=lambda owner,ops,regions,diag:prices.owner(owner,ops,regions,diag))
        functional=read(p.parent/'functional-receipt.json')
        if functional['status']!='passed' or functional['rtl_sha256']!=m['rtl_sha256']:
            raise ValueError('selected functional receipt differs')
        rows.append(dict(case=cid,T_ps=T,L=L,method=m['method'],status='passed',
            native_checks=result,rtl_sha256=m['rtl_sha256'],receipt_sha256=sha(p.parent/'functional-receipt.json')))
        Graph.origins.cache_clear();Graph.roots.cache_clear()
        print('IMPLEMENTATION_AUDIT_PASS '+cid+' T'+str(T)+' '+m['method'],flush=True)
    result=dict(status='passed',records=len(rows),required_records=95,complete=len(rows)==95,rows=rows,
        native_artifacts_match=True,application_PPA_read=False,EDA_calls=0,model_refitted=False,
        source_sha256=sha(__file__))
    write(root/'all-selected-owner-audit.json',result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();print(audit(a.root))
