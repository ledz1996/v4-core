"""Cycle 32. The runtime helpers that the native code of the gcc 15.2.0 build of monad 0.16.7 calls for MUL, DIV, MOD
and MULMOD, interpreted from the package's objdump text in the cycle 27 x86 model (nothing from the package is run on
the CPU): monad_vm_runtime_mul 0x44e160, runtime::udiv 0x397250, runtime::umod 0x397710, runtime::mulmod 0x398a70,
and what they call: udivrem<4,4> 0x2125b0, udivrem<8,4> 0x398560, monad::mulmod 0x3988b0, knuth_div 0x212400.
Also run_seq_calls: allocdrv.run_seq for an emitted stream that contains 'call qword ptr [ROD+k]'. The 8-byte
constant at ROD+k (recorded from RoData::add<8>) is the helper address; the call runs that helper's package text in
the same CPU, so the helper's real register and memory clobbers act on the stream's live state.
usage (Task 3): python3 -I helpers.py <outdir> <n per helper> [fault]"""
import sys, os, re, random, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(HERE)
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/030/theme-monad-gcc-allocator-model.work/scripts')
import allocdrv
from allocdrv import SeqCPU, Stop, ROD, M64
import emdrv, x86emu
FN = os.path.join(W, 'out', 'fn')
HELPERS = {0x44e160: 'MUL', 0x397250: 'DIV', 0x397710: 'MOD', 0x398a70: 'MULMOD'}
HELPERS_ALL = [0x44e160, 0x397250, 0x397710, 0x398a70, 0x2125b0, 0x398560, 0x3988b0, 0x212400]
FAULT = None
HFAULTS = {
    # planted one-instruction faults in the helper text, to show the Task 3 comparison can fail
    'h-mul-drop-carry': [(0x44e160, '44e198:\tadc    r13,rax', '44e198:\tadd    r13,rax')],
    'high-limb-dropped-in-mul-helper': [(0x44e160, '44e1e3:\tadd    r13,r8', '44e1e3:\tnop')],
    'h-mul-high-limb-dropped': [(0x44e160, '44e1e3:\tadd    r13,r8', '44e1e3:\tnop')],
}


def load(a, fault=None):
    t = open(os.path.join(FN, '%016x.s' % a)).read()
    t = '\n'.join(re.sub(r'\s+<.*$', '', l) if l.startswith(' ') else l for l in t.splitlines()) + '\n'
    for fa, old, new in (fault or []):
        if fa == a:
            assert t.count(old) == 1, (hex(a), old); t = t.replace(old, new)
    return t


_HTEXT = {}
def helper_text():
    f = HFAULTS.get(FAULT)
    k = repr(f)
    if k not in _HTEXT: _HTEXT[k] = ''.join(load(a, f) for a in HELPERS_ALL)
    return _HTEXT[k]


def _chk(c): raise Stop('stack_chk_fail')
def _assert(c): raise Stop('monad_assertion_failed in helper')


class CallCPU(SeqCPU):
    """SeqCPU that follows 'call QWORD PTR [mem]' to the helper the 8-byte constant names."""
    calls = None
    def i_call(self, o, pc, n):
        s = o[0]
        if 'PTR' in s:
            t = self.get(self.opnd(s))
            if t not in HELPERS: raise Stop('indirect call to %x' % t)
            if self.calls is not None:
                self.calls.append({'helper': HELPERS[t], 'rsp_mod32': self.r['rsp'] % 32, 'rdi': self.r['rdi'], 'rsi': self.r['rsi'], 'rdx': self.r['rdx'], 'rcx': self.r['rcx']})
            self.r['rsp'] -= 8; self.write(self.r['rsp'], 8, n); return t
        return super().i_call(o, pc, n)


