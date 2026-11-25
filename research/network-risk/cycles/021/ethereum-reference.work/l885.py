"""L-885: when and by whom 0x8366a39c... was created on Ethereum, and what it holds. Read-only."""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc
A = '0x8366a39cc670b4001a1121b8f6a443a643e40951'
U = sys.argv[1]
head = int(rpc(U, 'eth_blockNumber', []), 16)
def has(b): return len(rpc(U, 'eth_getCode', [A, hex(b)])) > 2
lo, hi = 0, head
assert has(hi)
while hi - lo > 1:
    m = (lo + hi) // 2
    if has(m): hi = m
    else: lo = m
blk = rpc(U, 'eth_getBlockByNumber', [hex(hi), True])
out = {'endpoint': U, 'head': head, 'firstBlockWithCode': hi, 'timestamp': int(blk['timestamp'], 16), 'creators': []}
for tx in blk['transactions']:
    r = rpc(U, 'eth_getTransactionReceipt', [tx['hash']])
    hit = (r.get('contractAddress') or '').lower() == A or any(l['address'].lower() == A for l in r['logs'])
    if hit or tx['to'] is None:
        out['creators'].append({'hash': tx['hash'], 'from': tx['from'], 'to': tx['to'], 'contractAddress': r.get('contractAddress'), 'logsFromA': sum(l['address'].lower() == A for l in r['logs']), 'input4': tx['input'][:10]})
out['balanceWei'] = int(rpc(U, 'eth_getBalance', [A, 'latest']), 16)
out['nonce'] = int(rpc(U, 'eth_getTransactionCount', [A, 'latest']), 16)
out['owner'] = rpc(U, 'eth_call', [{'to': A, 'data': '0x8da5cb5b'}, 'latest'])
out['protocolFeeController'] = rpc(U, 'eth_call', [{'to': A, 'data': '0xf02de3b2'}, 'latest'])
print(json.dumps(out, indent=1))
json.dump(out, open('l885.json', 'w'), indent=1)
