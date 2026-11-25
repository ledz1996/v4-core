// Test harness: Monad main uint256.hpp generic and Barrett paths.
// Reads lines "op a b m" (hex, no 0x) on stdin and prints results in hex, for comparison with Python integers.
#include <category/core/runtime/uint256.hpp>
#include <iostream>
#include <string>
using monad::uint256_t;
namespace B = monad::barrett;
static uint256_t H(std::string const &s) { return uint256_t::from_string(("0x" + s).c_str()); }
static std::string O(uint256_t const &v) { return v.to_string(16); }
int main()
{
    std::ios::sync_with_stdio(false);
    std::string op, sa, sb, sm;
    while (std::cin >> op >> sa >> sb >> sm) {
        uint256_t a = H(sa), b = H(sb), m = H(sm);
        size_t bw = monad::bit_width(m);
        if (op == "D") { auto r = monad::udivrem(a, m); std::cout << O(r.quot) << " " << O(r.rem) << "\n"; }
        else if (op == "S") { auto r = monad::sdivrem(a, m); std::cout << O(r.quot) << " " << O(r.rem) << "\n"; }
        else if (op == "A") { std::cout << O(monad::addmod(a, b, m)) << "\n"; }
        else if (op == "M") { std::cout << O(monad::mulmod(a, b, m)) << "\n"; }
        else if (op == "BD") {
            uint256_t q, r;
#define DO(T) { T rc(m); auto x = B::udivrem(a, rc); q = x.quot; r = x.rem; }
            if (bw < 65) DO(B::udivrem_reciprocal_1_65) else if (bw < 129) DO(B::udivrem_reciprocal_65_129) else if (bw < 193) DO(B::udivrem_reciprocal_129_193) else DO(B::udivrem_reciprocal_193_256)
#undef DO
            B::udivrem_reciprocal rc(m); auto y = B::udivrem(a, rc);
            std::cout << O(q) << " " << O(r) << " " << O(y.quot) << " " << O(y.rem) << "\n";
        }
        else if (op == "BA") {
            uint256_t r;
#define DO(T) { T rc(m); r = B::addmod(a, b, rc); }
            if (bw < 65) DO(B::addmod_reciprocal_1_65) else if (bw < 129) DO(B::addmod_reciprocal_65_129) else if (bw < 193) DO(B::addmod_reciprocal_129_193) else DO(B::addmod_reciprocal_193_256)
#undef DO
            B::addmod_reciprocal rc(m); std::cout << O(r) << " " << O(B::addmod(a, b, rc)) << "\n";
        }
        else if (op == "BM") {
            uint256_t r;
#define DO(T) { T rc(m); r = B::mulmod(a, b, rc); }
            if (bw < 65) DO(B::mulmod_reciprocal_1_65) else if (bw < 129) DO(B::mulmod_reciprocal_65_129) else if (bw < 193) DO(B::mulmod_reciprocal_129_193) else DO(B::mulmod_reciprocal_193_256)
#undef DO
            B::mulmod_reciprocal rc(m); std::cout << O(r) << " " << O(B::mulmod(a, b, rc)) << "\n";
        }
        else if (op == "BC") {
            uint256_t r;
#define DO(T) { T rc(b, m); r = B::mulmod_const(a, rc); }
            if (bw < 65) DO(B::mulmod_const_reciprocal_1_65) else if (bw < 129) DO(B::mulmod_const_reciprocal_65_129) else if (bw < 193) DO(B::mulmod_const_reciprocal_129_193) else DO(B::mulmod_const_reciprocal_193_256)
#undef DO
            B::mulmod_const_reciprocal rc(b, m); std::cout << O(r) << " " << O(B::mulmod_const(a, rc)) << "\n";
        }
    }
}
