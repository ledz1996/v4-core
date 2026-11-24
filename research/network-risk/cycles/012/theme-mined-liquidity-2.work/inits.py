"""Initialize events of the PoolManager over its whole history, as a second source of pool keys.
Usage: inits.py <chainId> <fromBlock> <span> <url>"""
import sys, json, time
from lib import *
INIT = '0x' + keccak(b'Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)').hex()
cid, lo, span, url = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
pm = NETS[cid]['poolManager']; head = int(rpc(cid, 'eth_blockNumber', [], urls=[url]), 16)
keys = {}
while lo <= head:
    hi = min(head, lo + span - 1)
    for x in rpc(cid, 'eth_getLogs', [{'address': pm, 'fromBlock': hex(lo), 'toBlock': hex(hi), 'topics': [INIT]}], urls=[url], tries=20):
        d = x['data']; w = [int(d[2 + 64 * i:66 + 64 * i], 16) for i in range(3)]
        keys[x['topics'][1]] = {'c0': '0x' + x['topics'][2][26:], 'c1': '0x' + x['topics'][3][26:], 'fee': w[0], 'spacing': s256(w[1]), 'hooks': '0x%040x' % w[2]}
    lo = hi + 1; time.sleep(0.5)
json.dump(keys, open(f'raw/inits-{cid}.json', 'w'))
print(cid, 'pools initialized', len(keys))
