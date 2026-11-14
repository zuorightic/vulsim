#include <fixint.hpp>
#pragma input_port x
Int<64> x;
#pragma input_port c0
Int<64> c0;
#pragma input_port c1
Int<64> c1;
#pragma input_port c2
Int<64> c2;
#pragma input_port c3
Int<64> c3;
#pragma input_port c4
Int<64> c4;
#pragma input_port iv
bool iv;
#pragma output_port y
Int<64> y;
#pragma output_port ov
bool ov;
void workload_top() {
    Int<64> n0 = c4 * x;
    Int<64> n1 = n0 + c3;
    Int<64> n2 = n1 * x;
    Int<64> n3 = n2 + c2;
    Int<64> n4 = n3 * x;
    Int<64> n5 = n4 + c1;
    Int<64> n6 = n5 * x;
    Int<64> n7 = n6 + c0;
    y = n7;
}