def run_seq_calls(m, seq, init, rnd, rbp=0x7fff00000000, rbx=0x7ffe00000000, calls=None, flags=None):
    text = allocdrv.seqtext(seq) + helper_text()
    if text not in emdrv.SCACHE: emdrv.SCACHE[text] = x86emu.Prog(text)
    c = CallCPU(emdrv.SCACHE[text], {0x6b580: _chk, 0x131ad0: _assert})
    c.calls = calls
    for r in x86emu.REG64: c.r[r] = rnd.getrandbits(64)
    for i in range(16): c.y[i] = rnd.getrandbits(256)
    for a, b in m.rod.items(): c.write(ROD + a, 1, b)
    c.r['rbp'] = rbp; c.r['rbx'] = rbx
    c.cf, c.zf, c.sf, c.of = flags if flags is not None else tuple(rnd.getrandbits(1) for _ in range(4))
    c.flags0 = (c.cf, c.zf, c.sf, c.of)
    for w, d in init:
        L = [(w >> (64 * i)) & M64 for i in range(4)]
        if 'gen' in d:
            for i in range(4): c.r[allocdrv.gp_of(d['gen'])[i]] = L[i]
        if 'avx' in d: c.y[d['avx']] = w
        if 'stack' in d:
            for i in range(4): c.write(rbp + 32 * d['stack'] + 8 * i, 8, L[i])
    c.call(0x1000, [], maxsteps=2000000)
    if c.r['rbx'] != rbx: raise Stop('reg_context not restored')
    if c.r['rbp'] != rbp: raise Stop('rbp changed')
    if c.r['rsp'] != 0x7ffff0000000: raise Stop('rsp not balanced')
    return c


# ---------------- Task 3: the helpers alone ----------------
M = (1 << 256) - 1
def run_helper(op, a, b, n=0, alias=None):
    """alias: None, or 'A', 'B', 'N': the result pointer equals that argument pointer, as the emitted calls do."""
    c = emdrv.C(x86emu.Prog(helper_text()) if 'P' not in _HTEXT else _HTEXT['P'], {0x6b580: _chk, 0x131ad0: _assert})
    R, A, B, N = 0x100000, 0x100100, 0x100200, 0x100300
    c.write(A, 32, a); c.write(B, 32, b); c.write(N, 32, n); c.write(R, 32, 0xdeadbeef * (1 + (1 << 200)))
    if alias: R = {'A': A, 'B': B, 'N': N}[alias]
    ent = {v: k for k, v in HELPERS.items()}[op]
    # caller's AVX state, to record whether the helper writes vector registers
    for i in range(16): c.y[i] = 0x5a5a << (16 * i)
    y0 = list(c.y)
    if op == 'MULMOD': c.call(ent, [R, A, B, N])
    else: c.call(ent, [R, A, B])
    return c.read(R, 32), [i for i in range(16) if c.y[i] != y0[i]], c


def ref(op, a, b, n):
    if op == 'MUL': return a * b & M
    if op == 'DIV': return a // b if b else 0
    if op == 'MOD': return a % b if b else 0
    if op == 'MULMOD': return a * b % n if n else 0


def shapes(rnd, op, N):
    """FullMath / SqrtPriceMath / SwapMath shapes (tools/opdiff/v4math.py), products at and above 2^256,
    denominators with a top limb of 0, 1 and all ones, and edge words."""
    sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
    EDGE = [0, 1, 2, 3, M, M - 1, 1 << 255, (1 << 255) - 1, (1 << 255) + 1, 1 << 64, (1 << 64) - 1, (1 << 64) + 1, 1 << 128, (1 << 128) - 1,
            (1 << 128) + 1, 1 << 192, (1 << 192) - 1, (1 << 192) + 1, 1 << 96, (1 << 96) - 1, 1 << 160, (1 << 160) - 1, 10 ** 6, 999_999, 1_000_000 - 3000,
            4295128739, 1461446703485210103287273052203988822378723970342]
    out = []
    for a in EDGE:
        for b in EDGE:
            out.append((a, b, rnd.choice(EDGE[1:])))
    def den(r):
        t = r.random()
        if t < 0.25: return r.getrandbits(r.choice([1, 32, 63, 64, 65, 96, 128, 160, 191, 192]))
        if t < 0.5: return (r.choice([0, 1, M64, 1 << 63, r.getrandbits(64)]) << 192) | r.getrandbits(192)
        if t < 0.6: return (1 << 192) | r.getrandbits(r.choice([1, 64, 128]))
        return r.getrandbits(256) | 1
    while len(out) < N:
        t = rnd.random()
        if t < 0.25:      # FullMath.mulDiv(a, b, d) with a 512-bit product: the MUL and MULMOD(a, b, ~0) words, then divisions
            a = rnd.getrandbits(rnd.choice([128, 160, 192, 224, 255, 256])); b = rnd.getrandbits(rnd.choice([96, 128, 160, 192, 256]))
            out.append((a, b, M if rnd.random() < 0.5 else den(rnd)))
        elif t < 0.45:    # SqrtPriceMath: liquidity << 96, sqrtPrice (160 bit), amounts
            L = rnd.getrandbits(128) << 96; sp = rnd.randrange(4295128739, 1461446703485210103287273052203988822378723970342)
            amt = rnd.getrandbits(rnd.choice([64, 128, 160, 255]))
            out.append(rnd.choice([(L, sp, amt * sp + L & M or 1), (L, sp - rnd.randrange(1, 1 << 64) & M, sp), (amt, sp, 1 << 96), (L, amt, sp)]))
        elif t < 0.6:     # SwapMath: amountRemaining * (1e6 - fee) / 1e6, fee amounts
            amt = rnd.getrandbits(rnd.choice([64, 127, 128, 255, 256])); fee = rnd.randrange(0, 1_000_001)
            out.append((amt, 1_000_000 - fee if fee < 1_000_000 else 1, 1_000_000))
        elif t < 0.8:     # products just above and below 2^256 and multiples of 2^64 boundaries
            k = rnd.randrange(1, 256); a = (1 << k) + rnd.choice([-1, 0, 1]) & M; b = (1 << (256 - k)) + rnd.choice([-1, 0, 1, 2]) & M
            out.append((a, b, den(rnd)))
        else:
            out.append((rnd.getrandbits(256), den(rnd), den(rnd)))
    return out[:max(N, len(out))]


