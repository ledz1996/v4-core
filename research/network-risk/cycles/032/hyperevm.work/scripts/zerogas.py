"""Census of gas price 0 transactions by sender in a block range. Usage: zerogas.py <out.json> <url> <from> <to>"""
import sys, json, urllib.request, concurrent.futures as cf
out, url, a, b = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
def batch(nums):
    body = [{'jsonrpc': '2.0', 'id': n, 'method': 'eth_getBlockByNumber', 'params': [hex(n), True]} for n in nums]
    for t in range(5):
        try:
            r = urllib.request.Request(url, json.dumps(body).encode(), {'content-type': 'application/json'})
            return json.load(urllib.request.urlopen(r, timeout=90))
        except Exception: pass
    return []
senders = {}; to = {}; blocks = 0; ntx = 0; z = 0; missing = 0
chunks = [list(range(s, min(s + 50, b + 1))) for s in range(a, b + 1, 50)]
with cf.ThreadPoolExecutor(4) as ex:
    for res in ex.map(batch, chunks):
        for r in res:
            x = r.get('result')
            if not x: missing += 1; continue
            blocks += 1
            for t in x['transactions']:
                ntx += 1
                if int(t.get('gasPrice', '0x1'), 16) == 0:
                    z += 1; senders[t['from'].lower()] = senders.get(t['from'].lower(), 0) + 1
                    k = (t.get('to') or 'create').lower(); to[k] = to.get(k, 0) + 1
pm = '0x12d4fd9c5dedd00ab8a0bce2cf0167bbf94b6b1f'
known = lambda s: s == '0x2222222222222222222222222222222222222222' or s.startswith('0x20000000000000000000000000000000000') or s in ('0x6b9e773128f453f5c2c60935ee2de2cbc5390a24', '0xc20699185c15d0a2fd65779bb5d69f5b0b113c00')
other = {s: c for s, c in senders.items() if not known(s)}
r = {'url': url, 'from': a, 'to': b, 'blocks': blocks, 'missing': missing, 'transactions': ntx, 'zeroGas': z, 'senders': len(senders), 'otherSenders': other, 'toPoolManager': to.get(pm, 0), 'topSenders': sorted(senders.items(), key=lambda kv: -kv[1])[:15]}
print(json.dumps(r, indent=1)); json.dump(r, open(out, 'w'), indent=1)
