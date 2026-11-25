import json, sys
sys.path.insert(0, '.')
from rpc import batch, call
U = 'https://rpc.mainnet.arc.io'
s = json.load(open('raw/selection.json'))
out = {}
hs = s['selected']
for i in range(0, len(hs), 10):
    ch = hs[i:i+10]
    r = batch(U, [('eth_getTransactionByHash', [h]) for h in ch] + [('eth_getTransactionReceipt', [h]) for h in ch])
    for j, h in enumerate(ch): out[h] = {'tx': r[j], 'rec': r[len(ch)+j]}
    print(i, flush=True)
blocks = sorted({int(v['tx']['blockNumber'], 16) for v in out.values()})
bl = {}
for i in range(0, len(blocks), 20):
    ch = blocks[i:i+20]
    r = batch(U, [('eth_getBlockByNumber', [hex(b), False]) for b in ch])
    for b, x in zip(ch, r): bl[b] = x
json.dump({'tx': out, 'blocks': {str(k): v for k, v in bl.items()}, 'client': call(U, 'arc_getVersion', [])}, open('raw/txs.json', 'w'))
