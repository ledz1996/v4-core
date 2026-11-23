# Summarise the sample digests of one network: which (caller, id) pairs hold unexplained or native-only claim mints.
import sys, json, gzip, collections
from stats import load
def run(cid, show=40):
    S = json.load(gzip.open('raw/sample_%d.json.gz' % cid, 'rt'))
    tot = collections.defaultdict(lambda: [0, 0, 0, 0, set()])  # (caller,id) -> n, sum, firstBlock, lastBlock, recipients
    txpair = collections.defaultdict(set)
    for b, tx, li, caller, to, i, amt in load(cid):
        t = tot[(caller, i[-40:])]; t[0] += 1; t[1] += int(amt); t[2] = b if not t[2] else min(t[2], b); t[3] = max(t[3], b); t[4].add(to)
        txpair[tx].add((caller, i[-40:]))
    res = collections.defaultdict(lambda: collections.Counter()); ex = {}
    for d in S['digests']:
        if 'err' in d: continue
        for i, v in d['ids'].items():
            for (c, ii) in txpair.get(d['tx'], ()):
                if ii == i:
                    res[(c, i)][v['cls']] += 1
                    if v['cls'] in ('unexplained', 'native'): ex.setdefault((c, i), []).append((d['tx'], d['from'], d['to'], v))
    rows = []
    for k, c in res.items():
        if c['unexplained'] or c['native']:
            t = tot[k]; rows.append((k, dict(c), t[0], t[1], t[2], t[3], len(t[4]), ex[k][0]))
    rows.sort(key=lambda r: -r[2])
    print(cid, 'pairs sampled', len(res), 'pairs with unexplained or native-only sample', len(rows))
    for r in rows[:show]:
        print(' caller', r[0][0], 'id', r[0][1], r[1], 'mints', r[2], 'sum', r[3], 'blocks', r[4], r[5], 'recips', r[6]); print('     e.g.', r[7][0], 'from', r[7][1], 'to', r[7][2], r[7][3])
    return rows
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))

def by_id(cid, show=40):
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()): rows = run(cid, 0)
    agg = collections.defaultdict(lambda: {'callers': 0, 'mints': 0, 'sum': 0, 'first': None, 'last': 0, 'cls': collections.Counter(), 'eg': None, 'topCaller': (0, None)})
    for k, c, n, s, b0, b1, nr, eg in rows:
        a = agg[k[1]]; a['callers'] += 1; a['mints'] += n; a['sum'] += s; a['first'] = b0 if a['first'] is None else min(a['first'], b0); a['last'] = max(a['last'], b1)
        a['cls'].update(c); a['eg'] = a['eg'] or eg[0]
        if n > a['topCaller'][0]: a['topCaller'] = (n, k[0])
    out = sorted(agg.items(), key=lambda kv: -kv[1]['mints'])
    print(cid, 'ids with unexplained or native-only samples:', len(out))
    for i, a in out[:show]:
        print('  id', i, 'callers', a['callers'], 'mints(all of those pairs)', a['mints'], 'sum', a['sum'], 'blocks', a['first'], a['last'], dict(a['cls']), 'top', a['topCaller'], 'eg', a['eg'])
    return out
