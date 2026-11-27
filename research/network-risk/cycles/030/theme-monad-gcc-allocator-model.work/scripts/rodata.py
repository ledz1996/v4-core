"""Cycle 30, Task 3: RoData's deduplication map in the gcc 15.2.0 build. RoData::add32 (0x375c50) with the
unordered_map emplace (0x39d250) and node insert/rehash (0x39d080) run from their own code in the x86 model.
Stubs by specification: operator new/delete, memset, and _Prime_rehash_policy::_M_need_rehash (libstdc++), which
asks for a rehash to the next bucket count of a fixed prime list once elements exceed buckets, so the bucketed
lookup path and the rehash relinking run too.
The constants are the 32-byte words the emitter adds for the PoolManager's literals (cycle 28 sitearms.json and the
non-literal shift constants), plus words built to share the map's hash (the xor of the four 64-bit limbs): limb
permutations, and pairs that differ in two limbs by the same xor mask. Check: two different words never get one
label, a repeated word always gets its first label, and the data vector holds each word at its label.
usage: python3 -I rodata.py <outdir> [fault]"""
import sys, os, json, random, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from allocdrv import load_fn, Prog, Stop, IMG, x86emu
import emdrv
from emdrv import C
OUT = sys.argv[1]; FAULT = sys.argv[2] if len(sys.argv) > 2 else None
M64 = (1 << 64) - 1
SEED = 3032
PRIMES = [1, 13, 29, 59, 127, 257, 541, 1109, 2357, 5087]
FAULTS = {'eq-low-half': (0x39d250, '39d306:\tvmovdqu ymm0,YMMWORD PTR [rsi]', '39d306:\tvmovdqu xmm0,XMMWORD PTR [rsi]')}


