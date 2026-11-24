"""Whole tick range through the compiled TickMath functions of the built runtime:
for every tick t in [MIN_TICK, MAX_TICK], getSqrtPriceAtTick(t) equals the transcription
of the source in tools/opdiff/v4math.py, prices are strictly increasing, and
getTickAtSqrtPrice(P(t)) == t and getTickAtSqrtPrice(P(t) - 1) == t - 1 (t > MIN_TICK).
Usage: python3 -I fullrange.py <out.json> [workers]"""
import sys, os, json, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
M = 1 << 256
def work(rng):
    import harness as H
    sys.path.insert(0, H.OPD); import v4math as V
    w = H.World({H.PM: H.HCODE})
    def call(fn, arg):
        w.init_stack = [H.RET, arg]; w.init_pc = H.EP[fn]
        ok, ret = w.run(H.PM, H.PM, 0, 0, b'', False, 0)
        return w.final_stack[-1] if ok else None
    lo, hi = rng; bad = []; prev = call('fun_getSqrtPriceAtTick', (lo - 1) % M) if lo > -887272 else 0
    for t in range(lo, hi):
        p = call('fun_getSqrtPriceAtTick', t % M)
        if p != V.get_sqrt_price_at_tick(t) or not p > prev: bad.append(['price', t, p])
        if t < 887272:
            if call('fun_getTickAtSqrtPrice', p) != t % M: bad.append(['tick', t])
        if t > -887272:
            if call('fun_getTickAtSqrtPrice', p - 1) != (t - 1) % M: bad.append(['tickBelow', t])
        prev = p
    return lo, hi, bad[:20], len(bad)
if __name__ == '__main__':
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    edges = list(range(-887272, 887273, 20000)) + [887273]
    chunks = list(zip(edges[:-1], edges[1:]))
    t0 = time.time(); res = []
    with Pool(n) as p:
        for r in p.imap_unordered(work, chunks):
            res.append(r); print(r[0], r[1], r[3], round(time.time() - t0), flush=True)
    tot = sum(r[3] for r in res)
    json.dump({'ticks': 887272 * 2 + 1, 'mismatches': tot, 'examples': [b for r in res for b in r[2]][:50], 'seconds': round(time.time() - t0)}, open(sys.argv[1], 'w'), indent=1)
    print('mismatches', tot)
