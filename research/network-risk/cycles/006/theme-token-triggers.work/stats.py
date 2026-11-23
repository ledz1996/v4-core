# Figures for the write-up: targets, trials, accepted calls, selectors without a known name, related contracts, per network.
import json, gzip, os, collections
from base import *
import sweep
out = {}
for n in NETS:
    cid = n['chainId']; fn = os.path.join(RAW6, 'discover_%d.json.gz' % cid)
    if not os.path.exists(fn): out[cid] = dict(name=n['name'], targets=0); continue
    d = jz(fn); o = dict(name=n['name'], targets=len(d), over10k=sum(1 for x in d.values() if x['usd'] > 1e4), usd=sum(x['usd'] for x in d.values() if x['usd'] < 5e8),
                         top=[(x['sym'], int(x['usd'])) for x in sorted(d.values(), key=lambda x: -x['usd']) if x['usd'] < 5e8][:5],
                         odd=[(x['sym'], t) for t, x in d.items() if x['usd'] >= 5e8],
                         related=sum(len(x.get('rel') or {}) for x in d.values()), tokensWithRelated=sum(1 for x in d.values() if x.get('rel')), aclMissing=sum(1 for x in d.values() if not x.get('acl')))
    sels = set(); un = set()
    for x in d.values():
        ss = set(x.get('sels') or [])
        for r in (x.get('rel') or {}).values(): ss.update(r['sels'])
        ss -= sweep.JUNK
        sels |= ss; un |= {s for s in ss if not sweep.SIG.get(s)}
    o['selectors'] = len(sels); o['unnamed'] = len(un)
    for md, f in (('A', 'sweep_%d.json.gz'), ('B', 'sweepB_%d.json.gz')):
        f = os.path.join(RAW6, f % cid)
        if os.path.exists(f):
            s = jz(f); tk = s['tokens']
            o['sweep' + md] = dict(tokens=len(tk), trials=sum(x['trials'] for x in tk.values()), accepted=sum(x['ok'] for x in tk.values()), failedCalls=sum(x['fail'] for x in tk.values()), dts=s['dts'],
                                   cats=dict(collections.Counter(h['cat'] for x in tk.values() for h in x['hits'])))
    f = os.path.join(RAW6, 'timeonly_%d.json.gz' % cid)
    if os.path.exists(f):
        t = jz(f); o['timeonly'] = dict(tokens=len(t), errors=sum(1 for r in t.values() if 'err' in r), blocks=sorted({r['block'] for r in t.values() if 'block' in r})[:1] + sorted({r['block'] for r in t.values() if 'block' in r})[-1:])
    out[cid] = o
json.dump(out, open(os.path.join(RAW6, 'stats.json'), 'w'), indent=1)
tot = collections.Counter()
for cid, o in out.items():
    a = o.get('sweepA') or {}; b = o.get('sweepB') or {}
    print(cid, o['name'], 'targets', o['targets'], '>10k', o.get('over10k'), 'usd %d' % (o.get('usd') or 0), 'sel', o.get('selectors'), 'unnamed', o.get('unnamed'), 'rel', o.get('related'), '| A', a.get('tokens'), a.get('trials'), a.get('accepted'), a.get('failedCalls'), a.get('dts'),
          '| B', b.get('tokens'), b.get('trials'), b.get('accepted'), b.get('failedCalls'), '| T', o.get('timeonly'), o.get('odd'))
    for k in ('targets', 'over10k', 'related'): tot[k] += o.get(k) or 0
    tot['trialsA'] += a.get('trials') or 0; tot['trialsB'] += b.get('trials') or 0; tot['accA'] += a.get('accepted') or 0; tot['accB'] += b.get('accepted') or 0; tot['tokB'] += b.get('tokens') or 0; tot['unnamed'] += o.get('unnamed') or 0
print(dict(tot))
