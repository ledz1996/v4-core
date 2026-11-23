# Find the blocks in [lo, hi] where balanceOf(PoolManager) of a token changes, by bisection. Read-only eth_call.
import sys, json
from lib import *
from config import CFG
def bal(u, t, pm, b):
    for i in range(4):
        try: return int(rpc(u, 'eth_call', [{'to': t, 'data': '0x70a08231' + adr(pm)}, hex(b)]), 16)
        except Exception as e: err = e; time.sleep(1)
    raise err
def jumps(cid, t, lo, hi, url=None, maxj=40):
    u = url or CFG[cid]['state'][0]; pm = net(cid)['poolManager'].lower(); cache = {}; out = []
    def g(b):
        if b not in cache: cache[b] = bal(u, t, pm, b)
        return cache[b]
    def rec(a, b):
        if len(out) >= maxj or g(a) == g(b): return
        if b == a + 1: out.append((b, g(a), g(b))); return
        m = (a + b) // 2; rec(a, m); rec(m, b)
    rec(lo, hi); return out
if __name__ == '__main__':
    cid = int(sys.argv[1]); t = sys.argv[2]; o = json.load(open('raw/mismatch_%d.json' % cid))
    for b, x, y in jumps(cid, t, o['B1'], o['B2']): print(b, x, y, y - x)
