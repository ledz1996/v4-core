"""Cycle 30, Task 1: Emitter::write_to_final_stack_offsets (0x3816e0) of the gcc 15.2.0 build, the block-exit
routine that moves every element of the virtual stack to the stack offset of each EVM stack index it occupies,
resolving the cycles that arise when an element sits in another element's final offset. It runs in the x86 model
with Stack::get, alloc_avx_reg, find_stack_elem_for_avx_reg_spill, spill_avx_reg, move_avx_reg,
remove_stack_offset, free_stack_offset, mov_literal_to_ymm and both mov_words_to_ymm instances lifted
(allocdrv.py lists the rest). The emitted sequence is then run, and for every index i from min_delta to top_index
the 32 bytes at rbp + 32*i must equal the word of the element at index i. Stack states are random: elements in
general registers, AVX registers, stack offsets (including other elements' final offsets, which makes chains and
cycles), literals, shared by several indices (DUP), with and without a free AVX register.
usage: python3 -I wfso.py <outdir> <ncases> <nwords> [fault]"""
import sys, os, json, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from allocdrv import *
OUT = sys.argv[1]; NC = int(sys.argv[2]); NW = int(sys.argv[3]); FAULT = sys.argv[4] if len(sys.argv) > 4 else None
SEED = 3033
M = (1 << 256) - 1
FNS = [0x3816e0, 0x3ab8f0, 0x3ada90, 0x3aded0, 0x381340, 0x398b40, 0x398c80, 0x3ac400, 0x36aa80, 0x3ad620, 0x3ad070,
       0x3aaa40, 0x3ac590, 0x3ac620, 0x3694d0, 0x3977a0, 0x3977d0]


class W(Model):
    def __init__(self, faults):
        super().__init__(FNS, faults)
        self.c.externs.update({0x3810b0: self.add4, 0x3a3860: self.add16})
        fs = self.alloc(4 * 1100); self.c.write(E + 0x668, 8, fs)
    def add4(self, c):
        x = c.r['rdx'] & 0xffffffff; self.rodconst.append(('add4', x)); self._rodata(c, x.to_bytes(4, 'little'), 4, 4)
    def add16(self, c):
        x = c.read(c.r['rdx'], 16); self.rodconst.append(('add16', x)); self._rodata(c, x.to_bytes(16, 'little'), 16, 16)
    def set_stack(self, mind, slots):
        """slots: block pointers for indices mind..mind+len-1."""
        pv = self.alloc(8 * 64); nv = self.alloc(8 * 64)
        for k, b in enumerate(slots):
            i = mind + k
            if i >= 0: self.c.write(pv + 8 * i, 8, b)
            else: self.c.write(nv + 8 * (-i - 1), 8, b)
        top = mind + len(slots) - 1
        npos = max(top + 1, 0); nneg = max(-mind, 0)
        self.c.write(S + 0x158, 8, pv); self.c.write(S + 0x160, 8, pv + 8 * npos); self.c.write(S + 0x168, 8, pv + 8 * 64)
        self.c.write(S + 0x140, 8, nv); self.c.write(S + 0x148, 8, nv + 8 * nneg); self.c.write(S + 0x150, 8, nv + 8 * 64)
        self.c.write(S + 8, 4, top & 0xffffffff); self.c.write(S + 0xc, 4, mind & 0xffffffff)
        self.c.write(S + 0x10, 4, (top + 4) & 0xffffffff)


def scenario(rnd):
    mind = -rnd.randrange(0, 5)
    n = rnd.randrange(1, 18)
    nelem = rnd.randrange(1, n + 1)
    owner = list(range(nelem)) + [rnd.randrange(nelem) for _ in range(n - nelem)]
    rnd.shuffle(owner)
    gens = [0, 1, 2]; rnd.shuffle(gens)
    full_avx = rnd.random() < 0.3
    avxs = list(range(16)); rnd.shuffle(avxs)
    offs = list(range(mind, mind + n + 6)); rnd.shuffle(offs)
    els = []
    for e in range(nelem):
        d = {}
        if rnd.random() < 0.55 and offs: d['stack'] = offs.pop()
        if rnd.random() < 0.3 and avxs: d['avx'] = avxs.pop()
        if rnd.random() < 0.2 and gens: d['gen'] = gens.pop()
        if rnd.random() < 0.12: d['lit'] = rnd.choice([0, M, 1, rnd.getrandbits(256), rnd.getrandbits(64), 1 << 255])
        if not d: d['stack'] = offs.pop() if offs else None
        if d.get('stack') is None and 'stack' in d: d.pop('stack'); d['avx'] = avxs.pop()
        els.append(d)
    if full_avx:
        # every AVX register held by some element on the stack, so the routine must spill one first
        while avxs:
            els.append({'avx': avxs.pop()}); owner.insert(rnd.randrange(len(owner) + 1), len(els) - 1)
    return {'mind': mind, 'owner': owner, 'els': els, 'extraAvx': [], 'fullAvx': full_avx}


