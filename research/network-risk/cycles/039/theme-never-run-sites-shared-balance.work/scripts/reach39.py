"""Cycle 39, theme-never-run-sites-shared-balance, Task 3. Read-only: eth_call with a state override of a driver contract only.
The DEPLOYED PoolManager of the network is called by the driver (tools/opdiff/pmdiff.py driver), which runs unlock and in the callback
a list of PoolManager calls, records each result and reverts, so nothing is settled or persisted.
Cases per network:
  own-B-*   : a hookless pool the driver creates from native currency0 and a currency1 that existing pools of the PoolManager hold,
              tick spacing 32767, price below tick 851,942, one position [851942, 884709] with L >= 2^96.5, then a small exact-input
              oneForZero swap. The second step enters getAmount1Delta (SqrtPriceMath.sol:250-252) with L*dP >= 2^256.
              Also run in pyevm.py on the same deployed bytecode with empty storage (the case touches only the new pool's slots).
  donate-*  : donate(1,1) in an existing hookless pool; feeGrowthGlobal before and after vs floor(a*2^128/L) (Pool.sol:473-478).
  exout-*   : exact-output swap of 1000 units in an existing hookless pool, both directions (SwapMath.sol:88-104).
  wide-*    : (MegaETH only, L-1353) exact input -2^236, -2^240, -2^250, -(2^255-1) in both directions, limit 2-3 ticks away.
Usage: python3 reach39.py <chainId> <out.json>. No sampling, no seed."""
import sys, json, hashlib, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import pmdiff as P, v4math as m
from evm import rpc, keccak
from pyevm import World

CID = int(sys.argv[1]); OUT = sys.argv[2]
NET = {4326: ('0xacb7e78fa05d562e0a5d3089ec896d57d057d38e', [('official', 'https://mainnet.megaeth.com/rpc'), ('globalstake', 'https://rpc-megaeth-mainnet.globalstake.io')],
              '/home/user/v4-core/research/network-risk/cycles/034/theme-first-inputs-and-stale-sync.work/out/pools-mega.json'),
       999: ('0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F', [('official', 'https://rpc.hyperliquid.xyz/evm'), ('purroof', 'https://rpc.purroofgroup.com'), ('hyperlend', 'https://rpc.hyperlend.finance/archive')],
             '/home/user/v4-core/research/network-risk/cycles/034/theme-first-inputs-and-stale-sync.work/out/pools-hl.json'),
       143: ('0x188d586ddcf52439676ca21a244753fa19f9ea8e', [('official', 'https://rpc.monad.xyz'), ('monad2', 'https://rpc2.monad.xyz'), ('monadinfra', 'https://rpc-mainnet.monadinfra.com')],
             '/home/user/v4-core/research/network-risk/cycles/034/theme-first-inputs-and-stale-sync.work/out/pools-monad.json')}
PMADDR, EPS, POOLFILE = NET[CID]
P.PM = PMADDR
DRV = P.DRV; drv = P.driver()
MASK = (1 << 256) - 1
def w(x): return P.w(x)
def item(cd): return len(cd).to_bytes(2, 'big') + cd
def keyw(c0, c1, fee, ts): return w(c0) + w(c1) + w(fee) + w(ts) + w(0)
def pid(c0, c1, fee, ts): return keccak(keyw(c0, c1, fee, ts))
def pslot(i, k): return (int.from_bytes(keccak(i + w(6)), 'big') + k) & MASK
def dslot(cur): return int.from_bytes(keccak(w(int(DRV, 16)) + w(cur)), 'big')
def ext(slot): return P.S_EXTSLOAD + w(slot)
def init(k, price): return P.S_INIT + k + w(price)
def mod(k, lo, hi, d): return P.S_MOD + k + w(lo) + w(hi) + w(d) + w(0) + w(0x140) + w(0)
def swap(k, zfo, amt, lim): return P.S_SWAP + k + w(int(zfo)) + w(amt) + w(lim) + w(0x120) + w(0)
def donate(k, a0, a1): return P.S_DONATE + k + w(a0) + w(a1) + w(0x100) + w(0)
def R(url, mth, params):
    last = None
    for k in range(4):
        try: return rpc(url, mth, params, timeout=90)
        except Exception as e: last = e; time.sleep(2 * (k + 1))
    raise last

