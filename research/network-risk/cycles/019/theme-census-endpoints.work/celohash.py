"""Celo: do the backends behind forno (and other public endpoints) report the same block hash for the same height?
forno answers from more than one client build. Each HTTP request is a JSON-RPC batch of web3_clientVersion and
eth_getBlockByNumber(h, false), so the build that answered is named in the same response. For each of 200 heights
(seed '42220-hashes': 100 uniform from the L2 migration block 31,056,500 to head, 60 among the last 5,000 blocks,
block 75,046,581 and its neighbours, and the rest uniform), requests are repeated until each build seen has answered
or 30 tries are spent. Records hash, stateRoot, receiptsRoot, extraData, and the client build. Read only.
Usage: celohash.py <out.json>"""
import sys, json, time, random, ssl, urllib.request, collections
C = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
OUT = sys.argv[1]
EPS = ['https://forno.celo.org', 'https://celo-json-rpc.stakely.io', 'https://rpc.ankr.com/celo', 'https://celo-rpc.publicnode.com', 'https://celo.api.pocket.network']
def batch(u, h):
    body = json.dumps([{'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []},
                       {'jsonrpc': '2.0', 'id': 2, 'method': 'eth_getBlockByNumber', 'params': [hex(h), False]}]).encode()
    r = json.loads(urllib.request.urlopen(urllib.request.Request(u, body, {'content-type': 'application/json', 'user-agent': 'rpc-client'}), timeout=60, context=C).read())
    if isinstance(r, dict): raise RuntimeError(str(r)[:200])
    d = {x['id']: x for x in r}
    cv = d[1].get('result'); b = d[2].get('result')
    if b is None: return cv, None
    return cv, {k: b.get(k) for k in ('hash', 'stateRoot', 'receiptsRoot', 'transactionsRoot', 'extraData', 'parentHash', 'gasUsed')}
def head():
    r = json.loads(urllib.request.urlopen(urllib.request.Request(EPS[0], json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_blockNumber', 'params': []}).encode(), {'content-type': 'application/json', 'user-agent': 'rpc-client'}), timeout=60, context=C).read())
    return int(r['result'], 16)
H = head() - 20; rnd = random.Random('42220-hashes'); MIG = 31056500
hs = set(rnd.sample(range(MIG, H), 100)) | set(rnd.sample(range(H - 5000, H), 60)) | {75046579, 75046580, 75046581, 75046582, 75046583}
while len(hs) < 200: hs.add(rnd.randrange(MIG, H))
hs = sorted(hs)
R = {'head': H, 'heights': hs, 'started': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'rows': {}, 'errors': collections.Counter()}
builds_seen = set()
for h in hs:
    row = {}
    for u in EPS:
        tries = 30 if u == EPS[0] else 2
        for t in range(tries):
            try:
                cv, b = batch(u, h)
            except Exception as e:
                R['errors'][u + ' ' + str(e)[:60]] += 1; time.sleep(1); continue
            key = u + ' | ' + str(cv); builds_seen.add(key)
            row.setdefault(key, b)
            if u != EPS[0]: break
            fb = [k for k in builds_seen if k.startswith(EPS[0])]
            if t >= 3 and all(k in row for k in fb): break
    hashes = {k: (v or {}).get('hash') for k, v in row.items()}
    R['rows'][h] = {'byBuild': row, 'agree': len(set(hashes.values())) == 1}
    if not R['rows'][h]['agree']: print('DIFF', h, hashes, flush=True)
R['buildsSeen'] = sorted(builds_seen); R['errors'] = dict(R['errors'])
R['finished'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
R['summary'] = {'heights': len(hs), 'agree': sum(1 for v in R['rows'].values() if v['agree']),
                'answersPerBuild': dict(collections.Counter(k for v in R['rows'].values() for k in v['byBuild']))}
json.dump(R, open(OUT, 'w'), indent=1); print(json.dumps(R['summary'], indent=1))
