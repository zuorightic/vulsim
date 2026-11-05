"""Real disjoint-input parallel Mux contexts, frozen by complete source group."""
import copy
from .model_m2_samples import source as original_source


def source(width,fanout,replicas,sampling):
    if width not in (1,5,8,16,32,64) or fanout not in (1,2,3) or replicas not in (2,3,4):raise ValueError('unregistered Mux context')
    cfg=copy.deepcopy(sampling);cfg['families']['control']['operations']=['mux']*replicas
    text,labels=original_source('control',width,fanout,cfg,'')
    if len(labels)!=replicas or any(s['operation']!='mux' for s in labels):raise ValueError('non-Mux sampling bundle')
    return text,labels
