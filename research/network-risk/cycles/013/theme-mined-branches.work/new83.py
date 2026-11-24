import json
W = '/home/user/v4-core/research/network-risk/cycles/012/theme-bytecode-coverage.work/'
b = {x['pc']: x for x in json.load(open(W + 'jumpmap-before.json'))['oneSided']}
a = {x['pc']: x for x in json.load(open(W + 'jumpmap-after.json'))['oneSided']}
out = []
for pc, x in sorted(b.items()):
    if pc in a: continue
    new = 0 if x['seen'] == 'taken' else 1  # the side sets 1 to 5 never took
    s = x['src']; out.append({'pc': pc, 'newSide': new, 'file': s['file'], 'line': s['line'], 'snippet': s['snippet'][:110]})
json.dump(out, open('new83.json', 'w'), indent=1)
print(len(out))
import collections
for o in out: print(o['pc'], o['newSide'], o['file'].split('/')[-1], o['line'], o['snippet'][:80])
