"""Cycle 34: CLZ (0x1e) of 2^255 and of 1 by eth_call with a code override, each call tied to its build; also eth_config. Read-only."""
import json, ssl, urllib.request, collections, sys
ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
A = '0x00000000000000000000000000000000c1a2c0de'
CODE = '0x600160ff1b1e60005260011e60205260406000f3'
def post(u, b):
    r = urllib.request.Request(u, data=json.dumps(b).encode(), headers={'content-type':'application/json','user-agent':'curl/8'})
    return {x['id']: x for x in json.load(urllib.request.urlopen(r, timeout=30, context=ctx))}
out = {}
for u in ['https://forno.celo.org', 'https://rpc.xlayer.tech']:
    c = collections.Counter()
    for i in range(40):
        j = post(u, [{'jsonrpc':'2.0','id':1,'method':'web3_clientVersion','params':[]},
                     {'jsonrpc':'2.0','id':2,'method':'eth_call','params':[{'to':A,'data':'0x'}, 'latest', {A:{'code':CODE}}]},
                     {'jsonrpc':'2.0','id':3,'method':'web3_clientVersion','params':[]}])
        r = j[2].get('result') or json.dumps(j[2].get('error'))[:120]
        c[(j[1]['result'] if j[1]['result']==j[3]['result'] else 'mixed', r)] += 1
    cfg = post(u, [{'jsonrpc':'2.0','id':1,'method':'eth_config','params':[]}])[1]
    out[u] = {'clz': [[list(k), v] for k, v in c.items()], 'eth_config': cfg}
json.dump(out, open(sys.argv[1],'w'), indent=1)
for u, v in out.items():
    print(u); [print('  ', x) for x in v['clz']]; print('  eth_config', json.dumps(v['eth_config'])[:1500])
