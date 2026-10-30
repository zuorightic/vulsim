#include <array>
#include <cstdint>
#include <type_traits>
#include <fixint.hpp>
#include <arithmetic.hpp>
using std::array;
using int8 = int8_t; using uint8 = uint8_t; using int16 = int16_t; using uint16 = uint16_t; using int32 = int32_t; using uint32 = uint32_t; using int64 = int64_t; using uint64 = uint64_t;
struct InputData {
    uint32_t a;
    uint32_t b;
};

#pragma input_port __vul_port_s1reg
Int<64> __vul_port_s1reg;
#pragma input_port __vul_port_s1valid
bool __vul_port_s1valid;
#pragma output_port __vul_port_s3reg
Int<64> __vul_port_s3reg;
#pragma output_port __vul_port_s3valid
bool __vul_port_s3valid;
void __vul_compute(const InputData &s1reg, const bool &s1valid, uint64_t &s3reg) {
    Int<64> a = s1reg.a;
    Int<64> b = s1reg.b;
    Int<64> product = a * b;
    s3reg = product.to<uint64_t>();
}
void LogicSubModule_MulProbe_sim_top_pipeline_multiply() {
InputData __vul_value_s1reg{};
__vul_value_s1reg.a = Int<32>(__vul_port_s1reg.at<31, 0>()).template to<typename std::remove_reference<decltype(__vul_value_s1reg.a)>::type>();
__vul_value_s1reg.b = Int<32>(__vul_port_s1reg.at<63, 32>()).template to<typename std::remove_reference<decltype(__vul_value_s1reg.b)>::type>();
bool __vul_value_s1valid{};
__vul_value_s1valid = __vul_port_s1valid;
uint64_t __vul_value_s3reg;
__vul_compute(__vul_value_s1reg, __vul_value_s1valid, __vul_value_s3reg);
__vul_port_s3reg = 0;
__vul_port_s3reg.at<63, 0>() = Int<64>(__vul_value_s3reg);
}
