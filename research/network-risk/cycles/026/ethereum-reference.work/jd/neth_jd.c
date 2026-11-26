// Port of the jump destination kernels of Nethermind 2.2.2
// (src/Nethermind/Nethermind.Evm/CodeAnalysis/JumpDestinationAnalyzer.cs and JumpDestinationAnalyzer.std.cs)
// to C. The three x86 kernels use the same hardware instructions the .NET JIT emits for the intrinsics
// (AVX-512 VBMI vpermb / vpermi2b, AVX2 and SSSE3 pshufb). The AdvSimd kernel is a software model of TBX and
// ADDP on 16-byte arrays. Each kernel is compared with an independent scalar rule.
// Build: cc -O2 -mavx512f -mavx512bw -mavx512vbmi -mavx2 -mssse3 -msse4.1 neth_jd.c -o neth_jd
// Run:   ./neth_jd <hexfile>...   (argument MUT=k as first arg plants fault k to show the harness detects it)
#include <immintrin.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PUSH1 0x60
#define PUSHx 0x5f
#define JUMPDEST 0x5b
#define PUSH32 0x7f
static int MUT = 0;

static void mark(uint64_t *bm, size_t pos, uint64_t flags) { bm[pos >> 6] |= flags; }

// ProcessJumpDestinationBitmap_Byte (std.cs)
static void byte_scan(size_t pc, uint64_t *bm, const uint8_t *code, size_t len) {
  uint64_t cur = 0; size_t fpos = 0;
  while (pc < len) {
    int op = code[pc];
    if ((unsigned)(op - JUMPDEST) > PUSH32 - JUMPDEST) { pc++; continue; }
    if (op == JUMPDEST) {
      if (((pc ^ fpos) >> 6) != 0 && cur != 0) { mark(bm, fpos, cur); cur = 0; }
      cur |= 1ULL << (pc & 63); fpos = pc; pc++;
    } else if (op >= PUSH1) pc += op - PUSH1 + 2;
    else pc++;
  }
  if (cur) mark(bm, fpos, cur);
}

// ProcessJumpDestinationBitmap_Scalar (std.cs), word at a time
static const uint64_t HB = 0x8080808080808080ULL, LB = 0x7f7f7f7f7f7f7f7fULL, JD = 0x5b5b5b5b5b5b5b5bULL, PK = 0x0002040810204081ULL;
static uint32_t match_bytes(uint64_t v) { uint64_t m = ~(v | ((v & LB) + LB)) & HB; return (uint32_t)((m * PK) >> 56); }
static int first_set_bit(uint8_t v) { int i = 0; if ((v & 0x0f) == 0) { i = 4; v >>= 4; } if ((v & 3) == 0) { i += 2; v >>= 2; } return i + 1 - (v & 1); }
static uint64_t ld64(const uint8_t *p) { uint64_t x; memcpy(&x, p, 8); return x; }
static void word_scan(uint64_t *bm, const uint8_t *code, size_t len) {
  uint64_t cur = 0; size_t fpos = 0, wordEnd = len & ~(size_t)7, pc = 0;
  while (pc < wordEnd) {
    int first = pc & 7; size_t ws = pc; uint64_t ops, rem;
    if (first == 0) { ops = ld64(code + pc); rem = ops; }
    else { ws -= first; ops = ld64(code + ws); rem = ops >> (first * 8); }
    uint64_t phb = ~rem & (rem << 1) & (rem << 2) & HB;
    int end = 8;
    if (phb) {
      int c = (uint8_t)rem;
      if ((unsigned)(c - PUSH1) <= PUSH32 - PUSH1) { pc += c - PUSH1 + 2; continue; }
      end = first + first_set_bit((uint8_t)((phb * PK) >> 56));
    }
    uint64_t jc = ops ^ JD;
    if (((jc - 0x0101010101010101ULL) & ~jc & HB) != 0) {
      uint32_t act = ((1U << end) - 1U) & ~((1U << first) - 1U);
      uint32_t jm = match_bytes(jc) & act;
      if (jm) {
        if (((ws ^ fpos) >> 6) != 0 && cur != 0) { mark(bm, fpos, cur); cur = 0; }
        cur |= (uint64_t)jm << (ws & 63); fpos = ws;
      }
    }
    if (!phb) pc = ws + 8;
    else { int pop = (uint8_t)(ops >> (end * 8)); pc = ws + end + pop - PUSH1 + 2; }
  }
  while (pc < len) {
    int op = code[pc];
    if (op == JUMPDEST) {
      if (((pc ^ fpos) >> 6) != 0 && cur != 0) { mark(bm, fpos, cur); cur = 0; }
      cur |= 1ULL << (pc & 63); fpos = pc; pc++;
    } else if ((unsigned)(op - PUSH1) <= PUSH32 - PUSH1) pc += op - PUSH1 + 2;
    else pc++;
  }
  if (cur) mark(bm, fpos, cur);
}
static int contains_push_byte(uint64_t o) { return (~o & (o << 1) & (o << 2) & HB) != 0; }
static void k_scalar(uint64_t *bm, const uint8_t *code, size_t len) {
  if (len < 64) byte_scan(0, bm, code, len);
  else if (contains_push_byte(ld64(code))) byte_scan(0, bm, code, len);
  else word_scan(bm, code, len);
}

