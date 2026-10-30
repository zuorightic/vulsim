#!/usr/bin/env python3
"""Revised step-two executable contracts; no physical data or model training."""
from copy import deepcopy
from fractions import Fraction
import json
import os
from pathlib import Path
import random
import sys
import subprocess
import tempfile
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.arithmetic_dse import fixed_cost
from experiments.arithmetic_dse.contracts import (ContractError, PLATFORMS, WIDTHS,
    case_manifest, check_partition, fixed_latency, freeze_target_batch,
    semantic_profile, target_period_ps, template_parameters)
from experiments.arithmetic_dse.case_generator import (Builder, build_graph, case_spec,
    evaluate_graph, generate_manifest, graph_signatures, source_files, validation_vectors)
from experiments.arithmetic_dse.fixed_cost import (Cost, candidate_score, graph_cost,
    lower_lookup, lower_priority_case, node_cost, state_cost)
from experiments.arithmetic_dse.reference import (FPResult, evaluate_case, evaluate_spec,
    f32_chain, f32_mul, logical_shift, udivrem)
checks = 0
def check(condition, message='contract assertion'):
    global checks
    checks += 1
    if not condition: raise AssertionError(message)
def rejects(function, code=None):
    try: function()
    except ValueError as error:
        check(code is None or isinstance(error,ContractError) and error.code == code,
              f'wrong rejection: {error!r}; expected {code}')
    else: raise AssertionError('expected rejection')
manifest = case_manifest()
check(manifest == generate_manifest())
partition = check_partition(manifest)
check((partition['formal'],partition['holdout'],partition['records_per_platform'],partition['all_platform_records']) == (32,11,172,688))
for case in manifest['cases']:
    check(fixed_latency(case) == (3 if case['family'] in ('H_D','F2') else 2))
