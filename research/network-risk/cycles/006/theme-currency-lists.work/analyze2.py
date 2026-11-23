# Part two summary for one network: joins the sweeps with prices and prints what needs reading. usage: python3 analyze2.py <chainId>
import sys, json, gzip, os, collections
from value import values
import show
cid = int(sys.argv[1]); R = 'raw/'
v = values(cid)
xf = json.load(gzip.open(R + 'xfer_%d.json.gz' % cid)); th = json.load(gzip.open(R + 'third_%d.json.gz' % cid))
odd = xf['odd']; cats = collections.Counter(); rej = []; partial = []
for t, w in odd.items():
    if w[0] == 'callfail': cats['callfail'] += 1; continue
    b0, fl, b1, bs = w
    if b0 == 0: cats['zero'] += 1; continue
    if not fl & 1: cats['balanceOf-failed'] += 1
    elif not fl & 2: cats['full-rejected'] += 1; rej.append(t)
    elif b1 != 0 and bs == b0 - b1: cats['kept-part'] += 1; partial.append(t)
    elif b1 != 0: cats['kept-part+fee'] += 1; partial.append(t)
    elif bs < b0: cats['recipient-got-less'] += 1
    elif bs > b0: cats['recipient-got-more'] += 1
    else: cats['other'] += 1
print(cid, 'xfer tested', xf['tested'], 'odd', len(odd), dict(cats))
def usd(t): return (v.get(t) or {}).get('usd') or 0
def sym(t): return (v.get(t) or {}).get('sym')
print(' priced tokens in universe', len(v), 'total usd', round(sum(x['usd'] for x in v.values() if x['usd'] < 5e9)))
print(' full transfer rejected, priced:')
for t in sorted(rej, key=usd, reverse=True)[:25]:
    if usd(t) > 0: print('   ', t, sym(t), '$%.0f' % usd(t), odd[t])
print(' balance left after full transfer, priced:')
for t in sorted(partial, key=usd, reverse=True)[:25]:
    if usd(t) > 0: print('   ', t, sym(t), '$%.0f' % usd(t), odd[t])
up = {t: x for t, x in th['odd'].items() if int(x[2]) > 0}; dn = {t: x for t, x in th['odd'].items() if int(x[2]) < 0}
print(' third: tested', th['tested'], 'senderKeepsMore', len(up), 'senderLosesMore', len(dn))
for nm, dd in (('keepsMore', up), ('losesMore', dn)):
    for t in sorted(dd, key=usd, reverse=True)[:15]:
        if usd(t) > 0 or nm == 'losesMore': print('   ', nm, t, sym(t), '$%.0f' % usd(t), dd[t])
rows = show.rows(cid); c = collections.Counter((r['cat'], r['usd'] > 0) for r in rows); print(' assign rows', dict(c))
seen = set()
for r in sorted(rows, key=lambda r: -r['usd']):
    k = (r['cat'], r['token'], r['fn'])
    if k in seen or r['usd'] <= 0: continue
    seen.add(k); print('   ', r['cat'], '$%.0f' % r['usd'], r['token'], r['sym'], r['fn'], 'dPM=%+.4g dA=%+.4g amt=%.4g full=%d part=%d' % (r['dPM'], r['dA'], r['amt'], r['full'], r['part']))
json.dump(dict(rej=rej, partial=partial, up=list(up), dn=list(dn), assign=sorted({r['token'] for r in rows})), open(R + 'flaggedtokens_%d.json' % cid, 'w'))
