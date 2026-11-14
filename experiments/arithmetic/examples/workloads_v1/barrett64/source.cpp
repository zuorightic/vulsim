#include <fixint.hpp>
#pragma input_port a
Int<64> a;
#pragma input_port b
Int<64> b;
#pragma input_port modulus
Int<64> modulus;
#pragma input_port mu
Int<65> mu;
#pragma input_port iv
bool iv;
#pragma output_port y
Int<64> y;
#pragma output_port ov
bool ov;
void workload_top() {
    Int<128> n0 = Int<128>(a) * Int<128>(b);
    Int<193> n1 = Int<193>(n0) * Int<193>(mu);
    Int<65> n2 = n1.at<192,128>();
    Int<129> n3 = Int<129>(n2) * Int<129>(modulus);
    Int<129> n4 = Int<129>(n0) - n3;
    Int<129> n5 = (n4 < Int<129>(modulus)) ? n4 : (n4 - Int<129>(modulus));
    Int<64> n6 = Int<64>(n5);
    y = n6;
}
