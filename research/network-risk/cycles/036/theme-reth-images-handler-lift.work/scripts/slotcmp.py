"""Compare all 256 handler slots of the main instruction table of two binaries that embed the same revm-interpreter
version (35.0.1), by normalised text of the slot's function (cmp_reth.py normalisation). Lists the opcodes whose
handler text differs, i.e. handlers a wrapper replaced or that were compiled differently. Read only.
usage: python3 -I slotcmp.py <nameA> <nameB> <out.json>"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cmp_reth as C
W = '/home/user/v4-core/research/network-risk/cycles/036/theme-reth-images-handler-lift.work/'
bins = dict(l.split() for l in open(W + 'build/bins.txt'))
def ld(n):
    c = json.load(open(W + 'build/%s.cfg.json' % n))
    d = C.load(dict(bin=bins[n], rel=W + 'build/%s.rel' % n, fde=W + 'build/%s.fde' % n))
    return d, int(c['table'], 16), int(c['stride'])
a, b, out = sys.argv[1:4]
(da, ta, sa), (db, tb, sb) = ld(a), ld(b)
res = {'A': a, 'B': b, 'tableA': hex(ta), 'tableB': hex(tb), 'differ': [], 'same': 0}
for op in range(256):
    xa, xb = da['relm'][ta + sa * op], db['relm'][tb + sb * op]
    try:
        na, nb = C.norm(da, *C.fn_range(da, xa)), C.norm(db, *C.fn_range(db, xb))
    except AssertionError:
        res['differ'].append({'op': hex(op), 'note': 'no fde'}); continue
    if na == nb: res['same'] += 1
    else: res['differ'].append({'op': hex(op), 'a': hex(xa), 'b': hex(xb), 'lenA': len(na), 'lenB': len(nb)})
json.dump(res, open(out, 'w'), indent=1)
print(a, b, 'same', res['same'], 'differ', [(d['op'], d.get('lenA'), d.get('lenB')) for d in res['differ']])
