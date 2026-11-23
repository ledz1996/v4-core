import json, os, sys
from lib import *
from show import dump
def norm(lines, o):
    out = []
    for i, l in enumerate(lines):
        out.append(l)
    return out
ref = json.load(open(os.path.join(HERE, 'raw', 'tests_1.json')))
summary = {}
for n in NETS:
    cid = n['chainId']; o = json.load(open(os.path.join(HERE, 'raw', 'tests_%d.json' % cid)))
    row = {}
    for k in ('proxy', 'designator', 'real'):
        key = [x for x in o if x.startswith(k + '_v')]
        used = [x for x in key if 'result' in o[x]]
        if not used: row[k] = 'no result: ' + json.dumps(o[key[-1]].get('error'))[:120]; continue
        a = dump(o[used[0]]['result']); b = dump(ref[k + '_v1000']['result'])
        # lines that legitimately differ: balances of the PoolManager and the real owner
        skip = {'proxy': (5, 9, 13), 'designator': (5, 9, 13), 'real': (10,)}[k]
        top = [i for i, l in enumerate(a) if not l.startswith('  ')]
        diffs = []
        if len(a) != len(b): diffs.append('length %d vs %d' % (len(a), len(b)))
        ti = -1
        for i, (x, y) in enumerate(zip(a, b)):
            if not x.startswith('  '): ti += 1
            if x != y and not (not x.startswith('  ') and ti in skip): diffs.append('%s | ref %s' % (x.strip(), y.strip()))
        row[k] = (used[0], 'same as Ethereum' if not diffs else diffs)
    summary[cid] = row
    print(cid, n['name']); [print('   ', k, v) for k, v in row.items()]
json.dump(summary, open(os.path.join(HERE, 'raw', 'compare.json'), 'w'), indent=1)
