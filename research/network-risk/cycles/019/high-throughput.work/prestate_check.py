# For a mined Monad tx: compare the prestateTracer value of PoolManager slots with the parent-block value and with
# the post value written by earlier transactions of the same block (prestateTracer diffMode). Read-only RPC.
import json, sys, urllib.request
U = sys.argv[1]; H = sys.argv[2]; PM = sys.argv[3].lower()
def rpc(m, p):
    rq = urllib.request.Request(U, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8.5.0'})
    r = json.load(urllib.request.urlopen(rq, timeout=120)); 
    if 'error' in r: raise Exception(r['error'])
    return r['result']
tx = rpc('eth_getTransactionByHash', [H]); bn = int(tx['blockNumber'], 16); ti = int(tx['transactionIndex'], 16)
pre = rpc('debug_traceTransaction', [H, {'tracer': 'prestateTracer'}])
slots = (pre.get(PM) or {}).get('storage', {})
blk = rpc('eth_getBlockByNumber', [hex(bn), False])
earlier = {}
for j, h2 in enumerate(blk['transactions'][:ti]):
    try: d = rpc('debug_traceTransaction', [h2, {'tracer': 'prestateTracer', 'tracerConfig': {'diffMode': True}}])
    except Exception as e: continue
    for k, v in ((d.get('post') or {}).get(PM) or {}).get('storage', {}).items(): earlier[k] = (j, v)
out = []
for k, v in slots.items():
    par = rpc('eth_getStorageAt', [PM, k, hex(bn - 1)])
    e = earlier.get(k)
    out.append({'slot': k, 'prestate': v, 'parent': par, 'lastEarlierWrite': e, 'prestateEqualsParent': int(v, 16) == int(par, 16),
                'prestateEqualsEarlierWrite': (e is not None and int(v, 16) == int(e[1], 16))})
print(json.dumps({'tx': H, 'block': bn, 'index': ti, 'txsInBlock': len(blk['transactions']), 'slots': out}, indent=1))
