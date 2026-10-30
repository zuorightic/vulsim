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

#pragma output_port __vul_port_s1reg
Int<64> __vul_port_s1reg;
#pragma output_port __vul_port_s1valid
bool __vul_port_s1valid;
void LogicSubModule_MulProbe_sim_top_pipeline_multiply_reset_inputs() {
{
InputData s1reg{};
__vul_port_s1reg = 0;
__vul_port_s1reg.at<31, 0>() = Int<32>(s1reg.a);
__vul_port_s1reg.at<63, 32>() = Int<32>(s1reg.b);
}
{
bool s1valid{};
__vul_port_s1valid = s1valid;
}
}
