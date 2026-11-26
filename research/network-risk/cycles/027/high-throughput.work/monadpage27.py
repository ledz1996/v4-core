"""L-1074, read only. Whole 128-slot pages of the real Monad PoolManager storage read two ways at one block:
extsload(bytes32,uint256) inside the EVM (eth_call, no override) and eth_getStorageAt slot by slot (JSON-RPC batch).
Pages: page 0 and the pages holding the 7 state words of pools seen in Swap logs of the last few hundred blocks.
Usage: python3 -I monadpage27.py <out.json> <rpc url>"""
import sys, json, time, ssl, urllib.request
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
URL = sys.argv[2]; PM = '0x188d586ddcf52439676ca21a244753fa19f9ea8e'
ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
def post(body):
    for k in range(8):
        try:
            req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
            with urllib.request.urlopen(req, timeout=60, context=ctx) as r: return json.load(r)
        except Exception as e:
            last = e; time.sleep(3 * (k + 1))
    raise last
def rpc(m, p):
    j = post({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p})
    if 'error' in j: raise RuntimeError(j['error'])
    return j['result']
SWAP = '0x' + keccak(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()
SEL = keccak(b'extsload(bytes32,uint256)')[:4]
def h(a, b): return int.from_bytes(keccak(a.to_bytes(32, 'big') + b.to_bytes(32, 'big')), 'big')
rec = {'rpc': URL, 'clientBefore': rpc('web3_clientVersion', [])}
blk = rpc('eth_blockNumber', []); b = int(blk, 16); rec['block'] = b
ids = []
for k in range(6):
    try:
        logs = rpc('eth_getLogs', [{'address': PM, 'topics': [SWAP], 'fromBlock': hex(b - 99 - 100 * k), 'toBlock': hex(b - 100 * k)}])
    except Exception as e:
        rec.setdefault('logErrors', []).append(str(e)[:200]); logs = []
    for lg in logs:
        if lg['topics'][1] not in ids: ids.append(lg['topics'][1])
    time.sleep(0.5)
    if len(ids) >= 4: break
pages = {0}
for pid in ids[:4]:
    s = h(int(pid, 16), 6); pages |= {s >> 7, (s + 6) >> 7}
rec['poolIds'] = ids[:4]; rec['pages'] = []
for p in sorted(pages):
    start = p << 7
    out = bytes.fromhex(rpc('eth_call', [{'to': PM, 'data': '0x' + (SEL + start.to_bytes(32, 'big') + (128).to_bytes(32, 'big')).hex()}, blk])[2:])
    w = [int.from_bytes(out[64 + 32 * i:96 + 32 * i], 'big') for i in range(128)]
    g = [None] * 128
    for c in range(0, 128, 16):
        body = [{'jsonrpc': '2.0', 'id': i, 'method': 'eth_getStorageAt', 'params': [PM, hex(start + i), blk]} for i in range(c, c + 16)]
        r = post(body)
        if isinstance(r, list):
            for x in r:
                if 'result' in x: g[x['id']] = int(x['result'], 16)
        time.sleep(1.0)
    for i in range(128):
        if g[i] is None:
            try: g[i] = int(rpc('eth_getStorageAt', [PM, hex(start + i), blk]), 16)
            except Exception: pass
            time.sleep(0.4)
    rec['pages'].append({'page': hex(p), 'read': sum(1 for x in g if x is not None),
                         'nonzero': [hex(start + i) for i in range(128) if w[i]],
                         'mismatches': [{'slot': hex(start + i), 'extsload': hex(w[i]), 'getStorageAt': None if g[i] is None else hex(g[i])} for i in range(128) if g[i] is not None and g[i] != w[i]]})
    print(hex(p)[:12], 'read', rec['pages'][-1]['read'], 'nonzero', len(rec['pages'][-1]['nonzero']), 'mismatch', len(rec['pages'][-1]['mismatches']), flush=True)
rec['clientAfter'] = rpc('web3_clientVersion', [])
rec['time'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
json.dump(rec, open(sys.argv[1], 'w'), indent=1)
print(json.dumps({k: rec[k] for k in ('clientBefore', 'block', 'poolIds', 'clientAfter')}))
