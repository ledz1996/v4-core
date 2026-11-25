#!/usr/bin/env python3
"""Instrument Emitter::write_to_final_stack_offsets of monad v0.16.5 (category/vm/compiler/ir/x86/emitter.cpp).

Changes, all inside that one function:
  1. The two loops over std::unordered_map dep_counts iterate a vector `hxw_order` holding the same keys.
     In mode 0 the vector is the map's own iteration order (unchanged behaviour); mode 1 puts the keys in
     lowest-stack-index order and applies the k-th lexicographic permutation (k = HXW_PERM mod n!) when the
     map has at most 6 keys, a seeded Fisher-Yates shuffle otherwise; mode 2 shuffles every block.
  2. Every instruction the function emits (vmovaps load/store, mov_literal_to_ymm, mov_general_reg_to_mem)
     also updates a symbolic machine (memory slot -> symbol, ymm -> symbol). At the end every final stack
     index min_delta..top_index must hold the symbol of the element that owns it.
The emitted instructions are the original ones; only their order follows hxw_order.
usage: patch_writer.py ORIG OUT
"""
import sys, hashlib
src = open(sys.argv[1]).read()
a = src.index('    // Does not update eflags\n    void Emitter::write_to_final_stack_offsets()')
b = src.index('    void Emitter::discharge_deferred_comparison()', a)
body = src[a:b]
orig_body = body

def rep(old, new, count=1):
    global body
    n = body.count(old)
    assert n == count, (old, n)
    body = body.replace(old, new)

# snapshot after the early return
rep("""            MONAD_DEBUG_ASSERT(stack_.missing_spill_count() == 0);
            return;
        }
""", """            MONAD_DEBUG_ASSERT(stack_.missing_spill_count() == 0);
            return;
        }
        HxwSim sim;
        sim.min_delta = min_delta;
        sim.top_index = top_index;
        for (int32_t i = min_delta; i <= top_index; ++i) {
            auto const d = stack_.get(i);
            if (i != *d->stack_indices().begin()) continue;
            int64_t const s = 1 + (i - min_delta);
            if (d->stack_offset()) {
                if (d->stack_offset()->offset < min_delta) ++hxw_stats.offset_below_min;
                sim.mem[d->stack_offset()->offset] = s;
            }
            if (d->avx_reg()) sim.ymm[d->avx_reg()->reg] = s;
        }
""")
rep("""            as_.vmovaps(
                stack_offset_to_mem(*spill_elem->stack_offset()), init_yx1);""",
"""            ++hxw_stats.spills;
            hxw_vmovaps(as_, sim,
                stack_offset_to_mem(*spill_elem->stack_offset()), init_yx1);""")
# order vector after dep_counts is built
rep("""        std::vector<StackElem *> non_dep;
        for (auto const &[e, c] : dep_counts) {
            if (c == 0) {""", """        std::vector<StackElem *> hxw_order;
        for (auto const &[e, c] : dep_counts) {
            hxw_order.push_back(e);
        }
        hxw_permute(hxw_order, min_delta);
        hxw_note_deps(sim, stack_, dep_counts, min_delta, top_index);
        std::vector<StackElem *> non_dep;
        for (StackElem *const e : hxw_order) {
            auto const c = dep_counts[e];
            if (c == 0) {""")
rep("""            if (d->avx_reg()) {
                // Stack element d is located in an AVX register we can use.
                yx1 = avx_reg_to_ymm(*d->avx_reg());
            }""", """            if (d->avx_reg()) {
                // Stack element d is located in an AVX register we can use.
                yx1 = avx_reg_to_ymm(*d->avx_reg());
                if (sim.ymm_get(d->avx_reg()->reg) !=
                    1 + (*d->stack_indices().begin() - min_delta)) {
                    ++hxw_stats.avx_clobbered_before_use;
                }
                if (hxw_fault == 3 && d->stack_offset()) {
                    // planted fault: reread an AVX element from its memory slot,
                    // which the writes of a skipped dependency may have overwritten
                    hxw_vmovaps(as_, sim, yx1, stack_offset_to_mem(*d->stack_offset()));
                }
            }""")
rep("""                    as_.vmovaps(yx1, stack_offset_to_mem(*d->stack_offset()));""",
    """                    hxw_vmovaps(as_, sim, yx1, stack_offset_to_mem(*d->stack_offset()));""")
