"""Collect v3 style Swap, Mint and Burn logs (all emitters) on HyperEVM from the archive client, compact rows. Read only.
Usage: collect999.py <lo> <hi> <span> <threads> <out.jsonl>"""
import sys, json, os, time, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from rpcu import rpc
from evm import keccak
U = ['https://rpc.purroofgroup.com']
SW = '0x' + keccak(b'Swap(address,address,int256,int256,uint160,uint128,int24)').hex()
MI = '0x' + keccak(b'Mint(address,address,int24,int24,uint128,uint256,uint256)').hex()
BU = '0x' + keccak(b'Burn(address,int24,int24,uint128,uint256,uint256)').hex()
K = {SW: 'S', MI: 'M', BU: 'B'}
lo, hi, span, th, out = map(int, sys.argv[1:5]) + [sys.argv[5]] if False else (int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5])
done = set()
if os.path.exists(out):
    for line in open(out):
        try: done.add(json.loads(line)['a'])
        except Exception: pass
def s(x): return x - (1 << 256) if x >> 255 else x
def one(a):
    b = min(hi, a + span - 1)
    for k in range(10):
        try:
            r = rpc(U[0], 'eth_getLogs', [{'topics': [[SW, MI, BU]], 'fromBlock': hex(a), 'toBlock': hex(b)}], timeout=180, tries=2)
            rows = []
            for l in r:
                t = K[l['topics'][0]]; d = l['data'][2:]; w = [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]
                row = [t, int(l['blockNumber'], 16), int(l['logIndex'], 16), l['transactionHash'], l['address'].lower()]
                if t == 'S':
                    if len(w) != 5: continue
                    row += [s(w[0]), s(w[1]), w[2], w[3], s(w[4])]
                elif t == 'M':
                    if len(w) != 4 or len(l['topics']) != 4: continue
                    row += [s(int(l['topics'][2], 16)), s(int(l['topics'][3], 16)), w[1]]
                else:
                    if len(w) != 3 or len(l['topics']) != 4: continue
                    row += [s(int(l['topics'][2], 16)), s(int(l['topics'][3], 16)), -w[0]]
                rows.append(row)
            return {'a': a, 'b': b, 'rows': rows}
        except Exception as e:
            time.sleep(2 + k)
    return {'a': a, 'b': b, 'error': True}
ranges = [a for a in range(lo, hi + 1, span) if a not in done]
f = open(out, 'a'); n = 0; t0 = time.time()
with cf.ThreadPoolExecutor(th) as ex:
    for r in ex.map(one, ranges):
        if r.get('error'): print('ERR', r['a'], flush=True); continue
        f.write(json.dumps(r, separators=(',', ':')) + '\n'); f.flush(); n += 1
        if n % 20 == 0: print(n, len(ranges), round(time.time() - t0), flush=True)
print('finished', n, len(ranges), flush=True)
