import json, gzip, os
from common import universe, RAW
def values(cid):
    fn = os.path.join(RAW, 'prices_%d.json.gz' % cid)
    if not os.path.exists(fn): return {}
    pr = json.load(gzip.open(fn))
    d, rows = universe(cid)
    out = {}
    for r in rows:
        t = r['token']; b = int(r.get('bal2') or 0)
        p = pr.get(t)
        if b and p and p.get('price') is not None and p.get('decimals') is not None:
            v = b / 10 ** p['decimals'] * p['price']
            out[t] = dict(sym=p.get('symbol'), usd=v, amt=b / 10 ** p['decimals'], conf=p.get('confidence'))
    return out
