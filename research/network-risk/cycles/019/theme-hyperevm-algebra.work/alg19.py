"""Cycle 19 Task 2: mined swaps of the two Algebra Integral factories on HyperEVM against the formulas of src/libraries.

Pools: factory 0xf77bd082c627aa54591cf2f2eaa811fd1ab3b1f3 (Integral 1.0/1.1 interface: communityFeeLastTimestamp(), Fee(uint16))
and factory 0x5f95e92c338e6453111fc55ee66d4aafcce661a7 (Integral 1.2.2 interface: lastFeeTransferTimestamp(),
getPluginFeePending(), SwapFee(address,uint24,uint24) emitted before Swap). The swap step is the one of
cryptoalgebra/Algebra tags integral-v1.1 and integral-v1.2.2, src/core/contracts/base/SwapCalculation.sol and
libraries/PriceMovementMath.sol, built from the functions of tools/opdiff/v4math.py (the transcription of
src/libraries FullMath, SqrtPriceMath, TickMath). TokenDeltaMath.getToken0Delta/getToken1Delta equal
SqrtPriceMath.getAmount0Delta/getAmount1Delta and PriceMovementMath.getNewPrice equals getNextSqrtPriceFromInput/Output
operation by operation.

Per group (pool, block): eth_getLogs of the pool in the block; at block-1 globalState(), liquidity(), prevTickGlobal(),
nextTickGlobal(); ticks(t) at block-1 as the loop walks the linked list. Mint and Burn logs earlier in the block are applied
with TickManagement.update, TickStructure._addOrRemoveTicks (insert or remove in the linked list, move of
prevTickGlobal/nextTickGlobal) and the in-range liquidity rule of LiquidityMath.getAmountsForLiquidity.
Fee: globalState.lastFee at block-1, moved by every Fee(uint16) log; for a 1.2.2 pool the SwapFee log just before the
Swap gives overrideFee and pluginFee (fee = overrideFee + pluginFee if overrideFee != 0, else lastFee + pluginFee).
The fee is read, never searched. Limits: open only (MIN+1 / MAX-1); the logged price is used as the limit only when a
32 byte word of the transaction input equals it. The rerun must equal price, tick, liquidity, amount0 and amount1 of the
Swap log to the unit.
Usage: alg19.py <out> [--shard k/n] [--threads T] [--plant none|mulmod|tick] [--groups FILE] [--cache FILE] [--write-cache FILE]
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
FEE_DEN = 10 ** 6; Q96 = 1 << 96
SAMPLE = json.load(open('out/alg-sample.json'))
POOLS = SAMPLE['pools']
V122 = '0x5f95e92c338e6453111fc55ee66d4aafcce661a7'

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
_n0 = m.next_price_amount0_rounding_up
def next0(p, liq, amount, add_):
    if amount and add_:
        prod = (amount * p) & MASK
        if not (prod // amount == p and ((liq << 96) + prod) & MASK >= (liq << 96)): _tl.c['fallback'] += 1
    return _n0(p, liq, amount, add_)
m.next_price_amount0_rounding_up = next0
_mm = m.mulmod; _gsp = m.get_sqrt_price_at_tick
if A.plant == 'mulmod':
    m.mulmod = lambda a, b, c: ((_mm(a, b, c) + 1) % c if c and c != MASK and (a * b) >> 256 else _mm(a, b, c))
elif A.plant == 'tick':
    m.get_sqrt_price_at_tick = lambda t: _gsp(t) + (1 if t % 10 == 0 else 0)

# ------------------------------------------------ PriceMovementMath.movePriceTowardsTarget (Algebra sign: exact input > 0)
def in_delta(zto, to, frm, L):   # getInputTokenDelta01 / 10
    return m.amount0_delta(to, frm, L, True) if zto else m.amount1_delta(frm, to, L, True)
def out_delta(zto, to, frm, L):  # getOutputTokenDelta01 / 10
    return m.amount1_delta(to, frm, L, False) if zto else m.amount0_delta(frm, to, L, False)
def move(zto, cur, target, L, avail, fee):
    if avail >= 0:
        after = m.mul_div(avail, FEE_DEN - fee, FEE_DEN)
        inp = in_delta(zto, target, cur, L)
        if after >= inp:
            res = target; fa = m.mul_div_rounding_up(inp, fee, FEE_DEN - fee)
        else:
            res = m.next_price_from_input(cur, L, after, zto)
            if res == target: raise m.Revert('assert')
            inp = in_delta(zto, res, cur, L); fa = avail - inp
        out = out_delta(zto, res, cur, L)
    else:
        out = out_delta(zto, target, cur, L)
        av = -avail
        if av >= out: res = target
        else:
            res = m.next_price_from_output(cur, L, av, zto)
            if target != res: out = out_delta(zto, res, cur, L)
            if out > av: out = av
        inp = in_delta(zto, res, cur, L); fa = m.mul_div_rounding_up(inp, fee, FEE_DEN - fee)
    return res, inp, out, fa

# ------------------------------------------------ RPC and cache
CACHE = {}
if A.cache and os.path.exists(A.cache):
    for l in open(A.cache):
        x = json.loads(l); CACHE[tuple(x['k'])] = x['v']
CW = open(A.write_cache, 'a') if A.write_cache else None
CLOCK = threading.Lock(); CACHE_ONLY = bool(A.cache) and not A.write_cache
def post(req):
    for k in range(8):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(URL, json.dumps(req).encode(), {'content-type': 'application/json'}), timeout=120, context=CTX).read())
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
    req = [{'jsonrpc': '2.0', 'id': j, 'method': 'eth_call', 'params': [{'to': t, 'data': d}, hex(b)]} for j, (t, d, b) in enumerate(calls)]
    for k in range(8):
        r = post(req)
        if isinstance(r, list) and not [x for x in r if 'error' in x]:
            out = [None] * len(calls)
            for x in r: out[x['id']] = x['result']
            return out
        if k == 7: raise RuntimeError(str(r)[:300])
        time.sleep(2 + 2 * k)
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
def words(h): h = h[2:]; return [int(h[i:i + 64], 16) for i in range(0, len(h), 64)]

class Ticks:
    """TickManagement.Tick (liquidityTotal, liquidityDelta, prevTick, nextTick) at block-1 plus the changes of earlier logs."""
    def __init__(self, pool, block): self.pool, self.b, self.cache, self.over = pool, block - 1, {}, {}
    def get(self, t):
        if t in self.over: return self.over[t]
        if t not in self.cache:
            res = cached(('tick', self.pool, self.b + 1, t), lambda: batch([(self.pool, '0xf30dba93' + enc_int(t), self.b)])[0])
            w = words(res); self.cache[t] = (w[0], s256(w[1]), s256(w[2]), s256(w[3]))
        return self.cache[t]
    def put(self, t, v): self.over[t] = v

class Pool:
    def __init__(self, pool, block, gs, lq, pg, ng):
        w = words(gs)
        self.price, self.tick, self.lastFee, self.pluginConfig, self.communityFee = w[0], s256(w[1]), w[2], w[3], w[4]
        self.liq = int(lq, 16); self.prevG = s256(int(pg, 16)); self.nextG = s256(int(ng, 16))
        self.T = Ticks(pool, block)
    def _update(self, t, delta, upper):
        tot, d, pv, nx = self.T.get(t)
        after = tot + delta
        if after < 0 or after >> 128: raise m.Revert('liquidityTotal')
        d2 = d - delta if upper else d + delta
        flipped = after == 0
        if tot == 0: flipped = not flipped
        self.T.put(t, (after, d2, pv, nx))
        return flipped
    def _remove(self, t):
        tot, d, pv, nx = self.T.get(t)
        if t in (m.MIN_TICK, m.MAX_TICK): self.T.put(t, (0, 0, pv, nx))
        else:
            if pv == nx: raise m.Revert('tickIsNotInitialized')
            self.T.put(t, (0, 0, 0, 0))
            a = self.T.get(pv); self.T.put(pv, (a[0], a[1], a[2], nx))
            b = self.T.get(nx); self.T.put(nx, (b[0], b[1], pv, b[3]))
        return pv, nx
    def _next_initialized_above(self, t):  # TickTree.getNextTick: the first initialized tick > t, found on the linked list
        n = self.prevG
        while n > t: n = self.T.get(n)[2]
        while self.T.get(n)[3] <= t: n = self.T.get(n)[3]
        return self.T.get(n)[3]
    def _add_or_remove(self, t, prevI, nextI, remove):
        if remove:
            pv, nx = self._remove(t)
            if prevI == t: prevI = pv
            elif nextI == t: nextI = nx
        else:
            if prevI < t < nextI:
                pv, nx = prevI, nextI
                if t > self.tick: nextI = t
                else: prevI = t
            else:
                nx = self._next_initialized_above(t); pv = self.T.get(nx)[2]
            if t not in (m.MIN_TICK, m.MAX_TICK):
                if not (pv < t < nx): raise m.Revert('tickInvalidLinks')
                a = self.T.get(t); self.T.put(t, (a[0], a[1], pv, nx))
                x = self.T.get(pv); self.T.put(pv, (x[0], x[1], x[2], t))
                y = self.T.get(nx); self.T.put(nx, (y[0], y[1], t, y[3]))
        return prevI, nextI
    def modify(self, bottom, top, delta):
        if delta == 0: return
        tb = self._update(bottom, delta, False); tt = self._update(top, delta, True)
        if tb or tt:
            pI, nI = self.prevG, self.nextG
            if tb: pI, nI = self._add_or_remove(bottom, pI, nI, delta < 0)
            if tt: pI, nI = self._add_or_remove(top, pI, nI, delta < 0)
            self.prevG, self.nextG = pI, nI
        if bottom <= self.tick < top: self.liq += delta
        if self.liq < 0: raise m.Revert('liq')

def calculate_swap(P, zto, amountRequired, limit, fee):
    """SwapCalculation._calculateSwap on a copy of the pool state. Returns amount0, amount1, price, tick, liquidity, steps."""
    if amountRequired == 0: raise m.Revert('zeroAmountRequired')
    exact = amountRequired > 0; initial = amountRequired
    L, prevI, nextI = P.liq, P.prevG, P.nextG
    cur, tick = P.price, P.tick
    if zto:
        if limit >= cur or limit <= m.MIN_SQRT_PRICE: raise m.Revert('invalidLimitSqrtPrice')
    else:
        if limit <= cur or limit >= m.MAX_SQRT_PRICE: raise m.Revert('invalidLimitSqrtPrice')
    calc = 0; steps = 0; crossed = []
    while True:
        steps += 1
        if steps > 5000: raise m.Revert('steps')
        nt = prevI if zto else nextI
        start = cur
        ntp = m.get_sqrt_price_at_tick(nt)
        target = limit if (zto == (ntp < limit)) else ntp
        cur, inp, out, fa = move(zto, cur, target, L, amountRequired, fee)
        if exact:
            amountRequired -= inp + fa; calc -= out
        else:
            amountRequired += out; calc += inp + fa
        if cur == ntp:
            tot, d, pv, nx = P.T.get(nt)
            if zto:
                d = -d; prevI = pv; tick, nextI = nt - 1, nt
            else:
                nextI = nx; tick, prevI = nt, nt
            L = L + d
            if L < 0 or L >> 128: raise m.Revert('addDelta')
            crossed.append(nt)
        elif cur != start:
            tick = m.get_tick_at_sqrt_price(cur); break
        if not (amountRequired != 0 and cur != limit): break
    spent = initial - amountRequired
    a0, a1 = (spent, calc) if zto == exact else (calc, spent)
    return a0, a1, cur, tick, L, steps, (L, prevI, nextI, bool(crossed))

SIG = {'0xc42079f9': 'S', '0x7a53080b': 'M', '0x0c396cd9': 'B', '0x598b9f04': 'F', '0x9443903d': 'SF'}
IGN = {'0x1a25098b', '0x70935338', '0xbdbdb71d', '0xef10ebb0', '0xb94331e4', '0x3647dccc', '0xb0b573c1'}  # BurnFee, Collect, Flash, ExcessTokens, Skim, CommunityFee, CommunityVault
def rows_of(logs):
    rows = []; other = collections.Counter()
    for l in logs:
        t = l['topics'][0][:10]; w = words(l['data']); li = int(l['logIndex'], 16); k = SIG.get(t)
        if k == 'S': rows.append(['S', li, l['transactionHash'], s256(w[0]), s256(w[1]), w[2], w[3], s256(w[4])])
        elif k == 'M': rows.append(['M', li, l['transactionHash'], s256(int(l['topics'][2], 16)), s256(int(l['topics'][3], 16)), w[1]])
        elif k == 'B': rows.append(['M', li, l['transactionHash'], s256(int(l['topics'][2], 16)), s256(int(l['topics'][3], 16)), -w[0]])
        elif k == 'F': rows.append(['F', li, l['transactionHash'], w[0]])
        elif k == 'SF': rows.append(['SF', li, l['transactionHash'], w[0], w[1]])
        else:
            other[l['topics'][0][:10]] += 1
            if t not in IGN: rows.append(['X', li, l['transactionHash'], l['topics'][0]])
    rows.sort(key=lambda r: r[1])
    return rows, other

def attempt(P, zto, amt, lim, fee, r):
    _tl.c.clear()
    try: q = calculate_swap(P, zto, amt, lim, fee)
    except m.Revert as e: return None, str(e)
    ok = q[0] == r[3] and q[1] == r[4] and q[2] == r[5] and q[4] == r[6] and q[3] == r[7]
    return ({'steps': q[5], 'm512': _tl.c['m512'], 'fallback': _tl.c['fallback'], 'crossed': q[6][3]} if ok else None), (q[:5] if not ok else None)

def trace_args(r, k):
    """Arguments of the k-th successful swap or swapWithPaymentInAdvance call to the pool in the transaction trace
    (debug_traceTransaction callTracer): (payInAdvance, zeroToOne, amount, limitSqrtPrice)."""
    pool = r[8]
    t = cached(('trace', r[2]), lambda: post({'jsonrpc': '2.0', 'id': 1, 'method': 'debug_traceTransaction', 'params': [r[2], {'tracer': 'callTracer'}]}).get('result'))
    if not t: return None
    calls = []
    def walk(c):
        sel = (c.get('input') or '')[:10]
        if (c.get('to') or '').lower() == pool and sel in ('0x128acb08', '0x9e4e0227') and not c.get('error'):
            calls.append(c); return
        for x in c.get('calls', []): walk(x)
    walk(t)
    if k >= len(calls): return None
    c = calls[k]; w = words('0x' + c['input'][10:])
    if c['input'][:10] == '0x128acb08': return (False, bool(w[1]), s256(w[2]), w[3])
    return (True, bool(w[2]), s256(w[3]), w[4])

def rerun(P, r, fee):
    a0, a1, p1 = r[3], r[4], r[5]
    tries = []
    for zto in ([p1 < P.price] if p1 != P.price else [True, False]):
        paid = a0 if zto else a1; got = -(a1 if zto else a0)
        edge = m.MIN_SQRT_PRICE + 1 if zto else m.MAX_SQRT_PRICE - 1
        for mode, amt in (('exactIn', paid), ('exactOut', -got)):
            if amt == 0: continue
            ok, q = attempt(P, zto, amt, edge, fee, r)
            if ok: return dict(ok, mode=mode, zto=zto, amt=amt, lim=edge)
            tries.append([mode, zto, str(q)])
    if p1 != P.price:
        inp = cached(('tx', r[2]), lambda: tx_input(r[2]))
        found = limit_in_input(inp, p1)
        if found:
            zto = p1 < P.price; paid = a0 if zto else a1; got = -(a1 if zto else a0)
            for mode, amt in (('limitInCalldataIn', paid), ('limitInCalldataOut', -got)):
                if amt == 0: continue
                ok, q = attempt(P, zto, amt, p1, fee, r)
                if ok: return dict(ok, mode=mode, zto=zto, amt=amt, lim=p1)
                tries.append([mode, zto, str(q)])
        if A.trace_args:
            ta = trace_args(r, r[9])
            if ta is not None:
                adv, zto, amt, lim = ta
                paid = a0 if zto else a1
                ok, q = attempt(P, zto, paid if adv else amt, lim, fee, r)
                if ok: return dict(ok, mode='traceArgs' + ('Advance' if adv else ''), zto=zto, amt=paid if adv else amt, lim=lim, traceArgs=list(map(str, ta)))
                tries.append(['traceArgs', str(ta), str(q)])
        # diagnostic only, never counted as a match: does the swap fit with the limit set to the logged price?
        zto = p1 < P.price; paid = a0 if zto else a1; got = -(a1 if zto else a0); diag = []
        for mode, amt in (('in', paid), ('out', -got)):
            if amt == 0: continue
            ok, q = attempt(P, zto, amt, p1, fee, r)
            if ok: diag.append(mode)
        return {'fail': True, 'limitWordInInput': found, 'tries': tries, 'diagLimitAtLoggedFits': diag}
    return {'fail': True, 'tries': tries}

def run_group(g):
    pool, block = g
    v122 = POOLS[pool] == V122
    logs = cached(('logs', pool, block), lambda: get_logs(pool, block))
    rows, other = rows_of(logs)
    gs, lq, pg, ng = cached(('state', pool, block), lambda: batch([(pool, '0xe76c01e4', block - 1), (pool, '0x1a686502', block - 1), (pool, '0x050a4d21', block - 1), (pool, '0xd5c35a7e', block - 1)]))
    P = Pool(pool, block, gs, lq, pg, ng)
    parent = {'price': P.price, 'tick': P.tick, 'lastFee': P.lastFee, 'pluginConfig': P.pluginConfig, 'communityFee': P.communityFee, 'liquidity': P.liq, 'prevTickGlobal': P.prevG, 'nextTickGlobal': P.nextG}
    out = []; pend = None; unknown = []; ordinal = collections.Counter()
    for r in rows:
        if r[0] == 'M': P.modify(r[3], r[4], r[5]); continue
        if r[0] == 'F': P.lastFee = r[3]; continue
        if r[0] == 'SF': pend = (r[3], r[4], r[2]); continue
        if r[0] == 'X': unknown.append(r[3]); continue
        # Swap
        r = r + [pool, ordinal[r[2]]]; ordinal[r[2]] += 1
        if v122:
            ov, pf = (pend[0], pend[1]) if (pend and pend[2] == r[2]) else (0, 0)
            fee = (ov + pf) if ov else (P.lastFee + pf)
            fsrc = {'lastFee': P.lastFee, 'overrideFee': ov, 'pluginFee': pf, 'swapFeeLog': bool(pend and pend[2] == r[2])}
        else:
            fee = P.lastFee; fsrc = {'lastFee': P.lastFee}
        pend = None
        rec = {'tx': r[2], 'block': block, 'logIndex': r[1], 'pool': pool, 'fee': fee, 'feeSource': fsrc}
        res = rerun(P, r, fee) if fee < FEE_DEN else {'fail': True, 'feeTooHigh': True}
        rec['res'] = res
        if not res.get('fail') and res['m512']:
            _tl.wrong = True
            try: w, _ = attempt(P, res['zto'], res['amt'], res['lim'], fee, r)
            finally: _tl.wrong = False
            rec['needBranch'] = w is None
        out.append((rec, r))
        # carry the logged state forward; the linked list pointers follow the rerun when it matched
        if not res.get('fail'):
            q = calculate_swap(P, res['zto'], res['amt'], res['lim'], fee)
            if q[6][3]: P.liq, P.prevG, P.nextG = q[6][0], q[6][1], q[6][2]
        else:
            P.liq = r[6]
        P.price, P.tick = r[5], r[7]
    return out, other, parent, unknown, logs

def client_version():
    try: return post({'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []}).get('result')
    except Exception as e: return 'error ' + str(e)[:80]

groups = [tuple(x) for x in (json.load(open(A.groups)) if A.groups else SAMPLE['groups'])]
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
            out, other, parent, unknown, logs = res
            C = collections.Counter()
            for rec, r in out:
                SF.write(json.dumps(rec) + '\n')
                x = rec['res']; C['swaps'] += 1; C['factory:' + POOLS[rec['pool']][:10]] += 1
                if x.get('fail'):
                    C['mismatch'] += 1
                    MF.write(json.dumps({'rec': rec, 'row': [str(v) for v in r], 'parent': parent, 'liveLogs': logs, 'plant': A.plant}) + '\n')
                else:
                    C['ok'] += 1; C['mode:' + x['mode']] += 1; C['multiStep' if x['steps'] > 1 else 'oneStep'] += 1
                    if x['crossed']: C['crossedTick'] += 1
                    if x['m512']: C['m512'] += 1; C['m512calls'] += x['m512']
                    if x['fallback']: C['fallback'] += 1
                    if rec.get('needBranch'): C['needBranch'] += 1
                    if rec['feeSource'].get('swapFeeLog'): C['swapFeeLog'] += 1
                    if rec['feeSource'].get('pluginFee'): C['pluginFee>0'] += 1
                    if rec['feeSource'].get('overrideFee'): C['overrideFee>0'] += 1
            if unknown: C['groupsUnknownTopic'] += 1
            for k, v in C.items(): R[k] += v
            GF.write(json.dumps({'g': list(g), 'counts': C, 'other': dict(other), 'unknown': unknown, 'parent': parent}) + '\n'); GF.flush(); SF.flush(); MF.flush()
        if n % 1000 == 0: print(n, len(todo), round(time.time() - t0), dict(R), flush=True)
        if n % 5000 == 0: print('clientVersion', client_version(), time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), flush=True)
print('clientVersion end', URL, client_version(), time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), flush=True)
print('done', dict(R), 'seconds', round(time.time() - t0), flush=True)
