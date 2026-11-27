"""PoolManager logs on HyperEVM from a start block to head. Usage: logs_since.py <out.json> <url> <from>"""
import sys, json, urllib.request
out, url, start = sys.argv[1], sys.argv[2], int(sys.argv[3])
PM = '0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F'
def rpc(m, p):
    r = urllib.request.Request(url, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json'})
    return json.load(urllib.request.urlopen(r, timeout=60))
head = int(rpc('eth_blockNumber', [])['result'], 16); logs = []; b = start; step = 10000
while b <= head:
    e = min(b + step - 1, head); r = rpc('eth_getLogs', [{'address': PM, 'fromBlock': hex(b), 'toBlock': hex(e)}])
    if 'error' in r: step //= 2; continue
    logs += r['result']; b = e + 1
T = {'0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438': 'Initialize', '0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec': 'ModifyLiquidity', '0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f': 'Swap'}
cnt = {}
for l in logs: n = T.get(l['topics'][0], l['topics'][0][:10]); cnt[n] = cnt.get(n, 0) + 1
print('from', start, 'to', head, 'logs', len(logs), cnt, 'last', int(logs[-1]['blockNumber'], 16) if logs else None)
json.dump({'from': start, 'to': head, 'counts': cnt, 'logs': logs}, open(out, 'w'), indent=1)
