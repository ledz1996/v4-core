"""v3check.py: mined Uniswap v3 style swaps on HyperEVM against the exact formulas of src/libraries.

Stage A (no RPC): every swap of the pools in raw/pools999.json, in (block, logIndex) order per pool, with the
pre-state carried from the previous Swap log of the pool (price, tick, liquidity) and moved by the Mint and
Burn logs in between (liquidity changes when tickLower <= tick < tickUpper). Each swap is tried as one step
of the v3 swap step (same FullMath, SqrtPriceMath and TickMath functions as tools/opdiff/v4math.py, the
transcription of src/libraries) and flagged when it reaches a branch of interest:
  m512      FullMath.mulDiv or mulDivRoundingUp with a product >= 2^256 (src/libraries/FullMath.sol)
  fallback  the overflow fallback of getNextSqrtPriceFromAmount0RoundingUp (src/libraries/SqrtPriceMath.sol)
  big160    a logged amount >= 2^160 (the mulDiv path of getNextSqrtPriceFromAmount1RoundingDown)
  onTick    the swap ends on a price that is exactly getSqrtPriceAtTick(t) for a multiple t of the spacing
Swaps that are not one step are flagged 'multi' when any of these could occur.
Stage B (read-only RPC, batched eth_call at block-1): for every (pool, block) that holds a flagged swap, slot0
and liquidity are read at the parent block, the pool's events in that block are applied in order, and each
swap is rerun through the whole v3 swap loop with the tick bitmap and liquidityNet read at the parent block
(and moved by earlier Mint and Burn logs of the block). The amounts, price, tick and liquidity in the log
must equal the rerun to the unit.

Usage: v3check.py <out.json> [--plant mulmod|fallback|tick|none] [--limit N] [--threads T] [--only m512,onTick,...]
"""
import sys, os, json, time, random, argparse, threading, collections, concurrent.futures as cf
import urllib.request, ssl
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import v4math as m
from evm import MASK

ap = argparse.ArgumentParser()
ap.add_argument('out'); ap.add_argument('--plant', default='none'); ap.add_argument('--limit', type=int, default=0)
ap.add_argument('--threads', type=int, default=6); ap.add_argument('--only', default=''); ap.add_argument('--seed', type=int, default=1)
ap.add_argument('--stageA-only', action='store_true')
A = ap.parse_args()
W = '/home/user/v4-core/research/network-risk/cycles/015/theme-closed-producers-2.work'  # inputs of cycle 15 (read only)
URL = 'https://rpc.purroofgroup.com'
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
U160 = (1 << 160) - 1
FEE_DEN = 10 ** 6

# ---------------------------------------------------------------- instrumentation of the branches
H = collections.Counter()
_md, _mdu, _n0 = m.mul_div, m.mul_div_rounding_up, m.next_price_amount0_rounding_up
def mul_div(a, b, d):
    if (a * b) >> 256: H['m512'] += 1
    return _md(a, b, d)
def mul_div_rounding_up(a, b, d):
    if (a * b) >> 256: H['m512'] += 1
    return _mdu(a, b, d)
