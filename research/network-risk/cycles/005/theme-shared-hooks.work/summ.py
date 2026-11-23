import json, gzip, glob, collections, sys
from lib import *
FL = ['beforeInitialize','afterInitialize','beforeAddLiquidity','afterAddLiquidity','beforeRemoveLiquidity','afterRemoveLiquidity','beforeSwap','afterSwap','beforeDonate','afterDonate','beforeSwapReturnDelta','afterSwapReturnDelta','afterAddLiquidityReturnDelta','afterRemoveLiquidityReturnDelta']
SH = ['bI','aI','bAL','aAL','bRL','aRL','bS','aS','bD','aD','bSΔ','aSΔ','aALΔ','aRLΔ']
def flags(h, short=True):
    v = int(h, 16) & 0x3fff
    return [ (SH if short else FL)[i] for i in range(14) if v & (1 << (13 - i))]
def _files(cid, pre):
    return sorted(f for f in glob.glob('raw/%s_%d*.json.gz' % (pre, cid)) if f.split(pre + '_')[1].split('.')[0].split('_')[0] == str(cid))
_cache = {}
def census(cid):
    """returns (counts per hook, dynamic fee counts per hook, sample or full rows, total pools, coverage notes)"""
    if cid in _cache: return _cache[cid]
    rows = []; cnt = collections.Counter(); dyn = collections.Counter(); total = 0; cov = []
    ag = _files(cid, 'agg')
    if ag:
        for f in ag:
            j = json.load(gzip.open(f)); K = j.get('sampleEvery', 1); rows += [tuple(r) for r in j['rows']]; cnt.update({h: c * K for h, c in j['counts'].items()}); dyn.update({h: c * K for h, c in j['dyn'].items()}); total += j['total'] * K; cov.append((j['lo'], j['hi'], j['nFail']) + (('one window of 1000 blocks in every %d read, counts multiplied by %d' % (K, K),) if K > 1 else ()))
    else:
        for f in _files(cid, 'init'):
            j = json.load(gzip.open(f)); rows += [tuple(r) for r in j['rows']]; cov.append((j['lo'], j['hi'], j['nFail']))
        import os
        if os.path.exists('raw/init_%d_back.jsonl' % cid):
            b = [tuple(json.loads(l)) for l in open('raw/init_%d_back.jsonl' % cid)]
            rows += b
            if b: cov.append((min(r[0] for r in b), max(r[0] for r in b), 'backward walk, partial'))
        seen = set(); out = []
        for r in sorted(rows):
            if r[1] in seen: continue
            seen.add(r[1]); out.append(r)
        rows = out; total = len(rows)
        for r in rows:
            cnt[r[6]] += 1
            if r[4] == 0x800000: dyn[r[6]] += 1
    rows.sort()
    _cache[cid] = (cnt, dyn, rows, total, cov)
    return _cache[cid]
def load(cid): return census(cid)[2]
if __name__ == '__main__':
    N = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    for n in NETS:
        cid = n['chainId']
        if len(sys.argv) > 1 and sys.argv[1] != 'all' and int(sys.argv[1]) != cid: continue
        cnt, dyn, rows, total, cov = census(cid)
        if not total: print(cid, n['name'], 'no data'); continue
        z = '0x' + '0' * 40
        print('%d %s pools %d hooks %d hookless %d coverage %s' % (cid, n['name'], total, len(cnt) - (1 if z in cnt else 0), cnt.get(z, 0), cov))
        for h, c in [x for x in cnt.most_common(N + 1) if x[0] != z][:N]:
            print('   %s %7d  %s' % (h, c, ','.join(flags(h))))
