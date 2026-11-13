"""Finite unsigned arithmetic semantics and RTL for common operator families.

Widths and demanded slices are numerical parameters. This module grants no
physical price qualification and contains no workload or shape price index.
"""
from copy import deepcopy
import math
import re

VERSION='unsigned-wide-arithmetic-semantics-v1'
POLICY='unsigned-wide-family-hierarchy-v1'
MAX_WIDTH=4096
OPERATIONS=('add','adc','sub','sbb','mul','ult','ule','eq','mux')
FIELDS={'operation','lhs_width','rhs_width','arithmetic_width','result_lo','value_width',
        'status','result_width','lhs_zero_hex','lhs_one_hex','rhs_zero_hex','rhs_one_hex','carry','capture_banks'}


def spec(operation,a,b,w,*,lo=0,bits=None,status='none',control='zero',za=0,zb=0,oa=0,ob=0,banks=1):
    if bits is None:bits=1 if operation in ('ult','ule','eq') else w-lo
    s=dict(operation=operation,lhs_width=a,rhs_width=b,arithmetic_width=w,result_lo=lo,value_width=bits,status=status,
           result_width=bits+int(status!='none'),lhs_zero_hex=hex(za),rhs_zero_hex=hex(zb),lhs_one_hex=hex(oa),rhs_one_hex=hex(ob),carry=control,capture_banks=banks)
    return validate(s)


def validate(s):
    if set(s)!=FIELDS or s['operation'] not in OPERATIONS:raise ValueError('unknown wide arithmetic schema/operation')
    for n in ('lhs_width','rhs_width','arithmetic_width','value_width','result_width'):
        if type(s[n]) is not int or not 1<=s[n]<=MAX_WIDTH:raise ValueError('bounded positive wide scalar required')
    if type(s['result_lo']) is not int or s['result_lo']<0:raise ValueError('nonnegative result slice required')
    if s['carry'] not in ('zero','one','dynamic') or s['status'] not in ('none','carry','borrow'):raise ValueError('invalid control/status semantics')
    if type(s['capture_banks']) is not int or not 1<=s['capture_banks']<=4:raise ValueError('capture bank bound')
    op=s['operation'];w=s['arithmetic_width']
    if s['result_width']!=s['value_width']+int(s['status']!='none'):raise ValueError('status packing width mismatch')
    if s['result_lo']+s['value_width']>w:raise ValueError('result demand exceeds arithmetic precision')
    if op in ('add','sub','mul','ult','ule','eq') and s['carry']!='zero':raise ValueError('nonzero control requires ADC/SBB or Mux')
    if s['status']=='carry' and op not in ('add','adc'):raise ValueError('carry output belongs to add family')
    if s['status']=='borrow' and op not in ('sub','sbb'):raise ValueError('borrow output belongs to subtract family')
    if s['status']!='none' and max(s['lhs_width'],s['rhs_width'])>w:raise ValueError('status precision cannot silently truncate operands')
    if op in ('ult','ule','eq') and (s['value_width']!=1 or s['result_lo'] or w<max(s['lhs_width'],s['rhs_width'])):raise ValueError('comparison result/native precision mismatch')
    for p in ('lhs','rhs'):
        width=s[p+'_width'];z=s[p+'_zero_hex'];o=s[p+'_one_hex']
        if any(not isinstance(v,str) or not re.fullmatch(r'(?:0[xX])?[0-9a-fA-F]+',v) for v in (z,o)):raise ValueError('unsigned hex masks required')
        z=int(z,16);o=int(o,16)
        if z<0 or o<0 or z&o or (z|o)>>width:raise ValueError('invalid operand masks')
    return s


def masked(s,p,value):
    return (value&((1<<s[p+'_width'])-1)&~int(s[p+'_zero_hex'],16))|int(s[p+'_one_hex'],16)


def evaluate(s,a,b,control=0):
    validate(s);a=masked(s,'lhs',a);b=masked(s,'rhs',b);w=s['arithmetic_width'];mask=(1<<w)-1
    c=int(bool(control)) if s['carry']=='dynamic' else int(s['carry']=='one');op=s['operation'];flag=0
    if op in ('add','adc'):
        raw=(a&mask)+(b&mask)+c;flag=(raw>>w)&1;value=raw&mask
    elif op in ('sub','sbb'):
        flag=int((a&mask)<(b&mask)+c);value=((a&mask)-(b&mask)-c)&mask
    elif op=='mul':value=(a*b)&mask
    elif op=='ult':value=int(a<b)
    elif op=='ule':value=int(a<=b)
    elif op=='eq':value=int(a==b)
    else:value=(b if c else a)&mask
    value=(value>>s['result_lo'])&((1<<s['value_width'])-1)
    return value|(flag<<s['value_width'] if s['status']!='none' else 0)


def precision(s):
    return max(s['lhs_width'],s['rhs_width']) if s['operation'] in ('ult','ule','eq') else s['arithmetic_width']


