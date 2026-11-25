"""Rerun, at the real address and with more gas, every script whose 25 million gas answer differs from the stored
fresh-address answer (raw/compare.json: differentFromStoredFresh and differentFromEthereumReal, or Ethereum's own list). As in pmdiff6.py the gas
limits 2,000,000,000, 150,000,000, 50,000,000 and 30,000,000 are tried in turn and the first that the endpoint accepts
is kept. The answer is then compared with the stored fresh-address hash.

Usage: python3 gasretry.py <set> <chainId> <out.json>
"""
import sys, os, json, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv_saved = list(sys.argv)
s, cid, outp = sys.argv[1], int(sys.argv[2]), sys.argv[3]
# realrun.py reads its own argv when imported, so give it the shape it expects
sys.argv = ['realrun.py', s, 'real', str(cid), '/dev/null', '1']
sys.path.insert(0, HERE)
import realrun as RR  # noqa
datas, kinds, drv, ov = RR.build()
cmp_ = json.load(open(os.path.join(HERE, '..', 'raw', 'compare.json')))['set' + s]
st = json.load(open(os.path.join(RR.TOOLS, '..', '..', 'opcodes', {'1': 'pmdiff.json', '2': 'pmdiff2.json', '6': 'pmdiff6.json'}[s])))
refh = st['referenceHashes']
idx = cmp_['ethereumRealVsStoredFresh']['different'] if cid == 1 else sorted(set(cmp_['networks'][str(cid)]['differentFromStoredFresh']) | set(cmp_['networks'][str(cid)]['differentFromEthereumReal']))
res = {}
for i in idx:
    got = None
    for gas in (2_000_000_000, 150_000_000, 50_000_000, 30_000_000):
        r = RR.ask(datas[i], drv, ov, gas)
        if not r.startswith('ERR'): got = (gas, r); break
    if got is None: res[str(i)] = {'error': r[:200]}; continue
    h = hashlib.sha256(bytes.fromhex(got[1][2:])).hexdigest()
    res[str(i)] = {'gas': got[0], 'equalsStoredFresh': h == refh[i], 'hash': h}
json.dump(res, open(outp, 'w'), indent=1)
print(s, cid, 'retried', len(idx), 'now equal to stored fresh', sorted(int(i) for i, v in res.items() if v.get('equalsStoredFresh')),
      'still different', sorted(int(i) for i, v in res.items() if not v.get('equalsStoredFresh')))
