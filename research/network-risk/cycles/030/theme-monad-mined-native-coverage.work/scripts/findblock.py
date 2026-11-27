import sys, json
from rpc30 import R
U = 'https://rpc.monad.xyz'
def ts(b): return int(R(U, 'eth_getBlockByNumber', [hex(b), False])[0]['timestamp'], 16)
def find(t):
    lo, hi = 1, int(R(U, 'eth_blockNumber', [])[0], 16)
    while lo < hi:
        mid = (lo + hi) // 2
        if ts(mid) < t: lo = mid + 1
        else: hi = mid
    return lo
import calendar
out = {}
for d in sys.argv[1:]:
    t = calendar.timegm(__import__('time').strptime(d, '%Y-%m-%dT%H:%M:%SZ')); b = find(t); out[d] = {'block': b, 'ts': ts(b), 'prevTs': ts(b - 1)}
print(json.dumps(out))
