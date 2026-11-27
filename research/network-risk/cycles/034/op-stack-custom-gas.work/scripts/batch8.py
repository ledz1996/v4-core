"""Cycle 34 L-1258: send a JSON-RPC batch of eight web3_clientVersion items N times; count batches with more than one build.
Read-only. Usage: batch8.py <url> <n> <out.json>"""
import sys, json, ssl, urllib.request, collections, time, concurrent.futures as cf
ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
url, n, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
body = json.dumps([{'jsonrpc': '2.0', 'id': i, 'method': 'web3_clientVersion', 'params': []} for i in range(8)]).encode()
def one(k):
    for t in range(3):
        try:
            req = urllib.request.Request(url, data=body, headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
            with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
                j = json.load(r)
            return [x.get('result') for x in sorted(j, key=lambda x: x['id'])]
        except Exception as e:
            last = str(e)[:100]; time.sleep(1 + t)
    return ['ERR ' + last]
with cf.ThreadPoolExecutor(4) as ex:
    res = list(ex.map(one, range(n)))
multi = [r for r in res if len(set(r)) > 1]
cnt = collections.Counter(v for r in res for v in r)
o = {'url': url, 'batches': n, 'multiBuild': len(multi), 'itemCounts': cnt, 'examples': multi[:5],
     'batchBuildSets': collections.Counter(' | '.join(sorted(set(r))) for r in res)}
json.dump(o, open(out, 'w'), indent=1)
print(json.dumps({k: o[k] for k in ('url', 'batches', 'multiBuild', 'itemCounts')}))
