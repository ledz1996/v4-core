#!/usr/bin/env python3
"""Fallback for Task 2 and Task 5 of theme-evm2-main-native-run (cycle 34).

The native build of evm2 was refused in this session, so the changed routines of
evm2 e80df9c4 against 7c9f3b6d are transcribed here and run on the vectors of
tools/opdiff/battery.py (seed 20261124) and tools/opdiff/targeted.py (seed 681),
plus constructed zero divisor and full-width divisor vectors (seed 34_2026_11_27).
Each transcription is compared with the reference word of tools/opdiff/evm.py and
with the other revision. Four planted faults are run on the same vectors.

Transcribed (file:line in the downloaded trees under ../dl):
  7c9f3b6d arithmetic.rs:22  div: if b.is_zero() { ZERO } else { a.wrapping_div(b) }
  e80df9c4 arithmetic.rs:22  div: a.checked_div(b).unwrap_or_default()
  7c9f3b6d arithmetic.rs:32  rem: if b.is_zero() { ZERO } else { a.wrapping_rem(b) }
  e80df9c4 arithmetic.rs:32  rem: a.checked_rem(b).unwrap_or_default()
  ruint 1.21.1 div.rs:9-41   checked_div/checked_rem: None for a zero divisor, else self.div/self.rem,
                             which impl_bin_op (macros.rs:11-51) maps to wrapping_div/wrapping_rem.
  ruint 1.21.1 lib.rs:371    Default for Uint is ZERO.
  gas_params.rs:258          EXP byte cost: bit_len().div_ceil(8) (old) and byte_len() (new);
                             ruint bits.rs:330 byte_len() = bit_len().div_ceil(8).
  modexp.rs:169-177          iteration count, old and new.
Usage: python3 -I revdiv.py <outdir>
"""
import sys, os, json, random, hashlib, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
OPD = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'tools', 'opdiff'))
sys.path.insert(0, OPD)
from evm import MASK, SIGN, REF  # noqa: E402
import battery, targeted  # noqa: E402

M = 1 << 256


def s(x): return x - M if x >> 255 else x


# --- revisions -------------------------------------------------------------
def div_old(a, b): return 0 if b == 0 else a // b
def rem_old(a, b): return 0 if b == 0 else a % b


def checked_div(a, b): return None if b == 0 else a // b
def checked_rem(a, b): return None if b == 0 else a % b
def unwrap_or_default(x): return 0 if x is None else x
def div_new(a, b): return unwrap_or_default(checked_div(a, b))
def rem_new(a, b): return unwrap_or_default(checked_rem(a, b))


# --- planted faults on the e80df9c4 form -----------------------------------
def f1_div(a, b): return a if b == 0 else a // b                    # division by zero returns the dividend
def f1_rem(a, b): return a if b == 0 else a % b
def f2_rem(a, b):                                                    # remainder with a signed (truncated) sign rule
    if b == 0: return 0
    sa, sb = s(a), s(b)
    if sa >= 0 and sb > 0: return a % b
    r = abs(sa) % abs(sb)
    return (-r if sa < 0 else r) % M
def f3_div(a, b):                                                    # quotient one too high at a full-width divisor
    if b == 0: return 0
    q = a // b
    return (q + 1) & MASK if (b >> 192) and q else q
def f4_div(a, b): return 0 if b == 0 else (a & ((1 << 192) - 1)) // b   # dividend's high limb dropped
def f4_rem(a, b): return 0 if b == 0 else (a & ((1 << 192) - 1)) % b

VARIANTS = {
    '7c9f3b6d': (div_old, rem_old),
    'e80df9c4': (div_new, rem_new),
    'F1-div-by-zero-returns-dividend': (f1_div, f1_rem),
    'F2-remainder-signed-rule': (div_new, f2_rem),
    'F3-quotient-off-by-one-full-width-divisor': (f3_div, rem_new),
    'F4-dropped-high-limb': (f4_div, f4_rem),
}


def word(op, a, b, c, div, rem):
    if op == 'DIV': return div(a, b)
    if op == 'MOD': return rem(a, b)
    if op == 'DIVUP':  # add(div(a, b), gt(mod(a, b), 0)) as UnsafeMath.divRoundingUp (src/libraries/UnsafeMath.sol:14)
        return (div(a, b) + int(rem(a, b) > 0)) & MASK
    raise KeyError(op)


def ref(op, a, b, c):
    if op == 'DIVUP': return battery.reference(op, a, b, c, b'')
    return REF[op](a, b, c)


