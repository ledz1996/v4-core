"""Cycle 39, lead L-1332: for every MegaETH PoolManager position with liquidity, does a full removal need a zero to
nonzero write inside the PoolManager? Position.update (src/libraries/Position.sol:77-108) writes
feeGrowthInside{0,1}LastX128 on every call, so a position whose stored last value is zero and whose current inside
growth is nonzero needs a new nonzero slot. Read-only: eth_getLogs, eth_getStorageAt, eth_call of extsload.
usage: python3 -I l1332_positions.py <out.json>"""
import sys, json, urllib.request, time
OUT = sys.argv[1]
R = 'https://mainnet.megaeth.com/rpc'; PM = '0xacb7e78fa05d562e0a5d3089ec896d57d057d38e'
def rpc(m, p):
    for k in range(6):
        try:
            q = urllib.request.Request(R, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'curl/8.5.0'})
            r = json.load(urllib.request.urlopen(q, timeout=60))
            if 'error' in r: raise RuntimeError(str(r['error'])[:200])
            return r['result']
        except Exception as e:
            err = e; time.sleep(1 + k)
    raise err
from hashlib import sha3_256
try:
    import sha3  # noqa
except Exception:
    pass
def keccak(b):
    # pure python keccak from the opdiff tools
    sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
    import pyevm
    return pyevm.keccak(b)
T0 = '0x' + keccak(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)').hex()
head = int(rpc('eth_blockNumber', []), 16)
logs = []; a = 7009653; step = 2000000
while a <= head:
    b = min(head, a + step - 1)
    try:
        logs += rpc('eth_getLogs', [{'address': PM, 'topics': [T0], 'fromBlock': hex(a), 'toBlock': hex(b)}]); a = b + 1
    except Exception as e:
        step //= 2
        if step < 1000: raise
def s(x, bits=256):
    x = int(x, 16); return x - (1 << bits) if x >> (bits - 1) else x
pos = {}
for l in logs:
    d = l['data'][2:]; pid = l['topics'][1]; owner = '0x' + l['topics'][2][-40:]
    k = (pid, owner, s(d[0:64]), s(d[64:128]), d[192:256])
    pos[k] = pos.get(k, 0) + s(d[128:192])
live = [(k, v) for k, v in pos.items() if v > 0]
def i24(x): return (x & 0xffffff).to_bytes(3, 'big')
def u(x): return int(x, 16)
def at(slot): return u(rpc('eth_getStorageAt', [PM, hex(slot), 'latest']))
rows = []
for (pid, owner, tl, tu, salt), L in live:
    st = int.from_bytes(keccak(bytes.fromhex(pid[2:]) + (6).to_bytes(32, 'big')), 'big')
    pkey = keccak(bytes.fromhex(owner[2:]) + i24(tl) + i24(tu) + bytes.fromhex(salt))
    pslot = int.from_bytes(keccak(pkey + (st + 6).to_bytes(32, 'big')), 'big')
    liq = at(pslot); f0 = at(pslot + 1); f1 = at(pslot + 2)
    s0 = at(st); tick = s(hex((s0 >> 160) & 0xffffff), 24)
    g0 = at(st + 1); g1 = at(st + 2)
    def tk(t):
        ts = int.from_bytes(keccak((t % (1 << 256)).to_bytes(32, 'big') + (st + 4).to_bytes(32, 'big')), 'big')
        return at(ts + 1), at(ts + 2)
    lo0, lo1 = tk(tl); hi0, hi1 = tk(tu)
    M = (1 << 256) - 1
    # Pool.getFeeGrowthInside (src/libraries/Pool.sol): below/above by the current tick
    def inside(g, lo, hi):
        if tick < tl: return (lo - hi) & M
        if tick >= tu: return (hi - lo) & M
        return (g - lo - hi) & M
    i0 = inside(g0, lo0, hi0); i1 = inside(g1, lo1, hi1)
    rows.append({'pool': pid, 'owner': owner, 'tl': tl, 'tu': tu, 'liqLogs': L, 'liqSlot': liq,
                 'last0zero': f0 == 0, 'last1zero': f1 == 0, 'inside0nonzero': i0 != 0, 'inside1nonzero': i1 != 0,
                 'needsNewFeeSlot': (f0 == 0 and i0 != 0) or (f1 == 0 and i1 != 0)})
summ = {'head': head, 'logs': len(logs), 'positions': len(pos), 'live': len(live),
        'liveWithSlotLiquidity': sum(1 for r in rows if r['liqSlot'] > 0),
        'needsNewFeeSlot': sum(1 for r in rows if r['needsNewFeeSlot'] and r['liqSlot'] > 0)}
json.dump({'summary': summ, 'rows': rows}, open(OUT, 'w'), indent=1)
print(summ)
