
/*============================================================================

This C source file is part of the SoftFloat IEEE Floating-Point Arithmetic
Package, Release 3d, by John R. Hauser.

Copyright 2011, 2012, 2013, 2014, 2015 The Regents of the University of
California.  All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

 1. Redistributions of source code must retain the above copyright notice,
    this list of conditions, and the following disclaimer.

 2. Redistributions in binary form must reproduce the above copyright notice,
    this list of conditions, and the following disclaimer in the documentation
    and/or other materials provided with the distribution.

 3. Neither the name of the University nor the names of its contributors may
    be used to endorse or promote products derived from this software without
    specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS "AS IS", AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE, ARE
DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

=============================================================================*/

// Bit-vector adaptation of SoftFloat 3d f32_mul / roundPackToF32, specialized
// to binary32, RNE and tininess-after-rounding. Per-operation flags, canonical
// NaN 0x7fc00000. This is an implementation, not the exact-integer oracle.
#pragma once
#include "fixint.hpp"
namespace vularith {
inline Int<37> F32MulRNEBody(Int<32> a, Int<32> b) {
    Int<1> sign = Int<1>((a ^ b) >> 31);
    Int<8> ea = Int<8>(a >> 23), eb = Int<8>(b >> 23);
    Int<23> fa = Int<23>(a), fb = Int<23>(b);
    bool na = (ea == Int<8>(255)) && (fa != Int<23>(0));
    bool nb = (eb == Int<8>(255)) && (fb != Int<23>(0));
    bool sn = (na && ((fa & Int<23>(0x400000)) == Int<23>(0))) ||
              (nb && ((fb & Int<23>(0x400000)) == Int<23>(0)));
    bool za = ((a & Int<32>(0x7fffffff)) == Int<32>(0));
    bool zb = ((b & Int<32>(0x7fffffff)) == Int<32>(0));
    Int<24> sa = Int<24>(fa), sb = Int<24>(fb);
    if (ea != Int<8>(0)) sa = sa | Int<24>(0x800000);
    if (eb != Int<8>(0)) sb = sb | Int<24>(0x800000);
    Int<8> la = 0, lb = 0;
    for (int i = 0; i < 23; ++i) {
        if (sa < Int<24>(0x800000)) { sa = sa << 1; la = la + Int<8>(1); }
        if (sb < Int<24>(0x800000)) { sb = sb << 1; lb = lb + Int<8>(1); }
    }
    // Signed exponents use a bias of 512, avoiding host signed shifts/casts.
    Int<12> xa = Int<12>(ea != Int<8>(0) ? ea : Int<8>(1)) + Int<12>(512) - Int<12>(la);
    Int<12> xb = Int<12>(eb != Int<8>(0) ? eb : Int<8>(1)) + Int<12>(512) - Int<12>(lb);
    Int<12> ez = xa + xb - Int<12>(639);
    Int<48> product = sa * sb;
    Int<32> sig = Int<32>(product >> 17);
    if ((product & Int<48>(0x1ffff)) != Int<48>(0)) sig = sig | Int<32>(1);
    if (sig < Int<32>(0x40000000)) { sig = sig << 1; ez = ez - Int<12>(1); }
    Int<5> flags = Int<5>(0);
    bool overflow = false;
    if (ez < Int<12>(512)) {
        bool tiny = (ez < Int<12>(511)) || (sig + Int<32>(64) < Int<32>(0x80000000));
        Int<12> shift = Int<12>(512) - ez;
        if (shift >= Int<12>(32)) {
            sig = sig != Int<32>(0) ? Int<32>(1) : Int<32>(0);
        } else {
            Int<32> mask = (Int<32>(1) << shift) - Int<32>(1);
            bool jam = (sig & mask) != Int<32>(0);
            sig = sig >> shift;
            if (jam) sig = sig | Int<32>(1);
        }
        ez = Int<12>(512);
        if (tiny && ((sig & Int<32>(127)) != Int<32>(0))) flags = flags | Int<5>(2);
    } else {
        overflow = (ez > Int<12>(765)) ||
            ((ez == Int<12>(765)) && (sig + Int<32>(64) >= Int<32>(0x80000000)));
    }
    Int<7> roundBits = Int<7>(sig);
    Int<32> rounded = (sig + Int<32>(64)) >> 7;
    if (roundBits != Int<7>(0)) flags = flags | Int<5>(1);
    if (roundBits == Int<7>(64)) rounded = rounded & Int<32>(0xfffffffe);
    Int<32> expBits = Int<32>(ez - Int<12>(512));
    if (rounded == Int<32>(0)) expBits = Int<32>(0);
    Int<32> result = (Int<32>(sign) << 31) | ((expBits << 23) + rounded);
    if (overflow) { result = (Int<32>(sign) << 31) | Int<32>(0x7f800000); flags = Int<5>(5); }
    if (na || nb) { result = Int<32>(0x7fc00000); flags = sn ? Int<5>(16) : Int<5>(0); }
    else if ((ea == Int<8>(255)) || (eb == Int<8>(255))) {
        if (za || zb) { result = Int<32>(0x7fc00000); flags = Int<5>(16); }
        else { result = (Int<32>(sign) << 31) | Int<32>(0x7f800000); flags = Int<5>(0); }
    } else if (za || zb) { result = Int<32>(sign) << 31; flags = Int<5>(0); }
    return Cat(flags, result);
}
// Reserved semantic API. Software executes the bit-vector body; RTLZZ carries
// an occurrence marker through BEOPT and materializes the same body as a region.
inline Int<37> F32MulRNE(Int<32> a, Int<32> b) { return F32MulRNEBody(a,b); }
}
