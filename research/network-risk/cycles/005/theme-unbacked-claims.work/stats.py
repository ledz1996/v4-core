# Group the claim mints of one network by caller, by id and by (caller, id).
import sys, json, gzip, glob, collections
def load(cid):
    for fn in sorted(glob.glob('raw/mints_%d_*.jsonl.gz' % cid)):
        with gzip.open(fn, 'rt') as f:
            for line in f:
                try: yield json.loads(line)
                except Exception: pass
if __name__ == '__main__':
    for cid in [int(x) for x in sys.argv[1:]]:
        callers = collections.Counter(); ids = collections.Counter(); pairs = collections.Counter(); txs = set(); n = 0; tos = collections.Counter()
        for b, tx, li, caller, to, i, amt in load(cid):
            n += 1; callers[caller] += 1; ids[i] += 1; pairs[(caller, i)] += 1; txs.add(tx); tos[to] += 1
        print(cid, 'mints', n, 'txs', len(txs), 'callers', len(callers), 'ids', len(ids), 'pairs', len(pairs), 'recipients', len(tos))
        print('  top callers', [(c[:10], k) for c, k in callers.most_common(8)])
        print('  top ids', [(c[-40:][:8], k) for c, k in ids.most_common(8)])
        print('  pairs with 1 mint', sum(1 for v in pairs.values() if v == 1), 'callers with <=3 mints', sum(1 for v in callers.values() if v <= 3))
