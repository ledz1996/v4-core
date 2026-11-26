"""Union of native coverage files (cov.hpp dump). Leaders are keyed by (IR block index, ordinal inside the block),
so files from compiles at different addresses (and of the two PoolManager byte strings) can be joined.
Usage: covsum.py out.json file.cov [file.cov ...]"""
import sys, json, collections
def load(p):
    B = []; L = []
    for line in open(p):
        t = line.split()
        if t[0] == 'B': B.append((int(t[2]), int(t[3], 16), int(t[4])))
        elif t[0] == 'L': L.append((int(t[1], 16), int(t[2]), int(t[3]), int(t[4])))
    per = collections.defaultdict(list)
    for a, eb, st, hit in L: per[eb].append((a, hit))
    keyed = {}
    for eb, xs in per.items():
        for k, (a, hit) in enumerate(sorted(xs)): keyed[(eb, k)] = hit
    return B, keyed
def main():
    out = sys.argv[1]; files = sys.argv[2:]
    B0 = None; hits = None; shape = None
    for p in files:
        B, K = load(p)
        sh = (tuple(o for o, _, _ in B), tuple(sorted(K)))
        if shape is None: shape, B0, hits = sh, B, dict(K)
        elif sh != shape: print('shape differs', p); B0b = B
        if sh == shape:
            for k, v in K.items(): hits[k] |= v
        else:
            for k, v in K.items():
                if k in hits: hits[k] |= v
    blocks_hit = collections.defaultdict(int); blocks_leaders = collections.defaultdict(int)
    for (eb, k), v in hits.items(): blocks_leaders[eb] += 1; blocks_hit[eb] += v
    ir = [{'index': i, 'evmOffset': o, 'enterable': en, 'leaders': blocks_leaders.get(i, 0), 'leadersHit': blocks_hit.get(i, 0),
           'entered': bool(hits.get((i, 0), 0)) if any(kk[0] == i for kk in hits) else None} for i, (o, a, en) in enumerate(B0)]
    res = {'files': files, 'irBlocks': len(B0), 'irBlocksEntered': sum(1 for b in ir if b['entered']),
           'nativeLeaders': len(hits), 'nativeLeadersHit': sum(hits.values()), 'blocks': ir,
           'prologueLeaders': blocks_leaders.get(-1, 0), 'prologueHit': blocks_hit.get(-1, 0)}
    json.dump(res, open(out, 'w'), indent=0)
    print({k: v for k, v in res.items() if k not in ('blocks', 'files')})
main()
