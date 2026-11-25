"""Collect up to 12 distinct pool ids from recent Swap logs of the Avalanche PoolManager (100 block windows).
Usage: python3 pools.py <out.json>"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'opdiff'))
from evm import rpc
URL = 'https://api.avax.network/ext/bc/C/rpc'; PM = '0x06380c0e0912312b5150364b9dc4542ba0dbbc85'
SWAP = '0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f'
cv = rpc(URL, 'web3_clientVersion', [])
head = int(rpc(URL, 'eth_blockNumber', []), 16); pools = {}; hi = head
for k in range(60):
    r = rpc(URL, 'eth_getLogs', [{'address': PM, 'topics': [SWAP], 'fromBlock': hex(hi - 99), 'toBlock': hex(hi)}])
    for e in r: pools.setdefault(e['topics'][1], int(e['blockNumber'], 16))
    hi -= 100
    if len(pools) >= 12: break
json.dump({'clientVersion': cv, 'clientVersionEnd': rpc(URL, 'web3_clientVersion', []), 'head': head, 'scannedFrom': hi, 'pools': pools}, open(sys.argv[1], 'w'), indent=1)
print(len(pools), head, hi)
