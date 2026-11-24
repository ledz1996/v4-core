"""Merge cg_<chain>.json files and summarise callee gas against Ethereum."""
import json, glob, os, sys
d = {}
here = os.path.dirname(os.path.abspath(__file__))
for f in glob.glob(os.path.join(here, 'raw', 'cg_*.json')) + [os.path.join(here, 'raw', 'calleegas.json')]:
    if os.path.exists(f):
        d.update(json.load(open(f)))
eth = d['1']['rows']
FWD = 1_000_000
out = {}
for cid, net in sorted(d.items(), key=lambda x: int(x[0])):
    allgas, heavy, diff_common = [], [], []
    for t, rr in net['rows'].items():
        for k, r in rr.items():
            if 'error' in r:
                heavy.append([t, k, 'rpc-error', r['error'][:100]]); continue
            if r['used'] >= FWD:
                if t in eth:
                    e = eth[t].get(k, {})
                    if e.get('used', 0) < FWD:
                        diff_common.append([t, k, r['used'], r['ok'], e.get('used')])
                else:
                    allgas.append([t, k, r['ok'], r['rds']])
            elif r['used'] > 60_000:
                heavy.append([t, k, r['used'], r['ok']])
            elif t in eth and k in eth[t] and 'used' in eth[t][k] and r['ok'] != eth[t][k]['ok']:
                diff_common.append([t, k, r['used'], r['ok'], eth[t][k].get('used'), 'okflag'])
    out[cid] = {'name': net['name'], 'specialAllGas': allgas, 'heavyOver60k': heavy, 'commonDiffersFromEthereum': diff_common}
json.dump(out, open(os.path.join(here, 'raw', 'summary.json'), 'w'), indent=1)
for cid, o in out.items():
    print(cid, o['name'])
    sa = {}
    for t, k, ok, rds in o['specialAllGas']:
        sa.setdefault(t, []).append(k)
    for t, ks in sa.items():
        print('   ALLGAS', t, ks)
    for h in o['heavyOver60k']:
        print('   HEAVY', h)
    for h in o['commonDiffersFromEthereum']:
        print('   DIFF ', h)
