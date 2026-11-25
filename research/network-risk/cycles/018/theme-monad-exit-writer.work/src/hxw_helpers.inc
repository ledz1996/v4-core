    // ---- hxw instrumentation (cycle 18, theme-monad-exit-writer) ----
    struct HxwStats
    {
        int64_t calls = 0, elems_total = 0, max_elems = 0, max_deps = 0,
                max_dep_count = 0, avx_skipped = 0, avx_clobbered_before_use = 0,
                spills = 0, cycles = 0, max_cycle_len = 0, cycle_elems_total = 0,
                max_cycle_elems = 0, yx_equal = 0, yx_equal_with_cycle = 0,
                offset_below_min = 0, nonzero_after_cycles = 0, bad_final = 0,
                permuted_exhaustive = 0, permuted_shuffle = 0;
        int64_t hist[8] = {}; // number of distinct elements: 1..6, 7..15, >=16
        uint64_t digest = 1469598103934665603ull;
    };
    HxwStats hxw_stats;
    int hxw_mode = 0;
    int hxw_fault = 0;
    uint64_t hxw_perm = 0, hxw_seed = 0;

    struct HxwSim
    {
        int32_t min_delta = 0, top_index = 0;
        std::unordered_map<int64_t, int64_t> mem;
        std::unordered_map<int64_t, int64_t> ymm;
        int64_t mem_get(int64_t off)
        {
            auto it = mem.find(off);
            return it == mem.end() ? -1000000 - off : it->second;
        }
        int64_t ymm_get(int64_t r)
        {
            auto it = ymm.find(r);
            return it == ymm.end() ? -2000000 - r : it->second;
        }
    };

    static void hxw_vmovaps(
        asmjit::x86::Assembler &as, HxwSim &sim, x86::Ymm const &y,
        x86::Mem const &m)
    {
        as.vmovaps(y, m);
        MONAD_ASSERT(m.baseReg() == x86::rbp && m.offset() % 32 == 0);
        sim.ymm[y.id()] = sim.mem_get(m.offset() / 32);
    }

    static void hxw_vmovaps(
        asmjit::x86::Assembler &as, HxwSim &sim, x86::Mem const &m,
        x86::Ymm const &y)
    {
        as.vmovaps(m, y);
        MONAD_ASSERT(m.baseReg() == x86::rbp && m.offset() % 32 == 0);
        sim.mem[m.offset() / 32] = sim.ymm_get(y.id());
    }

    static uint64_t hxw_mix(uint64_t x)
    {
        x += 0x9e3779b97f4a7c15ull;
        x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9ull;
        x = (x ^ (x >> 27)) * 0x94d049bb133111ebull;
        return x ^ (x >> 31);
    }

    static void hxw_permute(std::vector<StackElem *> &v, int32_t)
    {
        uint64_t const call = static_cast<uint64_t>(hxw_stats.calls);
        if (hxw_mode == 0) {
            return;
        }
        std::sort(v.begin(), v.end(), [](StackElem *a, StackElem *b) {
            return *a->stack_indices().begin() < *b->stack_indices().begin();
        });
        size_t const n = v.size();
        if (hxw_mode == 1 && n <= 6) {
            uint64_t f = 1;
            for (size_t i = 2; i <= n; ++i) f *= i;
            uint64_t k = hxw_perm % f;
            // k-th lexicographic permutation of the sorted order
            std::vector<StackElem *> pool = v, outv;
            for (size_t i = n; i >= 1; --i) {
                uint64_t g = 1;
                for (size_t j = 2; j < i; ++j) g *= j;
                size_t const idx = static_cast<size_t>(k / g);
                k %= g;
                outv.push_back(pool[idx]);
                pool.erase(pool.begin() + static_cast<long>(idx));
            }
            v = outv;
            ++hxw_stats.permuted_exhaustive;
            return;
        }
        uint64_t s = hxw_mix(hxw_seed * 0x100000001b3ull + call);
        for (size_t i = n; i > 1; --i) {
            s = hxw_mix(s);
            size_t const j = static_cast<size_t>(s % i);
            std::swap(v[i - 1], v[j]);
        }
        ++hxw_stats.permuted_shuffle;
    }

    static void hxw_note_deps(
        HxwSim &, Stack &stack,
        std::unordered_map<StackElem *, int32_t> const &dep_counts,
        int32_t min_delta, int32_t top_index)
    {
        ++hxw_stats.calls;
        int64_t const n = static_cast<int64_t>(dep_counts.size());
        hxw_stats.elems_total += n;
        if (n > hxw_stats.max_elems) hxw_stats.max_elems = n;
        hxw_stats.hist[n <= 6 ? n : (n <= 15 ? 7 : 0)]++;
        int64_t deps = 0;
        for (auto const &[e, c] : dep_counts) {
            if (c > 0) ++deps;
            if (c > hxw_stats.max_dep_count) hxw_stats.max_dep_count = c;
        }
        if (deps > hxw_stats.max_deps) hxw_stats.max_deps = deps;
        for (int32_t i = min_delta; i <= top_index; ++i) {
            auto const d = stack.get(i);
            if (i != *d->stack_indices().begin()) continue;
            if (!d->stack_offset()) continue;
            int32_t const off = d->stack_offset()->offset;
            if (off > top_index) continue;
            if (stack.get(off).get() == d.get()) continue;
            if (d->avx_reg()) ++hxw_stats.avx_skipped;
        }
    }

    static void
    hxw_check(HxwSim &sim, Stack &stack, int32_t min_delta, int32_t top_index)
    {
        uint64_t h = hxw_stats.digest;
        for (int32_t i = min_delta; i <= top_index; ++i) {
            auto const d = stack.get(i);
            int64_t const want = 1 + (*d->stack_indices().begin() - min_delta);
            int64_t const got = sim.mem_get(i);
            h = (h ^ static_cast<uint64_t>(got + 7 * i)) * 1099511628211ull;
            if (got != want) {
                ++hxw_stats.bad_final;
                std::fprintf(
                    stderr,
                    "HXW BAD call=%ld index=%d want=%ld got=%ld min=%d top=%d\n",
                    (long)hxw_stats.calls, i, (long)want, (long)got, min_delta,
                    top_index);
            }
        }
        hxw_stats.digest = h;
    }
}

