# Step 2c. Pair and pool addresses of every priced currency against the base tokens, read from the verified factories by static call.
import sys, json, os, collections
from base import *
from stubs import GET3
from getters import chunks, isaddr
def run(cid):
    F = json.load(open(os.path.join(RAW7, 'facs_%d.json' % cid)))
    live = jz(os.path.join(RAW7, 'live_%d.json.gz' % cid))['rows']
    toks = sorted(live); items = []
    for t in toks:
        for b in F['bases']:
            if b == t: continue
            for f in F['v2']: items.append((t, f, 'v2', 'e6a43905' + adr(t) + adr(b) + '0' * 64))
            for f in F['solidly']:
                items.append((t, f, 'solidly', '79bc57d5' + adr(t) + adr(b) + u256(0)))
                items.append((t, f, 'solidly', '79bc57d5' + adr(t) + adr(b) + u256(1)))
            for f, v in F['v3'].items():
                for fee in v['fees']: items.append((t, f, 'v3', '1698ee82' + adr(t) + adr(b) + u256(fee)))
    res = chunks(cid, items, 1200 if cid != 999 else 300, lambda x: adr(x[1]) + x[3].ljust(256, '0'), 64, GET3, gas=45_000_000 if cid != 999 else 29_000_000)
    out = collections.defaultdict(dict); fails = 0
    for (t, f, kind, cd), v in zip(items, res):
        if v is None: fails += 1; continue
        if isaddr(v): out[t]['0x%040x' % v] = [kind, f]
    wz(os.path.join(RAW7, 'pairs_%d.json.gz' % cid), out)
    k = collections.Counter(x[0] for d in out.values() for x in d.values())
    print(cid, net(cid)['name'], 'tokens', len(toks), 'lookups', len(items), 'failed', fails, 'tokens with a pair or pool', len(out), dict(k), flush=True)
if __name__ == '__main__':
    for c in sys.argv[1:]: run(int(c))
