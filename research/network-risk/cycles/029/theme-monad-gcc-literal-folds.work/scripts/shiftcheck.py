"""Cycle 29, Tasks 2 and 3 for the shift arms. Runs the gcc-built emitter code of monad 0.16.7 in the x86 model with
stubs (emdrv.py) for every literal shift count the PoolManager carries at a shift_by_literal site and for the 64-bit
limb boundaries, in every operand location the emitter distinguishes (general register reused as destination, general
register copied to a new destination, stack slot, AVX register). It records the decision (literal 0, identity,
emitted sequence, the 256 arm of SAR) and the instruction ids and operands handed to asmjit, rebuilds the emitted
sequence as text, runs it in the x86 model on operand words, and compares each result with pyevm.py (the reference
EVM of this review) running the single opcode.

Functions run (start address in monad 0.16.7):
  SHL  0x372dc0 shift_by_literal<SHL> with 0x39acd0 shift_avx_reg_by_literal<SHL>
  SHR  0x374090 shift_by_literal<SHR> with 0x39bf90 shift_avx_reg_by_literal<SHR>
  SAR  0x38a5d0 Emitter::sar(), which inlines shift_by_literal<SAR> and the general/stack arm, with 0x39e1d0
usage: python3 -I shiftcheck.py <outdir> [operands-per-case] [fault-name]"""
import sys, os, re, json, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emdrv import *
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import pyevm
OUT = sys.argv[1]; NOP = int(sys.argv[2]) if len(sys.argv) > 2 else 400; FAULT = sys.argv[3] if len(sys.argv) > 3 else None
M = (1 << 256) - 1
SEED = 2929

FAULTS = {  # one instruction each, as text replacements in the objdump text of the function
    'shl-limb': (0x372dc0, ('3730c6:\tmov    edx,0x3', '3730c6:\tmov    edx,0x2')),        # wrong limb index in the copy loop
    'shr-bit': (0x374090, ('37423d:\tand    eax,0x3f', '37423d:\tand    eax,0x3e')),       # bit offset off by one for odd counts
    'sar-fill': (0x38a5d0, ('38ad93:\tcall   63c6e0', '38ad93:\tnop')),                    # sign fill mov of the vacated limbs dropped
    'sar-bit': (0x38a5d0, ('38aba4:\tand    eax,0x3f', '38aba4:\tand    eax,0x3e')),        # bit offset off by one
    'shl-avx-perm': (0x39acd0, ('39ae3f:\tmov    edx,0xe4', '39ae3f:\tmov    edx,0xe5')),   # wrong lane permutation in the AVX arm
}

KIND = {'SHL': ([0x372dc0, 0x39acd0], 0x372dc0, 0x1b), 'SHR': ([0x374090, 0x39bf90], 0x374090, 0x1c),
        'SAR': ([0x38a5d0, 0x39e1d0], 0x38a5d0, 0x1d)}

world = pyevm.World({0xaa: b''})
def evm1(op, a, x):
    code = b'\x7f' + x.to_bytes(32, 'big') + b'\x7f' + a.to_bytes(32, 'big') + bytes([op]) + b'\x5f\x52\x60\x20\x5f\xf3'
    world.codes[0xaa] = code; world.jd[0xaa] = pyevm.jumpdests(code)
    ok, ret = world.call(1, 0xaa, 0, b'', False, 0)
    assert ok
    return int.from_bytes(ret, 'big')

def operands(rnd, n):
    base = [0, 1, M, 1 << 255, (1 << 255) - 1, (1 << 64) - 1, 1 << 64, 1 << 128, 1 << 192, M ^ ((1 << 64) - 1),
            (-1 << 23) & M, (-887272) & M, 887272, (-(1 << 127)) & M, (1 << 127) - 1, 1 << 159, (1 << 160) - 1]
    out = list(base)
    while len(out) < n:
        k = rnd.randrange(8)
        if k == 0: v = rnd.getrandbits(256)
        elif k == 1: v = rnd.getrandbits(256) | (1 << 255)                       # negative
        elif k == 2: v = rnd.getrandbits(64) << 192                               # only the high limb
        elif k == 3: v = rnd.getrandbits(128) << 128                              # only the two high limbs
        elif k == 4: v = (-rnd.getrandbits(rnd.randrange(1, 129))) & M            # small negative
        elif k == 5: v = rnd.getrandbits(rnd.randrange(1, 257))
        elif k == 6: v = 1 << rnd.randrange(256)
        else: v = M ^ (1 << rnd.randrange(256))
        out.append(v)
    return out

