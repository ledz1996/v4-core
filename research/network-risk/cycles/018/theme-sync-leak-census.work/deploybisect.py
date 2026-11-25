"""First block with a PoolManager log, by bisection of eth_getLogs counts over [0, b]; paced for rate limits. Read only.
Usage: deploybisect.py <url> <pm> <hi>"""
import sys, json, time, urllib.request, ssl
C = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt'); U, PM, HI = sys.argv[1], sys.argv[2], int(sys.argv[3])
def n(a, b):
    for k in range(10):
        try:
            r = json.loads(urllib.request.urlopen(urllib.request.Request(U, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getLogs', 'params': [{'address': PM, 'fromBlock': hex(a), 'toBlock': hex(b)}]}).encode(), {'content-type': 'application/json', 'user-agent': 'rpc-client'}), context=C, timeout=120).read())
            if 'error' in r: return 10 ** 9
            return len(r['result'])
        except Exception: time.sleep(10 * (k + 1))
    raise SystemExit('gave up')
lo, hi = 0, HI
while hi - lo > 1:
    m = (lo + hi) // 2
    if n(max(0, m - 9999999), m) > 0 or n(0, m) > 0: hi = m
    else: lo = m
    time.sleep(2)
print(hi)
