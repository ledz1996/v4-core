# Step 3b. The same trial for the pair addresses that DexScreener lists for a currency and that step 3 has not tried yet.
import sys, os, json
from base import *
import surcharge
def run_new(cid, tag='fac2'):
    import glob
    G = jz(os.path.join(RAW7, 'getters_%d.json.gz' % cid)); P = jz(os.path.join(RAW7, 'pairs_%d.json.gz' % cid)); F = json.load(open(os.path.join(RAW7, 'facs_%d.json' % cid)))
    live = jz(os.path.join(RAW7, 'live_%d.json.gz' % cid))['rows']
    done = set()
    for fn in glob.glob(os.path.join(RAW7, 'surch*_%d_div3.json.gz' % cid)):
        done |= set((r['t'], r['a']) for r in jz(fn)['rows'])
    items = []
    for t in sorted(live):
        if int(live[t]['bal'] or 0) < 3: continue
        for a, kind in surcharge.recipients(cid, t, G, P, F, True):
            if (t, a) not in done: items.append((t, a, kind))
    print(cid, 'new recipients', len(items), flush=True)
    if items: surcharge.run(cid, only=items, tag=tag)
def run(cid):
    fn = os.path.join(RAW7, 'dexs_%d.json.gz' % cid)
    if not os.path.exists(fn): print(cid, 'no dexscreener file'); return
    D = jz(fn); done = set((r['t'], r['a']) for r in jz(os.path.join(RAW7, 'surch_%d_div3.json.gz' % cid))['rows'])
    items = []
    for t, rows in D.items():
        for a, dex, lab, liq in rows:
            if (t, a) not in done: items.append((t, a, 'dexscreener:' + dex + ':' + lab))
    print(cid, 'pairs listed', sum(len(v) for v in D.values()), 'new', len(items), flush=True)
    if items: surcharge.run(cid, only=items, tag='dex')
if __name__ == '__main__':
    if sys.argv[1] == 'new':
        for c in sys.argv[2:]: run_new(int(c))
    else:
        for c in sys.argv[1:]: run(int(c))
