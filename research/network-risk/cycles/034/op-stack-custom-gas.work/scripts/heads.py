"""Cycle 34: compare forno backends on head height and on the hash and state root of one fixed block, each batch tied to its build. Read-only."""
import json, ssl, urllib.request, collections, sys
ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
u = 'https://forno.celo.org'
def post(b):
    r = urllib.request.Request(u, data=json.dumps(b).encode(), headers={'content-type':'application/json','user-agent':'curl/8'})
    return {x['id']: x.get('result') for x in json.load(urllib.request.urlopen(r, timeout=30, context=ctx))}
n0 = int(post([{'jsonrpc':'2.0','id':1,'method':'eth_blockNumber','params':[]}])[1],16) - 20
res = collections.defaultdict(collections.Counter)
for i in range(120):
    j = post([{'jsonrpc':'2.0','id':1,'method':'web3_clientVersion','params':[]},
              {'jsonrpc':'2.0','id':2,'method':'eth_getBlockByNumber','params':[hex(n0), False]},
              {'jsonrpc':'2.0','id':3,'method':'eth_blockNumber','params':[]},
              {'jsonrpc':'2.0','id':4,'method':'web3_clientVersion','params':[]}])
    b = j[2] or {}
    res[j[1] if j[1]==j[4] else 'mixed'][(b.get('hash'), b.get('stateRoot'), int(j[3],16)-n0)] += 1
o = {'block': n0, 'byBuild': {k: [[list(a), c] for a, c in v.items()] for k, v in res.items()}}
json.dump(o, open(sys.argv[1],'w'), indent=1)
for k, v in o['byBuild'].items():
    print(k, len(v), 'distinct (hash,root,lag)'); print('  hashes', {x[0][0] for x in v}, 'lags', sorted({x[0][2] for x in v}))
