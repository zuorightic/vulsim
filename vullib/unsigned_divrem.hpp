#pragma once
#include "fixint.hpp"

namespace vularith {
// Defined unsigned division wrappers. Ordinary inlined helpers emit real DAGs;
// they do not introduce a new BEIR opcode or promise a fused divider cell.
template <uint32_t W>
inline Int<2*W> UDivRemShared(Int<W> a,Int<W> d) {
    static_assert(W>=1&&W<=128,"UDivRemShared supports unsigned widths 1..128");
    bool zero=d==Int<W>(0);
    Int<W> safe=zero?Int<W>(1):d;
    Int<W> raw_q=a/safe;
    // One real quotient is reused. The low product is exact modulo 2^W;
    // a-q*d lies in [0,d) for nonzero d. Each graph primitive is billed.
    Int<W> raw_r=a-Int<W>(raw_q*safe);
    Int<W> q=zero?~Int<W>(0):raw_q;
    Int<W> r=zero?a:raw_r;
    return Cat(r,q);
}
}
