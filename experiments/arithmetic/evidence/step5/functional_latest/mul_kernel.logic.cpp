#include "fixint.hpp"
Int<32> a,b; Int<64> y; bool iv,ov;
#pragma input_port a
#pragma input_port b
#pragma input_port iv
#pragma output_port y
#pragma output_port ov
void mul_kernel(){y=a*b;}
