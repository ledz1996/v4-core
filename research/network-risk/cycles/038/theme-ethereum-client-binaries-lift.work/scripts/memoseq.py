"""The MULMOD memo of bor's develop branch (core/vm/mulmod_memo.go, fetched to dl/src/bor-develop-mulmod_memo.go) is
not in the tagged v2.11.2 binary. This script runs the memo's logic in Python on top of the two library routines it
calls, taken from the shipped bor v2.11.2 binary and run in the model: uint256.Reciprocal(m) on a miss and
(*Int).MulModWithReciprocal(z, x, y, m, mu) with z aliasing m, as the memo calls it. The memo compares the whole
modulus (mm.mod != *z); fault 'memo3' compares only limbs 0..2, as the plan's planted memo fault.
Sequences (seed 31_0731_08): reuse one modulus, alternate two moduli, change one limb of the modulus between calls,
FullMath shapes (modulus 2^256-1 then the denominator), and moduli with a zero top limb (stock path).
Reciprocal returns [5]uint64 on the stack at entry SP+8 on both architectures (arrays are not register-assigned).
usage: python3 -I memoseq.py <target> <steps> <out.json> [none|memo3]"""
import json, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import goshim as G, targets
from models import Stop, SP_TOP

TGT, N, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]
FAULT = sys.argv[4] if len(sys.argv) > 4 else 'none'
mdl = targets.model(TGT)
arch = mdl.arch
RECIP = G.U + 'Reciprocal'; MMR = G.U + '(*Int).MulModWithReciprocal'
assert RECIP in mdl.ranges and MMR in mdl.ranges
M = G.M
Z, X, Y, MU = G.OPND, G.OPND + 0x40, G.OPND + 0x80, G.OPND + 0xc0


def reciprocal(m):
    cpu = mdl._x64() if arch == 'amd64' else mdl._a64()
    mdl.wr(cpu, X, m)
    if arch == 'amd64':
        S = 0x7ffff0000000 - 8
        mdl._x64call(cpu, mdl.entry(RECIP), {'rax': X})
    else:
        S = SP_TOP
        mdl._a64call(cpu, mdl.entry(RECIP), [X])
    return [mdl.rd(cpu, S + 8 + 8 * i, 8) for i in range(5)], cpu.steps


def mulmod_mu(x, y, m, mu):
    cpu = mdl._x64() if arch == 'amd64' else mdl._a64()
    mdl.wr(cpu, X, x); mdl.wr(cpu, Y, y); mdl.wr(cpu, Z, m)
    for i, w in enumerate(mu):
        mdl.wr(cpu, MU + 8 * i, w, 8)
    args = [Z, X, Y, Z, MU]
    # step cap 200,000 (a correct call takes about 1,000 steps); a wrong reciprocal can make reduce4 loop
    if arch == 'amd64':
        for k, v in zip(['rax', 'rbx', 'rcx', 'rdi', 'rsi'], args):
            cpu.r[k] = v
        cpu.r['r14'] = G.GSTRUCT; cpu.y[15] = 0
        cpu.call(mdl.entry(MMR), [], maxsteps=200_000)
    else:
        cpu.x[31] = SP_TOP; cpu.x[28] = G.GSTRUCT; cpu.x[29] = 0
        cpu.call(mdl.entry(MMR), args, maxsteps=200_000)
    return mdl.rd(cpu, Z), cpu.steps


class Memo:
    def __init__(self, fault):
        self.ok = False; self.mod = None; self.mu = None; self.fault = fault; self.misses = 0; self.hits = 0

    def same(self, z):
        if self.fault == 'memo3':
            return (self.mod & ((1 << 192) - 1)) == (z & ((1 << 192) - 1))
        return self.mod == z

    def mulmod(self, x, y, z):
        if z >> 192:
            if not self.ok or not self.same(z):
                self.mod = z; self.mu, _ = reciprocal(z); self.ok = True; self.misses += 1
            else:
                self.hits += 1
            r, st = mulmod_mu(x, y, z, self.mu)
            return r, st
        return mdl.run_direct('MULMOD', x, y, z)


def full(rnd):
    return rnd.getrandbits(256) | (1 << rnd.randrange(192, 256))


def sequences(rnd):
    kinds = ['reuse', 'alternate', 'limb', 'fullmath', 'narrow']
    while True:
        k = rnd.choice(kinds); L = rnd.randrange(5, 40)
        a, b = full(rnd), full(rnd)
        m = a
        for i in range(L):
            x, y = rnd.getrandbits(256), rnd.getrandbits(256)
            if k == 'reuse':
                mod = a
            elif k == 'alternate':
                mod = a if i % 2 == 0 else b
            elif k == 'limb':
                limb = rnd.randrange(4)
                m = (m & ~(((1 << 64) - 1) << (64 * limb))) | (rnd.getrandbits(64) << (64 * limb))
                if not m >> 192:
                    m |= 1 << 200
                mod = m
            elif k == 'fullmath':
                mod = M if i % 2 == 0 else rnd.choice([a, rnd.getrandbits(128) | 1, 1 << 96, 1 << 128])
            else:
                mod = rnd.getrandbits(rnd.randrange(1, 193)) | 1
            yield k, x, y, mod


rnd = random.Random(310731_08)
memo = Memo(FAULT)
res = {'target': TGT, 'fault': FAULT, 'seed': 310731_08, 'steps': 0, 'mismatches': 0, 'errors': 0, 'byKind': {},
       'records': [], 'started': time.time()}
for k, x, y, mod in sequences(rnd):
    if res['steps'] >= N:
        break
    res['steps'] += 1; res['byKind'][k] = res['byKind'].get(k, 0) + 1
    try:
        got, _ = memo.mulmod(x, y, mod)
    except Exception as e:
        res['errors'] += 1; res['records'].append({'kind': k, 'x': hex(x), 'y': hex(y), 'm': hex(mod), 'error': str(e)})
        if FAULT != 'none' and res['mismatches'] + res['errors'] >= 20:
            break
        continue
    want = (x * y) % mod
    if got != want:
        res['mismatches'] += 1
        res['records'].append({'step': res['steps'], 'kind': k, 'x': hex(x), 'y': hex(y), 'm': hex(mod), 'model': hex(got), 'reference': hex(want)})
        if FAULT != 'none' and res['mismatches'] + res['errors'] >= 20:
            break
res['memoHits'] = memo.hits; res['memoMisses'] = memo.misses
res['seconds'] = time.time() - res.pop('started')
json.dump(res, open(OUT, 'w'), indent=1)
print(OUT, {k: res[k] for k in ('steps', 'mismatches', 'errors', 'memoHits', 'memoMisses', 'seconds')})
