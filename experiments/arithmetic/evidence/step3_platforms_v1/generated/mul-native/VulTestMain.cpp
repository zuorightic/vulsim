#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <type_traits>

#include "fixint.hpp"
#include "verilated.h"
#include "VMulProbe_sim_top.h"

using std::array;
using int8 = int8_t;
using uint8 = uint8_t;
using int16 = int16_t;
using uint16 = uint16_t;
using int32 = int32_t;
using uint32 = uint32_t;
using int64 = int64_t;
using uint64 = uint64_t;
using int128 = __int128_t;
using uint128 = __uint128_t;
using int128_t = __int128_t;
using uint128_t = __uint128_t;

struct InputData {
    uint32_t a;
    uint32_t b;
};

#include <cstdio>
#include <cstdlib>
#include <deque>

template <typename T>
static inline typename std::enable_if<std::is_integral<T>::value || std::is_enum<T>::value, uint64_t>::type
__vul_port_word(const T &value, uint32_t word) {
  return word == 0 ? static_cast<uint64_t>(value) : 0;
}

template <std::size_t Words>
static inline uint64_t __vul_port_word(const VlWide<Words> &value, uint32_t word) {
  uint32_t index = word * 2;
  uint64_t result = index < Words ? value[index] : 0;
  if (index + 1 < Words) result |= static_cast<uint64_t>(value[index + 1]) << 32;
  return result;
}

template <typename T>
static inline typename std::enable_if<std::is_integral<T>::value || std::is_enum<T>::value, void>::type
__vul_port_set_word(T &value, uint32_t word, uint64_t data) {
  if (word == 0) value = static_cast<T>(data);
}

template <std::size_t Words>
static inline void __vul_port_set_word(VlWide<Words> &value, uint32_t word, uint64_t data) {
  uint32_t index = word * 2;
  if (index < Words) value[index] = static_cast<uint32_t>(data);
  if (index + 1 < Words) value[index + 1] = static_cast<uint32_t>(data >> 32);
}

template <typename T>
static inline __uint128_t __vul_get_bits(const T &value, uint32_t offset, uint32_t width) {
  __uint128_t out = 0;
  for (uint32_t bit = 0; bit < width; ++bit) {
    uint32_t src = offset + bit;
    if ((__vul_port_word(value, src / 64) >> (src % 64)) & 1ULL) out |= ((__uint128_t)1 << bit);
  }
  return out;
}

template <typename T>
static inline void __vul_set_bits(T &value, uint32_t offset, uint32_t width, __uint128_t data) {
  for (uint32_t bit = 0; bit < width; ++bit) {
    uint32_t dst = offset + bit;
    uint32_t word = dst / 64;
    uint32_t shift = dst % 64;
    uint64_t cur = __vul_port_word(value, word);
    if ((data >> bit) & 1) cur |= (1ULL << shift); else cur &= ~(1ULL << shift);
    __vul_port_set_word(value, word, cur);
  }
}

class VulTestMain {
public:
  VulTestMain() {
    top = new VMulProbe_sim_top;
    top->clk = 0;
    top->rstn = 0;
    top->s0input___05Fvld___05F = false;
    for (int i = 0; i < 4; ++i) sim_commit_raw();
    top->rstn = 1;
    eval_and_process_services();
  }

  ~VulTestMain() {
    delete top;
  }

  void s0input(const uint32_t & a, const uint32_t & b) {
    assert(!__issued_s0input && "TestMain request 's0input' called more than once before sim_nextcycle()");
    __issued_s0input = true;
    top->s0input___05Fvld___05F = true;
    __vul_set_bits(top->s0input_a___05F, 0, 32, static_cast<__uint128_t>(a));
    __vul_set_bits(top->s0input_b___05F, 0, 32, static_cast<__uint128_t>(b));
    eval_and_process_services();
    return;
  }


protected:
      uint64_t current_tick = 0;

      struct ExpectedOutput {

          uint64_t value;

          uint64_t tick;

      };

      std::deque<ExpectedOutput> expected_outputs;


  VMulProbe_sim_top *top = nullptr;
  bool __processing_services = false;
  bool __issued_s0input = false;
  bool __handled_s3output = false;

  void sim_reset() {
    top->rstn = 0;
    top->s0input___05Fvld___05F = false;
    __issued_s0input = false;
    __handled_s3output = false;
    for (int i = 0; i < 4; ++i) sim_commit_raw();
    top->rstn = 1;
    eval_and_process_services();
  }

