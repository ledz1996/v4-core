# Trials refused at one divisor are repeated with a larger divisor (a smaller amount), to get past transaction size limits.
import sys, os, collections
from base import *
import surcharge
def run(cid, d0=3, d1=1000, tag0='', tag1='r'):
    d = jz(os.path.join(RAW7, 'surch%s_%d_div%d.json.gz' % (tag0, cid, d0)))
    items = []
    for r in d['rows']:
        w = r['w']
        if w is None or (int(w[0]) > 0 and int(w[3]) == 0) or (int(w[0]) == 0): items.append((r['t'], r['a'], r['kind']))
    if not items: print(cid, 'nothing to retry'); return
    surcharge.run(cid, div=d1, only=items, tag=tag1)
if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('d')]
    d0 = 3; d1 = 1000; t0 = ''; t1 = 'r'
    for x in sys.argv[1:]:
        if x.startswith('d0='): d0 = int(x[3:]); t0 = 'r'
        if x.startswith('d1='): d1 = int(x[3:])
    for c in a: run(int(c), d0, d1, t0, t1)