def drive(kind, count, loc, fault=None):
    fns, entry, op = KIND[kind]
    faults = {}
    if fault and FAULTS[fault][0] in fns: faults[FAULTS[fault][0]] = FAULTS[fault][1]
    pol = {}
    if loc[0] == 'reuse': pol = {'reuse': True}; val = dict(gen=loc[1])
    elif loc[0] == 'new': pol = {'dst': loc[2]}; val = dict(gen=loc[1])
    elif loc[0] == 'stack': pol = {'dst': loc[2]}; val = dict(stack=loc[1])
    else: val = dict(avx=loc[1])
    d = Drv(fns, entry, pol, faults)
    nxt = [loc[1] + 1 if loc[0] == 'avx' else 1]
    def alloc_avx(c):
        el = d.elem(avx=nxt[0] % 16); nxt[0] += 1; d.events.append('alloc_avx_reg'); d._pair(c, el)
    d.c.externs[0x36aa80] = alloc_avx
    for a in fns:
        if a in d.c.externs: del d.c.externs[a]
    v = d.elem(**val)
    if kind == 'SAR':
        s = d.elem(lit=count); d.popq = [s, v]; d.run([E]); res = d.pushed[-1]
    else:
        S = E + 0x2000; R = E + 0x3000; RET = E + 0x4000
        for i in range(4): d.c.write(S + 8 * i, 8, (count >> (64 * i)) & M64)
        d.c.write(R, 8, v); d.run([RET, E, S, R]); res = d.c.read(RET, 8)
    if res == v and not d.emitted: return d, ('identity',), None
    if res == 0xdead1000: return d, ('literal', d.lits[-1]), None
    if d.c.read(res + 0x57, 1): where = ('gen', d.table()[d.c.read(res + 0x56, 1)])
    elif d.c.read(res + 0x55, 1): where = ('avx', d.c.read(res + 0x54, 1))
    else: raise Stop('result location unknown')
    return d, ('seq',), where

def runseq(text, loc, where, x, rnd):
    if text not in SCACHE: SCACHE[text] = Prog(text)
    c = C(SCACHE[text])
    for r in REG64: c.r[r] = rnd.getrandbits(64)
    for i in range(16): c.y[i] = rnd.getrandbits(256)
    RBPV = 0x7fff00000000; c.r['rbp'] = RBPV
    L = [(x >> (64 * i)) & M64 for i in range(4)]
    if loc[0] in ('reuse', 'new'):
        for i in range(4): c.r[GPQREGS[loc[1]][i]] = L[i]
    elif loc[0] == 'stack':
        for i in range(4): c.write(RBPV + 32 * loc[1] + 8 * i, 8, L[i])
    else: c.y[loc[1]] = x
    rbp0 = c.r['rbp']
    c.call(0x1000, [])
    if where[0] == 'gen': return sum(c.r[where[1][i]] << (64 * i) for i in range(4))
    return c.y[where[1]]

