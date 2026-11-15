"""Finite steps-5 structural/placement search through the native compiler.

The public model remains diagnostic. No application PPA enters proposals or
selection. Equal grammar/expansion credits and common-pool rescoring expose the
contribution of additional search separately from the price function.
"""
import argparse
from collections import Counter
from copy import deepcopy
import json
import math
import os
from pathlib import Path
import shlex
import shutil
import tempfile

from .sampling_time_contract import ROOT,canonical,sha
from .workload_equivalent_run import read,write,compressed,compact_prediction
from .workload_equivalent import optimize,score_key,request_at,virtual_operator
from .workload_diagnostic import DiagnosticPrices,evaluate
from .workload_v10_replay import old_structure,retarget
from .workload_demand import Graph
from .workload_v10 import binding,Prices
from .workload_owned import verify_plan
from .workload_software_validation import bench,run as command
from .workload_sources import prepare_case
from .workload_reuse_validation import BASE,DEFAULT
from . import wide_arithmetic as arithmetic

BINARY=ROOT/'build/workload-v10-20261115/rtlzz-workload'
TRANSPARENT={'input','wire','slice','bitselect','concat'}


def best_key(row,mode):
    p=row[mode]
    return score_key(p)+(row['structure'],int(row['view']['directory']),row['id'])


def best(rows,mode):
    return min((r for r in rows if r.get(mode)),key=lambda r:best_key(r,mode))


def selected_variant(result):
    entry=result['trace'][int(result['best_variant_id'].split(':')[0])]
    variant=next(v for v in entry['variants'] if v['id']==result['best_variant_id'])
    return entry,variant


def response_receipt(row,prices):
    """Actual tau +/- 12.5%; unchanged shapes/maps and full response functions."""
    entry,variant=selected_variant(row['result']);out=[]
    for node,q in sorted(variant['actual_queries'].items(),key=lambda x:int(x[0])):
        price=prices.operator_price if 'flow_context' in q else prices.reduction_price
        t=q['flow_context']['target_period_ps'] if 'flow_context' in q else q['target_ps']
        values=[dict(tau_ps=t*f,**price(request_at(q,t*f))) for f in (.875,1.,1.125)]
        out.append(dict(node=int(node),budget_ps=entry['budgets_ps'].get(str(node),entry['budgets_ps'].get(node)),
            query_sha256=sha(canonical(q)),values=values,
            area_response=values[-1]['area_um2']-values[0]['area_um2'],
            delay_response=values[-1]['delay_ps']-values[0]['delay_ps']))
    return out


def structural_proposals(parent,mode,prices,policy,seen):
    """Rank finite grammar with a compositional pressure/area heuristic.

    This is proposal ranking only. Native regeneration and fresh full pricing
    determine every admitted candidate, including remainder blocks and carries.
    """
    pred=parent[mode];block,limb=parent['grammar'];reference=block or 32
    owner_queries={r['node']:r['query'] for r in parent['owners']['operators']}
    mults=[r for r in pred['owners'] if r['node'] in owner_queries and
           owner_queries[r['node']]['local_context']['producer']['operation']=='mul']
    sample=owner_queries[mults[0]['node']] if mults else None
    mul_delay=max((r['delay_ps'] for r in mults),default=0.)
    mul_area=sum(r['area_um2'] for r in mults)
    critical=max(pred['stages'],key=lambda s:s['required_ps'])['stage']
    critical_mul=any(parent['view']['placement'][r['node']]==critical for r in mults)
    # Both strategies consume the same observed grammar and ranking algorithm.
    # The static control changes the numerical owner costs via its frozen table.
    proposals=[]
    for b in policy['grammar_mul']:
        for l in policy['grammar_limb']:
            if (b,l) in seen:continue
            if b!=block and l!=limb:continue  # one grammar edit per expansion
            new_b=b or 32;new_delay=mul_delay;new_area=mul_area
            if sample is not None and new_b!=reference:
                if mode=='model':
                    spec=arithmetic.spec('mul',new_b,new_b,2*new_b)
                    q=virtual_operator(sample,spec)
                    # Use the parent's actual equivalent request, not a global
                    # stage budget; full candidates will allocate anew.
                    _,v=selected_variant(parent['result']);actual=v['actual_queries']
                    source=actual.get(str(mults[0]['node']),actual.get(mults[0]['node']))
                    p=prices.operator_price(request_at(q,source['flow_context']['target_period_ps']))
                    new_delay=p['delay_ps'];new_area=math.ceil(32/new_b)**2*p['area_um2']
                else:
                    ratio=new_b/reference
                    new_delay=mul_delay*ratio*ratio
                    new_area=mul_area*ratio*ratio*(math.ceil(32/new_b)/math.ceil(32/reference))**2
            estimates=[]
            for s in pred['stages']:
                at=s['stage'];d=s['comb_delay_ps']
                if mults and any(parent['view']['placement'][r['node']]==at for r in mults):
                    d=max(0.,d-mul_delay+new_delay)
                # A split final add can move carry work across legal cuts. This
                # optimistic bound only prioritizes proposals; no candidate is
                # accepted on this estimate.
                if l and l!=limb and not any(parent['view']['placement'][r['node']]==at for r in mults):
                    d*=max(l,16)/64
                estimates.append(d+s['boundary_ps']+pred['S']['reserve_ps'])
            required=max(pred['port_required_ps'],*estimates)
            area=max(0.,pred['total_area_um2']-mul_area+new_area)
            novelty=abs(math.log2(new_b/reference)) if b!=block else abs((l or 64)-(limb or 64))/64
            key=(0,area,novelty,b,l) if required<=pred['target_ps'] else (1,required-pred['target_ps'],area,novelty,b,l)
            proposals.append(dict(grammar=[b,l],rank_key=key,estimated_required_ps=required,
                estimated_area_um2=area,critical_stage=critical,critical_has_mul=critical_mul,
                reason='one finite grammar edit ranked by complete stage pressure and owner area response',
                approximate_only=True,parent=parent['id']))
    return sorted(proposals,key=lambda r:r['rank_key'])


