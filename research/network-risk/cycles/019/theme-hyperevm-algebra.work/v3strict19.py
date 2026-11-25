"""Cycle 19 Task 1: strict rerun of the cycle 18 v3 style swaps that touched the 512 bit branch of FullMath.mulDiv.

Group set: every group of cycles/018/theme-hyperevm-v3-rest.work/out/rest-*.json.groups.jsonl whose counts hold
branch:m512 (34,534 groups, 36,665 swaps on the branch in cycle 18).
For each swap of such a group the script runs
  lenient: the cycle 18 rule (fee from PoolCreated, limits open or at the logged price, then the fee search),
           so the swaps that cycle 18 counted on the branch are found again;
  strict:  the fee read from the pool at the parent block (fee() at block-1), moved by every FeeAdjustment(uint24,uint24)
           log (topic 0x0cba8718) of the pool earlier in the block; only the open price limit (MIN+1 or MAX-1);
           exact input with the logged paid amount, or exact output with the logged received amount.
           If neither matches, the transaction input is read and, only when a 32 byte word of it equals the logged price,
           the rerun is repeated with that word as the price limit (mode limitInCalldata).
  needBranch: for a strict match whose rerun took the 512 bit branch, the same rerun with every 512 bit result of
           mulDiv and mulDivRoundingUp replaced by result+1 (deliberately wrong) must fail to match.
Read-only eth_call, eth_getLogs and eth_getTransactionByHash on the archive client. Every swap result is written to
<out>.swaps.jsonl, every strict mismatch in full to <out>.mismatch.jsonl.
Usage: v3strict19.py <out> [--shard k/n] [--threads T] [--plant none|mulmod|tick] [--groups FILE] [--cache FILE]
"""
import sys, os, json, time, argparse, threading, collections, concurrent.futures as cf, urllib.request, ssl
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import v4math as m
from evm import MASK

ap = argparse.ArgumentParser()
ap.add_argument('out'); ap.add_argument('--shard', default='0/1'); ap.add_argument('--threads', type=int, default=6)
ap.add_argument('--plant', default='none'); ap.add_argument('--groups', default=''); ap.add_argument('--cache', default='')
ap.add_argument('--write-cache', default=''); ap.add_argument('--trace-args', action='store_true')
A = ap.parse_args()
URL = 'https://rpc.purroofgroup.com'
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
C18 = '/home/user/v4-core/research/network-risk/cycles/018/theme-hyperevm-v3-rest.work/out'
W15 = '/home/user/v4-core/research/network-risk/cycles/015/theme-closed-producers-2.work'
FEE_DEN = 10 ** 6
pools = json.load(open(os.path.join(W15, 'raw/pools999.json')))['pools']

# ------------------------------------------------ instrumentation (per thread) and the deliberately wrong branch
class _TL(threading.local):
    def __init__(self): self.c = collections.Counter(); self.wrong = False
_tl = _TL()
_md, _mdu = m.mul_div, m.mul_div_rounding_up
def mul_div(a, b, d):
    big = (a * b) >> 256
    if big: _tl.c['m512'] += 1
    r = _md(a, b, d)
    return (r + 1) & MASK if (big and _tl.wrong) else r
def mul_div_rounding_up(a, b, d):
    big = (a * b) >> 256
    if big: _tl.c['m512'] += 1
    r = _mdu(a, b, d)
    return (r + 1) & MASK if (big and _tl.wrong) else r
m.mul_div, m.mul_div_rounding_up = mul_div, mul_div_rounding_up
_mm = m.mulmod; _gsp = m.get_sqrt_price_at_tick
if A.plant == 'mulmod':
    m.mulmod = lambda a, b, c: ((_mm(a, b, c) + 1) % c if c and c != MASK and (a * b) >> 256 else _mm(a, b, c))
elif A.plant == 'tick':
    m.get_sqrt_price_at_tick = lambda t: _gsp(t) + (1 if t % 10 == 0 else 0)

# ------------------------------------------------ v3 swap step and loop (as cycle 18, v3check18.py)
def v3_step(cur, target, L, rem, fee):
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

