#include <fixint.hpp>
#pragma input_port a
Int<128> a;
#pragma input_port b
Int<128> b;
#pragma input_port iv
bool iv;
#pragma output_port y
Int<256> y;
#pragma output_port ov
bool ov;
void workload_top() {
    y = (Int<256>(a) * Int<256>(b));
}
