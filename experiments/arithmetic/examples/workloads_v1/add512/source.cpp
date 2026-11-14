#include <fixint.hpp>
#pragma input_port a
Int<512> a;
#pragma input_port b
Int<512> b;
#pragma input_port iv
bool iv;
#pragma output_port y
Int<513> y;
#pragma output_port ov
bool ov;
void workload_top() {
    y = (Int<513>(a) + Int<513>(b));
}