def constructed(seed=34_2026_11_27):
    rnd = random.Random(seed); V = []
    E = battery.edge_values()
    for a in E:  # zero divisor
        for op in ('DIV', 'MOD', 'DIVUP'): V.append((op, a, 0, 0))
    for _ in range(20000):  # full-width divisors: top limb nonzero, top bit set or not
        b = rnd.getrandbits(256) | (1 << rnd.randrange(192, 256))
        a = rnd.choice([rnd.getrandbits(256), MASK, b, b - 1, (b + 1) & MASK, (2 * b) & MASK, (2 * b - 1) & MASK, (b * rnd.randrange(1, 1 << 63)) & MASK])
        for op in ('DIV', 'MOD', 'DIVUP'): V.append((op, a & MASK, b & MASK, 0))
    for _ in range(20000):  # 2^64-aligned and limb-boundary divisors with dividends near multiples
        k = rnd.choice((64, 128, 192)); b = (rnd.getrandbits(64) | 1) << rnd.randrange(0, k)
        q = rnd.getrandbits(256 - b.bit_length()) if b.bit_length() < 256 else 1
        for a in (q * b - 1, q * b, q * b + 1):
            for op in ('DIV', 'MOD'): V.append((op, a & MASK, b & MASK, 0))
    return V


def run(name, V):
    out = {}
    for vn, (div, rem) in VARIANTS.items():
        bad = []; n = 0
        for (op, a, b, c) in V:
            if op not in ('DIV', 'MOD', 'DIVUP'): continue
            n += 1
            w, r = word(op, a, b, c, div, rem), ref(op, a, b, c)
            if w != r: bad.append({'op': op, 'a': hex(a), 'b': hex(b), 'got': hex(w), 'want': hex(r)})
        out[vn] = {'cases': n, 'mismatches': len(bad), 'firstMismatches': bad[:20]}
    # old against new, word by word
    d = sum(1 for (op, a, b, c) in V if op in ('DIV', 'MOD', 'DIVUP') and
            word(op, a, b, c, div_old, rem_old) != word(op, a, b, c, div_new, rem_new))
    out['oldVsNewDifferences'] = d
    return out


def exp_gas():
    rnd = random.Random(258); n = 0; bad = 0
    vals = [0, 1, 255, 256, MASK, SIGN] + [1 << k for k in range(256)] + [(1 << k) - 1 for k in range(1, 257)] + [rnd.getrandbits(256) for _ in range(20000)]
    for p in vals:
        bl = p.bit_length(); old = -(-bl // 8); new = -(-bl // 8)  # bits.rs:330 byte_len = bit_len().div_ceil(8)
        n += 1; bad += old != new
    return {'cases': n, 'differences': bad}


def modexp_iter():
    def old(exp_length, highp, multiplier=8):
        if exp_length <= 32 and highp == 0: return 0
        if exp_length <= 32: return highp.bit_length() - 1
        return min(multiplier * (exp_length - 32), (1 << 64) - 1) + max(1, highp.bit_length()) - 1
    def new(exp_length, highp, multiplier=8):
        hb = max(highp.bit_length() - 1, 0)
        if exp_length <= 32: return hb
        return min(multiplier * (exp_length - 32), (1 << 64) - 1) + hb
    rnd = random.Random(169); n = 0; bad = []
    for L in list(range(0, 70)) + [1 << 20, (1 << 61), (1 << 64) - 1]:
        for h in [0, 1, 2, 3, MASK] + [rnd.getrandbits(rnd.randrange(1, 257)) for _ in range(60)]:
            if L <= 32 and h >> (8 * L): continue
            for mult in (8, 16):
                n += 1
                if old(L, h, mult) != new(L, h, mult): bad.append((L, hex(h), mult))
    return {'cases': n, 'differences': len(bad), 'first': bad[:10]}


if __name__ == '__main__':
    out = sys.argv[1]
    res = {'seeds': {'battery': 20261124, 'targeted': 681, 'constructed': 34_2026_11_27, 'expGas': 258, 'modexp': 169}}
    res['battery'] = run('battery', battery.vectors())
    res['targeted'] = run('targeted', targeted.vectors())
    res['constructed'] = run('constructed', constructed())
    res['expByteGas'] = exp_gas()
    res['modexpIterationCount'] = modexp_iter()
    json.dump(res, open(os.path.join(out, 'revdiv.json'), 'w'), indent=1)
    for k in ('battery', 'targeted', 'constructed'):
        print(k, {vn: (v['cases'], v['mismatches']) if isinstance(v, dict) else v for vn, v in res[k].items()})
    print('exp', res['expByteGas'], 'modexp', {k: v for k, v in res['modexpIterationCount'].items() if k != 'first'})