// ---------------- Vector512 (AVX-512 VBMI) ----------------
static const uint64_t EvenLanes = 0x5555555555555555ULL;
static uint64_t push1_data_lanes(uint64_t p) { uint64_t f = p << 1; uint64_t ors = p & ~EvenLanes & ~f; return (EvenLanes ^ ((ors + p) << 1)) & f; }
static uint64_t lzcnt64(uint64_t x) { return x ? (uint64_t)__builtin_clzll(x) : 64; }
static uint64_t push1_carry_out(uint64_t p) { return lzcnt64(~p) & 1; }

static __m512i compose64(__m512i s, __m512i exits) { return _mm512_permutex2var_epi8(s, s, exits); }
static __m512i descend64(__m512i s, __m512i pos, __m512i lanes) {
  __m512i next = _mm512_permutexvar_epi8(pos, s);
  __mmask64 le = _mm512_cmple_epu8_mask(next, lanes);
  return _mm512_mask_blend_epi8(le, pos, next);
}
static __m512i ld512(const uint8_t *p) { return _mm512_loadu_si512((const void *)p); }

static size_t mark_push1_run(uint64_t *bm, const uint8_t *code, size_t len, size_t block, uint64_t carried, uint64_t *carryOut) {
  __m512i jd = _mm512_set1_epi8(JUMPDEST), p1 = _mm512_set1_epi8(PUSH1);
  size_t blocks = len >> 6;
  __m512i a = ld512(code + (block << 6)), b = ld512(code + ((block + 1) << 6));
  __m512i mx = _mm512_max_epi8(a, b);
  for (;;) {
    uint64_t jA = _mm512_cmpeq_epi8_mask(a, jd), jB = _mm512_cmpeq_epi8_mask(b, jd);
    if (_mm512_cmpeq_epi8_mask(mx, p1) == 0) {
      bm[block] = jA & ~carried; bm[block + 1] = jB; carried = 0;
    } else {
      uint64_t pA = _mm512_cmpeq_epi8_mask(a, p1) & ~carried;
      uint64_t pB = _mm512_cmpeq_epi8_mask(b, p1);
      uint64_t cB = push1_carry_out(pA);
      if ((jA | jB) != 0) {
        bm[block] = jA & ~(carried | push1_data_lanes(pA));
        bm[block + 1] = jB & ~(cB | push1_data_lanes(pB & ~cB));
      }
      carried = push1_carry_out(pB == ~0ULL ? pA : pB);
    }
    block += 2;
    if (block + 1 >= blocks) break;
    a = ld512(code + (block << 6)); b = ld512(code + ((block + 1) << 6));
    mx = _mm512_max_epi8(a, b);
    if (_mm512_cmpgt_epi8_mask(mx, p1) != 0) break;
  }
  *carryOut = carried;
  return block;
}

