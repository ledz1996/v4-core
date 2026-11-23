# Lighter sampler for the two networks with more than 40,000 (caller, id) pairs (Base, Robinhood Chain), where the
# public endpoints cannot serve the dense rule in reasonable time. It takes the TOP largest pairs (first, last and one
# random mint each) and RAND further pairs chosen at random (one random mint each). Output has the same format as
# sample_receipts.py, so report.py, native_check.py and summary.py read it.
# usage: python3 quick_sample.py <chainId> <TOP> <RAND> [workers]
import sys, json, gzip, random, collections
from stats import load
import sample_receipts as sr
def main():
    cid = int(sys.argv[1]); TOP = int(sys.argv[2]); RAND = int(sys.argv[3]); workers = int(sys.argv[4]) if len(sys.argv) > 4 else 5
    random.seed(7); P = {}; n = 0
    for b, tx, li, caller, to, i, amt in load(cid):
        k = (caller, i[-40:]); v = P.get(k); n += 1
        if v is None: P[k] = [1, tx, tx, tx]
        else:
            v[0] += 1; v[2] = tx
            if random.randrange(v[0]) == 0: v[3] = tx
    ks = sorted(P, key=lambda k: -P[k][0]); top = ks[:TOP]; rest = ks[TOP:]; rnd = random.sample(rest, min(RAND, len(rest)))
    want = {}
    for k in top:
        for t in P[k][1:]: want[t] = 1
    for k in rnd: want[P[k][3]] = 1
    covered = sum(P[k][0] for k in top) + sum(P[k][0] for k in rnd)
    print(cid, 'mints', n, 'pairs', len(P), 'top pairs', len(top), 'random pairs', len(rnd), 'mints in sampled pairs', covered, 'txs', len(want), flush=True)
    raw = {}; out = sr.fetch_receipts(cid, list(want), workers=workers, keep_raw=raw)
    for d in out.values(): d['v2'] = 1
    json.dump({'chainId': cid, 'perPair': 'quick top %d x3 + random %d x1' % (TOP, RAND), 'small': None, 'pairs': len(P), 'pairsSampled': len(top) + len(rnd), 'mintsInSampledPairs': covered, 'mints': n, 'digests': list(out.values())}, gzip.open('raw/sample_%d.json.gz' % cid, 'wt'))
    json.dump(raw, gzip.open('raw/sample_%d_unexplained_receipts.json.gz' % cid, 'wt'))
    c = collections.Counter()
    for d in out.values():
        if 'err' in d: c['err'] += 1; continue
        for v in d['ids'].values(): c[v['cls']] += 1
    print(cid, dict(c), flush=True)
main()
