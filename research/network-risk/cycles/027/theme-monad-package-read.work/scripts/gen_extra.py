"""Extra vectors for the package routine model.

1. knuth_div add-back and q_hat == BASE-1 branches: a Python transcription of
   knuth_div at the tag (category/core/runtime/uint256.hpp:705-806 of 0.16.7) flags
   operands that take each rare branch; operands are drawn from structured words.
2. The DIV, MOD, MULMOD and MUL operands that the pool math of src/libraries
   produces, recorded while tools/opdiff/v4math.py (a transcription of the source)
   runs over edge ticks, prices, liquidities and amounts.
Seeds: knuth 27_1123, math 27_1124.
usage: python3 -I gen_extra.py <out.json>
"""
import sys, json, random
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
M = 2 ** 256 - 1
B = 1 << 64
W = B - 1

def words(x, n): return [(x >> (64 * i)) & W for i in range(n)]

def knuth_flags(U, V, nU):
    """Return set of branch names taken when dividing U (nU words) by V (4 words)."""
    u = words(U, nU); v = words(V, 4)
    m = max([i + 1 for i in range(nU) if u[i]] or [0]); n = max([i + 1 for i in range(4) if v[i]] or [0])
    if n == 0 or m < n or m == 1 or n == 1: return set()
    sh = 64 - v[n - 1].bit_length()
    un = words((U << sh), nU + 1); vn = words(V << sh, 4)
    flags = set()
    for i in range(m - n, -1, -1):
        if un[i + n] == vn[n - 1]:
            qh = W; flags.add('qhat_max')
        else:
            num = (un[i + n] << 64) | un[i + n - 1]
            qh, rh = divmod(num, vn[n - 1])
            if qh == 0:
                flags.add('qhat_zero'); continue
            if qh * vn[n - 2] > (rh << 64) + un[i + n - 2]:
                qh -= 1; flags.add('pre_adjust')
        cur = sum(un[i + j] << (64 * j) for j in range(n + 1))
        Vv = sum(vn[j] << (64 * j) for j in range(n))
        rem = cur - qh * Vv
        if rem < 0:
            flags.add('add_back'); rem += Vv; qh -= 1
        for j in range(n + 1):
            un[i + j] = (rem >> (64 * j)) & W
    return flags

def structured(R, nwords):
    pool = [0, 1, 2, W, W - 1, 1 << 63, (1 << 63) - 1, (1 << 63) + 1, 1 << 32, (1 << 32) - 1]
    x = 0
    for i in range(nwords):
        w = R.choice(pool) if R.random() < 0.6 else R.getrandbits(64)
        x |= w << (64 * i)
    return x

def knuth_vectors():
    R = random.Random(27_1123)
    out = {'add_back': [], 'qhat_max': [], 'pre_adjust': [], 'qhat_zero': []}
    cap = {'add_back': 3000, 'qhat_max': 1500, 'pre_adjust': 1500, 'qhat_zero': 800}
    # Hacker's Delight add-back examples scaled from 16 bit to 64 bit digits
    seeds = [([0, 0, 1 << 63, (1 << 63) - 1], [1, 0, 1 << 63, 0]), ([0, W - 1, 0, 1 << 63], [W, 1 << 63, 0, 0]),
             ([0, W - 1, 0, 1 << 63], [W, 1 << 63, 0, 0])]
    for uw, vw in seeds:
        U = sum(w << (64 * i) for i, w in enumerate(uw)); V = sum(w << (64 * i) for i, w in enumerate(vw))
        for op in ('DIV', 'MOD'): out['add_back'].append((op, U, V, 0))
    tries = 0
    while tries < 3_000_000 and any(len(out[k]) < cap[k] for k in out):
        tries += 1
        kind = R.random()
        nv = R.choice((2, 3, 4))
        V = structured(R, nv)
        if V >> (64 * (nv - 1)) == 0: continue
        if R.random() < 0.5:
            s = R.randrange(0, 64); V >>= s
            if V >> (64 * (nv - 1)) == 0 and nv > 2: pass
        if kind < 0.5:
            U = structured(R, 4)
            fl = knuth_flags(U, V, 4)
            for f in fl:
                if len(out[f]) < cap[f]:
                    out[f].append((R.choice(('DIV', 'MOD', 'SDIV', 'SMOD')), U, V, 0))
        elif kind < 0.75:
            a = structured(R, 4); b = structured(R, 4)
            fl = knuth_flags(a + b, V, 5)
            for f in fl:
                if len(out[f]) < cap[f]:
                    out[f].append(('ADDMOD', a, b, V))
        else:
            a = structured(R, R.choice((2, 3, 4))); b = structured(R, 4)
            fl = knuth_flags(a * b, V, 8)
            for f in fl:
                if len(out[f]) < cap[f]:
                    out[f].append(('MULMOD', a, b, V))
    # SDIV and SMOD reach udivrem on absolute values; for those vectors the flags hold only for DIV and MOD,
    # so they are kept as extra signed cases and the DIV/MOD twin is added too.
    for f in out:
        extra = []
        for op, a, b, c in out[f]:
            if op in ('SDIV', 'SMOD'): extra.append(('DIV' if op == 'SDIV' else 'MOD', a, b, c))
        out[f] += extra
    print('knuth tries', tries, {k: len(v) for k, v in out.items()})
    return out