static void k_v512(uint64_t *bm, const uint8_t *code, size_t len) {
  uint8_t idx[64]; for (int i = 0; i < 64; i++) idx[i] = i;
  __m512i lanes = ld512(idx);
  __m512i bs = _mm512_set1_epi8(64);
  __m512i exits = _mm512_add_epi8(lanes, bs);
  __m512i endOff = _mm512_sub_epi8(lanes, _mm512_set1_epi8((char)(PUSHx - 1 + (MUT == 1))));
  __m512i jd = _mm512_set1_epi8(JUMPDEST), px = _mm512_set1_epi8(PUSHx), p1 = _mm512_set1_epi8(PUSH1);
  size_t blocks = len >> 6, block = 0;
  __m512i entry = _mm512_setzero_si512();
  while (block + 1 < blocks) {
    __m512i a = ld512(code + (block << 6)), b = ld512(code + ((block + 1) << 6));
    __m512i mx = _mm512_max_epi8(a, b);
    if (_mm512_cmpgt_epi8_mask(mx, p1) == 0) {
      uint64_t carried = _mm512_cmplt_epu8_mask(lanes, entry);
      if (_mm512_cmpeq_epi8_mask(mx, p1) == 0) {
        for (;;) {
          bm[block] = _mm512_cmpeq_epi8_mask(a, jd) & ~carried;
          bm[block + 1] = _mm512_cmpeq_epi8_mask(b, jd);
          block += 2;
          if (block + 1 >= blocks) break;
          a = ld512(code + (block << 6)); b = ld512(code + ((block + 1) << 6));
          if (_mm512_cmpgt_epi8_mask(_mm512_max_epi8(a, b), px) != 0) break;
          carried = 0;
        }
        entry = _mm512_setzero_si512();
        continue;
      }
      block = mark_push1_run(bm, code, len, block, carried, &carried);
      entry = carried == 0 ? _mm512_setzero_si512() : _mm512_set1_epi8(1);
      continue;
    }
    __m512i a0 = _mm512_add_epi8(_mm512_max_epi8(a, px), endOff), b0 = _mm512_add_epi8(_mm512_max_epi8(b, px), endOff);
    __m512i a1 = compose64(a0, exits), b1 = compose64(b0, exits);
    __m512i a2 = compose64(a1, exits), b2 = compose64(b1, exits);
    __m512i a3 = compose64(a2, exits), b3 = compose64(b2, exits);
    __m512i a4 = compose64(a3, exits), b4 = compose64(b3, exits);
    __m512i a5 = compose64(a4, exits), b5 = compose64(b4, exits);
    __m512i a6 = compose64(a5, exits), b6 = compose64(b5, exits);
    __m512i eA = entry;
    __m512i eB = _mm512_sub_epi8(_mm512_permutexvar_epi8(eA, a6), bs);
    entry = _mm512_sub_epi8(_mm512_permutexvar_epi8(eB, b6), bs);
    uint64_t jA = _mm512_cmpeq_epi8_mask(a, jd), jB = _mm512_cmpeq_epi8_mask(b, jd);
    if (jA) {
      __m512i p = descend64(a5, eA, lanes); p = descend64(a4, p, lanes); p = descend64(a3, p, lanes);
      p = descend64(a2, p, lanes); p = descend64(a1, p, lanes); p = descend64(a0, p, lanes);
      bm[block] = jA & _mm512_cmpeq_epi8_mask(p, lanes);
    }
    if (jB) {
      __m512i p = descend64(b5, eB, lanes); p = descend64(b4, p, lanes); p = descend64(b3, p, lanes);
      p = descend64(b2, p, lanes); p = descend64(b1, p, lanes); p = descend64(b0, p, lanes);
      bm[block + 1] = jB & _mm512_cmpeq_epi8_mask(p, lanes);
    }
    block += 2;
  }
  if (block < blocks) {
    __m512i o = ld512(code + (block << 6));
    __m512i n0 = _mm512_add_epi8(_mm512_max_epi8(o, px), endOff);
    __m512i n1 = compose64(n0, exits), n2 = compose64(n1, exits), n3 = compose64(n2, exits);
    __m512i n4 = compose64(n3, exits), n5 = compose64(n4, exits), n6 = compose64(n5, exits);
    __m512i be = entry;
    entry = _mm512_sub_epi8(_mm512_permutexvar_epi8(be, n6), bs);
    uint64_t j = _mm512_cmpeq_epi8_mask(o, jd);
    if (j) {
      __m512i p = descend64(n5, be, lanes); p = descend64(n4, p, lanes); p = descend64(n3, p, lanes);
      p = descend64(n2, p, lanes); p = descend64(n1, p, lanes); p = descend64(n0, p, lanes);
      bm[block] = j & _mm512_cmpeq_epi8_mask(p, lanes);
    }
  }
  size_t analyzed = blocks << 6;
  size_t pending = (uint8_t)_mm_cvtsi128_si32(_mm512_castsi512_si128(entry));
  if (analyzed + pending < len) byte_scan(pending, bm + blocks, code + analyzed, len - analyzed);
}

