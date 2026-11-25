"""Transactions with an ERC-20 Transfer log whose recipient is the PoolManager (catches settle-only transactions that emit no PoolManager log). Read only.
Usage: xfer2pm.py <chainId> <lo> <hi> <span> <url> <out.json>"""
import sys, os, json, time, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rpcu import rpc
cid, lo, hi, span, url, out = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], sys.argv[6]
PM = {4326: '0xacb7e78fa05d562e0a5d3089ec896d57d057d38e', 999: '0x12d4fd9c5dedd00ab8a0bce2cf0167bbf94b6b1f'}[cid]
T = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
top = '0x' + '0' * 24 + PM[2:]
def one(a):
    b = min(hi, a + span - 1)
    def go(a, b):
        try: return rpc(url, 'eth_getLogs', [{'topics': [T, None, top], 'fromBlock': hex(a), 'toBlock': hex(b)}], timeout=120, tries=4)
        except Exception as e:
            if b - a < 100: raise
            m = (a + b) // 2; return go(a, m) + go(m + 1, b)
    return [(int(l['blockNumber'], 16), l['transactionHash'], l['address'].lower()) for l in go(a, b)]
rows = []
with cf.ThreadPoolExecutor(4) as ex:
    for r in ex.map(one, range(lo, hi + 1, span)): rows += r
txs = {}
for b, h, tok in rows: txs.setdefault(h, [b, set()])[1].add(tok)
json.dump({'chainId': cid, 'lo': lo, 'hi': hi, 'txs': {h: [v[0], sorted(v[1])] for h, v in txs.items()}}, open(out, 'w'))
print(cid, len(rows), len(txs))
