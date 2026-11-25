"""Run cycle 17's offsets.py (large-offset copy, load and hash vectors) on rpc-bsc.48.club only,
with every eth_call sent as a batch [web3_clientVersion, eth_call] to tag the build that answered."""
import sys, json, urllib.request, collections, runpy
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import evm
URL = 'https://rpc-bsc.48.club'; tags = collections.Counter(); orig = evm.rpc
def rpc(url, method, params, timeout=60):
    if url != URL or method != 'eth_call': return orig(url, method, params, timeout)
    body = json.dumps([{'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []},
                       {'jsonrpc': '2.0', 'id': 2, 'method': method, 'params': params}]).encode()
    req = urllib.request.Request(url, data=body, headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    with urllib.request.urlopen(req, timeout=timeout, context=evm._ctx) as r: j = json.load(r)
    d = {x['id']: x for x in j}; tags[d[1].get('result', 'ERR')] += 1
    if 'error' in d[2]: raise RuntimeError(json.dumps(d[2]['error'])[:300])
    return d[2]['result']
evm.rpc = rpc
S = '/home/user/v4-core/research/network-risk/cycles/017/established-l1.work/scripts/offsets.py'
sys.argv = [S, sys.argv[1], '5600']
try:
    runpy.run_path(S, run_name='__main__')
finally:
    print('TAGS', json.dumps(tags))
