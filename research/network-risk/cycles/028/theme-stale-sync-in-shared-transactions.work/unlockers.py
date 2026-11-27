# Sample recent PoolManager Swap and ModifyLiquidity logs; the second topic is msg.sender of the PoolManager call, i.e. the unlocker.
# Count unlockers and the top-level transaction target. Brackets each network with web3_clientVersion.
import sys, os, json, collections, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from config import CFG
SW = '0x' + keccak256(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()
ML = '0x' + keccak256(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)').hex()
def run(cid, want=400):
    n = net(cid); urls = [n['rpc']] + CFG[cid]['state'] + [CFG[cid]['logs']]
    out = dict(chainId=cid)
    for u in urls:
        try:
            out['clientBefore'] = rpc(u, 'web3_clientVersion', [])
            head = int(rpc(u, 'eth_blockNumber', []), 16); out['head'] = head; hi = head - 1; logs = []; chunk = CFG[cid]['chunk']; req = 0
            while len(logs) < want and req < 60:
                lo = hi - chunk + 1
                try: l = rpc(u, 'eth_getLogs', [{'address': n['poolManager'], 'topics': [[SW, ML]], 'fromBlock': hex(lo), 'toBlock': hex(hi)}], timeout=60, tries=2)
                except Exception as e:
                    if chunk > 20: chunk //= 4; continue
                    raise
                logs += l; hi = lo - 1; req += 1
            out['range'] = [hi + 1, head - 1]; out['url'] = u; break
        except Exception as e: out['err'] = str(e)[:200]; logs = []
    txs = {}
    for l in logs: txs.setdefault(l['transactionHash'], set()).add('0x' + l['topics'][2][-40:])
    hs = list(txs)[:250]
    def gt(h):
        try: return rpc(out['url'], 'eth_getTransactionByHash', [h], tries=2)
        except Exception: return None
    with cf.ThreadPoolExecutor(6) as ex: tl = list(ex.map(gt, hs))
    unl = collections.Counter(); to = collections.Counter(); types = collections.Counter(); rows = []
    for h, t in zip(hs, tl):
        for s in txs[h]: unl[s] += 1
        if t: to[(t.get('to') or '').lower()] += 1; types[t.get('type')] += 1; rows.append(dict(h=h, to=(t.get('to') or '').lower(), type=t.get('type'), value=t.get('value'), unlockers=sorted(txs[h]), sel=t['input'][:10] if t.get('input') else None))
    out.update(logs=len(logs), txs=len(txs), sampledTxs=len(hs), unlockers=unl.most_common(15), txTo=to.most_common(10), txTypes=dict(types), rows=rows)
    out['clientAfter'] = rpc(out['url'], 'web3_clientVersion', [])
    return out
cids = [int(x) for x in sys.argv[1:]] or [480, 8453, 4217]
with cf.ThreadPoolExecutor(3) as ex: res = list(ex.map(run, cids))
json.dump(res, open('out/unlockers.json', 'w'), indent=1)
for r in res:
    print(r['chainId'], r.get('clientBefore'), r.get('range'), 'logs', r.get('logs'), 'txs', r.get('txs'), r.get('txTypes'), r.get('err', ''))
    print('  unlockers', r.get('unlockers')); print('  tx.to', r.get('txTo'))
