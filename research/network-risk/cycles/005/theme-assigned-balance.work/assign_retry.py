# Rerun the assign trials for tokens whose batch failed (gas or reply size), with small batches.
import sys, json, gzip, os, collections
from concurrent.futures import ThreadPoolExecutor
from common import *
from asm import MULTI, FWD
from assign_sweep import item, variants, classify, A, SINK
def run(cid, per=5):
    fn = os.path.join(RAW, 'assign_%d.json.gz' % cid)
    x = json.load(gzip.open(fn)); fam = json.load(gzip.open(os.path.join(RAW, 'families_%d.json.gz' % cid)))
    bad = sorted({(h['fam'], h['token']) for h in x['hits'] if h['cat'] == 'callfail'})
    if not bad: print(cid, 'nothing to retry'); return
    pm = net(cid)['poolManager']; now = int(time.time()); jobs = []
    for key, t in bad:
        f = fam[key]; fns = f['fns'] + f['trig']
        r = ecall(cid, t, sel('balanceOf(address)') + adr(pm))
        b = int(r, 16) if isinstance(r, str) and len(r) >= 66 else 0
        if b < 3: continue
        amt = max(1, b // 3)
        base = ('BASE', adr(t) + sel('balanceOf(address)')[2:] + adr(pm))
        items = []
        for nm in fns:
            for cd in variants(nm, pm, amt, now): items.append((nm, adr(t) + cd))
        for i in range(0, len(items), per): jobs.append((key, t, amt, [base] + items[i:i + per]))
    hits = [h for h in x['hits'] if h['cat'] != 'callfail']; still = 0; tr = 0
    def job(j):
        key, t, amt, ch = j
        data = '0x' + adr(t) + adr(A) + u256(amt) + adr(SINK) + ''.join(item(p) for nm, p in ch)
        r = ecall(cid, pm, data, {pm: {'code': MULTI}, A: {'code': FWD}}, gas=45_000_000, rot=hash(t) % 7)
        if not isinstance(r, str) or len(r) != 2 + 512 * len(ch): return j, None
        return j, [[int(r[2 + 512 * k + 64 * m: 66 + 512 * k + 64 * m], 16) for m in range(8)] for k in range(len(ch))]
    with ThreadPoolExecutor(5) as ex:
        for j, ws in ex.map(job, jobs):
            key, t, amt, ch = j
            if ws is None: still += 1; hits.append(dict(fam=key, token=t, cat='callfail', n=len(ch))); continue
            for (nm, p), w in zip(ch[1:], ws[1:]):
                tr += 1
                c = classify(ws[0], w, amt)
                if c: hits.append(dict(fam=key, token=t, fn=nm, cat=c, amt=str(amt), w=[str(z) for z in w], base=[str(z) for z in ws[0]], data=p[40:]))
    x['hits'] = hits; x['stats']['retryTrials'] = tr; x['stats']['stillFailed'] = still
    json.dump(x, gzip.open(fn, 'wt'))
    print(cid, 'retried tokens', len(bad), 'jobs', len(jobs), 'trials', tr, 'still failed batches', still, flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