def task3(outd, N):
    rnd = random.Random(3233)
    res = {'seed': 3233, 'fault': FAULT, 'helpers': {}}
    t0 = time.time()
    for op in ('MUL', 'DIV', 'MOD', 'MULMOD'):
        cases = shapes(rnd, op, N)
        mism = []; vec_touch = set(); stops = []
        for a, b, n in cases:
            if op in ('DIV', 'MOD'): n = 0
            try: got, touched, c = run_helper(op, a, b, n)
            except Stop as e:
                stops.append({'a': hex(a), 'b': hex(b), 'n': hex(n), 'stop': str(e)}); continue
            vec_touch.update(touched)
            want = ref(op, a, b, n)
            if got != want:
                mism.append({'a': hex(a), 'b': hex(b), 'n': hex(n), 'got': hex(got), 'want': hex(want)})
        amism = 0; acases = 0
        for al in (('A', 'B', 'N') if op == 'MULMOD' else ('A', 'B')):
            for a, b, n in cases[:3000]:
                if op in ('DIV', 'MOD'): n = 0
                got, _, _ = run_helper(op, a, b, n, al); acases += 1
                if got != ref(op, a, b, n):
                    amism += 1
                    if len(mism) < 200: mism.append({'alias': al, 'a': hex(a), 'b': hex(b), 'n': hex(n), 'got': hex(got), 'want': hex(ref(op, a, b, n))})
        print(op, 'aliased result pointer cases', acases, 'mismatches', amism, flush=True)
        res['helpers'][op] = {'aliasCases': acases, 'aliasMismatches': amism, 'cases': len(cases), 'mismatches': len(mism), 'mismatchRecords': mism, 'stops': stops,
                              'vectorRegsWritten': sorted(vec_touch)}
        print(op, len(cases), 'mismatches', len(mism), 'stops', len(stops), 'ymm written', sorted(vec_touch), flush=True)
    # which instructions the helpers use, and coverage
    cov = {}; mn = {}
    for a in HELPERS_ALL:
        txt = load(a)
        addrs = [int(x, 16) for x in re.findall(r'^\s+([0-9a-f]+):', txt, re.M)]
        cov['%x' % a] = [sum(1 for x in addrs if x in x86emu.VISITED), len(addrs), txt.splitlines()[0][:110]]
        for l in txt.splitlines():
            mm = re.match(r'^\s+[0-9a-f]+:\s+(\S+)', l)
            if mm: mn[mm.group(1)] = mn.get(mm.group(1), 0) + 1
    res['coverage'] = cov; res['mnemonics'] = mn; res['seconds'] = round(time.time() - t0, 1)
    json.dump(res, open(os.path.join(outd, 'helpers%s.json' % ('-' + FAULT if FAULT else '')), 'w'), indent=1)


if __name__ == '__main__':
    FAULT = sys.argv[3] if len(sys.argv) > 3 else None
    _HTEXT['P'] = x86emu.Prog(helper_text())
    task3(sys.argv[1], int(sys.argv[2]))
