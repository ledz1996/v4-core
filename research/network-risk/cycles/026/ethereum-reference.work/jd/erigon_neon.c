// Software model of erigon v3.8.1 execution/vm/analysis_arm64.s (jumpdestBitmapNEON) and
// analysis_arm64.go (codeBitmapNEON + markJumpdestsTail from analysis.go), instruction by instruction,
// with AArch64 semantics: TBL gives 0 for an index >= 16, TBX keeps the destination lane, BSL is
// Vd = (Vd & Vn) | (~Vd & Vm), SMAX signed, CMHI unsigned >, UMAX unsigned.
// The two WORD encodings per VECTOR are decoded as SMAX Vd=n, Vn=c, Vm=V20 and CMHI Vd=x, Vn=V17, Vm=n
// (0x4e346406, 0x6e263627, 0x4e34642c, 0x6e2c362d: checked field by field in the run log).
// Build: cc -O2 erigon_neon.c -o erigon_neon ; Run: ./erigon_neon [MUT=k] <hexfile>...
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct { uint8_t b[16]; } v16;
static int MUT = 0;
static v16 tbl(v16 idx, v16 tab) { v16 r; for (int i = 0; i < 16; i++) r.b[i] = idx.b[i] < 16 ? tab.b[idx.b[i]] : 0; return r; }
static void tbx(v16 *d, v16 idx, v16 tab) { for (int i = 0; i < 16; i++) if (idx.b[i] < 16) d->b[i] = tab.b[idx.b[i]]; }
static v16 dup(uint8_t x) { v16 r; memset(r.b, x, 16); return r; }
static v16 V16i, V17be, V18lane, V19bit, V20, V21, V22;

static void vector(v16 c, v16 *ex, v16 *xm, v16 *vv) {
  v16 n, x, v, t;
  for (int i = 0; i < 16; i++) n.b[i] = (int8_t)c.b[i] > (int8_t)V20.b[i] ? c.b[i] : V20.b[i]; // SMAX
  for (int i = 0; i < 16; i++) n.b[i] = n.b[i] + V16i.b[i];                                     // VADD
  for (int i = 0; i < 16; i++) x.b[i] = V17be.b[i] > n.b[i] ? 0xff : 0;                         // CMHI x = V17 > n
  for (int i = 0; i < 16; i++) x.b[i] = (x.b[i] & n.b[i]) | (~x.b[i] & V18lane.b[i]);         // VBSL
  for (int i = 0; i < 16; i++) v.b[i] = c.b[i] == V21.b[i] ? 0xff : 0;                          // VCMEQ
  for (int i = 0; i < 16; i++) v.b[i] &= V19bit.b[i];                                           // VAND
  for (int r = 0; r < 3 - (MUT == 1); r++) {
    t = tbl(x, v); for (int i = 0; i < 16; i++) v.b[i] |= t.b[i];
    x = tbl(x, x);
  }
  *ex = tbl(x, n);
  t = tbl(*ex, *ex);
  for (int i = 0; i < 16; i++) xm->b[i] = t.b[i] > ex->b[i] ? t.b[i] : ex->b[i]; // UMAX
  *vv = v;
}

static int jumpdest_neon(const uint8_t *code, int steps, uint8_t *tab, uint8_t *out) {
  v16 e = dup(0);
  uint8_t *T0 = tab, *T2 = tab + 48, *VA = tab + 96, *VC = tab + 160;
  while (steps--) {
    v16 c0, c1; memcpy(c0.b, code, 16); memcpy(c1.b, code + 16, 16); code += 32;
    v16 ex1, xm1, v1, ex2, xm2, v2;
    vector(c0, &ex1, &xm1, &v1);
    vector(c1, &ex2, &xm2, &v2);
    memcpy(T0, ex1.b, 16); memcpy(T2, ex2.b, 16); memcpy(VA, v1.b, 16); memcpy(VC, v2.b, 16);
    v16 e2 = e; tbx(&e2, e, xm1); for (int i = 0; i < 16; i++) e2.b[i] -= V22.b[i];
    unsigned s = e.b[0], s2 = e2.b[0];
    e = e2; tbx(&e, e2, xm2); for (int i = 0; i < 16; i++) e.b[i] -= V22.b[i];
    unsigned r10 = T0[s], r11 = T2[s2], r12 = VA[s], r13 = VC[s2];
    if (s < 8) { /* r10 kept */ } else { r10 = s; }
    if (!(s < 8)) r12 = 0;
    if (s2 < 8) { } else { r11 = s2; }
    if (!(s2 < 8)) r13 = 0;
    r10 = VA[r10]; r11 = VC[r11];
    uint32_t w = r12 | (r10 << 8) | (r13 << 16) | (r11 << 24);
    memcpy(out, &w, 4); out += 4;
  }
  return e.b[0];
}

