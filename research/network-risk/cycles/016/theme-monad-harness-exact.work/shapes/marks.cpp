// Collects the emitter markers in a file named by HX_MARKS (compile time only).
#include <cstdio>
#include <cstdlib>
static FILE *g_f = nullptr;
extern "C" void hx_mark(char const *s)
{
    static bool init = false;
    if (!init) { init = true; if (char const *p = std::getenv("HX_MARKS")) g_f = std::fopen(p, "w"); }
    if (g_f) { std::fputs(s, g_f); std::fputc('\n', g_f); }
}
