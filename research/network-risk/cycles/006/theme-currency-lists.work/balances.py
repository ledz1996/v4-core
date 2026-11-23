# balanceOf(PoolManager) for every pool currency of one network, through a measuring stub placed by state override (eth_call only).
# Writes raw/bal_<cid>.json.gz {token: balance} and raw/universe_<cid>.json.gz (rows with token and bal2, the shape the sweep
# scripts of cycle 5 expect), which holds the tokens with a balance that cycle 5 did not test.
# usage: python3 balances.py <chainId> [per] [workers]
import sys, json, gzip, os, time
from concurrent.futures import ThreadPoolExecutor
from common import *
from asm import assemble
BALS = assemble('''
0x70a0823100000000000000000000000000000000000000000000000000000000 0 MSTORE
0 CALLDATALOAD 4 MSTORE
0x20
loop:
DUP1 CALLDATASIZE EQ @end JUMPI
0 DUP2 0x100 ADD MSTORE
0x20 DUP2 0x100 ADD 0x24 0 DUP5 CALLDATALOAD 0x493e0 STATICCALL
ISZERO @bad JUMPI
back:
0x20 ADD
@loop JUMP
bad:
0 DUP2 0x100 ADD MSTORE @back JUMP
end:
0x20 CALLDATASIZE SUB 0x120 RETURN
''')
def tokens(cid):
    if cid == 8453:
        import numpy as np
        return ['0x' + bytes(x).hex() for x in np.load('raw/base_tokens.npy')]
    d = json.load(gzip.open('raw/currencies_%d.json.gz' % cid)); return sorted(d['currencies'])
def run(cid, per=500, workers=6, toks=None, tag=''):
    pm = net(cid)['poolManager']; toks = toks or [t for t in tokens(cid) if int(t, 16) != 0]
    fn = 'raw/bal_%d%s.json.gz' % (cid, tag); out = json.load(gzip.open(fn)) if os.path.exists(fn) else {}
    todo = [t for t in toks if t not in out]; print(cid, 'tokens', len(toks), 'todo', len(todo), flush=True)
    def one(chunk, depth=0):
        r = ecall(cid, STUB, '0x' + adr(pm) + ''.join(adr(t) for t in chunk), {STUB: {'code': BALS}}, gas=min(48_000_000, 400_000 * len(chunk) + 1_000_000), rot=depth + (int(chunk[0][-4:], 16) % 7), tries=5)
        if isinstance(r, str) and len(r) == 2 + 64 * len(chunk):
            return {t: str(int(r[2 + 64 * j: 66 + 64 * j], 16)) for j, t in enumerate(chunk)}
        if len(chunk) > 1:
            h = len(chunk) // 2; o = one(chunk[:h], depth + 1); o.update(one(chunk[h:], depth + 1)); return o
        return {chunk[0]: 'fail'}
    done = 0; t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        for res in ex.map(lambda i: one(todo[i:i + per]), range(0, len(todo), per)):
            out.update(res); done += per
            if done % (per * 200) == 0:
                print(cid, 'progress', done, len(todo), round(time.time() - t0), flush=True); json.dump(out, gzip.open(fn, 'wt'))
    json.dump(out, gzip.open(fn, 'wt'))
    nz = {t: b for t, b in out.items() if b != 'fail' and int(b) > 0}
    print(cid, net(cid)['name'], 'read', len(out), 'nonzero', len(nz), 'fail', sum(1 for b in out.values() if b == 'fail'), flush=True)
    return out
def universe_file(cid):
    out = json.load(gzip.open('raw/bal_%d.json.gz' % cid))
    old = set()
    f5 = '../../005/theme-assigned-balance.work/raw/xfer_%d.json.gz' % cid
    if os.path.exists(f5): old = set(json.load(gzip.open(f5))['bal'])
    rows = [dict(token=t, bal2=b) for t, b in out.items() if b != 'fail' and int(b) > 0 and t not in old]
    json.dump(dict(chainId=cid, rows=rows, testedBefore=len(old), withBalance=sum(1 for b in out.values() if b != 'fail' and int(b) > 0)), gzip.open('raw/universe_%d.json.gz' % cid, 'wt'))
    print(cid, 'universe', len(rows), 'tested before', len(old), 'of which in new list', len(old & set(out)), flush=True)
if __name__ == '__main__':
    cid = int(sys.argv[1]); run(cid, int(sys.argv[2]) if len(sys.argv) > 2 else 500, int(sys.argv[3]) if len(sys.argv) > 3 else 6); universe_file(cid)