def expect(zfo, a0, a1): return (a0, -a1) if zfo else (a1, -a0)

# ------------------------------------------------ RPC with an optional cache (so the plants see the same answers)
CACHE = {}
if A.cache and os.path.exists(A.cache):
    for l in open(A.cache):
        x = json.loads(l); CACHE[tuple(x['k'])] = x['v']
CW = open(A.write_cache, 'a') if A.write_cache else None
CLOCK = threading.Lock(); CACHE_ONLY = bool(A.cache) and not A.write_cache
def post(req):
    for k in range(8):
        try:
            r = json.loads(urllib.request.urlopen(urllib.request.Request(URL, json.dumps(req).encode(), {'content-type': 'application/json'}), timeout=120, context=CTX).read())
            return r
        except Exception:
            if k == 7: raise
            time.sleep(2 + 2 * k)
def cached(key, fn):
    key = tuple(key)
    if key in CACHE: return CACHE[key]
    if CACHE_ONLY: raise RuntimeError('cache miss %s' % (key,))
    v = fn()
    if CW is not None:
        with CLOCK: CW.write(json.dumps({'k': list(key), 'v': v}) + '\n'); CW.flush()
    return v
def get_logs(pool, b):
    r = post({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getLogs', 'params': [{'address': pool, 'fromBlock': hex(b), 'toBlock': hex(b)}]})
    if 'result' not in r: raise RuntimeError(str(r)[:200])
    return r['result']
def batch(calls):
    out = [None] * len(calls)
    for i in range(0, len(calls), 100):
        part = calls[i:i + 100]
        req = [{'jsonrpc': '2.0', 'id': j, 'method': 'eth_call', 'params': [{'to': t, 'data': d}, hex(b)]} for j, (t, d, b) in enumerate(part)]
        for k in range(8):
            r = post(req)
            if isinstance(r, list):
                bad = [x for x in r if 'error' in x and 'revert' not in str(x['error']).lower()]
                if not bad:
                    for x in r: out[i + x['id']] = x.get('result')
                    break
            if k == 7: raise RuntimeError(str(r)[:200])
            time.sleep(2 + 2 * k)
    return out
def tx_input(h):
    r = post({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getTransactionByHash', 'params': [h]})
    return (r.get('result') or {}).get('input', '0x')

def limit_in_input(inp, p1):
    """True when the big-endian bytes of p1 without leading zero bytes (at least 8 bytes) start at a byte boundary of the
    transaction input after the selector. This covers 32 byte ABI words, packed uint160 and shorter packed encodings."""
    h = '%x' % p1
    if len(h) % 2: h = '0' + h
    if len(h) < 16: h = h.rjust(16, '0')
    body = inp[10:] if inp.startswith('0x') else inp[8:]
    i = body.find(h)
    while i >= 0:
        if i % 2 == 0: return True
        i = body.find(h, i + 1)
    return False

def enc_int(x): return (x & MASK).to_bytes(32, 'big').hex()
def s256(x): return x - (1 << 256) if x >> 255 else x

class View:  # tick bitmap and liquidityNet at the parent block, moved by earlier Mint and Burn logs (cycle 18 class)
    def __init__(self, pool, block, sp):
        self.pool, self.b, self.sp, self.cache, self.over = pool, block - 1, sp, {}, {}
    def _get(self, kind, k):
        if (kind, k) in self.over: return self.over[(kind, k)]
        if (kind, k) not in self.cache:
            sel = '0x5339c296' if kind == 'w' else '0xf30dba93'
            res = cached((kind, self.pool, self.b + 1, k), lambda: batch([(self.pool, sel + enc_int(k), self.b)])[0])
            if kind == 'w': self.cache[(kind, k)] = int(res, 16)
            else: self.cache[(kind, k)] = (int(res[2:66], 16), s256(int(res[66:130], 16)))
        return self.cache[(kind, k)]
    def word(self, w): return self._get('w', w)
    def net(self, t): return self._get('t', t)[1]
    def apply(self, tl, tu, delta):
        for t, upper in ((tl, False), (tu, True)):
            g, n = self._get('t', t)
            g2 = g + delta; flipped = (g2 == 0) != (g == 0)
            n2 = n - delta if upper else n + delta
            self.over[('t', t)] = (g2, n2) if g2 else (0, 0)
            if flipped:
                c = t // self.sp
                self.over[('w', c >> 8)] = self.word(c >> 8) ^ (1 << (c & 0xff))
    def next_tick(self, tick, lte):
        sp = self.sp; c = tick // sp
        if lte:
            w, bit = c >> 8, c & 0xff
            masked = self.word(w) & (MASK >> (255 - bit))
            return ((c - (bit - m.most_significant_bit(masked))) * sp, True) if masked else ((c - bit) * sp, False)
        c += 1
        w, bit = c >> 8, c & 0xff
        masked = self.word(w) & (MASK ^ ((1 << bit) - 1))
        return ((c + (m.least_significant_bit(masked) - bit)) * sp, True) if masked else ((c + (255 - bit)) * sp, False)

SIG = {'0xc42079f9': 'S', '0x7a53080b': 'M', '0x0c396cd9': 'B', '0xd78218c0': 'V', '0x0cba8718': 'F'}
IGN = {'0x70935338'}
def rows_of(pool, b, logs):
    rows = []; other = collections.Counter()
    for l in logs:
        t = l['topics'][0][:10]; d = l['data'][2:]; w = [int(d[q:q + 64], 16) for q in range(0, len(d), 64)]; li = int(l['logIndex'], 16)
        k_ = SIG.get(t)
        if k_ == 'S': rows.append(['S', b, li, l['transactionHash'], pool, s256(w[0]), s256(w[1]), w[2], w[3], s256(w[4])])
        elif k_ == 'F': rows.append(['F', b, li, l['transactionHash'], pool, w[0], w[1]])
        elif k_ in ('M', 'B', 'V'):
            tl, tu = s256(int(l['topics'][2], 16)), s256(int(l['topics'][3], 16))
            amt = w[1] if k_ == 'M' else (-w[0] if k_ == 'B' else w[2])
            rows.append(['M' if amt > 0 else 'B', b, li, l['transactionHash'], pool, tl, tu, amt])
        elif t not in IGN: other[l['topics'][0][:10]] += 1
    rows.sort(key=lambda r: r[2])
    return rows, other

def attempt(view, p, tick, liq, zfo, amt, lim, fee, r):
    _tl.c.clear()
    try: q = loop(view, p, tick, liq, zfo, amt, lim, fee)
    except m.Revert: return None
    paid, got = expect(zfo, r[5], r[6])
    if q[0] == r[7] and q[1] == r[9] and q[2] == r[8] and q[3] == paid and q[4] == got:
        return {'steps': q[5], 'm512': _tl.c['m512']}
    return None

def lenient(view, p, tick, liq, r, fee):
    """The cycle 18 rule, kept to find again the swaps cycle 18 counted on the 512 bit branch."""
    a0, a1, p1 = r[5], r[6], r[7]
    for zfo in ([p1 < p] if p1 != p else [True, False]):
        paid, got = expect(zfo, a0, a1)
        edge = m.MIN_SQRT_PRICE + 1 if zfo else m.MAX_SQRT_PRICE - 1
        for mode, amt, lim in (('exactIn', -paid, edge), ('exactOut', got, edge), ('exactIn', -paid, p1), ('exactOut', got, p1),
                               ('toLimitIn', -(1 << 200), p1), ('toLimitOut', 1 << 200, p1)):
            if amt == 0 or lim == p or (zfo and lim > p) or ((not zfo) and lim < p): continue
            ok = attempt(view, p, tick, liq, zfo, amt, lim, fee, r)
            if ok: return dict(ok, mode=mode)
    if p1 == p: return None
    zfo = p1 < p; paid, got = expect(zfo, a0, a1)
    edge = m.MIN_SQRT_PRICE + 1 if zfo else m.MAX_SQRT_PRICE - 1
    def land(fe, amt, lim):
        try: return loop(view, p, tick, liq, zfo, amt, lim, fe)
        except m.Revert: return None
    if paid <= 0: return None
    lo_, hi_ = 0, 999999
    for _ in range(22):
        mid = (lo_ + hi_) // 2; q = land(mid, -paid, edge)
        if q is None: lo_ = mid + 1; continue
        if ((q[0] < p1) if zfo else (q[0] > p1)): lo_ = mid + 1
        else: hi_ = mid
        if lo_ >= hi_: break
    cands = list(range(max(0, lo_ - 3), min(999999, lo_ + 4)))
    if got > 0:
        lo2, hi2 = 0, 999999
        for _ in range(22):
            mid = (lo2 + hi2) // 2; q = land(mid, got, edge)
            if q is None: hi2 = mid; continue
            if q[3] < paid: lo2 = mid + 1
            else: hi2 = mid
            if lo2 >= hi2: break
        cands += list(range(max(0, lo2 - 3), min(999999, lo2 + 4)))
    for fe in cands:
        for amt, lim in ((-paid, edge), (got, edge), (-paid, p1), (got, p1), (-(1 << 200), p1)):
            if amt == 0: continue
            ok = attempt(view, p, tick, liq, zfo, amt, lim, fe, r)
            if ok: return dict(ok, mode='feeSearch', fee=fe, limitAtLogged=(lim == p1))
    return None

S_TRACE = {}
def trace_fee(r):
    """r: swap row. Returns the fee the pool's swap call read from its factory, from debug_traceTransaction callTracer."""
    pool = r[4]
    t = cached(('trace', r[3]), lambda: post({'jsonrpc': '2.0', 'id': 1, 'method': 'debug_traceTransaction', 'params': [r[3], {'tracer': 'callTracer'}]}).get('result'))
    if not t: return None
    toks = {pools[pool]['token0'].lower(), pools[pool]['token1'].lower()}
    calls = []
    def walk(c):
        if (c.get('to') or '').lower() == pool and (c.get('input') or '')[:10] == '0x128acb08' and not c.get('error'):
            calls.append(c); return
        for k in c.get('calls', []): walk(k)
    walk(t)
    k = r[10] if len(r) > 10 else 0
    if k >= len(calls): return None
    def first(c):
        for x in c.get('calls', []):
            if (x.get('from') or '').lower() == pool and (x.get('to') or '').lower() not in toks and x.get('type') == 'STATICCALL' and len(x.get('output') or '') == 66:
                return int(x['output'], 16)
            y = first(x)
            if y is not None: return y
        return None
    return first(calls[k])

def trace_swap_args(r):
    """(zeroForOne, amountSpecified, sqrtPriceLimitX96) of the k-th successful swap call to the pool in the trace."""
    pool = r[4]
    t = cached(('trace', r[3]), lambda: post({'jsonrpc': '2.0', 'id': 1, 'method': 'debug_traceTransaction', 'params': [r[3], {'tracer': 'callTracer'}]}).get('result'))
    if not t: return None
    calls = []
    def walk(c):
        if (c.get('to') or '').lower() == pool and (c.get('input') or '')[:10] == '0x128acb08' and not c.get('error'):
            calls.append(c); return
        for x in c.get('calls', []): walk(x)
    walk(t)
    k = r[10]
    if k >= len(calls): return None
    h = calls[k]['input'][10:]; w = [int(h[i:i + 64], 16) for i in range(0, len(h) - 63, 64)]
    return (bool(w[1]), s256(w[2]), w[3])

def strict(view, p, tick, liq, r, fee):
    a0, a1, p1 = r[5], r[6], r[7]
    tried = []
    for zfo in ([p1 < p] if p1 != p else [True, False]):
        paid, got = expect(zfo, a0, a1)
        edge = m.MIN_SQRT_PRICE + 1 if zfo else m.MAX_SQRT_PRICE - 1
        for mode, amt in (('exactIn', -paid), ('exactOut', got)):
            if amt == 0: continue
            ok = attempt(view, p, tick, liq, zfo, amt, edge, fee, r)
            if ok: return dict(ok, mode=mode, amt=amt, lim=edge, zfo=zfo)
    # a fee read inside the pool's own swap call (fork pools whose swap asks the factory for the fee): the output of the
    # first one-word STATICCALL from the pool to an address other than its two tokens (the factory, or a fee contract) inside the k-th swap call of this pool in the transaction trace
    tf = None
    if not S_TRACE.get('off'):
        tf = trace_fee(r)
        if tf is not None and tf != fee:
            for zfo in ([p1 < p] if p1 != p else [True, False]):
                paid, got = expect(zfo, a0, a1)
                edge = m.MIN_SQRT_PRICE + 1 if zfo else m.MAX_SQRT_PRICE - 1
                for mode, amt in (('exactIn', -paid), ('exactOut', got)):
                    if amt == 0: continue
                    ok = attempt(view, p, tick, liq, zfo, amt, edge, tf, r)
                    if ok: return dict(ok, mode=mode + ':traceFee', amt=amt, lim=edge, zfo=zfo, fee=tf)
    # the limit is taken only from the transaction's own input
    inp = cached(('tx', r[3]), lambda: tx_input(r[3]))
    found = limit_in_input(inp, p1)
    if found and p1 != p:
        zfo = p1 < p; paid, got = expect(zfo, a0, a1)
        for mode, amt in (('limitInCalldataIn', -paid), ('limitInCalldataOut', got)):
            if amt == 0: continue
            ok = attempt(view, p, tick, liq, zfo, amt, p1, fee, r)
            if ok: return dict(ok, mode=mode, amt=amt, lim=p1, zfo=zfo)
    if A.trace_args:
        ta = trace_swap_args(r)
        if ta is not None:
            zfo, amt_spec, lim = ta
            paid, got = expect(zfo, a0, a1)
            for fe in ([fee] + ([tf] if (not S_TRACE.get('off') and tf is not None and tf != fee) else [])):
                ok = attempt(view, p, tick, liq, zfo, -amt_spec, lim, fe, r)
                if ok: return dict(ok, mode='traceArgs', amt=-amt_spec, lim=lim, zfo=zfo, fee=fe, traceArgs=[zfo, str(amt_spec), str(lim)])
    return {'fail': True, 'limitWordInInput': found}

def run_group(g):
    pool, block = g
    sp = pools[pool]['tickSpacing']; fee0 = pools[pool]['fee']
    logs = cached(('logs', pool, block), lambda: get_logs(pool, block))
    rows, other = rows_of(pool, block, logs)
    s0, lq, fe = cached(('state3', pool, block), lambda: batch([(pool, '0x3850c7bd', block - 1), (pool, '0x1a686502', block - 1), (pool, '0xddca3f43', block - 1)]))
    p = int(s0[2:66], 16); tick = s256(int(s0[66:130], 16)); liq = int(lq, 16)
    fee = int(fe, 16) if fe and fe != '0x' else None
    viewL = View(pool, block, sp); viewS = View(pool, block, sp)
    out = []
    feeSeq = []; ordinal = collections.Counter()
    for r in rows:
        if r[0] in ('M', 'B'):
            if r[7]:
                viewL.apply(r[5], r[6], r[7]); viewS.apply(r[5], r[6], r[7])
                if r[5] <= tick < r[6]: liq += r[7]
            continue
        if r[0] == 'F':
            feeSeq.append([r[2], r[5], r[6]])
            if fee is not None and r[5] != fee: feeSeq[-1].append('oldFeeDiffers')
            fee = r[6]; continue
        a0, a1, p1, L1, t1 = r[5], r[6], r[7], r[8], r[9]
        r = r + [ordinal[r[3]]]; ordinal[r[3]] += 1
        rec = {'tx': r[3], 'block': block, 'logIndex': r[2], 'pool': pool, 'feeRead': fee}
        if a0 == 0 and a1 == 0 and p1 == p and t1 == tick and L1 == liq:
            rec['kind'] = 'zero'; out.append((rec, r)); continue
        L = lenient(viewL, p, tick, liq, r, fee0)
        rec['lenient'] = L
        S = strict(viewS, p, tick, liq, r, fee) if fee is not None else {'fail': True, 'noFee': True}
        rec['strict'] = S
        if not S.get('fail') and S['m512']:
            _tl.wrong = True
            try: W = attempt(viewS, p, tick, liq, S['zfo'], S['amt'], S['lim'], fee, r)
            finally: _tl.wrong = False
            rec['needBranch'] = W is None
        out.append((rec, r))
        p, tick, liq = p1, t1, L1
    return out, other, feeSeq, logs, (s0, lq, fe)

def client_version():
    try: return post({'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []}).get('result')
    except Exception as e: return 'error ' + str(e)[:80]

if A.groups:
    groups = [tuple(x) for x in json.load(open(A.groups))]
else:
    groups = []
    for k in range(4):
        for l in open(os.path.join(C18, 'rest-%d.json.groups.jsonl' % k)):
            x = json.loads(l)
            if x['counts'].get('branch:m512'): groups.append(tuple(x['g']))
    groups.sort()
k_, n_ = map(int, A.shard.split('/')); groups = groups[k_::n_]
DONE = set()
if os.path.exists(A.out + '.groups.jsonl'):
    for l in open(A.out + '.groups.jsonl'):
        try: DONE.add(tuple(json.loads(l)['g']))
        except Exception: pass
todo = [g for g in groups if g not in DONE]
print('groups', len(groups), 'todo', len(todo), 'plant', A.plant, flush=True)
print('clientVersion start', URL, client_version(), time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), flush=True)
SF = open(A.out + '.swaps.jsonl', 'a'); MF = open(A.out + '.mismatch.jsonl', 'a'); GF = open(A.out + '.groups.jsonl', 'a')
R = collections.Counter(); lock = threading.Lock()
def safe(g):
    try: return g, run_group(g), None
    except Exception as e: return g, None, repr(e)[:300]
t0 = time.time(); n = 0
with cf.ThreadPoolExecutor(A.threads) as ex:
    for g, res, err in ex.map(safe, todo):
        n += 1
        with lock:
            if err:
                R['groupError'] += 1; GF.write(json.dumps({'g': list(g), 'error': err}) + '\n'); GF.flush(); continue
            out, other, feeSeq, logs, st = res
            C = collections.Counter()
            for rec, r in out:
                SF.write(json.dumps(rec) + '\n')
                if rec.get('kind') == 'zero': C['zero'] += 1; continue
                L = rec['lenient']; S = rec['strict']
                C['swaps'] += 1
                if L: C['lenientOk'] += 1
                if L and L['m512']: C['lenientM512'] += 1
                if not S.get('fail'):
                    C['strictOk'] += 1; C['strict:' + S['mode']] += 1
                    if S['m512']: C['strictM512'] += 1
                    if rec.get('needBranch'): C['needBranch'] += 1
                    if L and L['m512']:
                        C['c18m512_strictOk'] += 1
                        if S['m512']: C['c18m512_strictM512'] += 1
                        if rec.get('needBranch'): C['c18m512_needBranch'] += 1
                else:
                    C['strictFail'] += 1
                    if L and L['m512']: C['c18m512_strictFail'] += 1
                    MF.write(json.dumps({'rec': rec, 'row': [str(x) for x in r], 'feeSeq': feeSeq, 'parentState': st, 'liveLogs': logs, 'plant': A.plant}) + '\n')
            for k, v in C.items(): R[k] += v
            GF.write(json.dumps({'g': list(g), 'counts': C, 'other': dict(other), 'feeSeq': feeSeq}) + '\n'); GF.flush(); SF.flush(); MF.flush()
        if n % 1000 == 0:
            print(n, len(todo), round(time.time() - t0), dict(R), flush=True)
        if n % 5000 == 0: print('clientVersion', client_version(), time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), flush=True)
print('clientVersion end', URL, client_version(), time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), flush=True)
print('done', dict(R), 'seconds', round(time.time() - t0), flush=True)