def math_vectors():
    import v4math as vm
    rec = set()
    od, omm, omul, omod = vm.div, vm.mulmod, vm.mul, vm.REF['MOD']
    def div(a, b): rec.add(('DIV', a, b, 0)); return od(a, b)
    def mulmod(a, b, c): rec.add(('MULMOD', a, b, c)); return omm(a, b, c)
    def mul(a, b): rec.add(('MUL', a, b, 0)); return omul(a, b)
    REF2 = dict(vm.REF); REF2['MOD'] = lambda a, b, c: (rec.add(('MOD', a, b, 0)), omod(a, b, c))[1]
    vm.div, vm.mulmod, vm.mul, vm.REF = div, mulmod, mul, REF2
    R = random.Random(27_1124)
    ticks = list(range(-887272, -887000)) + list(range(887000, 887273)) + list(range(-300, 301)) + [R.randrange(-887272, 887273) for _ in range(600)]
    for t in ticks:
        p = vm.get_sqrt_price_at_tick(t)
        if vm.MIN_SQRT_PRICE <= p < vm.MAX_SQRT_PRICE:
            try: vm.get_tick_at_sqrt_price(p)
            except vm.Revert: pass
    prices = [vm.MIN_SQRT_PRICE, vm.MIN_SQRT_PRICE + 1, vm.MAX_SQRT_PRICE - 1, vm.MAX_SQRT_PRICE, 1 << 96, (1 << 96) + 1, (1 << 160) - 1] + \
             [vm.get_sqrt_price_at_tick(R.randrange(-887272, 887273)) for _ in range(40)]
    liqs = [1, 2, (1 << 128) - 1, (1 << 127), 10 ** 18, 3 << 100] + [R.getrandbits(R.choice((20, 64, 100, 128))) or 1 for _ in range(20)]
    amts = [1, 2, (1 << 255) - 1, M, M - 1, (1 << 128), (1 << 160) - 1, 10 ** 30] + [R.getrandbits(R.choice((8, 64, 128, 200, 255))) for _ in range(20)]
    fees = [0, 1, 3000, 500000, 999999, 10 ** 6]
    n = 0
    for _ in range(4000):
        pc, pt = R.choice(prices), R.choice(prices)
        L = R.choice(liqs); A = R.choice(amts); f = R.choice(fees)
        try:
            vm.compute_swap_step(pc, pt, L, vm.u(-A) if R.random() < 0.5 else A, f)
        except Exception:
            pass
        for fn in (vm.amount0_delta, vm.amount1_delta):
            try: fn(pc, pt, L, R.random() < 0.5)
            except Exception: pass
        n += 1
    for a in amts + liqs:
        for b in amts + liqs:
            for d in [1, 2, 3, M, M - 1, 1 << 96, 1 << 128, (1 << 255) + 1] + liqs[:4]:
                try: vm.mul_div(a, b, d); vm.mul_div_rounding_up(a, b, d)
                except vm.Revert: pass
    L = sorted(rec)
    R.shuffle(L)
    L = L[:40000]
    print('math operands', len(rec), 'kept', len(L))
    return L

if __name__ == '__main__':
    out = {}
    for k, v in knuth_vectors().items():
        out['knuth_' + k] = [(op, hex(a), hex(b), hex(c)) for op, a, b, c in v]
    out['poolmath'] = [(op, hex(a), hex(b), hex(c)) for op, a, b, c in math_vectors()]
    json.dump(out, open(sys.argv[1], 'w'))
