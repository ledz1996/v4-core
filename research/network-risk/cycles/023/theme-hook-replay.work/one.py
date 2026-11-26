"""Binary search for the creation block of one address on one endpoint, then list transactions of that block. usage: one.py url addr. Read only."""
import sys, json
sys.path.insert(0, '.')
from rpcu import rpc
u, h = sys.argv[1], sys.argv[2].lower()
cv = rpc(u, 'web3_clientVersion', [])
hi = int(rpc(u, 'eth_blockNumber', []), 16); lo = 0
while hi - lo > 1:
    m = (lo + hi) // 2
    if len(rpc(u, 'eth_getCode', [h, hex(m)])) > 2: hi = m
    else: lo = m
b = rpc(u, 'eth_getBlockByNumber', [hex(hi), True])
r = {'url': u, 'client': [cv], 'addr': h, 'block': hi, 'nonceBefore': int(rpc(u, 'eth_getTransactionCount', [h, hex(lo)]), 16), 'txs': [{'hash': t['hash'], 'from': t['from'], 'to': t['to'], 'type': t.get('type'), 'inputLen': (len(t['input']) - 2) // 2, 'sel': t['input'][:10]} for t in b['transactions']]}
r['client'].append(rpc(u, 'web3_clientVersion', []))
json.dump(r, open('raw/create_%s_%s.json' % (h[:10], u.split('//')[1].split('/')[0]), 'w'), indent=1)
print(json.dumps({k: v for k, v in r.items() if k != 'txs'}), len(r['txs']))
for t in r['txs']:
    if t['to'] and t['to'].lower() in ('0x4e59b44847b379578588920ca78fbf26c0b4956c', '0xba5ed099633d3b313e4d5f7bdc1305d3c28ba5ed') or t['to'] is None: print(t)
