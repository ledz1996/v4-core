"""Case list of theme-unexecuted-sides. Deterministic: no random sampling is used here.

Usage: python3 cases.py <out.json>
Writes the cases with the parameters the driver needs. Token addresses are unique per case so every case has its own
pool. v4math (a transcription of the source) is used only to pick tick ranges and limit prices; the checks in
check.py do not use it.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import MIN_SQRT, MAX_SQRT, MIN_TICK, MAX_TICK, D
import v4math as V

PRICES = [('MIN+1', MIN_SQRT + 1), ('2^64', 1 << 64), ('2^96', 1 << 96), ('2^128', 1 << 128), ('2^129', 1 << 129),
          ('2^158', 1 << 158), ('2^159', 1 << 159), ('MAX-1', MAX_SQRT - 1)]
AMTS = [('1', 1), ('2^64', 1 << 64), ('2^96', 1 << 96), ('2^97', 1 << 97), ('2^120', 1 << 120), ('2^126', 1 << 126),
        ('2^127-1', (1 << 127) - 1)]
FEES = [0, 1, 500, 999999, 1000000]
I127 = (1 << 127) - 1


def maxL(ts):
    q = -((-MIN_TICK) // ts)               # MIN_TICK / ts, truncated toward zero
    mn = q - (1 if q * ts != MIN_TICK else 0)
    mx = MAX_TICK // ts
    return ((1 << 128) - 1) // (mx - mn + 1)


def usable(ts):
    return -((-MIN_TICK) // ts) * ts, (MAX_TICK // ts) * ts


def deposits(s, L, tl, tu):
    pl, pu = V.get_sqrt_price_at_tick(tl), V.get_sqrt_price_at_tick(tu)
    a0 = a1 = 0
    if s < pu:
        lo = max(s, pl); a0 = -(-(L << 96) * (pu - lo) // (pu * lo))
    if s > pl:
        hi = min(s, pu); a1 = -(-L * (hi - pl) // (1 << 96))
    return a0, a1


def choose_range(s, L, ts):
    t = V.get_tick_at_sqrt_price(s)
    lo, hi = usable(ts)
    base = (t // ts) * ts
    cands = [(lo, hi)] + [(max(lo, base - k * ts), min(hi, base + (k + 1) * ts)) for k in (10000, 1000, 100, 10, 1, 0)]
    for tl, tu in cands:
        if not (tl <= t < tu) and not (t == MAX_TICK and tu == hi):
            continue
        if ts == 1 and (tu - tl) > 25600:
            continue
        a0, a1 = deposits(s, L, tl, tu)
        if a0 <= I127 and a1 <= I127:
            return tl, tu
    return None


def limit_for(s, zfo, tl, tu):
    if zfo:
        lim = V.get_sqrt_price_at_tick(tl)
        if lim <= MIN_SQRT or lim >= s: lim = MIN_SQRT + 1
    else:
        lim = V.get_sqrt_price_at_tick(tu)
        if lim >= MAX_SQRT or lim <= s: lim = MAX_SQRT - 1
    return lim


class Gen:
    def __init__(self):
        self.cases = []; self.k = 0

    def pair(self):
        self.k += 1
        t0 = 0x00000000000000000000000000000000_10000000 + 2 * self.k
        return t0, t0 + 1

    def add(self, c, tag):
        t0, t1 = self.pair(); c.update(t0=t0, t1=t1); c.setdefault('hooks', 0); c['tag'] = tag; c['id'] = len(self.cases)
        self.cases.append(c)


def swaps(g):
    seen_fail = set()
    for ip, (pn, s) in enumerate(PRICES):
        ts = 1 if pn in ('MIN+1', 'MAX-1') else 60
        LS = [('1', 1), ('2^32', 1 << 32), ('2^64', 1 << 64), ('2^96', 1 << 96), ('2^127', 1 << 127), ('maxL', maxL(ts))]
        for il, (ln, L) in enumerate(LS):
            rg = choose_range(s, L, ts)
            for ia, (an, a) in enumerate(AMTS):
                for zfo in (True, False):
                    for exin in (True, False):
                        sweep = pn in ('2^96', '2^159') and ln in ('2^64', 'maxL')
                        fees = FEES if sweep else [FEES[(ip + il + ia + 2 * zfo + exin) % 5]]
                        for f in fees:
                            if rg is None or L > maxL(ts):
                                key = (pn, ln)
                                if key in seen_fail: continue
                                seen_fail.add(key)
                                tl, tu = usable(ts)
                            else:
                                tl, tu = rg
                            c = dict(kind=0, fee=f, ts=ts, sqrtP=s, tl=tl, tu=tu, liq=L, zfo=zfo, amt=-a if exin else a,
                                     lim=limit_for(s, zfo, tl, tu))
                            g.add(c, f'swap P={pn} L={ln} A={an} {"zfo" if zfo else "ofz"} {"in" if exin else "out"} fee={f}')


def fallback(g):
    """Task 4 inputs: exact-input zeroForOne steps that reach getNextSqrtPriceFromAmount0RoundingUp(add=true)."""
    out = []
    for sname, s, L in [('2^150', 1 << 150, 1 << 72), ('2^159.9', (MAX_SQRT * 15) // 16, 1 << 62),
                        ('MAX-2^100', MAX_SQRT - (1 << 100), 1 << 62)]:
        ts = 60
        t = V.get_tick_at_sqrt_price(s)
        tl = (V.get_tick_at_sqrt_price(1 << 40) // ts) * ts
        tu = min(usable(ts)[1], (t // ts + 1) * ts)
        N = L << 96
        amax = M // s
        # product fits and numerator1 + product does not wrap: largest amount with a*s + N < 2^256
        afit = ((1 << 256) - N - 1) // s
        cands = [('fits, no wrap (line 47)', afit), ('fits, line 45 wraps', afit + 1) if afit + 1 <= amax else None,
                 ('largest fitting product', amax), ('first wrapped product (line 43)', amax + 1),
                 ('wrapped, 2*amax', 2 * amax), ('wrapped, 2^127-1', I127), ('2^120', 1 << 120)]
        for row in cands:
            if row is None: continue
            name, a = row
            if a <= 0 or a > I127: continue
            c = dict(kind=0, fee=0, ts=ts, sqrtP=s, tl=tl, tu=tu, liq=L, zfo=True, amt=-a, lim=limit_for(s, True, tl, tu))
            g.add(c, f'fallback P={sname} L=2^{L.bit_length()-1} {name} a={a}')
            out.append(c['id'])
        # with fee 3000, the amount that reaches the function is floor(a * 997000 / 1e6)
        a = (amax + 1) * 10 ** 6 // 997000 + 1
        g.add(dict(kind=0, fee=3000, ts=ts, sqrtP=s, tl=tl, tu=tu, liq=L, zfo=True, amt=-a, lim=limit_for(s, True, tl, tu)),
              f'fallback P={sname} fee=3000 first wrapped after fee a={a}')
    return out


M = (1 << 256) - 1


def donates(g):
    ts = 60; s = 1 << 96
    for ln, L in [('1', 1), ('2^32', 1 << 32), ('2^64', 1 << 64), ('2^96', 1 << 96), ('maxL', maxL(ts))]:
        tl, tu = choose_range(s, L, ts)
        for an, a in AMTS + [('2^127', 1 << 127)]:
            for a0, a1, nm in [(a, a, 'both'), (a, 0, 'amount0'), (0, a, 'amount1')]:
                g.add(dict(kind=1, fee=500, ts=ts, sqrtP=s, tl=tl, tu=tu, liq=L, p=[a0, a1]), f'donate L={ln} A={an} {nm}')
    for nm, s2 in [('2^96', 1 << 96), ('2^159', 1 << 159)]:
        g.add(dict(kind=1, fee=500, ts=ts, sqrtP=s2, tl=0, tu=0, liq=0, p=[1000, 1000]), f'donate no liquidity P={nm}')
        # liquidity exists but out of range: position above the price
        g.add(dict(kind=1, fee=500, ts=ts, sqrtP=1 << 96, tl=600, tu=1200, liq=1 << 64, p=[1000, 1000]),
              'donate position out of range')
    g.add(dict(kind=1, fee=500, ts=ts, sqrtP=1 << 96, tl=-600, tu=600, liq=1 << 64, p=[0, 0]), 'donate zero amounts')


def clears(g):
    for an, a in [('1', 1), ('1000', 1000), ('2^64', 1 << 64), ('2^127-1', I127)]:
        for nm, x in [('exact', a), ('minus 1', a - 1), ('plus 1', a + 1), ('zero', 0), ('2^127', 1 << 127), ('2^255', 1 << 255)]:
            g.add(dict(kind=2, p=[a, x]), f'clear credit={an} amount={nm}')


def settlefors(g):
    for an, a in [('1', 1), ('2^64', 1 << 64), ('2^127-1', I127), ('0', 0)]:
        g.add(dict(kind=3, p=[a]), f'settleFor credit={an}')


def erc6909(g):
    for an, a in [('100', 100), ('2^64', 1 << 64), ('2^127-1', I127), ('2^128', 1 << 128)]:
        g.add(dict(kind=4, p=[a, a // 10, a // 5, a // 20, a // 20, a // 20]), f'erc6909 a={an}')
    g.add(dict(kind=4, p=[100, 0, 0, 0, 0, 0]), 'erc6909 zero amounts')
    g.add(dict(kind=4, p=[100, 100, 0, 0, 0, 0]), 'erc6909 transfer all')


def dynamic(g):
    s = 1 << 96; ts = 60; L = 1 << 64
    tl, tu = choose_range(s, L, ts)
    for nf in (0, 3000, 999999, 1000000, 1000001):
        for exin in (True, False):
            for zfo in (True, False):
                g.add(dict(kind=5, fee=0x800000, ts=ts, hooks=D, sqrtP=s, tl=tl, tu=tu, liq=L, zfo=zfo,
                           amt=-(1 << 60) if exin else (1 << 60), lim=limit_for(s, zfo, tl, tu), p=[nf]),
                      f'dynamic fee={nf} {"zfo" if zfo else "ofz"} {"in" if exin else "out"}')


if __name__ == '__main__':
    g = Gen()
    swaps(g); fb = fallback(g); donates(g); clears(g); settlefors(g); erc6909(g); dynamic(g)
    from collections import Counter
    print(len(g.cases), Counter(c['kind'] for c in g.cases))
    json.dump({'note': 'deterministic grid, no seed', 'cases': g.cases}, open(sys.argv[1], 'w'), indent=0)
