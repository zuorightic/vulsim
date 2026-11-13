"""Same sum emission and sparse-output contract with a versioned wide validator."""
from types import FunctionType,SimpleNamespace
from . import reduction_sampling as dense,reduction_sampling_v2 as sparse
from . import reduction_wide_features as wide

VERSION='register-reduction-wide-sampling-v1'


def _bind(function,**replacements):
    return FunctionType(function.__code__,dict(function.__globals__,**replacements),
                        argdefs=function.__defaults__,closure=function.__closure__)


def _validate(width,terms,target):return wide.features(width,terms,target)['delay']
_dense_geometry=_bind(dense.geometry,features=_validate)
geometry=_bind(sparse.geometry,parent=SimpleNamespace(geometry=_dense_geometry))
_dense_source=_bind(dense.source,geometry=_dense_geometry)
source=_bind(sparse.source,geometry=geometry,parent=SimpleNamespace(source=_dense_source))
evaluate=_bind(dense.evaluate,geometry=_dense_geometry)
geometry_contract=_bind(sparse.geometry_contract,geometry=geometry)
mapped_port_contract=_bind(sparse.mapped_port_contract,geometry=geometry)
