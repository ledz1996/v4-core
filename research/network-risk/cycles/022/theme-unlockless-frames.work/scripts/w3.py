"""Reads every candidate transaction with an ERC-20 Transfer out of the PoolManager and no PoolManager log
(Arc, Elysium), with its receipt, and classifies the top-level call. Read-only.
Usage: w3.py <cid> <url>   (writes raw/w3-<cid>.json)"""
import sys, os, json, collections, time
sys.path.insert(0, os.path.dirname(__file__))
from rpcu import call
cid, url = sys.argv[1], sys.argv[2]
W = os.path.join(os.path.dirname(__file__), '..', 'raw')
s = json.load(open(os.path.join(W, 'list-%s.json' % cid))); pm = s['pm']; PMT = '0x' + '0' * 24 + pm[2:]
T = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
bytx = collections.defaultdict(list)
for l in s['logs'].values(): bytx[l['tx']].append(l)
outs = [t for t, ls in bytx.items() if any(l['topics'][0] == T and len(l['topics']) == 3 and l['topics'][1] == PMT and l['addr'] != pm for l in ls)]
w3 = [t for t in outs if not any(l['addr'] == pm for l in bytx[t])]
res = {'clientVersionStart': call(url, 'web3_clientVersion', []), 'tx': {}}
for h in w3:
    for k in range(6):
        tx, e1 = call(url, 'eth_getTransactionByHash', [h]); rc, e2 = call(url, 'eth_getTransactionReceipt', [h])
        if tx and rc: break
        time.sleep(3 + 3 * k)
    code, _ = call(url, 'eth_getCode', [tx['from'], hex(int(tx['blockNumber'], 16))])
    res['tx'][h] = {'block': int(tx['blockNumber'], 16), 'from': tx['from'].lower(), 'fromCodeLen': (len(code) - 2) // 2 if code else None,
                    'to': (tx.get('to') or '').lower(), 'sel': (tx.get('input') or '0x')[:10], 'status': rc['status'],
                    'logs': [[l['address'].lower(), l['topics'][:3], l['data'][:66]] for l in rc['logs']]}
    time.sleep(0.3)
res['clientVersionEnd'] = call(url, 'web3_clientVersion', [])
R = res['tx']
res['summary'] = {'n': len(R), 'byToSel': dict(collections.Counter(r['to'] + ':' + r['sel'] + ':' + r['status'] for r in R.values())),
                  'toPM': [h for h, r in R.items() if r['to'] == pm]}
json.dump(res, open(os.path.join(W, 'w3-%s.json' % cid), 'w'), indent=1)
print(json.dumps(res['summary'], indent=1))
