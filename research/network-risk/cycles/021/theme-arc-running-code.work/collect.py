"""Collect the last 2,000 mined Arc transactions (counting back from a fixed head) in which the PoolManager sends or
receives native USDC, from the EIP-7708 Transfer logs of the system emitter, plus every PoolManager log in the window.
Deterministic: no sampling, so no seed applies (seed recorded as none). Read-only RPC."""
import json, sys
sys.path.insert(0, '.')
from rpc import call
U = 'https://rpc.mainnet.arc.io'; PM = '0x8366a39cc670b4001a1121b8f6a443a643e40951'
HEAD = 33140226; EM = '0xfffffffffffffffffffffffffffffffffffffffe'
T = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'; pmt = '0x' + '0' * 24 + PM[2:]
out = {'head': HEAD, 'endpoint': U, 'clientBefore': call(U, 'arc_getVersion', []), 'seed': None, 'chunks': []}
txs = {}; emlogs = []; pmlogs = []
hi = HEAD
while len(txs) < 2000:
    lo = hi - 999
    a = call(U, 'eth_getLogs', [{'fromBlock': hex(lo), 'toBlock': hex(hi), 'address': EM, 'topics': [T, pmt]}])
    b = call(U, 'eth_getLogs', [{'fromBlock': hex(lo), 'toBlock': hex(hi), 'address': EM, 'topics': [T, None, pmt]}])
    c = call(U, 'eth_getLogs', [{'fromBlock': hex(lo), 'toBlock': hex(hi), 'address': PM}])
    emlogs += a + b; pmlogs += c
    for l in a + b: txs.setdefault(l['transactionHash'], int(l['blockNumber'], 16))
    out['chunks'].append([lo, hi, len(a), len(b), len(c)])
    print(lo, hi, len(a), len(b), len(c), len(txs), flush=True)
    hi = lo - 1
sel = sorted(txs.items(), key=lambda x: -x[1])
# the last 2,000: order by (block, then log index of first native log) descending
first = {}
for l in emlogs: 
    k = l['transactionHash']; v = (int(l['blockNumber'], 16), int(l['logIndex'], 16))
    if k not in first or v < first[k]: first[k] = v
sel = sorted(first, key=lambda k: first[k], reverse=True)[:2000]
out['window'] = [min(first[k][0] for k in sel), HEAD]
out['selected'] = sel
out['clientAfter'] = call(U, 'arc_getVersion', [])
json.dump(out, open('raw/selection.json', 'w'), indent=0)
json.dump({'emitter': emlogs, 'pm': pmlogs}, open('raw/logs.json', 'w'))
print('window', out['window'], len(sel))
