"""Exact analysis wire protocol: integer counters, reduced rational objects.

These analysis files are audit artifacts, not training labels, model features or
production scheduling inputs. Step7/8 consumers must opt into this version and
parse exact values; generic JSON-string or float sorting is not an interface.
"""
from fractions import Fraction
import math
VERSION='arithmetic-exact-analysis-v2'
def integer(value,label,minimum=0):
 if type(value) is not int or value<minimum:raise ValueError(label+' requires JSON integer')
 return value
def rational(value):
 if isinstance(value,Fraction):return value
 if type(value) is int:return Fraction(value)
 if type(value) is float and math.isfinite(value):return Fraction(str(value))
 raise ValueError('exact calculation requires finite numeric value')
def encode(value):
 f=rational(value);return {'numerator':f.numerator,'denominator':f.denominator}
def decode(value,label='rational'):
 if type(value) is not dict or set(value)!= {'numerator','denominator'}:raise ValueError(label+' requires numerator/denominator object')
 n=value['numerator'];d=value['denominator']
 if type(n) is not int or type(d) is not int or d<=0:raise ValueError(label+' requires integer numerator and positive denominator')
 f=Fraction(n,d)
 if f.numerator!=n or f.denominator!=d:raise ValueError(label+' must be reduced canonical rational')
 return f

def score(cost,candidate):
 if type(candidate) is not str or not candidate:raise ValueError('candidate ID string required')
 return {'maximum_delay':encode(cost['maximum_delay']),'comb_plus_register_bits':encode(cost['comb']+cost['register_bits']),'register_bits':integer(cost['register_bits'],'register_bits'),'register_count':integer(cost['register_count'],'register_count'),'candidate_id':candidate}
def score_key(value):
 if type(value) is not dict or set(value)!= {'maximum_delay','comb_plus_register_bits','register_bits','register_count','candidate_id'}:raise ValueError('invalid typed score')
 candidate=value['candidate_id']
 if type(candidate) is not str:raise ValueError('candidate ID string required')
 return (decode(value['maximum_delay']),decode(value['comb_plus_register_bits']),integer(value['register_bits'],'score register_bits'),integer(value['register_count'],'score register_count'),candidate)

def check_sensitivity(document):
 if document.get('version')!='mul-comb-sensitivity-v2' or document.get('numeric_protocol')!=VERSION:raise ValueError('unsupported sensitivity version')
 for key in ('structures','contexts','selected_changes'):integer(document[key],key)
 if len(document['rows'])!=document['contexts']:raise ValueError('sensitivity context count')
 for row in document['rows']:
  integer(row['W'],'W',1)
  if type(row['selected_changed']) is not bool:raise ValueError('selected_changed requires boolean')
  for variant in row['structures']:
   for key in ('register_bits','register_count','linear_rank','square_rank'):integer(variant[key],key,1 if key.endswith('_rank') else 0)
   for key in ('linear_comb','square_comb'):decode(variant[key],key)
   for value in variant['stage_delays']:decode(value,'stage delay')
   score_key(variant['linear_score']);score_key(variant['square_score'])
