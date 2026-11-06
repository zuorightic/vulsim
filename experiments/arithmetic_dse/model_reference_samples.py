"""Prospective reference shells; no formal graph or physical result is copied."""
import hashlib
import re


def spec(key):
    if key=='f32_mul_rne':op,width,result='fp32',32,37
    elif re.fullmatch(r'mul_u\d+_r\d+',key):
        width,result=map(int,re.findall(r'\d+',key));op='mul'
    else:
        match=re.fullmatch(r'(add|bitor|div|eq|ite|mod)_u(\d+)',key)
        if not match:raise ValueError('unknown reference key')
        op,width=match[1],int(match[2]);result=1 if op=='eq' else width
    inputs={'a':width}
    if op!='eq':inputs['b']=width
    if op=='ite':inputs['sel']=1
    reset={n:int.from_bytes(hashlib.sha256((key+'/'+n).encode()).digest(),'big')&((1<<w)-1) for n,w in inputs.items()}
    if op in ('div','mod') and not reset['b']:reset['b']=1
    return {'id':key,'operation':op,'width':width,'result_width':result,'inputs':inputs,'reset':reset,
        'variable_result_bits':36 if op=='fp32' else result,
        'input_service_bits':sum(inputs.values())+1,
        'native_state_bits':(36 if op=='fp32' else result)+1,
        'external_state_bits':(36 if op=='fp32' else result)+1}


def evaluate(s,values):
    a=values['a'];b=values.get('b',0);op=s['operation']
    if op=='fp32':
        from .reference import f32_mul
        result=f32_mul(a,b);return result.bits|(result.flags<<32)
    value={'add':lambda:a+b,'bitor':lambda:a|b,'eq':lambda:int(a==0),'ite':lambda:a if values['sel'] else b,
           'mul':lambda:a*b,'div':lambda:a//b,'mod':lambda:a%b}[op]()
    return value&((1<<s['result_width'])-1)


def source(s,atom):
    key,op,w,r=s['id'],s['operation'],s['width'],s['result_width']
    def port(direction,name,width):return direction+' wire '+(f'[{width-1}:0] ' if width>1 else '')+name
    input_ports=[port('input',n,width) for n,width in s['inputs'].items()]
    enables=['input wire we_'+n for n in s['inputs']]
    launch_ports=['input wire clk,rstn,iv',*input_ports,*enables,'output reg valid']
    launch_ports += [f'output reg [{width-1}:0] data_{n}' for n,width in s['inputs'].items()]
    text=['(* keep_hierarchy=1 *) module RefLaunch('+','.join(launch_ports)+');',
        'always @(posedge clk)if(!rstn)valid<=0;else valid<=iv;']
    for n,width in s['inputs'].items():
        value='('+n+'==0 ? '+str(width)+"'d1 : "+n+')' if op in ('div','mod') and n=='b' else n
        text.append(f'always @(posedge clk)if(!rstn)data_{n}<={width}\'h{s["reset"][n]:x};else if(we_{n})data_{n}<={value};')
    text += ['endmodule','(* keep_hierarchy=1 *) module RefCore('+','.join(input_ports+[port('output','value',r)])+');']
    if op=='fp32':text.append('AtomicFp atom(.a(a),.b(b),.value(value));')
    else:
        expression={'add':'a+b','bitor':'a|b','eq':'a==0','ite':'sel?a:b','div':'a/b','mod':'a%b','mul':'a*b'}[op]
        text.append('assign value='+expression+';')
    reset=evaluate(s,s['reset'])
    v=s['variable_result_bits']
    packed="{value[36],value[34:0]}" if op=='fp32' else 'value'
    packed_reset=((reset>>36)<<35)|(reset&((1<<35)-1)) if op=='fp32' else reset
    text += ['endmodule',f'(* keep_hierarchy=1 *) module RefCapture(input wire clk,rstn,iv,input wire [{r-1}:0] value,output reg [{v-1}:0] data,output reg valid);',
        'always @(posedge clk)if(!rstn)valid<=0;else valid<=iv;',
        f'always @(posedge clk)if(!rstn)data<={v}\'h{packed_reset:x};else if(iv)data<={packed};',
        'endmodule',f'(* keep_hierarchy=1 *) module RefExternal(input wire clk,rstn,iv,input wire [{r-1}:0] value,output reg [{v-1}:0] data,output reg valid);',
        'always @(posedge clk)if(!rstn)valid<=0;else valid<=iv;',
        f'always @(posedge clk)if(!rstn)data<={v}\'h{packed_reset:x};else data<={packed};',
        'endmodule',f'(* keep_hierarchy=1 *) module RefObserver(input wire [{r-1}:0] value,output wire y);assign y=^value;endmodule',
        'module ModelBundle('+','.join(['input wire clk,rstn,iv',*input_ports,*enables,'output wire y,ov'])+');',
        f'wire [{r-1}:0] core_value,captured,external_value;wire [{v-1}:0] captured_payload,external_payload;wire launch_valid,capture_valid;']
    if op=='fp32':text += ["assign captured={captured_payload[35],1'b0,captured_payload[34:0]};","assign external_value={external_payload[35],1'b0,external_payload[34:0]};"]
    else:text += ['assign captured=captured_payload;assign external_value=external_payload;']
    for n,width in s['inputs'].items():text.append(f'wire [{width-1}:0] launch_{n};')
    launch=['.clk(clk)','.rstn(rstn)','.iv(iv)','.valid(launch_valid)']
    launch += ['.'+n+'('+n+')' for n in s['inputs']]+['.we_'+n+'(we_'+n+')' for n in s['inputs']]+['.data_'+n+'(launch_'+n+')' for n in s['inputs']]
    text += ['RefLaunch launch('+','.join(launch)+');',
        'RefCore core('+','.join(['.'+n+'(launch_'+n+')' for n in s['inputs']]+['.value(core_value)'])+');',
        'RefCapture capture(.clk(clk),.rstn(rstn),.iv(launch_valid),.value(core_value),.data(captured_payload),.valid(capture_valid));',
        'RefExternal external(.clk(clk),.rstn(rstn),.iv(capture_valid),.value(captured),.data(external_payload),.valid(ov));',
        'RefObserver observer(.value(external_value),.y(y));','endmodule']
    if op=='fp32':text.insert(0,atom)
    return '\n'.join(text)+'\n'


def requests(s):
    return [
        {'id':'data','kind':'register','from':['launch/data_*'],'to':['capture/data*'],'core_prefix':'core/'},
        {'id':'native_enable','kind':'register','from':['launch/valid*'],'to':['capture/data*']},
        {'id':'valid','kind':'register','from':['launch/valid*'],'to':['capture/valid*']},
        {'id':'external_data','kind':'register','from':['capture/data*'],'to':['external/data*']},
        {'id':'external_valid','kind':'register','from':['capture/valid*'],'to':['external/valid*']},
        {'id':'input_data','kind':'port','from':[n+'*' if width>1 else n for n,width in s['inputs'].items()],'to':['launch/data_*']},
        {'id':'input_enable','kind':'port','from':['we_*'],'to':['launch/data_*']},
        {'id':'input_valid','kind':'port','from':['iv'],'to':['launch/valid*']}]


def render_requests(s):
    return 'set vulsim_reference_requests {\n'+''.join('  {'+r['id']+' '+r['kind']+' {'+' '.join(r['from'])+'} {'+' '.join(r['to'])+'}}\n' for r in requests(s))+'}\n'
