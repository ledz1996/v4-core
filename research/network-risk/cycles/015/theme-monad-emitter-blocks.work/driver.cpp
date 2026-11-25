// Size-estimate driver: compiles a runtime bytecode with Monad's x86 emitter
// and prints the size estimate the production check compares to 10240+32*size.
#include <category/vm/compiler/ir/x86.hpp>
#include <category/vm/compiler/ir/basic_blocks.hpp>
#include <category/vm/evm/traits.hpp>
#include <asmjit/core/jitruntime.h>
#include <cstdio>
#include <fstream>
#include <string>
#include <vector>
using namespace monad::vm;
using namespace monad::vm::compiler;
template <monad::Traits T>
void run(char const *name, std::vector<uint8_t> const &code, uint32_t offset) {
    asmjit::JitRuntime rt;
    native::CompilerConfig cfg{};
    cfg.max_code_size_offset = interpreter::code_size_t::unsafe_from(offset);
    auto const n = interpreter::code_size_t::unsafe_from((uint32_t)code.size());
    auto bound = native::max_code_size(cfg.max_code_size_offset, n);
    auto nc = native::compile<T>(rt, code.data(), n, cfg);
    std::printf("%s offset=%u codesize=%zu bound=%u entry=%s error=%d estimate=%zu\n",
        name, offset, code.size(), (unsigned)*bound, nc->entrypoint() ? "yes" : "null",
        (int)nc->error_code(), nc->code_size_estimate_before_error());
}
int main(int argc, char **argv) {
    std::ifstream f(argv[1]); std::string hex; f >> hex;
    if (hex.rfind("0x", 0) == 0) hex = hex.substr(2);
    std::vector<uint8_t> code;
    for (size_t i = 0; i + 1 < hex.size(); i += 2) code.push_back((uint8_t)std::stoul(hex.substr(i, 2), nullptr, 16));
    uint32_t off = argc > 2 ? (uint32_t)std::stoul(argv[2]) : 10240;
    run<monad::MonadTraits<MONAD_TEN>>("MONAD_TEN", code, off);
    run<monad::MonadTraits<MONAD_NINE>>("MONAD_NINE", code, off);
    run<monad::MonadTraits<MONAD_EIGHT>>("MONAD_EIGHT", code, off);
}
