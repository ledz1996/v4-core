# Step 3. For every priced currency and every candidate recipient: one read-only trial with the measuring stub SURCH placed at the
# PoolManager address by state override. The stub sends balance / divisor to the recipient, reads both balances, calls skim(PoolManager)
# on the recipient and reads the PoolManager balance again. Each trial reverts. Nothing is sent on chain.
import sys, json, os, collections
from concurrent.futures import ThreadPoolExecutor
from base import *
from stubs import SURCH
DEAD = '0x000000000000000000000000000000000000dead'
def recipients(cid, t, G, P, F, mc3):
    out = []; seen = set()
    def add(a, kind):
        a = a.lower()
        if a in seen or int(a, 16) == 0: return
        seen.add(a); out.append((a, kind))
    rows = G.get(t) or []
    for r in rows:
        if t in (r['t0'], r['t1']): add(r['a'], 'named-pair')
    for a, (kind, f) in (P.get(t) or {}).items(): add(a, kind + '-pool')
    n = 0
    for r in rows:
        if r['size'] and n < 8: add(r['a'], 'named-contract'); n += 1
    n = 0
    for r in rows:
        if not r['size'] and n < 4: add(r['a'], 'named-account'); n += 1
    add(SINK, 'plain'); add(t, 'self'); add(DEAD, 'dead')
    if F.get('wrappedNative'): add(F['wrappedNative'], 'contract')
    elif mc3: add(MC3, 'contract')
    return out[:40]
def run(cid, per=10, workers=6, div=3, only=None, tag=''):
    pm = net(cid)['poolManager'].lower()
    live = jz(os.path.join(RAW7, 'live_%d.json.gz' % cid))['rows']
    G = jz(os.path.join(RAW7, 'getters_%d.json.gz' % cid)); P = jz(os.path.join(RAW7, 'pairs_%d.json.gz' % cid)); F = json.load(open(os.path.join(RAW7, 'facs_%d.json' % cid)))
    c = ecall(cid, MC3, '0x', tries=2); mc3 = True
    items = []
    if only is None:
        for t in sorted(live):
            if int(live[t]['bal'] or 0) < 3: continue
            for a, kind in recipients(cid, t, G, P, F, mc3): items.append((t, a, kind))
    else: items = only
    gas = 45_000_000 if cid != 999 else 29_000_000
    if cid == 999: per = 6
    out = [None] * len(items)
    def one(lo, hi, depth=0):
        data = '0x' + u256(div) + ''.join(adr(t) + adr(a) for t, a, k in items[lo:hi])
        for k in range(4):
            r = ecall(cid, pm, data, {pm: {'code': SURCH}}, gas=gas, frm=A, rot=k + depth + lo, tries=2, timeout=120)
            if isinstance(r, str) and len(r) == 2 + 512 * (hi - lo):
                for j in range(hi - lo): out[lo + j] = [int(r[2 + 512 * j + 64 * m: 66 + 512 * j + 64 * m], 16) for m in range(8)]
                return
            time.sleep(0.4)
        if hi - lo > 1:
            m = (lo + hi) // 2; one(lo, m, depth + 1); one(m, hi, depth + 1)
    done = [0]
    def job(i):
        one(i, min(len(items), i + per)); done[0] += 1
        if done[0] % 300 == 0: print(cid, 'calls', done[0], (len(items) + per - 1) // per, flush=True)
    with ThreadPoolExecutor(workers) as ex: list(ex.map(job, range(0, len(items), per)))
    bn = 0
    for u in urls2(cid) + [net(cid)['rpc']]:
        try: bn = int(rpc(u, 'eth_blockNumber', [], tries=2), 16); break
        except Exception: pass
    rows = [dict(t=t, a=a, kind=k, w=[str(x) for x in w] if w else None) for (t, a, k), w in zip(items, out)]
    wz(os.path.join(RAW7, 'surch%s_%d_div%d.json.gz' % (tag, cid, div)), dict(chainId=cid, block=bn, div=div, rows=rows))
    st = collections.Counter()
    for r in rows:
        w = r['w']
        if w is None: st['callfail'] += 1; continue
        b0, r0, amt, ok, b1, r1, sk, b2 = [int(x) for x in w]
        if b0 == 0: st['zero-or-oog'] += 1; continue
        if not ok: st['refused'] += 1; continue
        loss = b0 - b1
        if loss > amt: st['sender-pays-more'] += 1
        elif loss < amt: st['sender-pays-less'] += 1
        else: st['exact'] += 1
    print(cid, net(cid)['name'], 'block', bn, 'div', div, 'tokens', len(set(r['t'] for r in rows)), 'trials', len(rows), dict(st), flush=True)
if __name__ == '__main__':
    div = 3
    for c in sys.argv[1:]:
        if c.startswith('div='): div = int(c[4:]); continue
        run(int(c), div=div)