def canonical_move(raw,units,placement,index,direction,L):
    """Move one compiler unit; transparent successors follow earliest parents."""
    nodes=raw['nodes'];unit_of={n:i for i,u in enumerate(units) for n in u['members']}
    if set(unit_of)!=set(range(len(nodes))):raise ValueError('scheduling unit coverage differs')
    current=[]
    for unit in units:
        stages={placement[n] for n in unit['members']}
        if len(stages)!=1:raise ValueError('input placement splits a native group')
        current.append(next(iter(stages)))
    current[index]+=direction
    if not 0<=current[index]<L:return None,'stage_out_of_range'
    for u,unit in enumerate(units):
        parents={unit_of[a['node']] for i in unit['members'] for a in nodes[i]['operands']
                 if a['node'] is not None and unit_of[a['node']]!=u and not nodes[a['node']]['constant']}
        earliest=max((current[p] for p in parents),default=0)
        computational=any(nodes[i]['operation'] not in TRANSPARENT and not nodes[i]['constant'] for i in unit['members'])
        if unit['fixed']:pass  # Includes constant output-valid, fixed at L-1.
        elif unit['constant']:current[u]=0
        elif not unit['fixed'] and not computational:current[u]=earliest
        if current[u]<earliest:return None,'dependency_violation'
        if not 0<=current[u]<L:return None,'stage_out_of_range'
    result=[current[unit_of[i]] for i in range(len(nodes))]
    return result,'legal_proposal'


def placement_proposals(parent,units,mode,seen,prices):
    raw=parent['graph'];nodes=raw['nodes'];placement=parent['view']['placement'];p=parent[mode];L=p['L']
    responses={r['node']:r for r in response_receipt(parent,prices)} if mode=='model' else {}
    # Attribute each owner's contribution to its native members for proposing
    # moves. G will be rediscovered after materialization, before real scoring.
    contribution={};area_response={}
    regions={r['root']:r['members'] for r in parent['owners']['G_regions']}
    for r in p['owners']:
        members=regions.get(r['node'],[r['node']]);share=r['delay_ps']/len(members)
        for n in members:
            contribution[n]=share
            area_response[n]=responses.get(r['node'],{}).get('area_response',0.)/len(members)
    rejected=Counter();rows=[]
    for i,u in enumerate(units):
        if u['fixed'] or u['constant'] or not any(nodes[n]['operation'] not in TRANSPARENT and not nodes[n]['constant'] for n in u['members']):continue
        for direction in (-1,1):
            stages,reason=canonical_move(raw,units,placement,i,direction,L)
            if stages is None:rejected[reason]+=1;continue
            identity=sha(canonical(stages))
            if identity in seen:rejected['already_seen']+=1;continue
            est=[s['comb_delay_ps'] for s in p['stages']];old=placement[u['members'][0]];new=old+direction
            weight=sum(contribution.get(n,0.) for n in u['members'])
            est[old]=max(0.,est[old]-weight);est[new]+=weight
            required=max(p['port_required_ps'],*(d+s['boundary_ps']+p['S']['reserve_ps'] for d,s in zip(est,p['stages'])))
            area_delta=sum(area_response.get(n,0.) for n in u['members'])
            # Prefer moving from a more pressured stage when the bound ties.
            balance=p['stages'][old]['required_ps']-p['stages'][new]['required_ps']
            rank=(max(0.,required-p['target_ps']),required,area_delta,-balance,i,direction)
            rows.append(dict(parent=parent['id'],placement=stages,placement_sha256=identity,
                unit=i,label=u['label'],members=u['members'],from_stage=old,to_stage=new,
                estimated_required_ps=required,area_response=area_delta,rank_key=rank,
                reason='full-stage pressure with shared-response area sensitivity; approximate proposal only'))
    return sorted(rows,key=lambda r:r['rank_key']),dict(rejected)


