"""Vectors for the holiman/uint256 harness (u256harness.go), run against v1.3.2 (the release every geth-family
client on the list pins) and master de2a038 of 2026-11-22 (unreleased; rewrites Div, Mod, SDiv, SMod, Slt, Sgt,
WriteToSlice and adds udiv/umod with rem5by4, rem4by3, rem3by2). Oracle: Python integers and the reference
semantics of tools/opdiff/evm.py. Seed 29_2026_11_27. Also replays the 21,537 MULMOD/ADDMOD vectors of
cycles/025/stablecoin-l1.work/maxmod.py and maxmod2.py (regenerated from their own seeds).
Usage: python3 u256vectors.py <harness binary> [<harness binary> ...] <out.json> [nRandom]
"""
import sys, os, json, random, subprocess, time
NR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(NR, 'tools', 'opdiff'))
from evm import ref_sdiv, ref_smod, ref_signextend, ref_byte, ref_sar

M = (1 << 256) - 1; SIGN = 1 << 255
def s(x): return x - (1 << 256) if x & SIGN else x


def ref(op, a, b, c):
    if op == 'DIV': return a // b if b else 0
    if op == 'SDIV': return ref_sdiv(a, b)
    if op == 'MOD': return a % b if b else 0
    if op == 'SMOD': return ref_smod(a, b)
    if op == 'ADDMOD': return (a + b) % c if c else 0
    if op == 'MULMOD': return (a * b) % c if c else 0
    if op == 'EXP': return pow(a, b, 1 << 256)
    if op == 'SIGNEXTEND': return ref_signextend(a, b)
    if op == 'LT': return int(a < b)
    if op == 'GT': return int(a > b)
    if op == 'SLT': return int(s(a) < s(b))
    if op == 'SGT': return int(s(a) > s(b))
    if op == 'EQ': return int(a == b)
    if op == 'BYTE': return ref_byte(a, b)
    if op == 'SHL': return (b << a) & M if a < 256 else 0
    if op == 'SHR': return b >> a if a < 256 else 0
    if op == 'SAR': return ref_sar(a, b)
    if op == 'MUL': return (a * b) & M
    if op == 'ADD': return (a + b) & M
    if op == 'SUB': return (a - b) & M
    if op == 'MULDIV': return ((a * b) // c) & M if c else 0
    if op == 'BYTES32': return a
    if op == 'PAD20': return a & ((1 << 160) - 1)
    raise ValueError(op)


def edges():
    E = {0, 1, 2, 3, M, M - 1, SIGN, SIGN - 1, SIGN + 1, 1 << 128, (1 << 128) - 1, (1 << 160) - 1, 1 << 96, 1 << 192, 1 << 64}
    for k in range(0, 256, 1): E.add(1 << k)
    for k in (63, 64, 65, 127, 128, 129, 191, 192, 193):
        E.add((1 << k) - 1); E.add((1 << k) + 1); E.add(M ^ (1 << k)); E.add(M - (1 << k) + 1)
    # TickMath, BitMath, SqrtPriceMath constants and limits
    E |= {4295128739, 1461446703485210103287273052203988822378723970342, 887272, (-887272) & M, 2 ** 96 * 3, 0xfffcb933bd6fad37aa2d162d1a594001}
    return sorted(E)


def gen(n_random, rnd):
    V = []
    E = edges()
    binops = ['DIV', 'SDIV', 'MOD', 'SMOD', 'LT', 'GT', 'SLT', 'SGT', 'EQ', 'MUL', 'ADD', 'SUB', 'EXP']
    # every edge pair for the binary arithmetic and comparisons
    for op in binops:
        for a in E:
            for b in E:
                if op == 'EXP' and b > 300 and rnd.random() < 0.9: continue
                V.append((op, a, b, 0))
    # powers of two and near powers as divisors with random dividends (the new Div fast path and udiv/umod)
    for k in range(256):
        for d in ((1 << k), (1 << k) - 1 if k else 1, (1 << k) + 1, (1 << k) | rnd.getrandbits(max(1, k // 2)), ((1 << k) | 1) if k else 1):
            for _ in range(6):
                x = rnd.getrandbits(rnd.choice([64, 128, 192, 256])) | (1 << rnd.randrange(0, 256))
                for op in ('DIV', 'MOD', 'SDIV', 'SMOD'):
                    V.append((op, x, d, 0)); V.append((op, x, (-d) & M, 0)); V.append((op, (-x) & M, d, 0))
    # divisors by limb count with the top limb normalised or not (s = 0 and s > 0 in umod/udiv)
    for limbs in (1, 2, 3, 4):
        for top in (1, 2, (1 << 63) - 1, 1 << 63, (1 << 64) - 1, None):
            for _ in range(400):
                t = top if top is not None else rnd.getrandbits(64) | 1
                d = (t << (64 * (limbs - 1))) | rnd.getrandbits(64 * (limbs - 1)) if limbs > 1 else t
                x = rnd.getrandbits(256)
                if rnd.random() < 0.3: x = d * rnd.getrandbits(rnd.randrange(1, 200)) + rnd.choice([0, 1, d - 1]) ; x &= M
                for op in ('DIV', 'MOD', 'SDIV', 'SMOD'): V.append((op, x, d, 0))
                V.append(('MULMOD', rnd.getrandbits(256), rnd.getrandbits(256), d))
                V.append(('ADDMOD', rnd.getrandbits(256), rnd.getrandbits(256), d))
                V.append(('MULMOD', x, rnd.getrandbits(64), d))  # product within 256 bits goes through Mod
    # quotients near a limb boundary: x = q*d + r with q = 2^64-1, 2^64, 2^64+1 (one Knuth digit at its limit)
    for _ in range(4000):
        limbs = rnd.choice([2, 3, 4]); d = rnd.getrandbits(64 * limbs - rnd.randrange(0, 63)) | 1
        for q in ((1 << 64) - 1, 1 << 64, (1 << 64) + 1, (1 << 64) - 2, rnd.getrandbits(64)):
            for r in (0, 1, d - 1, d // 2):
                x = q * d + r
                if x <= M:
                    V.append(('DIV', x, d, 0)); V.append(('MOD', x, d, 0))
    # FullMath shapes: mulmod(a, b, not(0)), mulDiv denominators 2^96, 2^128, liquidity sized
    for _ in range(4000):
        a = rnd.getrandbits(rnd.choice([96, 128, 160, 200, 256])); b = rnd.getrandbits(rnd.choice([96, 128, 160, 256]))
        for c in (M, 1 << 96, 1 << 128, rnd.getrandbits(128) | 1, rnd.getrandbits(160) | 1, rnd.getrandbits(256) | 1):
            V.append(('MULMOD', a, b, c)); V.append(('MULDIV', a, b, c))
    # shifts, BYTE and SIGNEXTEND with large and small indices
    idx = list(range(0, 260)) + [M, SIGN, 1 << 64, (1 << 64) + 3, 1 << 128, 1 << 255 | 7]
    for i in idx:
        for _ in range(8):
            v = rnd.choice([rnd.getrandbits(256), rnd.getrandbits(256) | SIGN, rnd.getrandbits(256) & (SIGN - 1), M, SIGN, 1])
            for op in ('SHL', 'SHR', 'SAR', 'BYTE', 'SIGNEXTEND'): V.append((op, i, v, 0))
    # conversions used by MSTORE, RETURN, CALLDATALOAD paths and address handling
    for _ in range(3000):
        v = rnd.getrandbits(rnd.randrange(1, 257))
        V.append(('BYTES32', v, 0, 0)); V.append(('PAD20', v, 0, 0))
    # random
    ops = binops + ['ADDMOD', 'MULMOD', 'MULDIV', 'SHL', 'SHR', 'SAR', 'BYTE', 'SIGNEXTEND']
    for _ in range(n_random):
        op = rnd.choice(ops)
        a, b, c = (rnd.getrandbits(rnd.choice([8, 64, 128, 192, 255, 256])) for _ in range(3))
        if rnd.random() < 0.3: b = (-b) & M
        if op in ('SHL', 'SHR', 'SAR', 'BYTE', 'SIGNEXTEND') and rnd.random() < 0.8: a &= 0x1ff
        V.append((op, a, b, c))
    return V


def maxmod_vectors():
    out = []
    for f in ('maxmod.py', 'maxmod2.py'):
        p = os.path.join(NR, 'cycles', '025', 'stablecoin-l1.work', f)
        g = {'__file__': p, '__name__': 'gen'}
        src = open(p).read().rsplit("\nif __name__", 1)[0]
        exec(compile(src, p, 'exec'), g)
        vs = g['vecs']()
        if isinstance(vs, tuple): vs = vs[0]
        for a, b, n in vs:
            out.append(('MULMOD', a, b, n)); out.append(('ADDMOD', a, b, n)); out.append(('MULMOD', a, b, M)); out.append(('MULDIV', a, b, n))
    return out


if __name__ == '__main__':
    bins = sys.argv[1:-2] if len(sys.argv) > 3 and sys.argv[-1].isdigit() else sys.argv[1:-1]
    out = sys.argv[-2] if sys.argv[-1].isdigit() else sys.argv[-1]
    nr = int(sys.argv[-1]) if sys.argv[-1].isdigit() else 300000
    rnd = random.Random(29_2026_11_27)
    V = gen(nr, rnd); mm = maxmod_vectors(); V += mm
    print('vectors', len(V), 'of which maxmod', len(mm), flush=True)
    inp = ''.join(f'{op} {hex(a)} {hex(b)} {hex(c)}\n' for op, a, b, c in V).encode()
    res = {'seed': 29_2026_11_27, 'vectors': len(V), 'maxmodRecords': len(mm) // 4, 'byOp': {}, 'binaries': {}}
    for op, *_ in V: res['byOp'][op] = res['byOp'].get(op, 0) + 1
    for b in bins:
        t0 = time.time(); r = subprocess.run([b], input=inp, capture_output=True, check=True)
        got = r.stdout.decode().split('\n')[:-1]; assert len(got) == len(V), (len(got), len(V))
        mism = []
        for (op, a, x, c), g in zip(V, got):
            want = ref(op, a, x, c)
            if int(g, 16) != want: mism.append({'op': op, 'a': hex(a), 'b': hex(x), 'c': hex(c), 'got': '0x' + g, 'want': hex(want)})
        res['binaries'][b] = {'mismatches': len(mism), 'records': mism[:2000], 'seconds': round(time.time() - t0, 1)}
        print(b, 'mismatches', len(mism), flush=True)
    json.dump(res, open(out, 'w'), indent=1)
