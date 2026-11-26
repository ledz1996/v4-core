# Coverage patch of Monad's x86 emitter: bind one extra label at the start of every IR basic block
# (a label emits no bytes) and, after the runtime has placed the code, record each block's native address.
# Nothing else in the emitted code changes. Usage: patch_emitter.py <in emitter.cpp> <out emitter.cpp>
import sys, re
s = open(sys.argv[1]).read()
hdr = '''
#include <vector>
#include <utility>
namespace monad_cov {
    std::vector<std::pair<uint32_t, asmjit::Label>> pending;
    std::vector<std::pair<uint32_t, uint64_t>> blocks;   // (EVM offset of the IR block, native address)
    std::vector<uint8_t> enterable;                       // block_prologue result
    uint64_t base = 0, text_end = 0, error_addr = 0, epilogue_addr = 0;
}
'''
# after the last #include line
idx = [m.end() for m in re.finditer(r'^#include[^\n]*\n', s, re.M)][-1]
s = s[:idx] + hdr + s[idx:]
n0 = s.count('contract_prologue();\n    }')
s = s.replace('        contract_prologue();\n    }', '        monad_cov::pending.clear(); monad_cov::enterable.clear();\n        contract_prologue();\n    }', 1)
a = 'bool Emitter::begin_new_block(basic_blocks::Block const &b)\n    {\n'
assert s.count(a) == 1
s = s.replace(a, a + '        { auto const cov_l = as_.newLabel(); as_.bind(cov_l); monad_cov::pending.emplace_back(static_cast<uint32_t>(b.offset), cov_l); }\n')
# record block_prologue result: the function ends with "return block_prologue(b);"
s = s.replace('        return block_prologue(b);\n', '        bool const cov_ok = block_prologue(b); monad_cov::enterable.push_back(cov_ok); return cov_ok;\n', 1)
b = '''        auto const err = rt.add(&contract_main, &code_holder_);
        if (err != asmjit::kErrorOk) {
            fail_with_error(err);
        }
'''
assert s.count(b) == 1
s = s.replace(b, b + '''        monad_cov::base = reinterpret_cast<uint64_t>(contract_main);
        monad_cov::blocks.clear();
        for (auto const &[o, l] : monad_cov::pending) monad_cov::blocks.emplace_back(o, monad_cov::base + code_holder_.labelOffsetFromBase(l));
        monad_cov::text_end = jump_table_label_ ? monad_cov::base + code_holder_.labelOffsetFromBase(jump_table_label_.value()) : monad_cov::base + code_holder_.textSection()->realSize();
        monad_cov::error_addr = monad_cov::base + code_holder_.labelOffsetFromBase(error_label_);
        monad_cov::epilogue_addr = monad_cov::base + code_holder_.labelOffsetFromBase(epilogue_label_);
''')
open(sys.argv[2], 'w').write(s)
print('patched', sys.argv[2], 'prologue-hook', n0)
