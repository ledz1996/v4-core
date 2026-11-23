import json, gzip, os, re, collections
from names import *
from value import values
from common import universe
_c = {}
def tok_names(cid):
    """token -> list of (selector, name) from own code and resolved implementation code"""
    if cid in _c: return _c[cid]
    ch, se = load(cid)
    px = {}
    fn = os.path.join(RAW, 'proxies_%d.json.gz' % cid)
    if os.path.exists(fn): px = json.load(gzip.open(fn))
    out = {}
    for t, h in ch.items():
        p = se.get(h)
        if not p: continue
        sels = set(p['sels'])
        for k, a in (px.get('impl', {}).get(t) or []):
            a2 = px['beacon'].get(a, a) if k == 'beacon' else a
            c = px['code'].get(a2)
            if c: sels.update(c['sels'])
        out[t] = sels
    _c[cid] = out
    return out
def find(cid, rx, minusd=0):
    tn = tok_names(cid); v = values(cid); res = []
    d, rows = universe(cid); bal = {r['token']: int(r.get('bal2') or 0) for r in rows}
    for t, sels in tn.items():
        hits = sorted({nm for s in sels for nm in (SIG.get(s) or []) if rx.search(nm)})
        if hits:
            x = v.get(t) or {}
            if (x.get('usd') or 0) >= minusd: res.append((x.get('usd') or 0, t, x.get('sym'), bal.get(t), hits))
    return sorted(res, reverse=True)
