"""Shows the replay can fail: a planted interpreter fault (MULMOD result off by one when the modulus is 2^256-1,
the case FullMath.mulDiv uses) must make replays of mined swaps unmatched. Usage: planted.py <chainId> <jsonl> <n>"""
import sys, json
sys.path.insert(0, "/home/user/v4-core/research/network-risk/tools/opdiff")
ARGV = list(sys.argv)
import pyevm2
from report import ok
src = open(pyevm2.__file__).read()
assert "elif op == 0x09: a = st.pop(); b = st.pop(); c = st[-1]; st[-1] = (a * b) % c if c else 0" in src
import types
code = src.replace("elif op == 0x09: a = st.pop(); b = st.pop(); c = st[-1]; st[-1] = (a * b) % c if c else 0",
                   "elif op == 0x09: a = st.pop(); b = st.pop(); c = st[-1]; st[-1] = (((a * b) % c) ^ (1 if c == (1 << 256) - 1 else 0)) if c else 0")
exec(compile(code, pyevm2.__file__, 'exec'), pyevm2.__dict__)
import pmreplay; pmreplay.World = pyevm2.World
class PW(pyevm2.World): pass
for k, v in pmreplay.PMWorld.__dict__.items():
    if k in ('call', 'replay_children'): setattr(PW, k, v)
pmreplay.PMWorld = PW
cid, f, n = int(ARGV[1]), ARGV[2], int(ARGV[3])
rows = [json.loads(l) for l in open(f)]
rows = [r for r in rows if 'frames' in r and ok(r) and 'swap:hooked' not in r.get('families', {})][:n]
res = {'tried': 0, 'unmatched': 0}
for r in rows:
    x = pmreplay.pmreplay(cid, r['tx']); res['tried'] += 1
    res['unmatched'] += int('frames' not in x or not ok(x))
print(json.dumps(res))
