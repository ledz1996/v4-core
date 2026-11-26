// Cycle 27: compile one runtime bytecode (hex file) with Monad's x86 emitter at the linked tag and write the asmjit
// listing with the emitter's debug comments (CompilerConfig::asm_log_path). Analysis only.
#include <category/vm/compiler/ir/x86.hpp>
#include <category/vm/evm/traits.hpp>
#include <category/vm/interpreter/intercode.hpp>
#include <asmjit/core/jitruntime.h>
#include <cstdio>
#include <fstream>
#include <string>
#include <vector>
using namespace monad::vm;
using T = monad::MonadTraits<MONAD_TEN>;
int main(int argc, char **argv) {
    std::ifstream f(argv[1]); std::string h; f >> h; if (h.rfind("0x", 0) == 0) h = h.substr(2);
    std::vector<uint8_t> code; for (size_t i = 0; i + 1 < h.size(); i += 2) code.push_back((uint8_t)std::stoul(h.substr(i, 2), nullptr, 16));
    asmjit::JitRuntime rt; compiler::native::CompilerConfig cfg{}; cfg.asm_log_path = argv[2];
    auto nc = compiler::native::compile<T>(rt, code.data(), interpreter::code_size_t::unsafe_from((uint32_t)code.size()), cfg);
    std::printf("code=%zu entry=%p native_size=%u\n", code.size(), (void *)nc->entrypoint(), 0u);
    return nc->entrypoint() ? 0 : 1;
}
