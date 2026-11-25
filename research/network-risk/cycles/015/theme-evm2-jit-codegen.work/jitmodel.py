"""Transcription of the evm2 JIT lowering rules that are not plain calls into the interpreter's
own routines, run against the specification on the battery and targeted vectors.

Sources transcribed (evm2 66687c18 and 35aa3280, identical in these files):
  crates/jit/codegen/src/compiler/translate/mod.rs   SIGNEXTEND 804-821, LT..EQ 823-837,
      ISZERO 838-843, BYTE 848-867, SHL/SHR/SAR 868-875 with the @shift macro 679-686,
      JUMPI condition 1050, dynamic jump target 1135 with u256_to_u64_saturating 2269-2277,
      multi jump 1092-1095.
  crates/jit/codegen/src/compiler/translate/peephole.rs   every rule (DIV, SDIV, MOD, SMOD,
      ADDMOD, MULMOD, EXP with pay_exp_dynamic_gas, SIGNEXTEND, BYTE).
  crates/jit/codegen/src/bytecode/passes/const_fold.rs   try_const_fold rules written in the
      file (SIGNEXTEND, BYTE, SHL, SHR, SAR, DIV/MOD by zero); try_range_fold for every opcode.
  crates/jit/codegen/src/bytecode/passes/block_analysis.rs   AbsValue::range 137-148,
      at_most 160-168, Branch bound 1990-2015.

LLVM semantics modelled: i256 wraparound for add/sub/mul; shl/lshr/ashr by >= 256 give poison;
select with a non-poison condition returns the chosen operand even when the other is poison;
sdiv truncates toward zero, srem takes the dividend's sign; udiv/urem/sdiv/srem by zero and
sdiv/srem of INT_MIN by -1 are undefined and are flagged if reached.

Usage: python3 jitmodel.py <out.json> [--plant NAME]
"""
import sys, os, json, random, itertools
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools', 'opdiff'))
from evm import REF, MASK, SIGN, M, s, u, ref_sdiv, ref_smod, ref_signextend, ref_byte, ref_sar  # noqa: E402
import battery, targeted  # noqa: E402

POISON = object()
PLANT = None


class UB(Exception):
    pass


def P(x):
    return x is POISON


# ---- LLVM i256 ops ---------------------------------------------------------------------
def shl(v, sh):
    if P(v) or P(sh) or sh >= 256: return POISON
    return (v << sh) & MASK


def lshr(v, sh):
    if P(v) or P(sh) or sh >= 256: return POISON
    return v >> sh


def ashr(v, sh):
    if P(v) or P(sh) or sh >= 256: return POISON
    return u(s(v) >> sh)


def select(c, a, b):
    if P(c): return POISON
    return a if c else b


def add(a, b): return POISON if P(a) or P(b) else (a + b) & MASK
def sub(a, b): return POISON if P(a) or P(b) else (a - b) & MASK
def mul(a, b): return POISON if P(a) or P(b) else (a * b) & MASK


def udiv(a, b):
    if b == 0: raise UB('udiv by 0')
    return a // b


def urem(a, b):
    if b == 0: raise UB('urem by 0')
    return a % b


def sdiv(a, b):
    if b == 0 or (a == SIGN and b == MASK): raise UB('sdiv')
    q = abs(s(a)) // abs(s(b))
    return u(-q if (s(a) < 0) != (s(b) < 0) else q)


def srem(a, b):
    if b == 0 or (a == SIGN and b == MASK): raise UB('srem')
    r = abs(s(a)) % abs(s(b))
    return u(-r if s(a) < 0 else r)


def is_pow2(x): return x != 0 and x & (x - 1) == 0


# ---- inline lowerings (translate/mod.rs) -------------------------------------------------
def jit_signextend(ext, x):
    might = ext < {'signextend-guard': 32, 'signextend-30': 30}.get(PLANT, 31)
    shift = sub(248, mul(ext, 8))
    sext = ashr(shl(x, shift), shift)
    return select(might, sext, x)


def jit_byte(index, value):
    in_range = index < (33 if PLANT == 'byte-guard' else 32)
    shift = sub(248, mul(index, 8))
    b = lshr(value, shift)
    b = POISON if P(b) else b & 0xff
    return select(in_range, b, 0)


