"""HyperEVM: the whole history of PoolManager ModifyLiquidity events since deployment (block 45,997,710 to 45,998,505
by eth_getCode bisection), read in 100,000-block windows from an endpoint that serves them."""
import sys, json, time
from lib import *
pm = NETS[999]['poolManager']; U = ['https://rpc.hyperlend.finance']
head = int(rpc(999, 'eth_blockNumber', [], urls=['https://hyperliquid.drpc.org']), 16) - 3
logs = []; lo = 45997000
while lo <= head:
    hi = min(head, lo + 99999)
    logs += rpc(999, 'eth_getLogs', [{'address': pm, 'fromBlock': hex(lo), 'toBlock': hex(hi), 'topics': [MOD]}], urls=U, tries=20)
    lo = hi + 1; time.sleep(1)
json.dump({'chainId': 999, 'head': head, 'lo': 45997000, 'logs': logs}, open('raw/mod-999.json', 'w'))
print('999 logs', len(logs), 'nonpos', sum(1 for l in logs if s256(int(l['data'][2 + 128:2 + 192], 16)) <= 0))
