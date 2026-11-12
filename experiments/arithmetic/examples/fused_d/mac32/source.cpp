#include <array>
#include <cstdint>
#include <type_traits>
#include <fixint.hpp>
#include <arithmetic.hpp>
using std::array;
using int8 = int8_t; using uint8 = uint8_t; using int16 = int16_t; using uint16 = uint16_t; using int32 = int32_t; using uint32 = uint32_t; using int64 = int64_t; using uint64 = uint64_t;
struct CaseInput {
    Int<32> a;
    Int<32> b;
    Int<64> c;
};

struct CaseOutput {
    Int<64> y;
};

#pragma input_port __vul_port_a
Int<32> __vul_port_a;
#pragma input_port __vul_port_b
Int<32> __vul_port_b;
#pragma input_port __vul_port_c
Int<64> __vul_port_c;
#pragma input_port __vul_port_iv
bool __vul_port_iv;
#pragma output_port __vul_port_y
Int<64> __vul_port_y;
#pragma output_port __vul_port_ov
bool __vul_port_ov;
void __vul_compute(const Int<32> &a, const Int<32> &b, const Int<64> &c, const bool &iv, Int<64> &y) {
    Int<64> n_product = (a * b);
    Int<64> n_sum = (Int<64>(n_product) + Int<64>(c));
    y = n_sum;
}
void LogicSubModule_Top_sim_top_pipeline_core() {
Int<32> __vul_value_a{};
__vul_value_a = Int<32>(__vul_port_a.at<31, 0>());
Int<32> __vul_value_b{};
__vul_value_b = Int<32>(__vul_port_b.at<31, 0>());
Int<64> __vul_value_c{};
__vul_value_c = Int<64>(__vul_port_c.at<63, 0>());
bool __vul_value_iv{};
__vul_value_iv = __vul_port_iv;
Int<64> __vul_value_y;
__vul_compute(__vul_value_a, __vul_value_b, __vul_value_c, __vul_value_iv, __vul_value_y);
__vul_port_y = 0;
__vul_port_y.at<63, 0>() = Int<64>(__vul_value_y);
}