def jit_shift(kind, sh, value):
    r = {'SHL': shl, 'SHR': lshr, 'SAR': ashr}[kind](value, sh)
    overflow = sh > (256 if PLANT == 'shift-guard' else 255)
    if kind == 'SAR':
        default = MASK if (s(value) < 0 and PLANT != 'sar-default') else 0
    else:
        default = 0
    return select(overflow, default, r)


def jit_cmp(op, a, b):
    return int({'LT': a < b, 'GT': a > b, 'SLT': s(a) < s(b), 'SGT': s(a) > s(b), 'EQ': a == b}[op])


def jit_iszero(a): return int(a == 0)


def jit_jumpi_cond(w): return w != 0  # icmp ne i256 w, 0


def u256_to_u64_saturating(v, bits):
    sentinel = ((1 << bits) - 1) & ((1 << 128) - 1)
    return v & ((1 << 64) - 1) if v <= sentinel else sentinel & ((1 << 64) - 1)


# ---- peepholes (translate/peephole.rs); const operands are given as values or None ---------
INT_MIN = SIGN


def pp_div(a, b, ca, cb):
    if cb == 0: return 0
    if cb == 1: return a
    if cb is not None and is_pow2(cb): return udiv(a, cb)
    if ca == 0: return 0
    return None


def pp_sdiv(a, b, ca, cb):
    if cb == 0: return 0
    if cb == 1: return a
    if cb == MASK: return sub(0, a)
    if cb == INT_MIN: return int(a == INT_MIN)
    if cb is not None and (is_pow2(cb) or is_pow2(u(-cb))): return sdiv(a, cb)
    if ca == 0: return 0
    return None


def pp_mod(a, b, ca, cb):
    if cb in (0, 1): return 0
    if cb is not None and is_pow2(cb): return urem(a, cb)
    if ca == 0: return 0
    return None


def pp_smod(a, b, ca, cb):
    if cb in (0, 1, MASK): return 0
    if cb is not None and (is_pow2(cb) or is_pow2(u(-cb))): return srem(a, cb)
    if ca == 0: return 0
    return None


def pp_addmod(a, b, n, ca, cb, cn):
    if cn in (0, 1): return 0
    if cn is not None and is_pow2(cn): return add(a, b) & (cn - 1)
    if ca == 0 and cb == 0: return 0
    return None


def pp_mulmod(a, b, n, ca, cb, cn):
    if cn in (0, 1): return 0
    if cn is not None and is_pow2(cn):
        return mul(a, b) & ((cn if PLANT == 'mulmod-mask' else cn - 1))
    if ca == 0 or cb == 0: return 0
    return None


