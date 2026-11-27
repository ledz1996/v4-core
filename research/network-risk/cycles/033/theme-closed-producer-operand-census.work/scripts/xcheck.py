"""Instrument check: classes counted by the census build of the validator for the PoolManager in one block
against classes recomputed in Python from the replica's struct-log trace of the block's single PoolManager transaction."""
import json, gzip, sys, os, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classes import structlog_census
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = 'https://mainnet.megaeth.com/rpc'; PM = '0xacb7e78fa05d562e0a5d3089ec896d57d057d38e'
def rpc(m, p):
    q = json.dumps({"jsonrpc": "2.0", "id": 1, "method": m, "params": p}).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(R, q, {'content-type': 'application/json', 'user-agent': 'census-readonly'}), timeout=120).read())
cen = {}
for l in open(sys.argv[1]):
    p = l.split(); bn = int(p[0])
    if p[3] == PM: cen.setdefault(bn, {})[(int(p[1]), int(p[2]), p[3], int(p[4]))] = int(p[5])
out = []
print('client', rpc('web3_clientVersion', [])['result'])
for tx, bn in [l.split() for l in open(sys.argv[2])]:
    bn = int(bn)
    blk = rpc('eth_getBlockByNumber', [hex(bn), True])['result']
    t = [x for x in blk['transactions'] if x['hash'] == tx][0]
    p = os.path.join(W, 'data/structlog', tx + '.json.gz')
    if not os.path.exists(p):
        r = rpc('debug_traceTransaction', [tx, {"disableMemory": True, "disableStorage": True}])
        json.dump(r, gzip.open(p, 'wt'))
    tr = json.load(gzip.open(p))['result']
    sl = {k: v for k, v in structlog_census(tr, t['to']).items() if k[2] == PM}
    cb = cen.get(bn, {})
    diff = {str(k): [sl.get(k), cb.get(k)] for k in set(sl) | set(cb) if sl.get(k) != cb.get(k)}
    out.append({'tx': tx, 'block': bn, 'keys': len(sl), 'census_keys': len(cb), 'steps': len(tr['structLogs']), 'diff': diff})
    print(tx, bn, len(sl), len(cb), len(diff), list(diff.items())[:3])
print('client', rpc('web3_clientVersion', [])['result'])
json.dump(out, open(sys.argv[3], 'w'), indent=1)
