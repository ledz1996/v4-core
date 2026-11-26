// Cycle 27: countl_zero / bit_width of monad::uint256_t at one tag (include path selects it) against an independent
// per-limb count, on edge words and 2,000,000 random words with random zero limbs. Seed 27027.
#include <category/core/runtime/uint256.hpp>
#include <cstdio>
#include <random>
using monad::uint256_t;
static size_t ref(uint64_t const w[4]) { for (int i = 3; i >= 0; --i) if (w[i]) return (3 - i) * 64 + __builtin_clzll(w[i]); return 256; }
int main() {
    std::mt19937_64 g(27027); size_t n = 0, bad = 0;
    auto t = [&](uint64_t a, uint64_t b, uint64_t c, uint64_t d) {
        uint64_t w[4] = {a, b, c, d}; uint256_t x{a, b, c, d}; n++;
        if (monad::countl_zero(x) != ref(w) || monad::bit_width(x) != 256 - ref(w)) { if (bad++ < 5) std::printf("BAD %lx %lx %lx %lx\n", d, c, b, a); }
    };
    uint64_t e[] = {0, 1, 2, 3, 0x7fffffffffffffffULL, 0x8000000000000000ULL, ~0ULL, 0x100000000ULL};
    for (auto a : e) for (auto b : e) for (auto c : e) for (auto d : e) t(a, b, c, d);
    for (int k = 0; k < 2000000; k++) {
        uint64_t w[4]; for (auto &x : w) { x = g(); int m = g() % 4; if (m == 0) x = 0; else if (m == 1) x >>= (g() % 64); }
        t(w[0], w[1], w[2], w[3]);
    }
    std::printf("cases=%zu bad=%zu\n", n, bad); return bad != 0;
}