def next0(p, liq, amount, add_):
    if amount and add_:
        prod = (amount * p) & MASK
        if not (prod // amount == p and ((liq << 96) + prod) & MASK >= (liq << 96)):
            H['fallback'] += 1
    return _n0(p, liq, amount, add_)
m.mul_div, m.mul_div_rounding_up, m.next_price_amount0_rounding_up = mul_div, mul_div_rounding_up, next0

# planted faults, to show that the comparison can fail on each branch class
_mm = m.mulmod; _gsp = m.get_sqrt_price_at_tick; _dru = m.div_rounding_up
def install_plant():
    global _n0
    if A.plant == 'mulmod':   # MULMOD by a modulus other than 2^256-1 returns one more when the product needs 512 bits
        m.mulmod = lambda a, b, c: ((_mm(a, b, c) + 1) % c if c and c != MASK and (a * b) >> 256 else _mm(a, b, c))
    elif A.plant == 'fallback':  # the fallback rounds down
        def next0f(p, liq, amount, add_):
            if amount and add_:
                prod = (amount * p) & MASK
                if not (prod // amount == p and ((liq << 96) + prod) & MASK >= (liq << 96)):
                    H['fallback'] += 1
                    return ((liq << 96) // ((liq << 96) // p + amount)) & U160
            return _n0(p, liq, amount, add_)
        m.next_price_amount0_rounding_up = next0f
    elif A.plant == 'tick':  # getSqrtPriceAtTick one unit high for ticks that are multiples of 10
        m.get_sqrt_price_at_tick = lambda t: _gsp(t) + (1 if t % 10 == 0 else 0)
    
# ---------------------------------------------------------------- v3 swap step and loop
def v3_step(cur, target, L, rem, fee):
    """Uniswap v3 SwapMath.computeSwapStep with rem < 0 for exact input (v4 sign), built from the same library functions."""
    zfo = cur >= target; exact_in = rem < 0
    if exact_in:
        less = m.mul_div(-rem, FEE_DEN - fee, FEE_DEN)
        a_in = m.amount0_delta(target, cur, L, True) if zfo else m.amount1_delta(cur, target, L, True)
        nxt = target if less >= a_in else m.next_price_from_input(cur, L, less, zfo)
    else:
        a_out = m.amount1_delta(target, cur, L, False) if zfo else m.amount0_delta(cur, target, L, False)
        nxt = target if rem >= a_out else m.next_price_from_output(cur, L, rem, zfo)
    mx = target == nxt
    if zfo:
        if not (mx and exact_in): a_in = m.amount0_delta(nxt, cur, L, True)
        if not (mx and not exact_in): a_out = m.amount1_delta(nxt, cur, L, False)
    else:
        if not (mx and exact_in): a_in = m.amount1_delta(cur, nxt, L, True)
        if not (mx and not exact_in): a_out = m.amount0_delta(cur, nxt, L, False)
    if not exact_in and a_out > rem: a_out = rem
    f = (-rem - a_in) if (exact_in and nxt != target) else m.mul_div_rounding_up(a_in, fee, FEE_DEN - fee)
    return nxt, a_in, a_out, f

def loop(view, p, tick, liq, zfo, amount, limit, fee, max_steps=3000):
    rem = amount; s_in = 0; s_out = 0; steps = 0
    while rem != 0 and p != limit:
        steps += 1
        if steps > max_steps: raise m.Revert('steps')
        start = p
        tn, init = view.next_tick(tick, zfo)
        tn = max(m.MIN_TICK, min(m.MAX_TICK, tn))
        pn = m.get_sqrt_price_at_tick(tn)
        target = (limit if pn < limit else pn) if zfo else (limit if pn > limit else pn)
        p, a_in, a_out, f = v3_step(p, target, liq, rem, fee)
        if amount < 0: rem += a_in + f
        else: rem -= a_out
        s_in += a_in + f; s_out += a_out
        if p == pn:
            if init:
                net = view.net(tn)
                liq = liq - net if zfo else liq + net
                if liq < 0 or liq >> 128: raise m.Revert('liq')
            tick = tn - 1 if zfo else tn
        elif p != start:
            tick = m.get_tick_at_sqrt_price(p)
    return p, tick, liq, s_in, s_out, steps

def expect(zfo, a0, a1):  # v3 log: positive = paid into the pool
    return (a0, -a1) if zfo else (a1, -a0)

# ---------------------------------------------------------------- data
pools = json.load(open(os.path.join(W, 'raw/pools999.json')))['pools']
ev = collections.defaultdict(list)
for line in open(os.path.join(W, 'raw/logs999.jsonl')):
    for r in json.loads(line)['rows']:
        if r[4] in pools: ev[r[4]].append(r)
for p in ev: ev[p].sort(key=lambda r: (r[1], r[2]))

def tick_of(price):
    t = m.get_tick_at_sqrt_price(price)
    return t if m.get_sqrt_price_at_tick(t) == price else None

class Flat:  # a view with no initialized ticks: one step means no initialized tick was crossed
    def next_tick(self, tick, lte): return (m.MIN_TICK if lte else m.MAX_TICK), False
    def net(self, t): return 0

st = collections.Counter(); flagged = set(); gflags = collections.defaultdict(set); perpool = collections.Counter(); ex = collections.defaultdict(list)
for pool, rows in ev.items():
    fee, sp = pools[pool]['fee'], pools[pool]['tickSpacing']
    pre = None
    for r in rows:
        if r[0] in ('M', 'B'):
            if pre is not None and r[5] <= pre[1] < r[6]: pre = (pre[0], pre[1], pre[2] + r[7])
            continue
        a0, a1, p1, L1, t1 = r[5], r[6], r[7], r[8], r[9]
        st['swaps'] += 1; perpool[pool] += 1
        if not (m.MIN_SQRT_PRICE <= p1 < m.MAX_SQRT_PRICE): st['priceOutOfRange'] += 1; pre = None; continue
        flags = set()
        tt = tick_of(p1)
        if tt is not None and tt % sp == 0: flags.add('onTick')
        if max(abs(a0), abs(a1)) >> 160: flags.add('big160')
        one = None
        if pre is not None and pre[2] > 0 and p1 != pre[0]:
            p0, tk0, L0 = pre; zfo = p1 < p0
            paid, got = expect(zfo, a0, a1)
            for mode, amt, lim in (('exactIn', -paid, p1), ('exactOut', got, p1)):
                if amt == 0: continue
                H.clear()
                try:
                    q, a_in, a_out, f = v3_step(p0, lim, L0, amt, fee)
                except m.Revert: continue
                if q == p1 and a_in + f == paid and a_out == got and L1 == L0:
                    one = mode; flags |= {k for k, v in H.items() if v}; break
            if one is None:
                # not one step without crossing: could any branch of interest occur inside?
                Lm = max(L0, L1)
                if (Lm * max(p0, p1)) >> 160 or (Lm * abs(p1 - p0)) >> 160: flags.add('m512?')
                if (abs(a0) * max(p0, p1)) >> 256: flags.add('fallback?')
                flags.add('multi')
        elif pre is None: flags.add('noPre')
        if one: st['single:' + one] += 1
        for f_ in flags: st['flag:' + f_] += 1
        key = {k for k in flags if k in ('m512', 'fallback', 'big160', 'onTick', 'm512?', 'fallback?')}
        if key and 'noPre' not in flags:
            flagged.add((pool, r[1])); gflags[(pool, r[1])] |= key
            for k in key:
                if len(ex[k]) < 5: ex[k].append(r[3])
        pre = (p1, t1, L1)
print('stageA', dict(st), 'groups', len(flagged), flush=True)
if A.stageA_only:
    json.dump({'stageA': st, 'groups': len(flagged), 'examples': ex}, open(A.out, 'w'), indent=1); sys.exit()

# ---------------------------------------------------------------- stage B
# the plant goes in after stage A, so that both runs pick the same groups and only the stage B comparison sees the fault
install_plant()
groups = sorted(flagged)
if A.only:
    want = set(A.only.split(','))
    groups = [g for g in groups if gflags[g] & want]
print('groups selected', len(groups), collections.Counter(k for g in groups for k in gflags[g]), flush=True)
rnd = random.Random(A.seed)
# cycle 17: leave out the groups that cycle 15 already ran (seed 1, limits 5000 and 20000), then sample the rest
done_ = set(random.Random(1).sample(groups, 20000)) | set(random.Random(1).sample(groups, 5000))
groups = [g for g in groups if g not in done_]
print('groups not run in cycle 15', len(groups), flush=True)
if A.limit and len(groups) > A.limit: groups = sorted(rnd.sample(groups, A.limit))
STOP = int(os.environ.get('STOP', '0'))
if STOP: groups = groups[:STOP]
MISF = open(A.out + '.mismatch.jsonl', 'w')

def batch(calls):
    """calls: list of (to, data, block). Returns list of hex results (None on revert)."""
    out = [None] * len(calls)
    for i in range(0, len(calls), 100):
        part = calls[i:i + 100]
        req = [{'jsonrpc': '2.0', 'id': j, 'method': 'eth_call', 'params': [{'to': t, 'data': d}, hex(b)]} for j, (t, d, b) in enumerate(part)]
        for k in range(8):
            try:
                r = json.loads(urllib.request.urlopen(urllib.request.Request(URL, json.dumps(req).encode(), {'content-type': 'application/json'}), timeout=120, context=CTX).read())
                if not isinstance(r, list): raise RuntimeError(str(r)[:200])
                for x in r:
                    if 'error' in x and 'revert' not in str(x['error']).lower(): raise RuntimeError(str(x['error'])[:200])
                    out[i + x['id']] = x.get('result')
                break
            except Exception as e:
                if k == 7: raise
                time.sleep(2 + 2 * k)
    return out

def enc_int(x): return (x & MASK).to_bytes(32, 'big').hex()
def s128(x): return x - (1 << 256) if x >> 255 else x  # ABI words of int128 are sign extended to 256 bits

class View:
    def __init__(self, pool, block, sp):
        self.pool, self.b, self.sp, self.cache, self.over = pool, block - 1, sp, {}, {}
    def _get(self, kind, k):
        if (kind, k) in self.over: return self.over[(kind, k)]
        if (kind, k) not in self.cache:
            sel = '0x5339c296' if kind == 'w' else '0xf30dba93'
            res = batch([(self.pool, sel + enc_int(k), self.b)])[0]
            if kind == 'w': self.cache[(kind, k)] = int(res, 16)
            else: self.cache[(kind, k)] = (int(res[2:66], 16), s128(int(res[66:130], 16)))
        return self.cache[(kind, k)]
    def word(self, w): return self._get('w', w)
    def net(self, t): return self._get('t', t)[1]
    def apply(self, tl, tu, delta):  # Mint (delta > 0) or Burn (delta < 0): Tick.update and TickBitmap.flipTick
        for t, upper in ((tl, False), (tu, True)):
            g, n = self._get('t', t)
            g2 = g + delta; flipped = (g2 == 0) != (g == 0)
            n2 = n - delta if upper else n + delta
            self.over[('t', t)] = (g2, n2) if g2 else (0, 0)
            if flipped:
                c = t // self.sp
                self.over[('w', c >> 8)] = self.word(c >> 8) ^ (1 << (c & 0xff))
    def next_tick(self, tick, lte):
        sp = self.sp
        c = tick // sp if tick >= 0 or tick % sp == 0 else tick // sp  # floor division equals v3 compress
        if lte:
            w, bit = c >> 8, c & 0xff
            masked = self.word(w) & (MASK >> (255 - bit))
            return ((c - (bit - m.most_significant_bit(masked))) * sp, True) if masked else ((c - bit) * sp, False)
        c += 1
        w, bit = c >> 8, c & 0xff
        masked = self.word(w) & (MASK ^ ((1 << bit) - 1))
        return ((c + (m.least_significant_bit(masked) - bit)) * sp, True) if masked else ((c + (255 - bit)) * sp, False)

lock = threading.Lock(); R = collections.Counter(); bad = []; hits_tot = collections.Counter(); matched_ex = collections.defaultdict(list)

def run_group(g):
    pool, block = g
    fee, sp = pools[pool]['fee'], pools[pool]['tickSpacing']
    rows = [r for r in ev[pool] if r[1] == block]
    s0, lq = batch([(pool, '0x3850c7bd', block - 1), (pool, '0x1a686502', block - 1)])
    if not s0 or not lq: return [('noState', None, None)]
    p = int(s0[2:66], 16); tick = m.s(int(s0[66:130], 16)) if hasattr(m, 's') else None
    t_raw = int(s0[66:130], 16); tick = t_raw - (1 << 256) if t_raw >> 255 else t_raw
    liq = int(lq, 16)
    view = View(pool, block, sp); res = []
    for r in rows:
        if r[0] in ('M', 'B'):
            if r[7]:
                view.apply(r[5], r[6], r[7])
                if r[5] <= tick < r[6]: liq += r[7]
            continue
        a0, a1, p1, L1, t1 = r[5], r[6], r[7], r[8], r[9]
        if a0 == 0 and a1 == 0 and p1 == p and t1 == tick and L1 == liq:
            res.append(('zero', r, {})); continue
        ok = None
        for zfo in ([p1 < p] if p1 != p else [True, False]):
            paid, got = expect(zfo, a0, a1)
            edge = m.MIN_SQRT_PRICE + 1 if zfo else m.MAX_SQRT_PRICE - 1
            big = 1 << 200
            for mode, amt, lim in (('exactIn', -paid, edge), ('exactOut', got, edge), ('exactIn', -paid, p1), ('exactOut', got, p1),
                                   ('toLimitIn', -big, p1), ('toLimitOut', big, p1)):
                if amt == 0 or lim == p or (zfo and lim > p) or ((not zfo) and lim < p): continue
                H.clear()
                try:
                    q, tk, l2, s_in, s_out, steps = loop(view, p, tick, liq, zfo, amt, lim, fee)
                except m.Revert:
                    continue
                if q == p1 and tk == t1 and l2 == L1 and s_in == paid and s_out == got:
                    ok = (mode, steps, dict(H)); break
            if ok: break
        if not ok and p1 != p:
            # The pool may charge a fee other than fee() (dynamic fee forks). Search the fee in pips that makes the
            # exact-input loop land on the logged price (the landing price falls as the fee falls for zeroForOne),
            # then require every logged field to equal the rerun at that fee or a neighbour.
            zfo = p1 < p; paid, got = expect(zfo, a0, a1)
            edge = m.MIN_SQRT_PRICE + 1 if zfo else m.MAX_SQRT_PRICE - 1
            def land(fe):
                try: return loop(view, p, tick, liq, zfo, -paid, edge, fe)
                except m.Revert: return None
            lo_, hi_ = 0, 999999
            if paid > 0:
                for _ in range(22):
                    mid = (lo_ + hi_) // 2; q = land(mid)
                    if q is None: lo_ = mid + 1; continue
                    moved_far = (q[0] < p1) if zfo else (q[0] > p1)
                    if moved_far: lo_ = mid + 1
                    else: hi_ = mid
                    if lo_ >= hi_: break
                def land2(fe, amt, lim):
                    try: return loop(view, p, tick, liq, zfo, amt, lim, fe)
                    except m.Revert: return None
                cands = list(range(max(0, lo_ - 3), min(999999, lo_ + 4)))
                if got > 0:  # exact output: the amount paid rises with the fee
                    lo2, hi2 = 0, 999999
                    for _ in range(22):
                        mid = (lo2 + hi2) // 2; q = land2(mid, got, edge)
                        if q is None: hi2 = mid; continue
                        if q[3] < paid: lo2 = mid + 1
                        else: hi2 = mid
                        if lo2 >= hi2: break
                    cands += list(range(max(0, lo2 - 3), min(999999, lo2 + 4)))
                for fe in cands:
                    for amt, lim in ((-paid, edge), (got, edge), (-paid, p1), (got, p1), (-(1 << 200), p1)):
                        if amt == 0: continue
                        H.clear(); q = land2(fe, amt, lim)
                        if q and q[0] == p1 and q[1] == t1 and q[2] == L1 and q[3] == paid and q[4] == got:
                            ok = ('feeSearch', q[5], dict(H)); break
                    if ok: break
        res.append(('ok' if ok else 'mismatch', r, ok))
        p, tick, liq = p1, t1, L1  # carry the logged state forward
    return res

t0 = time.time(); n = 0
with cf.ThreadPoolExecutor(A.threads) as exr:
    for res in exr.map(run_group, groups):
        n += 1
        with lock:
            for kind, r, ok in res:
                R[kind] += 1
                if kind == 'ok':
                    mode, steps, hh = ok
                    R['mode:' + mode] += 1; R['multiStep' if steps > 1 else 'oneStep'] += 1
                    for k, v in hh.items():
                        if v: R['branch:' + k] += 1; hits_tot[k] += v
                    tt = tick_of(r[7])
                    if tt is not None and tt % pools[r[4]]['tickSpacing'] == 0:
                        R['branch:onTick'] += 1
                        if r[8] != 0 and len(matched_ex['onTick']) < 10: matched_ex['onTick'].append(r[3])
                    if max(abs(r[5]), abs(r[6])) >> 160: R['branch:big160'] += 1; matched_ex['big160'].append(r[3])
                    for k in ('fallback', 'm512'):
                        if hh.get(k) and len(matched_ex[k]) < 10: matched_ex[k].append(r[3])
                elif kind == 'mismatch':
                    MISF.write(json.dumps({'tx': r[3], 'block': r[1], 'logIndex': r[2], 'pool': r[4], 'row': [str(x) for x in r]}) + '\n'); MISF.flush()
                    bad.append({'tx': r[3], 'block': r[1], 'logIndex': r[2], 'pool': r[4], 'a0': str(r[5]), 'a1': str(r[6]), 'price': str(r[7]), 'liq': str(r[8]), 'tick': r[9]})
        if n % 500 == 0:
            print(n, len(groups), round(time.time() - t0), dict(R), flush=True)
            json.dump({'partial': True, 'n': n, 'R': R}, open(A.out + '.part', 'w'))
json.dump({'plant': A.plant, 'stageA': st, 'groupsFlagged': len(flagged), 'groupsRun': len(groups), 'stageB': R, 'branchCalls': hits_tot,
           'mismatches': bad, 'examples': matched_ex, 'perPoolSwaps': perpool.most_common(30), 'seconds': round(time.time() - t0)}, open(A.out, 'w'), indent=1)
print('done', dict(R), flush=True)
