import sys, json, os
from lib import *
def load(cid):
    st = json.load(open(os.path.join(HERE, 'raw', 'state_%d.json' % cid))); cl = json.load(open(os.path.join(HERE, 'raw', 'claims_%d.json' % cid)))
    bal = {}
    for o, i, v in cl['bal']:
        if v: bal.setdefault(o, {})[i] = v
    X = {}
    for ow, x, v in st['liveOp']:
        if v: X.setdefault(x, dict(op=set(), al={}))['op'].add(ow)
    for ow, x, i, v in st['liveAl']:
        if v: X.setdefault(x, dict(op=set(), al={}))['al'].setdefault(ow, {})[i] = v
    rows = []
    for x, d in X.items():
        info = st['info'].get(x, {})
        kind = ('7702->' + info['delegate']) if info.get('delegate') else ('EOA' if info.get('len') == 0 else 'code %d %s' % (info.get('len', -1), info.get('h')))
        ex = {}  # owner -> {id: reachable amount}
        for ow in d['op']:
            if ow in bal: ex[ow] = dict(bal[ow])
        for ow, m in d['al'].items():
            for i, a in m.items():
                i64 = '0x' + int(i, 16).to_bytes(32, 'big').hex()
                b = bal.get(ow, {}).get(i64, 0)
                if b and ow not in d['op']: ex.setdefault(ow, {})[i64] = min(a, b)
        rows.append(dict(x=x, kind=kind, nOp=len(d['op']), nAl=len(d['al']), exposed=ex, ownerCode={o: st['ownerCodeLen'].get(o) for o in ex}))
    return rows
if __name__ == '__main__':
    for c in sys.argv[1:]:
        cid = int(c); rows = load(cid)
        print('==', cid, net(cid)['name'], 'approved addresses with live approvals', len(rows), 'with owners holding claims', sum(1 for r in rows if r['exposed']))
        for r in sorted(rows, key=lambda r: -len(r['exposed'])):
            if not r['exposed'] and r['nOp'] + r['nAl'] < 3: continue
            print('  %s %-40s liveOp %3d liveAl %3d ownersWithClaims %3d ownerIsContract %d' % (r['x'], r['kind'], r['nOp'], r['nAl'], len(r['exposed']), sum(1 for o, l in r['ownerCode'].items() if l)))
