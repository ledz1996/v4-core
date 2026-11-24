# Lead L-155 on all 21 networks for the priced currencies of cycle 7: is any address that a pooled token names
# (implementation, embedded address, any zero argument getter answer with code) a second currency id on the same ledger?
# Step 1: X.balanceOf(PoolManager) for every named address X. Step 2: for every nonzero X, the PoolManager address
# (measuring stub by state override, eth_call) sends one third of its balance of T and X is read before and after, and the reverse.
# Input: cycles/007/theme-transfer-side-effects.work/raw/getters_<chain>.json.gz and live_<chain>.json.gz. Nothing is sent.
import sys, os, json, gzip, time
HERE2 = os.path.dirname(os.path.abspath(__file__))
T6 = os.path.join(HERE2, '..', '..', '006', 'theme-currency-lists.work')
T7 = os.path.join(HERE2, '..', '..', '007', 'theme-transfer-side-effects.work')
sys.path.insert(0, T6)
from common import *
from mirror import MIRROR, SINK
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, HERE2)
from impl_face import BALS
def jz(fn): return json.load(gzip.open(fn, 'rt'))
def run(cid, per=100):
    pm = net(cid)['poolManager']
    G = jz(os.path.join(T7, 'raw', 'getters_%d.json.gz' % cid)); live = dict(jz(os.path.join(T7, 'raw', 'live_%d.json.gz' % cid))['rows'])
    named = {}
    for t, lst in G.items():
        for e in lst:
            x = e['a'].lower()
            if e.get('size') and x != t.lower() and x != pm.lower(): named.setdefault(x, []).append(t.lower())
    L = sorted(named)
    def one(chunk, depth=0):
        r = ecall(cid, STUB, '0x' + adr(pm) + ''.join(adr(t) for t in chunk), {STUB: {'code': BALS}}, gas=40_000_000, rot=depth + len(chunk), tries=4)
        if isinstance(r, str) and len(r) == 2 + 64 * len(chunk):
            return {t: int(r[2 + 64 * j: 66 + 64 * j], 16) for j, t in enumerate(chunk)}
        if len(chunk) > 1:
            h = len(chunk) // 2; o = one(chunk[:h], depth + 1); o.update(one(chunk[h:], depth + 1)); return o
        return {chunk[0]: None}
    out = {}
    with ThreadPoolExecutor(3) as ex:
        for res in ex.map(lambda i: one(L[i:i + per]), range(0, len(L), per)): out.update(res)
    nz = {k: v for k, v in out.items() if v}; fail = [k for k, v in out.items() if v is None]
    jobs = []
    for x in nz:
        ts = [t for t in named[x] if int(live.get(t, {}).get('bal') or 0) > 2][:4]
        for t in ts: jobs.append((x, t))
    def mir(j):
        x, t = j; row = {'X': x, 'T': t, 'Xbal': str(nz[x]), 'Tsym': live.get(t, {}).get('sym'), 'Tusd': live.get(t, {}).get('usd'), 'XisPriced': x in live}
        for a, k in ((t, 'sendT'), (x, 'sendX')):
            r = ecall(cid, pm, '0x' + adr(SINK) + adr(a) + adr(x) + adr(t), {pm: {'code': MIRROR}}, gas=30_000_000, rot=int(x[-2:], 16), tries=4)
            if isinstance(r, str) and len(r) == 2 + 256:
                v = [int(r[2 + 64 * i: 66 + 64 * i], 16) for i in range(4)]     # X before, X after, T before, T after
                row[k] = [str(i) for i in v]
            else: row[k] = None
        return row
    rows = []
    with ThreadPoolExecutor(3) as ex:
        for row in ex.map(mir, jobs): rows.append(row)
    hits = []
    for r in rows:
        a = r.get('sendT'); b = r.get('sendX')
        if a and a[2] != a[3] and a[0] != a[1]: hits.append(('T moved and X reading changed', r))
        if b and b[0] != b[1] and b[2] != b[3]: hits.append(('X moved and T reading changed', r))
    blk = rpc(urls2(cid)[0], 'eth_blockNumber', [])
    res = {'chainId': cid, 'block': blk, 'pricedTokens': len(G), 'namedAddresses': len(L), 'answered': len(out) - len(fail), 'failed': len(fail),
           'nonzero': len(nz), 'pairsTested': len(rows), 'pairsFailed': sum(1 for r in rows if r.get('sendT') is None or r.get('sendX') is None), 'hits': hits, 'rows': rows}
    json.dump(res, gzip.open(os.path.join(HERE2, 'raw', 'all_faces_%d.json.gz' % cid), 'wt'))
    print(cid, 'block', blk, 'priced', len(G), 'named', len(L), 'answered', len(out) - len(fail), 'failed', len(fail), 'nonzero', len(nz), 'pairs', len(rows),
          'pairsFailed', res['pairsFailed'], 'hits', len(hits), flush=True)
    for why, r in hits[:40]: print('   HIT', why, json.dumps(r)[:420], flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]:
        try: run(int(c))
        except Exception as e: print(c, 'ERROR', repr(e)[:300], flush=True)
