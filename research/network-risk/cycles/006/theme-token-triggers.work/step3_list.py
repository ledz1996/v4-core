# Step 3 list: tokens worth more than 10,000 USD at a PoolManager whose function names (own code, implementation, contracts
# read by balanceOf) contain lock, vest, cooldown, freeze, escrow, idle, inactive, sweep, reflect or claim words.
import sys, json, gzip, os, re, glob, collections
from base import *
SIG = jz(os.path.join(RAW5, 'signatures.json.gz')); SIG.update(jz(os.path.join(RAW6, 'signatures_more.json.gz')))
RX = re.compile(r'(?i)((?<![bc])lock|(?<!in)vest|cooldown|freez|frozen|escrow|idle|inactiv|sweep|reflect|claim)')   # not clock, block, invest
NOISE = re.compile(r'(?i)^(LOCK8605463013|claimOwnership|claimGovernance|nonblockingLzReceive|available_assert_time|claimOwnership|pendingOwner|block|unblock|isBlock|blockList|blocklist|addToBlock|removeFromBlock|isBlocked|blocked|getBlock|destroyBlockedFunds|isBlackListed|blockPlaceholder|Blocked)')
out = []
for f in sorted(glob.glob(os.path.join(RAW6, 'discover_*.json.gz'))):
    cid = int(f.split('_')[-1].split('.')[0])
    for t, o in jz(f).items():
        if o['usd'] < 10000: continue
        sels = set(o.get('sels') or [])
        for a, r in (o.get('rel') or {}).items(): sels.update(r['sels'])
        nms = sorted({nm.split('(')[0] for s in sels for nm in (SIG.get(s) or [])[:3] if RX.search(nm.split('(')[0]) and not NOISE.search(nm)})
        unnamed = sum(1 for s in sels if not SIG.get(s))
        if nms: out.append(dict(cid=cid, token=t, sym=o['sym'], usd=o['usd'], names=nms, unnamed=unnamed, rel=list((o.get('rel') or {}).keys())))
out.sort(key=lambda x: -min(x['usd'], 1e15))
json.dump(out, open(os.path.join(RAW6, 'step3_list.json'), 'w'), indent=0)
print(len(out), collections.Counter(x['cid'] for x in out))
for x in out: print(x['cid'], x['token'], str(x['sym'])[:12], '$%d' % min(x['usd'], 9e15), ','.join(x['names'])[:230])
