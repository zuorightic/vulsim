"""Export the callable node function against independent physical points."""
import argparse
from copy import deepcopy
import csv
from pathlib import Path

from .model_fast_preflight import read
from .operator_condition_model import query


def plot(release,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    model=read(release/'operators.json');rows=read(release/'fresh-data.json')['rows']
    fig,axes=plt.subplots(2,2,figsize=(11,7),sharex=True);data=[]
    colors=('#2463a6','#bb4d34')
    for at,op in enumerate(('mul','add')):
        group=[r for r in rows if r['operation']==op]
        for color,sid in zip(colors,sorted({r['source_id'] for r in group})):
            samples=sorted([r for r in group if r['source_id']==sid],key=lambda r:r['target_ps']);base=samples[0]['descriptor'];p=base['local_context']['producer']
            label=f'{op.upper()}({p["lhs_width"]}, {p["rhs_width"]}) → {p["result_width"]}'
            xs=[500+i*12.5 for i in range(201)];delay=[];area=[]
            for t in xs:
                d=deepcopy(base);d['flow_context'].update(target_period_ps=t,abc_target_ps=t);r=query(model,d)
                delay.append(r.get('operator_delay_ps',float('nan')));area.append(r.get('comb_area_um2',float('nan')))
                data.append(dict(operation=op,source=sid,T_ps=t,operator_delay_ps=r.get('operator_delay_ps'),comb_area_um2=r.get('comb_area_um2'),role='function_curve'))
            for col,ys,field in ((0,delay,'operator_delay_ps'),(1,area,'comb_area_um2')):
                ax=axes[at,col];ax.plot(xs,ys,color=color,label=label,linewidth=1.7)
                ax.scatter([r['target_ps'] for r in samples],[r[field] for r in samples],color=color,edgecolor='white',marker='o',s=46,zorder=3)
            for r in samples:data.append(dict(operation=op,source=sid,T_ps=r['target_ps'],operator_delay_ps=r['operator_delay_ps'],comb_area_um2=r['comb_area_um2'],role='independent_measurement'))
        for col in (0,1):
            ax=axes[at,col];ax.grid(alpha=.2);ax.axvline(1000,color='#777777',linestyle=':',linewidth=1);ax.set_title(('Multiplication' if op=='mul' else 'Addition')+' — '+('delay' if col==0 else 'area'))
            ax.set_ylabel('Operator delay (ps)' if col==0 else 'Combinational area (µm²)');ax.legend(frameon=False,fontsize=8)
    for ax in axes[1]:ax.set_xlabel('Requested period T (ps), ABC = SDC')
    fig.suptitle('Released conditional node functions: lines = f(x,T), dots = fresh independent measurements',fontsize=11)
    fig.tight_layout(rect=(0,0,1,.95));out.mkdir(parents=True,exist_ok=True)
    fig.savefig(out/'independent-response.svg');fig.savefig(out/'independent-response.png',dpi=170);plt.close(fig)
    with (out/'independent-response.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
    print(dict(status='exported_function_response',curve_points=804,independent_points=16,new_EDA_calls=0),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--release',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();plot(a.release.resolve(),a.out.resolve())