// ---------------- Vector256 (AVX2) ----------------
#define BIAS 0x70
static uint8_t s128(__m128i v) { return (uint8_t)_mm_cvtsi128_si32(v); }
static __m256i compose16x2(__m256i s) { return _mm256_max_epu8(_mm256_shuffle_epi8(s, s), s); }
static __m256i descend16x2(__m256i s, __m256i pos, __m256i lanesF, __m256i sign) {
  __m256i next = _mm256_shuffle_epi8(s, pos);
  __m256i passes = _mm256_cmpgt_epi8(_mm256_xor_si256(next, sign), lanesF);
  return _mm256_blendv_epi8(next, pos, passes); // ConditionalSelect(passes, positions, next)
}
static uint32_t jd16x2(__m256i ops, __m128i *entry, __m256i lanes, __m256i endOff, __m256i lanesF, __m256i sign) {
  __m256i px = _mm256_set1_epi8(PUSHx);
  uint32_t jds = (uint32_t)_mm256_movemask_epi8(_mm256_cmpeq_epi8(ops, _mm256_set1_epi8(JUMPDEST)));
  if (_mm256_movemask_epi8(_mm256_cmpgt_epi8(ops, px)) == 0) {
    int carried = s128(*entry) - BIAS;
    *entry = _mm_set1_epi8(BIAS);
    return (uint32_t)(((uint64_t)jds >> carried) << carried);
  }
  __m256i n0 = _mm256_add_epi8(_mm256_max_epi8(ops, px), endOff);
  __m256i n1 = compose16x2(n0), n2 = compose16x2(n1), n3 = compose16x2(n2);
  __m256i ne = _mm256_sub_epi8(compose16x2(n3), _mm256_set1_epi8(16));
  __m128i bsz = _mm_set1_epi8(16);
  __m128i eA = *entry;
  __m128i eB = _mm_max_epu8(_mm_shuffle_epi8(_mm256_castsi256_si128(ne), eA), _mm_sub_epi8(eA, bsz));
  *entry = _mm_max_epu8(_mm_shuffle_epi8(_mm256_extracti128_si256(ne, 1), eB), _mm_sub_epi8(eB, bsz));
  if (jds == 0) return 0;
  __m256i entries = _mm256_set_m128i(eB, eA);
  __m256i p = descend16x2(n3, entries, lanesF, sign);
  p = descend16x2(n2, p, lanesF, sign);
  p = descend16x2(n1, p, lanesF, sign);
  __m256i starts = _mm256_or_si256(_mm256_cmpeq_epi8(p, lanes), _mm256_cmpeq_epi8(_mm256_shuffle_epi8(n0, p), lanes));
  return (uint32_t)_mm256_movemask_epi8(starts) & jds & ~(uint32_t)_mm256_movemask_epi8(entries);
}
static void k_v256(uint64_t *bm, const uint8_t *code, size_t len) {
  uint8_t idx[32]; for (int i = 0; i < 32; i++) idx[i] = (i & 15) + BIAS + (MUT == 2 && i == 7);
  __m256i lanes = _mm256_loadu_si256((const __m256i *)idx);
  __m256i endOff = _mm256_sub_epi8(lanes, _mm256_set1_epi8(PUSHx - 1));
  __m256i sign = _mm256_set1_epi8((char)0x80);
  __m256i lanesF = _mm256_xor_si256(lanes, sign);
  size_t pairs = len / 32, pair = 0;
  __m128i entry = _mm_set1_epi8(BIAS);
  for (; pair + 1 < pairs; pair += 2) {
    uint64_t lo = jd16x2(_mm256_loadu_si256((const __m256i *)(code + pair * 32)), &entry, lanes, endOff, lanesF, sign);
    uint64_t hi = jd16x2(_mm256_loadu_si256((const __m256i *)(code + (pair + 1) * 32)), &entry, lanes, endOff, lanesF, sign);
    bm[pair >> 1] = lo | (hi << 32);
  }
  if (pair < pairs) bm[pair >> 1] = jd16x2(_mm256_loadu_si256((const __m256i *)(code + pair * 32)), &entry, lanes, endOff, lanesF, sign);
  size_t analyzed = pairs * 32, ws = analyzed & ~(size_t)63;
  size_t pending = analyzed - ws + s128(entry) - BIAS;
  if (ws + pending < len) byte_scan(pending, bm + (ws >> 6), code + ws, len - ws);
}