class CPU(C):
    def i_vpsrldq(self, o, pc, n):
        d = self.opnd(o[0]); W = self._vw(d); a = self.get(self.opnd(o[1]), W); k = int(o[2], 0)
        lanes = [(a >> (128 * i)) & ((1 << 128) - 1) for i in range(W // 128)]
        self.put(d, sum(((x >> (8 * k)) if k < 16 else 0) << (128 * i) for i, x in enumerate(lanes)))


class R:
    def __init__(self, fault=None):
        fs = {}
        if fault:
            a, old, new = FAULTS[fault]; fs[a] = [(old, new)]
        self.p = Prog(''.join(load_fn(a, fs.get(a)) for a in (0x375c50, 0x39d250, 0x39d080)))
        self.c = CPU(self.p, {0x6b2e0: self.new, 0x6b1f0: lambda c: None, 0x6b5e0: self.memset, 0x6c440: self.need_rehash,
                              0x6b580: self.fail, 0x131ad0: self.fail})
        self.heap = 0x600000000; self.rehashes = 0
        self.RD = 0x500000000 + 0x4e0
        c = self.c
        for i in range(0, 0x80, 8): c.write(self.RD + i, 8, 0)
        c.write(self.RD + 4, 4, 0x77)
        v = self.alloc(32 * 4); c.write(self.RD + 0x18, 8, v); c.write(self.RD + 0x20, 8, v); c.write(self.RD + 0x28, 8, v + 32 * 4)
        H = self.RD + 0x30
        c.write(H, 8, H + 0x30); c.write(H + 8, 8, 1); c.write(H + 0x10, 8, 0); c.write(H + 0x18, 8, 0)
        c.write(H + 0x20, 4, 0x3f800000); c.write(H + 0x28, 8, 0); c.write(H + 0x30, 8, 0)
    def fail(self, c): raise Stop('assert or stack check')
    def alloc(self, n):
        a = self.heap; self.heap += (n + 63) // 64 * 64 + 64
        for i in range(n): self.c.mem[a + i] = 0
        return a
    def new(self, c): c.r['rax'] = self.alloc(c.r['rdi'])
    def memset(self, c):
        for i in range(c.r['rdx']): c.mem[c.r['rdi'] + i] = c.r['rsi'] & 0xff
        c.r['rax'] = c.r['rdi']
    def need_rehash(self, c):
        # pair<bool, size_t> _M_need_rehash(size_t n_bkt, size_t n_elt, size_t n_ins): returned in rax:rdx
        nb, ne, ni = c.r['rsi'], c.r['rdx'], c.r['rcx']
        if ne + ni > nb:
            nxt = next(p for p in PRIMES if p > ne + ni); self.rehashes += 1
            c.r['rax'] = 1; c.r['rdx'] = nxt
        else:
            c.r['rax'] = 0; c.r['rdx'] = 0
    def add32(self, x):
        c = self.c; key = self.alloc(32); res = self.alloc(16)
        for i in range(4): c.write(key + 8 * i, 8, (x >> (64 * i)) & M64)
        c.call(0x375c50, [res, self.RD, key], maxsteps=200000)
        sig = c.read(res, 4); off = c.read(res + 12, 4)
        return off, sig
    def data(self):
        b, e = self.c.read(self.RD + 0x18, 8), self.c.read(self.RD + 0x20, 8)
        return [sum(self.c.read(a + 8 * i, 8) << (64 * i) for i in range(4)) for a in range(b, e, 32)]


def words():
    rnd = random.Random(SEED)
    R0 = '/home/user/v4-core/research/network-risk'
    pm = set()
    for r in json.load(open(R0 + '/cycles/028/theme-monad-shipped-emitter.work/out/sitearms.json'))['rows']:
        for v in r['values']:
            if v: pm.add(int(v, 16))
    pm |= {0x0000000700000006000000050000000400000003000000020000000100000000 >> 0,
           (0x0200000001) | (0x0400000003 << 64) | (0x0600000005 << 128) | (0x0800000007 << 192),
           (0x0100000000) | (0x0300000002 << 64) | (0x0500000004 << 128) | (0x0700000006 << 192), 256, 0, (1 << 256) - 1}
    ws = sorted(pm)
    extra = []
    for _ in range(60):
        L = [rnd.getrandbits(64) for _ in range(4)]
        for perm in ([1, 0, 2, 3], [3, 2, 1, 0], [2, 3, 0, 1], [0, 1, 3, 2]):
            extra.append(sum(L[p] << (64 * i) for i, p in enumerate(perm)))
        m = rnd.getrandbits(64)
        extra.append(sum(x << (64 * i) for i, x in enumerate([L[0] ^ m, L[1] ^ m, L[2], L[3]])))
        extra.append(sum(x << (64 * i) for i, x in enumerate([L[0], L[1], L[2] ^ m, L[3] ^ m])))
    for w in list(ws[:40]):
        L = [(w >> (64 * i)) & M64 for i in range(4)]
        extra.append(sum(L[p] << (64 * i) for i, p in enumerate([1, 0, 3, 2])))
        extra.append(w ^ (1 << 255) ^ (1 << 191))     # same limb xor, different word
        m = rnd.getrandbits(64)
        extra.append(w ^ (m << 128) ^ (m << 192))      # same low half and same limb xor
    return ws, extra


def main():
    ws, extra = words()
    rnd = random.Random(SEED + 1)
    seq = ws + extra
    seq = seq + rnd.sample(seq, len(seq) // 2)       # repeats
    rnd.shuffle(seq)
    r = R(FAULT)
    label = {}; bad = []; byoff = {}
    for x in seq:
        try: off, sig = r.add32(x)
        except Stop as e: bad.append({'word': hex(x), 'stop': str(e)}); break
        if x in label and label[x] != off: bad.append({'word': hex(x), 'why': 'repeat got a new label', 'first': label[x], 'now': off})
        if x not in label: label[x] = off
        if off in byoff and byoff[off] != x: bad.append({'word': hex(x), 'why': 'label shared with a different word', 'other': hex(byoff[off]), 'off': off})
        byoff.setdefault(off, x)
    d = r.data()
    for x, off in label.items():
        if off % 32 or off // 32 >= len(d) or d[off // 32] != x: bad.append({'word': hex(x), 'why': 'data at label differs', 'off': off})
    hashes = {}
    for x in label:
        h = 0
        for i in range(4): h ^= (x >> (64 * i)) & M64
        hashes.setdefault(h, []).append(x)
    coll = sum(1 for v in hashes.values() if len(v) > 1)
    fns = [0x375c50, 0x39d250, 0x39d080]
    cov = {}
    for f in fns:
        txt = load_fn(f); addrs = [int(a, 16) for a in re.findall(r'^\s+([0-9a-f]+):', txt, re.M)]
        cov['%x' % f] = [sum(1 for a in addrs if a in x86emu.VISITED), len(addrs)]
    out = {'seed': SEED, 'fault': FAULT, 'calls': len(seq), 'distinctWords': len(label), 'pmWords': len(ws),
           'hashCollidingGroups': coll, 'rehashes': r.rehashes, 'dataWords': len(d), 'bad': bad[:50], 'nBad': len(bad), 'instructionCoverage': cov}
    json.dump(out, open(os.path.join(OUT, 'rodata%s.json' % ('-' + FAULT if FAULT else '')), 'w'), indent=0)
    print({k: v for k, v in out.items() if k != 'bad'}); print(bad[:2])
main()