class Experiment:
    def __init__(self,root,binary=BINARY):
        self.root=Path(root).resolve();self.binary=Path(binary).resolve()
        self.protocol=read(self.root/'protocol.json');self.policy=self.protocol['search']
        self.out=self.root/'search';self.out.mkdir(exist_ok=False)
        compressed(self.out/'input-source.json.gz',{str(p.relative_to(ROOT)):p.read_text()
            for p in sorted((ROOT/'experiments/arithmetic_dse').glob('*.py'))})
        write(self.out/'execution-inputs.json',dict(protocol_sha256=sha((self.root/'protocol.json').read_bytes()),
            model_sha256=sha((BASE/'diagnostic-model.json').read_bytes()),
            contract_sha256=sha((BASE/'characterization-contract.json').read_bytes()),
            source_sha256=sha((self.out/'input-source.json.gz').read_bytes()),
            compiler_sha256=sha(self.binary.read_bytes()),EDA_calls=0))
        self.prices=DiagnosticPrices(read(BASE/'diagnostic-model.json'));self.contract=read(BASE/'characterization-contract.json')
        self.bindings=binding();self.native_prices=Prices(self.bindings)
        self.spec=read(self.root/'source/semantics.json')
        self.native={};self.rows=[];self.events=[];self.simulations={};self.units={};self.score_count=0
        self.noeda=self.out/'no-eda-bin';self.noeda.mkdir();self.marker=self.out/'backend-attempt'
        for name in ('yosys','abc','yosys-abc','openroad','opensta','sta'):
            p=self.noeda/name;p.write_text('#!/bin/sh\nprintf forbidden > '+shlex.quote(str(self.marker))+'\nexit 97\n');p.chmod(0o755)
        self.env=dict(os.environ,PATH=str(self.noeda)+os.pathsep+os.environ['PATH'])

    def export(self,target,grammar,*,placements=None):
        block,limb=grammar;key=(target,block,limb,sha(canonical(placements)) if placements else 'beam')
        if key in self.native:return self.native[key]
        name=f'T{target}-mul{block}-limb{limb}-'+(key[-1][:12] if placements else 'beam')
        path=self.out/'native'/name;path.parent.mkdir(exist_ok=True)
        cmd=[self.binary,ROOT,self.root/'source/request.json',3,limb,4,100000,path,block,target,'owned',self.root/'model-bindings.json']
        if placements:
            initial=self.export(target,grammar)
            request=path.with_suffix('.placements.json')
            write(request,dict(version='workload-explicit-schedules-v1',L=3,T_clk_ps=target,
                graph_export_sha256=sha((initial/'graph.json').read_bytes()),placements=placements))
            cmd.append(request)
        command(cmd,path.with_suffix('.log'),self.env,timeout=180)
        self.native[key]=path
        return path

    def check_simulation(self,path,view,graph):
        checks=verify_plan(path,view,graph,self.bindings,
            predictor=lambda owner,ops,regions,diag:self.native_prices.owner(owner,ops,regions,diag))
        dest=path/view['directory'];rtl=(dest/'workload.sv').read_bytes();identity=sha(rtl)
        tb,expected_checks=bench(self.spec,view['artifact'],3,cycles=192);(dest/'tb.sv').write_text(tb)
        if identity not in self.simulations:
            with tempfile.TemporaryDirectory(prefix='vulsim-guided-sim-') as tmp:
                sim=Path(tmp)/'sim.vvp'
                command(['iverilog','-g2012','-s','tb','-o',sim,dest/'workload.sv',dest/'tb.sv'],dest/'iverilog.log',self.env)
                output=command(['vvp',sim],dest/'simulation.log',self.env)
            if 'PASS' not in output:raise ValueError('new RTL simulation lacks PASS')
            self.simulations[identity]=dict(rtl_sha256=identity,testbench_sha256=sha(tb.encode()),
                log_sha256=sha((dest/'simulation.log').read_bytes()),directory=str(dest.relative_to(self.root)),
                cycles=192,integer_cycle_checks=expected_checks,status='fresh_integer_cycle_reset_stall_PASS')
        receipt=self.simulations[identity]
        if receipt['testbench_sha256']!=sha(tb.encode()):raise ValueError('same RTL different functional protocol')
        write(dest/'functional-receipt.json',dict(receipt,checks=dict(checks),
            reused_by_exact_RTL_hash=receipt['directory']!=str(dest.relative_to(self.root))))
        return dict(checks)

    def score(self,target,grammar,path,view,*,origin,seed_result=None,structure=None):
        raw=read(path/'graph.json');graph=Graph(raw);dest=path/view['directory']
        state=read(dest/'state.json');owners=read(dest/'owners.json')
        ident=sha(canonical(dict(graph=raw,placement=view['placement'],target=target)))
        old=next((r for r in self.rows if r['id']==ident),None)
        if old:return old
        check=self.check_simulation(path,view,graph)
        result=seed_result or optimize(graph,view,state,owners,self.prices,self.contract)
        static=evaluate(graph,view,state,owners,self.prices,static_cal=True)
        if result['status']!='diagnostic_complete':raise ValueError('new candidate uncovered; preserve and diagnose')
        write(dest/'equivalent-requests.json',dict(T_clk_ps=target,best_variant_id=result['best_variant_id'],
            budget=selected_variant(result)[0]['budgets_ps'],queries=selected_variant(result)[1]['actual_queries']))
        row=dict(id=ident,structure=structure if structure is not None else 10+grammar[0]*3+[0,16,32].index(grammar[1]),
            grammar=list(grammar),target_ps=target,origin=origin,path=str(path.relative_to(self.root)),view=view,
            graph=raw,state=state,owners=owners,result=result,model=result['prediction'],static=static,
            rtl_sha256=sha((dest/'workload.sv').read_bytes()),functional_checks=check)
        compressed(self.out/'scores'/f'{ident}.json.gz',row)
        self.rows.append(row);self.score_count+=1
        print(f'T{target} {origin} mul{grammar[0]} limb{grammar[1]} view{view["directory"]}: '
            f'{row["model"]["critical_required_ps"]:.3f} ps, {row["model"]["total_area_um2"]:.3f} um2',flush=True)
        Graph.origins.cache_clear();Graph.roots.cache_clear()
        return row

    def seeds(self,target):
        rows=[]
        for number in range(4):
            members=old_structure('mac32',number);inventory=json.loads(members['inventory.json'])
            block=inventory['mul_block_width'];grammar=(block,0)
            original_views=inventory['views']
            path=self.export(target,grammar,placements=[v['placement'] for v in original_views])
            if (path/'graph.json').read_bytes()!=members['graph.json']:
                raise ValueError('native seed graph changed')
            for view,original in zip(read(path/'inventory.json')['views'],original_views):
                dest=path/view['directory'];directory=original['directory']
                if (dest/'workload.sv').read_bytes()!=members[directory+'/workload.sv']:
                    raise ValueError('native explicit seed RTL changed')
                expected=retarget(json.loads(members[directory+'/owners.json']),target)
                state=json.loads(members[directory+'/state.json']);state['features']['sdc_period_ps']=target
                if read(dest/'owners.json')!=expected or read(dest/'state.json')!=state:
                    raise ValueError('native regenerated seed state/owners changed')
                result=read(BASE/f'run/T{target}-L3/structure-{number}-view-{directory}.json.gz')
                row=self.score(target,grammar,path,view,origin='fixed_seed',seed_result=result,structure=number)
                rows.append(row)
        return rows

    def units_for(self,target,grammar):
        key=(target,*grammar)
        if key not in self.units:
            path=self.export(target,grammar)
            self.units[key]=read(path/'scheduling-units.json')['units']
        return self.units[key]

    def run_target(self,target):
        seeds=self.seeds(target);by_mode={};policy=self.policy
        for mode in ('model','static'):
            available=list(seeds);seen={tuple(r['grammar']) for r in available}
            for credit in range(policy['structure_credits_per_strategy_per_target']):
                parent=best(available,mode)
                proposals=structural_proposals(parent,mode,self.prices,policy,seen)
                if not proposals:
                    self.events.append(dict(target=target,strategy=mode,phase='structure',stop='no_novel_grammar',credit=credit));break
                proposal=proposals[0];grammar=tuple(proposal['grammar']);seen.add(grammar)
                path=self.export(target,grammar);inventory=read(path/'inventory.json');added=[]
                for view in inventory['views']:
                    row=self.score(target,grammar,path,view,origin=f'{mode}_structure');available.append(row);added.append(row['id'])
                self.events.append(dict(target=target,strategy=mode,phase='structure',credit=credit,
                    proposal=proposal,considered=proposals,added=added))
            seen_placements={}
            for row in available:seen_placements.setdefault(tuple(row['grammar']),set()).add(sha(canonical(row['view']['placement'])))
            credits=0
            for round_index in range(policy['position_rounds']):
                # Expand best parents across structures; duplicate estimates
                # for the same graph/map are discarded before native export.
                parents=sorted(available,key=lambda r:best_key(r,mode))
                proposals=[];rejections=Counter()
                for parent in parents:
                    grammar=tuple(parent['grammar']);units=self.units_for(target,grammar)
                    probe=self.export(target,grammar)
                    if read(probe/'graph.json')!=parent['graph']:raise ValueError('native probe/parent graph mismatch')
                    options,rejected=placement_proposals(parent,units,mode,seen_placements[grammar],self.prices)
                    proposals.extend(dict(p,grammar=list(grammar)) for p in options)
                    rejections.update(rejected)
                proposals.sort(key=lambda r:(r['rank_key'],r['grammar'],r['parent']))
                chosen=[];unique=set()
                for proposal in proposals:
                    key=(tuple(proposal['grammar']),proposal['placement_sha256'])
                    if key in unique:continue
                    unique.add(key);chosen.append(proposal)
                    if len(chosen)>=policy['moves_per_round']:break
                self.events.append(dict(target=target,strategy=mode,phase='placement',round=round_index,
                    considered_legal=len(unique) if not proposals else len(proposals),rejections=dict(rejections),chosen=chosen,
                    stop='credit_round' if chosen else 'no_legal_novel_proposal'))
                if not chosen:break
                for proposal in chosen:
                    grammar=tuple(proposal['grammar']);seen_placements[grammar].add(proposal['placement_sha256'])
                    path=self.export(target,grammar,placements=[proposal['placement']]);view=read(path/'inventory.json')['views'][0]
                    row=self.score(target,grammar,path,view,origin=f'{mode}_placement')
                    available.append(row);credits+=1
            winner=best(available,mode)
            by_mode[mode]=dict(candidate_ids=sorted({r['id'] for r in available}),selected_id=winner['id'],
                selection=compact_prediction(winner[mode]),structure_credits=sum(e['phase']=='structure' and 'added' in e
                    for e in self.events if e['target']==target and e['strategy']==mode),placement_credits=credits)
        common=[r for r in self.rows if r['target_ps']==target]
        comparisons={}
        for name,rs in [('fixed',seeds),('common_generated_pool',common)]:
            comparisons[name]={mode:dict(selected_id=best(rs,mode)['id'],grammar=best(rs,mode)['grammar'],
                selection=compact_prediction(best(rs,mode)[mode])) for mode in ('model','static')}
        model_winner=next(r for r in common if r['id']==by_mode['model']['selected_id'])
        selected=self.out/f'T{target}-selected';selected.mkdir()
        source=self.root/model_winner['path']/model_winner['view']['directory']
        for name in ('workload.sv','tb.sv','state.json','owners.json','equivalent-requests.json','functional-receipt.json'):
            shutil.copyfile(source/name,selected/name)
        write(selected/'graph.json',model_winner['graph'])
        e,v=selected_variant(model_winner['result'])
        write(selected/'identity.json',dict(candidate_id=model_winner['id'],T_clk_ps=target,L=3,II=1,
            grammar=model_winner['grammar'],RTL_sha256=model_winner['rtl_sha256'],
            graph_sha256=sha(canonical(model_winner['graph'])),state_sha256=sha(canonical(model_winner['state'])),
            owner_plan_sha256=sha(canonical(model_winner['owners'])),budget_sha256=e['budget_sha256'],
            equivalent_queries_sha256=v['owner_queries_sha256'],
            model_sha256=sha((BASE/'diagnostic-model.json').read_bytes()),
            contract_sha256=sha((BASE/'characterization-contract.json').read_bytes()),
            protocol_sha256=sha((self.root/'protocol.json').read_bytes()),
            compiler_sha256=sha(self.binary.read_bytes()),qualified=False,
            actual_implementation='whole-design global T; no local ABC constraint applied'))
        return dict(T_clk_ps=target,strategies=by_mode,comparisons=comparisons,
            unique_candidates=len(common),model_selected_grammar=model_winner['grammar'])

    def run(self):
        targets=[self.run_target(t) for t in self.policy['targets_ps']]
        if self.marker.exists():raise ValueError('forbidden EDA startup attempted')
        write(self.out/'search-events.json',self.events)
        compressed(self.out/'response-receipts.json.gz',[dict(candidate_id=r['id'],response=response_receipt(r,self.prices))
            for r in self.rows if r['origin']!='fixed_seed'])
        report=dict(status='step5_software_search_complete_diagnostic_only',qualified=False,targets=targets,
            unique_candidates=len(self.rows),new_candidates=sum(r['origin']!='fixed_seed' for r in self.rows),
            unique_RTL_freshly_simulated=len(self.simulations),simulations=list(self.simulations.values()),
            native_plan_verified=True,fresh_cycles_per_unique_RTL=192,EDA_calls=0,EDA_sentinel_attempts=0,
            model_response_refits=0,global_optimum_claimed=False,ABCD_physical_comparison_complete=False,
            old_queue_resumed=False,static_control='same complete scorer + frozen train-only static bridge; attribution control, not final C')
        write(self.out/'summary.json',report)
        # Portable numerical replay needs only exact compiler artifacts and
        # frozen model/contract, with no native execution or external labels.
        compressed(self.root/'search-replay-inputs.json.gz',dict(rows=self.rows,model=read(BASE/'diagnostic-model.json'),
            contract=self.contract,protocol=self.protocol,events=self.events,targets=targets))
        write(self.out/'manifest.json',dict(protocol_sha256=sha((self.root/'protocol.json').read_bytes()),
            compiler_sha256=sha(self.binary.read_bytes()),compiler_source_sha256=sha((ROOT/'rtlzz/main/arithmetic_workload.cpp').read_bytes()),
            replay_inputs_sha256=sha((self.root/'search-replay-inputs.json.gz').read_bytes()),
            files={str(p.relative_to(self.out)):sha(p.read_bytes()) for p in sorted(self.out.rglob('*')) if p.is_file()}))
        return report


