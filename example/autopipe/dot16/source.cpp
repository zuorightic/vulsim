#include <fixint.hpp>
#pragma input_port a0
Int<64> a0;
#pragma input_port b0
Int<64> b0;
#pragma input_port a1
Int<64> a1;
#pragma input_port b1
Int<64> b1;
#pragma input_port a2
Int<64> a2;
#pragma input_port b2
Int<64> b2;
#pragma input_port a3
Int<64> a3;
#pragma input_port b3
Int<64> b3;
#pragma input_port a4
Int<64> a4;
#pragma input_port b4
Int<64> b4;
#pragma input_port a5
Int<64> a5;
#pragma input_port b5
Int<64> b5;
#pragma input_port a6
Int<64> a6;
#pragma input_port b6
Int<64> b6;
#pragma input_port a7
Int<64> a7;
#pragma input_port b7
Int<64> b7;
#pragma input_port a8
Int<64> a8;
#pragma input_port b8
Int<64> b8;
#pragma input_port a9
Int<64> a9;
#pragma input_port b9
Int<64> b9;
#pragma input_port a10
Int<64> a10;
#pragma input_port b10
Int<64> b10;
#pragma input_port a11
Int<64> a11;
#pragma input_port b11
Int<64> b11;
#pragma input_port a12
Int<64> a12;
#pragma input_port b12
Int<64> b12;
#pragma input_port a13
Int<64> a13;
#pragma input_port b13
Int<64> b13;
#pragma input_port a14
Int<64> a14;
#pragma input_port b14
Int<64> b14;
#pragma input_port a15
Int<64> a15;
#pragma input_port b15
Int<64> b15;
#pragma input_port iv
bool iv;
#pragma output_port y
Int<132> y;
#pragma output_port ov
bool ov;
void workload_top() {
    Int<132> p0 = Int<132>(Int<128>(a0) * Int<128>(b0));
    Int<132> p1 = Int<132>(Int<128>(a1) * Int<128>(b1));
    Int<132> p2 = Int<132>(Int<128>(a2) * Int<128>(b2));
    Int<132> p3 = Int<132>(Int<128>(a3) * Int<128>(b3));
    Int<132> p4 = Int<132>(Int<128>(a4) * Int<128>(b4));
    Int<132> p5 = Int<132>(Int<128>(a5) * Int<128>(b5));
    Int<132> p6 = Int<132>(Int<128>(a6) * Int<128>(b6));
    Int<132> p7 = Int<132>(Int<128>(a7) * Int<128>(b7));
    Int<132> p8 = Int<132>(Int<128>(a8) * Int<128>(b8));
    Int<132> p9 = Int<132>(Int<128>(a9) * Int<128>(b9));
    Int<132> p10 = Int<132>(Int<128>(a10) * Int<128>(b10));
    Int<132> p11 = Int<132>(Int<128>(a11) * Int<128>(b11));
    Int<132> p12 = Int<132>(Int<128>(a12) * Int<128>(b12));
    Int<132> p13 = Int<132>(Int<128>(a13) * Int<128>(b13));
    Int<132> p14 = Int<132>(Int<128>(a14) * Int<128>(b14));
    Int<132> p15 = Int<132>(Int<128>(a15) * Int<128>(b15));
    Int<132> s0_0 = p0 + p1;
    Int<132> s0_1 = p2 + p3;
    Int<132> s0_2 = p4 + p5;
    Int<132> s0_3 = p6 + p7;
    Int<132> s0_4 = p8 + p9;
    Int<132> s0_5 = p10 + p11;
    Int<132> s0_6 = p12 + p13;
    Int<132> s0_7 = p14 + p15;
    Int<132> s1_0 = s0_0 + s0_1;
    Int<132> s1_1 = s0_2 + s0_3;
    Int<132> s1_2 = s0_4 + s0_5;
    Int<132> s1_3 = s0_6 + s0_7;
    Int<132> s2_0 = s1_0 + s1_1;
    Int<132> s2_1 = s1_2 + s1_3;
    Int<132> s3_0 = s2_0 + s2_1;
    y = s3_0;
}
