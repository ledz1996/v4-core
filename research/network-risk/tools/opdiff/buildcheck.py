"""The bytecode built from this checkout against the source it was built from. The
build runs in the reference interpreter (pyevm.py); the expected values come from the
transcription of the source in v4math.py and a step loop written from Pool.swap. A
difference would mean the compiler, with the via-IR optimizer at the settings of
foundry.toml, produced code that does not compute what the source says.

Each case: a new pool, one or two positions, then swaps. Compared: both amounts of
every liquidity change, both amounts of every swap, and price, tick and liquidity in
storage after every swap.

Usage: PM_BUILD=<build json> python3 buildcheck.py <out.json> [cases]
"""
import sys, os, json, random, time
from evm import keccak, MASK, s, u, ref_signextend
import v4math as m
import pmdiff as P
from pyevm import World

PM, DRV = int(P.PM, 16), int(P.DRV, 16)


def item(data): return len(data).to_bytes(2, 'big') + data


class Model:
    """Pool state as the source keeps it, for a pool without protocol fee and without hook."""
    def __init__(self, price, sp, fee):
        self.p, self.sp, self.fee, self.liq = price, sp, fee, 0
        self.tick = m.get_tick_at_sqrt_price(price); self.net = {}; self.gross = {}

    def modify(self, lo, hi, d):
        pa, pb = m.get_sqrt_price_at_tick(lo), m.get_sqrt_price_at_tick(hi)
        up = d > 0; L = abs(d); inside = False
        if self.tick < lo: a0, a1 = m.amount0_delta(pa, pb, L, up), 0
        elif self.tick < hi:
            a0, a1 = m.amount0_delta(self.p, pb, L, up), m.amount1_delta(pa, self.p, L, up); inside = True
        else: a0, a1 = 0, m.amount1_delta(pa, pb, L, up)
        if a0 >> 127 or a1 >> 127: return 'revert'  # SafeCast to int128 in the source (toInt128 / toInt256 chain)
        for t, sign in ((lo, 1), (hi, -1)):
            self.gross[t] = self.gross.get(t, 0) + d; self.net[t] = self.net.get(t, 0) + sign * d
            if self.gross[t] == 0: del self.gross[t]; del self.net[t]
        if inside: self.liq += d
        return (-a0, -a1) if up else (a0, a1)

    def next_tick(self, lte):
        c = self.tick // self.sp  # floor division, as compress() does
        ticks = sorted(self.gross)
        if lte:
            word_lo = (c >> 8 << 8) * self.sp
            cand = [t for t in ticks if word_lo <= t <= c * self.sp]
            return (max(cand), True) if cand else (word_lo, False)
        c += 1
        word_hi = ((c >> 8 << 8) + 255) * self.sp
        cand = [t for t in ticks if c * self.sp <= t <= word_hi]
        return (min(cand), True) if cand else (word_hi, False)

    def swap(self, zfo, amount, limit):
        if amount == 0: return 0, 0
        rem, calc = amount, 0
        while not (rem == 0 or self.p == limit):
            start = self.p
            tn, init = self.next_tick(zfo); tn = max(m.MIN_TICK, min(m.MAX_TICK, tn))
            pn = m.get_sqrt_price_at_tick(tn)
            target = (pn if pn >= limit else limit) if zfo else (pn if pn < limit else limit)
            self.p, a_in, a_out, f = m.compute_swap_step(self.p, target, self.liq, rem, self.fee)
            if amount > 0: rem -= a_out; calc -= a_in + f
            else: rem += a_in + f; calc += a_out
            if self.p == pn:
                if init: self.liq += -self.net[tn] if zfo else self.net[tn]
                self.tick = tn - 1 if zfo else tn
            elif self.p != start: self.tick = m.get_tick_at_sqrt_price(self.p)
        spec, other = amount - rem, calc
        return (spec, other) if zfo == (amount < 0) else (other, spec)


def delta(ret):
    v = int.from_bytes(ret[:32], 'big'); a0 = v >> 128; a1 = v & ((1 << 128) - 1)
    return (a0 - (1 << 128) if a0 >> 127 else a0), (a1 - (1 << 128) if a1 >> 127 else a1)


