"""Cycle 31 copy of the cycle 30 driver: runs vector sets through the handler models of the shipped bsc, bor and
avalanchego binaries (targets.py) and compares with Python integers.

usage: python3 -I drive.py <target> <set> <shard> <nshard> <out.json> [fault]
sets: battery, targeted, c27, v4shapes, random, direct
Seeds: v4shapes 31_0731_01, random 31_0731_02 (per op: seed + index of op), direct 31_0731_03.
Every mismatch and every model error is saved in full.
"""
import json, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import models, goshim as G, targets
import faults as F

W = os.path.dirname(HERE)
TGT, SET, SHARD, NSHARD, OUT = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
arch = TGT.split('-')[1]
FAULT = sys.argv[6] if len(sys.argv) > 6 else 'none'
M = G.M
OPS = set(G.HANDLERS)
SEEDS = {'v4shapes': 310731_01, 'random': 310731_02, 'direct': 310731_03}
NRAND = int(os.environ.get('NRAND', '100000'))


def battery():
    sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
    import battery as B
    for op, a, b, c in B.vectors():
        if op in OPS:
            yield 'battery', op, a, b, c
        elif op == 'MULDIV512':
            yield 'battery-muldiv', 'MULMOD', a, b, c
            yield 'battery-muldiv', 'MULMOD', a, b, M
            yield 'battery-muldiv', 'MUL', a, b, 0
        elif op == 'DIVUP':
            yield 'battery-divup', 'DIV', a, b, 0
            yield 'battery-divup', 'MOD', a, b, 0


def targeted():
    sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
    import targeted as T
    for op, a, b, c in T.vectors():
        if op in OPS:
            yield 'targeted', op, a, b, c
        elif op == 'MULDIV512':
            yield 'targeted-muldiv', 'MULMOD', a, b, c
            yield 'targeted-muldiv', 'MULMOD', a, b, M
            yield 'targeted-muldiv', 'MUL', a, b, 0


def c27():
    d = json.load(open('/home/user/v4-core/research/network-risk/cycles/027/theme-monad-package-read.work/out/extra-vectors.json'))
    for k, V in d.items():
        for op, a, b, c in V:
            if op in OPS:
                yield 'c27-' + k, op, int(a, 16), int(b, 16), int(c, 16)


def v4shapes():
    """Operand shapes of FullMath.mulDiv (src/libraries/FullMath.sol:24-48) as SqrtPriceMath and SwapMath call it:
    numerators a*b of five to eight limbs, denominators 2^96, 2^128, liquidity values and prices."""
    rnd = random.Random(SEEDS['v4shapes'])
    Q96, Q128 = 1 << 96, 1 << 128
    for i in range(12000):
        limbs = rnd.choice((5, 6, 7, 8))
        bits = rnd.randrange(64 * limbs - 63, 64 * limbs + 1)
        abits = rnd.randrange(max(1, bits - 256), min(256, bits - 1) + 1)
        a = rnd.getrandbits(abits) | (1 << (abits - 1))
        bb = max(1, min(256, bits - abits))
        b = rnd.getrandbits(bb) | (1 << (bb - 1))
        den = rnd.choice([Q96, Q128, rnd.getrandbits(128) | 1, rnd.getrandbits(rnd.randrange(1, 129)) | 1,
                          rnd.getrandbits(160) | (1 << 159), 4295128739, 1461446703485210103287273052203988822378723970342,
                          (rnd.getrandbits(128) << 96) | 1, M - rnd.getrandbits(64)])
        p = a * b
        yield 'v4shapes', 'MULMOD', a, b, M
        yield 'v4shapes', 'MULMOD', a, b, den
        yield 'v4shapes', 'MUL', a, b, 0
        yield 'v4shapes', 'DIV', p & M, den, 0
        yield 'v4shapes', 'DIV', (p >> 256) & M, den, 0
        yield 'v4shapes', 'MOD', p & M, den, 0
        yield 'v4shapes', 'SUB', p & M, (p * 0 + rnd.getrandbits(256)), 0


