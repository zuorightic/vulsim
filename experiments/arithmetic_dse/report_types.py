"""Static key-field JSON type checks for arithmetic reports (no coercion).

The embedded JSON Schemas use only the subset below. Unsupported schema keywords
are rejected rather than silently ignored. Integer tokens must decode as Python
int, so 128.0 and booleans cannot masquerade as report counters.
"""
import math

_KEYWORDS={'$schema','title','description','type','const','enum','required','properties','items','minimum','maximum','additionalProperties'}

def validate_report_types(report, schemas):
    if type(report) is not dict or report.get('status') not in schemas:
        raise ValueError('report type contract: unsupported status')
    def check(value, schema, path):
        unsupported=set(schema)-_KEYWORDS
        if unsupported:raise ValueError('unsupported report schema keyword: '+','.join(sorted(unsupported)))
        kind=schema.get('type')
        valid={'object':type(value) is dict,'array':type(value) is list,
               'string':type(value) is str,'integer':type(value) is int,
               'boolean':type(value) is bool,
               'number':type(value) in (int,float) and math.isfinite(value)}
        if kind not in valid or not valid[kind]:raise ValueError(f'report type contract: {path} requires {kind}')
        if 'const' in schema and (type(value) is not type(schema['const']) or value!=schema['const']):raise ValueError('report type contract: '+path+' const')
        if 'enum' in schema and value not in schema['enum']:raise ValueError('report type contract: '+path+' enum')
        for bound,op in [('minimum',lambda x,y:x<y),('maximum',lambda x,y:x>y)]:
            if bound in schema and op(value,schema[bound]):raise ValueError('report type contract: '+path+' '+bound)
        if kind=='object':
            for name in schema.get('required',[]):
                if name not in value:raise ValueError('report type contract: '+path+'.'+name+' missing')
            declared=schema.get('properties',{})
            for name,child in value.items():
                if name in declared:check(child,declared[name],path+'.'+name)
                else:
                    extra=schema.get('additionalProperties',True)
                    if extra is False:raise ValueError('report type contract: '+path+'.'+name+' unknown')
                    if type(extra) is dict:check(child,extra,path+'.'+name)
        if kind=='array' and 'items' in schema:
            for i,child in enumerate(value):check(child,schema['items'],f'{path}[{i}]')
    check(report,schemas[report['status']],'report')