def bit_values(s,p,i):
    if i>=s[p+'_width'] or int(s[p+'_zero_hex'],16)>>i&1:return (0,)
    if int(s[p+'_one_hex'],16)>>i&1:return (1,)
    return (0,1)


def aliases(s):
    """Exact 0/1/shift/identity lowering, independent of any measured price."""
    op=s['operation'];constants={}
    for name in ('lhs','rhs'):
        if (int(s[name+'_zero_hex'],16)|int(s[name+'_one_hex'],16))==(1<<s[name+'_width'])-1:
            constants[name]=int(s[name+'_one_hex'],16)
    source=None;shift=0
    if op=='mul':
        for name,other in (('lhs','rhs'),('rhs','lhs')):
            if name in constants:
                value=constants[name]
                if value==0:return ['0']*s['result_width']
                if value&(value-1)==0:source=other;shift=value.bit_length()-1;break
    elif op in ('add','adc') and s['carry']=='zero':
        if constants.get('lhs')==0:source='rhs'
        elif constants.get('rhs')==0:source='lhs'
    elif op in ('sub','sbb') and s['carry']=='zero' and constants.get('rhs')==0:source='lhs'
    elif op=='mux' and s['carry']!='dynamic':source='rhs' if s['carry']=='one' else 'lhs'
    if source is None:return None
    result=[]
    for i in range(s['result_lo'],s['result_lo']+s['value_width']):
        bit=i-shift;v=bit_values(s,source,bit) if bit>=0 else (0,)
        result.append(str(v[0]) if len(v)==1 else [source,bit])
    if s['status']!='none':result.append('0')
    return result


def known_result(s):
    validate(s);op=s['operation'];w=s['arithmetic_width'];native=[];flag=(0,)
    alias=aliases(s)
    if alias is not None:return (sum(1<<i for i,v in enumerate(alias) if v=='0'),sum(1<<i for i,v in enumerate(alias) if v=='1'))
    if op in ('add','adc','sub','sbb'):
        carry=(0,1) if s['carry']=='dynamic' else (int(s['carry']=='one'),)
        for i in range(w):
            outcomes={(a+b+c if op in ('add','adc') else a-b-c) for a in bit_values(s,'lhs',i) for b in bit_values(s,'rhs',i) for c in carry}
            native.append(tuple(sorted({v&1 for v in outcomes})))
            carry=tuple(sorted({int(v>=2) if op in ('add','adc') else int(v<0) for v in outcomes}))
        flag=carry
    elif op=='mul':
        amin=int(s['lhs_one_hex'],16);bmin=int(s['rhs_one_hex'],16);amax=((1<<s['lhs_width'])-1)^int(s['lhs_zero_hex'],16);bmax=((1<<s['rhs_width'])-1)^int(s['rhs_zero_hex'],16)
        if amin==amax and bmin==bmax:native=[((amin*bmin>>i)&1,) for i in range(w)]
        else:
            az=next((i for i in range(s['lhs_width']) if not(int(s['lhs_zero_hex'],16)>>i&1)),s['lhs_width']);bz=next((i for i in range(s['rhs_width']) if not(int(s['rhs_zero_hex'],16)>>i&1)),s['rhs_width']);high=(amax*bmax).bit_length()
            native=[(0,) if i<az+bz or i>=high else (0,1) for i in range(w)]
    elif op=='mux':
        for i in range(w):
            aa=bit_values(s,'lhs',i);bb=bit_values(s,'rhs',i);native.append(aa if s['carry']=='zero' else bb if s['carry']=='one' else tuple(sorted(set(aa+bb))))
    else:
        amin=int(s['lhs_one_hex'],16);bmin=int(s['rhs_one_hex'],16);amax=((1<<s['lhs_width'])-1)^int(s['lhs_zero_hex'],16);bmax=((1<<s['rhs_width'])-1)^int(s['rhs_zero_hex'],16)
        if op=='ult':v=(1,) if amax<bmin else (0,) if amin>=bmax else (0,1)
        elif op=='ule':v=(1,) if amax<=bmin else (0,) if amin>bmax else (0,1)
        else:
            conflict=(int(s['lhs_one_hex'],16)&int(s['rhs_zero_hex'],16))|(int(s['rhs_one_hex'],16)&int(s['lhs_zero_hex'],16))
            v=(0,) if conflict else (int(amin==bmin),) if amin==amax and bmin==bmax else (0,1)
        native=[v]+[(0,)]*(w-1)
    bits=native[s['result_lo']:s['result_lo']+s['value_width']]+([flag] if s['status']!='none' else [])
    return (sum(1<<i for i,v in enumerate(bits) if v==(0,)),sum(1<<i for i,v in enumerate(bits) if v==(1,)))


def permutation(s):
    if s['operation'] not in ('add','adc'):return [0,1]
    def key(p):
        live=[i for i in range(min(s[p+'_width'],precision(s))) if len(bit_values(s,p,i))==2]
        return (len(live),max(live,default=-1)+1,min(live,default=0),s[p+'_width'],int(s[p+'_zero_hex'],16),int(s[p+'_one_hex'],16))
    return [1,0] if key('rhs')>key('lhs') else [0,1]


