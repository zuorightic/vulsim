#include "fixint.hpp"
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <stdexcept>

using namespace vulfixint;

template <typename L, typename R>
concept HasDivision = requires(const L& a, const R& b) { a / b; a % b; };
static_assert(HasDivision<Int<8>, Int<8>>);
static_assert(!HasDivision<Int<8>, Int<16>>);
static_assert((Int<8>(255) / Int<8>(3)).to<uint32_t>() == 85);
static_assert((Int<8>(255) % Int<8>(3)).to<uint32_t>() == 0);

template <uint32_t W>
void host_vectors() {
    constexpr uint64_t mask = ~uint64_t(0) >> (64-W);
    uint64_t state = 0x1234abcdef987654ull;
    for (unsigned i=0; i<512; ++i) {
        state ^= state << 13; state ^= state >> 7; state ^= state << 17;
        uint64_t a = state & mask;
        state ^= state << 13; state ^= state >> 7; state ^= state << 17;
        uint64_t d = (state & mask) | 1;
        assert((Int<W>(a)/Int<W>(d)).template to<uint64_t>() == a/d);
        assert((Int<W>(a)%Int<W>(d)).template to<uint64_t>() == a%d);
    }
}

int main() {
    unsigned pairs = 0;
    for (unsigned a=0; a<256; ++a) {
        for (unsigned d=1; d<256; ++d) {
            assert((Int<8>(a)/Int<8>(d)).to<unsigned>() == a/d);
            assert((Int<8>(a)%Int<8>(d)).to<unsigned>() == a%d);
            ++pairs;
        }
    }
    host_vectors<12>(); host_vectors<16>(); host_vectors<24>();
    host_vectors<32>(); host_vectors<48>(); host_vectors<64>();
    Int<128> all = ~Int<128>(0);
    assert(all/Int<128>(2) == (all >> 1u));
    assert(all%Int<128>(2) == Int<128>(1));
    Int<128> a = Int<128>(1) << 127u;
    Int<128> d = (Int<128>(1) << 64u)+Int<128>(1);
    assert(a/d == Int<128>((uint64_t(1) << 63)-1));
    assert(a%d == (Int<128>(1) << 64u)-Int<128>(uint64_t(1) << 63)+Int<128>(1));
    bool rejected = false;
    try { (void)(all/Int<128>(0)); } catch (const std::domain_error&) { rejected = true; }
    assert(rejected);
    rejected = false;
    try { (void)(all%Int<128>(0)); } catch (const std::domain_error&) { rejected = true; }
    assert(rejected);
    std::printf("FIXINT DIVISION PASS exhaustive_nonzero_pairs=%u random_pairs=3072 wide_checks=4 zero_rejections=2\n",pairs);
}
