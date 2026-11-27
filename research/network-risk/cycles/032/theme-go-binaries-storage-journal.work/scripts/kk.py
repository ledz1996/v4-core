"""Cycle 32 task 3 (L-1225): bor v2.11.2's 64-byte keccak cache in core/vm.opKeccak256, run from the shipped amd64 and
arm64 binaries (cycle 31 downloads, read as data only) in the cycle 31 x86-64 and AArch64 models.

Run from the binary: core/vm.opKeccak256, (*BoundedCache[go.shape.[64]uint8,go.shape.[32]uint8]).Load and .Store,
holiman/uint256.(*Int).SetBytes and its callees. Stubbed in Python: sync.(*Map).Load and
internal/sync.(*HashTrieMap[...]).LoadOrStore (one dict per cache, keyed by the key type pointer and the full bytes the
boxed key points to, the stored value kept as the boxed pointer the binary hands over, exactly as an interface value
is kept by the real map), runtime.convTnoptr (copies type.Size_ bytes, as the runtime does), runtime.memmove, and the
three hasher interface methods Reset, Write and Read at the itab offsets opKeccak256 calls (0x28, 0x40, 0x20), which
compute Keccak-256 in Python. The EVM fields used are read from the disassembly: Config.Keccak256Cache at evm+0x138,
Config.EnablePreimageRecording at evm+0x101 (left 0), hasher interface at evm+0x170, hasherBuf at evm+0x180;
BoundedCache.count at +0x30 and maxSize at +0x38.

Two workers (two EVM objects, each with its own hasherBuf and hasher) share one cache, as the BlockSTM V2 workers and
the prefetcher share sharedBlockCaches.keccak (core/blockchain.go:1268-1289 at v2.11.2). Random interleavings of the
two workers hash 64-byte inputs of the PoolManager's mapping shapes, near-collisions of them (one bit or one byte
apart, last 8 bytes apart), and inputs of other lengths that overwrite a worker's hasherBuf between its Store and the
other worker's Load. Every result must equal Keccak-256 of the input.
usage: python3 -I kk.py <arch> <nseq> <out.json> [fault]   seed 32_1225_01
"""
import json, os, random, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tsgo as T
from tsgo import Stop, AStop, G, targets, XProg, AProg, rewrite_rip, x86emu, M64
from evm import keccak

SEED = 32_1225_01
VMP = 'github.com/ethereum/go-ethereum/core/vm.'
LOAD = VMP + '(*BoundedCache[go.shape.[64]uint8,go.shape.[32]uint8]).Load'
STORE = VMP + '(*BoundedCache[go.shape.[64]uint8,go.shape.[32]uint8]).Store'
HT = 'internal/sync.(*HashTrieMap[go.shape.interface {},go.shape.interface {}]).LoadOrStore'
SMLOAD = 'sync.(*Map).Load'
B = T.BASE
SCOPE, STACKOBJ, MEMOBJ, MEMDATA, PCPTR = B, B + 0x1000, B + 0x9000, B + 0xa000, B + 0xf000
EVMS = [B + 0x20000, B + 0x21000]
HOBJ = [B + 0x22000, B + 0x22100]
ITAB = B + 0x23000
CACHE = B + 0x24000
FAKE = 0x7e000000  # addresses of the stubbed hasher methods

# planted faults (task 5): the cache key handed to Load and Store loses its last 8 bytes
PLANT = {'key_last8': {'amd64': [(0xb4da78, 'movq   xmm14,QWORD PTR [rax+0x30]'), (0xb4dc68, 'movq   xmm14,QWORD PTR [rbx+0x30]')],
                       'arm64': [(0xa42ea0, 'stp\tx12, xzr, [sp, #0xa8]')]},
         # Store is handed a pointer-sized view of hasherBuf: the value word copied is zeroed (caught as wrong hash)
         'store_zero_value': {'amd64': [(0xb4dc32, 'pxor   xmm14,xmm14')], 'arm64': [(0xa42fdc, 'ldp\tx2, x3, [x1, #0x1a0]')]}}


