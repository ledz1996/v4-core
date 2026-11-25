"""PoolCreated logs of the v3 style factories on HyperEVM (archive client), and swap counts per pool and factory in the window. Read only."""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from rpcu import rpc
from evm import keccak
U = 'https://rpc.purroofgroup.com'
PC = '0x' + keccak(b'PoolCreated(address,address,uint24,int24,address)').hex()
cnt = collections.Counter()
for line in open('raw/logs999.jsonl'):
    for r in json.loads(line)['rows']:
        if r[0] == 'S': cnt[r[4]] += 1
print('swaps', sum(cnt.values()), 'emitters', len(cnt))
fac = {}; fcount = collections.Counter()
top = [a for a, n in cnt.most_common(400)]
for a in top:
    try: f = '0x' + rpc(U, 'eth_call', [{'to': a, 'data': '0xc45a0155'}, 'latest'])[-40:]
    except Exception: f = None
    fac[a] = f; fcount[f] += cnt[a]
print(fcount.most_common(20))
pools = {}
for f, n in fcount.most_common(12):
    if f is None: continue
    def get(a, b):
        try: return rpc(U, 'eth_getLogs', [{'address': f, 'topics': [PC], 'fromBlock': hex(a), 'toBlock': hex(b)}], timeout=180, tries=2)
        except Exception as e:
            if b - a < 1000: raise
            m = (a + b) // 2; return get(a, m) + get(m + 1, b)
    L = get(0, 52165551)
    for l in L:
        d = l['data'][2:]
        ts = int(d[0:64], 16); ts = ts - (1 << 256) if ts >> 255 else ts
        p = '0x' + d[64 + 24:128]
        pools[p] = {'factory': f, 'fee': int(l['topics'][3], 16), 'tickSpacing': ts, 'token0': '0x' + l['topics'][1][26:], 'token1': '0x' + l['topics'][2][26:], 'block': int(l['blockNumber'], 16)}
    print(f, n, 'PoolCreated', len(L))
cover = sum(cnt[p] for p in pools)
json.dump({'pools': pools, 'swapCount': {p: cnt[p] for p in pools}, 'factorySwaps': {str(k): v for k, v in fcount.items()}, 'totalSwaps': sum(cnt.values()), 'covered': cover}, open('raw/pools999.json', 'w'), indent=0)
print('pools', len(pools), 'covered swaps', cover)
