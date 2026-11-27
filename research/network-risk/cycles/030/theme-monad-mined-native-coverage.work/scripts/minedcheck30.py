"""Tie the replay to mined state: for sampled blocks, (a) the prestate of the block's first PoolManager transaction equals
eth_getStorageAt at the parent block, and (b) every slot the replay wrote (last writer in the block) equals eth_getStorageAt
at the block, which is the state committed by consensus (Monad's delayed execution header carries the state root).
Usage: python3 -I minedcheck30.py <blocksdir> <written.json> <out.json> <nblocks> <seed> url [url ...]"""
import sys, os, json, gzip, random
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rpc30 import R
PM = '0x188d586ddcf52439676ca21a244753fa19f9ea8e'
bd, wf, out, n, seed = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]); urls = sys.argv[6:]
W = json.load(open(wf)); blocks = sorted(int(b) for b, v in W.items() if v)
rnd = random.Random(seed); pick = sorted(rnd.sample(blocks, min(n, len(blocks))))
cv0 = {u: R(u, 'web3_clientVersion', [])[0] for u in urls}
def one(b):
    d = json.load(gzip.open(os.path.join(bd, f'{b}.json.gz')))
    pre = (d['txs'][0]['pre'] or {}).get('storage') or {}
    bad = []; np = 0
    for k, v in list(pre.items())[:40]:
        g = R(urls, 'eth_getStorageAt', [PM, k, hex(b - 1)])[0]; np += 1
        if int(g, 16) != int(v, 16): bad.append(['pre', k, v, g])
    nw = 0
    for k, v in W[str(b)].items():
        g = R(urls, 'eth_getStorageAt', [PM, k, hex(b)])[0]; nw += 1
        if int(g, 16) != int(v, 16): bad.append(['post', k, v, g])
    return {'block': b, 'preChecked': np, 'postChecked': nw, 'bad': bad}
with ThreadPoolExecutor(4) as ex: rows = list(ex.map(one, pick))
res = {'seed': seed, 'urls': urls, 'clientBefore': cv0, 'clientAfter': {u: R(u, 'web3_clientVersion', [])[0] for u in urls},
       'blocks': len(rows), 'preChecked': sum(r['preChecked'] for r in rows), 'postChecked': sum(r['postChecked'] for r in rows),
       'differ': [r for r in rows if r['bad']], 'rows': rows}
json.dump(res, open(out, 'w'), indent=1)
print({k: v for k, v in res.items() if k not in ('rows',)})
