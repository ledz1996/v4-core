"""Task 1 and 3 probe for theme-avalanche-sae (cycle 25). Read-only.
Repeatedly: read the latest header, then at once ask for headers latest+1..latest+4 by explicit number (the backend
resolves an explicit number up to the last accepted block, blocks/access.go:139-146), and for each one that exists ask
eth_getBalance of the PoolManager at that number and time the answer (the state path waits for execution,
sae/rpc/blocks.go:82). Records how many accepted blocks lie ahead of latest and how long a state read for them takes.
usage: probe_gap.py <out.json> <samples> [url]"""
import json, sys, time, ssl, urllib.request
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
PM = '0x06380c0e0912312b5150364b9dc4542ba0dbbc85'
u = sys.argv[3] if len(sys.argv) > 3 else 'https://api.avax.network/ext/bc/C/rpc'
def post(body):
    rq = urllib.request.Request(u, json.dumps(body).encode(), {'content-type': 'application/json', 'user-agent': 'rpc-client'})
    t = time.time()
    try:
        return json.loads(urllib.request.urlopen(rq, timeout=60, context=CTX).read()), time.time() - t
    except Exception as e:
        return {'exc': str(e)[:200]}, time.time() - t
out = {'url': u, 'clientBefore': post({'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []})[0].get('result'), 'samples': []}
for s in range(int(sys.argv[2])):
    r, _ = post({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getBlockByNumber', 'params': ['latest', False]})
    L = int(r['result']['number'], 16)
    b = [{'jsonrpc': '2.0', 'id': k, 'method': 'eth_getBlockByNumber', 'params': [hex(L + k), False]} for k in range(1, 5)]
    r2, dt = post(b)
    ahead = []
    if isinstance(r2, list):
        for x in sorted(r2, key=lambda x: x['id']):
            if x.get('result'): ahead.append(L + x['id'])
    rec = {'latest': L, 'acceptedAhead': ahead, 'headerBatchSec': round(dt, 3)}
    if ahead:
        n = ahead[-1]
        r3, dt3 = post({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getBalance', 'params': [PM, hex(n)]})
        r4, _ = post({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getBlockByNumber', 'params': ['latest', False]})
        rec.update({'balanceAt': n, 'balance': r3.get('result', r3.get('error')), 'balanceSec': round(dt3, 3), 'latestAfter': int(r4['result']['number'], 16)})
    out['samples'].append(rec)
    time.sleep(0.3)
out['clientAfter'] = post({'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []})[0].get('result')
s = out['samples']
out['summary'] = {'samples': len(s), 'withAcceptedAhead': sum(1 for x in s if x['acceptedAhead']), 'maxAhead': max((len(x['acceptedAhead']) for x in s), default=0),
                  'maxBalanceSec': max((x.get('balanceSec', 0) for x in s), default=0)}
print(json.dumps(out['summary']), out['clientBefore'])
json.dump(out, open(sys.argv[1], 'w'), indent=1)
