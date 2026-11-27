"""Cycle 30, Task 1: alloc_or_release_general_reg<> (0x36b020, empty live set) and
alloc_or_release_general_reg<RcPtr> (0x39a300, one live element) of the gcc 15.2.0 build, run alone in the x86
model on random Stack states, against the rule of emitter.cpp:1204-1216 at v0.16.7: when the element is live
(on the EVM stack, or the live element) and either a general register is free or the element is held only in a
general register, a new register is allocated (spilling if needed) and the element keeps its own; otherwise the
element's register is released to a fresh element. Also checks the Stack bookkeeping after the call and that a
spill store, when emitted, writes the spilled element's own row to its recorded stack offset.
usage: python3 -I aorel.py <outdir> <ncases>"""
import sys, os, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from allocdrv import *
OUT = sys.argv[1]; NC = int(sys.argv[2]); SEED = 3034
rnd = random.Random(SEED)
res = {'seed': SEED, 'cases': 0, 'bad': [], 'stops': [], 'byRule': {}}
for n in range(NC):
    fn = rnd.choice([0x36b020, 0x39a300])
    m = Model([fn], {})
    rows = [0, 1, 2]; rnd.shuffle(rows)
    er = rows[0]
    d = {'gen': er}
    if rnd.random() < 0.3: d['stack'] = rnd.randrange(0, 8)
    if rnd.random() < 0.25: d['avx'] = 4
    if rnd.random() < 0.15: d['lit'] = rnd.getrandbits(256)
    onstack = rnd.random() < 0.5
    e = m.elem(1 + int(onstack), indices=[3] if onstack else [], gen=er, avx=d.get('avx'), stack=d.get('stack'), lit=d.get('lit'))
    others = []
    for r in rows[1:]:
        if rnd.random() < 0.6:
            o = {'gen': r}
            if rnd.random() < 0.3: o['stack'] = 10 + r
            others.append((m.elem(1, indices=[5 + r], gen=r, stack=o.get('stack')), o))
    islive_elem = fn == 0x39a300 and rnd.random() < 0.4
    live = m.alloc(8)
    if fn == 0x39a300:
        lb = e if islive_elem else (others[0][0] if others and rnd.random() < 0.5 else m.elem(1))
        if lb != e: m.c.write(lb, 8, m.c.read(lb, 8) + 1)
        else: m.c.write(e, 8, m.c.read(e, 8) + 1)
        m.c.write(live, 8, lb)
    used = {d.get('stack')} | {o.get('stack') for _, o in others}
    m.set_available([x for x in range(0, 16) if x not in used])
    held = {er} | {o['gen'] for _, o in others}
    m.set_free_general([r for r in range(3) if r not in held])
    m.set_free_avx([r for r in range(16) if r != 4])
    pe = m.alloc(8); m.c.write(pe, 8, e); out = m.alloc(16)
    free_before = len(m.free_general()) > 0
    is_live = onstack or islive_elem
    only_gen = 'stack' not in d and 'avx' not in d and 'lit' not in d
    want_alloc = is_live and (free_before or only_gen)
    try:
        m.c.call(fn, [out, E, pe] + ([live] if fn == 0x39a300 else [0]), maxsteps=200000)
    except Stop as ex:
        res['stops'].append({'case': n, 'stop': str(ex)}); continue
    rb = m.c.read(out, 8); rl = m.loc(rb); el = m.loc(e)
    rule = '%s/live%d/free%d/onlygen%d' % (hex(fn), int(is_live), int(free_before), int(only_gen))
    res['byRule'][rule] = res['byRule'].get(rule, 0) + 1
    bad = []
    if 'gen' not in rl: bad.append('result has no general register')
    if want_alloc:
        if rb == e: bad.append('reused the live element')
        if el.get('gen') != er: bad.append('live element lost its register')
        if rl.get('gen') == el.get('gen'): bad.append('result shares the live element register')
    else:
        if rl.get('gen') != er: bad.append('did not take the released register')
        if 'gen' in el and rb != e: bad.append('released element still records the register')
    liveb = [b for b, _ in others if m.loc(b)['onstack']] + ([e] if el['onstack'] else []) + [rb]
    bad += m.invariants(list(dict.fromkeys(liveb)))
    # spill stores, if any, must store each limb of the spilled row to the recorded offset
    for b, o in others:
        lo = m.loc(b)
        if 'gen' not in lo and 'stack' in lo and 'stack' not in o:
            stores = [(mn, ops) for mn, ops in m.emitted if mn == 'mov' and ops[0][0] == 'mem']
            want = [('mem', 'rbp', None, 32 * lo['stack'] + 8 * i) for i in range(4)]
            got = [(ops[0][0], ops[0][1], ops[0][2], ops[0][3]) for _, ops in stores]
            src = [ops[1][1] for _, ops in stores]
            if got != want or src != GPQREGS[o['gen']]: bad.append('spill stores %r from %r' % (got, src))
    if bad: res['bad'].append({'case': n, 'rule': rule, 'bad': bad, 'emitted': repr(m.emitted)[:600]})
    res['cases'] += 1
cov = {}
for f in (0x36b020, 0x39a300, 0x36ae40, 0x3ad770, 0x3ad250, 0x3aac30, 0x3ac870, 0x3ac7f0, 0x3adc00):
    txt = load_fn(f); addrs = [int(a, 16) for a in re.findall(r'^\s+([0-9a-f]+):', txt, re.M)]
    cov['%x' % f] = [sum(1 for a in addrs if a in x86emu.VISITED), len(addrs)]
res['instructionCoverage'] = cov
json.dump(res, open(os.path.join(OUT, 'aorel.json'), 'w'), indent=0)
print('cases', res['cases'], 'bad', len(res['bad']), 'stops', len(res['stops'])); print(res['byRule']); print(res['bad'][:3]); print(cov)
