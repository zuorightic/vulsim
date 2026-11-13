"""Factor-selected shared sources and roles, never per-workload prices."""
from . import wide_arithmetic as arithmetic
from .model_fast_preflight import key

VERSION='wide-family-factor-sources-v1'


def local(p,*,banks=1,consumer_width=None,shift=0):
    r=p['result_width']
    if consumer_width is None:return dict(producer=p,consumers=[],captures=[dict(banks=banks,declared_width=r,result_bit_map=list(range(r)))])
    if shift+r>consumer_width:raise ValueError('consumer demand exceeds width')
    mapping=['0']*shift+list(range(r))+['0']*(consumer_width-shift-r)
    consumer=arithmetic.spec('add',consumer_width,consumer_width,consumer_width,za=((1<<consumer_width)-1)^(((1<<r)-1)<<shift))
    return dict(producer=p,consumers=[dict(spec=consumer,bindings=[dict(operand_index=0,result_bit_map=mapping)],other_dynamic_inputs='independent_launch; source correlations require G validation')],captures=[])


def sources():
    s=arithmetic.spec;defs=[]
    def add(role,p,**load):defs.append((role,p,load))
    for a,b,w in ((32,32,33),(64,48,65),(128,96,129),(256,192,257)):
        add('train',s('add',a,b,w))
    add('train',s('add',512,512,513),consumer_width=640,shift=37)
    add('train',s('adc',64,64,64,status='carry',control='dynamic'))
    add('train',s('adc',128,128,128,status='carry',control='one'),banks=2)
    add('train',s('adc',256,256,257,control='dynamic'))
    add('train',s('sub',32,32,32,status='borrow'))
    add('train',s('sub',64,80,80,status='borrow'))
    add('train',s('sub',64,64,64))
    add('train',s('sbb',128,128,128,status='borrow',control='dynamic'))
    add('train',s('sbb',256,256,256,bits=128,status='borrow',control='one'))
    add('train',s('sbb',256,256,256,control='dynamic'))
    add('train',s('add',24,8,25,za=15),consumer_width=96,shift=43)
    add('train',s('add',12,20,21,za=255))
    for p in (s('add',47,63,65),s('add',193,127,194,bits=129),s('adc',95,95,95,status='carry',control='dynamic'),s('adc',257,253,258,control='one'),s('sub',97,128,128,status='borrow'),s('sbb',191,177,191,status='borrow',control='dynamic')):add('validation',p)
    for p in (s('add',509,511,512),s('adc',145,139,145,status='carry',control='dynamic'),s('sub',269,251,269,status='borrow'),s('sbb',83,79,83,status='borrow',control='one')):add('locked_test',p)
    add('train',s('mul',64,64,128))
    add('train',s('mul',64,64,128,bits=48),consumer_width=160,shift=83)
    add('train',s('mul',128,128,256))
    add('validation',s('mul',64,96,160,lo=80,bits=80))
    add('validation',s('mul',127,65,192))
    add('locked_test',s('mul',83,109,192,lo=96,bits=96))
    add('locked_test',s('mul',128,97,225,bits=129))
    for p in (s('ult',64,64,64),s('ule',128,128,128),s('eq',256,256,256)):add('train',p)
    for p in (s('ult',256,256,256),s('ule',256,256,256),s('eq',64,64,64)):add('train',p)
    for p in (s('ult',96,97,97),s('eq',193,191,193)):add('validation',p)
    for p in (s('ule',145,147,147),s('eq',269,251,269)):add('locked_test',p)
    add('train',s('mux',64,64,64,control='dynamic'))
    add('train',s('mux',256,256,256,control='dynamic'),banks=2)
    add('train',s('mux',128,128,128,control='dynamic'))
    add('train',s('mux',256,256,256,control='dynamic'))
    add('train',s('mux',64,64,64,control='dynamic'),banks=2)
    add('validation',s('mux',96,96,96,control='dynamic'))
    add('validation',s('mux',193,177,193,control='dynamic'))
    add('locked_test',s('mux',145,145,145,control='dynamic'))
    add('locked_test',s('mux',269,257,269,control='dynamic'))
    rows=[]
    for role,p,load in defs:
        f=local(p,**load);h=key(f);rows.append(dict(id='wide-'+h[:16],role=role,source_group=h,features=f))
    if len({r['source_group'] for r in rows})!=len(rows):raise ValueError('wide source role collision')
    return rows


def qualification_sources():
    s=arithmetic.spec
    definitions=[s('add',512,512,513),s('adc',63,65,65,status='carry',control='dynamic'),s('sub',128,97,128,status='borrow'),s('sbb',129,125,129,status='borrow',control='dynamic'),s('mul',64,64,128,lo=64,bits=64),s('ult',65,64,65),s('mux',193,193,193,control='dynamic')]
    rows=[];banned={r['source_group'] for r in sources()}
    for p in definitions:
        f=local(p);h=key(f)
        if h in banned:raise ValueError('qualification source cannot become training')
        rows.append(dict(id='qual-'+h[:16],role='not_training',source_group=h,features=f))
    return rows
