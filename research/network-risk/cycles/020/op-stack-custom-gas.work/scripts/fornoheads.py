"""L-895: does forno's op-geth backend follow the canonical Celo chain? Sends batches
[web3_clientVersion, eth_blockNumber, eth_getBlockByNumber(N) for N in probe blocks, web3_clientVersion]
and keeps answers where both version strings agree, then compares block hashes per backend.
Also compares against a second public endpoint. Read-only. Usage: python3 fornoheads.py <out.json>"""
import json, sys, urllib.request, time, collections
URL = 'https://forno.celo.org'
OTHER = ['https://rpc.ankr.com/celo', 'https://celo.drpc.org', 'https://celo-json-rpc.stakely.io']
def post(url, body):
    r = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    return json.load(urllib.request.urlopen(r, timeout=60))
head = int(post(URL, {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_blockNumber', 'params': []})['result'], 16)
probes = [75046580, 75046581, 75046582, 76000000, 80000000, 83000000, head - 2000, head - 200]
seen = collections.defaultdict(dict); heads = collections.defaultdict(list)
for k in range(40):
    body = [{'jsonrpc': '2.0', 'id': 0, 'method': 'web3_clientVersion', 'params': []},
            {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_blockNumber', 'params': []}]
    body += [{'jsonrpc': '2.0', 'id': 10 + i, 'method': 'eth_getBlockByNumber', 'params': [hex(n), False]} for i, n in enumerate(probes)]
    body += [{'jsonrpc': '2.0', 'id': 99, 'method': 'web3_clientVersion', 'params': []}]
    try: res = {x['id']: x for x in post(URL, body)}
    except Exception as e: time.sleep(2); continue
    v0, v9 = res[0].get('result'), res[99].get('result')
    if v0 != v9: continue
    be = v0.split('/')[0]
    heads[be].append(int(res[1]['result'], 16))
    for i, n in enumerate(probes):
        b = res[10 + i].get('result')
        seen[be][n] = (b or {}).get('hash') if b else ('error:' + json.dumps(res[10 + i].get('error'))[:120] if res[10 + i].get('error') else None)
    time.sleep(0.3)
other = {}
for u in OTHER:
    try:
        other[u] = {'version': post(u, {'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []}).get('result'),
                    'blocks': {n: (post(u, {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getBlockByNumber', 'params': [hex(n), False]}).get('result') or {}).get('hash') for n in probes}}
    except Exception as e: other[u] = {'error': str(e)[:200]}
res = {'head': head, 'probes': probes, 'byBackend': {k: {str(n): h for n, h in v.items()} for k, v in seen.items()},
       'headsSeen': {k: [min(v), max(v), len(v)] for k, v in heads.items()}, 'other': {u: {**o, 'blocks': {str(n): h for n, h in o.get('blocks', {}).items()}} for u, o in other.items()}}
json.dump(res, open(sys.argv[1], 'w'), indent=1)
print(json.dumps(res, indent=1))
