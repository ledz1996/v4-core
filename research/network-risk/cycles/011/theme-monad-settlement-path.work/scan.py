"""Monad (143): PoolManager logs over the newest blocks, in the 100 block windows the public
endpoint allows. Read-only. Usage: python3 -I scan.py <out.json> <nBlocks> [threads]"""
import sys, os, json, time, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rpcq import rpc
PM = '0x188d586ddcf52439676ca21a244753fa19f9ea8e'
out = sys.argv[1]; nb = int(sys.argv[2]); th = int(sys.argv[3]) if len(sys.argv) > 3 else 4
head = int(rpc('eth_blockNumber', []), 16)
wins = [(a, min(a + 99, head)) for a in range(head - nb + 1, head + 1, 100)]
def get(w):
    try: return w, rpc('eth_getLogs', [{'address': PM, 'fromBlock': hex(w[0]), 'toBlock': hex(w[1])}])
    except Exception as e: return w, {'err': str(e)[:200]}
logs = []; fails = []
with cf.ThreadPoolExecutor(th) as ex:
    for i, (w, r) in enumerate(ex.map(get, wins)):
        if isinstance(r, dict): fails.append([w, r]); continue
        for l in r:
            logs.append({'tx': l['transactionHash'], 'b': int(l['blockNumber'], 16), 'i': int(l['transactionIndex'], 16), 't0': l['topics'][0]})
        if i % 50 == 0: print(i, len(wins), len(logs), len(fails), flush=True)
json.dump({'head': head, 'fromBlock': head - nb + 1, 'windows': len(wins), 'fails': fails, 'logs': logs}, open(out, 'w'))
txs = {}
for l in logs: txs.setdefault(l['tx'], l)
print('logs', len(logs), 'txs', len(txs), 'index0', sum(1 for t in txs.values() if t['i'] == 0), 'fails', len(fails))
