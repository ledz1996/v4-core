"""L-997: collect the last 2,000 mined Arc transactions (back from a fixed head) that emit a PoolManager Swap or
ModifyLiquidity log and in which the PoolManager neither sends nor receives native USDC (no EIP-7708 Transfer log of
the system emitter names it). Deterministic, no sampling. Read-only RPC. Writes raw/selection.json, raw/logs.json, raw/txs.json."""
import json, sys, os
H = os.path.dirname(os.path.abspath(__file__)); C21 = os.path.join(H, '..', '..', '..', '021', 'theme-arc-running-code.work')
sys.path.insert(0, C21); sys.path.insert(0, os.path.join(H, '..', '..', '..', '..', 'tools', 'opdiff'))
from rpc import call, batch
from evm import keccak
U = 'https://rpc.mainnet.arc.io'; PM = '0x8366a39cc670b4001a1121b8f6a443a643e40951'
HEAD = int(sys.argv[1]); EM = '0xfffffffffffffffffffffffffffffffffffffffe'
T = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'; pmt = '0x' + '0' * 24 + PM[2:]
SW = '0x' + keccak(b'Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)').hex()
ML = '0x' + keccak(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)').hex()
os.makedirs(os.path.join(H, 'raw'), exist_ok=True)
out = {'head': HEAD, 'endpoint': U, 'clientBefore': call(U, 'arc_getVersion', []), 'seed': None, 'topics': [SW, ML], 'chunks': []}
cand = {}; natx = set(); emlogs = []; pmlogs = []
hi = HEAD
while True:
    lo = hi - 999
    a = call(U, 'eth_getLogs', [{'fromBlock': hex(lo), 'toBlock': hex(hi), 'address': EM, 'topics': [T, pmt]}])
    b = call(U, 'eth_getLogs', [{'fromBlock': hex(lo), 'toBlock': hex(hi), 'address': EM, 'topics': [T, None, pmt]}])
    c = call(U, 'eth_getLogs', [{'fromBlock': hex(lo), 'toBlock': hex(hi), 'address': PM}])
    emlogs += a + b; pmlogs += c
    for l in a + b: natx.add(l['transactionHash'])
    for l in c:
        if l['topics'][0] in (SW, ML):
            k = l['transactionHash']; v = (int(l['blockNumber'], 16), int(l['logIndex'], 16))
            if k not in cand or v < cand[k]: cand[k] = v
    n = len([k for k in cand if k not in natx])
    out['chunks'].append([lo, hi, len(a), len(b), len(c), n])
    print(lo, hi, len(a), len(b), len(c), n, flush=True)
    hi = lo - 1
    if n >= 2000: break
sel = sorted([k for k in cand if k not in natx], key=lambda k: cand[k], reverse=True)[:2000]
out['window'] = [min(cand[k][0] for k in sel), HEAD]; out['selected'] = sel
out['excludedNative'] = len([k for k in cand if k in natx])
out['clientAfter'] = call(U, 'arc_getVersion', [])
json.dump(out, open(os.path.join(H, 'raw/selection.json'), 'w'), indent=0)
json.dump({'emitter': emlogs, 'pm': pmlogs}, open(os.path.join(H, 'raw/logs.json'), 'w'))
print('window', out['window'], len(sel), 'excludedNative', out['excludedNative'])
txo = {}
for i in range(0, len(sel), 10):
    ch = sel[i:i+10]
    r = batch(U, [('eth_getTransactionByHash', [h]) for h in ch] + [('eth_getTransactionReceipt', [h]) for h in ch])
    for j, h in enumerate(ch): txo[h] = {'tx': r[j], 'rec': r[len(ch)+j]}
blocks = sorted({int(v['tx']['blockNumber'], 16) for v in txo.values()})
bl = {}
for i in range(0, len(blocks), 20):
    ch = blocks[i:i+20]
    r = batch(U, [('eth_getBlockByNumber', [hex(b), False]) for b in ch])
    for b, x in zip(ch, r): bl[b] = x
json.dump({'tx': txo, 'blocks': {str(k): v for k, v in bl.items()}, 'client': call(U, 'arc_getVersion', [])}, open(os.path.join(H, 'raw/txs.json'), 'w'))
print('fetched', len(txo), len(bl))