class KModel:
    def __init__(self, arch, fault='none'):
        self.arch = arch
        t = targets.get('bor-' + arch)
        self.bin = t['bin']
        self.img = T.Img(self.bin)
        self.fns = G.fnlist(t['fns'])
        self.byaddr = {v[0]: k for k, v in self.fns.items()}
        names = [VMP + 'opKeccak256', LOAD, STORE] + [n for n in self.fns if n.startswith('github.com/holiman/uint256.(*Int).SetBytes')]
        text = G.disasm(self.bin, arch, [self.fns[n] for n in names])
        if fault != 'none':
            for a, ins in PLANT[fault][arch]:
                pat = re.compile(r'^(\s*%x:\s+).*$' % a, re.M)
                text, k = pat.subn(lambda m: m.group(1) + ins, text)
                assert k == 1, (fault, hex(a))
        self.text = text
        self.names = names
        self.entries = {self.fns[n][0] for n in names}
        sym = T.nm_symbols(self.bin)
        self.dict_ = sym['github.com/ethereum/go-ethereum/core/vm..dict.BoundedCache[[64]uint8,github.com/ethereum/go-ethereum/common.Hash]']
        self.prog = XProg(rewrite_rip(text)) if arch == 'amd64' else AProg([text])
        self.visited = set()

    def regs(self, c, n):
        if self.arch == 'amd64':
            return [c.r[k] for k in ('rax', 'rbx', 'rcx', 'rdi', 'rsi', 'r8')[:n]]
        return c.x[:n]

    def ret(self, c, *v):
        if self.arch == 'amd64':
            for k, x in zip(('rax', 'rbx', 'rcx'), v):
                c.r[k] = x & M64
        else:
            for i, x in enumerate(v):
                c.x[i] = x & M64

    def rd(self, c, a, n): return c.read(a, n) if self.arch == 'amd64' else c.m.read(a, n)
    def wr(self, c, a, n, v): c.write(a, n, v) if self.arch == 'amd64' else c.m.write(a, n, v)
    def rb(self, c, a, n): return bytes(self.rd(c, a + i, 1) for i in range(n))

    def wb(self, c, a, b):
        for i, x in enumerate(b):
            self.wr(c, a + i, 1, x)