if __name__ == '__main__':
    out = sys.argv[1]; cases = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    code = P.fetch_code(); drv = P.driver(); rnd = random.Random(26_11_24)
    tot = {'cases': 0, 'liquidityChanges': 0, 'swaps': 0, 'swapSteps': 0, 'mismatches': [], 'reverts': 0}
    t0 = time.time()
    for case in range(cases):
        fee = rnd.choice([0, 1, 100, 500, 3000, 10000, 500000, 999999]); sp = rnd.choice([1, 2, 10, 60, 200, 2000])
        t_start = rnd.choice([0, rnd.randrange(-200000, 200000), rnd.randrange(-800000, 800000), rnd.randrange(-500, 500)])
        price = m.get_sqrt_price_at_tick(t_start) + rnd.randrange(0, 1 << 40)
        price = min(m.MAX_SQRT_PRICE - 1, max(m.MIN_SQRT_PRICE, price))
        mod = Model(price, sp, fee); key = P.key_words(fee, sp); base = P.pool_slot(fee, sp, 0)
        calls = [('init', P.c_init(fee, sp, price))]; expect = [None]
        lo_t, hi_t = -(887272 // sp) * sp, (887272 // sp) * sp
        for _ in range(rnd.randrange(1, 4)):
            w = rnd.choice([sp, 5 * sp, 50 * sp, 400 * sp, 3000 * sp])
            lo = max(lo_t, (mod.tick - rnd.randrange(0, w + 1)) // sp * sp); hi = min(hi_t, (mod.tick + rnd.randrange(1, w + 2)) // sp * sp + sp)
            if rnd.random() < 0.15: lo, hi = lo_t, hi_t
            if lo >= hi: continue
            L = rnd.choice([rnd.getrandbits(40), rnd.getrandbits(70), rnd.getrandbits(100), 10 ** 18]) or 1
            calls.append(('mod', P.c_mod(fee, sp, lo, hi, L))); expect.append(mod.modify(lo, hi, L))
        for _ in range(rnd.randrange(2, 7)):
            zfo = rnd.random() < 0.5; mag = rnd.choice([1, rnd.getrandbits(20), rnd.getrandbits(50), rnd.getrandbits(80), rnd.getrandbits(110)])
            amt = -mag if (rnd.random() < 0.6 or fee >= 999999) else mag
            limit = (max(m.MIN_SQRT_PRICE + 1, mod.p - (mod.p >> rnd.randrange(3, 24))) if zfo else min(m.MAX_SQRT_PRICE - 1, mod.p + (mod.p >> rnd.randrange(3, 24))))
            if limit == mod.p: continue
            calls.append(('swap', P.c_swap(fee, sp, zfo, amt, limit)))
            try:
                r = mod.swap(zfo, amt, limit)
                if abs(r[0]) >> 127 or abs(r[1]) >> 127: raise m.Revert('SafeCast')
                expect.append(r + (mod.p, mod.tick, mod.liq))
            except m.Revert:
                expect.append('revert'); break
            calls.append(('slot0', P.c_ext(base))); expect.append(None); calls.append(('liq', P.c_ext((base + 3) & MASK))); expect.append(None)
        data = b''.join(item(c) for _, c in calls) + b'\0\0'
        w = World({PM: code, DRV: drv}); ok, ret = w.call(0, DRV, 0, data, False, 0)
        got = P.parse(ret); tot['cases'] += 1
        i = 0
        while i < len(calls):
            kind = calls[i][0]; ex = expect[i]; g_ok, g_ret = got[i]
            if kind == 'mod':
                tot['liquidityChanges'] += 1
                if ex == 'revert':
                    tot['reverts'] += 1
                    if g_ok: tot['mismatches'].append([case, i, 'liquidity change expected to revert'])
                elif not g_ok or delta(g_ret) != ex: tot['mismatches'].append([case, i, 'mod', g_ok, [str(x) for x in delta(g_ret)] if g_ok else g_ret.hex()[:16], [str(x) for x in ex]])
            elif kind == 'swap':
                if ex == 'revert':
                    tot['reverts'] += 1
                    if g_ok: tot['mismatches'].append([case, i, 'swap expected to revert'])
                    break
                tot['swaps'] += 1
                slot0 = int.from_bytes(got[i + 1][1], 'big'); liq = int.from_bytes(got[i + 2][1], 'big')
                state = (slot0 & ((1 << 160) - 1), s(ref_signextend(2, (slot0 >> 160) & 0xffffff)), liq)
                if not g_ok or delta(g_ret) != ex[:2] or state != ex[2:]:
                    tot['mismatches'].append([case, i, 'swap', g_ok, [str(x) for x in (delta(g_ret) if g_ok else ())], [str(x) for x in ex], [str(x) for x in state]])
            i += 1
    tot['seconds'] = round(time.time() - t0); tot['mismatchCount'] = len(tot['mismatches']); tot['mismatches'] = tot['mismatches'][:20]
    print(tot)
    json.dump(tot, open(out, 'w'), indent=1)
