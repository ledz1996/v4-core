# Run a swap inside a real unlock without sending anything: debug_traceCall of the deployed V4 Quoter (quoteExactInputSingle or
# quoteExactOutputSingle) from an unrelated address. When the pool does not exist, a state override writes slot0 of that pool id
# in the PoolManager (sqrtPrice 2^96, tick 0, the key's static fee), which is what initialize would store (src/libraries/Pool.sol,
# StateLibrary POOLS_SLOT = 6). The Quoter always reverts at the end, so no delta has to be settled.
# usage: python3 qtr.py <cid> <hook> <c0> <c1> <fee> <ts> <zeroForOne> <amount> [exact=in|out] [override=1|0] [depth]
import sys
from common import *
os.chdir(C5)
import probe as P, trace as T
os.chdir(HERE)
from tr import DBG
SELIN = keccak256(b'quoteExactInputSingle(((address,address,uint24,int24,address),bool,uint128,bytes))').hex()[:8]
SELOUT = keccak256(b'quoteExactOutputSingle(((address,address,uint24,int24,address),bool,uint128,bytes))').hex()[:8]
def pool_id(c0, c1, fee, ts, hook): return keccak256(bytes.fromhex(P.key(c0, c1, fee, ts, hook))).hex()
def run(cid, hook, c0, c1, fee, ts, zfo, amount, exact='in', override=True, depth=6, hookData='', frm='0x00000000000000000000000000000000c0ffee03', quiet=False, extra=None):
    n = net(cid); pm = n['poolManager']; q = n['contracts']['Quoter']
    k = P.key(c0, c1, fee, ts, hook); pid = pool_id(c0, c1, fee, ts, hook)
    hd = hookData
    data = (SELIN if exact == 'in' else SELOUT) + P.w(32) + k + P.w(zfo) + P.w(amount) + P.w(0x100) + P.w(len(hd) // 2) + hd.ljust((len(hd) + 63) // 64 * 64, '0')
    ov = dict(extra or {})
    if override:
        slot = keccak256(bytes.fromhex(pid) + (6).to_bytes(32, 'big')).hex()
        slot0 = (1 << 96) | ((fee if fee != 0x800000 else 0) << 208)
        ov[pm] = {'stateDiff': {'0x' + slot: '0x' + P.w(slot0)}}
    last = None
    for u in DBG.get(cid, []) + urls(cid):
        try:
            r = T.trace(u, {'from': frm, 'to': q, 'data': '0x' + data}, overrides=ov or None)
            if not quiet:
                print('# pool id 0x%s traced on %s' % (pid, u))
                for l in T.show(r, maxdepth=depth): print(l[:300])
            return r
        except Exception as e: last = repr(e)[:300]
    print('trace failed', last)
if __name__ == '__main__':
    a = sys.argv
    run(int(a[1]), a[2].lower(), a[3], a[4], int(a[5]), int(a[6]), int(a[7]), int(float(a[8])), a[9] if len(a) > 9 else 'in', (a[10] != '0') if len(a) > 10 else True, int(a[11]) if len(a) > 11 else 6)
