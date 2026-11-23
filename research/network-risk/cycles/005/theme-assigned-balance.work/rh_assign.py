# Robinhood Chain: selector families from sampled code, then the same assign trials as on the other networks.
import json, gzip, os, hashlib, collections
from common import *
from names import SIG
from families import INCL, STD
from abi import split_types, supported
cid = 4663
x = json.load(gzip.open(os.path.join(RAW, 'rh_codes.json.gz')))
d, rows = universe(cid); bal = {r['token']: int(r.get('bal2') or 0) for r in rows}
fam = {}
for t, p in x['codes'].items():
    sels = set(p['sels'])
    for a in x['impl'].get(t, []):
        c = x['icode'].get(a)
        if c: sels.update(c['sels'])
    key = hashlib.sha1(','.join(sorted(sels)).encode()).hexdigest()[:16]
    f = fam.setdefault(key, dict(sels=sorted(sels), tokens=0, usd=0.0, reps=[]))
    f['tokens'] += p.get('n', 1)
    if len(f['reps']) < 2 and bal.get(t, 0) >= 3: f['reps'].append(t)
for key, f in fam.items():
    fns = []; trig = []
    for s in f['sels']:
        for nm in SIG.get(s) or []:
            if nm in STD or not INCL.search(nm): continue
            try: ty = split_types(nm)
            except Exception: continue
            if not supported(ty): continue
            if 'address' in [z.replace('[]', '') for z in ty]: fns.append(nm)
            elif len(ty) <= 2: trig.append(nm)
    f['fns'] = sorted(set(fns)); f['trig'] = sorted(set(trig)); del f['sels']
json.dump(fam, gzip.open(os.path.join(RAW, 'families_%d.json.gz' % cid), 'wt'))
print('families', len(fam), 'pairs', sum(len(f['fns']) + len(f['trig']) for f in fam.values()), flush=True)
import assign_sweep
assign_sweep.run(cid)
