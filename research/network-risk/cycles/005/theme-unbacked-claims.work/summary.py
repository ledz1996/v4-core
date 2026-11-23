# Collect the per-network results of this unit into raw/summary.json and print one line per network.
import json, gzip, glob, os, collections
from lib import NETS
S = {}
for n in NETS:
    cid = n['chainId']; r = {'name': n['name']}
    for f in glob.glob('raw/mints_%d_*.meta.json' % cid):
        m = json.load(open(f)); r['mints'] = dict(url=m['url'], fromBlock=m['fromBlock'], toBlock=m['toBlock'], mints=m['mints'], requests=m['requests'], nFailed=m['nFailed'])
    f = 'raw/sample_%d.json.gz' % cid
    if os.path.exists(f):
        try:
            s = json.load(gzip.open(f, 'rt')); c = collections.Counter(); un = collections.Counter()
            for d in s['digests']:
                if 'err' in d: c['err'] += 1; continue
                for i, v in d['ids'].items():
                    c[v['cls']] += 1
                    if v['cls'] == 'unexplained': un[i] += 1
            r['sample'] = dict(pairs=s['pairs'], perPair=s['perPair'], small=s.get('small'), txs=len(s['digests']), classes=dict(c), unexplainedIds=dict(un))
        except Exception as e: r['sample'] = {'err': str(e)[:80]}
    f = 'raw/native_%d.json' % cid
    if os.path.exists(f): x = json.load(open(f)); r['native'] = dict(sampled=x['nativeOnlySampled'], counts=x['counts'])
    f = 'raw/census_%d.json.gz' % cid
    if os.path.exists(f):
        x = json.load(gzip.open(f, 'rt')); F = x['roundTrips']
        r['census'] = dict(B1=x['B1'], B2=x['B2'], days=x['days'], txs=x['txs'], txsNoPool=x['txsNoPool'], U=len(x['unexplained']), Utokens=len(set(u['token'] for u in x['unexplained'])), wrapDeposits=x['stats']['dep']['logs'],
                           roundTripTokens=len(F), roundTrips=sum(v['n'] for v in F.values()), roundTripsNoPool=sum(v['n0'] for v in F.values()), exactNoPool=sum(v['nx0'] for v in F.values()), fails=sum(v['nFail'] for v in x['stats'].values()))
    f = 'raw/burns_%d.json.gz' % cid
    if os.path.exists(f):
        x = json.load(gzip.open(f, 'rt')); r['burns'] = dict(fromBlock=x['fromBlock'], toBlock=x['toBlock'], rows=len(x['rows']), tokens=len(set(q[2] for q in x['rows'])), nFail=x['nFail'])
        g = 'raw/burns_%d_classified.json' % cid
        if os.path.exists(g): y = json.load(open(g)); r['burns']['flagged'] = len(y['flagged'])
        g = 'raw/burns_%d_validated.json' % cid
        if os.path.exists(g):
            y = json.load(open(g)); r['burns']['validated'] = len(y['rows']); r['burns']['real'] = sum(1 for q in y['rows'] if q.get('real')); r['burns']['spoof'] = sum(1 for q in y['rows'] if q.get('real') is False)
            r['burns']['realTokens'] = [dict(token=q['token'], symbol=q.get('symbol'), noPM=q['noPM'], sum=q['sumNoPM'], balBefore=q.get('balBefore'), balAfter=q.get('balAfter'), balNow=q.get('balNow'), pools=q.get('pools'), selector=q.get('selector'), egTx=q['egTx']) for q in y['rows'] if q.get('real')]
    S[cid] = r
json.dump(S, open('raw/summary.json', 'w'), indent=0)
for cid, r in S.items():
    m = r.get('mints', {}); s = r.get('sample', {}); c = r.get('census', {}); b = r.get('burns', {})
    print(cid, r['name'], '| mints', m.get('mints'), 'blocks', m.get('fromBlock'), m.get('toBlock'), '| sample txs', s.get('txs'), s.get('classes'), 'unexpl ids', len(s.get('unexplainedIds', {})), '| native', r.get('native', {}).get('counts'), '| census days', c.get('days'), 'U', c.get('U'), 'F0', c.get('roundTripsNoPool'), 'dep', c.get('wrapDeposits'), '| burns rows', b.get('rows'), 'flag', b.get('flagged'), 'real', b.get('real'))