def replay(root=DEFAULT):
    from .workload_steps45_package import replay_data,artifact_files
    root=Path(root);data,input_identity=replay_data(root);prices=DiagnosticPrices(data['model'])
    manifest=read(root/'search/manifest.json')
    if input_identity!=manifest['replay_inputs_sha256']:
        raise ValueError('search input identity changed')
    files=artifact_files(root,data['rows'])
    for name,expected in manifest['files'].items():
        if sha(files[name])!=expected:raise ValueError('native/result artifact changed: '+name)
    counts=Counter()
    for row in data['rows']:
        graph=Graph(row['graph']);result=optimize(graph,row['view'],row['state'],row['owners'],prices,data['contract'])
        # Seed snapshots additionally carry the old steps1-3 outer identity;
        # all numerical traces and best choices must still reproduce exactly.
        expected={k:v for k,v in row['result'].items() if k!='identity'}
        if canonical(result)!=canonical(expected):raise ValueError('full equivalent trace differs '+row['id'])
        static=evaluate(graph,row['view'],row['state'],row['owners'],prices,static_cal=True)
        if canonical(static)!=canonical(row['static']):raise ValueError('static complete score differs')
        counts['candidates']+=1;counts['complete_variants']+=result['complete_variants']
        Graph.origins.cache_clear();Graph.roots.cache_clear()
    return dict(status='all_candidate_traces_and_static_prices_reproduced',counts=dict(counts),
        EDA_calls=0,external_artifacts_needed=False,native_processes_needed=False)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['run','replay']);p.add_argument('--root',type=Path,default=DEFAULT)
    args=p.parse_args();print(json.dumps(Experiment(args.root).run() if args.action=='run' else replay(args.root),indent=2))