  void sim_execute() {
    eval_and_process_services();
  }

  void sim_nextcycle() {
    sim_execute();
    sim_commit();
  }

  void sim_commit() {
    top->clk = !top->clk;
    top->eval();
    top->s0input___05Fvld___05F = false;
    __issued_s0input = false;
    top->clk = !top->clk;
    top->eval();
    __handled_s3output = false;
  }

  void sim_commit_raw() {
    top->clk = !top->clk;
    top->eval();
    top->clk = !top->clk;
    top->eval();
  }

  void eval_and_process_services() {
    top->eval();
    process_services();
  }

  void process_services() {
    if (__processing_services) return;
    __processing_services = true;
    bool again = true;
    while (again) {
      again = false;
      {
        uint64_t y = {};
        y = static_cast<std::remove_cvref_t<decltype(y)>>(__vul_get_bits(top->s3output_y___05F, 0, 64));
        if (top->s3output___05Fvld___05F && !__handled_s3output) {
          __impl_s3output(y);
          __handled_s3output = true;
          top->eval();
          again = true;
        }
      }
    }
    __processing_services = false;
  }

  void __impl_s3output(const uint64_t & y) {
        if (expected_outputs.empty()) {

            std::printf("backend probe failed: unexpected output %llu at tick %llu\n",

                        static_cast<unsigned long long>(y),

                        static_cast<unsigned long long>(current_tick));

            std::exit(1);

        }

        const ExpectedOutput expected = expected_outputs.front();

        expected_outputs.pop_front();

        if (y != expected.value) {

            std::printf("backend probe failed: output %llu at tick %llu, expected %llu\n",

                        static_cast<unsigned long long>(y),

                        static_cast<unsigned long long>(current_tick),

                        static_cast<unsigned long long>(expected.value));

            std::exit(1);

        }

        if (current_tick != expected.tick) {

            std::printf("backend probe failed: latency mismatch at tick %llu, expected tick %llu\n",

                        static_cast<unsigned long long>(current_tick),

                        static_cast<unsigned long long>(expected.tick));

            std::exit(1);

        }

  }

public:
  void simulation() {
        constexpr uint64_t target_cycle = 10'000;

        constexpr uint64_t random_seed = 0x1'BF52;

        constexpr uint32_t directed[][2] = {

            {0U, 0U},

            {0U, 0xffffffffU},

            {1U, 0xffffffffU},

            {0xffffffffU, 0xffffffffU},

            {0x0000ffffU, 0x00010001U},

            {0x80000000U, 2U},

            {0x7fffffffU, 0x7fffffffU},

            {0x12345678U, 0x9abcdef0U},

        };

        uint64_t random_cur = random_seed;

        auto random = [&]() -> uint32_t {

            random_cur = random_cur * 6364136223846793005ULL + 1;

            uint32_t xorshifted = static_cast<uint32_t>(((random_cur >> 18) ^ random_cur) >> 27);

            uint32_t rot = static_cast<uint32_t>(random_cur >> 59);

            return (xorshifted >> rot) | (xorshifted << ((-rot) & 31));

        };

        for (current_tick = 0; current_tick < target_cycle; ++current_tick) {

            bool send = false;

            uint32_t a = 0;

            uint32_t b = 0;

            if (current_tick < sizeof(directed) / sizeof(directed[0])) {

                send = true;

                a = directed[current_tick][0];

                b = directed[current_tick][1];

            } else if ((random() & 1U) == 0U) {

                send = true;

                a = random();

                b = random();

            }

            if (send) {

                s0input(a, b);

                expected_outputs.push_back({

                    static_cast<uint64_t>(a) * static_cast<uint64_t>(b),

                    current_tick + 3,

                });

            }

            sim_nextcycle();

        }

        for (current_tick = target_cycle; current_tick < target_cycle + 3; ++current_tick) {

            sim_nextcycle();

        }

        if (!expected_outputs.empty()) {

            std::printf("backend probe failed: %llu expected outputs were not produced\n",

                        static_cast<unsigned long long>(expected_outputs.size()));

            std::exit(1);

        }

        std::printf("backend probe passed: %llu cycles\n",

                    static_cast<unsigned long long>(target_cycle));

  }

};

int main(int argc, char **argv) {
  Verilated::commandArgs(argc, argv);
  VulTestMain test_main;
  test_main.simulation();
  return 0;
}