// ---------------- SSSE3 ----------------
static __m128i adv16_x86(__m128i s, __m128i pos) { return _mm_max_epu8(_mm_shuffle_epi8(s, pos), pos); }
static void succ16(__m128i ops, __m128i endOff, __m128i *n0, __m128i *n1, __m128i *n2, __m128i *n3, __m128i *n4) {
  *n0 = _mm_add_epi8(_mm_max_epi8(ops, _mm_set1_epi8(PUSHx)), endOff);
  *n1 = adv16_x86(*n0, *n0); *n2 = adv16_x86(*n1, *n1); *n3 = adv16_x86(*n2, *n2); *n4 = adv16_x86(*n3, *n3);
}
static __m128i next_entry16(__m128i exits, __m128i entry) {
  __m128i b = _mm_set1_epi8(16);
  return _mm_max_epu8(_mm_shuffle_epi8(_mm_sub_epi8(exits, b), entry), _mm_sub_epi8(entry, b));
}
static __m128i descend16_x86(__m128i s, __m128i pos, __m128i lanes) {
  __m128i next = _mm_shuffle_epi8(s, pos);
  __m128i le = _mm_cmpeq_epi8(_mm_min_epu8(next, lanes), next); // unsigned next <= lane
  return _mm_or_si128(_mm_and_si128(le, next), _mm_andnot_si128(le, pos));
}
static uint32_t jd16(__m128i ops, __m128i *entry, __m128i endOff, __m128i lanes) {
  __m128i n0, n1, n2, n3, ex;
  succ16(ops, endOff, &n0, &n1, &n2, &n3, &ex);
  __m128i be = *entry;
  *entry = next_entry16(ex, be);
  __m128i p = descend16_x86(n3, be, lanes); p = descend16_x86(n2, p, lanes); p = descend16_x86(n1, p, lanes);
  __m128i starts = _mm_or_si128(_mm_cmpeq_epi8(p, lanes), _mm_cmpeq_epi8(_mm_shuffle_epi8(n0, p), lanes));
  return (uint32_t)_mm_movemask_epi8(starts) & ~(uint32_t)_mm_movemask_epi8(be);
}
static void k_ssse3(uint64_t *bm, const uint8_t *code, size_t len) {
  uint8_t idx[16]; for (int i = 0; i < 16; i++) idx[i] = i + BIAS;
  __m128i lanes = _mm_loadu_si128((const __m128i *)idx);
  __m128i endOff = _mm_sub_epi8(lanes, _mm_set1_epi8(PUSHx - 1));
  __m128i jd = _mm_set1_epi8(JUMPDEST), px = _mm_set1_epi8(PUSHx);
  __m128i entry = _mm_set1_epi8(BIAS);
  size_t blocks = len >> 6;
  for (size_t block = 0; block < blocks; block++) {
    const uint8_t *r = code + (block << 6);
    __m128i o0 = _mm_loadu_si128((const __m128i *)r), o1 = _mm_loadu_si128((const __m128i *)(r + 16));
    __m128i o2 = _mm_loadu_si128((const __m128i *)(r + 32)), o3 = _mm_loadu_si128((const __m128i *)(r + 48));
    uint64_t jds = (uint64_t)(uint16_t)_mm_movemask_epi8(_mm_cmpeq_epi8(o0, jd)) | ((uint64_t)(uint16_t)_mm_movemask_epi8(_mm_cmpeq_epi8(o1, jd)) << 16) |
                   ((uint64_t)(uint16_t)_mm_movemask_epi8(_mm_cmpeq_epi8(o2, jd)) << 32) | ((uint64_t)(uint16_t)_mm_movemask_epi8(_mm_cmpeq_epi8(o3, jd)) << 48);
    __m128i mx = _mm_max_epi8(_mm_max_epi8(o0, o1), _mm_max_epi8(o2, o3));
    if (_mm_movemask_epi8(_mm_cmpgt_epi8(mx, px)) == 0) {
      if (jds) { int c = s128(entry) - BIAS; bm[block] = (jds >> c) << c; }
      entry = _mm_set1_epi8(BIAS);
      continue;
    }
    if (jds == 0) {
      __m128i n0, n1, n2, n3, ex;
      succ16(o0, endOff, &n0, &n1, &n2, &n3, &ex); entry = next_entry16(ex, entry);
      succ16(o1, endOff, &n0, &n1, &n2, &n3, &ex); entry = next_entry16(ex, entry);
      succ16(o2, endOff, &n0, &n1, &n2, &n3, &ex); entry = next_entry16(ex, entry);
      succ16(o3, endOff, &n0, &n1, &n2, &n3, &ex); entry = next_entry16(ex, entry);
      continue;
    }
    uint64_t st = (uint64_t)jd16(o0, &entry, endOff, lanes);
    st |= (uint64_t)jd16(o1, &entry, endOff, lanes) << 16;
    st |= (uint64_t)jd16(o2, &entry, endOff, lanes) << 32;
    st |= (uint64_t)jd16(o3, &entry, endOff, lanes) << 48;
    bm[block] = st & jds & (MUT == 3 ? ~1ULL : ~0ULL);
  }
  size_t analyzed = blocks << 6, pending = s128(entry) - BIAS;
  if (analyzed + pending < len) byte_scan(pending, bm + blocks, code + analyzed, len - analyzed);
}

