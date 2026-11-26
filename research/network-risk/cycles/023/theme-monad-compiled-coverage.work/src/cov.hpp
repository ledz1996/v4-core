// Native block coverage for the Monad x86 emitter (cycle 23). After the PoolManager is compiled, the code range
// [base, text_end) is disassembled with objdump; every native basic block leader (the start of every IR block,
// every direct branch target inside the range, every instruction after a branch, call or return) gets a one-shot
// INT3. The SIGTRAP handler records the leader, puts the original byte back and resumes at the same address, so
// every instruction runs exactly as emitted; only the first execution of each leader traps.
#pragma once
#include <signal.h>
#include <sys/mman.h>
#include <ucontext.h>
#include <unistd.h>
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <unordered_map>
#include <vector>
namespace monad_cov {
    extern std::vector<std::pair<uint32_t, uint64_t>> blocks;
    extern std::vector<uint8_t> enterable;
    extern uint64_t base, text_end, error_addr, epilogue_addr;
}
namespace cov {
    struct Leader { uint64_t addr; uint8_t orig; uint8_t hit; int evm_block; bool is_block_start; };
    static std::vector<Leader> L;
    static std::unordered_map<uint64_t, uint32_t> idx;
    static uint64_t traps = 0, stray = 0;
    static bool installed = false;
    static void on_trap(int, siginfo_t *, void *uc0)
    {
        auto *uc = (ucontext_t *)uc0;
        uint64_t rip = (uint64_t)uc->uc_mcontext.gregs[REG_RIP] - 1;
        auto it = idx.find(rip);
        if (it == idx.end()) { stray++; std::fprintf(stderr, "stray SIGTRAP at %lx\n", (unsigned long)rip); std::abort(); }
        auto &l = L[it->second];
        *(volatile uint8_t *)rip = l.orig;
        l.hit = 1; traps++;
        uc->uc_mcontext.gregs[REG_RIP] = (greg_t)rip;
    }
    static void install()
    {
        if (installed) return;
        installed = true;
        uint64_t b = monad_cov::base, e = monad_cov::text_end;
        // dump and disassemble
        std::string bin = std::string(std::getenv("HX_COVTMP") ? std::getenv("HX_COVTMP") : "/tmp") + "/cov-code-" + std::to_string(getpid()) + ".bin";
        { FILE *f = std::fopen(bin.c_str(), "wb"); std::fwrite((void *)b, 1, e - b, f); std::fclose(f); }
        char cmd[1024];
        std::snprintf(cmd, sizeof cmd, "objdump -D -b binary -m i386:x86-64 --adjust-vma=0x%lx -w %s", (unsigned long)b, bin.c_str());
        FILE *p = popen(cmd, "r");
        std::vector<uint64_t> ins; std::vector<uint64_t> lead;
        char line[4096]; bool next_is_leader = true;
        while (std::fgets(line, sizeof line, p)) {
            char *c = line; while (*c == ' ') c++;
            char *end; uint64_t a = std::strtoull(c, &end, 16);
            if (end == c || *end != ':' || a < b || a >= e) continue;
            // mnemonic: after the second tab
            char *t1 = std::strchr(end, '\t'); if (!t1) continue; char *t2 = std::strchr(t1 + 1, '\t'); if (!t2) continue;
            std::string mn(t2 + 1); while (!mn.empty() && (mn.back() == '\n')) mn.pop_back();
            ins.push_back(a);
            if (next_is_leader) lead.push_back(a);
            next_is_leader = false;
            for (char const *px : {"notrack ", "bnd ", "rex.W ", "data16 ", "cs ", "ds "}) while (mn.rfind(px, 0) == 0) mn = mn.substr(std::strlen(px));
            if (mn.rfind("(bad)", 0) == 0) { std::fprintf(stderr, "undecodable instruction at %lx\n", (unsigned long)a); std::abort(); }
            std::string op = mn.substr(0, mn.find(' '));
            bool br = op[0] == 'j' || op.rfind("call", 0) == 0 || op.rfind("ret", 0) == 0 || op == "ud2" || op == "int3" || op.rfind("bnd", 0) == 0;
            if (br) {
                next_is_leader = true;
                size_t sp = mn.find_first_of(' ');
                if (sp != std::string::npos && op[0] == 'j') {
                    std::string arg = mn.substr(sp); size_t q = arg.find_first_not_of(' ');
                    if (q != std::string::npos && arg.compare(q, 2, "0x") == 0) {
                        uint64_t tgt = std::strtoull(arg.c_str() + q, nullptr, 16);
                        if (tgt >= b && tgt < e) lead.push_back(tgt);
                    }
                }
            }
        }
        pclose(p); if (!std::getenv("HX_COVKEEP")) std::remove(bin.c_str()); else std::fprintf(stderr, "cov: code kept in %s base %lx\n", bin.c_str(), (unsigned long)b);
        std::sort(ins.begin(), ins.end());
        for (auto const &[o, a] : monad_cov::blocks) lead.push_back(a);
        std::sort(lead.begin(), lead.end()); lead.erase(std::unique(lead.begin(), lead.end()), lead.end());
        // every leader must be an instruction start
        for (auto a : lead) if (!std::binary_search(ins.begin(), ins.end(), a)) { std::fprintf(stderr, "leader %lx is not an instruction start\n", (unsigned long)a); std::abort(); }
        auto const &B = monad_cov::blocks;
        for (auto a : lead) {
            int eb = -1; bool st = false;
            for (int i = (int)B.size() - 1; i >= 0; i--) if (B[i].second <= a) { eb = i; break; }
            for (auto const &x : B) if (x.second == a) st = true;
            L.push_back({a, *(uint8_t *)a, 0, eb, st});
        }
        for (uint32_t i = 0; i < L.size(); i++) idx[L[i].addr] = i;
        static std::vector<uint8_t> altstack(1 << 16);
        stack_t ss{}; ss.ss_sp = altstack.data(); ss.ss_size = altstack.size(); sigaltstack(&ss, nullptr);
        struct sigaction sa{}; sa.sa_sigaction = on_trap; sa.sa_flags = SA_SIGINFO | SA_ONSTACK | SA_NODEFER; sigemptyset(&sa.sa_mask);
        sigaction(SIGTRAP, &sa, nullptr);
        long pg = sysconf(_SC_PAGESIZE);
        uint64_t p0 = b & ~(uint64_t)(pg - 1), p1 = (e + pg - 1) & ~(uint64_t)(pg - 1);
        if (mprotect((void *)p0, p1 - p0, PROT_READ | PROT_WRITE | PROT_EXEC)) { std::perror("mprotect"); std::abort(); }
        for (auto &l : L) *(volatile uint8_t *)l.addr = 0xCC;
        std::fprintf(stderr, "cov: %zu IR blocks, %zu native leaders, %zu instructions, text %lu bytes\n", B.size(), L.size(), ins.size(), (unsigned long)(e - b));
    }
    static void dump()
    {
        char const *out = std::getenv("HX_COVOUT");
        if (!out || !installed) return;
        FILE *f = std::fopen(out, "w");
        std::fprintf(f, "META base=%lx text_end=%lx error=%lx epilogue=%lx traps=%lu\n", (unsigned long)monad_cov::base, (unsigned long)monad_cov::text_end,
                     (unsigned long)monad_cov::error_addr, (unsigned long)monad_cov::epilogue_addr, (unsigned long)traps);
        auto const &B = monad_cov::blocks;
        for (size_t i = 0; i < B.size(); i++)
            std::fprintf(f, "B %zu %u %lx %d\n", i, B[i].first, (unsigned long)(B[i].second - monad_cov::base), i < monad_cov::enterable.size() ? (int)monad_cov::enterable[i] : -1);
        for (auto const &l : L) std::fprintf(f, "L %lx %d %d %d\n", (unsigned long)(l.addr - monad_cov::base), l.evm_block, (int)l.is_block_start, (int)l.hit);
        std::fclose(f);
    }
}
