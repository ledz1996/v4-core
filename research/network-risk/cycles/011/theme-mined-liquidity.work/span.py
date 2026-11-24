import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import rpc, keccak
MOD = '0x' + keccak(b'ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)').hex()
pm, url = sys.argv[1], sys.argv[2]
head = int(rpc(url, 'eth_blockNumber', []), 16)
for span in map(int, sys.argv[3:]):
    try:
        L = rpc(url, 'eth_getLogs', [{'address': pm, 'fromBlock': hex(head - span), 'toBlock': hex(head), 'topics': [MOD]}], timeout=90); print(span, len(L))
    except Exception as e: print(span, 'ERR', str(e)[:100])
