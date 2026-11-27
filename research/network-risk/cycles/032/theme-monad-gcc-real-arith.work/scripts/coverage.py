"""Per block of the 128 un-entered value blocks: emit kinds run on real states in the gcc model (cycle 31 shifts,
cycle 32 arithmetic and Task 4 kinds) and those still not run. usage: python3 -I coverage.py <out.json>"""
import json, sys, os, collections
C31 = '/home/user/v4-core/research/network-risk/cycles/031/theme-monad-gcc-real-states.work'
sys.path.insert(0, C31 + '/scripts')
from blockops import opname
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
st = [json.loads(l) for l in open(C31 + '/out/states.jsonl')]
want = {int(k, 16) for k in json.load(open(C31 + '/out/value128-ops.json'))['blocks']}
ran = set()
for f in ('realarith.json', 'realother.json', 'realother-SGT_SLT.json'):
    for s in json.load(open(os.path.join(W, 'out/model', f)))['sites']:
        if s.get('stream', '').startswith('equal'): ran.add(int(s['pc'], 16))
for s in json.load(open(C31 + '/out/model/realshift.json'))['sites']: ran.add(int(s['pc'], 16))
BOOK = lambda k: k.startswith(('PUSH', 'DUP', 'SWAP')) or k == 'POP' or k == 'JUMPDEST'
per = collections.defaultdict(lambda: {'run': collections.Counter(), 'left': collections.Counter()})
tot = {'run': collections.Counter(), 'left': collections.Counter()}
for s in st:
    if s['b'] not in want: continue
    if s['w'] == 'i':
        k = opname(s['pc'])
        if BOOK(k): continue
        side = 'run' if s['pc'] in ran else 'left'
    elif s['w'] == 't': k = 'terminator'; side = 'left'
    else: continue
    per[hex(s['b'])][side][k] += 1; tot[side][k] += 1
out = {'total': {k: dict(v) for k, v in tot.items()}, 'blocks': {b: {k: dict(v) for k, v in d.items()} for b, d in sorted(per.items(), key=lambda x: int(x[0], 16))}}
json.dump(out, open(sys.argv[1], 'w'), indent=1)
print('run', sum(tot['run'].values()), dict(tot['run'])); print('left', sum(tot['left'].values()), dict(tot['left']))
for b in ('0x5757', '0x57ca', '0x5860', '0x588a', '0x58d6', '0x58db'): print(b, out['blocks'].get(b))
