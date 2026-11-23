import sys, json, os
from lib import *
from summarize import load
def show(cid, top=40):
    o, ops, sp = load(cid); st = json.load(open(os.path.join(HERE, 'raw', 'state_%d.json' % cid)))
    info = st['info']; liveop = {}; liveal = {}
    for ow, x, v in st['liveOp']:
        if v: liveop.setdefault(x, set()).add(ow)
    for ow, x, i, v in st['liveAl']:
        if v: liveal.setdefault(x, set()).add(ow)
    g = {}
    for x, d in info.items():
        k = ('7702->' + d['delegate']) if d.get('delegate') else ('EOA' if d.get('len') == 0 else '%s/%d' % (d.get('h'), d.get('len', -1)))
        g.setdefault(k, []).append(x)
    print('==', cid, net(cid)['name'], 'addresses', len(info), 'code groups', len(g))
    for k, xs in sorted(g.items(), key=lambda kv: -sum(len(liveop.get(x, ())) + len(liveal.get(x, ())) for x in kv[1]))[:top]:
        nlo = sum(len(liveop.get(x, ())) for x in xs); nla = sum(len(liveal.get(x, ())) for x in xs)
        print('  %-58s addrs %3d  liveOpOwners %3d liveAllowOwners %3d  e.g. %s' % (k, len(xs), nlo, nla, xs[0]))
if __name__ == '__main__':
    for c in sys.argv[1:]: show(int(c))
