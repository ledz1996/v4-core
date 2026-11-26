"""Creation transaction of a hook in a known block without tracing: direct call to 0x4e59b448 (address recomputed), CREATE
transaction, or the transaction that emitted the first log of the hook in that block. Records from, to, selector, type,
chainId and the sender's nonce on the empty networks. usage: quickprov.py url block hook. Read only."""
import sys, json
sys.path.insert(0, '.')
from rpcu import rpc
from kk import c2, rlp_create
u, blk, h = sys.argv[1], int(sys.argv[2]), sys.argv[3].lower()
D2 = '0x4e59b44847b379578588920ca78fbf26c0b4956c'
cv = [rpc(u, 'web3_clientVersion', [])]
b = rpc(u, 'eth_getBlockByNumber', [hex(blk), True]); res = None
for t in b['transactions']:
    to = (t['to'] or '').lower()
    if to == D2 and len(t['input']) > 66:
        inp = bytes.fromhex(t['input'][2:])
        if c2(D2, inp[:32], inp[32:]) == h: res = {'how': 'direct call to CREATE2 deployer', 'salt': '0x' + inp[:32].hex()}
    if not t['to'] and rlp_create(t['from'], int(t['nonce'], 16)) == h: res = {'how': 'CREATE transaction'}
    if res: res.update({'tx': t['hash'], 'from': t['from'], 'to': t['to'], 'type': t.get('type'), 'chainId': t.get('chainId'), 'nonce': int(t['nonce'], 16)}); break
if not res:
    L = rpc(u, 'eth_getLogs', [{'address': h, 'fromBlock': hex(blk), 'toBlock': hex(blk)}])
    if L:
        t = rpc(u, 'eth_getTransactionByHash', [L[0]['transactionHash']])
        res = {'how': 'inside a call (first hook log)', 'tx': t['hash'], 'from': t['from'], 'to': t['to'], 'sel': t['input'][:10], 'type': t.get('type'), 'chainId': t.get('chainId'),
               'firstLog': L[0]['topics'], 'toCodeLen': (len(rpc(u, 'eth_getCode', [t['to'], 'latest'])) - 2) // 2 if t['to'] else None}
cv.append(rpc(u, 'web3_clientVersion', []))
out = {'url': u, 'client': cv, 'block': blk, 'hook': h, 'txCount': len(b['transactions']), 'result': res}
json.dump(out, open('raw/prov_%s_%d.json' % (h[:10], blk), 'w'), indent=1); print(json.dumps(out)[:900])
