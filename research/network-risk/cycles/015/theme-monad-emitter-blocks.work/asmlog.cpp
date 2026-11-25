// Writes the x86 assembly Monad's emitter produces for a runtime bytecode,
// with the emitter's own per-instruction comments, to argv[2].
#include <category/vm/compiler/ir/x86.hpp>
#include <category/vm/evm/traits.hpp>
#include <asmjit/core/jitruntime.h>
#include <cstdio>
#include <fstream>
#include <string>
#include <vector>
using namespace monad::vm;
int main(int argc, char **argv) {
    std::ifstream f(argv[1]); std::string hex; f >> hex;
    std::vector<uint8_t> code;
    for (size_t i = 0; i + 1 < hex.size(); i += 2) code.push_back((uint8_t)std::stoul(hex.substr(i, 2), nullptr, 16));
    asmjit::JitRuntime rt;
    compiler::native::CompilerConfig cfg{};
    cfg.asm_log_path = argv[2];
    auto nc = compiler::native::compile<monad::MonadTraits<MONAD_TEN>>(rt, code.data(), interpreter::code_size_t::unsafe_from((uint32_t)code.size()), cfg);
    std::printf("entry=%s estimate=%zu\n", nc->entrypoint() ? "yes" : "null", nc->code_size_estimate_before_error());
}