// ---------------- AdvSimd (software model of the arm64 instructions) ----------------
typedef struct { uint8_t b[16]; } v16;
static v16 tbx(v16 def, v16 tab, v16 idx) { v16 r; for (int i = 0; i < 16; i++) r.b[i] = idx.b[i] < 16 ? tab.b[idx.b[i]] : def.b[i]; return r; }
static v16 vadd(v16 a, v16 b) { v16 r; for (int i = 0; i < 16; i++) r.b[i] = a.b[i] + b.b[i]; return r; }
static v16 vsub(v16 a, v16 b) { v16 r; for (int i = 0; i < 16; i++) r.b[i] = a.b[i] - b.b[i]; return r; }
static v16 vset(uint8_t x) { v16 r; memset(r.b, x, 16); return r; }
static v16 vmaxs(v16 a, uint8_t x) { v16 r; for (int i = 0; i < 16; i++) r.b[i] = ((int8_t)a.b[i] > (int8_t)x) ? a.b[i] : x; return r; }
static v16 veq(v16 a, v16 b) { v16 r; for (int i = 0; i < 16; i++) r.b[i] = a.b[i] == b.b[i] ? 0xff : 0; return r; }
static v16 vand(v16 a, v16 b) { v16 r; for (int i = 0; i < 16; i++) r.b[i] = a.b[i] & b.b[i]; return r; }
static int vnz(v16 a) { for (int i = 0; i < 16; i++) if (a.b[i]) return 1; return 0; }
static v16 vld(const uint8_t *p) { v16 r; memcpy(r.b, p, 16); return r; }
static v16 addp(v16 a, v16 b) { v16 r; for (int i = 0; i < 8; i++) { r.b[i] = a.b[2 * i] + a.b[2 * i + 1]; r.b[8 + i] = b.b[2 * i] + b.b[2 * i + 1]; } return r; }
static uint64_t to_word(v16 s0, v16 s1, v16 s2, v16 s3) {
  v16 w; for (int i = 0; i < 16; i++) w.b[i] = 1u << (i & 7);
  v16 p01 = addp(vand(s0, w), vand(s1, w)), p23 = addp(vand(s2, w), vand(s3, w));
  v16 q = addp(p01, p23); v16 r = addp(q, q);
  uint64_t x; memcpy(&x, r.b, 8); return x;
}
static v16 adv16_arm(v16 s, v16 pos) { return tbx(pos, s, pos); }
static void succ16_arm(v16 ops, v16 endOff, v16 *n) {
  n[0] = vadd(vmaxs(ops, PUSHx), endOff);
  for (int k = 1; k < 5; k++) n[k] = adv16_arm(n[k - 1], n[k - 1]);
}
static v16 descend16_arm(v16 s, v16 pos, v16 lanes) {
  v16 next = tbx(pos, s, pos), r;
  for (int i = 0; i < 16; i++) r.b[i] = next.b[i] <= lanes.b[i] ? next.b[i] : pos.b[i];
  return r;
}
static v16 starts16(v16 *n, v16 entry, v16 lanes) {
  v16 p = descend16_arm(n[3], entry, lanes); p = descend16_arm(n[2], p, lanes);
  p = descend16_arm(n[1], p, lanes); p = descend16_arm(n[0], p, lanes);
  return veq(p, lanes);
}
static void k_advsimd(uint64_t *bm, const uint8_t *code, size_t len) {
  v16 lanes; for (int i = 0; i < 16; i++) lanes.b[i] = i;
  v16 endOff = vsub(lanes, vset(PUSHx - 1)), bsz = vset(16 + (MUT == 4)), jd = vset(JUMPDEST);
  v16 entry = vset(0);
  size_t blocks = len >> 6;
  for (size_t block = 0; block < blocks; block++) {
    const uint8_t *r = code + (block << 6);
    v16 o[4]; for (int k = 0; k < 4; k++) o[k] = vld(r + 16 * k);
    v16 j[4]; for (int k = 0; k < 4; k++) j[k] = veq(o[k], jd);
    int has = vnz(j[0]) | vnz(j[1]) | vnz(j[2]) | vnz(j[3]);
    int anyPush = 0; for (int k = 0; k < 4; k++) for (int i = 0; i < 16; i++) if ((int8_t)o[k].b[i] > (int8_t)PUSHx) anyPush = 1;
    if (!anyPush) {
      if (has) { int c = entry.b[0]; bm[block] = to_word(j[0], j[1], j[2], j[3]) & (~0ULL << c); }
      entry = vset(0);
      continue;
    }
    v16 n[4][5]; for (int k = 0; k < 4; k++) succ16_arm(o[k], endOff, n[k]);
    v16 e[4]; e[0] = entry;
    for (int k = 1; k < 4; k++) e[k] = vsub(adv16_arm(n[k - 1][4], e[k - 1]), bsz);
    entry = vsub(adv16_arm(n[3][4], e[3]), bsz);
    if (!has) continue;
    v16 s[4]; for (int k = 0; k < 4; k++) s[k] = vand(starts16(n[k], e[k], lanes), j[k]);
    bm[block] = to_word(s[0], s[1], s[2], s[3]);
  }
  size_t analyzed = blocks << 6, pending = entry.b[0];
  if (analyzed + pending < len) byte_scan(pending, bm + blocks, code + analyzed, len - analyzed);
}

