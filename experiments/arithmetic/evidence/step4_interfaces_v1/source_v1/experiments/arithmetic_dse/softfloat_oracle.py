"""Compile just f32_mul and its dependencies from a supplied flat SoftFloat tree."""
import ctypes
import hashlib
from pathlib import Path
import subprocess

ADAPTER = Path(__file__).with_name('softfloat_adapter.c')
SOURCES = ('f32_mul.c', 's_normSubnormalF32Sig.c', 's_roundPackToF32.c',
           's_propagateNaNF32UI.c', 's_countLeadingZeros8.c',
           'softfloat_state.c', 'softfloat_raiseFlags.c')
HEADERS = ('platform.h', 'internals.h', 'specialize.h', 'softfloat.h',
           'softfloat_types.h', 'primitiveTypes.h', 'primitives.h')


def source_fingerprints(source: Path) -> dict:
    return {name: hashlib.sha256((source/name).read_bytes()).hexdigest()
            for name in (*SOURCES, *HEADERS)}


class SoftFloatOracle:
    def __init__(self, source: Path, output: Path):
        self.source_hashes = source_fingerprints(source)
        self.command = ['cc', '-std=c11', '-O2', '-shared', '-fPIC', '-Wl,-z,defs',
                        '-I'+str(source), str(ADAPTER),
                        *(str(source/name) for name in SOURCES), '-o', str(output)]
        subprocess.run(self.command, check=True, capture_output=True, text=True)
        self.library = ctypes.CDLL(str(output))
        self.function = self.library.arithmetic_ref_f32_mul
        self.function.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
        self.function.restype = ctypes.c_uint64

    def multiply(self, a: int, b: int) -> tuple[int, int]:
        if not 0 <= a < 1 << 32 or not 0 <= b < 1 << 32:
            raise ValueError('binary32 bit pattern out of range')
        value = self.function(a, b)
        return value & 0xFFFFFFFF, (value >> 32) & 31
