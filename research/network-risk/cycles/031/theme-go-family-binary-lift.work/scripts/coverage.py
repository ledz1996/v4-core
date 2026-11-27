"""Which of the modelled functions the vectors reach, and what share of their instructions.
Runs the first 300 random vectors per op, all c27 knuth vectors and 2,000 v4shapes vectors through the handler
model, then maps visited addresses to functions. usage: python3 -I coverage.py <arch> <out.json>"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys_argv = sys.argv[:]
arch, OUT = sys_argv[1], sys_argv[2]
sys.argv = [sys.argv[0], arch, 'random', '0', '1', '/dev/null']
os.environ['NRAND'] = '300'
src = open(os.path.join(HERE, 'drive.py')).read().split('\nGEN = ')[0]
g = {'__name__': 'cov', '__file__': os.path.join(HERE, 'drive.py')}
exec(src, g)
import models, goshim as G
W = os.path.dirname(HERE)
m = models.Model(arch, W + '/dl/%s/usr/local/bin/nitro' % arch, W + '/dl/build/all-%s.txt' % arch)
V = list(g['rand']()) + [v for v in g['c27']() if not v[0].startswith('c27-poolmath')] + list(g['v4shapes']())[:2000]
for tag, op, a, b, c in V:
    m.run_handler(op, a, b, c)
out = {}
ins = sorted(m.prog.ins)
for name, (lo, hi) in m.ranges.items():
    tot = [a for a in ins if lo <= a < hi]
    hit = [a for a in tot if a in m.visited]
    out[name.replace(G.U, 'uint256.').replace(G.VM, 'vm.')] = [len(hit), len(tot)]
json.dump({'arch': arch, 'vectors': len(V), 'functions': out}, open(OUT, 'w'), indent=1)
for k, v in out.items():
    print(k, v)
