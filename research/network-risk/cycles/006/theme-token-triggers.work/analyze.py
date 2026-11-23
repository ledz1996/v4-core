# List the trial results that are not plain transfers, and the changes that the time shift alone causes.
import sys, json, gzip, os, glob, collections
from base import *
TRIV = ('transfer(address,uint256)',)
SHOWTIME = False   # the sweep reads 'latest' per call, so base rows differ by live activity; timeonly.py pins the block
def load(cid, mode):
    fn = os.path.join(RAW6, 'sweep%s_%d.json.gz' % ('' if mode == 'A' else mode, cid))
    return jz(fn) if os.path.exists(fn) else None
def report(cid, verbose=True):
    rows = []
    for mode in 'ABC':
        d = load(cid, mode)
        if not d: continue
        for t, o in d['tokens'].items():
            b = o['base']
            if '0' in b:
                for dt, w in b.items():
                    if dt == '0': continue
                    if SHOWTIME and (w[0] != b['0'][0] or w[1] != b['0'][1] or w[5] != b['0'][5] or w[3] != b['0'][3]):
                        rows.append((cid, mode, t, o['sym'], o['usd'], int(dt), 'TIME-ONLY', '', 'b0 %s->%s toA %s->%s full %s->%s b1 %s->%s' % (b['0'][0], w[0], b['0'][1], w[1], b['0'][5], w[5], b['0'][3], w[3]), ''))
            seen = set()
            for h in o['hits']:
                nm = h['fn']
                if h['cat'] == 'raise-paid': continue   # A lost what the PoolManager gained and the full balance still leaves: a transfer
                if h['cat'] == 'free-raise' and abs((int(h['w'][3]) - int(h['base'][3])) + (int(h['w'][4]) - int(h['base'][4]))) <= 2: continue   # share rounding of one or two base units
                k = (nm, h['cat'], h['dt'], h['target'])
                if k in seen: continue
                seen.add(k)
                w = [int(x) for x in h['w']]; bs = [int(x) for x in h['base']]
                rows.append((cid, mode, t, o['sym'], o['usd'], h['dt'], h['cat'], nm, 'dPM %d dA %d full %d->%d (b0 %d amt %s)' % (w[3] - bs[3], w[4] - bs[4], bs[5], w[5], bs[0], h['amt']), h['target'] if h['target'] != t else ''))
    return rows
if __name__ == '__main__':
    cids = [int(c) for c in sys.argv[1:]] or [n['chainId'] for n in NETS]
    for cid in cids:
        rows = report(cid)
        # collapse over dt
        agg = collections.OrderedDict()
        for r in rows:
            k = (r[1], r[2], r[6], r[7], r[9])
            agg.setdefault(k, dict(r=r, dts=[]))['dts'].append(r[5])
        print('==', cid, net(cid)['name'], 'rows', len(agg))
        for k, v in agg.items():
            r = v['r']
            print(' ', r[1], r[2], str(r[3])[:10], '$%d' % min(r[4], 9e15), r[6], r[7][:70], '| dts', sorted(set(v['dts'])), '|', r[8][:160], ('via ' + r[9]) if r[9] else '')
