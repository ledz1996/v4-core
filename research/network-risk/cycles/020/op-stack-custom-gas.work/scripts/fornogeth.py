"""L-895, second part: per probe block, send [web3_clientVersion, eth_getBlockByNumber(N), web3_clientVersion]
batches to forno until each backend has answered, and record the hash each backend gives, plus each
backend's eth_blockNumber. Read-only. Usage: python3 fornogeth.py <out.json>"""
import json, sys, urllib.request, time
URL = 'https://forno.celo.org'
def post(body):
    r = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    return {x['id']: x for x in json.load(urllib.request.urlopen(r, timeout=60))}
probes = [75046580, 75046581, 75046582, 76000000, 80000000, 83000000, 'latest']
out = {}
for n in probes:
    got = {}
    for k in range(60):
        if len(got) == 2: break
        p = [n if n == 'latest' else hex(n), False]
        try: res = post([{'jsonrpc': '2.0', 'id': 0, 'method': 'web3_clientVersion', 'params': []},
                         {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getBlockByNumber', 'params': p},
                         {'jsonrpc': '2.0', 'id': 2, 'method': 'web3_clientVersion', 'params': []}])
        except Exception as e: time.sleep(1); continue
        if res[0].get('result') != res[2].get('result'): continue
        be = res[0]['result'].split('/')[0]
        if be in got: continue
        b = res[1].get('result')
        got[be] = {'hash': b.get('hash'), 'number': int(b['number'], 16), 'timestamp': int(b['timestamp'], 16)} if b else {'error': res[1].get('error')}
        time.sleep(0.2)
    out[str(n)] = got
json.dump(out, open(sys.argv[1], 'w'), indent=1); print(json.dumps(out, indent=1))
