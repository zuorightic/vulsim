#include <array>
#include <cstdint>
#include <type_traits>
#include <fixint.hpp>
#include <arithmetic.hpp>

using std::array;

using int8 = int8_t;
using uint8 = uint8_t;
using int16 = int16_t;
using uint16 = uint16_t;
using int32 = int32_t;
using uint32 = uint32_t;
using int64 = int64_t;
using uint64 = uint64_t;

struct InputData {
    uint32_t a;
    uint32_t b;
};


#pragma output_port s3output__vld__
bool s3output__vld__;
#pragma output_port s3output_y__
Int<64> s3output_y__;
#pragma input_port s0input__vld__
bool s0input__vld__;
#pragma input_port s0input_a__
Int<32> s0input_a__;
#pragma input_port s0input_b__
Int<32> s0input_b__;
#pragma output_port wen_s1reg__
bool wen_s1reg__;
#pragma output_port wdata_s1reg__
Int<64> wdata_s1reg__;
#pragma output_port resetvalue_s1reg__
Int<64> resetvalue_s1reg__;
#pragma output_port wen_s1valid__
std::array<bool, 2> wen_s1valid__;
#pragma output_port wdata_s1valid__
std::array<Int<1>, 2> wdata_s1valid__;
#pragma output_port resetvalue_s1valid__
Int<1> resetvalue_s1valid__;
#pragma input_port rdata_s3reg__
Int<64> rdata_s3reg__;
#pragma input_port rdata_s3valid__
Int<1> rdata_s3valid__;

bool __vul_read_reg_s3valid() {
  const Int<1> &__vul_rdata = rdata_s3valid__;
  bool value = 0;
  value = ReduceOr(__vul_rdata.at<0, 0>());
  return value;
}

uint64_t __vul_read_reg_s3reg() {
  const Int<64> &__vul_rdata = rdata_s3reg__;
  uint64_t value = 0;
  value = Int<64>(__vul_rdata.at<63, 0>()).template to<typename std::remove_reference<decltype(value)>::type>();
  return value;
}

template <uint32_t P = 0>
void __vul_reg_setnext_s1valid(bool value) {
  Int<1> __vul_reg_wdata = 0;
  __vul_reg_wdata.at<0, 0>() = Int<1>(value);
  wdata_s1valid__[P] = __vul_reg_wdata;
  wen_s1valid__[P] = true;
}

template <uint32_t P = 0>
void __vul_reg_setnext_s1reg(InputData value) {
  Int<64> __vul_reg_wdata = 0;
  __vul_reg_wdata.at<31, 0>() = Int<32>(value.a);
  __vul_reg_wdata.at<63, 32>() = Int<32>(value.b);
  wdata_s1reg__ = __vul_reg_wdata;
  wen_s1reg__ = true;
}

void __vul_req_call_s3output(uint64_t y) {
  s3output__vld__ = true;
  uint64_t __vul_req_arg_y = (y);
  s3output_y__.at<63, 0>() = Int<64>(__vul_req_arg_y);
}

void LogicSubModule_MulProbe_sim_top() {
s3output__vld__ = false;
s3output_y__ = 0;
wen_s1reg__ = false;
wdata_s1reg__ = 0;
for (uint32_t __vul_p = 0; __vul_p < 2; ++__vul_p) {
  wen_s1valid__[__vul_p] = false;
  wdata_s1valid__[__vul_p] = 0;
}

{
  InputData s1reg{};
  Int<64> s1reg_flatten = 0;
  s1reg_flatten.at<31, 0>() = Int<32>(s1reg.a);
  s1reg_flatten.at<63, 32>() = Int<32>(s1reg.b);
  resetvalue_s1reg__ = s1reg_flatten;
}
{
  bool s1valid{};
  Int<1> s1valid_flatten = 0;
  s1valid_flatten.at<0, 0>() = Int<1>(s1valid);
  resetvalue_s1valid__ = s1valid_flatten;
}

auto s0input_impl__ = [&](uint32_t a, uint32_t b) -> void {
    __vul_reg_setnext_s1reg<0>(InputData{a, b});
    __vul_reg_setnext_s1valid<0>(true);
};
auto tick0__ = [&]() {
    __vul_reg_setnext_s1valid<1>(false);
    if (__vul_read_reg_s3valid()) __vul_req_call_s3output(__vul_read_reg_s3reg());
};

{
  uint32_t a = {};
  a = Int<32>(s0input_a__.at<31, 0>()).template to<typename std::remove_reference<decltype(a)>::type>();
  uint32_t b = {};
  b = Int<32>(s0input_b__.at<31, 0>()).template to<typename std::remove_reference<decltype(b)>::type>();
  if (s0input__vld__) {
    s0input_impl__(a, b);
  }
}
tick0__();

}

