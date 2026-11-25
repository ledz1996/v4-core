// Sets the writer order of the instrumented v0.16.5 emitter from the environment before main:
// HXW_MODE (0 map order, 1 permutation index, 2 shuffle) and HXW_K (index or seed); reports at exit.
#include <cstdint>
#include <cstdio>
#include <cstdlib>
extern "C" void hxw_set(int mode, uint64_t perm, uint64_t seed);
extern "C" void hxw_report(FILE *f, char const *tag);
static void at_end() { hxw_report(stderr, "HXW"); }
__attribute__((constructor)) static void hxw_init() {
    char const *m = std::getenv("HXW_MODE"), *k = std::getenv("HXW_K");
    uint64_t const kk = k ? std::strtoull(k, nullptr, 10) : 0;
    hxw_set(m ? std::atoi(m) : 0, kk, kk);
    std::atexit(at_end);
}