static void code_bitmap_neon(const uint8_t *code, size_t len, uint64_t *bits) {
  size_t pc = 0;
  int steps = (int)(len / 32);
  if (steps > 0) { uint8_t tab[224]; memset(tab, 0, sizeof tab); pc = steps * 32 + jumpdest_neon(code, steps, tab, (uint8_t *)bits); }
  for (; pc < len; pc++) {
    uint8_t op = code[pc];
    if ((int8_t)op >= (int8_t)0x60) pc += op - 0x60 + 1;
    else if (op == 0x5b) bits[pc / 64] |= 1ULL << (pc % 64);
  }
}

static uint8_t want[1 << 16];
static void ref(const uint8_t *c, size_t n) { memset(want, 0, n); for (size_t pc = 0; pc < n; pc++) { uint8_t op = c[pc]; if (op >= 0x60 && op <= 0x7f) pc += op - 0x5f; else if (op == 0x5b) want[pc] = 1; } }
static long ncases, nbad, ntail;
static void check(const uint8_t *c, size_t n, const char *tag) {
  ref(c, n);
  size_t words = (n + 63) / 64;
  uint64_t *bm = calloc(words + 1, 8);
  code_bitmap_neon(c, n, bm);
  ncases++;
  for (size_t i = 0; i < n; i++) if ((int)((bm[i >> 6] >> (i & 63)) & 1) != want[i]) { if (nbad < 5) printf("MISMATCH %s len %zu pos %zu want %d\n", tag, n, i, want[i]); nbad++; }
  for (size_t i = n; i < words * 64; i++) if ((bm[i >> 6] >> (i & 63)) & 1) ntail++;
  if (bm[words]) ntail++;
  free(bm);
}
static uint64_t rs = 26027;
static uint32_t rnd(uint32_t m) { rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17; return (uint32_t)(rs % m); }
static int unhex(int ch) { return ch <= '9' ? ch - '0' : (ch | 32) - 'a' + 10; }
int main(int argc, char **argv) {
  uint64_t iota0 = 0xa9a8a7a6a5a4a3a2ULL, iota1 = 0xb1b0afaeadacabaaULL;
  memcpy(V16i.b, &iota0, 8); memcpy(V16i.b + 8, &iota1, 8);
  memset(V17be.b, 8, 8); memset(V17be.b + 8, 16, 8);
  for (int i = 0; i < 16; i++) { V18lane.b[i] = i; V19bit.b[i] = 1u << (i & 7); }
  V20 = dup(0x5f); V21 = dup(0x5b); V22 = dup(16);
  int a = 1;
  if (argc > 1 && strncmp(argv[1], "MUT=", 4) == 0) { MUT = atoi(argv[1] + 4); a = 2; }
  if (MUT == 2) V17be.b[3] = 9;
  for (; a < argc; a++) {
    FILE *f = fopen(argv[a], "r"); static char buf[1 << 17]; size_t L = fread(buf, 1, sizeof buf, f); fclose(f);
    char *p = buf; while (L && (p[L - 1] == '\n' || p[L - 1] == ' ' || p[L - 1] == '\r')) L--;
    if (L >= 2 && p[0] == '0' && p[1] == 'x') { p += 2; L -= 2; }
    size_t n = L / 2; uint8_t *c = malloc(n);
    for (size_t i = 0; i < n; i++) c[i] = unhex(p[2 * i]) * 16 + unhex(p[2 * i + 1]);
    long jd = 0; ref(c, n); for (size_t i = 0; i < n; i++) jd += want[i];
    printf("file %s len %zu jumpdests %ld\n", argv[a], n, jd);
    check(c, n, "file");
    for (size_t k = 1; k < 192; k++) { check(c + k, n - k, "suffix"); check(c, n - k, "prefix"); }
    free(c);
  }
  static const uint8_t alpha[] = {0x5b, 0x5b, 0x60, 0x61, 0x6f, 0x7e, 0x7f, 0x5f, 0x80, 0xff, 0x00, 0x56, 0x57, 0x5a, 0x5c};
  uint8_t c[1024];
  for (int t = 0; t < 400000; t++) {
    size_t n = rnd(300); int mode = t % 4;
    for (size_t i = 0; i < n; i++) switch (mode) {
      case 0: c[i] = rnd(256); break;
      case 1: c[i] = alpha[rnd(sizeof alpha)]; break;
      case 2: c[i] = rnd(3) == 0 ? 0x60 + rnd(32) : 0x5b; break;
      default: c[i] = 0x5a + rnd(0x28);
    }
    check(c, n, "rand");
  }
  for (size_t n = 0; n <= 130; n++)
    for (int op = 0x5f; op <= 0x80; op++)
      for (size_t pos = 0; pos < n; pos++) { memset(c, 0x5b, n); c[pos] = op; check(c, n, "single"); }
  printf("MUT=%d neon cases %ld mismatches %ld tailbits %ld\n", MUT, ncases, nbad, ntail);
  return 0;
}
