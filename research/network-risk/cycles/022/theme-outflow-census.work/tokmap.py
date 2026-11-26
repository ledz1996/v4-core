"""For every non-fee flagged row in raw/reclass_*.json.gz: class, token, rows, one example, and the findings and cleared
entries in research/network-risk/state that name the token address. Writes raw/tokmap.json. No RPC."""
import json, gzip, glob, os, collections
H = os.path.dirname(os.path.abspath(__file__)); ST = os.path.join(H, '..', '..', '..', 'state')
F = json.load(open(os.path.join(ST, 'findings.json')))['findings']; C = json.load(open(os.path.join(ST, 'cleared.json')))['cleared']
FS = [(f['id'], json.dumps(f).lower()) for f in F]; CS = [('#%d' % i, json.dumps(c).lower()) for i, c in enumerate(C)]
g = collections.defaultdict(lambda: collections.defaultdict(list))
for fn in glob.glob(os.path.join(H, 'raw', 'reclass_*.json.gz')):
    d = json.load(gzip.open(fn))
    for r in d['rows']:
        k = r.get('refined')
        if k != 'fees': g[(d['chainId'], k)][r['token']].append(r)
out = []
for (cid, k), toks in sorted(g.items(), key=lambda x: (x[0][0], str(x[0][1]))):
    for t, rs in sorted(toks.items(), key=lambda x: -len(x[1])):
        a = t[2:].lower(); refs = [i for i, s in FS if a in s][:5]; crefs = [i for i, s in CS if a in s][:3]
        r = rs[0]; out.append(dict(chainId=cid, cls=k, token=t, rows=len(rs), findings=refs, cleared=crefs, example=r['tx'], block=r.get('block'), poolEvents=r.get('poolEvents'), b0=r.get('b0'), b1=r.get('b1'), why=r.get('why', '')[:120]))
json.dump(out, open(os.path.join(H, 'raw', 'tokmap.json'), 'w'), indent=1)
for o in out: print(o['chainId'], o['cls'], o['token'], o['rows'], o['findings'], o['cleared'], o['example'][:14])
