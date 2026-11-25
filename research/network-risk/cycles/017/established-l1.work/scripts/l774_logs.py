"""L-774: count PoolManager logs per block for BSC blocks 135,480,000-135,490,000 on several endpoints."""
import json, sys, urllib.request, time, collections
PM = '0x28e2ea090877bf75740558f6bfb36a5ffee9e9df'
EPS = {'dataseed1': 'https://bsc-dataseed1.bnbchain.org', 'dataseed2': 'https://bsc-dataseed2.bnbchain.org',
       'publicnode-reth': 'https://bsc-rpc.publicnode.com', '48club': 'https://rpc-bsc.48.club'}
def rpc(url, m, p, t=60):
    for a in range(4):
        try:
            r = urllib.request.Request(url, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
            j = json.loads(urllib.request.urlopen(r, timeout=t).read())
            if 'error' in j: raise Exception(j['error'])
            return j['result']
        except Exception as e:
            err = e; time.sleep(1 + a)
    raise err
A, B, STEP = 135480000, 135490000, int(sys.argv[2]) if len(sys.argv) > 2 else 200
out = {}
for name, url in EPS.items():
    per = collections.Counter(); errs = []
    b = A
    while b < B:
        e = min(b + STEP - 1, B - 1)
        try:
            logs = rpc(url, 'eth_getLogs', [{'address': PM, 'fromBlock': hex(b), 'toBlock': hex(e)}])
            for l in logs: per[int(l['blockNumber'], 16)] += 1
        except Exception as x:
            errs.append([b, e, str(x)[:200]])
        b = e + 1
    out[name] = {'total': sum(per.values()), 'blocks': len(per), 'per': dict(per), 'errors': errs}
    print(name, out[name]['total'], out[name]['blocks'], len(errs), flush=True)
json.dump(out, open(sys.argv[1], 'w'))
