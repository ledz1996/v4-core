# Step 2a. Every selector of a priced currency (own code and implementation) is called with no arguments by static call.
# Answers that look like an address become candidate recipients. For candidates with code: token0(), token1(), factory().
import sys, json, os, collections
from concurrent.futures import ThreadPoolExecutor
from base import *
from stubs import GET, CSIZE
ST = '0x00000000000000000000000000000000000ba1a5'
STD = {'06fdde03', '095ea7b3', '18160ddd', '23b872dd', '313ce567', '70a08231', '95d89b41', 'a9059cbb', 'dd62ed3e', '39509351', 'a457c2d7', 'ffffffff', '4e487b71', '08c379a0', '00000000', '01ffc9a7', '3644e515', '7ecebe00', 'd505accf'}
def chunks(cid, items, per, enc, width, stub, workers=5, gas=45_000_000):
    """items -> list of ints (one per item); None where the call failed."""
    out = [None] * len(items)
    def one(lo, hi, depth=0):
        data = '0x' + ''.join(enc(x) for x in items[lo:hi])
        for k in range(4):
            r = ecall(cid, ST, data, {ST: {'code': stub}}, gas=gas, rot=k + depth + lo, tries=2)
            if isinstance(r, str) and len(r) == 2 + 64 * (hi - lo):
                for j in range(hi - lo): out[lo + j] = int(r[2 + 64 * j: 66 + 64 * j], 16)
                return
            time.sleep(0.4)
        if hi - lo > 1:
            m = (lo + hi) // 2; one(lo, m, depth + 1); one(m, hi, depth + 1)
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda i: one(i, min(len(items), i + per)), range(0, len(items), per)))
    return out
def isaddr(v): return v is not None and 2 ** 128 < v < 2 ** 160
def run(cid):
    S = jz(os.path.join(RAW7, 'sels_%d.json.gz' % cid))
    items = []
    for t, o in S.items():
        for s in (o.get('sels') or [])[:300]:
            if s not in STD: items.append((t, s))
    per = 400 if cid != 999 else 150
    res = chunks(cid, items, per, lambda x: adr(x[0]) + x[1].ljust(64, '0'), 64, GET, gas=45_000_000 if cid != 999 else 29_000_000)
    cand = collections.defaultdict(dict)
    fails = 0
    for (t, s), v in zip(items, res):
        if v is None: fails += 1; continue
        if isaddr(v):
            a = '0x%040x' % v
            if a != t: cand[t].setdefault(a, []).append(s)
    for t, o in S.items():
        for e in o.get('emb') or []:
            if e != t and isaddr(int(e, 16)): cand[t].setdefault(e, []).append('emb')
    addrs = sorted(set(a for d in cand.values() for a in d))
    cs = chunks(cid, addrs, 800, lambda a: adr(a), 64, CSIZE)
    size = dict(zip(addrs, cs))
    wc = [a for a in addrs if size.get(a)]
    q = [(a, s) for a in wc for s in ('0dfe1681', 'd21220a7', 'c45a0155')]
    r2 = chunks(cid, q, 600, lambda x: adr(x[0]) + x[1].ljust(64, '0'), 64, GET)
    info = collections.defaultdict(dict)
    for (a, s), v in zip(q, r2): info[a][s] = ('0x%040x' % v) if isaddr(v) else None
    out = {}
    for t in S:
        rows = []
        for a, src in cand.get(t, {}).items():
            i = info.get(a, {})
            rows.append(dict(a=a, src=src[:4], size=size.get(a), t0=i.get('0dfe1681'), t1=i.get('d21220a7'), fac=i.get('c45a0155')))
        out[t] = rows
    wz(os.path.join(RAW7, 'getters_%d.json.gz' % cid), out)
    npair = sum(1 for t, rows in out.items() if any(t in (r['t0'], r['t1']) for r in rows))
    fac = collections.Counter(r['fac'] for t, rows in out.items() for r in rows if t in (r['t0'], r['t1']) and r['fac'])
    other = collections.Counter((r['t1'] if r['t0'] == t else r['t0']) for t, rows in out.items() for r in rows if t in (r['t0'], r['t1']))
    print(cid, net(cid)['name'], 'tokens', len(S), 'static calls', len(items), 'failed', fails, 'candidate addresses', len(addrs), 'with code', len(wc), 'tokens naming a pair of their own', npair, flush=True)
    print('   factories', fac.most_common(12), flush=True)
    print('   counterparts', other.most_common(8), flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
