"""Task 1: one table of all 774 jump sides of the build: run by script sets 1-6 (jumpmap.json), by cycle 25 cases,
by cycle 26 cases, and by mined transactions of the Monad, MegaETH, HyperEVM producers (and Base for reference),
from the cycle 24 producer coverage. Usage: python3 table.py <out.json>"""
import sys, os, json
NR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
C = lambda *p: os.path.join(NR, *p)
build = json.load(open(C('build', 'PoolManager.json')))
rt = build.get('runtime') or build.get('deployedBytecode') or build.get('bin-runtime')
if isinstance(rt, dict): rt = rt.get('object')
code = bytes.fromhex(rt[2:] if rt.startswith('0x') else rt)
jumps = []; i = 0
while i < len(code):
    op = code[i]
    if op == 0x57: jumps.append(i)
    i += op - 0x5e if 0x60 <= op <= 0x7f else 1
jm = json.load(open(C('opcodes', 'jumpmap.json')))
one = {r['pc']: r for r in jm['oneSided']}; never = {r['pc']: r for r in jm['neverReached']}
c25 = json.load(open(C('cycles', '025', 'theme-unexecuted-sides.work', 'out', 'ref-1.json')))
s25 = set(c25['sides']) | set(c25.get('perCaseSides', {}).get('outside', []))
c26 = set(json.load(open(C('cycles', '026', 'theme-hook-and-native-sides.work', 'out', 'ref-1.json')))['sides'])
prod = {}; srcrow = {}
for ch in ('143', '4326', '999', '8453'):
    b = json.load(open(C('cycles', '024', 'theme-producer-branch-coverage.work', 'out', ch, 'branches.json')))
    s = set()
    for r in b['rows']:
        if r['taken']: s.add('%d:1' % r['pc'])
        if r['fallthrough']: s.add('%d:0' % r['pc'])
        srcrow[r['pc']] = r
    prod[ch] = s
rows = []
for pc in jumps:
    for sd in (0, 1):
        k = '%d:%d' % (pc, sd)
        if pc in never: sets = False
        elif pc in one: sets = (one[pc]['seen'] == ('taken' if sd else 'fallthrough'))
        else: sets = True
        r = srcrow.get(pc, {})
        row = {'side': k, 'file': r.get('file'), 'line': r.get('line'), 'snippet': (r.get('snippet') or '')[:100],
               'sets1to6': sets, 'c25': k in s25, 'c26': k in c26,
               'monad143': k in prod['143'], 'megaeth4326': k in prod['4326'], 'hyperevm999': k in prod['999'], 'base8453': k in prod['8453']}
        row['nothing'] = not any(row[x] for x in ('sets1to6', 'c25', 'c26', 'monad143', 'megaeth4326', 'hyperevm999', 'base8453'))
        row['nrSets'] = sum(row[x] for x in ('sets1to6', 'c25', 'c26'))
        if pc in one: row['jumpmapWhy'] = one[pc].get('why'); row['decides'] = one[pc].get('decides')
        if pc in never: row['jumpmapWhy'] = never[pc].get('why'); row['decides'] = never[pc].get('decides')
        rows.append(row)
cnt = lambda f: sum(1 for r in rows if f(r))
summ = {'jumps': len(jumps), 'sides': len(rows), 'sets1to6': cnt(lambda r: r['sets1to6']), 'c25': cnt(lambda r: r['c25']),
        'c26': cnt(lambda r: r['c26']), 'monad': cnt(lambda r: r['monad143']), 'megaeth': cnt(lambda r: r['megaeth4326']),
        'hyperevm': cnt(lambda r: r['hyperevm999']), 'base': cnt(lambda r: r['base8453']), 'nothing': cnt(lambda r: r['nothing']),
        'notByClosedProducers': cnt(lambda r: not r['megaeth4326'] and not r['hyperevm999'])}
json.dump({'summary': summ, 'rows': rows}, open(sys.argv[1], 'w'), indent=1)
print(summ)
for r in rows:
    if r['nothing']: print('NOTHING', r['side'], (r['file'] or '').split('/')[-1], r['line'], r['snippet'][:60], '|', (r.get('jumpmapWhy') or '')[:150])