def source(s,name):
    validate(s)
    if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',name):raise ValueError('safe module identifier required')
    wa,wb,w,r=(s[k] for k in ('lhs_width','rhs_width','arithmetic_width','result_width'));order=permutation(s);names=['masked_a','masked_b'];left,right=(names[i] for i in order)
    def expression(p,value):
        bits=s[p+'_width'];z=int(s[p+'_zero_hex'],16);o=int(s[p+'_one_hex'],16)
        return f"(({value}&{bits}'h{(((1<<bits)-1)&~(z|o)):x})|{bits}'h{o:x})"
    ctrl='cin' if s['carry']=='dynamic' else "1'b1" if s['carry']=='one' else "1'b0";op=s['operation']
    text=f'// {POLICY}\n(* keep_hierarchy=1 *) module {name}Core(input wire [{wa-1}:0] a,input wire [{wb-1}:0] b,input wire cin,output wire [{r-1}:0] value);\n'
    text+=f'wire [{wa-1}:0] masked_a={expression("lhs","a")};\nwire [{wb-1}:0] masked_b={expression("rhs","b")};\n'
    text+=f"wire [{w-1}:0] aa={w}'({left});\nwire [{w-1}:0] bb={w}'({right});\n"
    if op in ('add','adc','sub','sbb'):
        sign='+' if op in ('add','adc') else '-';text+=f"wire [{w}:0] extended={{1'b0,aa}}{sign}{{1'b0,bb}}{sign}{w+1}'({ctrl});\nwire [{w-1}:0] native_value=extended[{w-1}:0];\n";status=f'extended[{w}]'
    elif op=='mul':text+=f'wire [{w-1}:0] native_value=aa*bb;\n';status="1'b0"
    elif op=='mux':text+=f'wire [{w-1}:0] native_value={ctrl}?bb:aa;\n';status="1'b0"
    else:
        operator={'ult':'<','ule':'<=','eq':'=='}[op];text+=f"wire [{w-1}:0] native_value={w}'(aa{operator}bb);\n";status="1'b0"
    selected=f'native_value[{s["result_lo"]}+:{s["value_width"]}]';text+='assign value='+('{'+status+','+selected+'}' if s['status']!='none' else selected)+';\nendmodule\n'
    # Match the existing context generator's Core/body split marker.
    return text+f'(* keep_hierarchy=1 *) module {name}();endmodule\n'


def features(s,target):
    validate(s)
    if type(target) not in (int,float) or not math.isfinite(target) or target<=0:raise ValueError('positive numerical T required')
    p=deepcopy(s)
    if permutation(p)==[1,0]:
        for suffix in ('width','zero_hex','one_hex'):p['lhs_'+suffix],p['rhs_'+suffix]=p['rhs_'+suffix],p['lhs_'+suffix]
    op=p['operation'];w=p['arithmetic_width'];live={name:[i for i in range(min(p[name+'_width'],precision(p))) if len(bit_values(p,name,i))==2] for name in ('lhs','rhs')}
    result=dict(one=1.,lhs_width=float(p['lhs_width']),rhs_width=float(p['rhs_width']),arithmetic_width=float(w),result_lo=float(p['result_lo']),value_width=float(p['value_width']),result_width=float(p['result_width']),target_ps=float(target),log2_target=math.log2(target/500.),clock_pressure=1500./target,
        family_add=float(op in ('add','adc')),family_sub=float(op in ('sub','sbb')),family_mul=float(op=='mul'),family_compare=float(op in ('ult','ule','eq')),family_mux=float(op=='mux'),predicate_lt=float(op=='ult'),predicate_le=float(op=='ule'),predicate_eq=float(op=='eq'),control_dynamic=float(p['carry']=='dynamic'),control_one=float(p['carry']=='one'),status_carry=float(p['status']=='carry'),status_borrow=float(p['status']=='borrow'))
    for name in ('lhs','rhs'):
        result[name+'_live_bits']=float(len(live[name]));result['log2_'+name+'_live_bits']=math.log2(len(live[name])+1.)
        result[name+'_low_position']=float(min(live[name],default=0));result[name+'_high_position']=float(max(live[name],default=-1)+1)
        result[name+'_known_one_bits']=float(int(p[name+'_one_hex'],16).bit_count())
    hi=p['result_lo']+p['value_width'];terms=sum(1 for a in live['lhs'] for b in live['rhs'] if a+b<hi)
    overlap=len(set(live['lhs'])&set(live['rhs']));z,o=known_result(p)
    result.update(active_overlap=float(overlap),retained_product_terms=float(terms),known_result_bits=float((z|o).bit_count()),dynamic_result_bits=float(p['result_width']-(z|o).bit_count()),log2_arithmetic_width=math.log2(w+1.),pressure_product_terms=terms*1500./target,pressure_width=w*1500./target)
    return result