def pp_exp(base, e, cbase, ce):
    """Returns (value, dynamic_gas_bytes_charged_inline) or None."""
    if ce is not None:
        if ce == 0: return 1, None
        if ce == 1: return base, None
        if ce == 2: return mul(base, base), None
        return pow(base, ce, M), None  # gas-free builtin Pow (ruint pow)
    if cbase == 0: return select(e == 0, 1, 0), exp_bytes(e)
    if cbase == 1: return 1, exp_bytes(e)
    if cbase == MASK: return select((e & 1) == 0, 1, MASK), exp_bytes(e)
    if cbase is not None and is_pow2(cbase):
        k = (cbase & -cbase).bit_length() - 1
        threshold = -(-256 // k)
        in_range = e < threshold
        shift = e if k == 1 else mul(e, k)
        return select(in_range, shl(1, shift), 0), exp_bytes(e)
    return None


def exp_bytes(e):
    clz = 256 - e.bit_length()
    return ((256 + 7 - clz) & ((1 << 64) - 1)) >> 3


def pp_signextend(ext, x, cext):
    if cext is not None and cext >= 31: return x
    return None


def pp_byte(i, x, ci):
    if ci is not None and ci >= 32: return 0
    return None


# ---- const_fold.rs try_const_fold rules written in that file --------------------------------
def sat_usize(v): return min(v, (1 << 64) - 1)


def cf(op, a, b):
    if op == 'DIV': return a // b if b else 0
    if op == 'MOD': return a % b if b else 0
    if op == 'SIGNEXTEND':
        if a < 31:
            bit_index = 8 * a + 7
            bit = (b >> bit_index) & 1
            mask = (1 << bit_index) - 1
            return (b | (MASK ^ mask)) if bit else (b & mask)
        return b
    if op == 'BYTE':
        i = sat_usize(a)
        return ((b >> (8 * (31 - i))) & 0xff) if i < 32 else 0  # b.byte(31 - i): little endian index
    if op == 'SHL':
        sh = sat_usize(a); return (b << sh) & MASK if sh < 256 else 0
    if op == 'SHR':
        sh = sat_usize(a); return b >> sh if sh < 256 else 0
    if op == 'SAR':
        sh = sat_usize(a)
        if sh < 256: return u(s(b) >> sh)
        return MASK if b >> 255 else 0
    raise KeyError(op)


# ---- try_range_fold (const_fold.rs 213-389) and AbsValue::range ----------------------------
U64 = (1 << 64) - 1


def mask64(v):
    lz = 64 - v.bit_length()
    return U64 >> lz if lz < 64 else 0


def absrange(lo, hi):
    """AbsValue::range: None unless hi < 2^31; a single value becomes a constant."""
    if hi >= 1 << 31 or hi > U64: return None
    return (lo & 0xffffffff, hi)


def range_fold(op, inputs):
    """inputs: list top first; each is ('r', lo, hi) for a range or inline const (< 2^31),
    ('c', value) for a constant that is not inline, or ('t',) for Top. Returns (lo, hi) or None."""
    def bounds(d):
        x = inputs[d]
        if x[0] == 'r': return (x[1], x[2])
        return None

    def konst(d):
        x = inputs[d]
        if x[0] == 'c': return x[1]
        if x[0] == 'r' and x[1] == x[2]: return x[1]
        return None

    def shr(v, sh): return v >> sh if sh < 64 else 0

    def cmp(lt, ge): return (1, 1) if lt else ((0, 0) if ge else (0, 1))

    def need(*xs):
        if any(x is None for x in xs): raise StopIteration
        return xs
    try:
        if op == 'ADD':
            (a_lo, a_hi), (b_lo, b_hi) = need(bounds(0), bounds(1)); r = (a_lo + b_lo, a_hi + b_hi)
        elif op == 'MUL':
            (a_lo, a_hi), (b_lo, b_hi) = need(bounds(0), bounds(1)); r = (a_lo * b_lo, a_hi * b_hi)
        elif op == 'SUB':
            (a_lo, a_hi), (b_lo, b_hi) = need(bounds(0), bounds(1))
            if a_lo < b_hi: return None
            r = (a_lo - b_hi, a_hi - b_lo)
        elif op in ('DIV', 'SDIV'):
            A, B = bounds(0), bounds(1)
            if A and B and B[0] > 0: r = (A[0] // B[1], A[1] // B[0])
            elif A and (op == 'DIV' or B is not None): r = (0, A[1])
            elif A is None and op == 'DIV':
                b = konst(1)
                if b is None: return None
                v = 0 if b == 0 else MASK // b
                if v > U64: return None
                r = (0, v)
            else: return None
        elif op in ('MOD', 'SMOD'):
            A, B, kb = bounds(0), bounds(1), konst(1)
            if op == 'SMOD' and A is None: return None
            if A and B and B[0] > A[1]: r = A
            elif A and B is None and kb is not None and op == 'MOD': r = A
            else:
                c = [x for x in ([A[1]] if A else []) + ([max(B[1] - 1, 0)] if B else [])]
                if not c: return None
                r = (0, min(c))
        elif op in ('ADDMOD', 'MULMOD'):
            A, B, N = bounds(0), bounds(1), bounds(2)
            ab = None
            if A and B: ab = (A[0] + B[0], A[1] + B[1]) if op == 'ADDMOD' else (A[0] * B[0], A[1] * B[1])
            if ab and N and N[0] > ab[1]: r = ab
            else:
                c = ([ab[1]] if ab else []) + ([max(N[1] - 1, 0)] if N else [])
                if not c: return None
                r = (0, min(c))
        elif op == 'EXP':
            (a_lo, a_hi), (b_lo, b_hi) = need(bounds(0), bounds(1))
            def pw(a, b):
                if b > 0xffffffff: return None
                v = a ** b if a < 2 or b < 70 else None
                if v is None or v > U64: return None
                return v
            lo = pw(a_lo, b_lo) if a_lo > 0 else int(b_hi == 0)
            hi = pw(a_hi, b_hi) if a_hi > 0 else int(b_lo == 0)
            if lo is None or hi is None: return None
            r = (lo, hi)
        elif op == 'SIGNEXTEND':
            B = need(bounds(1))[0]
            a_lo = bounds(0)[0] if bounds(0) else 0
            if a_lo < 31 and B[1] >> (8 * min(a_lo, 7) + 7) != 0: return None
            r = B
        elif op in ('LT', 'GT', 'SLT', 'SGT', 'EQ'):
            A, B = bounds(0), bounds(1)
            if A and B:
                (a_lo, a_hi), (b_lo, b_hi) = A, B
                if op in ('LT', 'SLT'): r = cmp(a_hi < b_lo, a_lo >= b_hi)
                elif op in ('GT', 'SGT'): r = cmp(a_lo > b_hi, a_hi <= b_lo)
                else: r = cmp(False, a_hi < b_lo or b_hi < a_lo)
            else: r = (0, 1)
        elif op == 'ISZERO':
            A = bounds(0); r = cmp(A[1] == 0, A[0] > 0) if A else (0, 1)
        elif op == 'AND':
            c = [x[1] for x in (bounds(0), bounds(1)) if x]
            if not c: return None
            r = (0, min(c))
        elif op == 'OR':
            (a_lo, a_hi), (b_lo, b_hi) = need(bounds(0), bounds(1)); r = (max(a_lo, b_lo), mask64(a_hi | b_hi))
        elif op == 'XOR':
            (_, a_hi), (_, b_hi) = need(bounds(0), bounds(1)); r = (0, mask64(a_hi | b_hi))
        elif op == 'NOT':
            return None
        elif op == 'BYTE':
            I = bounds(0)
            i_lo, i_hi = (min(I[0], 32), min(I[1], 32)) if I else (0, 32)
            w = konst(1)
            if w is not None:
                wb = w.to_bytes(32, 'big')
                bs = [wb[i] if i < 32 else 0 for i in range(i_lo, i_hi + 1)]
                r = (min(bs), max(bs))
            else:
                B = bounds(1); r = (0, min(B[1], 255) if B else 255)
        elif op == 'SHL':
            S = need(bounds(0))[0]
            if S[0] >= 256: r = (0, 0)
            elif bounds(1) and S[1] < 32: r = (bounds(1)[0] << S[0], bounds(1)[1] << S[1])
            else: return None
        elif op in ('SHR', 'SAR'):
            s_lo, s_hi = bounds(0) or (0, 256)
            B, kb = bounds(1), konst(1)
            if B: r = (shr(B[0], s_hi), shr(B[1], s_lo))
            elif kb is not None and (op == 'SHR' or not kb >> 255):
                def sh(x): return kb >> x if x < 256 else 0
                lo, hi = sh(s_hi), sh(s_lo)
                if lo > U64 or hi > U64: return None
                r = (lo, hi)
            elif B is None and kb is None and op == 'SHR' and s_lo >= 225:
                r = (0, U64 >> (s_lo - 192) if s_lo < 256 else 0)
            else: return None
        else:
            return None
    except StopIteration:
        return None
    return absrange(*r)


# ---- Branch bound (block_analysis.rs 1990-2015) -------------------------------------------
def branch_bound(tail):
    """tail: instructions before JUMPI, last first, as (name, imm). Returns (bound_taken, depth, bound)."""
    it = iter(tail)
    def dup(x): return int(x[0][3:]) - 1 if x[0].startswith('DUP') else None
    def push(x): return x[1] if x[0] == 'PUSH' and x[1] < 1 << 31 else None
    first = next(it, None)
    if first is None or first[0] != 'PUSH': return None
    zero_taken = False
    test = next(it, None)
    while test is not None and test[0] == 'ISZERO':
        zero_taken = not zero_taken; test = next(it, None)
    if test is None: return None
    if dup(test) is not None: return (zero_taken, dup(test), 0)
    if test[0] not in ('LT', 'GT'): return None
    a, b = next(it, None), next(it, None)
    if a is None or b is None: return None
    if dup(a) is not None and push(b) is not None:
        if dup(a) == 0: return None
        less, depth, c = test[0] == 'LT', dup(a) - 1, push(b)
    else:
        if dup(b) is None or push(a) is None: return None
        less, depth, c = test[0] == 'GT', dup(b), push(a)
    if less:
        if c == 0: return None
        return (not zero_taken, depth, c - (2 if PLANT == 'bound-lt' and c >= 2 else 1))
    return (zero_taken, depth, c)


def run_seq(stack, seq):
    """Concrete execution of DUP/PUSH/LT/GT/ISZERO followed by PUSH target and JUMPI; returns taken."""
    st = list(stack)
    for name, imm in seq:
        if name == 'PUSH': st.append(imm)
        elif name.startswith('DUP'): st.append(st[-int(name[3:])])
        elif name == 'LT': a, b = st.pop(), st.pop(); st.append(int(a < b))
        elif name == 'GT': a, b = st.pop(), st.pop(); st.append(int(a > b))
        elif name == 'ISZERO': st.append(int(st.pop() == 0))
    st.append(0x1234)  # jump target
    tgt, cond = st.pop(), st.pop()
    return cond != 0, st


# ---- the comparison -----------------------------------------------------------------------
def main(out):
    rnd = random.Random(15015)
    V = battery.vectors() + targeted.vectors()
    from evm import keccak  # noqa
    extra = []
    edges = battery.edge_values() + [1 << 64, (1 << 64) + 1, (1 << 64) + 255, 1 << 128, 1 << 200, MASK - 30, MASK - 31, 2 ** 64 - 1,
                                     255, 256, 257, 31, 32, 33, 30, 29, 248]
    for i in edges:
        for x in edges:
            for op in ('SIGNEXTEND', 'BYTE', 'SHL', 'SHR', 'SAR', 'SDIV', 'SMOD', 'DIV', 'MOD', 'EXP', 'LT', 'GT', 'SLT', 'SGT', 'EQ'):
                extra.append((op, i, x, 0))
    pows = [1 << k for k in range(256)] + [u(-(1 << k)) for k in range(256)] + [0, 1, MASK, 3, 10 ** 6, MASK - 1]
    for n in pows:
        for _ in range(12):
            a, b = rnd.getrandbits(256), rnd.getrandbits(rnd.choice((1, 64, 128, 255, 256)))
            for op in ('MULMOD', 'ADDMOD'):
                extra.append((op, a, b, n)); extra.append((op, MASK, MASK, n)); extra.append((op, SIGN, b, n))
            for op in ('DIV', 'SDIV', 'MOD', 'SMOD'):
                extra.append((op, a, n, 0)); extra.append((op, SIGN, n, 0)); extra.append((op, MASK, n, 0)); extra.append((op, s(a) < 0 and a or u(-a), n, 0))
    for k in range(256):
        for e in list(range(0, 260)) + [1 << 64, MASK, rnd.getrandbits(256)]:
            extra.append(('EXP', 1 << k, e, 0))
        for e in (0, 1, 2, 3, MASK, SIGN, rnd.getrandbits(256)):
            extra.append(('EXP', rnd.getrandbits(256), e, 0))
    for e in list(range(0, 600)) + [MASK, SIGN, 1 << 64, (1 << 64) - 1]:
        for bse in (0, 1, MASK):
            extra.append(('EXP', bse, e, 0))
    V = V + extra
    res = {'vectors': len(V), 'checks': 0, 'mismatches': [], 'ub': [], 'plant': PLANT}

    def check(rule, op, a, b, c, got):
        res['checks'] += 1
        want = REF[op](a, b, c)
        if got is POISON or got != want:
            if len(res['mismatches']) < 40:
                res['mismatches'].append({'rule': rule, 'op': op, 'a': hex(a), 'b': hex(b), 'c': hex(c),
                                          'got': 'poison' if got is POISON else hex(got), 'want': hex(want)})
            res.setdefault('mismatchCount', 0); res['mismatchCount'] = res['mismatchCount'] + 1

    for op, a, b, c in V:
        if op not in REF: continue
        try:
            if op == 'SIGNEXTEND':
                check('inline', op, a, b, c, jit_signextend(a, b))
                r = pp_signextend(a, b, a)
                if r is not None: check('peephole', op, a, b, c, r)
                check('constfold', op, a, b, c, cf(op, a, b))
            elif op == 'BYTE':
                check('inline', op, a, b, c, jit_byte(a, b))
                r = pp_byte(a, b, a)
                if r is not None: check('peephole', op, a, b, c, r)
                check('constfold', op, a, b, c, cf(op, a, b))
            elif op in ('SHL', 'SHR', 'SAR'):
                check('inline', op, a, b, c, jit_shift(op, a, b))
                check('constfold', op, a, b, c, cf(op, a, b))
            elif op in ('LT', 'GT', 'SLT', 'SGT', 'EQ'):
                check('inline', op, a, b, c, jit_cmp(op, a, b))
            elif op == 'ISZERO':
                check('inline', op, a, b, c, jit_iszero(a))
            elif op in ('DIV', 'SDIV', 'MOD', 'SMOD'):
                f = {'DIV': pp_div, 'SDIV': pp_sdiv, 'MOD': pp_mod, 'SMOD': pp_smod}[op]
                for ca, cb in ((None, b), (a, None), (a, b)):
                    r = f(a, b, ca, cb)
                    if r is not None: check('peephole', op, a, b, c, r)
                if op in ('DIV', 'MOD'): check('constfold', op, a, b, c, cf(op, a, b))
            elif op in ('ADDMOD', 'MULMOD'):
                f = pp_addmod if op == 'ADDMOD' else pp_mulmod
                for ca, cb, cn in ((None, None, c), (a, None, None), (None, b, None), (a, b, None), (a, b, c)):
                    r = f(a, b, c, ca, cb, cn)
                    if r is not None: check('peephole', op, a, b, c, r)
            elif op == 'EXP':
                for cbase, ce in ((a, None), (None, b), (a, b)):
                    r = pp_exp(a, b, cbase, ce)
                    if r is not None:
                        check('peephole', op, a, b, c, r[0])
                        if r[1] is not None:
                            res['checks'] += 1
                            if r[1] != (b.bit_length() + 7) // 8:
                                res['mismatches'].append({'rule': 'exp-gas', 'e': hex(b), 'got': r[1]})
        except UB as e:
            res['ub'].append({'op': op, 'a': hex(a), 'b': hex(b), 'c': hex(c), 'why': str(e)})

    # JUMPI condition and jump target conversion
    for w in battery.edge_values() + [rnd.getrandbits(256) for _ in range(2000)] + [1 << k for k in range(256)]:
        res['checks'] += 1
        if jit_jumpi_cond(w) != (w != 0): res['mismatches'].append({'rule': 'jumpi', 'w': hex(w)})
        t = u256_to_u64_saturating(w, 64)
        res['checks'] += 1
        # spec: a target >= 2^64 is never a valid pc; the sentinel u64::MAX is not a pc of a <= 24 KiB code either
        if w < 1 << 64 and t != w or w >= 1 << 64 and t != U64:
            res['mismatches'].append({'rule': 'jump-target', 'w': hex(w), 't': hex(t)})
        t63 = u256_to_u64_saturating(w, 63)
        res['checks'] += 1
        if (w < 1 << 63 and t63 != w) or (w >= 1 << 63 and t63 != (1 << 63) - 1):
            res['mismatches'].append({'rule': 'mem-offset', 'w': hex(w), 't': hex(t63)})

    # Range fold soundness: random ranges and constants, every concrete combination sampled
    rf = {'cases': 0, 'unsound': []}
    ops2 = ['ADD', 'MUL', 'SUB', 'DIV', 'SDIV', 'MOD', 'SMOD', 'EXP', 'SIGNEXTEND', 'LT', 'GT', 'SLT', 'SGT', 'EQ', 'ISZERO',
            'AND', 'OR', 'XOR', 'BYTE', 'SHL', 'SHR', 'SAR', 'ADDMOD', 'MULMOD']
    arity = {'ISZERO': 1, 'ADDMOD': 3, 'MULMOD': 3}
    smalls = [0, 1, 2, 3, 7, 8, 30, 31, 32, 33, 63, 64, 192, 224, 225, 248, 255, 256, 257, (1 << 31) - 1, 1 << 16]

    def gen_abs():
        k = rnd.random()
        if k < 0.55:
            lo = rnd.choice(smalls + [rnd.randrange(0, 1 << rnd.choice((3, 8, 16, 31)))])
            lo = min(lo, (1 << 31) - 1)
            hi = min((1 << 31) - 1, lo + rnd.choice((0, 1, 2, 7, 31, 255, rnd.randrange(0, 1 << rnd.choice((4, 12, 31))))))
            return ('r', lo, hi)
        if k < 0.85:
            return ('c', rnd.choice([1 << 31, MASK, SIGN, u(-1), u(-2), (1 << 64) - 1, 1 << 64, 1 << 200, rnd.getrandbits(256),
                                     0x1f0d1e100c1d070f090b19131c1706010e11080a1a141802121b1503160405, (1 << 255) - 1]))
        return ('t',)

    def sample(x):
        if x[0] == 'r':
            return [x[1], x[2], rnd.randint(x[1], x[2]), rnd.randint(x[1], x[2])]
        if x[0] == 'c': return [x[1]]
        return [0, 1, MASK, SIGN, rnd.getrandbits(256), rnd.getrandbits(32), 255, 256, 31]

    for _ in range(60000):
        op = rnd.choice(ops2)
        n = arity.get(op, 2)
        ins = [gen_abs() for _ in range(n)]
        r = range_fold(op, ins)
        if r is None: continue
        lo, hi = r
        for vals in itertools.product(*[sample(x) for x in ins]):
            rf['cases'] += 1
            a = vals[0]; b = vals[1] if n > 1 else 0; c = vals[2] if n > 2 else 0
            want = REF[op](a, b, c)
            bad = not (lo <= want <= hi)
            if PLANT == 'range-mod' and op == 'MOD': bad = not (lo <= want <= max(lo, hi - 1)) if want else bad
            if bad and len(rf['unsound']) < 30:
                rf['unsound'].append({'op': op, 'inputs': [list(map(lambda v: hex(v) if isinstance(v, int) else v, x)) for x in ins],
                                      'range': [lo, hi], 'values': [hex(v) for v in vals], 'result': hex(want)})
    res['rangeFold'] = rf

    # Branch bound soundness
    bb = {'cases': 0, 'unsound': []}
    for _ in range(40000):
        depth = rnd.randrange(0, 6)
        stack = [rnd.choice([rnd.getrandbits(256), rnd.randrange(0, 70), 0, 1, MASK]) for _ in range(8)]
        c = rnd.choice([0, 1, 2, 31, 32, 64, 256, (1 << 31) - 1, rnd.randrange(0, 1 << 31)])
        stack[-1 - depth] = rnd.choice([c - 1 if c else 0, c, c + 1, rnd.randrange(0, 2 * c + 3), rnd.getrandbits(256)])
        x = stack[-1 - depth]
        form = rnd.randrange(3)
        if form == 0: seq = [(f'DUP{depth + 1}', None)]
        elif form == 1: seq = [('PUSH', c), (f'DUP{depth + 2}', None), (rnd.choice(['LT', 'GT']), None)]
        else: seq = [(f'DUP{depth + 1}', None), ('PUSH', c), (rnd.choice(['LT', 'GT']), None)]
        seq += [('ISZERO', None)] * rnd.randrange(0, 3)
        tail = list(reversed(seq + [('PUSH', 0x1234)]))
        bound = branch_bound(tail)
        if bound is None: continue
        taken, st = run_seq(stack, seq)
        bound_taken, d, limit = bound
        bb['cases'] += 1
        if taken == bound_taken and not (st[-1 - d] <= limit):
            if len(bb['unsound']) < 20: bb['unsound'].append({'seq': seq, 'x': hex(x), 'bound': bound})
        if st[-1 - d] != x: bb['unsound'].append({'seq': seq, 'depthMismatch': True})
    res['branchBound'] = bb
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps({k: (v if k not in ('mismatches', 'ub') else len(v)) for k, v in res.items() if k not in ('rangeFold', 'branchBound')}),
          'mismatchCount', res.get('mismatchCount', 0), 'rangeFold', rf['cases'], len(rf['unsound']), 'branchBound', bb['cases'], len(bb['unsound']))


if __name__ == '__main__':
    if '--plant' in sys.argv:
        PLANT = sys.argv[sys.argv.index('--plant') + 1]
    main(sys.argv[1])