bad = deepcopy(manifest); bad['cases'][0]['inputs']['a'] = 7
rejects(lambda: check_partition(bad),'invalid_case_manifest')
rejects(lambda: check_partition({**manifest,'cases':manifest['cases'][:-1]}),'invalid_case_manifest')
for w in WIDTHS:
    check(semantic_profile({'kind':'unsigned_integer','width':w})['width'] == w)
    for mode in ('full','truncated'):
        for block in (None,w//2,w//4):
            p = {'operation':'Mul','W':w,'R':2*w if mode=='full' else w,'block_width':block,'product':mode}
            check(template_parameters(p)['R'] == p['R'])
check(semantic_profile({'kind':'binary32_mul_rne'})['flags_width'] == 5)
for request in ({'kind':'unsigned_integer','width':32,'signed':True},
                {'kind':'unsigned_integer','width':32,'fraction_bits':8},
                {'kind':'unsigned_integer','width':True},{'kind':'fixed_point','width':16},
                {'kind':'binary32_mul_rne','rounding':'toward_zero'}):
    rejects(lambda request=request: semantic_profile(request),'unsupported_semantic_profile')
for request in ({'operation':'Mul','W':32,'R':32,'product':'full'},
                {'operation':'Mul','W':32,'R':64,'block_width':1},
                {'operation':'Mul','W':256,'R':512},{'operation':'Mul','W':32,'R':64,'L':2}):
    rejects(lambda request=request: template_parameters(request),'template_ineligible')
small = case_spec('MUL',8)
for a in range(256):
    for b in range(256):
        product = sum(a << bit for bit in range(8) if b >> bit & 1)
        check(evaluate_spec(small,{'a':a,'b':b}) == {'y':product})
        safe = b if b else 1
        qr = (a//safe,a % safe) if b else (255,a)
        check(udivrem(a,b,8) == qr)
        check(b == 0 or qr[0]*b+qr[1] == a and 0 <= qr[1] < b)
shift_checks = 0
for w in WIDTHS:
    for a in (0,1,(1 << w)-1,1 << (w-1),(1 << w)-2):
        for s in range(2*w+2):
            safe = s if s < w else 0
            check(logical_shift(a,s,w) == ((a << safe) & ((1 << w)-1) if s < w else 0))
            check(logical_shift(a,s,w,right=True) == (a >> safe if s < w else 0))
            shift_checks += 2
rejects(lambda: logical_shift(1,-1,8)); rejects(lambda: logical_shift(256,0,8))
case_evaluations = nonpower_evaluations = 0
for case in manifest['cases']:
    graph = build_graph(case['family'],case['width'])
    check(graph_signatures(graph) == (case['inputs'],case['outputs']))
    check(set(source_files(case)) == {'header.uh','Case.vul','graph.json'})
    for inputs in validation_vectors(case):
        expected = evaluate_spec(case,inputs)
        check(evaluate_graph(graph,inputs) == expected,(case['id'],inputs,expected))
        case_evaluations += 1
    rejects(lambda case=case: evaluate_spec(case,{}))
    if case['width'] is not None: check(graph_cost(graph)['delay_weight'] > 0)
    else: rejects(lambda graph=graph: graph_cost(graph),'cost_uncovered')
check(evaluate_case('DOT2_128',{x:(1 << 128)-1 for x in ('a','b','c','d')})['y'] >> 256 == 1)
check(evaluate_case('MAC_128',{'a':(1 << 128)-1,'b':(1 << 128)-1,'c':(1 << 256)-1})['y'] == (1 << 256)-(1 << 129))
check(evaluate_case('H_D_128',{'a':123,'d':0,'e':0}) == {'q':(1 << 128)-1,'r1':123,'r2':(1 << 128)-1})
for width in (12,24,48,96):
    for family in ('MUL','MAC','DOT2','UDR','DIVSEL','MIX','H_M','H_D'):
        case = case_spec(family,width); graph = build_graph(family,width)
        for inputs in validation_vectors(case,random_count=16):
            check(evaluate_graph(graph,inputs) == evaluate_spec(case,inputs)); nonpower_evaluations += 1
        check('Case.vul' in source_files(case))
fp_vectors = [(0x3f800000,0x40000000,0x40000000,0),(0x80000000,0x40000000,0x80000000,0),
              (0,0x7f800000,0x7fc00000,16),(0x7f812345,0x3f800000,0x7fc00000,16),
              (0x7fc12345,0x3f800000,0x7fc00000,0),(0x7f7fffff,0x40000000,0x7f800000,5),
              (1,0x3f000000,0,3),(3,0x3f000000,2,3),(0x00800000,0x3f7fffff,0x00800000,3)]
for a,b,bits,flags in fp_vectors: check(f32_mul(a,b) == FPResult(bits,flags))
check(f32_chain(0x7f7fffff,0x40000000,0) == FPResult(0x7fc00000,21))
check(evaluate_case('H_F1',{'a':0,'b':0x7f800000,'bypass':0x7f812345,'select':0}) == {'bits':0x7f812345,'flags':0})
rejects(lambda: evaluate_case('M1',{'a':1,'b':1,'c':0}))
softfloat_details = None
if os.environ.get('ARITHMETIC_SOFTFLOAT_DIR'):
    from experiments.arithmetic_dse.softfloat_oracle import SoftFloatOracle
    with tempfile.TemporaryDirectory(prefix='revised-softfloat-') as directory:
        oracle = SoftFloatOracle(Path(os.environ['ARITHMETIC_SOFTFLOAT_DIR']),Path(directory)/'oracle.so')
        rng = random.Random(730021)
        edges = [0,0x80000000,1,3,0x007fffff,0x00800000,0x3f000000,0x3f7fffff,
                 0x3f800000,0x3f800001,0x40000000,0x7f7fffff,0xff7fffff,
                 0x7f800000,0xff800000,0x7fc00000,0x7f812345,0xff812345]
        pairs = [(a,b) for a in edges for b in edges]
        pairs += [(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(20000)]
        for a,b in pairs:
            fp = f32_mul(a,b)
            check((fp.bits,fp.flags) == oracle.multiply(a,b),'SoftFloat mismatch')
        softfloat_details = {'vectors':len(pairs),'source_sha256':oracle.source_hashes,
                             'build_command':oracle.command}
for width,mul,div in [(1,1,2),(2,1,4),(4,2,8),(8,4,16),(16,8,32),(32,16,64),(64,32,128),(128,64,256)]:
    check(node_cost('Mul',[width,width],2*width) == Cost(mul,mul))
    for op in ('Div','Mod'): check(node_cost(op,[width,width],width) == Cost(div,div))
    check(node_cost('Mul',[width,width],width) == node_cost('Mul',[width,width],2*width))
    check(node_cost('Mul',[width,width],2*width,diagnostic_square_mul=True).comb_weight == Fraction(width*width,64))
for op,widths,result,expected in [('Mul',[12,24],48,Cost(16,16)),('Add',[256,256],257,Cost(1,1)),
        ('AddCarry',[256,256,1],257,Cost(1,1)),('ReduceXor',[257],1,Cost(1,1)),
        ('Shl',[128,9],128,Cost(2,2)),('Concat',[128,128],256,Cost(0,0))]:
    check(node_cost(op,widths,result) == expected)
check(node_cost('Shl',[128,9],128,constant_shift=True) == Cost(0,0))
rejects(lambda: node_cost('Mul',[129,1],130),'cost_uncovered')
rejects(lambda: node_cost('ExternalIP',[],1,transaction_constant=True),'cost_uncovered')
rejects(lambda: node_cost('Lookup',[8]*8,8),'cost_uncovered')
with tempfile.TemporaryDirectory(prefix='fixed-fields-') as directory:
    config = json.loads(fixed_cost.CONFIG.read_text())
    config['operations']['Mul']['delay_weight']['32'] = 7
    config['operations']['Mul']['comb_weight']['32'] = 11
    p = Path(directory)/'weights.json'; p.write_text(json.dumps(config))
    with patch.object(fixed_cost,'CONFIG',p): check(node_cost('Mul',[32,32],64) == Cost(7,11))
b = Builder(); a,x = b.input('a',32),b.input('b',32)
ea,ex = b.node('ea','ZExt',64,a),b.node('ex','ZExt',64,x)
p = b.node('p','Mul',64,ea,ex); graph = {'nodes':b.nodes,'outputs':{'y':p}}
check(graph_cost(graph)['node_costs']['p'] == Cost(16,16))
check(graph_cost(graph)['width_audit']['p']['billing_widths'] == [32,32])
dot = graph_cost(build_graph('DOT2',32)); check(dot['delay_weight'] == 17 and dot['comb_weight'] == 33)
b = Builder(); a,x = b.input('a',32),b.input('b',32)
p = b.node('p','Mul',64,a,x); y = b.node('y','Add',64,p,p)
check(graph_cost({'nodes':b.nodes,'outputs':{'y':y}})['comb_weight'] == 17)
b = Builder(); a,d = b.input('a',16),b.input('d',16)
q,r = b.node('q','Div',16,a,d),b.node('r','Mod',16,a,d); graph = {'nodes':b.nodes,'outputs':{'q':q,'r':r}}
check(graph_cost(graph)['comb_weight'] == 64)
receipt = {'implementation_id':'verified-qr','members':[q,r],'proof_ref':'implementation-receipt'}
check(graph_cost(graph,verified_shared_divrem=[receipt])['comb_weight'] == 32)
rejects(lambda: graph_cost(graph,verified_shared_divrem=[{**receipt,'proof_ref':None}]),'invalid_expansion_graph')
b = Builder(); index = b.input('index',3); entries = [b.input('e'+str(i),8) for i in range(8)]
y = lower_lookup(b,'lut',index,entries,8); graph = {'nodes':b.nodes,'outputs':{'y':y}}
check(graph_cost(graph)['delay_weight'] == 3 and graph_cost(graph)['comb_weight'] == 7)
for i in range(8): check(evaluate_graph(graph,{'index':i,**{'e'+str(n):17+n for n in range(8)}}) == {'y':17+i})
rejects(lambda: lower_lookup(b,'bad',index,entries[:6],8),'template_ineligible')
b = Builder(); index = b.input('index',1); entries = [b.input('e'+str(i),8) for i in range(8)]
y = lower_lookup(b,'lut',index,entries,8); check(graph_cost({'nodes':b.nodes,'outputs':{'y':y}})['comb_weight'] == 1)
b = Builder(); c0,c1 = b.input('c0',1),b.input('c1',1); a,x,d = b.input('a',8),b.input('b',8),b.input('d',8)
y = lower_priority_case(b,'case',[(c0,a),(c1,x)],d,8); graph = {'nodes':b.nodes,'outputs':{'y':y}}
check(evaluate_graph(graph,{'c0':1,'c1':1,'a':11,'b':22,'d':33}) == {'y':11})
check(graph_cost(graph)['delay_weight'] == 2 and graph_cost(graph)['comb_weight'] == 2)
check(state_cost([{'source':'p','width':257,'producer_stage':0,'last_consumer_stage':2}],valid_boundaries=2)
      == {'register_bits':516,'register_signals':4,'state_weight':516})
rejects(lambda: state_cost([{'source':'p','width':8,'producer_stage':0,'last_consumer_stage':1}]*2))
check(candidate_score(3,Fraction(1,64),16,2,'a') < candidate_score(3,Fraction(1,16),16,2,'b'))
cases = {c['id']:c for c in manifest['cases']}
labels = {n['primitive']:100 if n['heavy'] else 1 for c in manifest['cases'] for n in c['reference_graph'] if n['primitive']}
bundle = {'platform':'asap7','stage':'grt','source_role':'microbenchmark_only',
          'label_definition':'combinational_data_path_excluding_boundary','reference_set_id':'synthetic-formula-test-only',
          'settings_sha256':'0'*64,'delays_ps':labels}
for name,expected in [('MUL_32',95),('MAC_32',96),('DOT2_32',96),('F2',121)]:
    check(target_period_ps(cases[name],bundle,20,platform='asap7') == expected)
for platform in PLATFORMS:
    check(target_period_ps(cases['MUL_32'],{**bundle,'platform':platform},Fraction(41,2),platform=platform) == 96)
rejects(lambda: target_period_ps(cases['MUL_32'],bundle,20,platform='gf180'),'invalid_reference')
rejects(lambda: target_period_ps(cases['MUL_32'],{**bundle,'delays_ps':{}},20,platform='asap7'),'missing_reference')
rejects(lambda: target_period_ps(cases['MUL_32'],{**bundle,'source_role':'formal_case_PPA'},20,platform='asap7'),'invalid_reference')
rejects(lambda: target_period_ps(cases['MUL_32'],bundle,'nan',platform='asap7'),'invalid_reference')
rejects(lambda: target_period_ps(cases['MUL_32'],{**bundle,'settings_sha256':'unknown'},20,platform='asap7'),'invalid_reference')
targets = freeze_target_batch(manifest['cases'],bundle,{c['id']:20 for c in manifest['cases']},platform='asap7')
check(len(targets['periods_ps']) == 43 and len(targets['batch_sha256']) == 64)
rejects(lambda: freeze_target_batch(manifest['cases'],bundle,{},platform='asap7'),'invalid_reference')
bad = deepcopy(build_graph('DOT2',128)); next(n for n in bad['nodes'] if n['id']=='wide_p')['width'] = 255
rejects(lambda: graph_cost(bad),'width_contract_violation')
bad = deepcopy(build_graph('DOT2',128)); bad['nodes'][0]['deps'] = ['missing']
rejects(lambda: graph_cost(bad),'invalid_expansion_graph')
bad = deepcopy(build_graph('MUL',32)); bad['nodes'][0]['params']['signed'] = True
rejects(lambda: graph_cost(bad),'invalid_expansion_graph')
requests = [{'case':'MAC_32','inputs':{'a':3,'b':7,'c':5}},
            {'case':'DOT2_128','inputs':{name:(1 << 128)-1 for name in ('a','b','c','d')}}]
cli = subprocess.run([sys.executable,'-m','experiments.arithmetic_dse.reference'],cwd=ROOT,
                     input=''.join(json.dumps(r)+'\n' for r in requests),text=True,capture_output=True)
check(cli.returncode == 0,cli.stderr)
check([json.loads(line)['outputs'] for line in cli.stdout.splitlines()]
      == [evaluate_case(r['case'],r['inputs']) for r in requests])
report = {'status':'passed','version':'step2-revised-contracts-v1','checks':checks,'partition':partition,
          'integer_exhaustive_multiply_pairs':65536,'integer_exhaustive_division_pairs':65536,
          'safe_shift_checks':shift_checks,'case_graph_reference_evaluations':case_evaluations,
          'nonpower_width_graph_reference_evaluations':nonpower_evaluations,'nonpower_widths':[12,24,48,96],
          'fp_directed_vectors':len(fp_vectors),'target_labels':'synthetic_formula_tests_only',
          'softfloat_crosscheck':softfloat_details,
          'new_cost_mode':'fixed-op-width-v1','physical_measurements_read':False,
          'compiler_BEIR_preflight':'steps4_5','scheduling_and_actual_D_model':'later_steps',
          'cost_sensitivity':'protocol_and_exact_weights_verified; ranking_runs_in_step5'}
if os.environ.get('ARITHMETIC_REPORT'): Path(os.environ['ARITHMETIC_REPORT']).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
