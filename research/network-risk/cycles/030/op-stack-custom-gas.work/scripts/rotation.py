"""Cycle 30 op-stack-custom-gas, lead L-1174: send N batches [web3_clientVersion x3] to one endpoint and count
which build answers each element and whether the three elements of a batch agree. Read-only.
Usage: python3 rotation.py <out.json> <url> [N] [pause]"""
import sys, json, time, urllib.request, ssl, collections
ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
out, url = sys.argv[1], sys.argv[2]; N = int(sys.argv[3]) if len(sys.argv) > 3 else 300; pause = float(sys.argv[4]) if len(sys.argv) > 4 else 0.3
body = json.dumps([{'jsonrpc': '2.0', 'id': i, 'method': 'web3_clientVersion', 'params': []} for i in (1, 2, 3)]).encode()
per = collections.Counter(); whole = collections.Counter(); mixed = 0; errs = 0; seq = []
for n in range(N):
    try:
        req = urllib.request.Request(url, body, {'content-type': 'application/json', 'user-agent': 'curl/8'})
        with urllib.request.urlopen(req, timeout=30, context=ctx) as r: j = json.load(r)
        v = [str({x['id']: x for x in j}[i].get('result')) for i in (1, 2, 3)]
        for x in v: per[x] += 1
        if len(set(v)) == 1: whole[v[0]] += 1
        else: mixed += 1
        seq.append([x.split('-')[1].split('/')[0] if '-' in x else x for x in v])
    except Exception as e:
        errs += 1; seq.append(['ERR', repr(e)[:80]])
    time.sleep(pause)
r = {'url': url, 'batches': N, 'perElement': dict(per), 'wholeBatch': dict(whole), 'mixedBatches': mixed, 'errors': errs, 'sequence': seq, 'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
json.dump(r, open(out, 'w'), indent=0); print(json.dumps({k: v for k, v in r.items() if k != 'sequence'}, indent=1))