// ---------------- harness ----------------
static void ref(uint8_t *want, const uint8_t *c, size_t n) {
  memset(want, 0, n);
  for (size_t pc = 0; pc < n; pc++) { uint8_t op = c[pc]; if (op >= 0x60 && op <= 0x7f) pc += op - 0x5f; else if (op == 0x5b) want[pc] = 1; }
}
typedef void (*kern)(uint64_t *, const uint8_t *, size_t);
static const char *names[] = {"scalar", "vector512", "vector256", "ssse3", "advsimd"};
static kern ks[] = {k_scalar, k_v512, k_v256, k_ssse3, k_advsimd};
static size_t minlen[] = {0, 64, 32, 16, 16};
static long cases[5], bad[5], tail[5];
static uint8_t want[1 << 16];
static void check(const uint8_t *c, size_t n, const char *tag) {
  ref(want, c, n);
  size_t words = (n + 63) / 64; if (words == 0) words = 1;
  uint64_t *bm = calloc(words + 1, 8);
  // kernels read whole vectors only inside [0, n); pad the copy so the byte scanner and loads stay in bounds
  for (int k = 0; k < 5; k++) {
    if (n < minlen[k] || n == 0 || c[0] == 0x00) continue; // dispatch preconditions (code[0]==STOP is not analyzed)
    memset(bm, 0, (words + 1) * 8);
    ks[k](bm, c, n);
    cases[k]++;
    long b = 0;
    for (size_t i = 0; i < n; i++) if ((int)((bm[i >> 6] >> (i & 63)) & 1) != want[i]) { if (bad[k] + b < 5) printf("MISMATCH %s %s len %zu pos %zu want %d\n", names[k], tag, n, i, want[i]); b++; }
    for (size_t i = n; i < words * 64; i++) if ((bm[i >> 6] >> (i & 63)) & 1) tail[k]++;
    if (bm[words]) tail[k]++;
    bad[k] += b;
  }
  free(bm);
}
static uint64_t rs = 26026;
static uint32_t rnd(uint32_t m) { rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17; return (uint32_t)(rs % m); }
static int unhex(int ch) { return ch <= '9' ? ch - '0' : (ch | 32) - 'a' + 10; }
int main(int argc, char **argv) {
  int a = 1;
  if (argc > 1 && strncmp(argv[1], "MUT=", 4) == 0) { MUT = atoi(argv[1] + 4); a = 2; }
  for (; a < argc; a++) {
    FILE *f = fopen(argv[a], "r"); static char buf[1 << 17]; size_t L = fread(buf, 1, sizeof buf, f); fclose(f);
    char *p = buf; while (L && (p[L - 1] == '\n' || p[L - 1] == ' ' || p[L - 1] == '\r')) L--;
    if (L >= 2 && p[0] == '0' && p[1] == 'x') { p += 2; L -= 2; }
    size_t n = L / 2; uint8_t *c = malloc(n);
    for (size_t i = 0; i < n; i++) c[i] = unhex(p[2 * i]) * 16 + unhex(p[2 * i + 1]);
    long jd = 0; ref(want, c, n); for (size_t i = 0; i < n; i++) jd += want[i];
    printf("file %s len %zu jumpdests %ld\n", argv[a], n, jd);
    check(c, n, "file");
    for (size_t k = 1; k < 192; k++) { check(c + k, n - k, "suffix"); check(c, n - k, "prefix"); }
    free(c);
  }
  static const uint8_t alpha[] = {0x5b, 0x5b, 0x60, 0x61, 0x6f, 0x7e, 0x7f, 0x5f, 0x80, 0xff, 0x00, 0x56, 0x57, 0x5a, 0x5c, 0x60, 0x60};
  uint8_t c[1024];
  for (int t = 0; t < 400000; t++) {
    size_t n = rnd(t % 5 == 4 ? 1000 : 300);
    int mode = t % 5;
    for (size_t i = 0; i < n; i++) {
      switch (mode) {
        case 0: c[i] = rnd(256); break;
        case 1: c[i] = alpha[rnd(sizeof alpha)]; break;
        case 2: c[i] = rnd(3) == 0 ? 0x60 + rnd(32) : 0x5b; break;
        case 3: c[i] = 0x5a + rnd(0x28); break;
        default: c[i] = rnd(4) == 0 ? 0x5b : (rnd(8) == 0 ? 0x60 + rnd(32) : 0x60); break; // long PUSH1 runs
      }
    }
    if (n && c[0] == 0) c[0] = 0x5b;
    check(c, n, "rand");
  }
  for (size_t n = 1; n <= 200; n++)
    for (int op = 0x5f; op <= 0x80; op++)
      for (size_t pos = 0; pos < n; pos++) {
        memset(c, 0x5b, n); c[pos] = op; check(c, n, "single");
      }
  // runs of 0x60 of every length at every offset (the PUSH1 carry arithmetic of the 64-byte kernel)
  for (size_t n = 64; n <= 320; n += 64)
    for (size_t run = 1; run <= 200 && run < n; run++)
      for (size_t pos = 0; pos + run <= n; pos += 3) {
        memset(c, 0x5b, n); memset(c + pos, 0x60, run); check(c, n, "run60");
      }
  printf("MUT=%d\n", MUT);
  for (int k = 0; k < 5; k++) printf("%s cases %ld mismatches %ld tailbits %ld\n", names[k], cases[k], bad[k], tail[k]);
  return 0;
}