class World:
    def __init__(self, km, maxsize, rnd):
        self.km = km
        self.rnd = rnd
        self.heap = T.HEAP0
        self.cache = {}  # (key type, 64 key bytes) -> (value type, boxed pointer)
        self.hash = {HOBJ[0]: b'', HOBJ[1]: b''}
        self.events = []
        ext = {}
        f = km.fns
        def stop(n):
            def s(c): raise Stop('call ' + n)
            return s
        for m in re.finditer(r'\b(?:call|bl)\s+(?:0x)?([0-9a-f]+)\s*<([^>]+)>', km.text):
            a = int(m.group(1), 16)
            if a not in km.entries:
                ext.setdefault(a, stop(km.byaddr.get(a, m.group(2))))

        def memmove(c):
            d, s, n = km.regs(c, 3); km.wb(c, d, km.rb(c, s, n))

        def convT(c):
            t, p = km.regs(c, 2); size = km.img.read(t, 8)
            a = self.alloc(size); km.wb(c, a, km.rb(c, p, size)); km.ret(c, a)

        def smload(c):
            m, kt, kp = km.regs(c, 3)
            if m != CACHE: raise Stop('Load on unknown map')
            ks = km.img.read(kt, 8)
            k = (kt, km.rb(c, kp, ks))
            if k in self.cache:
                vt, vp = self.cache[k]; km.ret(c, vt, vp, 1); self.events.append('hit')
            else:
                km.ret(c, 0, 0, 0); self.events.append('miss')
                if self.rnd.random() < 0.25 and len(k[1]) == 64:
                    # the other worker stores the same key between this worker's Load and Store (its value boxed
                    # as the binary's Store boxes it); this worker's LoadOrStore must then find it loaded
                    vt = km.img.read(km.dict_ + 0x28, 8)
                    a = self.alloc(32); km.wb(c, a, keccak(k[1]))
                    self.cache[k] = (vt, a); self.events.append('raced')

        def loadorstore(c):
            m, dct, kt, kp, vt, vp = km.regs(c, 6)
            if m != CACHE: raise Stop('LoadOrStore on unknown map')
            k = (kt, km.rb(c, kp, km.img.read(kt, 8)))
            if k in self.cache:
                ot, op = self.cache[k]; km.ret(c, ot, op, 1); self.events.append('loaded')
            else:
                self.cache[k] = (vt, vp); km.ret(c, vt, vp, 0); self.events.append('stored')

        def h_reset(c):
            h, = km.regs(c, 1); self.hash[h] = b''

        def h_write(c):
            h, p, n = km.regs(c, 3); self.hash[h] += km.rb(c, p, n); km.ret(c, n, 0, 0)

        def h_read(c):
            h, p, n = km.regs(c, 3)
            km.wb(c, p, keccak(self.hash[h])[:n]); km.ret(c, n, 0, 0)

        for n, fn in (('runtime.memmove', memmove), ('runtime.convTnoptr', convT), (SMLOAD, smload), (HT, loadorstore)):
            ext[f[n][0]] = fn
        ext[FAKE + 0x20] = h_read
        ext[FAKE + 0x28] = h_reset
        ext[FAKE + 0x40] = h_write
        self.ext = ext
        if km.arch == 'amd64':
            self.c = T.XC(km.prog, km.img, ext, {})
            self.c.write(T.GSTRUCT, 8, 0); self.c.write(T.GSTRUCT + 0x10, 8, 0)
        else:
            mem = T.A64Mem(km.img)
            mem.add(T.BASE, 0x2000000); mem.add(T.GSTRUCT, 0x1000); mem.add(T.SP_LO, T.SP_TOP - T.SP_LO + 0x100)
            self.c = T.AC(km.prog, mem, externs=ext, faults={})
        c = self.c
        for o in (0x20, 0x28, 0x40):
            km.wr(c, ITAB + o, 8, FAKE + o)
        for i, e in enumerate(EVMS):
            km.wr(c, e + 0x138, 8, CACHE)
            km.wr(c, e + 0x170, 8, ITAB)
            km.wr(c, e + 0x178, 8, HOBJ[i])
            km.wb(c, e + 0x180, bytes(32))
        km.wr(c, CACHE + 0x38, 8, maxsize)
        km.wr(c, SCOPE, 8, MEMOBJ)
        km.wr(c, SCOPE + 8, 8, STACKOBJ)
        km.wr(c, MEMOBJ, 8, MEMDATA)
        km.wr(c, MEMOBJ + 8, 8, 0x4000)
        km.wr(c, MEMOBJ + 0x10, 8, 0x4000)

    def alloc(self, n):
        a = self.heap; self.heap += (n + 15) & ~15
        if self.heap > T.BASE + 0x2000000: raise Stop('heap exhausted')
        return a

    def sha3(self, worker, data, off):
        km, c = self.km, self.c
        km.wb(c, MEMDATA + off, data)
        km.wr(c, STACKOBJ, 8, 4)  # Stack.len (bor fixed array layout: len at +0, slots inline from +8)
        for i, v in enumerate([0xa5a5, 0xa5a5, len(data), off]):
            km.wr(c, STACKOBJ + 8 + 32 * i, 32, v)
        e = km.fns[VMP + 'opKeccak256'][0]
        if km.arch == 'amd64':
            for k, v in zip(('rax', 'rbx', 'rcx'), (PCPTR, EVMS[worker], SCOPE)):
                c.r[k] = v
            c.r['r14'] = T.GSTRUCT; c.y[15] = 0
            x86emu.VISITED.clear(); c.call(e, [], maxsteps=2_000_000); km.visited |= x86emu.VISITED
            r = (c.r['rax'], c.r['rbx'])
        else:
            c.x[31] = T.SP_TOP; c.x[28] = T.GSTRUCT; c.x[29] = 0
            c.call(e, [PCPTR, EVMS[worker], SCOPE], maxsteps=2_000_000); km.visited |= c.visited
            r = (c.x[0], c.x[1])
        if any(r): raise Stop('opKeccak256 returned %s' % (r,))
        if km.rd(c, STACKOBJ, 8) != 3: raise Stop('stack len after SHA3')
        return km.rd(c, STACKOBJ + 8 + 32 * 2, 32)


