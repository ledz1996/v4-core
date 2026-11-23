# debug_traceCall of one hook callback from the PoolManager address with a chosen PoolKey; prints the call tree. Read-only.
# usage: python3 tr.py <cid> <hook> <fn> <c0> <c1> <fee> <ts> [zeroForOne=1] [amount=-1e18]
import sys
from common import *
os.chdir(C5)
import probe as P, trace as T
os.chdir(HERE)
DBG = {1: ['https://eth.drpc.org', 'https://mainnet.gateway.tenderly.co'], 42161: ['https://arbitrum.drpc.org', 'https://arbitrum.gateway.tenderly.co'], 137: ['https://polygon.drpc.org', 'https://polygon.gateway.tenderly.co'], 56: ['https://bsc.drpc.org'], 130: ['https://unichain.drpc.org'], 8453: ['https://base.drpc.org'], 4663: ['https://robinhood.drpc.org'], 5042: ['https://arc.drpc.org', 'https://rpc.mainnet.arc.io'], 99901: ['https://rpc.elysium.kinetiq.xyz'], 143: ['https://rpc.monad.xyz', 'https://monad.drpc.org'], 43114: ['https://avalanche.drpc.org'], 10: ['https://optimism.drpc.org'], 57073: ['https://ink.drpc.org'], 999: ['https://hyperliquid.drpc.org', 'https://rpc.purroofgroup.com'], 4217: ['https://rpc.mainnet.tempo.xyz'], 196: ['https://xlayer.drpc.org']}
def run(cid, hook, fn, c0, c1, fee, ts, zfo=1, amt=-10 ** 18, depth=5, frm=None, hookData=''):
    n = net(cid); pm = n['poolManager']
    k = P.key(c0, c1, fee, ts, hook)
    data = P.cd(fn, P.EOA, k, hookData)
    if fn in ('beforeSwap', 'afterSwap'):
        # patch zeroForOne and amountSpecified (words 7 and 8 after selector: sender + 5 key words)
        d = data; w = lambda i: 8 + 64 * i
        d = d[:w(6)] + P.w(zfo) + P.w(amt) + P.w(P.MINP if zfo else P.MAXP) + d[w(9):]
        data = d
    last = None
    for u in DBG.get(cid, []) + urls(cid):
        try:
            r = T.trace(u, {'from': frm or pm, 'to': hook, 'data': '0x' + data}); 
            print('# traced on', u)
            for l in T.show(r, maxdepth=depth): print(l[:330])
            return r
        except Exception as e: last = repr(e)[:200]
    print('trace failed', last)
if __name__ == '__main__':
    a = sys.argv
    run(int(a[1]), a[2].lower(), a[3], a[4], a[5], int(a[6]), int(a[7]), int(a[8]) if len(a) > 8 else 1, int(float(a[9])) if len(a) > 9 else -10 ** 18)