off = EPS[0][1]
raw = json.load(open(POOLFILE))['pools']
pools = []
for i, p in raw.items():
    if int(p['hooks'], 16) != 0: continue
    pools.append(dict(p, id=i))
# live reads only for the 25 hookless pools with the largest liquidity recorded in cycle 34 (rate limits); native-currency0 pools kept too
pools.sort(key=lambda p: -(p.get('liquidity') or 0))
pools = pools[:25] + [p for p in pools[25:] if int(p['currency0'], 16) == 0][:10]
# live state of every hookless pool on the official endpoint, then the three with the largest in-range liquidity
live = []
for p in pools:
    b = bytes.fromhex(p['id'][2:])
    s0 = int(R(off, 'eth_call', [{'to': PMADDR, 'data': '0x' + ext(pslot(b, 0)).hex()}, 'latest']), 16)
    L = int(R(off, 'eth_call', [{'to': PMADDR, 'data': '0x' + ext(pslot(b, 3)).hex()}, 'latest']), 16)
    if s0 == 0 or L == 0: continue
    tick = (s0 >> 160) & 0xffffff
    if tick >= 1 << 23: tick -= 1 << 24
    live.append(dict(p, sqrt=s0 & ((1 << 160) - 1), tickLive=tick, L=L, lpFee=(s0 >> 208) & 0xffffff, protoFee=(s0 >> 184) & 0xffffff))
live.sort(key=lambda x: -x['L'])
top = [p for p in live if p['protoFee'] == 0][:3]
# currency1 for the own pool: the currency1 of the largest native/ERC20 pool (an asset that other pools hold)
nat = [p for p in live if int(p['currency0'], 16) == 0]
own_c1 = int((nat[0] if nat else live[0])['currency1'], 16)
own_c0 = 0 if nat else int(live[0]['currency0'], 16)

