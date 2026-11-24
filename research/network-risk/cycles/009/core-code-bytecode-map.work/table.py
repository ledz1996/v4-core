"""Assign every range of the runtime to a function and list the ranges no script executes.
Dispatcher code (outside any Yul function with an entry point) is labelled with the
external functions whose selector case reaches it in a static walk of the control flow.
Usage: python3 -I table.py <full.json> <instrs.json> <coverage-full.json> <out.json>"""
import sys, json, collections
full, fi, fc, out = sys.argv[1:5]
b = json.load(open(full)); ins = json.load(open(fi)); cov = set(json.load(open(fc))['cover'])
sel2name = {v: k.split('(')[0] + ('' if k.count(',') == 0 and k.endswith('()') else '') for k, v in b['methodIdentifiers'].items()}
sel2sig = {v: k for k, v in b['methodIdentifiers'].items()}
pcs = [e['pc'] for e in ins]; idx = {e['pc']: k for k, e in enumerate(ins)}
jd = {e['pc'] for e in ins if e['op'] == 'JUMPDEST'}
entry = {v['entryPoint'] for v in b['functionDebugData'].values() if v.get('entryPoint') is not None}
# blocks
blocks = {}; start = 0
for k, e in enumerate(ins):
    if e['op'] == 'JUMPDEST' and k != start:
        blocks[ins[start]['pc']] = (start, k - 1); start = k
    if e['op'] in ('JUMP', 'JUMPI', 'STOP', 'RETURN', 'REVERT', 'INVALID') or e['src'] == 'data':
        blocks[ins[start]['pc']] = (start, k); start = k + 1
    if start >= len(ins): break
def succ(bpc):
    s, t = blocks[bpc]; out = set()
    for k in range(s, t + 1):
        e = ins[k]
        if e['op'] == 'PUSH2' and int(e['imm'], 16) in jd: out.add(int(e['imm'], 16))
    last = ins[t]['op']
    if last not in ('JUMP', 'STOP', 'RETURN', 'REVERT', 'INVALID') and t + 1 < len(ins): out.add(ins[t + 1]['pc'])
    return out
# selector cases: PUSH4 sel ... EQ PUSH2 tag JUMPI in the dispatcher
cases = {}
for k, e in enumerate(ins[:700]):
    if e['op'] in ('PUSH3', 'PUSH4') and e['imm'].rjust(8, '0') in sel2sig:
        e = dict(e, imm=e['imm'].rjust(8, '0'))
        for j in range(k + 1, k + 6):
            if ins[j]['op'] == 'PUSH2' and ins[j + 1]['op'] == 'JUMPI': cases[e['imm']] = int(ins[j]['imm'], 16); break
owner = collections.defaultdict(set)
for sel, tag in cases.items():
    seen = set(); st = [tag]
    while st:
        p = st.pop()
        if p in seen or p not in blocks: continue
        seen.add(p)
        if p in entry and p != tag: owner[p].add(sel); continue   # call into a Yul function: record, do not walk its body here
        for q in succ(p): st.append(q)
    for p in seen: owner[p].add(sel)
# label per instruction
blk_of = {}
for bpc, (s, t) in blocks.items():
    for k in range(s, t + 1): blk_of[k] = bpc
def label(k):
    e = ins[k]
    if e['src'] == 'data': return 'data (end marker 0xfe and CBOR metadata)'
    if e['yul'] != '<entry/dispatcher>':
        return 'yul ' + e['yul']
    o = owner.get(blk_of.get(k), set())
    if k < 200 and not o: return 'dispatcher (selector switch)'
    if len(o) == 1: return 'external ' + sel2sig[next(iter(o))]
    if len(o) == 0: return 'dispatcher: unreached in static walk'
    return 'shared by %d external functions' % len(o)
rows = []
for k, e in enumerate(ins):
    lab = label(k)
    fn = e['fn'] if not e['fn'].startswith('<') else '-'
    key = (lab, fn)
    c = e['pc'] in cov
    if rows and rows[-1]['key'] == key:
        r = rows[-1]; r['end'] = e['pc']; r['n'] += 1; r['covered'] += c
    else: rows.append({'key': key, 'start': e['pc'], 'end': e['pc'], 'n': 1, 'covered': int(c)})
# coarse table: merge consecutive rows with the same top label
coarse = []
for r in rows:
    if coarse and coarse[-1]['owner'] == r['key'][0]:
        c = coarse[-1]; c['end'] = r['end']; c['instructions'] += r['n']; c['covered'] += r['covered']
        if r['key'][1] != '-' and r['key'][1] not in c['source']: c['source'].append(r['key'][1])
    else: coarse.append({'start': r['start'], 'end': r['end'], 'owner': r['key'][0], 'instructions': r['n'], 'covered': r['covered'], 'source': [] if r['key'][1] == '-' else [r['key'][1]]})
# uncovered runs with attribution
unc = []; cur = None
for k, e in enumerate(ins):
    if e['pc'] not in cov:
        if cur is None: cur = {'start': e['pc'], 'end': e['pc'], 'n': 0, 'owners': collections.Counter(), 'src': collections.Counter(), 'ops': collections.Counter()}
        cur['end'] = e['pc']; cur['n'] += 1; cur['owners'][label(k)] += 1; cur['src'][e['src'].split('-')[0]] += 1; cur['ops'][e['op']] += 1
    elif cur: unc.append(cur); cur = None
if cur: unc.append(cur)
unc_out = [{'start': u['start'], 'end': u['end'], 'instructions': u['n'], 'owners': dict(u['owners']), 'sourceLines': dict(u['src'].most_common(6)),
            'notableOps': {o: c for o, c in u['ops'].items() if o in ('MULMOD', 'SDIV', 'SMOD', 'SAR', 'BYTE', 'DIV', 'MOD', 'SIGNEXTEND', 'SLT', 'SGT', 'SSTORE', 'SLOAD', 'TSTORE', 'TLOAD', 'CALL', 'STATICCALL', 'CALLER', 'CALLVALUE', 'SELFBALANCE', 'MCOPY', 'LOG1', 'LOG2', 'LOG3', 'LOG4', 'KECCAK256')}} for u in unc]
byowner = collections.Counter(); byowner_cov = collections.Counter()
for k, e in enumerate(ins):
    l = label(k); byowner[l] += 1; byowner_cov[l] += e['pc'] in cov
json.dump({'cases': {sel2sig[s]: t for s, t in cases.items()}, 'coarse': coarse, 'fine': [{'start': r['start'], 'end': r['end'], 'owner': r['key'][0], 'sourceFunction': r['key'][1], 'instructions': r['n'], 'covered': r['covered']} for r in rows],
           'perOwner': {o: {'instructions': n, 'covered': byowner_cov[o]} for o, n in byowner.most_common()}, 'uncovered': unc_out,
           'uncoveredInstructions': sum(u['n'] for u in unc)}, open(out, 'w'), indent=1)
print(len(cases), 'selector cases;', len(coarse), 'coarse ranges;', len(rows), 'fine ranges;', len(unc), 'uncovered runs,', sum(u['n'] for u in unc), 'instructions')
for o, n in byowner.most_common(): print('%5d %5d  %s' % (n, byowner_cov[o], o))
