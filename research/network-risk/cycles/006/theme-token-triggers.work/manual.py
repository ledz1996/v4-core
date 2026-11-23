# Run the step 2 trial set on named tokens whatever their price (controls and follow-ups). Usage: manual.py <chainId> <token> [...]
import sys, json, gzip, os
from base import *
from tokcode import parse
from discover import rr, SLOTS
from acl_fix import acl_of
import sweep
def entry(cid, t):
    pm = net(cid)['poolManager'].lower(); t = t.lower()
    r = ecall(cid, t, sel('balanceOf(address)') + adr(pm)); b = int(r[2:66], 16)
    c = rr(cid, 'eth_getCode', [t, 'latest']); p = parse(c)
    o = dict(usd=0, sym='manual', bal=str(b), dec=18, size=p['size'], sels=p['sels'], deleg=p['deleg'], rel={})
    rel = {}
    acl = acl_of(cid, t, pm)
    for e in acl.get('accessList') or []:
        a = e['address'].lower()
        if a != t and int(a, 16) > 0xffff: rel[a] = 'acl'
    for s in SLOTS:
        v = rr(cid, 'eth_getStorageAt', [t, s, 'latest'])
        if isinstance(v, str) and int(v, 16) and int(v, 16) < 2 ** 160: rel['0x%040x' % int(v, 16)] = 'impl'
    for a, k in rel.items():
        c2 = rr(cid, 'eth_getCode', [a, 'latest'])
        if isinstance(c2, str) and len(c2) > 2: o['rel'][a] = dict(kind=k, size=len(c2) // 2 - 1, sels=parse(c2)['sels'])
    return t, o
def slot_entry(cid, t, o):
    import slots as S
    f = S.find(cid, t, [t] + [a for a, r in o['rel'].items() if r['kind'] == 'acl'])
    if f:
        ts = ecall(cid, t, sel('totalSupply()')); f['totalSupply'] = str(int(ts[2:66], 16) if isinstance(ts, str) and len(ts) >= 66 else 0)
    return f
if __name__ == '__main__':
    md = 'A'
    if sys.argv[1] == 'B': md = 'B'; sys.argv.pop(1)
    cid = int(sys.argv[1]); toks = sys.argv[2:]
    fn = os.path.join(RAW6, 'discover_%d.json.gz' % (cid + 10 ** 9))
    d = dict(entry(cid, t) for t in toks)
    # write under a control name so the main files are untouched
    import shutil
    real = os.path.join(RAW6, 'discover_%d.json.gz' % cid); bak = real + '.main'
    shutil.copy(real, bak)
    try:
        json.dump(d, gzip.open(real, 'wt'))
        sreal = os.path.join(RAW6, 'slots_%d.json.gz' % cid); sbak = sreal + '.main'
        if md == 'B':
            if os.path.exists(sreal): shutil.copy(sreal, sbak)
            sl = {t: slot_entry(cid, t, o) for t, o in d.items()}; sl = {t: f for t, f in sl.items() if f}
            print('slots', sl)
            json.dump(sl, gzip.open(sreal, 'wt'))
        sweep.run(cid, only=set(d), mode=md)
    finally:
        shutil.move(bak, real)
        if md == 'B' and os.path.exists(sbak): shutil.move(sbak, sreal)
    pf = os.path.join(RAW6, 'sweep%s_%d_part.json.gz' % ('' if md == 'A' else 'B', cid))
    r = jz(pf)
    os.replace(pf, os.path.join(RAW6, 'control%s_%d_%s.json.gz' % (md, cid, toks[0][:10])))
    for t, o in r['tokens'].items():
        print(t, 'bal', d[t]['bal'], 'trials', o['trials'], 'accepted', o['ok'], 'failed calls', o['fail'])
        for dt, b in o['base'].items(): print('  base dt', dt, b)
        seen = set()
        for h in o['hits']:
            k = (h['fn'], h['cat'], h['dt'])
            if k in seen: continue
            seen.add(k); print('  ', h['dt'], h['cat'], h['fn'], h['target'][:10], 'w', h['w'])