rep("""                    mov_literal_to_ymm(*d->literal(), yx1);""",
    """                    mov_literal_to_ymm(*d->literal(), yx1);
                    sim.ymm[yx1.id()] = 1 + (*d->stack_indices().begin() - min_delta);""")
rep("""                    mov_general_reg_to_mem(*d->general_reg(), m);""",
    """                    mov_general_reg_to_mem(*d->general_reg(), m);
                    sim.mem[m.offset() / 32] = 1 + (*d->stack_indices().begin() - min_delta);""")
rep("""                        as_.vmovaps(yx1, m);""", """                        hxw_vmovaps(as_, sim, yx1, m);""")
rep("""                    as_.vmovaps(
                        stack_offset_to_mem(StackOffset{*it, PrevLoc::AvxReg}),
                        yx1);""", """                    hxw_vmovaps(as_, sim,
                        stack_offset_to_mem(StackOffset{*it, PrevLoc::AvxReg}),
                        yx1);""")
rep("""        yx1 = init_yx1;
        MONAD_DEBUG_ASSERT(yx1 != yx2);
""", """        yx1 = init_yx1;
        if (hxw_fault == 1) yx2 = yx1; // planted fault: one temporary for cycles
        MONAD_DEBUG_ASSERT(yx1 != yx2);
        if (yx1 == yx2) ++hxw_stats.yx_equal;
        {
            int64_t left = 0;
            for (StackElem *const e : hxw_order) if (dep_counts[e] != 0) ++left;
            hxw_stats.cycle_elems_total += left;
            if (left > hxw_stats.max_cycle_elems) hxw_stats.max_cycle_elems = left;
            if (left > 0 && yx1 == yx2) ++hxw_stats.yx_equal_with_cycle;
        }
""")
rep("""        for (auto const [e, ec] : dep_counts) {
            MONAD_DEBUG_ASSERT(ec >= 0);""", """        for (StackElem *const e : hxw_order) {
            auto const ec = dep_counts[e];
            MONAD_DEBUG_ASSERT(ec >= 0);""")
rep("""            as_.vmovaps(
                yx1, stack_offset_to_mem(*cycle.back()->stack_offset()));""",
    """            ++hxw_stats.cycles;
            if ((int64_t)cycle.size() > hxw_stats.max_cycle_len) hxw_stats.max_cycle_len = (int64_t)cycle.size();
            hxw_vmovaps(as_, sim,
                yx1, stack_offset_to_mem(*cycle.back()->stack_offset()));""")
rep("""                as_.vmovaps(
                    yx2, stack_offset_to_mem(*cycle[k - 1]->stack_offset()));""",
    """                hxw_vmovaps(as_, sim,
                    yx2, stack_offset_to_mem(*cycle[k - 1]->stack_offset()));""")
rep("""                    as_.vmovaps(
                        stack_offset_to_mem(StackOffset{i, PrevLoc::AvxReg}),
                        yx1);""", """                    hxw_vmovaps(as_, sim,
                        stack_offset_to_mem(StackOffset{i, PrevLoc::AvxReg}),
                        yx1);""")
rep("""                as_.vmovaps(
                    stack_offset_to_mem(StackOffset{i, PrevLoc::AvxReg}), yx1);""",
    """                hxw_vmovaps(as_, sim,
                    stack_offset_to_mem(StackOffset{i, PrevLoc::AvxReg}), yx1);""")
rep("""        if (spill_elem != nullptr) {
            // Reset the state change""", """        {
            int64_t left = 0;
            for (StackElem *const e : hxw_order) if (dep_counts[e] != 0) ++left;
            hxw_stats.nonzero_after_cycles += left;
        }
        hxw_check(sim, stack_, min_delta, top_index);
        if (spill_elem != nullptr) {
            // Reset the state change""")
assert 'as_.' not in body.replace('as_.vmovaps(y, m)', ''), [l for l in body.splitlines() if 'as_.' in l]

helpers = open(sys.argv[0].replace('patch_writer.py', 'hxw_helpers.inc')).read()
out = src[:a] + helpers + body + src[b:]
open(sys.argv[2], 'w').write(out)
print('orig writer sha256', hashlib.sha256(orig_body.encode()).hexdigest(), 'lines', orig_body.count('\n'))
