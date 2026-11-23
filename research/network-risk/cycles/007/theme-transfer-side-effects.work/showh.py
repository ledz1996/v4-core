# Hits of the holder-argument sweep, grouped by token.
import sys, json, os, collections
from base import *
def show(cid, cats=('lowered',), maxrows=6):
    d = jz(os.path.join(RAW7, 'holder_%d.json.gz' % cid))
    for t, o in sorted(d['tokens'].items(), key=lambda x: -x[1]['usd']):
        hs = [h for h in o['hits'] if h['cat'] in cats]
        if not hs: continue
        base = [int(x) for x in o['base']]
        print('%d %s %-12s usd %.2f trials %d hits %d' % (cid, t, (o['sym'] or '')[:12], o['usd'], o['trials'], len(hs)))
        seen = set()
        for h in hs:
            k = (h['fn'].split('~')[0], h['cat'])
            if k in seen: continue
            seen.add(k)
            w = [int(x) for x in h['w']]
            print('     %-13s %-55s dPM %.6g%% of amt, dA %.6g%%, full transfer after %d (base %d)  data %s' % (h['cat'], h['fn'][:55], (w[3] - base[3]) / max(1, int(h['amt'])) * 100, (w[4] - base[4]) / max(1, int(h['amt'])) * 100, w[5], base[5], h['data'][:8 + 64 * 2]))
            if len(seen) >= maxrows: break
if __name__ == '__main__':
    cats = ('lowered',)
    for c in sys.argv[1:]:
        if c.startswith('cats='): cats = tuple(c[5:].split(',')); continue
        show(int(c), cats)
