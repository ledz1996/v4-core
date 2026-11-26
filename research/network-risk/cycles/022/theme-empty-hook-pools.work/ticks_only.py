"""Initialized ticks of every census pool, from the tick bitmap words read with extsload. Read only. usage: ticks_only.py <cid> <url>"""
import sys, json, subprocess
from ep import rpc, NETS
cid, U = int(sys.argv[1]), sys.argv[2]; PM = NETS[cid]['poolManager']; C = json.load(open('raw/census_%d.json' % cid))
M = 1 << 256
def kec(b, n): return subprocess.run(['build/kec', str(n)], input=b, capture_output=True).stdout
def i256(x): return (x % M).to_bytes(32, 'big')
blk = hex(int(rpc(U, 'eth_blockNumber', []), 16) - 30)
def extsload(slots):
    out = []
    for i in range(0, len(slots), 1000):
        part = slots[i:i + 1000]
        r = bytes.fromhex(rpc(U, 'eth_call', [{'to': PM, 'data': '0xdbd035ff' + (32).to_bytes(32, 'big').hex() + len(part).to_bytes(32, 'big').hex() + b''.join(part).hex()}, blk])[2:])
        out += [int.from_bytes(r[64 + 32 * k:96 + 32 * k], 'big') for k in range(len(part))]
    return out
res = []
for p in C['hookPools']:
    pid = bytes.fromhex(p['poolId'][2:]); st = int.from_bytes(kec(pid + (6).to_bytes(32, 'big'), 64), 'big'); ts = p['tickSpacing']
    words = list(range(((-887272 // ts) >> 8) - 1, ((887272 // ts) >> 8) + 2)); base = (st + 5).to_bytes(32, 'big')
    hs = kec(b''.join(i256(w) + base for w in words), 64)
    bm = extsload([hs[32 * i:32 * i + 32] for i in range(len(words))])
    t = [((w << 8) + b) * ts for w, v in zip(words, bm) for b in range(256) if v >> b & 1]
    s0, liq = extsload([st.to_bytes(32, 'big'), (st + 3).to_bytes(32, 'big')])
    res.append({'poolId': p['poolId'], 'hook': p['hook'], 'flagBits': int(p['hook'], 16) & 0x3fff, 'kind': p['kind'], 'initBlock': p['block'], 'ticks': t, 'liquidity': liq, 'sqrtPriceX96': s0 & ((1 << 160) - 1), 'currency0': p['currency0'], 'currency1': p['currency1']})
json.dump({'chainId': cid, 'url': U, 'block': int(blk, 16), 'client': rpc(U, 'web3_clientVersion', []), 'pools': res}, open('raw/ticks_%d.json' % cid, 'w'), indent=1)
k = [r for r in res if r['ticks']]
print(cid, 'pools', len(res), 'with ticks', len(k), 'min init', min([r['initBlock'] for r in k] or [0]))
for r in k: print('  ', r['poolId'][:12], r['hook'], hex(r['flagBits']), r['kind'], 'ticks', len(r['ticks']), 'L', r['liquidity'], 'init', r['initBlock'])