REG64 = x86emu.REG64
def main():
    sa = json.load(open('/home/user/v4-core/research/network-risk/cycles/028/theme-monad-shipped-emitter.work/out/sitearms.json'))['rows']
    pm = {'SHL': set(), 'SHR': set(), 'SAR': set()}
    for r in sa:
        if r['arm'].startswith('shift_by_literal'): pm[r['op']].add(int(r['values'][0], 16))
    bound = {0, 1, 2, 7, 8, 63, 64, 65, 127, 128, 129, 191, 192, 193, 254, 255, 256, 257, 300, 511, 512, 1 << 64, (1 << 64) + 1,
             (1 << 64) + 5, 1 << 128, (1 << 128) + 255, 1 << 192, (1 << 192) | 3, 1 << 255, M}
    locs = [('reuse', 0), ('reuse', 1), ('reuse', 2), ('new', 1, 0), ('new', 2, 1), ('new', 0, 2), ('stack', 0, 0), ('stack', 7, 1), ('avx', 0), ('avx', 9)]
    rnd = random.Random(SEED)
    res = {'seed': SEED, 'fault': FAULT, 'operandsPerCase': NOP, 'cases': [], 'mismatches': [], 'decisionMismatches': []}
    nrun = 0; t0 = time.time()
    for kind in ('SHL', 'SHR', 'SAR'):
        op = KIND[kind][2]
        counts = sorted(pm[kind] | bound)
        if FAULT: counts = sorted(pm[kind] | {0, 1, 63, 64, 65, 129, 193, 255, 256})
        for cnt in counts:
            for loc in locs:
                try:
                    d, dec, where = drive(kind, cnt, loc, FAULT)
                except Stop as e:
                    res['decisionMismatches'].append({'kind': kind, 'count': hex(cnt), 'loc': loc, 'stop': str(e)}); continue
                # decision check against the v0.16.7 source rule (emitter.cpp shift_by_literal)
                want = 'identity' if cnt == 0 else ('literal' if cnt >= 256 and kind != 'SAR' else 'seq')
                if dec[0] != want or (dec[0] == 'literal' and dec[1] != 0):
                    res['decisionMismatches'].append({'kind': kind, 'count': hex(cnt), 'loc': loc, 'got': repr(dec), 'want': want})
                try:
                    emitted = [[m, [optext(o) for o in ops]] for m, ops in d.emitted]
                except Stop as e:
                    res['mismatches'].append({'kind': kind, 'count': hex(cnt), 'loc': loc, 'stop': 'operand handed to asmjit is not a register, memory or immediate: %s' % e}); continue
                case = {'kind': kind, 'count': hex(cnt), 'pmCount': cnt in pm[kind], 'loc': loc, 'decision': dec[0],
                        'events': [e if isinstance(e, str) else repr(e) for e in d.events], 'emitted': emitted, 'result': where}
                if dec[0] == 'seq':
                    text = seqtext(d.emitted); bad = 0
                    xs = operands(random.Random(SEED * 1000003 + cnt % 1000003 + 7919 * len(res['cases'])), NOP)
                    for x in xs:
                        got = runseq(text, loc, where, x, rnd); exp = evm1(op, cnt, x); nrun += 1
                        if got != exp:
                            bad += 1
                            res['mismatches'].append({'kind': kind, 'count': hex(cnt), 'loc': loc, 'x': hex(x), 'got': hex(got), 'want': hex(exp), 'seq': case['emitted']})
                    case['operands'] = len(xs); case['bad'] = bad
                elif dec[0] == 'identity' or dec[0] == 'literal':
                    for x in operands(random.Random(SEED + cnt % 999983), 50):
                        exp = evm1(op, cnt, x); got = x if dec[0] == 'identity' else dec[1]; nrun += 1
                        if got != exp: res['mismatches'].append({'kind': kind, 'count': hex(cnt), 'loc': loc, 'x': hex(x), 'got': hex(got), 'want': hex(exp), 'decision': dec[0]})
                res['cases'].append(case)
    reach = {}
    for f in [0x372dc0, 0x374090, 0x38a5d0, 0x39acd0, 0x39bf90, 0x39e1d0]:
        txt = load_fn(f); addrs = [int(m, 16) for m in re.findall(r'^\s+([0-9a-f]+):', txt, re.M)]
        reach['%x' % f] = [sum(1 for a in addrs if a in x86emu.VISITED), len(addrs)]
    res['instructionCoverage'] = reach
    res['runs'] = nrun; res['seconds'] = round(time.time() - t0, 1)
    res['pmCounts'] = {k: sorted(v) for k, v in pm.items()}
    name = 'shiftcheck%s.json' % ('-' + FAULT if FAULT else '')
    json.dump(res, open(os.path.join(OUT, name), 'w'), indent=0)
    print(name, 'cases', len(res['cases']), 'runs', nrun, 'mismatches', len(res['mismatches']), 'decision', len(res['decisionMismatches']), res['seconds'], 's')
    for m in (res['decisionMismatches'] + res['mismatches'])[:5]: print(m)
main()