extern "C" void hxw_set(int mode, uint64_t perm, uint64_t seed)
{
    using namespace monad::vm::compiler::native;
    hxw_stats = HxwStats{};
    hxw_mode = mode;
    hxw_perm = perm;
    hxw_seed = seed;
    char const *fe = std::getenv("HXW_FAULT");
    hxw_fault = fe ? std::atoi(fe) : 0;
}

extern "C" void hxw_report(FILE *f, char const *tag)
{
    using namespace monad::vm::compiler::native;
    auto const &s = hxw_stats;
    std::fprintf(
        f,
        "%s calls=%ld elems_total=%ld max_elems=%ld max_deps=%ld max_dep_count=%ld "
        "avx_skipped=%ld avx_clobbered_before_use=%ld spills=%ld cycles=%ld "
        "max_cycle_len=%ld cycle_elems_total=%ld max_cycle_elems=%ld yx_equal=%ld "
        "yx_equal_with_cycle=%ld offset_below_min=%ld nonzero_after_cycles=%ld "
        "bad_final=%ld exh=%ld shuf=%ld hist1-6=%ld,%ld,%ld,%ld,%ld,%ld h7-15=%ld h16+=%ld digest=%016lx\n",
        tag, (long)s.calls, (long)s.elems_total, (long)s.max_elems,
        (long)s.max_deps, (long)s.max_dep_count, (long)s.avx_skipped,
        (long)s.avx_clobbered_before_use, (long)s.spills, (long)s.cycles,
        (long)s.max_cycle_len, (long)s.cycle_elems_total,
        (long)s.max_cycle_elems, (long)s.yx_equal, (long)s.yx_equal_with_cycle,
        (long)s.offset_below_min, (long)s.nonzero_after_cycles,
        (long)s.bad_final, (long)s.permuted_exhaustive,
        (long)s.permuted_shuffle, (long)s.hist[1], (long)s.hist[2],
        (long)s.hist[3], (long)s.hist[4], (long)s.hist[5], (long)s.hist[6],
        (long)s.hist[7], (long)s.hist[0], (unsigned long)s.digest);
}

namespace monad::vm::compiler::native
{
