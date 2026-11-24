"""Ask forno.celo.org repeatedly, with batches of web3_clientVersion + eth_blockNumber + eth_getBlockByNumber(fixed N)
+ PoolManager eth_getBalance and eth_getStorageAt slot 0, and compare the two client families."""
import json, sys, ssl, urllib.request, concurrent.futures as cf
ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
URL = 'https://forno.celo.org'; PM = '0x288dc841A52FCA2707c6947B3A777c5E56cd87BC'
N = int(sys.argv[1]); out = sys.argv[2]
def q():
    body = [{'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []},
            {'jsonrpc': '2.0', 'id': 2, 'method': 'eth_blockNumber', 'params': []},
            {'jsonrpc': '2.0', 'id': 3, 'method': 'eth_getBlockByNumber', 'params': [hex(N), False]},
            {'jsonrpc': '2.0', 'id': 4, 'method': 'eth_getBalance', 'params': [PM, hex(N)]},
            {'jsonrpc': '2.0', 'id': 5, 'method': 'eth_getStorageAt', 'params': [PM, '0x0', hex(N)]},
            {'jsonrpc': '2.0', 'id': 6, 'method': 'eth_getBlockByNumber', 'params': ['latest', False]}]
    r = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    j = {x['id']: x for x in json.load(urllib.request.urlopen(r, timeout=30, context=ctx))}
    b = j[3].get('result') or {}; l = j[6].get('result') or {}
    return {'client': j[1].get('result'), 'head': int(j[2]['result'], 16) if 'result' in j[2] else None,
            'hashN': b.get('hash'), 'stateRootN': b.get('stateRoot'), 'pmBalanceN': j[4].get('result', j[4].get('error')),
            'pmSlot0N': j[5].get('result', j[5].get('error')), 'latestNumber': l.get('number'), 'latestHash': l.get('hash'), 'latestTs': l.get('timestamp')}
res = []
with cf.ThreadPoolExecutor(6) as ex:
    for f in [ex.submit(q) for _ in range(60)]:
        try: res.append(f.result())
        except Exception as e: res.append({'error': str(e)[:100]})
fam = {}
for r in res:
    c = (r.get('client') or 'err').split('/')[0]; fam.setdefault(c, []).append(r)
summary = {c: {'n': len(v), 'clients': sorted({x.get('client') for x in v}), 'hashN': sorted({x.get('hashN') for x in v}),
               'stateRootN': sorted({x.get('stateRootN') for x in v}), 'pmBalanceN': sorted({str(x.get('pmBalanceN')) for x in v}),
               'pmSlot0N': sorted({str(x.get('pmSlot0N')) for x in v}), 'heads': sorted({x.get('head') for x in v})[-3:],
               'latest': sorted({(x.get('latestNumber'), x.get('latestTs')) for x in v})[-2:]} for c, v in fam.items()}
json.dump({'block': N, 'summary': summary, 'raw': res}, open(out, 'w'), indent=1)
print(json.dumps({'block': N, 'summary': summary}, indent=1))
