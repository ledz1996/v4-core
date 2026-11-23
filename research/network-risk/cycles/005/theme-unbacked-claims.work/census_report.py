import json, gzip, glob, collections, sys
def u_by_token(cid):
    d = json.load(gzip.open('raw/census_%d.json.gz' % cid, 'rt')); c = collections.defaultdict(list)
    for u in d['unexplained']: c[u['token']].append(u)
    return d, c
if __name__ == '__main__':
    for f in sorted(glob.glob('raw/census_*.json.gz')):
        cid = int(f.split('_')[1].split('.')[0])
        if len(sys.argv) > 1 and str(cid) not in sys.argv[1:]: continue
        d, c = u_by_token(cid)
        print(cid, d['name'], 'blocks', d['B1'], d['B2'], 'days', d['days'], 'txs', d['txs'], 'noPool', d['txsNoPool'], 'U rows', len(d['unexplained']), 'U tokens', len(c), 'fail', sum(v['nFail'] for v in d['stats'].values()))
        for t, v in sorted(c.items(), key=lambda kv: -len(kv[1]))[:12]:
            e = v[-1]; print('    ', t, 'n', len(v), 'eg', e['tx'], 'out', e['out'], 'in', e['in'], 'mint', e['mint'], 'burn', e['burn'])
