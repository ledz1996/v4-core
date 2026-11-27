import sys, json
from rpc30 import R
U, pm = sys.argv[1], sys.argv[2]
def has(b): return len(R(U, 'eth_getCode', [pm, hex(b)])[0]) > 2
lo, hi = 0, int(R(U, 'eth_blockNumber', [])[0], 16)
while lo < hi:
    m = (lo + hi) // 2
    if has(m): hi = m
    else: lo = m + 1
print(json.dumps({'url': U, 'pm': pm, 'firstBlockWithCode': lo, 'client': R(U, 'web3_clientVersion', [])[0]}))
