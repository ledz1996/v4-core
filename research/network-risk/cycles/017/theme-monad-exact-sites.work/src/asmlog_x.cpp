// asm log of the patched x86.cpp build for a runtime bytecode (argv[1] hex file, argv[2] log path)
#include <category/vm/compiler/ir/x86.hpp>
#include <category/vm/evm/traits.hpp>
#include <category/core/runtime/uint256.hpp>
#include <asmjit/core/jitruntime.h>
#include <cstdio>
#include <fstream>
#include <string>
#include <vector>
using namespace monad::vm;
extern "C" { uint64_t hx_counts[64]; uint64_t hx_save; void hx_cap_impl(uint64_t, monad::uint256_t const *) {} }
namespace monad::vm::interpreter { void hx_step(uint8_t const *, uint8_t const *, void const *) {} }
static void one(char const *in, char const *outp);
int main(int argc, char **argv) { for (int i = 1; i + 1 < argc; i += 2) one(argv[i], argv[i + 1]); }
static void one(char const *in, char const *outp) {
    std::ifstream f(in); std::string hex; f >> hex; if (hex.rfind("0x",0)==0) hex=hex.substr(2);
    std::vector<uint8_t> code;
    for (size_t i = 0; i + 1 < hex.size(); i += 2) code.push_back((uint8_t)std::stoul(hex.substr(i, 2), nullptr, 16));
    asmjit::JitRuntime rt;
    compiler::native::CompilerConfig cfg{};
    cfg.asm_log_path = outp;
    auto nc = compiler::native::compile<monad::MonadTraits<MONAD_TEN>>(rt, code.data(), interpreter::code_size_t::unsafe_from((uint32_t)code.size()), cfg);
    std::printf("entry=%s estimate=%zu\n", nc->entrypoint() ? "yes" : "null", nc->code_size_estimate_before_error());
}
