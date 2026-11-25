"""eth_simulateV1 at the parent block with the block's earlier transactions and the target, at the mined gas limit and at
a larger one, to see whether the target's log count depends on the gas it is given. Read-only."""
import sys, json
sys.path.insert(0, '.')
from rpc import call, batch
U = sys.argv[2] if len(sys.argv) > 2 else 'https://rpc.mainnet.arc.io'
D = json.load(open('raw/txs.json')); h = sys.argv[1]
tx = D['tx'][h]['tx']; bn = int(tx['blockNumber'], 16); idx = int(tx['transactionIndex'], 16); blk = D['blocks'][str(bn)]
hs = blk['transactions'][:idx]
prev = batch(U, [('eth_getTransactionByHash', [x]) for x in hs]) if hs else []
def c(t, gas=None):
    o = {'from': t['from'], 'to': t['to'], 'input': t['input'], 'value': t['value'], 'gas': gas or t['gas'], 'nonce': t['nonce']}
    if t.get('maxFeePerGas'): o['maxFeePerGas'] = t['maxFeePerGas']; o['maxPriorityFeePerGas'] = t['maxPriorityFeePerGas']
    else: o['gasPrice'] = t['gasPrice']
    if t.get('authorizationList'): o['authorizationList'] = t['authorizationList']
    return o
out = {'tx': h, 'client': call(U, 'arc_getVersion', []), 'runs': []}
for g in [None, hex(int(tx['gas'], 16) * 2), hex(int(tx['gas'], 16) * 4)]:
    r = call(U, 'eth_simulateV1', [{'blockStateCalls': [{'calls': [c(p) for p in prev] + [c(tx, g)]}], 'validation': False, 'traceTransfers': False}, hex(bn - 1)])
    last = r[0]['calls'][-1]
    out['runs'].append({'gas': g or tx['gas'], 'status': last['status'], 'logs': len(last['logs']), 'gasUsed': last['gasUsed'], 'pmLogs': sum(1 for l in last['logs'] if l['address'].lower() == '0x8366a39cc670b4001a1121b8f6a443a643e40951')})
    print(out['runs'][-1], 'mined logs', len(D['tx'][h]['rec']['logs']), flush=True)
out['clientAfter'] = call(U, 'arc_getVersion', [])
json.dump(out, open('raw/simcheck_%s.json' % h[:10], 'w'), indent=1)