def rword(rnd):
    k = rnd.random()
    if k < 0.45:
        return rnd.getrandbits(rnd.randrange(0, 257))
    if k < 0.65:
        return rnd.getrandbits(256)
    if k < 0.75:
        return M - rnd.getrandbits(rnd.randrange(0, 200))
    if k < 0.85:  # limb patterns
        v = 0
        for i in range(4):
            v |= rnd.choice((0, 1, (1 << 64) - 1, 1 << 63, rnd.getrandbits(64), (1 << 63) - 1)) << (64 * i)
        return v
    if k < 0.93:
        return (1 << rnd.randrange(256)) + rnd.choice((-1, 0, 1)) & M
    return G.u(-rnd.getrandbits(rnd.randrange(1, 256)))


def rand():
    oplist = sorted(OPS)
    for j, op in enumerate(oplist):
        rnd = random.Random(SEEDS['random'] + j)
        n = NRAND if op != 'EXP' else NRAND
        for i in range(n):
            a, b, c = rword(rnd), rword(rnd), rword(rnd)
            if op in ('SIGNEXTEND', 'BYTE', 'SHL', 'SHR', 'SAR') and rnd.random() < 0.8:
                a = rnd.randrange(0, 300)
            if op == 'EXP':
                # exponents of up to 16 bits, plus one case in 50 with a full random exponent
                b = rnd.getrandbits(256) if i % 50 == 0 else rnd.getrandbits(rnd.randrange(0, 17))
            if op in ('MULMOD', 'ADDMOD') and rnd.random() < 0.5:
                c = rnd.getrandbits(256) | (1 << 255) if rnd.random() < 0.5 else rnd.getrandbits(rnd.randrange(1, 257))
            yield 'random', op, a, b, c


def direct():
    rnd = random.Random(SEEDS['direct'])
    for op in ('LT', 'GT', 'SLT', 'SGT'):
        for i in range(NRAND):
            a = rword(rnd)
            b = a if i % 10 == 0 else (a ^ (1 << rnd.randrange(256)) if i % 10 == 1 else rword(rnd))
            yield 'direct', op, a, b, 0


GEN = {'battery': battery, 'targeted': targeted, 'c27': c27, 'v4shapes': v4shapes, 'random': rand, 'direct': direct}

fspec = F.get(TGT, FAULT)
mdl = targets.model(TGT, faults=fspec.get('faults'), text_patch=fspec.get('text_patch'))
res = {'target': TGT, 'faultWhere': fspec.get('where'), 'arch': arch, 'set': SET, 'shard': SHARD, 'nshard': NSHARD, 'fault': FAULT, 'seed': SEEDS.get(SET),
       'cases': 0, 'mismatches': 0, 'errors': 0, 'steps': 0, 'byOp': {}, 'byTag': {}, 'records': [], 'started': time.time()}
for k, (tag, op, a, b, c) in enumerate(GEN[SET]()):
    if k % NSHARD != SHARD:
        continue
    if fspec.get('ops') and op not in fspec['ops']:
        continue
    want = G.ref(op, a, b, c)
    st = res['byOp'].setdefault(op, [0, 0, 0]); res['byTag'][tag] = res['byTag'].get(tag, 0) + 1
    st[0] += 1; res['cases'] += 1
    try:
        got, steps = (mdl.run_direct if SET == 'direct' else mdl.run_handler)(op, a, b, c)
        res['steps'] += steps
    except Exception as e:
        st[2] += 1; res['errors'] += 1
        res['records'].append({'index': k, 'tag': tag, 'op': op, 'a': hex(a), 'b': hex(b), 'c': hex(c), 'error': '%s: %s' % (type(e).__name__, e)})
        continue
    if got != want:
        st[1] += 1; res['mismatches'] += 1
        res['records'].append({'index': k, 'tag': tag, 'op': op, 'a': hex(a), 'b': hex(b), 'c': hex(c), 'model': hex(got), 'reference': hex(want)})
    if fspec.get('stop_after') and res['mismatches'] >= fspec['stop_after']:
        break
res['seconds'] = time.time() - res.pop('started')
res['visited'] = len(mdl.visited)
json.dump(res, open(OUT, 'w'))
print(OUT, 'cases', res['cases'], 'mismatches', res['mismatches'], 'errors', res['errors'], 'steps', res['steps'], flush=True)
