// Compile a runtime bytecode with monad v0.16.5's native compiler under forced block-exit writer orders.
// usage: orders HEXFILE MODE FROM TO [asmdir]
//   MODE 1: k = FROM..TO-1 is the permutation index (blocks with <= 6 elements: k mod n! th permutation;
//           larger blocks: shuffle seeded by k);  MODE 2: k is the shuffle seed for every block; MODE 0: map order.
// For each k prints the instrumentation report (symbolic check of every block exit) and the code size.
#include <category/vm/compiler/ir/x86.hpp>
#include <category/vm/evm/traits.hpp>
#include <asmjit/core/jitruntime.h>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <vector>
using namespace monad::vm;
extern "C" void hxw_set(int mode, uint64_t perm, uint64_t seed);
extern "C" void hxw_report(FILE *f, char const *tag);
int main(int argc, char **argv)
{
    std::ifstream f(argv[1]);
    std::string hex;
    f >> hex;
    if (hex.rfind("0x", 0) == 0) hex = hex.substr(2);
    std::vector<uint8_t> code;
    for (size_t i = 0; i + 1 < hex.size(); i += 2)
        code.push_back((uint8_t)std::stoul(hex.substr(i, 2), nullptr, 16));
    int const mode = std::atoi(argv[2]);
    uint64_t const from = std::strtoull(argv[3], nullptr, 10), to = std::strtoull(argv[4], nullptr, 10);
    std::fprintf(stdout, "code_bytes=%zu\n", code.size());
    for (uint64_t k = from; k < to; ++k) {
        hxw_set(mode, k, k);
        asmjit::JitRuntime rt;
        compiler::native::CompilerConfig cfg{};
        std::string lp;
        if (argc > 5) {
            lp = std::string(argv[5]) + "/asm-" + std::to_string(mode) + "-" + std::to_string(k) + ".asm";
            cfg.asm_log_path = lp.c_str();
        }
        auto nc = compiler::native::compile<monad::MonadTraits<MONAD_TEN>>(
            rt, code.data(), interpreter::code_size_t::unsafe_from((uint32_t)code.size()), cfg);
        char tag[64];
        std::snprintf(tag, sizeof tag, "mode=%d k=%lu entry=%s", mode, (unsigned long)k,
                      nc->entrypoint() ? "yes" : "null");
        hxw_report(stdout, tag);
        std::fflush(stdout);
    }
}
