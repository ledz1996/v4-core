# Part two on the full currency lists (priced or not): every pooled currency that has a function whose name says it acts for a
# holder passed as argument gets one trial per such function, with the PoolManager as that argument and an ordinary account as caller.
import sys, json, os, re, collections
from concurrent.futures import ThreadPoolExecutor
from base import *
import holder, hfam
from live2 import bals
SKIP = re.compile(r'^(burnFrom\(address,uint256\)|upgradeTo|updatePauser|updateOwner|updateAndCall|swapV2Call)')
def run(cid, per=30, workers=6):
    pm = net(cid)['poolManager'].lower()
    T = hfam.tokens(cid)
    sel_ok = {s: [n for n in v if not SKIP.match(n)] for s, v in hfam.WANT.items()}
    T = {t: [s for s in ss if sel_ok.get(s)] for t, ss in T.items()}
    T = {t: ss for t, ss in T.items() if ss}
    toks = sorted(T)
    B = bals(cid, toks, pm)
    now = int(time.time()); far = now + 5 * 365 * 86400
    jobs = []; n = 0
    for t in toks:
        b = B.get(t) or 0
        if b < 3: continue
        amt = b // 3; pl = []
        for s in T[t]:
            for nm in sel_ok[s][:3]:
                for cd in holder.named(nm, pm, amt, far) or []: pl.append((nm, t, cd))
        if not pl: continue
        n += 1
        jobs.append((t, amt, [('BASE', t, sel('balanceOf(address)')[2:] + adr(pm))] + pl[:per]))
    print(cid, net(cid)['name'], 'tokens with such a function', len(toks), 'with a balance', n, 'trials', sum(len(j[2]) - 1 for j in jobs), flush=True)
    hits = []; st = collections.Counter()
    def job(j):
        t, amt, ch = j
        data = '0x' + adr(t) + adr(A) + u256(amt) + adr(SINK) + ''.join(holder.item(adr(tg) + cd) for nm, tg, cd in ch)
        for k in range(6):
            r = ecall(cid, pm, data, {pm: {'code': MULTI}, A: {'code': FWD}}, gas=29_000_000 if cid == 999 else (120_000_000 if k < 2 else 45_000_000), rot=hash(t) + k, tries=1, timeout=120)
            if isinstance(r, str) and len(r) == 2 + 512 * len(ch):
                return j, [[int(r[2 + 512 * q + 64 * m: 66 + 512 * q + 64 * m], 16) for m in range(8)] for q in range(len(ch))]
            time.sleep(0.4 * (k + 1))
        return j, None
    with ThreadPoolExecutor(workers) as ex:
        for j, ws in ex.map(job, jobs):
            t, amt, ch = j
            if ws is None: st['callfail'] += 1; continue
            base = ws[0]
            for (nm, tg, cd), w in zip(ch[1:], ws[1:]):
                st['trials'] += 1
                if w[2]: st['accepted'] += 1
                c = holder.classify(base, w)
                if c: st[c] += 1
                if c and c != 'raise-paid': hits.append(dict(t=t, fn=nm, cat=c, amt=str(amt), base=[str(x) for x in base], w=[str(x) for x in w], data=cd))
    json.dump(dict(chainId=cid, tokens=len(toks), withBalance=n, stats=dict(st), hits=hits), open(os.path.join(RAW7, 'hfam_%d.json' % cid), 'w'), indent=0)
    print(cid, net(cid)['name'], dict(st), flush=True)
    for h in hits[:40]:
        w = [int(x) for x in h['w']]; b = [int(x) for x in h['base']]
        print('    ', h['t'], h['cat'], h['fn'][:50], 'dPM', w[3] - b[3], 'dA', w[4] - b[4], 'amt', h['amt'], 'full', w[5], b[5])
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
