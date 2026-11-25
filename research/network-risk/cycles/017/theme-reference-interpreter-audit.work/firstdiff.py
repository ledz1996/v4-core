"""Debug helper: the first call, in start order, where the reference run of replay17.py and the chain's call tree part.
usage: python3 firstdiff.py <cid> <url> <tx>"""
import sys, json, replay17 as RP, pyevm_tx17 as P
cid, url, h = int(sys.argv[1]), sys.argv[2], sys.argv[3]
class All(set):
    def __contains__(self, x): return True
o = P.World.__setattr__
def sa(self, n, v):
    if n == 'watch': v = All()
    object.__setattr__(self, n, v)
P.World.__setattr__ = sa
nets = {n['chainId']: n for n in json.load(open(RP.os.path.join(RP.NR, 'state', 'networks.json')))['networks']}
W = []
oi = P.World.__init__
def init(self, *a, **k):
    oi(self, *a, **k); W.append(self)
    if len(sys.argv) > 5: self.trace = []; self.trace_stack = 3
P.World.__init__ = init
r = RP.one(cid, url, nets[cid]['poolManager'], h)
ct = RP.R(url, 'debug_traceTransaction', [h, {'tracer': 'callTracer'}])
chain = []
def walk(n, d):
    chain.append((d, (n.get('to') or '').lower(), (n.get('input') or '')[:10], 'error' not in n, n.get('type'), n.get('gas'), n.get('gasUsed'), (n.get('output') or '')[:74]))
    for c in n.get('calls', []) or []: walk(c, d + 1)
walk(ct, 0)
ref = [(f[0], '0x%040x' % f[1], '0x' + f[2], f[3]) for f in W[0].frames]
for i, (a, b) in enumerate(zip(chain, ref)):
    if (a[0], a[2]) != (b[0], b[2]) or (len(sys.argv) > 6 and a[3] != b[3]) or (a[4] != 'DELEGATECALL' and a[1] != b[1]):
        print('first difference at call', i)
        N = int(sys.argv[4]) if len(sys.argv) > 4 else 3
        for j in range(max(0, i - 2), min(len(chain), i + N)): print('  chain', j, chain[j][:4], chain[j][4])
        for j in range(max(0, i - 2), min(len(ref), i + N)): print('  ref  ', j, ref[j])
        w = W[0]
        if w.trace is not None:
            import collections
            print('  last ops at depth 8/9:', [t for t in w.trace if t[0] in (8, 9)][-25:])
        break
else: print('no difference in', min(len(chain), len(ref)), 'calls', len(chain), len(ref))
