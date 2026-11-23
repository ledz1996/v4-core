# Which pooled currencies of the full lists (priced or not) have a function whose name says it acts for a holder passed as argument?
import sys, json, os, re, collections
from base import *
import holder
PAT = re.compile(r'(?i)^(claim|migrat|redeem|exit|convert|upgrade|wrap|unwrap|withdraw|burn|swap|exchange|release|unstake|harvest|liquidat|settle|close|sweep|recover|rescue|reclaim|seize|force|expire|cancel|refund|collect|compound|reinvest|rebalanc|process|poke|touch|update|accrue|checkpoint|sync|kick|deposit)\w*')
HOLD = re.compile(r'(?i)(for|to|onbehalf|behalf|of|user|account|holder|from|owner|all)$')
def want(nm):
    try: types = split_types(nm)
    except Exception: return False
    if not any(t.split('[')[0] == 'address' for t in types): return False
    n = nm.split('(')[0]
    if n in ('transferFrom', 'burnFrom', 'allowance', 'balanceOf', 'delegates', 'nonces', 'depositFor', 'withdrawTo') and False: return False
    return bool(PAT.match(n)) and bool(HOLD.search(n))
WANT = {s: [n for n in v if want(n)] for s, v in holder.SIG.items()}
WANT = {s: v for s, v in WANT.items() if v}
def tokens(cid):
    """token -> set of wanted selectors (own code and implementation)."""
    out = collections.defaultdict(set)
    for raw in (RAW6C, RAW5):
        f1 = os.path.join(raw, 'codehash_%d.json.gz' % cid); f2 = os.path.join(raw, 'selectors_%d.json.gz' % cid); f3 = os.path.join(raw, 'proxies_%d.json.gz' % cid)
        if not (os.path.exists(f1) and os.path.exists(f2)): continue
        ch = jz(f1); se = jz(f2)
        hit = {h: [s for s in o['sels'] if s in WANT] for h, o in se.items()}
        for t, h in ch.items():
            for s in hit.get(h) or []: out[t].add(s)
        if os.path.exists(f3):
            px = jz(f3); code = px.get('code') or {}
            for t, lst in (px.get('impl') or {}).items():
                for kind, a in lst:
                    for s in (code.get(a) or {}).get('sels') or []:
                        if s in WANT: out[t].add(s)
        break
    return out
if __name__ == '__main__':
    tot = 0; names = collections.Counter()
    for cid in CIDS:
        o = tokens(cid); tot += len(o)
        for t, ss in o.items():
            for s in ss: names[WANT[s][0]] += 1
        print(cid, net(cid)['name'], 'tokens with such a function', len(o), flush=True)
    print('total', tot, 'selectors wanted', len(WANT))
    for n, c in names.most_common(70): print('  ', c, n)
