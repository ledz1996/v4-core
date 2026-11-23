# Rerun batches that failed for lack of gas with eight trials per call and merge the result into the main sweep file.
import sys, json, gzip, os
from base import *
import sweep
def fix(cid, mode):
    fn = os.path.join(RAW6, 'sweep%s_%d.json.gz' % ('' if mode == 'A' else mode, cid))
    if not os.path.exists(fn): return
    d = jz(fn); bad = {t for t, o in d['tokens'].items() if o['fail']}
    if not bad: return
    sweep.run(cid, per=8, only=bad, mode=mode)
    pf = os.path.join(RAW6, 'sweep%s_%d_part.json.gz' % ('' if mode == 'A' else mode, cid)); p = jz(pf)
    for t, o in p['tokens'].items():
        o['rerun'] = 'per=8'; d['tokens'][t] = o
    json.dump(d, gzip.open(fn, 'wt')); os.remove(pf)
    print(cid, mode, 'rerun', len(bad), 'still failing', {t: o['fail'] for t, o in p['tokens'].items() if o['fail']}, flush=True)
for c in sys.argv[1:]:
    for m in 'ABC': fix(int(c), m)
