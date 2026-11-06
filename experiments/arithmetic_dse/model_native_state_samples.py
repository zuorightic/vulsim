"""Prospective synthetic banks matching native previous-stage-valid semantics."""
from .model_m2_state_samples import reset_value

VERSION='native-state-bank-contract-v1'


def specifications(cfg):
    result=[]
    for index,w in enumerate(cfg['word_widths']):
        result.append(dict(id=f'native-state-train-small-w{w}',split='train',maximum=w,stages=2,
            reset_pattern='zero',words=[word(w,0,index,2,False)]))
    for index,w in enumerate(cfg['large_train_widths']):
        count=min(cfg['max_parallel_words'],608//w,(cfg['max_state_bits']-3)//(3*w))
        result.append(dict(id=f'native-state-train-large-w{w}',split='train',maximum=w,stages=3,
            reset_pattern='one',words=packing(cfg,w,count,index,3,index%2==1)))
    for split,count,phase,pattern in (('validation',6,3,'alternating'),('test',7,8,'one_in_three')):
        for index,w in enumerate(cfg['validation_test_widths']):
            stages=2+(index+phase)%2
            result.append(dict(id=f'native-state-{split}-w{w}',split=split,maximum=w,stages=stages,
                reset_pattern=pattern,words=packing(cfg,w,count,index+phase,stages,True)))
    for spec in result:
        spec['slots']=[]
        for j,entry in enumerate(spec['words']):
            for stage in range(entry['start'],entry['end']+1):
                v=entry['variable_mask'].bit_count()
                spec['slots'].append({'name':f'dst{stage}_{j}','word':j,'stage':stage,
                    'declared_width':entry['declared_width'],'variable_mask':entry['variable_mask'],
                    'variable_bits':v,'enable_stage':stage-1,
                    'reset_variable':reset_value(v,spec['reset_pattern'],j,stage)})
        spec['input_bits']=1+sum(w['variable_mask'].bit_count() for w in spec['words'])
        spec['features']=features(spec,1500)
        for key,value in [('max_input_bits',spec['input_bits']),('max_capture_bits',spec['features']['state_bits']),
                          ('max_state_bits',spec['features']['state_bits']),('max_state_signals',spec['features']['state_signals'])]:
            if value>cfg[key]:raise ValueError('native state geometry exceeds '+key)
    if len(result)!=48:raise ValueError('native state source count differs')
    return result


def word(width,index,phase,stages,mixed):
    mask=(1<<width)-1
    if width>1 and (index+phase)%3==1:mask^=1<<(width-1)
    elif width>1 and (index+phase)%3==2:mask^=1<<((3*width//5+phase)%width)
    start=1 if index==0 or not mixed else 1+(index+phase)%stages
    end=stages if index==0 or not mixed else start+(phase+2*index)%(stages-start+1)
    return {'declared_width':width,'variable_mask':mask,'start':start,'end':end}


def packing(cfg,maximum,count,phase,stages,mixed):
    palette=[w for w in cfg['word_widths'] if w<=maximum]
    result=[]
    for j in range(count):
        width=maximum if j==0 or not mixed else palette[(phase+3*j)%len(palette)]
        if mixed and maximum>=5 and j==1:width=5
        entry=word(width,j,phase,stages,mixed)
        if width==5 and j==1:entry['variable_mask']=0x17
        if width==65 and j==0:entry['variable_mask']=(1<<64)-1
        result.append(entry)
    return result


def features(spec,period):
    slots=spec['slots'];data=sum(s['variable_bits'] for s in slots);valid=spec['stages']
    return dict(state_bits=data+valid,state_signals=len(slots)+valid,data_bits=data,data_signals=len(slots),
        valid_bits=valid,valid_signals=valid,enable_domains=len({s['enable_stage'] for s in slots}),
        reset_one_bits=sum(s['reset_variable'].bit_count() for s in slots),
        max_declared_width=max(s['declared_width'] for s in slots),min_variable_width=min(s['variable_bits'] for s in slots),
        sdc_period_ps=period)


def ports(name,width):
    return 'input wire '+(f'[{width-1}:0] ' if width>1 else '')+name


def source(spec):
    inputs=['input wire clk,rstn,iv']+[ports('in'+str(j),w['variable_mask'].bit_count()) for j,w in enumerate(spec['words'])]
    text=['(* keep_hierarchy=1 *) module StateBank('+','.join(inputs+['output wire y,ov'])+');']
    for stage in range(1,spec['stages']+1):
        previous='iv' if stage==1 else 'valid_q'+str(stage-1)
        text += [f'(* keep *) reg valid_q{stage};',f'always @(posedge clk) if(!rstn)valid_q{stage}<=0;else valid_q{stage}<={previous};']
    for slot in spec['slots']:
        j,stage,v,name=slot['word'],slot['stage'],slot['variable_bits'],slot['name']
        previous=f'in{j}' if stage==spec['words'][j]['start'] else f'dst{stage-1}_{j}'
        enable='iv' if stage==1 else f'valid_q{stage-1}'
        text += [f'(* keep *) reg [{v-1}:0] {name};',
            f'always @(posedge clk) if(!rstn){name}<={v}\'h{slot["reset_variable"]:x};else if({enable}){name}<={previous};']
    # Explicit declared-width padding/hole wires retain semantic geometry.
    observed=[]
    for j,w in enumerate(spec['words']):
        k=0;bits=[]
        for bit in range(w['declared_width']):
            bits.append(f'dst{w["end"]}_{j}[{k}]' if w['variable_mask']>>bit&1 else "1'b0")
            k+=bool(w['variable_mask']>>bit&1)
        text.append(f'wire [{w["declared_width"]-1}:0] logical{j}={{{",".join(reversed(bits))}}};')
        observed.append('logical'+str(j))
    width=sum(w['declared_width'] for w in spec['words'])
    text += [f'assign ov=valid_q{spec["stages"]};',
        'StateObserver observer(.value({'+','.join(reversed(observed))+'}),.y(y));','endmodule',
        f'(* keep_hierarchy=1 *) module StateObserver(input wire [{width-1}:0] value,output wire y);assign y=^value;endmodule']
    connections=['.clk(clk)','.rstn(rstn)','.iv(iv)','.y(y)','.ov(ov)']+[f'.in{j}(in{j})' for j in range(len(spec['words']))]
    text += ['module ModelBundle('+','.join(inputs+['output wire y,ov'])+');StateBank bank('+','.join(connections)+');endmodule']
    return '\n'.join(text)+'\n'


def step(spec,old,inputs,reset):
    result={}
    for slot in spec['slots']:
        stage,j=slot['stage'],slot['word'];enable=inputs['iv'] if stage==1 else old[f'valid_q{stage-1}']
        previous=inputs[f'in{j}'] if stage==spec['words'][j]['start'] else old[f'dst{stage-1}_{j}']
        result[slot['name']]=slot['reset_variable'] if reset else previous if enable else old[slot['name']]
    for stage in range(1,spec['stages']+1):
        result[f'valid_q{stage}']=0 if reset else inputs['iv'] if stage==1 else old[f'valid_q{stage-1}']
    return result
