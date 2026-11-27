// Cycle 31: gcc 13 lacks __builtin_addcll/__builtin_subcll (gcc 14+). Same contract: returns a+b+cin (a-b-bin) modulo
// 2^64 and stores the carry (borrow) out, 0 or 1, through the pointer. Only used for the system-gcc rebuild.
#pragma once
#ifdef __cplusplus
static inline unsigned long long hx31_addc(unsigned long long a, unsigned long long b, unsigned long long c, unsigned long long *co) {
    unsigned __int128 s = (unsigned __int128)a + b + (c ? 1 : 0); *co = (unsigned long long)(s >> 64); return (unsigned long long)s; }
static inline unsigned long long hx31_subc(unsigned long long a, unsigned long long b, unsigned long long c, unsigned long long *bo) {
    unsigned long long d = a - b; unsigned long long b1 = a < b; unsigned long long e = d - (c ? 1 : 0); unsigned long long b2 = d < (c ? 1ull : 0ull);
    *bo = b1 | b2; return e; }
#define __builtin_addcll hx31_addc
#define __builtin_subcll hx31_subc
#endif
