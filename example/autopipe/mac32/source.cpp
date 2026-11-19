#include <fixint.hpp>
#pragma input_port a
Int<32> a;
#pragma input_port b
Int<32> b;
#pragma input_port c
Int<64> c;
#pragma input_port iv
bool iv;
#pragma output_port y
Int<64> y;
#pragma output_port ov
bool ov;
void workload_top() {
    y = (Int<64>(a) * Int<64>(b)) + Int<64>(c);
}
