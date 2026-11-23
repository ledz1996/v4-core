# free-raise and A-gain hits of the holder sweep with their size in USD.
import sys, json, os, collections
from base import *
def show(cid, cats=('free-raise', 'A-gain', 'final-differs', 'unlock', 'lock-only'), minusd=0.01):
    d = jz(os.path.join(RAW7, 'holder_%d.json.gz' % cid)); live = jz(os.path.join(RAW7, 'live_%d.json.gz' % cid))['rows']
    for t, o in sorted(d['tokens'].items(), key=lambda x: -x[1]['usd']):
        hs = [h for h in o['hits'] if h['cat'] in cats]
        if not hs: continue
        base = [int(x) for x in o['base']]; L = live[t]
        rows = {}
        for h in hs:
            w = [int(x) for x in h['w']]
            dpm = w[3] - base[3]; da = w[4] - base[4]
            usd = (dpm + da) / 10 ** L['dec'] * L['price']
            k = (h['fn'].split('~')[0], h['cat'])
            if k not in rows or abs(usd) > abs(rows[k][0]): rows[k] = (usd, dpm, da, w[5], base[5], h['data'][:8 + 128])
        if max(abs(v[0]) for v in rows.values()) < minusd and not any(k[1] != 'free-raise' for k in rows): continue
        print('%d %s %-12s usd %.2f bal %s' % (cid, t, (o['sym'] or '')[:12], o['usd'], L['bal']))
        for k, v in sorted(rows.items(), key=lambda x: -abs(x[1][0]))[:5]:
            print('     %-12s %-50s created %.6f USD  dPM %d dA %d full %d/%d %s' % (k[1], k[0][:50], v[0], v[1], v[2], v[3], v[4], v[5][:8 + 64]))
if __name__ == '__main__':
    mu = 0.01
    for c in sys.argv[1:]:
        if c.startswith('minusd='): mu = float(c[7:]); continue
        show(int(c), minusd=mu)
