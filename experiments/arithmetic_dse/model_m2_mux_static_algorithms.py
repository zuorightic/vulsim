"""Same registered estimator families, with the Mux-only static feature ABI."""
import json,math
from .model_m2_mux_static_features import FEATURES,EXTRA
def algorithms(train,key,floor):
    import numpy as np
    from sklearn.linear_model import LinearRegression,Ridge
    from sklearn.tree import DecisionTreeRegressor
    y=np.asarray([r[key] for r in train]);result=[]
    names=list(FEATURES)
    def linear_export(model,selected,mean=None,scale=None):
        coefficients=model.coef_ if scale is None else model.coef_/scale
        intercept=float(model.intercept_) if mean is None else float(model.intercept_-np.dot(coefficients,mean))
        return {'kind':'linear','features':selected,'intercept':intercept,'coefficients':[float(v) for v in coefficients]}
    result.append(('constant_per_operation',{'kind':'linear','features':[],'coefficients':[],'intercept':float(np.mean(y))}))
    selected=['lhs_width','rhs_width','result_width','width_product','fanout','width_result_product','retained_product_terms',*EXTRA]
    x=np.asarray([[r['features'][k] for k in selected] for r in train]);simple=LinearRegression().fit(x,y)
    result.append(('linear_per_operation',linear_export(simple,selected)))
    x=np.asarray([[r['features'][k] for k in names] for r in train]);mean=x.mean(axis=0);scale=x.std(axis=0);scale[scale==0]=1
    for alpha in (.01,.1,1.,10.):
        model=Ridge(alpha=alpha).fit((x-mean)/scale,y);result.append((f'ridge_{alpha}',linear_export(model,names,mean,scale)))
    weights=1/np.maximum(np.abs(y),floor)**2;weights*=len(weights)/np.sum(weights)
    model=LinearRegression().fit((x-mean)/scale,y,sample_weight=weights)
    result.append(('relative_weighted_linear',linear_export(model,names,mean,scale)))
    for alpha in (.000001,.0001,.01,.1,1.):
        model=Ridge(alpha=alpha).fit((x-mean)/scale,y,sample_weight=weights);result.append((f'relative_weighted_ridge_{alpha}',linear_export(model,names,mean,scale)))
    for depth in (2,3,4):
        model=DecisionTreeRegressor(max_depth=depth,min_samples_leaf=2,random_state=20261102).fit(x,y);tree=model.tree_;nodes=[]
        for i in range(tree.node_count):
            nodes.append({'value':float(tree.value[i][0][0])} if tree.children_left[i]<0 else
                         {'feature':int(tree.feature[i]),'threshold':float(tree.threshold[i]),'left':int(tree.children_left[i]),'right':int(tree.children_right[i])})
        result.append((f'decision_tree_{depth}',{'kind':'tree','features':names,'nodes':nodes}))
    return result
