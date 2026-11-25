# Writes instrumented copies of Monad's x86.cpp (native: per-pc execution counter and, with HX_CAP,
# capture of the value an instruction leaves on top of the stack) and of the interpreter's
# instruction_table.hpp (a hook after every instruction that records the stack top at chosen pcs).
# The emitter itself (emitter.cpp) is not changed. Usage: patch.py MONADDIR OUTDIR
import sys, os, re
M, O = sys.argv[1], sys.argv[2]
x = open(os.path.join(M, 'category/vm/compiler/ir/x86.cpp')).read()
pre = r'''
#include <asmjit/x86.h>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <format>
#include <functional>
#include <limits>
#include <list>
#include <map>
#include <memory>
#include <optional>
#include <set>
#include <span>
#include <string>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <variant>
#include <vector>
#include <category/core/assert.h>
#include <category/core/likely.h>
#include <category/vm/compiler/ir/basic_blocks.hpp>
#include <category/vm/compiler/ir/instruction.hpp>
#include <category/vm/compiler/types.hpp>
#include <category/vm/evm/traits.hpp>
#include <category/vm/runtime/types.hpp>
#define private public
#define protected public
#include <category/vm/compiler/ir/x86/emitter.hpp>
#undef private
#undef protected
extern "C" uint64_t hx_counts[64];
extern "C" uint64_t hx_save;
extern "C" void hx_cap_impl(uint64_t pc, monad::uint256_t const *x);
namespace hxp {
    inline int slot_of(uint32_t pc) {
        static std::vector<uint32_t> pcs = [] {
            std::vector<uint32_t> v; char const *s = std::getenv("HX_COUNT_PCS");
            if (s) { char *e; while (*s) { v.push_back((uint32_t)std::strtoul(s, &e, 10)); s = *e ? e + 1 : e; } }
            return v; }();
        for (size_t i = 0; i < pcs.size(); i++) if (pcs[i] == pc) return (int)i;
        return -1;
    }
    inline bool cap_at(uint32_t pc) {
        static std::vector<uint32_t> pcs = [] {
            std::vector<uint32_t> v; char const *s = std::getenv("HX_CAP_PCS");
            if (s) { char *e; while (*s) { v.push_back((uint32_t)std::strtoul(s, &e, 10)); s = *e ? e + 1 : e; } }
            return v; }();
        for (auto p : pcs) if (p == pc) return true;
        return false;
    }
    using namespace monad::vm::compiler::native;
    namespace x86 = asmjit::x86;
    // execution counter: rax is saved and restored, mov and lea leave the flags alone,
    // nothing on the virtual stack changes
    inline void before(Emitter &e, uint32_t pc) {
        int s = slot_of(pc); if (s < 0) return;
        e.as_.mov(x86::ptr_abs((uint64_t)&hx_save, 8), x86::rax);
        e.as_.mov(x86::rax, x86::ptr_abs((uint64_t)&hx_counts[s], 8));
        e.as_.lea(x86::rax, x86::qword_ptr(x86::rax, 1));
        e.as_.mov(x86::ptr_abs((uint64_t)&hx_counts[s], 8), x86::rax);
        e.as_.mov(x86::rax, x86::ptr_abs((uint64_t)&hx_save, 8));
    }

    // planted fault (HX_FAULT_PC): after the site's instruction, change its result where it lives
    inline void fault(Emitter &e, uint32_t pc) {
        static long fpc = std::getenv("HX_FAULT_PC") ? std::strtol(std::getenv("HX_FAULT_PC"), nullptr, 10) : -1;
        if ((long)pc != fpc) return;
        e.discharge_deferred_comparison();
        auto const e1 = e.stack_.get(e.stack_.top_index());
        auto on_q = [&](auto const &q, int limb) {
            switch (pc) {
            case 22378: if (limb == 1) e.as_.btr(q, 63); break;                 // bit 127 of the remainder (width 127)
            case 22639: if (limb == 1) e.as_.btr(q, 31); break;                 // bit 95 of the remainder (width 95)
            case 15519: if (limb == 3) e.as_.mov(q, 0); break;                  // no sign fill in the top word
            case 16642: if (limb >= 1) e.as_.and_(q, -8); break;                // carries between words lost
            case 12232: if (limb == 0) e.as_.and_(q, -256); break;              // last byte of the word lost
            }
        };
        if (e1->general_reg()) { auto &g = e.general_reg_to_gpq256(*e1->general_reg()); for (int i = 0; i < 4; i++) on_q(g[i], i); }
        if (e1->stack_offset()) for (int i = 0; i < 4; i++) on_q(x86::qword_ptr(x86::rbp, e1->stack_offset()->offset * 32 + 8 * i), i);
        if (e1->avx_reg()) {
            monad::uint256_t m = ~monad::uint256_t{0};
            if (pc == 12232) m = ~monad::uint256_t{255};
            if (pc == 22378) m = ~(monad::uint256_t{1} << 127);
            if (pc == 22639) m = ~(monad::uint256_t{1} << 95);
            if (pc == 15519) m = ~(~monad::uint256_t{0} << 192);
            if (pc == 16642) m = ~((monad::uint256_t{7} << 64) | (monad::uint256_t{7} << 128) | (monad::uint256_t{7} << 192));
            auto y = x86::Ymm(e1->avx_reg()->reg);
            e.as_.vpand(y, y, e.rodata_.add32(m));
        }
    }
    // capture of the result: as Emitter::runtime_print_top1, after the instruction has been emitted
    inline void after(Emitter &e, uint32_t pc) {
        if (!cap_at(pc)) return;
        auto const fn_mem = e.rodata_.add8(reinterpret_cast<uint64_t>(&hx_cap_impl));
        e.discharge_deferred_comparison();
        e.spill_caller_save_regs(true);
        e.as_.mov(x86::rdi, (uint64_t)pc);
        auto const e1 = e.stack_.get(e.stack_.top_index());
        if (!e1->stack_offset() && !e1->literal()) e.mov_stack_elem_to_stack_offset(e1);
        if (e1->stack_offset().has_value()) e.as_.lea(x86::rsi, x86::qword_ptr(x86::rbp, e1->stack_offset().value().offset * 32));
        else { auto const m = e.rodata_.add_literal(e1->literal().value()); e.as_.lea(x86::rsi, m); }
        e.as_.vzeroupper();
        e.as_.call(fn_mem);
    }
}
'''
x = pre + x
old = 'emit_instr<traits>(emit, instr, remaining_base_gas);'
assert x.count(old) == 1
x = x.replace(old, 'hxp::before(emit, (uint32_t)instr.pc());\n            ' + old + '\n            hxp::fault(emit, (uint32_t)instr.pc());\n            hxp::after(emit, (uint32_t)instr.pc());')
os.makedirs(O, exist_ok=True)
open(os.path.join(O, 'x86.cpp'), 'w').write(x)
t = open(os.path.join(M, 'category/vm/interpreter/instruction_table.hpp')).read()
decl = '\nnamespace monad::vm::interpreter { void hx_step(uint8_t const *code, uint8_t const *ip, void const *top); }\n'
i = t.index('#define MONAD_VM_NEXT(OP)')
t = t[:i] + decl + t[i:]
n0 = t.count('        if constexpr (debug_enabled) {                                         \\\n            trace(analysis, gas_remaining, instr_ptr);')
t = t.replace('        if constexpr (debug_enabled) {                                         \\\n            trace(analysis, gas_remaining, instr_ptr);',
              '        ::monad::vm::interpreter::hx_step(analysis.code(), instr_ptr, &((stack_top + delta)[0])); \\\n        if constexpr (debug_enabled) {                                         \\\n            trace(analysis, gas_remaining, instr_ptr);')
assert n0 == 2, n0
d = os.path.join(O, 'inc/category/vm/interpreter'); os.makedirs(d, exist_ok=True)
open(os.path.join(d, 'instruction_table.hpp'), 'w').write(t)
print('ok', O)
