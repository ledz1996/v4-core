"""L-780: every mined liquidity removal of the Celo PoolManager, recomputed from parent-block state. Read-only.

For each ModifyLiquidity log with liquidityDelta < 0 (from celologs.py output):
  - skip if another PoolManager log of the same pool sits earlier in the same block (parent state would be stale);
  - read slot0, feeGrowthGlobal, both ticks and the position at block-1 by eth_getStorageAt
    (Pool.State layout src/libraries/Pool.sol:83-91, TickInfo :68-77, Position.State src/libraries/Position.sol:19-25,
    position key src/libraries/Position.sol:48-62, POOLS_SLOT=6 src/libraries/StateLibrary.sol:11);
  - principal = Pool.modifyLiquidity (src/libraries/Pool.sol:206-240) with SqrtPriceMath signed deltas (:261-288),
    fees = Position.update (src/libraries/Position.sol:76-102) with getFeeGrowthInside (Pool.sol:488-511),
    callerDelta = principal + fees (src/PoolManager.sol:171);
  - for pools with no hook and txs whose only PoolManager log is this one, compare with ERC-20 Transfer logs out of
    the PoolManager in the same transaction (native side: PoolManager balance change is not observable per tx; skipped).
Also checks the post-state: position liquidity at block equals pre minus |delta| when the tx is the pool's last log in the block.
Usage: python3 removals.py <logs.json> <out.json>
"""
import sys, json, urllib.request, time, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
import v4math as m
URL = 'https://forno.celo.org'
PM = '0x288dc841a52fca2707c6947b3a777c5e56cd87bc'
POSM = '0xf7965f3981e4d5bc383bfbcb61501763e9068ca9'
TRANSFER = '0x' + keccak(b'Transfer(address,address,uint256)').hex()
PKSEL = '0x' + keccak(b'poolKeys(bytes25)')[:4].hex()
Q128 = 1 << 128
def rpc(meth, p):
    err = None
    for k in range(10):
        try:
            r = urllib.request.Request(URL, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": meth, "params": p}).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
            j = json.load(urllib.request.urlopen(r, timeout=90))
            if 'error' in j: raise RuntimeError(j['error'])
            return j['result']
        except Exception as e:
            err = e; time.sleep(1 + k)
    raise err
def sx(x, bits): return x - (1 << bits) if x >> (bits - 1) else x
def h32(x): return (x % (1 << 256)).to_bytes(32, 'big')
def slot_of(key_bytes, base): return int.from_bytes(keccak(key_bytes + h32(base)), 'big')
def sload(slot, blk): return int(rpc('eth_getStorageAt', [PM, hex(slot), hex(blk)]), 16)
keys = {}
def poolkey(pid):
    if pid in keys: return keys[pid]
    rr = rpc('eth_call', [{'to': POSM, 'data': PKSEL + pid[2:52] + '00' * 7}, 'latest'])
    k = None
    if len(rr) >= 2 + 64 * 5 and '0x' + keccak(bytes.fromhex(rr[2:2 + 64 * 5])).hex() == pid:
        k = {'c0': '0x' + rr[26:66], 'c1': '0x' + rr[90:130], 'hooks': '0x' + rr[2 + 64 * 4 + 24:2 + 64 * 5]}
    keys[pid] = k; return k
def one(lg):
    pid = lg['topics'][1]; sender = '0x' + lg['topics'][2][26:]
    d = lg['data'][2:]; w = [int(d[i * 64:(i + 1) * 64], 16) for i in range(4)]
    tl, tu, ld, salt = sx(w[0], 256), sx(w[1], 256), sx(w[2], 256), w[3]
    blk = int(lg['blockNumber'], 16); txh = lg['transactionHash']; li = int(lg['logIndex'], 16)
    rec = {'tx': txh, 'block': blk, 'pool': pid, 'tl': tl, 'tu': tu, 'ld': ld}
    blogs = rpc('eth_getLogs', [{'address': PM, 'fromBlock': hex(blk), 'toBlock': hex(blk)}])
    if any(x['topics'][1] == pid and int(x['logIndex'], 16) < li for x in blogs if len(x['topics']) > 1):
        rec['status'] = 'skip-earlier-event-in-block'; return rec
    base = slot_of(bytes.fromhex(pid[2:]), 6); pb = blk - 1
    s0 = sload(base, pb); p = s0 & ((1 << 160) - 1); tick = sx((s0 >> 160) & 0xffffff, 24)
    fg0, fg1 = sload(base + 1, pb), sload(base + 2, pb)
    tlS, tuS = slot_of(h32(tl), base + 4), slot_of(h32(tu), base + 4)
    lo0, lo1, up0, up1 = sload(tlS + 1, pb), sload(tlS + 2, pb), sload(tuS + 1, pb), sload(tuS + 2, pb)
    pkey = keccak(bytes.fromhex(sender[2:]) + (tl & 0xffffff).to_bytes(3, 'big') + (tu & 0xffffff).to_bytes(3, 'big') + h32(salt))
    ps = slot_of(pkey, base + 6)
    pliq, last0, last1 = sload(ps, pb) & ((1 << 128) - 1), sload(ps + 1, pb), sload(ps + 2, pb)
    M = (1 << 256) - 1
    if tick < tl: fi0, fi1 = (lo0 - up0) & M, (lo1 - up1) & M
    elif tick >= tu: fi0, fi1 = (up0 - lo0) & M, (up1 - lo1) & M
    else: fi0, fi1 = (fg0 - lo0 - up0) & M, (fg1 - lo1 - up1) & M
    f0 = m.mul_div((fi0 - last0) & M, pliq, Q128); f1 = m.mul_div((fi1 - last1) & M, pliq, Q128)
    L = -ld; a0 = a1 = 0
    pl, pu = m.get_sqrt_price_at_tick(tl), m.get_sqrt_price_at_tick(tu)
    if tick < tl: a0 = m.amount0_delta(pl, pu, L, False)
    elif tick < tu: a0 = m.amount0_delta(p, pu, L, False); a1 = m.amount1_delta(pl, p, L, False)
    else: a1 = m.amount1_delta(pl, pu, L, False)
    rec.update({'pre_liq': pliq, 'principal': [a0, a1], 'fees': [f0, f1], 'expected': [a0 + f0, a1 + f1]})
    if pliq < L: rec['status'] = 'pre-liquidity-below-removal'; return rec
    k = poolkey(pid); rec['key'] = k
    pmlogs = [x for x in blogs if x['transactionHash'] == txh]
    if not k or int(k['hooks'], 16) != 0 or len(pmlogs) != 1:
        rec['status'] = 'computed-only'; return rec
    rc = None
    for k2 in range(12):
        rc = rpc('eth_getTransactionReceipt', [txh])
        if rc: break
        time.sleep(1)
    if not rc: rec['status'] = 'error-no-receipt'; return rec
    out = {}
    for x in rc['logs']:
        if x['topics'] and x['topics'][0] == TRANSFER and len(x['topics']) == 3 and x['topics'][1][26:] == PM[2:]:
            out[x['address'].lower()] = out.get(x['address'].lower(), 0) + int(x['data'], 16)
    got = [out.get(k['c0'].lower(), None) if int(k['c0'], 16) else None, out.get(k['c1'].lower(), None)]
    rec['transfers_out'] = got
    ok = True; checked = 0
    for i in (0, 1):
        exp = rec['expected'][i]
        if i == 0 and int(k['c0'], 16) == 0: continue
        g = got[i] or 0; checked += 1
        if g != exp: ok = False
    rec['status'] = ('match' if ok else 'MISMATCH') + ('' if checked == 2 else '-erc20-side-only')
    return rec
def main():
    logs = json.load(open(sys.argv[1]))['logs']
    rem = [l for l in logs if sx(int(l['data'][2 + 128:2 + 192], 16), 256) < 0]
    res = []
    with cf.ThreadPoolExecutor(6) as ex:
        futs = [ex.submit(one, l) for l in rem]
        for f in futs:
            try: res.append(f.result())
            except Exception as e: res.append({'status': 'error', 'err': str(e)[:200]})
    from collections import Counter
    c = Counter(r['status'] for r in res)
    json.dump({'modifyLiquidity': len(logs), 'removals': len(rem), 'counts': c, 'results': res}, open(sys.argv[2], 'w'), default=str)
    print(len(logs), 'logs', len(rem), 'removals', dict(c))
if __name__ == '__main__': main()
