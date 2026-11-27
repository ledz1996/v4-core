"""Cycle 34 Task 4 (L-1253): the cycle 31 hook plus StackElem::touched_memory_size_ per element ("tm") and the
Emitter limb table gpq256_regs_ ("gpq", register ids of the four limbs of each of the three rows) at every state.
Cycle 31 text follows. Cycle 31 Task 1: make src/x86_hook.cpp from src/x86_orig.cpp (category/vm/compiler/ir/x86.cpp of monad v0.16.7, the
copy cycle 23 fetched). Adds one read-only hook that writes the emitter's virtual stack, as JSON lines, to the file
named by HX_STATELOG: at entry to each compiled block (after begin_new_block), before each instruction's emit call
and before the terminator's emit call. Private members are read through pointers to members formed by explicit
template instantiation, so no access specifier or layout changes. The hook reads fields only and calls no Stack
method that changes state."""
import sys, os
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C31 = '/home/user/v4-core/research/network-risk/cycles/031/theme-monad-gcc-real-states.work'
s = open(os.path.join(C31, 'src/x86_orig.cpp')).read()
HOOK = r'''
#include <cstdio>
#include <cstdlib>
#include <set>
#include <queue>
// ---- cycle 31 state hook (read only) ----
namespace hx31 {
using namespace monad::vm::compiler::native;
template <typename Tag, typename Tag::type M> struct Rob { friend typename Tag::type get(Tag) { return M; } };
#define HX31_ROB(NAME, CLS, TYPE, MEM) struct NAME { using type = TYPE CLS::*; friend type get(NAME); }; \
    template struct Rob<NAME, &CLS::MEM>;
HX31_ROB(S_top, Stack, int32_t, top_index_)
HX31_ROB(S_min, Stack, int32_t, min_delta_)
HX31_ROB(S_max, Stack, int32_t, max_delta_)
HX31_ROB(S_delta, Stack, int32_t, delta_)
HX31_ROB(S_avail, Stack, std::set<int32_t>, available_stack_offsets_)
HX31_ROB(S_favx, Stack, AvxRegQueue, free_avx_regs_)
HX31_ROB(S_fgen, Stack, GeneralRegQueue, free_general_regs_)
HX31_ROB(S_neg, Stack, std::vector<StackElemRef>, negative_elems_)
HX31_ROB(S_pos, Stack, std::vector<StackElemRef>, positive_elems_)
HX31_ROB(S_dc, Stack, DeferredComparison, deferred_comparison_)
using AvxArr = std::array<StackElem *, AVX_REG_COUNT>;
using GenArr = std::array<StackElem *, GENERAL_REG_COUNT>;
HX31_ROB(S_avxe, Stack, AvxArr, avx_reg_stack_elems_)
HX31_ROB(S_gene, Stack, GenArr, general_reg_stack_elems_)
HX31_ROB(E_ra, StackElem, uint32_t, reserve_avx_reg_count_)
HX31_ROB(E_rg, StackElem, uint32_t, reserve_general_reg_count_)
HX31_ROB(D_cmp, DeferredComparison, Comparison, comparison_)
using GpqArr = std::array<Emitter::Gpq256, 3>;
HX31_ROB(Em_gpq, Emitter, GpqArr, gpq256_regs_)
template <typename Q> struct QA : Q { static auto const &c_of(Q const &q) { return q.*(&QA::c); } };
static FILE *out() {
    static FILE *f = nullptr; static bool tried = false;
    if (!tried) { tried = true; if (char const *p = std::getenv("HX_STATELOG")) f = std::fopen(p, "w"); }
    return f;
}
static void elem(FILE *f, int idx, StackElemRef const &r) {
    if (!r) { std::fprintf(f, "{\"i\":%d,\"null\":1}", idx); return; }
    StackElem const &e = *r;
    std::fprintf(f, "{\"i\":%d,\"id\":\"%p\"", idx, (void const *)&e);
    if (e.stack_offset()) std::fprintf(f, ",\"so\":[%d,%d]", e.stack_offset()->offset, (int)e.stack_offset()->moved_from);
    if (e.avx_reg()) std::fprintf(f, ",\"avx\":%d", e.avx_reg()->reg);
    if (e.general_reg()) std::fprintf(f, ",\"gen\":%d", e.general_reg()->reg);
    if (e.literal()) { auto const &w = e.literal()->value.as_words();
        std::fprintf(f, ",\"lit\":\"%016lx%016lx%016lx%016lx\"", w[3], w[2], w[1], w[0]); }
    std::fprintf(f, ",\"ix\":[");
    bool first = true; for (int32_t k : e.stack_indices()) { std::fprintf(f, first ? "%d" : ",%d", k); first = false; }
    std::fprintf(f, "],\"rv\":[%u,%u],\"tm\":%d}", e.*get(E_ra{}), e.*get(E_rg{}), (int)e.touched_memory_size());
}
static void dump(Emitter &emit, char const *what, uint32_t block_off, int64_t pc, int op) {
    FILE *f = out(); if (!f) return;
    Stack &s = emit.get_stack();
    auto const &neg = s.*get(S_neg{}); auto const &pos = s.*get(S_pos{});
    int32_t top = s.*get(S_top{});
    std::fprintf(f, "{\"w\":\"%s\",\"b\":%u,\"pc\":%ld,\"op\":%d,\"top\":%d,\"min\":%d,\"max\":%d,\"delta\":%d,\"nneg\":%zu,\"npos\":%zu",
        what, block_off, (long)pc, op, top, s.*get(S_min{}), s.*get(S_max{}), s.*get(S_delta{}), neg.size(), pos.size());
    std::fprintf(f, ",\"avail\":["); bool first = true;
    for (int32_t k : s.*get(S_avail{})) { std::fprintf(f, first ? "%d" : ",%d", k); first = false; }
    std::fprintf(f, "],\"fgen\":["); first = true;
    for (auto const &g : QA<GeneralRegQueue>::c_of(s.*get(S_fgen{}))) { std::fprintf(f, first ? "%d" : ",%d", g.reg); first = false; }
    std::fprintf(f, "],\"favx\":["); first = true;
    for (auto const &g : QA<AvxRegQueue>::c_of(s.*get(S_favx{}))) { std::fprintf(f, first ? "%d" : ",%d", g.reg); first = false; }
    std::fprintf(f, "],\"genowner\":["); first = true;
    for (auto *p : s.*get(S_gene{})) { std::fprintf(f, first ? "\"%p\"" : ",\"%p\"", (void *)p); first = false; }
    std::fprintf(f, "],\"avxowner\":["); first = true;
    for (auto *p : s.*get(S_avxe{})) { std::fprintf(f, first ? "\"%p\"" : ",\"%p\"", (void *)p); first = false; }
    auto const &dc = s.*get(S_dc{});
    std::fprintf(f, "],\"dc\":[\"%p\",\"%p\",%d]", (void *)dc.stack_elem, (void *)dc.negated_stack_elem, (int)(dc.*get(D_cmp{})));
    std::fprintf(f, ",\"gpq\":[");
    { bool fr = true; for (auto const &row : emit.*get(Em_gpq{})) { std::fprintf(f, fr ? "[" : ",["); fr = false;
        bool fl = true; for (auto const &r : row) { std::fprintf(f, fl ? "%u" : ",%u", (unsigned)r.id()); fl = false; } std::fputc(']', f); } }
    std::fprintf(f, "]");
    std::fprintf(f, ",\"elems\":[");
    first = true;
    for (int32_t i = -(int32_t)neg.size(); i <= top; ++i) {
        if (!first) std::fputc(',', f); first = false;
        if (i < 0) elem(f, i, neg[(size_t)(-i - 1)]);
        else if ((size_t)i < pos.size()) elem(f, i, pos[(size_t)i]);
        else std::fprintf(f, "{\"i\":%d,\"absent\":1}", i);
    }
    std::fprintf(f, "]}\n");
}
}
// ---- end hook ----
'''
HOOK = HOOK.replace(' BOOST_PP_EMPTY()', '')
anchor = 'namespace\n{\n    using monad::Traits;'
assert s.count(anchor) == 1
s = s.replace(anchor, HOOK + anchor)
old = '''            emit_instr<traits>(emit, instr, remaining_base_gas);'''
assert s.count(old) == 1
s = s.replace(old, '''            hx31::dump(emit, "i", (uint32_t)block.offset, (int64_t)instr.pc(), (int)instr.opcode());
''' + old)
old = '''                emit_terminator<traits>(emit, ir, block);'''
assert s.count(old) == 1
s = s.replace(old, '''                hx31::dump(emit, "t", (uint32_t)block.offset, (int64_t)terminator_pc(ir, block), 1000 + (int)block.terminator);
''' + old)
old = '''            if (can_enter_block) {
                int64_t const base_gas = block_base_gas(block);'''
assert s.count(old) == 1
s = s.replace(old, '''            if (can_enter_block) {
                hx31::dump(emit, "e", (uint32_t)block.offset, -1, -1);
                int64_t const base_gas = block_base_gas(block);''')
open(os.path.join(W, 'src/x86_hook.cpp'), 'w').write(s)
print('ok')
