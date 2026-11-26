"""Weaker log form for networks with no trace endpoint (Arc, Elysium). Read-only.
For every candidate transaction with an ERC-20 Transfer out of the PoolManager (from lister.py output), read the
transaction (batched eth_getTransactionByHash) and its receipt status (batched eth_getTransactionReceipt), and flag:
 W1: the top-level call goes to the PoolManager with a selector other than unlock (a direct call cannot pass
     through unlock, because unlockCallback is called on msg.sender) and the transaction succeeded;
 W2: the top-level sender has code (EIP-7702 delegation) and calls the PoolManager directly;
 W3: a Transfer out with no PoolManager log in the transaction (listed in full for reading).
Usage: weak.py <list.json> <out.json> <batch> <url>"""
import sys, os, json, time, collections, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from rpcu import call, CTX
lst, out, B, url = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
s = json.load(open(lst)); pm = s['pm']; PMT = '0x' + '0' * 24 + pm[2:]
T = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
bytx = collections.defaultdict(list)
for l in s['logs'].values(): bytx[l['tx']].append(l)
outs = [t for t, ls in bytx.items() if any(l['topics'][0] == T and len(l['topics']) == 3 and l['topics'][1] == PMT and l['addr'] != pm for l in ls)]


def batch(method, items):
    body = json.dumps([{'jsonrpc': '2.0', 'id': i, 'method': method, 'params': [h]} for i, h in enumerate(items)]).encode()
    for k in range(8):
        try:
            req = urllib.request.Request(url, body, {'content-type': 'application/json', 'user-agent': 'rpc-client'})
            r = json.loads(urllib.request.urlopen(req, timeout=120, context=CTX).read())
            if isinstance(r, list) and all('result' in x and x['result'] for x in r):
                return {x['id']: x['result'] for x in r}
        except Exception as e:
            pass
        time.sleep(3 + 3 * k)
    raise RuntimeError('batch failed')


res = json.load(open(out)) if os.path.exists(out) else {'clientVersionStart': call(url, 'web3_clientVersion', []), 'tx': {}}
todo = [t for t in outs if t not in res['tx']]
for i in range(0, len(todo), B):
    ch = todo[i:i + B]
    a = batch('eth_getTransactionByHash', ch); b = batch('eth_getTransactionReceipt', ch)
    for j, h in enumerate(ch):
        tx, rc = a[j], b[j]
        res['tx'][h] = {'to': (tx.get('to') or '').lower(), 'from': tx['from'].lower(), 'sel': (tx.get('input') or '0x')[:10],
                        'value': tx.get('value'), 'type': tx.get('type'), 'status': rc.get('status'), 'block': int(tx['blockNumber'], 16),
                        'nlogs': len(rc.get('logs') or []), 'pmLogs': sum(1 for l in rc.get('logs') or [] if l['address'].lower() == pm),
                        'outs': [[l['address'].lower(), l['topics'][2], l['data']] for l in rc.get('logs') or [] if l['topics'] and l['topics'][0] == T and len(l['topics']) == 3 and l['topics'][1] == PMT]}
    time.sleep(0.7)
    if (i // B) % 50 == 0:
        json.dump(res, open(out, 'w')); print(i, len(todo), flush=True)
res['clientVersionEnd'] = call(url, 'web3_clientVersion', [])
R = res['tx']
W1 = [h for h, r in R.items() if r['to'] == pm and r['sel'] != '0x48c89491' and r['status'] == '0x1']
toPM = collections.Counter(r['sel'] for r in R.values() if r['to'] == pm)
W3 = [h for h, r in R.items() if r['pmLogs'] == 0 and r['status'] == '0x1']
res['summary'] = {'txWithTransferOut': len(outs), 'read': len(R), 'success': sum(1 for r in R.values() if r['status'] == '0x1'),
                  'W1': W1, 'topLevelToPMSelectors': dict(toPM), 'W3': W3,
                  'W3byTo': dict(collections.Counter(R[h]['to'] for h in W3)), 'W3bySel': dict(collections.Counter(R[h]['to'] + ':' + R[h]['sel'] for h in W3))}
json.dump(res, open(out, 'w'))
print(json.dumps(res['summary'])[:3000])
