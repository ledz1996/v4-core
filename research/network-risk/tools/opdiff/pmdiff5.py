"""Fifth script set: pools at extreme prices with very large liquidity. They reach
arithmetic that ordinary pools never do: the 512 bit branch of FullMath.mulDiv with
the constant denominator 2^96 (SqrtPriceMath.getAmount1Delta when liquidity times the
price difference needs more than 256 bits), mulDiv and mulDivRoundingUp on amounts
above 2^160 in getNextSqrtPriceFromAmount1RoundingDown, the overflow branches of
getNextSqrtPriceFromAmount0RoundingUp, and the SafeCast reverts that follow. In a
swap the 512 bit result decides whether the step reaches its target, so it steers
control flow even when the amounts that are paid stay small.

Every network's answer is compared with the reference interpreter's.
Usage: python3 pmdiff5.py <out.json> [chainId ...]
"""
import sys, json, random, hashlib, time, concurrent.futures as cf
from evm import rpc, networks, MASK
import v4math as m
import pmdiff as P
from pyevm import World, NAMES

PMI, DRV = int(P.PM, 16), int(P.DRV, 16)


def item(c): return len(c).to_bytes(2, 'big') + c


def scripts():
    rnd = random.Random(5_2026_11_24); out = []
    for sp, fee in ((60, 3000), (200, 10000), (1, 100), (2000, 0), (32767, 500), (10, 999999)):
        hi_t = (887272 // sp) * sp
        for sign in (1, -1):
            for t_abs in (880020, 870000, 800040, 700020, 500000, 887220):
                t = sign * (t_abs // sp * sp)
                if abs(t) + sp > hi_t: t = sign * (hi_t - 2 * sp)
                for exact in (True, False):
                    price = m.get_sqrt_price_at_tick(t) + (0 if exact else rnd.randrange(1, 1 << 30))
                    price = min(m.MAX_SQRT_PRICE - 1, max(m.MIN_SQRT_PRICE, price))
                    calls = [P.c_init(fee, sp, price)]
                    for _ in range(rnd.randrange(1, 4)):
                        lo = t - sp * rnd.choice([0, 0, 1, 3]); hi = t + sp * rnd.choice([1, 1, 2, 5])
                        if rnd.random() < 0.2: lo, hi = -hi_t, hi_t
                        lo, hi = max(-hi_t, lo), min(hi_t, hi)
                        if lo >= hi: continue
                        calls.append(P.c_mod(fee, sp, lo, hi, 1 << rnd.choice([60, 90, 100, 105, 107, 110, 113, 120, 126])))
                    for k in (0, 3): calls.append(P.c_ext(P.pool_slot(fee, sp, k)))
                    for _ in range(rnd.randrange(3, 7)):
                        zfo = rnd.random() < 0.5; mag = 1 << rnd.choice([1, 40, 60, 100, 120, 126, 127, 140, 165, 200, 254])
                        mag += rnd.randrange(0, 1000); amt = -mag if rnd.random() < 0.65 else mag
                        limit = rnd.choice([m.MIN_SQRT_PRICE + 1 if zfo else m.MAX_SQRT_PRICE - 1,
                                            max(m.MIN_SQRT_PRICE + 1, price - (price >> rnd.randrange(1, 12))) if zfo else min(m.MAX_SQRT_PRICE - 1, price + (price >> rnd.randrange(1, 12)))])
                        calls.append(P.c_swap(fee, sp, zfo, amt, limit))
                        for k in (0, 1, 2, 3): calls.append(P.c_ext(P.pool_slot(fee, sp, k)))
                        calls.append(P.S_EXTTLOAD + P.w(P.delta_slot(DRV, P.C0))); calls.append(P.S_EXTTLOAD + P.w(P.delta_slot(DRV, P.C1)))
                    out.append(b''.join(item(c) for c in calls) + b'\0\0')
    # one family aimed at mulDiv(amount, 2^96, liquidity) with an amount above 2^160: price exactly on a tick, a very large
    # position that starts at that tick, then token1 paid in with amounts between 2^160 and what the next tick would take
    for sp, L, t in ((60, 113, 880020), (60, 110, 880020), (200, 114, 880000), (10, 110, 885000), (60, 112, 860040)):
        price = m.get_sqrt_price_at_tick(t); calls = [P.c_init(3000, sp, price), P.c_mod(3000, sp, t, t + 5 * sp, 1 << L)]
        for e in (159, 160, 161, 162, 163, 164, 165, 166, 167, 170):
            calls.append(P.c_swap(3000, sp, False, -(1 << e) - 12345, m.MAX_SQRT_PRICE - 1))
            calls.append(P.c_swap(3000, sp, False, (1 << (e - 120)) + 7, m.MAX_SQRT_PRICE - 1))
            calls.append(P.c_swap(3000, sp, True, 1 << e, m.MIN_SQRT_PRICE + 1))
            for k in (0, 3): calls.append(P.c_ext(P.pool_slot(3000, sp, k)))
        out.append(b''.join(item(c) for c in calls) + b'\0\0')
    return out


if __name__ == '__main__':
    out = sys.argv[1]; only = set(map(int, sys.argv[2:]))
    code = P.fetch_code(); drv = P.driver(); S = scripts()
    ref = []; cover = set(); branches = {}; ops = {}; calls = 0; failed = 0; heavy = 0; sel = {}
    for data in S:
        wd = World({PMI: code, DRV: drv}); wd.max_steps = 8_000_000
        try:
            ok, ret = wd.call(0, DRV, 0, data, False, 0)
        except TimeoutError:
            ref.append(None); heavy += 1; continue
        ref.append(ret); cover |= wd.cover.get(PMI, set())
        for (a, pc), o in wd.branches.items():
            if a == PMI: branches.setdefault(pc, set()).update(o)
        for o, c in wd.ops.items(): ops[o] = ops.get(o, 0) + c
        for k, r in P.parse(ret):
            calls += 1; failed += 1 - k
            if not k: sel[r[:4].hex() or 'empty'] = sel.get(r[:4].hex() or 'empty', 0) + 1
    json.dump({'cover': sorted(cover), 'branches': {str(k): sorted(v) for k, v in branches.items()}, 'ops': {NAMES.get(o, hex(o)): c for o, c in ops.items()}},
              open(out.replace('.json', '-coverage.json'), 'w'))
    print(len(S), 'scripts,', calls, 'calls,', failed, 'failed in the reference with selectors', sel, '; left out as too long:', heavy)
    refh = [hashlib.sha256(r).hexdigest() if r is not None else 'heavy' for r in ref]
    ov = {P.PM: {'code': '0x' + code.hex()}, P.DRV: {'code': '0x' + drv.hex()}}

    def ask(url, data, gas):
        last = None
        for k in range(5):
            try:
                return hashlib.sha256(bytes.fromhex(rpc(url, 'eth_call', [{'to': P.DRV, 'data': '0x' + data.hex(), 'gas': hex(gas)}, 'latest', ov], timeout=120)[2:])).hexdigest()
            except Exception as e:  # noqa
                last = str(e)[:120]
                if 'gas' in last.lower() and 'limit' in last.lower(): break
                time.sleep(3 * (k + 1))
        return 'ERR ' + last

    def run_net(nw):
        cid, name, url = nw; res = []
        for i, data in enumerate(S):
            if refh[i] == 'heavy': res.append('heavy'); continue
            h = ask(url, data, 25_000_000)
            if h != refh[i] and not h.startswith('ERR'):
                for gas in (2_000_000_000, 150_000_000):
                    h2 = ask(url, data, gas)
                    if not h2.startswith('ERR'): h = h2 if h2 == refh[i] else h; break
            res.append(h)
        return cid, name, res

    summary = []; n = len(S) - heavy
    with cf.ThreadPoolExecutor(8) as ex:
        for cid, name, res in ex.map(run_net, [x for x in networks() if not only or x[0] in only]):
            diff = [i for i, (a, b) in enumerate(zip(res, refh)) if a != b and not a.startswith('ERR')]; err = [a for a in res if a.startswith('ERR')]
            same = sum(1 for a, b in zip(res, refh) if a == b and a != 'heavy')
            print(f'{cid:>8} {name:16} equal to the reference {same}/{n} different {len(diff)} errors {len(err)} {err[:1]}', flush=True)
            summary.append({'chainId': cid, 'name': name, 'identical': same, 'different': diff, 'errors': len(err)})
    json.dump({'scripts': len(S), 'compared': n, 'calls': calls, 'failedInReference': failed, 'revertSelectors': sel, 'results': summary, 'referenceHashes': refh}, open(out, 'w'), indent=1)
