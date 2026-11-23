# Lead L-397, last part, and L-386: every pooled currency on the 21 networks whose code (own or resolved implementation) holds the
# selector of claimIdleTokens(address) or of a few other functions that move or burn another holder's balance by rule.
import json, gzip, os, sys, collections
from base import *
SIGS = ['claimIdleTokens(address)', 'getTimeUntilClaimable(address)', 'lastTransferTime(address)', 'claimInactive(address)', 'sweepInactive(address)', 'burnInactive(address)',
        'reclaimIdle(address)', 'claimDormant(address)', 'liquidateInactive(address)', 'claimAbandoned(address)', 'decay(address)', 'burnIdle(address)', 'claimExpired(address)',
        'collectDemurrage(address)', 'applyDemurrage(address)', 'reapInactive(address)', 'purge(address)', 'isIdle(address)', 'lastActive(address)', 'lastActivity(address)']
SEL = {sel(s)[2:]: s for s in SIGS}
print(SEL)
out = {}
for n in NETS:
    cid = n['chainId']
    f1 = os.path.join(RAW5, 'codehash_%d.json.gz' % cid); f2 = os.path.join(RAW5, 'selectors_%d.json.gz' % cid); f3 = os.path.join(RAW5, 'proxies_%d.json.gz' % cid)
    if not (os.path.exists(f1) and os.path.exists(f2)): print(cid, 'no selector file'); continue
    ch = jz(f1); se = jz(f2); px = jz(f3) if os.path.exists(f3) else {'impl': {}, 'beacon': {}, 'code': {}}
    hits = collections.defaultdict(list); covered = 0
    for t, h in ch.items():
        p = se.get(h)
        if not p: continue
        covered += 1
        sels = set(p['sels'])
        for k, a in (px['impl'].get(t) or []):
            a2 = px['beacon'].get(a, a) if k == 'beacon' else a
            c = px['code'].get(a2)
            if c: sels.update(c['sels'])
        for s in sels & set(SEL): hits[SEL[s]].append(t)
    out[cid] = dict(tokens=len(ch), covered=covered, hits={k: v for k, v in hits.items()})
    print(cid, n['name'], 'currencies', len(ch), 'with parsed code', covered, {k: (len(v), v[:6]) for k, v in hits.items()}, flush=True)
json.dump(out, open(os.path.join(RAW6, 'idle_scan.json'), 'w'))
