/* ABI wrapper only. Link against a separately supplied Berkeley SoftFloat.
 * The arithmetic implementation and its copyright remain in that source tree.
 * Packed return: bits[31:0], exception flags[36:32]. Not thread-safe.
 */
#include <stdint.h>
#include "softfloat.h"

uint64_t arithmetic_ref_f32_mul(uint32_t a_bits, uint32_t b_bits) {
    softfloat_roundingMode = softfloat_round_near_even;
    softfloat_detectTininess = softfloat_tininess_afterRounding;
    softfloat_exceptionFlags = 0;
    float32_t a = {a_bits};
    float32_t b = {b_bits};
    const float32_t result = f32_mul(a, b);
    uint32_t bits = result.v;
    /* Normalize payload/sign for source specializations that propagate NaNs. */
    if ((bits & UINT32_C(0x7fffffff)) > UINT32_C(0x7f800000))
        bits = UINT32_C(0x7fc00000);
    return (uint64_t)bits | ((uint64_t)(softfloat_exceptionFlags & 31) << 32);
}
