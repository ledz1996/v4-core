"""Mined Uniswap v3 style swaps (event Swap(address,address,int256,int256,uint160,uint128,int24)) on one network:
pair each swap with the previous swap of the same pool in the window, test the single-step relations of
computeSwapStep (tools/opdiff/swaps.py check_amounts, v4math transcription of src/libraries), and count
which matching swaps ran FullMath.mulDiv with a nonzero high word (512 bit branch, MULMOD by 2^256-1 with
a nonzero high half and MULMOD by the denominator). Read-only RPC.
Usage: v3ops.py <chainId> <lo> <hi> <span> <out.json> [--plant]"""
import sys, json, collections, itertools, time, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc as _rpc, keccak, MASK
import v4math as m
from swaps import check_tick
cid, lo, hi, span, out = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
PLANT = '--plant' in sys.argv; PLANTHI = '--plant-hi' in sys.argv
URL = {143: 'https://rpc3.monad.xyz', 4326: 'https://mainnet.megaeth.com/rpc', 999: 'https://rpc.hyperliquid.xyz/evm'}[cid]
T = '0x' + keccak(b'Swap(address,address,int256,int256,uint160,uint128,int24)').hex()
def rpc(meth, p):
    for k in range(10):
        try: return _rpc(URL, meth, p, timeout=60)
        except Exception as e:
            if 'revert' in str(e).lower(): raise
            time.sleep(1 + k)
    raise RuntimeError('rpc')
def get(a):
    return rpc('eth_getLogs', [{'topics': [T], 'fromBlock': hex(a), 'toBlock': hex(min(hi, a + span - 1))}])
logs = []
with cf.ThreadPoolExecutor(3) as ex:
    for r in ex.map(get, range(lo, hi + 1, span)): logs += r
logs.sort(key=lambda l: (int(l['blockNumber'], 16), int(l['logIndex'], 16)))
def s256(x): return x - (1 << 256) if x >> 255 else x
fees = {}
def fee(p):
    if p not in fees:
        try: fees[p] = int(rpc('eth_call', [{'to': p, 'data': '0xddca3f43'}, 'latest']), 16)
        except Exception: fees[p] = None
    return fees[p]
# instrumentation of the 512 bit branch
hits = [0]
orig_mul_div = m.mul_div
def mul_div(a, b, d):
    if (a * b) >> 256: hits[0] += 1
    return orig_mul_div(a, b, d)
m.mul_div = mul_div
om = m.mulmod
if PLANTHI:  # planted fault: MULMOD by 2^256-1 returns one more when the high half is nonzero
    m.mulmod = lambda a, b, c: ((om(a, b, c) + 1) % c if c == MASK and (a * b) >> 256 else om(a, b, c))
elif PLANT:  # planted fault: MULMOD by any other modulus returns one more when the product needs more than 256 bits
    m.mulmod = lambda a, b, c: ((om(a, b, c) + 1) % c if c != MASK and (a * b) >> 256 else om(a, b, c))
def check(p0, p1, liq, a0, a1, fee):
    # same relations as tools/opdiff/swaps.py check_amounts; returns (relation, 512-bit mulDiv calls inside the relation that held)
    zf = p1 < p0
    paid, got = (-a0, a1) if zf else (-a1, a0)
    if paid < 0 or got < 0: return None, 0
    try:
        hits[0] = 0
        out = m.amount1_delta(p1, p0, liq, False) if zf else m.amount0_delta(p0, p1, liq, False)
        less = m.mul_div(paid, m.MAX_SWAP_FEE - fee, m.MAX_SWAP_FEE)
        if m.next_price_from_input(p0, liq, less, zf) == p1 and out == got: return 'exactIn', hits[0]
        h_out = hits[0]
        hits[0] = 0
        amt_in = m.amount0_delta(p1, p0, liq, True) if zf else m.amount1_delta(p0, p1, liq, True)
        total = amt_in + m.mul_div_rounding_up(amt_in, fee, m.MAX_SWAP_FEE - fee)
        h_in = hits[0]
        if total == paid and got <= out:
            hits[0] = 0
            try:
                if m.next_price_from_output(p0, liq, got, zf) == p1: return 'exactOut', h_in + hits[0]
            except m.Revert: pass
        if total == paid and out == got: return 'target', h_in
        if 0 <= out - got <= 64 and 0 <= paid - total <= 64: return 'multi', 0
    except m.Revert:
        return None, 0
    return None, 0
last = {}; st = collections.Counter(); ex512 = []; tb = []
for l in logs:
    d = l['data']; w = lambda i: int(d[2 + 64 * i:2 + 64 * (i + 1)], 16)
    a0, a1, p1, L, tick = s256(w(0)), s256(w(1)), w(2), w(3), s256(w(4))
    if not (m.MIN_SQRT_PRICE <= p1 < m.MAX_SQRT_PRICE): st['priceOutOfRange'] += 1; continue
    st['swaps'] += 1
    if check_tick(p1, tick): st['tickOK'] += 1
    else:
        st['tickBad'] += 1
        if len(tb) < 200: tb.append({'tx': l['transactionHash'], 'pool': l['address'].lower(), 'price': p1, 'tick': tick, 'tickOfPrice': m.get_tick_at_sqrt_price(p1)})
    pool = l['address'].lower(); prev = last.get(pool); last[pool] = p1
    if prev is None or prev == p1 or L == 0: continue
    f = fee(pool)
    if f is None or f >= 10 ** 6: st['noFee'] += 1; continue
    st['paired'] += 1
    # v3 amounts are the pool's view (positive = paid in); swaps.py takes the v4 view
    r, h = check(prev, p1, L, -a0, -a1, f)
    if r in ('exactIn', 'exactOut', 'target'):
        st['single:' + r] += 1
        if h:
            st['single512'] += 1; st['single512:' + r] += 1
            if len(ex512) < 40: ex512.append({'tx': l['transactionHash'], 'block': int(l['blockNumber'], 16), 'pool': pool, 'kind': r, 'mulDiv512': h})
    elif r == 'multi': st['multi'] += 1
    else: st['unmatched'] += 1
json.dump({'chainId': cid, 'lo': lo, 'hi': hi, 'plant': 'hi' if PLANTHI else ('rem' if PLANT else None), 'counts': st, 'pools': len(last), 'examples512': ex512, 'tickBad': tb}, open(out, 'w'), indent=1)
print(cid, dict(st), 'pools', len(last))
