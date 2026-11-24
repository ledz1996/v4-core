"""Census of unsigned system transactions in recent HyperEVM blocks on the archive
client: does any name the PoolManager as sender, target or argument.
Usage: python3 systx_census.py <rpc> <nblocks> <out.json>"""
import json, sys, urllib.request, collections
url, n, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
PM = '12d4fd9c5dedd00ab8a0bce2cf0167bbf94b6b1f'
def rpc(b):
    req = urllib.request.Request(url, json.dumps(b).encode(), {'content-type': 'application/json', 'user-agent': 'review-client'})
    return json.load(urllib.request.urlopen(req, timeout=120))
head = int(rpc({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_blockNumber', 'params': []})['result'], 16)
c = collections.Counter(); hits = []; senders = collections.Counter()
nonce = rpc({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getTransactionCount', 'params': ['0x' + PM, 'latest']})['result']
for lo in range(head - n + 1, head + 1, 25):
    batch = [{'jsonrpc': '2.0', 'id': b, 'method': 'eth_getBlockByNumber', 'params': [hex(b), True]} for b in range(lo, min(lo + 25, head + 1))]
    for r in rpc(batch):
        for i, tx in enumerate((r.get('result') or {}).get('transactions', [])):
            c['tx'] += 1
            if int(tx.get('gasPrice', '0x0'), 16) == 0:
                c['system'] += 1; senders[tx['from'].lower()] += 1
            blob = (tx['from'] + (tx.get('to') or '') + tx.get('input', '')).lower()
            if PM in blob: hits.append({'block': r['id'], 'hash': tx['hash'], 'from': tx['from'], 'to': tx.get('to'), 'gasPrice': tx.get('gasPrice')})
res = {'rpc': url, 'head': head, 'blocks': n, 'counts': c, 'topSystemSenders': senders.most_common(8), 'pmNonce': nonce,
       'systemTxNamingPM': [h for h in hits if int(h['gasPrice'] or '0x0', 16) == 0], 'signedTxNamingPM': len([h for h in hits if int(h['gasPrice'] or '0x0', 16) != 0])}
json.dump(res, open(out, 'w'), indent=1); print(json.dumps(res)[:1500])
