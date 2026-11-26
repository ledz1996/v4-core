// Only the assertion handler remains a stand-in (the real one in category/core/assert.c prints a backtrace
// through boost::stacktrace before abort). Keccak is the real category/crypto/keccak.c + keccak_impl.S.
#include <stdio.h>
#include <stdlib.h>
void monad_assertion_failed(char const *expr, char const *function, char const *file, long line, char const *msg)
{
    fprintf(stderr, "assertion failed: %s in %s at %s:%ld %s\n", expr ? expr : "abort", function, file, line, msg ? msg : "");
    abort();
}