CASES = []
sp = m.get_sqrt_price_at_tick
LO, HI = 26 * 32767, 27 * 32767
for name, L, amt in (('own-B-L2^96.5', -(-(1 << 256) // (sp(HI) - sp(LO))), -1000), ('own-B-L2^100', 1 << 100, -10 ** 6)):
    k = keyw(own_c0, own_c1, 3000, 32767); i = pid(own_c0, own_c1, 3000, 32767)
    calls = [init(k, sp(LO - 1)), mod(k, LO, HI, L), ext(pslot(i, 0)), ext(pslot(i, 3)), swap(k, False, amt, m.MAX_SQRT_PRICE - 1),
             ext(pslot(i, 0)), ext(pslot(i, 2)), ext(pslot(i, 3)), P.S_EXTTLOAD + w(dslot(own_c0)), P.S_EXTTLOAD + w(dslot(own_c1))]
    CASES.append({'name': name, 'kind': 'own', 'L': L, 'amount': amt, 'c0': hex(own_c0), 'c1': hex(own_c1), 'data': b''.join(item(c) for c in calls) + b'\0\0'})
for p in top:
    c0, c1 = int(p['currency0'], 16), int(p['currency1'], 16); k = keyw(c0, c1, p['fee'], p['tickSpacing']); b = bytes.fromhex(p['id'][2:])
    calls = [ext(pslot(b, 1)), ext(pslot(b, 2)), ext(pslot(b, 3)), donate(k, 1, 1), ext(pslot(b, 1)), ext(pslot(b, 2))]
    CASES.append({'name': 'donate-' + p['id'][:18], 'kind': 'donate', 'pool': p['id'], 'data': b''.join(item(c) for c in calls) + b'\0\0'})
    for zfo in (True, False):
        lim = m.MIN_SQRT_PRICE + 1 if zfo else m.MAX_SQRT_PRICE - 1
        calls = [ext(pslot(b, 0)), ext(pslot(b, 3)), swap(k, zfo, 1000, lim), ext(pslot(b, 0)), ext(pslot(b, 3))]
        CASES.append({'name': 'exout-%s-%s' % (p['id'][:18], int(zfo)), 'kind': 'exout', 'pool': p['id'], 'zfo': zfo, 'data': b''.join(item(c) for c in calls) + b'\0\0'})
    if CID == 4326:
        for zfo in (True, False):
            for e in (236, 240, 250, 255):
                amt = -(1 << e) if e < 255 else -((1 << 255) - 1)
                lim = sp(p['tickLive'] - 2) if zfo else sp(p['tickLive'] + 3)
                calls = [ext(pslot(b, 0)), ext(pslot(b, 3)), swap(k, zfo, amt, lim), ext(pslot(b, 0)), ext(pslot(b, 3)),
                         P.S_EXTTLOAD + w(dslot(c0)), P.S_EXTTLOAD + w(dslot(c1))]
                CASES.append({'name': 'wide-%s-%s-%d' % (p['id'][:18], int(zfo), e), 'kind': 'wide', 'pool': p['id'], 'zfo': zfo, 'amount': amt, 'limit': lim,
                              'data': b''.join(item(c) for c in calls) + b'\0\0'})

def i128(b, hi): v = int.from_bytes(b[:16] if hi else b[16:32], 'big'); return v - (1 << 128) if v >> 127 else v
def sgn(x): return x - (1 << 256) if x >> 255 else x

# reference for own-pool cases: pyevm on the deployed bytecode, empty storage
code = bytes.fromhex(R(off, 'eth_getCode', [PMADDR, 'latest'])[2:])
out = {'chainId': CID, 'pm': PMADDR, 'codeSha256': hashlib.sha256(code).hexdigest()[:16], 'codeLen': len(code), 'ownCurrencies': [hex(own_c0), hex(own_c1)],
       'pools': [{k: p[k] for k in ('id', 'currency0', 'currency1', 'fee', 'tickSpacing', 'sqrt', 'tickLive', 'L', 'lpFee')} for p in top],
       'livePools': len(live), 'clientVersionBefore': {}, 'clientVersionAfter': {}, 'cases': []}
for name, url in EPS:
    try: out['clientVersionBefore'][name] = R(url, 'web3_clientVersion', [])
    except Exception as e: out['clientVersionBefore'][name] = 'ERR ' + str(e)[:200]
for c in CASES:
    rec = {k: v for k, v in c.items() if k != 'data'}; rec['calldataSha256'] = hashlib.sha256(c['data']).hexdigest()[:16]; rec['answers'] = {}
    for name, url in EPS:
        try:
            r = R(url, 'eth_call', [{'to': DRV, 'data': '0x' + c['data'].hex(), 'gas': hex(25_000_000)}, 'latest', {DRV: {'code': '0x' + drv.hex()}}])
            recs = P.parse(bytes.fromhex(r[2:]))
            rec['answers'][name] = {'sha': hashlib.sha256(bytes.fromhex(r[2:])).hexdigest()[:16], 'ok': [ok for ok, _ in recs], 'words': [d.hex() for _, d in recs]}
        except Exception as e:
            rec['answers'][name] = {'err': str(e)[:300]}
        time.sleep(0.2)
    a = rec['answers'][EPS[0][0]]
    shas = {k: v.get('sha', 'ERR') for k, v in rec['answers'].items() if 'sha' in v}
    rec['endpointsAgree'] = len(set(shas.values())) == 1 and len(shas) > 0
    rec['endpointsAnswered'] = sorted(shas)
    if c['kind'] == 'own':
        wd = World({int(PMADDR, 16): code, int(DRV, 16): drv}); wd.max_steps = 20_000_000
        ok, ret = wd.call(0, int(DRV, 16), 0, c['data'], False, 0)
        rec['pyevmSha'] = hashlib.sha256(ret).hexdigest()[:16]
        rec['pyevmEqual'] = {k: v == rec['pyevmSha'] for k, v in shas.items()}
        if 'words' in a and all(a['ok']):
            W_ = [int(x, 16) if x else 0 for x in a['words']]
            sw = bytes.fromhex(a['words'][4]); rec['swapDelta'] = [i128(sw, True), i128(sw, False)]
            rec['priceBeforeSwap'] = W_[2] & ((1 << 160) - 1); rec['liquidityBeforeSwap'] = W_[3]
            rec['priceAfter'] = W_[5] & ((1 << 160) - 1); rec['feeGrowth1After'] = W_[6]; rec['liquidityAfter'] = W_[7]
            rec['driverDeltas'] = [sgn(W_[8]), sgn(W_[9])]
            md = bytes.fromhex(a['words'][1]); rec['mintDelta'] = [i128(md, True), i128(md, False)]
            # reference: step 1 has no liquidity and reaches tick LO; step 2 is the wide getAmount1Delta step
            L = c['L']; Pa, Pb = sp(LO), sp(HI)
            rec['wideProductLog2'] = (L * (Pb - Pa)).bit_length() - 1
            np_, ain, aout, fee = m.compute_swap_step(Pa, Pb, L, c['amount'], 3000)
            rec['stepReference'] = {'amountIn': ain, 'amountOut': aout, 'fee': fee, 'next': np_, 'amountInToTarget': m.amount1_delta(Pa, Pb, L, True)}
            rec['equalToReference'] = rec['swapDelta'] == [aout, -(ain + fee)] and rec['priceAfter'] == np_ and rec['liquidityAfter'] == L
    elif c['kind'] == 'donate' and 'words' in a and all(a['ok']):
        W_ = [int(x, 16) for x in a['words']]; g0, g1, L, g0a, g1a = W_[0], W_[1], W_[2], W_[4], W_[5]
        rec['feeGrowthDelta'] = [(g0a - g0) & MASK, (g1a - g1) & MASK]; rec['reference'] = [(1 << 128) // L, (1 << 128) // L]
        rec['equalToReference'] = rec['feeGrowthDelta'] == rec['reference']
    elif c['kind'] in ('exout', 'wide') and 'words' in a and all(a['ok']):
        W_ = [int(x, 16) for x in a['words']]; sw = bytes.fromhex(a['words'][2])
        d0, d1 = i128(sw, True), i128(sw, False); pb, Lb, pa, La = W_[0] & ((1 << 160) - 1), W_[1], W_[3] & ((1 << 160) - 1), W_[4]
        lpfee = (W_[0] >> 208) & 0xffffff
        rec.update(swapDelta=[d0, d1], priceBefore=pb, priceAfter=pa, liquidityBefore=Lb, liquidityAfter=La, lpFee=lpfee)
        if c['kind'] == 'wide':
            rec['wideFeeProduct'] = ((-c['amount']) * (10 ** 6 - lpfee)) >> 256 != 0
            rec['driverDeltas'] = [sgn(W_[5]), sgn(W_[6])]
            tgt = c['limit']
            if La == Lb and pa == tgt:
                np_, ain, aout, fee = m.compute_swap_step(pb, tgt, Lb, c['amount'], lpfee)
                exp = [-(ain + fee), aout] if c['zfo'] else [aout, -(ain + fee)]
                rec['singleStepReference'] = exp; rec['equalToReference'] = exp == [d0, d1] and np_ == pa
        else:
            if La == Lb:
                # single step from pb towards the far limit; reference only when the step ended inside the range (price after not on a tick)
                tgt = pa
                np_, ain, aout, fee = m.compute_swap_step(pb, m.MIN_SQRT_PRICE + 1 if c['zfo'] else m.MAX_SQRT_PRICE - 1, Lb, 1000, lpfee)
                exp = [-(ain + fee), aout] if c['zfo'] else [aout, -(ain + fee)]
                rec['singleStepReference'] = exp; rec['equalToReference'] = exp == [d0, d1] and np_ == pa
    out['cases'].append(rec)
    print(c['name'], rec.get('endpointsAgree'), rec.get('equalToReference'), rec.get('pyevmEqual'), rec.get('swapDelta'), rec.get('feeGrowthDelta'), {k: v.get('err', '')[:80] for k, v in rec['answers'].items() if 'err' in v})
for name, url in EPS:
    try: out['clientVersionAfter'][name] = R(url, 'web3_clientVersion', [])
    except Exception as e: out['clientVersionAfter'][name] = 'ERR ' + str(e)[:200]
json.dump(out, open(OUT, 'w'), indent=1)
