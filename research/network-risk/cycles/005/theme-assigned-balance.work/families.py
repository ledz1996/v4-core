# Group pooled currencies of one network by their selector set (own code plus resolved implementation).
import sys, json, gzip, os, re, hashlib, collections
from names import SIG, RAW, load, CIDS
from value import values
from common import universe
from abi import split_types, supported
INCL = re.compile(r'(?i)^\w*(lock|freez|frozen|vest|stak|bond|escrow|grant|allocat|airdrop|distribut|reward|deposit|mint|issue|assign|delegat|fund|gift|credit|drop|donat|migrat|wrap|hold|restrict|cooldown|transfer|send|pay|give|push|claim|settle|release|burn|seize|slash|confiscat|reclaim|recover|sweep|rescue|collect|rebase|sync|skim|update|accrue|harvest|poke|checkpoint|convert|redeem|withdraw|unstake|unlock|unfreez|revoke|tax|fee|process|trigger|execute|swap|liquidity|buyback|dividend|reflect|compound|earn|tend|kick|drip|gulp|touch|refresh|report|notify|rebalanc|epoch|interest|yield|index|rate|price|oracle)\w*\(')
STD = {'transfer(address,uint256)', 'transferFrom(address,address,uint256)', 'approve(address,uint256)', 'increaseAllowance(address,uint256)', 'decreaseAllowance(address,uint256)',
       'allowance(address,address)', 'balanceOf(address)', 'permit(address,address,uint256,uint256,uint8,bytes32,bytes32)', 'nonces(address)', 'delegates(address)', 'getVotes(address)'}
def build(cid):
    ch, se = load(cid)
    px = {}
    fn = os.path.join(RAW, 'proxies_%d.json.gz' % cid)
    if os.path.exists(fn): px = json.load(gzip.open(fn))
    v = values(cid)
    d, rows = universe(cid); bal = {r['token']: int(r.get('bal2') or 0) for r in rows}
    fam = {}
    cache = {}
    for t, h in ch.items():
        p = se.get(h)
        if not p: continue
        im = tuple(sorted((px.get('beacon', {}).get(a, a) if k == 'beacon' else a) for k, a in (px.get('impl', {}).get(t) or [])))
        ck = (h, im)
        if ck not in cache:
            sels = set(p['sels'])
            for a in im:
                c = px['code'].get(a)
                if c: sels.update(c['sels'])
            key = hashlib.sha1(','.join(sorted(sels)).encode()).hexdigest()[:16]
            cache[ck] = (key, sels)
        key, sels = cache[ck]
        f = fam.setdefault(key, dict(sels=sorted(sels), tokens=0, usd=0.0, reps=[]))
        f['tokens'] += 1; u = (v.get(t) or {}).get('usd') or 0.0
        if u < 5e9: f['usd'] += u
        f['reps'].append((u, t))
        if len(f['reps']) > 40: f['reps'] = sorted(f['reps'], reverse=True)[:3]
    for key, f in fam.items():
        f['reps'] = [t for u, t in sorted(f['reps'], reverse=True)[:3]]
        fns = []; trig = []
        for s in f['sels']:
            for nm in SIG.get(s) or []:
                if nm in STD or not INCL.search(nm): continue
                try: ty = split_types(nm)
                except Exception: continue
                if not supported(ty): continue
                if 'address' in [x.replace('[]', '') for x in ty]: fns.append(nm)
                elif len(ty) <= 2: trig.append(nm)
        f['fns'] = sorted(set(fns)); f['trig'] = sorted(set(trig)); del f['sels']
    json.dump(fam, gzip.open(os.path.join(RAW, 'families_%d.json.gz' % cid), 'wt'))
    print(cid, 'families', len(fam), 'with addr fns', sum(1 for f in fam.values() if f['fns']), 'pairs', sum(len(f['fns']) for f in fam.values()),
          'trigger pairs', sum(len(f['trig']) for f in fam.values()), flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: build(int(c))
