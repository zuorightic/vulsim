#include <fixint.hpp>
Int<32> a,b;Int<64> y;
#pragma input_port a
#pragma input_port b
#pragma output_port y
void top(){y=a*b;}
