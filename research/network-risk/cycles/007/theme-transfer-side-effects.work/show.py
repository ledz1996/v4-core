# Rows of the surcharge sweep where the PoolManager balance falls by more than the amount.
import sys, json, os, collections
from base import *
def load(cid, div=3, tag=''):
    d = jz(os.path.join(RAW7, 'surch%s_%d_div%d.json.gz' % (tag, cid, div))); live = jz(os.path.join(RAW7, 'live_%d.json.gz' % cid))['rows']
    return d, live
def show(cid, div=3, minbp=0.0, tag=''):
    d, live = load(cid, div, tag)
    by = collections.defaultdict(list)
    for r in d['rows']:
        if not r['w']: continue
        b0, r0, amt, ok, b1, r1, sk, b2 = [int(x) for x in r['w']]
        if not ok or b0 == 0 or amt == 0: continue
        loss = b0 - b1
        if loss > amt:
            by[r['t']].append((r['kind'], r['a'], (loss - amt) / amt, (r1 - r0) / amt, sk, (b2 - b1) / amt, loss - amt))
    for t, rows in sorted(by.items(), key=lambda x: -live[x[0]]['usd']):
        L = live[t]
        mx = max(x[2] for x in rows)
        if mx * 1e4 < minbp: continue
        kinds = collections.Counter(x[0] for x in rows)
        print('%d %s %-10s usd %.2f  max surcharge %.6f%% (%d base units)  kinds %s' % (cid, t, (L['sym'] or '')[:10], L['usd'], mx * 100, max(x[6] for x in rows), dict(kinds)))
        if mx > 1e-5:
            for x in sorted(rows, key=lambda x: -x[2])[:6]: print('      %-14s %s surcharge %.4f%% recipient got %.4f%% skim ok %d returned %.4f%%' % (x[0], x[1], x[2] * 100, x[3] * 100, x[4], x[5] * 100))
if __name__ == '__main__':
    mb = 0.0
    for c in sys.argv[1:]:
        if c.startswith('minbp='): mb = float(c[6:]); continue
        show(int(c), minbp=mb)
