"""Cycle 34 Task 4 (L-1253). The extended hook (scripts/mkhook.py, build/clang/asmdump_hook34) logs gpq256_regs_ and
StackElem::touched_memory_size_ at every state. Checks: (1) every other field of every state equals the cycle 31 log;
(2) every limb table that cycles 32, 33 and 34 took from the clang listing (realarith/realother/term/inl
'tableFromClangListing', block.py's entry 'table' and 'tablesThroughBlock') equals the logged table at that state;
(3) the touched memory size cycle 33 task3.py read from the listing equals the logged value of the offset element;
(4) the tables and sizes the default model assumed everywhere else equal the logged ones at the 128 blocks' sites.
usage: python3 -I tablecmp.py <out.json>"""
import sys, json, glob
C = '/home/user/v4-core/research/network-risk/cycles'
W = C + '/034/theme-monad-gcc-inlined-storage-sites.work'
GP = ['rax', 'rcx', 'rdx', 'rbx', 'rsp', 'rbp', 'rsi', 'rdi'] + ['r%d' % i for i in range(8, 16)]
DEFAULT = [['r12', 'r13', 'r14', 'r15'], ['r8', 'r9', 'r10', 'r11'], ['rcx', 'rsi', 'rdx', 'rdi']]
old = [json.loads(l) for l in open(C + '/031/theme-monad-gcc-real-states.work/out/states.jsonl')]
new = [json.loads(l) for l in open(W + '/out/states34.jsonl')]
res = {'states': len(new), 'otherFieldsEqual': 0, 'otherFieldsDiffer': []}
ids = {}   # per run the element ids are heap addresses: compare up to a consistent renaming
def strip(s, mp):
    s = json.loads(json.dumps(s)); s.pop('gpq', None)
    for e in s['elems']:
        e.pop('tm', None)
        if 'id' in e: e['id'] = mp.setdefault(e['id'], len(mp))
    for k in ('genowner', 'avxowner'): s[k] = [mp.setdefault(x, len(mp)) if x != '(nil)' else x for x in s[k]]
    s['dc'] = [mp.setdefault(x, len(mp)) if x != '(nil)' else x for x in s['dc'][:2]] + s['dc'][2:]
    return s
mo, mn = {}, {}
assert len(old) == len(new)
for i, (a, b) in enumerate(zip(old, new)):
    if strip(a, mo) == strip(b, mn): res['otherFieldsEqual'] += 1
    else: res['otherFieldsDiffer'].append(i)
tab = lambda s: [[GP[x] for x in r] for r in s['gpq']]
def at(b, pc, w):
    return [i for i, s in enumerate(new) if s['b'] == int(b, 16) and s['pc'] == int(pc, 16) and s['w'] == w]
cmp = []
def check(src, b, pc, w, t, offset=0):
    ii = at(b, pc, w)
    if not ii: cmp.append({'source': src, 'block': b, 'pc': pc, 'result': 'state not found'}); return
    i = ii[0] + offset; lg = tab(new[i])
    cmp.append({'source': src, 'block': b, 'pc': pc, 'w': w, 'fromListing': t, 'logged': lg, 'equal': lg == t})
for f in [C + '/032/theme-monad-gcc-real-arith.work/out/model/realarith.json', C + '/032/theme-monad-gcc-real-arith.work/out/model/realother.json',
          W + '/out/inl.json']:
    for r in json.load(open(f))['sites']:
        if 'tableFromClangListing' in r: check(f.split('/')[-1], r['block'], r['pc'], 'i', r['tableFromClangListing'])
for r in json.load(open(C + '/033/theme-monad-gcc-terminators.work/out/term.json'))['blocks']:
    if 'tableFromClangListing' in r: check('term.json', r['block'], r['pc'], 't', r['tableFromClangListing'])
for f in sorted(glob.glob(C + '/033/theme-monad-gcc-terminators.work/out/block-0x*.json')):
    if any(x in f.split('/')[-1] for x in ('cc-', 'dc-', 'lt-', 'successor')): continue
    for r in json.load(open(f))['blocks']:
        e = [i for i, s in enumerate(new) if s['b'] == int(r['block'], 16) and s['w'] == 'e']
        lg = tab(new[e[0]]); cmp.append({'source': f.split('/')[-1] + ' entry', 'block': r['block'], 'fromListing': r['table'], 'logged': lg, 'equal': lg == r['table']})
        # tables after each emitting instruction: compare with the logged table before the next instruction
        sts = [i for i, s in enumerate(new) if s['b'] == int(r['block'], 16) and s['w'] in ('i', 't')]
        emit = [k for k, (pc, op, n) in enumerate(r['perSite']) if n or op in ('JumpI', 'Jump', 'FallThrough', 'Return', 'Stop')]
        ok = 0; bad = []
        ems = [(pc, op) for pc, op, n in r['perSite'] if not (op.startswith('PUSH') or op.startswith('DUP') or op.startswith('SWAP') or op == 'POP') and op not in ('JumpI', 'Jump', 'FallThrough', 'Return', 'Stop')]
        for (pc, op), t in zip(ems, r['tablesThroughBlock']):
            k = [i for i in sts if new[i]['pc'] == int(pc, 16) and new[i]['w'] == 'i'][0]
            nx = sts[sts.index(k) + 1]
            if tab(new[nx]) == t: ok += 1
            else: bad.append({'pc': pc, 'op': op, 'model': t, 'loggedNext': tab(new[nx])})
        cmp.append({'source': f.split('/')[-1] + ' through block', 'block': r['block'], 'equalAfterEmit': ok, 'differ': bad})
res['listingTables'] = cmp
res['listingTablesEqual'] = sum(1 for x in cmp if x.get('equal') is True)
res['listingTablesDiffer'] = [x for x in cmp if x.get('equal') is False or x.get('differ')]
tm = []
for r in json.load(open(C + '/033/theme-monad-gcc-terminators.work/out/task3.json'))['sites']:
    i = at(r['block'], r['pc'], 'i')[0]; top = new[i]['elems'][-1]
    tm.append({'block': r['block'], 'pc': r['pc'], 'op': r['op'], 'fromListing': r.get('touchedMemorySizeFromListing', 0), 'logged': top.get('tm'),
               'equal': r.get('touchedMemorySizeFromListing', 0) == top.get('tm')})
res['touchedMemorySize'] = {'sites': len(tm), 'equal': sum(1 for x in tm if x['equal']), 'differ': [x for x in tm if not x['equal']],
                            'nonzeroLogged': [x for x in tm if x['logged']]}
want = {int(k, 16) for k in json.load(open(C + '/031/theme-monad-gcc-real-states.work/out/value128-ops.json'))['blocks']}
sel = [s for s in new if s['b'] in want]
res['value128'] = {'states': len(sel), 'defaultTable': sum(1 for s in sel if tab(s) == DEFAULT),
                   'tables': sorted({json.dumps(tab(s)) for s in sel}),
                   'elementsWithNonzeroTouchedMemory': sum(1 for s in sel for e in s['elems'] if e.get('tm'))}
json.dump(res, open(sys.argv[1], 'w'), indent=1)
print({k: (v if not isinstance(v, list) else len(v)) for k, v in res.items() if k not in ('touchedMemorySize', 'value128')})
print('touched', {k: (v if not isinstance(v, list) else len(v)) for k, v in res['touchedMemorySize'].items()})
print('value128', {k: (v if not isinstance(v, list) else len(v)) for k, v in res['value128'].items()})
for x in res['listingTablesDiffer'][:10]: print(json.dumps(x)[:400])
