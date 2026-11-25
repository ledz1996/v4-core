// Operand-class recorder for the interpreter (coverage build only): for each pc of the 15 target
// instructions, the union of edge classes seen per operand, and joint classes for shifts, BYTE,
// SIGNEXTEND and MULMOD. Written to $HX_OPND_OUT at exit.
#include <category/core/runtime/uint256.hpp>
#include <cstdio>
#include <cstdlib>
#include <map>
#include <set>
#include <string>
#include <array>
using monad::uint256_t;
namespace {
struct Rec { std::array<uint32_t, 3> m{}; std::set<std::string> joint; uint64_t n = 0; };
std::map<uint32_t, Rec> g;
bool g_on = std::getenv("HX_OPND_OUT") != nullptr;
uint32_t cls(uint256_t const &x)
{
    uint64_t w0 = x[0], w1 = x[1], w2 = x[2], w3 = x[3];
    bool hi0 = !(w1 | w2 | w3);
    uint32_t m = 0;
    if (hi0 && w0 == 0) m |= 1;            // 0
    else if (hi0 && w0 == 1) m |= 2;       // 1
    else if (hi0 && w0 == 31) m |= 4;      // 31
    else if (hi0 && w0 == 32) m |= 8;      // 32
    else if (hi0 && w0 == 255) m |= 16;    // 255
    else if (hi0 && w0 == 256) m |= 32;    // 256
    else if (hi0 && w0 > 256) m |= 64;     // 257 .. 2^64-1
    else if (hi0) m |= 2048;               // 2 .. 254 other small
    else if (w3 == 0x8000000000000000ull && !(w0 | w1 | w2)) m |= 256;  // 2^255
    else if (!~w0 && !~w1 && !~w2 && !~w3) m |= 512;                    // 2^256-1
    else if (w3 >> 63) m |= 1024;          // other with the top bit set
    else m |= 128;                         // other >= 2^64 without the top bit
    return m;
}
char const *sh(uint256_t const &s)
{
    if (s[1] | s[2] | s[3]) return "big";
    uint64_t v = s[0];
    if (v == 0) return "0"; if (v < 64) return "1-63"; if (v == 64) return "64"; if (v < 128) return "65-127";
    if (v == 128) return "128"; if (v < 192) return "129-191"; if (v == 192) return "192"; if (v < 255) return "193-254";
    if (v == 255) return "255"; if (v == 256) return "256"; return "257+";
}
char const *sg(uint256_t const &x)
{
    if (!(x[0] | x[1] | x[2] | x[3])) return "zero";
    if (!~x[0] && !~x[1] && !~x[2] && !~x[3]) return "max";
    return (x[3] >> 63) ? "neg" : "pos";
}
struct Dump { ~Dump() {
    if (!g_on) return;
    FILE *f = std::fopen(std::getenv("HX_OPND_OUT"), "w");
    for (auto const &[pc, r] : g) {
        std::fprintf(f, "%u %llu %u %u %u", pc, (unsigned long long)r.n, r.m[0], r.m[1], r.m[2]);
        for (auto const &j : r.joint) std::fprintf(f, " %s", j.c_str());
        std::fprintf(f, "\n");
    }
    std::fclose(f);
} } g_dump;
}
namespace monad::vm::interpreter {
void hx_opnd(uint8_t const *code, uint8_t const *ip, uint256_t const *bottom, uint256_t const *top)
{
    if (!g_on) return;
    long depth = top - bottom + 1;
    uint8_t op = *ip;
    auto &r = g[(uint32_t)(ip - code)];
    r.n++;
    for (int i = 0; i < 3 && i < depth; i++) r.m[i] |= cls(top[-i]);
    if (depth >= 2 && (op == 0x1b || op == 0x1c || op == 0x1d)) r.joint.insert(std::string("s") + sh(top[0]) + "/" + sg(top[-1]));
    if (depth >= 2 && op == 0x1a) r.joint.insert(std::string("i") + sh(top[0]) + "/" + sg(top[-1]));
    if (depth >= 2 && op == 0x0b) r.joint.insert(std::string("b") + sh(top[0]) + "/" + sg(top[-1]));
    if (depth >= 3 && (op == 0x09 || op == 0x08)) {
        // MULMOD: is the full product at least 2^256, and the operand widths
        auto const &a = top[0]; auto const &b = top[-1];
        auto bits = [](uint256_t const &x) { for (int k = 3; k >= 0; k--) if (x[k]) return 64 * k + 64 - __builtin_clzll(x[k]); return 0; };
        int ba = bits(a), bb = bits(b);
        char buf[64]; std::snprintf(buf, sizeof buf, "w%d", (ba + bb > 256) ? 2 : (ba + bb >= 256 ? 1 : 0));
        r.joint.insert(buf);
    }
}
}