def main():
    rnd = random.Random(SEED + (sum(map(ord, FAULT)) if FAULT else 0))
    out = {'seed': SEED, 'fault': FAULT, 'cases': 0, 'runs': 0, 'stops': [], 'bad': [], 'nBadRuns': 0, 'paths': {}}
    t0 = time.time()
    for n in range(NC):
        sc = scenario(rnd)
        m = W(dict(FAULTS_LIVE) if FAULT else {})
        mind = sc['mind']; owner = sc['owner']
        idx = {}
        for k, e in enumerate(owner): idx.setdefault(e, []).append(mind + k)
        blocks = []
        for e, d in enumerate(sc['els']):
            blocks.append(m.elem(len(idx[e]), gen=d.get('gen'), avx=d.get('avx'), stack=d.get('stack'), lit=d.get('lit'), indices=idx[e]))
        # extra AVX holders not on the stack (held by an outside reference) when the AVX file is full
        for d in sc['extraAvx']: m.elem(1, avx=d['avx'])
        used = {d['stack'] for d in sc['els'] if 'stack' in d}
        m.set_available([o for o in range(mind, mind + len(owner) + 8) if o not in used])
        m.set_free_general([r for r in range(3) if r not in {d.get('gen') for d in sc['els']}])
        held = {d.get('avx') for d in sc['els']} | {d['avx'] for d in sc['extraAvx']}
        m.set_free_avx([r for r in range(16) if r not in held])
        m.set_stack(mind, [blocks[e] for e in owner])
        try:
            m.c.call(0x3816e0, [E], maxsteps=3000000)
        except Stop as e:
            out['stops'].append({'case': n, 'sc': repr(sc), 'stop': str(e)}); continue
        cyc = sum(1 for e, d in enumerate(sc['els']) if 'stack' in d and d['stack'] in [mind + k for k, o in enumerate(owner) if o != e])
        path = 'n%d/elems%d/dep%d/fullavx%d' % (min(len(owner), 9), min(len(sc['els']), 9), min(cyc, 3), int(sc['fullAvx']))
        out['paths'][path] = out['paths'].get(path, 0) + 1
        seq = m.emitted
        for w_i in range(NW):
            words = [d['lit'] if 'lit' in d else rnd.getrandbits(256) for d in sc['els']]
            init = [(words[e], d) for e, d in enumerate(sc['els'])]
            for d in sc['extraAvx']: init.append((rnd.getrandbits(256), d))
            try: c = run_seq(m, seq, init, rnd)
            except Stop as e:
                out['bad'].append({'case': n, 'why': 'seq stop ' + str(e), 'seq': seqtext(seq)}); out['nBadRuns'] += 1; break
            out['runs'] += 1
            for k, e in enumerate(owner):
                i = mind + k
                got = word_at(c, {'stack': i})['stack']
                if got != words[e]:
                    out['nBadRuns'] += 1
                    if len(out['bad']) < 60:
                        out['bad'].append({'case': n, 'sc': repr(sc), 'index': i, 'got': hex(got), 'want': hex(words[e]), 'seq': seqtext(seq)})
                    break
        out['cases'] += 1
    cov = {}
    for f in FNS:
        txt = load_fn(f); addrs = [int(a, 16) for a in re.findall(r'^\s+([0-9a-f]+):', txt, re.M)]
        cov['%x' % f] = [sum(1 for a in addrs if a in x86emu.VISITED), len(addrs)]
    out['instructionCoverage'] = cov
    out['seconds'] = round(time.time() - t0, 1)
    name = 'wfso%s.json' % ('-' + FAULT if FAULT else '')
    json.dump(out, open(os.path.join(OUT, name), 'w'), indent=0)
    import collections
    print(name, 'cases', out['cases'], 'runs', out['runs'], 'stops', len(out['stops']), 'badRuns', out['nBadRuns'], out['seconds'], 's')
    print(collections.Counter(s['stop'][:70] for s in out['stops']).most_common(6))
    for x in out['bad'][:2]: print(str(x)[:1800])


FAULTS_LIVE = {}
if FAULT:
    F = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'faults.json')))
    for a, old, new in F[FAULT]: FAULTS_LIVE.setdefault(int(a, 16), []).append((old, new))
main()