def w32(x): return (x % (1 << 256)).to_bytes(32, 'big')


def inputs(rnd):
    pm = 0x360e68faccca8ca495c1b759fd9eee466db9fb32
    base = [w32(pm) + w32(6), w32(0xd21fe301) + w32(0xaf88d065e77c8cc2239327c5edb3a432268e5831),
            w32(rnd.getrandbits(160)) + w32(rnd.randrange(16)), w32(rnd.getrandbits(256)) + w32(6),
            w32(rnd.getrandbits(256)) + w32(rnd.getrandbits(256)), bytes(64), b'\xff' * 64]
    out = []
    for x in base:
        out.append(x)
        b = bytearray(x); b[63] ^= 1; out.append(bytes(b))
        b = bytearray(x); b[56] ^= 0x80; out.append(bytes(b))
        b = bytearray(x); b[0] ^= 1; out.append(bytes(b))
        b = bytearray(x); b[31] ^= 1; out.append(bytes(b))
        b = bytearray(x); b[32] ^= 1; out.append(bytes(b))
    return out


def main():
    arch, nseq, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    fault = sys.argv[4] if len(sys.argv) > 4 else 'none'
    km = KModel(arch, fault)
    rnd = random.Random(SEED)
    res = {'arch': arch, 'fault': fault, 'seed': SEED, 'functions': km.names, 'sequences': nseq, 'hashes': 0, 'hits': 0,
           'misses': 0, 'stored': 0, 'loaded': 0, 'raced': 0, 'overwrites': 0, 'capRuns': 0, 'mismatches': [], 'errors': [], 'started': time.time()}
    for q in range(nseq):
        maxsize = rnd.choice([1 << 20, 1 << 20, 1 << 20, 3, 0])
        res['capRuns'] += maxsize < 100
        w = World(km, maxsize, rnd)
        pool = inputs(rnd)
        try:
            for _ in range(rnd.randrange(6, 30)):
                wk = rnd.randrange(2)
                r = rnd.random()
                if r < 0.2:
                    data = bytes(rnd.getrandbits(8) for _ in range(rnd.choice([0, 1, 32, 63, 65, 96, 128])))
                    res['overwrites'] += 1
                else:
                    data = rnd.choice(pool[:6] if rnd.random() < 0.5 else pool)
                off = rnd.choice([0, 32, 64, 0x100])
                got = w.sha3(wk, data, off)
                res['hashes'] += 1
                want = int.from_bytes(keccak(data), 'big')
                if got != want:
                    res['mismatches'].append({'seq': q, 'worker': wk, 'input': data.hex(), 'want': hex(want), 'got': hex(got),
                                              'events': w.events[-4:]})
                    break
            cnt = km.rd(w.c, CACHE + 0x30, 8)
            if cnt != w.events.count('stored') or cnt > maxsize:
                res['errors'].append({'seq': q, 'error': 'count %d stored %d max %d' % (cnt, w.events.count('stored'), maxsize)})
        except (Stop, AStop) as e:
            res['errors'].append({'seq': q, 'error': str(e)})
        for ev in w.events:
            res[{'hit': 'hits', 'miss': 'misses', 'stored': 'stored', 'loaded': 'loaded', 'raced': 'raced'}[ev]] += 1
    res['visited'] = len(km.visited)
    res['elapsed'] = time.time() - res['started']
    json.dump(res, open(out, 'w'), indent=1)
    print(arch, fault, {k: res[k] for k in ('hashes', 'hits', 'misses', 'stored', 'loaded', 'raced', 'overwrites', 'capRuns')},
          'mismatches', len(res['mismatches']), 'errors', len(res['errors']), (res['errors'][:1] or [''])[0])


if __name__ == '__main__':
    main()
