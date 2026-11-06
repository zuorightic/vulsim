"""General state banks with explicit service/native/external owners and resets."""
import hashlib
import json

VERSION='general-state-bank-contract-v1'


def bits(tag,width):
    return int.from_bytes(hashlib.sha512(tag.encode()).digest(),'big')&((1<<width)-1)


def semantic_signature(s):
    value={k:s[k] for k in ('roots','service_mode','depth','words','external_words')}
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def specifications(cfg):
    result=[]
    for split,phase in [('train',0),('validation',19),('test',37)]:
        for index in range(cfg['splits'][split]['sources']):
            number=index+phase;depth=1 if index%3==0 else 2
            count=[6,8,10,12,18,9][index%6]
            widths=([64,66],[65,65],[40,41,49])[index%3]
            roots=[{'width':w,'reset':bits(f'general-S/{split}/{index}/root/{j}',w)} for j,w in enumerate(widths)]
            total=sum(widths);root_reset=sum(r['reset']<<sum(v['width'] for v in roots[:j]) for j,r in enumerate(roots))
            full=index%3==1;words=[]
            for j in range(count):
                w=cfg['word_widths'][(index*7+j)%len(cfg['word_widths'])]
                v=min(w,cfg['max_variable_word_bits']);mode=(number+j)%4
                if w==37 and j%2==0:mask=((1<<37)-1)^(1<<35);v=36
                elif w>1 and mode==1:v=min(v,w-1);mask=((1<<v)-1)<<(w-v)
                elif w>2 and mode==2:
                    v=min(v,w-1);hole=w//2;mask=sum(1<<k for k in list(range(w)) if k!=hole) & ((1<<w)-1)
                    # 65/66-bit words retain at most64 semantic variable bits.
                    selected=[k for k in range(w) if mask>>k&1][:v];mask=sum(1<<k for k in selected)
                else:mask=(1<<v)-1
                offset=(number*11+j*7)%total
                positions=[(offset+k)%total for k in range(v)]
                pattern=(number+j)%4
                reset=(0 if pattern==0 else (1<<v)-1 if pattern==1 else
                    sum(1<<k for k in range(v) if k%2==0) if pattern==2 else bits(f'general-S/{split}/{index}/word/{j}',v))
                initial=sum(((root_reset>>at)&1)<<k for k,at in enumerate(positions))
                invert=initial^reset
                if depth==1:start=end=1
                elif full and j==0:start,end=1,depth
                elif full:start=1+(number+j)%depth;end=depth if j%2 else start
                else:start=end=1+(number+j)%depth
                words.append({'declared_width':w,'variable_mask':mask,'variable_bits':v,'source_positions':positions,
                    'invert':invert,'reset':reset,'start':start,'end':end})
            terminal=[j for j,w in enumerate(words) if w['end']==depth]
            external=[];external_bits=0
            for j in terminal:
                if external_bits+words[j]['variable_bits']<=cfg['max_external_data_bits']:
                    external.append(j);external_bits+=words[j]['variable_bits']
            if not external:raise ValueError('general state requires external data')
            s={'id':f'general-state-{split}-{index:02d}','split':split,'roots':roots,'depth':depth,
               'service_mode':(index+index//3)%3,'words':words,'external_words':external}
            s['slots']=[{'name':f'data_{j}_s{stage}','word':j,'stage':stage,'variable_bits':w['variable_bits'],
                         'reset':w['reset']} for j,w in enumerate(words) for stage in range(w['start'],w['end']+1)]
            s['expected_FF_bits']={'input_service':total+1,'native_state':sum(x['variable_bits'] for x in s['slots'])+depth,
                                   'external_state':external_bits+1}
            s['features']=features(s,1500);s['semantic_signature']=semantic_signature(s)
            if total>cfg['max_input_data_bits'] or s['features']['native_data_bits']>cfg['max_native_data_bits']:
                raise ValueError('general state source exceeds preregistered capacity')
            result.append(s)
    if len({s['semantic_signature'] for s in result})!=len(result):raise ValueError('duplicate semantic source')
    return result


def features(s,period):
    slots=s['slots'];external=[s['words'][j] for j in s['external_words']]
    return {'input_data_bits':sum(r['width'] for r in s['roots']),'input_signals':len(s['roots']),
        'input_reset_one_bits':sum(r['reset'].bit_count() for r in s['roots']),
        'native_data_bits':sum(x['variable_bits'] for x in slots),'native_data_signals':len(slots),
        'native_valid_bits':s['depth'],'native_reset_one_bits':sum(x['reset'].bit_count() for x in slots),
        'external_data_bits':sum(w['variable_bits'] for w in external),'external_data_signals':len(external),
        'external_reset_one_bits':sum(w['reset'].bit_count() for w in external),
        'max_declared_width':max(w['declared_width'] for w in s['words']),
        'min_variable_width':min(w['variable_bits'] for w in s['words']),
        'data_channels':len(s['words']),'has_full_native_chain':int(any(w['start']==1 and w['end']==s['depth'] for w in s['words'])),
        'service_mode':s['service_mode'],'sdc_period_ps':period}


def source(s):
    def port(name,w):return f'input wire [{w-1}:0] {name}'
    rootports=[port('in'+str(j),r['width']) for j,r in enumerate(s['roots'])]
    enables=[f'input wire we{j}' for j in range(len(s['roots']))]+['input wire we_iv']
    topports=['input wire clk,rstn,iv',*rootports,*enables,'output wire y,ov']
    launchports=['input wire clk,rstn,iv',*rootports,*enables,'output reg valid']
    launchports += [f'output reg [{r["width"]-1}:0] data_{j}' for j,r in enumerate(s['roots'])]
    text=['(* keep_hierarchy=1 *) module GeneralLaunch('+','.join(launchports)+');']
    for j,r in enumerate(s['roots']):
        enable='we_iv' if s['service_mode']==1 else f'we{j}'
        text.append(f'always @(posedge clk)if(!rstn)data_{j}<={r["width"]}\'h{r["reset"]:x};else if({enable})data_{j}<=in{j};')
    enabled='' if s['service_mode']==2 else 'if(we_iv)'
    text += [f'always @(posedge clk)if(!rstn)valid<=0;else {enabled}valid<=iv;','endmodule']
    total=sum(r['width'] for r in s['roots'])
    adapterports=[f'input wire [{total-1}:0] roots']+[f'output wire [{w["variable_bits"]-1}:0] word{j}' for j,w in enumerate(s['words'])]
    text += ['(* keep_hierarchy=1 *) module GeneralAdapter('+','.join(adapterports)+');']
    for j,w in enumerate(s['words']):
        mapping=','.join(f'roots[{at}]' for at in reversed(w['source_positions']))
        text.append(f'assign word{j}={{{mapping}}}^{w["variable_bits"]}\'h{w["invert"]:x};')
    text += ['endmodule']
    nativeports=['input wire clk,rstn,iv']+[port('word'+str(j),w['variable_bits']) for j,w in enumerate(s['words'])]
    nativeports += [f'output reg [{x["variable_bits"]-1}:0] {x["name"]}' for x in s['slots']]
    nativeports += [f'output reg valid_{stage}' for stage in range(1,s['depth']+1)]
    text += ['(* keep_hierarchy=1 *) module GeneralNative('+','.join(nativeports)+');']
    for stage in range(1,s['depth']+1):
        previous='iv' if stage==1 else f'valid_{stage-1}'
        text.append(f'always @(posedge clk)if(!rstn)valid_{stage}<=0;else valid_{stage}<={previous};')
    for x in s['slots']:
        j,stage=x['word'],x['stage'];w=s['words'][j]
        previous=f'word{j}' if stage==w['start'] else f'data_{j}_s{stage-1}'
        enable='iv' if stage==1 else f'valid_{stage-1}'
        text.append(f'always @(posedge clk)if(!rstn){x["name"]}<={x["variable_bits"]}\'h{x["reset"]:x};else if({enable}){x["name"]}<={previous};')
    text += ['endmodule']
    extports=['input wire clk,rstn,iv','output reg valid']
    extports += [port('word'+str(j),s['words'][j]['variable_bits']) for j in s['external_words']]
    extports += [f'output reg [{s["words"][j]["variable_bits"]-1}:0] data_{j}' for j in s['external_words']]
    text += ['(* keep_hierarchy=1 *) module GeneralExternal('+','.join(extports)+');',
        'always @(posedge clk)if(!rstn)valid<=0;else valid<=iv;']
    for j in s['external_words']:
        w=s['words'][j];text.append(f'always @(posedge clk)if(!rstn)data_{j}<={w["variable_bits"]}\'h{w["reset"]:x};else data_{j}<=word{j};')
    text += ['endmodule','module ModelBundle('+','.join(topports)+');','wire launch_valid;']
    for j,r in enumerate(s['roots']):text.append(f'wire [{r["width"]-1}:0] root{j};')
    for j,w in enumerate(s['words']):text.append(f'wire [{w["variable_bits"]-1}:0] adapter_word{j};')
    for x in s['slots']:text.append(f'wire [{x["variable_bits"]-1}:0] native_{x["name"]};')
    for stage in range(1,s['depth']+1):text.append(f'wire native_valid_{stage};')
    for j in s['external_words']:text.append(f'wire [{s["words"][j]["variable_bits"]-1}:0] external_data_{j};')
    launch=['.clk(clk)','.rstn(rstn)','.iv(iv)','.we_iv(we_iv)','.valid(launch_valid)']
    launch += [f'.in{j}(in{j}),.we{j}(we{j}),.data_{j}(root{j})' for j in range(len(s['roots']))]
    text += ['GeneralLaunch launch('+','.join(launch)+');',
        'GeneralAdapter adapter(.roots({'+','.join('root'+str(j) for j in reversed(range(len(s['roots']))))+'}),'+
        ','.join(f'.word{j}(adapter_word{j})' for j in range(len(s['words'])))+');']
    native=['.clk(clk)','.rstn(rstn)','.iv(launch_valid)']+[f'.word{j}(adapter_word{j})' for j in range(len(s['words']))]
    native += [f'.{x["name"]}(native_{x["name"]})' for x in s['slots']]
    native += [f'.valid_{stage}(native_valid_{stage})' for stage in range(1,s['depth']+1)]
    external=['.clk(clk)','.rstn(rstn)',f'.iv(native_valid_{s["depth"]})','.valid(ov)']
    external += [f'.word{j}(native_data_{j}_s{s["words"][j]["end"]}),.data_{j}(external_data_{j})' for j in s['external_words']]
    text += ['GeneralNative native('+','.join(native)+');','GeneralExternal external('+','.join(external)+');']
    observed=[]
    # Retain every logical channel terminal, including channels without an
    # external output; declared masks reconstruct padding without adding FFs.
    for j,w in enumerate(s['words']):
        source_name=f'external_data_{j}' if j in s['external_words'] else f'native_data_{j}_s{w["end"]}'
        cursor=0;logical=[]
        for bit in range(w['declared_width']):
            logical.append(f'{source_name}[{cursor}]' if w['variable_mask']>>bit&1 else "1'b0")
            cursor+=bool(w['variable_mask']>>bit&1)
        text.append(f'wire [{w["declared_width"]-1}:0] logical{j}={{{",".join(reversed(logical))}}};');observed.append('logical'+str(j))
    width=sum(w['declared_width'] for w in s['words'])
    text += ['GeneralObserver observer(.value({'+','.join(observed)+'}),.y(y));','endmodule',
        f'(* keep_hierarchy=1 *) module GeneralObserver(input wire [{width-1}:0] value,output wire y);assign y=^value;endmodule']
    return '\n'.join(text)+'\n'


def step(s,old,inputs,reset):
    result={};totalroot=0;root_shift=0
    for j,r in enumerate(s['roots']):
        enable=inputs['we_iv'] if s['service_mode']==1 else inputs[f'we{j}']
        result[f'launch.data_{j}']=r['reset'] if reset else inputs[f'in{j}'] if enable else old[f'launch.data_{j}']
        totalroot |= old[f'launch.data_{j}']<<root_shift;root_shift+=r['width']
    result['launch.valid']=0 if reset else inputs['iv'] if s['service_mode']==2 or inputs['we_iv'] else old['launch.valid']
    for stage in range(1,s['depth']+1):
        result[f'native.valid_{stage}']=0 if reset else old['launch.valid'] if stage==1 else old[f'native.valid_{stage-1}']
    for x in s['slots']:
        w=s['words'][x['word']];stage=x['stage'];key='native.'+x['name']
        if stage==w['start']:
            value=sum(((totalroot>>at)&1)<<k for k,at in enumerate(w['source_positions']))^w['invert']
        else:value=old[f'native.data_{x["word"]}_s{stage-1}']
        enable=old['launch.valid'] if stage==1 else old[f'native.valid_{stage-1}']
        result[key]=w['reset'] if reset else value if enable else old[key]
    for j in s['external_words']:
        w=s['words'][j];result[f'external.data_{j}']=w['reset'] if reset else old[f'native.data_{j}_s{w["end"]}']
    result['external.valid']=0 if reset else old[f'native.valid_{s["depth"]}']
    return result
