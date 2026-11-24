"""Monad (143): every PoolManager log in 100 block windows below a given block (the endpoint limit).
Read-only. Usage: python3 monad_scan.py <out.json> <hiBlock> <nBlocks> <threads>"""
import sys, json, time, itertools, threading, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc
PM = '0x188d586ddcf52439676ca21a244753fa19f9ea8e'
URLS = ['https://rpc.monad.xyz', 'https://rpc3.monad.xyz', 'https://rpc1.monad.xyz', 'https://rpc-mainnet.monadinfra.com']
out, hi, nb, th = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
wins = [(a, min(a + 99, hi)) for a in range(hi - nb + 1, hi + 1, 100)]
ctr = itertools.count()
def get(w):
    for k in range(12):
        u = URLS[next(ctr) % len(URLS)]
        try: return w, rpc(u, 'eth_getLogs', [{'address': PM, 'fromBlock': hex(w[0]), 'toBlock': hex(w[1])}], timeout=30)
        except Exception as e: time.sleep(1 + k)
    return w, None
logs = []; fails = []
with cf.ThreadPoolExecutor(th) as ex:
    for i, (w, r) in enumerate(ex.map(get, wins)):
        if r is None: fails.append(w); continue
        for l in r:
            logs.append({'tx': l['transactionHash'], 'b': int(l['blockNumber'], 16), 'i': int(l['transactionIndex'], 16), 'li': int(l['logIndex'], 16), 'topics': l['topics'], 'data': l['data']})
        if i % 200 == 0: print(i, len(wins), len(logs), len(fails), flush=True)
json.dump({'hi': hi, 'fromBlock': hi - nb + 1, 'windows': len(wins), 'fails': fails, 'logs': logs}, open(out, 'w'))
print('logs', len(logs), 'txs', len({l['tx'] for l in logs}), 'fails', len(fails))
