"""PoolManager logs on MegaETH from a start block to the head, via eth_getLogs in windows. Usage: python3 -I logs.py <out.jsonl> <from>"""
import json, sys, urllib.request, time
R = 'https://mainnet.megaeth.com/rpc'; PM = '0xacb7e78fa05d562e0a5d3089ec896d57d057d38e'
def rpc(m, p):
    for k in range(6):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(R, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'review-client'}), timeout=120))
            if 'error' in r: raise RuntimeError(r['error'])
            return r['result']
        except Exception as e:
            err = e; time.sleep(2 + 2 * k)
    raise err
head = int(rpc('eth_blockNumber', []), 16); a = int(sys.argv[2]); step = 20000; n = 0
with open(sys.argv[1], 'w') as f:
    while a <= head:
        b = min(head, a + step - 1)
        try:
            L = rpc('eth_getLogs', [{'address': PM, 'fromBlock': hex(a), 'toBlock': hex(b)}])
        except Exception as e:
            step = max(500, step // 2); print('shrink', step, e, flush=True); continue
        for l in L: f.write(json.dumps({'b': int(l['blockNumber'], 16), 'tx': l['transactionHash'], 't0': l['topics'][0]}) + '\n')
        n += len(L); a = b + 1
print('head', head, 'logs', n)
