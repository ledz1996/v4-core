import sys, json, gzip, os, collections
from value import values
from common import RAW
def rel(h):
    w = [int(z) for z in h['w']]; b = [int(z) for z in h['base']]; amt = int(h['amt'])
    dPM = w[3] - b[3]; dA = w[4] - b[4]
    if b[1] == 0: return None, dPM, dA, w, b          # token would not even move to A
    if dPM > 0 and w[5] == 0 and b[5] == 1: return 'locked-assign', dPM, dA, w, b
    if dPM == 0 and w[5] == 0 and b[5] == 1: return 'lock-only', dPM, dA, w, b
    if dPM > 0 and dPM + dA > 0: return 'free-raise', dPM, dA, w, b
    if dPM < 0: return 'lowered', dPM, dA, w, b
    if dA > 0: return 'A-gain', dPM, dA, w, b
    return None, dPM, dA, w, b
def rows(cid):
    fn = os.path.join(RAW, 'assign_%d.json.gz' % cid)
    if not os.path.exists(fn): return []
    x = json.load(gzip.open(fn)); fam = json.load(gzip.open(os.path.join(RAW, 'families_%d.json.gz' % cid))) if cid != 4663 else {}
    v = values(cid); out = []
    for h in x['hits']:
        if h['cat'] == 'callfail': continue
        c, dPM, dA, w, b = rel(h)
        if not c: continue
        f = fam.get(h['fam'], {'tokens': 0, 'usd': 0}); u = v.get(h['token']) or {}
        out.append(dict(cid=cid, cat=c, usd=u.get('usd') or 0, token=h['token'], sym=u.get('sym'), famTokens=f['tokens'], famUsd=f['usd'], fn=h['fn'], dPM=dPM, dA=dA, amt=int(h['amt']), full=w[5], part=w[6], data=h['data']))
    return out
def show(cid, cats=None, maxn=400, skipfn=()):
    seen = set(); n = 0
    for r in sorted(rows(cid), key=lambda r: (r['cat'], -r['usd'], r['token'], r['fn'])):
        if cats and r['cat'] not in cats: continue
        if r['fn'].split('(')[0] in skipfn: continue
        k = (r['cat'], r['token'], r['fn'])
        if k in seen: continue
        seen.add(k); n += 1
        if n > maxn: break
        print(cid, r['cat'], '$%.0f' % r['usd'], r['token'], r['sym'], 'fam=%d/$%d' % (r['famTokens'], r['famUsd']), r['fn'], 'dPM=%+.4g dA=%+.4g amt=%.4g full=%d part=%d' % (r['dPM'], r['dA'], r['amt'], r['full'], r['part']))
if __name__ == '__main__':
    show(int(sys.argv[1]), sys.argv[2].split(',') if len(sys.argv) > 2 else None)
