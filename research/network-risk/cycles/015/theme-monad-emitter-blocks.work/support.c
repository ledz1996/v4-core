// Support symbols for the harness: a plain Keccak-256 in place of Monad's
// OpenSSL-derived assembly (same function is used by interpreter and native
// code, so it cannot separate the two), and an assertion handler.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const uint64_t RC[24] = {
    0x0000000000000001ULL, 0x0000000000008082ULL, 0x800000000000808aULL,
    0x8000000080008000ULL, 0x000000000000808bULL, 0x0000000080000001ULL,
    0x8000000080008081ULL, 0x8000000000008009ULL, 0x000000000000008aULL,
    0x0000000000000088ULL, 0x0000000080008009ULL, 0x000000008000000aULL,
    0x000000008000808bULL, 0x800000000000008bULL, 0x8000000000008089ULL,
    0x8000000000008003ULL, 0x8000000000008002ULL, 0x8000000000000080ULL,
    0x000000000000800aULL, 0x800000008000000aULL, 0x8000000080008081ULL,
    0x8000000000008080ULL, 0x0000000080000001ULL, 0x8000000080008008ULL};
static const int ROT[25] = {0, 1, 62, 28, 27, 36, 44, 6, 55, 20, 3, 10, 43,
                            25, 39, 41, 45, 15, 21, 8, 18, 2, 61, 56, 14};
static uint64_t rol(uint64_t x, int n) { return n ? (x << n) | (x >> (64 - n)) : x; }
static void keccakf(uint64_t s[25])
{
    for (int r = 0; r < 24; r++) {
        uint64_t C[5], D[5], B[25];
        for (int x = 0; x < 5; x++) C[x] = s[x] ^ s[x + 5] ^ s[x + 10] ^ s[x + 15] ^ s[x + 20];
        for (int x = 0; x < 5; x++) D[x] = C[(x + 4) % 5] ^ rol(C[(x + 1) % 5], 1);
        for (int i = 0; i < 25; i++) s[i] ^= D[i % 5];
        for (int x = 0; x < 5; x++)
            for (int y = 0; y < 5; y++)
                B[y + 5 * ((2 * x + 3 * y) % 5)] = rol(s[x + 5 * y], ROT[x + 5 * y]);
        for (int x = 0; x < 5; x++)
            for (int y = 0; y < 5; y++)
                s[x + 5 * y] = B[x + 5 * y] ^ ((~B[(x + 1) % 5 + 5 * y]) & B[(x + 2) % 5 + 5 * y]);
        s[0] ^= RC[r];
    }
}
void monad_keccak256(void const *in, size_t len, uint8_t out[32])
{
    uint64_t s[25];
    memset(s, 0, sizeof s);
    const uint8_t *p = in;
    size_t rate = 136;
    while (len >= rate) {
        for (size_t i = 0; i < rate / 8; i++) { uint64_t w; memcpy(&w, p + 8 * i, 8); s[i] ^= w; }
        keccakf(s); p += rate; len -= rate;
    }
    uint8_t blk[136];
    memset(blk, 0, rate);
    memcpy(blk, p, len);
    blk[len] ^= 0x01;
    blk[rate - 1] ^= 0x80;
    for (size_t i = 0; i < rate / 8; i++) { uint64_t w; memcpy(&w, blk + 8 * i, 8); s[i] ^= w; }
    keccakf(s);
    memcpy(out, s, 32);
}
void monad_assertion_failed(char const *expr, char const *function, char const *file, long line, char const *msg)
{
    fprintf(stderr, "assertion failed: %s in %s at %s:%ld %s\n", expr, function, file, line, msg ? msg : "");
    abort();
}
