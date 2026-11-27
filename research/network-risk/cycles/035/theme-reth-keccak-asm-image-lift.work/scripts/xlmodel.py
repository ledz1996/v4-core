"""Model of the KECCAK256 path of the official X Layer image xlayer/xlayer-reth:v0.0.7.3-rc.1 (amd64,
binary sha256 7a9230ac...019c2e, reth 2.3.0 f60420a, build features asm_keccak, keccak_cache_global).
The disassembly text of the binary is interpreted by the cycle 27/28 x86 model (x86emu.py, x86emu2.py from
cycles/032/theme-opstack-reth-binary-lift.work/scripts). No code from the binary is executed.

Functions (addresses are link-time virtual addresses of the PIE):
  0x3bde4a0 / 0x3bde660  revm KECCAK256 handlers (entry 0x20 of the four 256-entry instruction tables 0x70cb168..)
  0x3b6e6c0              alloy-primitives keccak256 with keccak_cache_global (fixed-cache): len 1..87 cached
  0x3770440              the hasher the cache uses to pick bucket and tag
  0x2147080              uncached keccak-asm Keccak256 (any length), reached through GOT slot 0x71c1bd0
  0x6f67680 / 0x6f67760  CRYPTOGAMS SHA3_absorb / SHA3_squeeze (GOT 0x71c1bc0 / 0x71c1bc8)
  0x6f675e0 / 0x6f67300  KeccakF1600 / __KeccakF1600 (generic x86_64, lane complementing), iotas at 0x6f67840
"""
import os, re, sys
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/032/theme-opstack-reth-binary-lift.work/scripts')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from x86emu2 import CPU2, Prog, Stop, rewrite_rip, M64
from evm import keccak

SEGS = [(0x0, 0x0, 0x20c6acc), (0x20c7b00, 0x20c6b00, 0x4ea3eb0), (0x6f6c9b0, 0x6f6a9b0, 0x26d200),
        (0x71dabb0, 0x71d7bb0, 0x0239a8)]
HANDLER, HANDLER2, KCACHE, HASHER, KLONG = 0x3bde4a0, 0x3bde660, 0x3b6e6c0, 0x3770440, 0x2147080
ABSORB, SQUEEZE, KF, IOTAS = 0x6f67680, 0x6f67760, 0x6f675e0, 0x6f67840
CACHE_GLOBAL, BUCKETS, CAP = 0x71dac80, 0x71fe600, 0x20000
INTERNAL = {0x71c1bc0: ABSORB, 0x71c1bc8: SQUEEZE, 0x71c1bd0: KLONG}
GOT_MEMCPY, GOT_MEMSET, GOT_BCMP = 0x71c16e0, 0x71c1730, 0x71c1b60
HSEED, SECRET = 0x3841f612376719ec, 0xfbff38
CG_SLOT = 0x71c1bb8
KF_LO, KF_HI = 0x6f67300, 0x6f675d8
PAD_LONG = (0x2147165, 'mov BYTE PTR [rsp+r14*1+0xd0],0x1', 'mov BYTE PTR [rsp+r14*1+0xcf],0x1')
PAD_CACHE = (0x3b6e807, 'mov BYTE PTR [rsp+r14*1+0x100],0x1', 'mov BYTE PTR [rsp+r14*1+0xff],0x1')
LENJNE = 0x3b6e748
# handler fixture: interpreter field offsets read from the handler text
HFIX = {'ctx': {HANDLER: 0x5c0, HANDLER2: 0x450}, 'wordgas': 0x48, 'limit': None}
NAME = 'xlayer'

if os.environ.get('KMODEL') == 'bsc':
    # ghcr.io/bnb-chain/reth-bsc:v0.1.4 amd64, binary sha256 31c061b9...f467b860, reth 2.2.0 6e08308
    NAME = 'reth-bsc'
    SEGS = [(0x0, 0x0, 0x1d00d14), (0x1d01e00, 0x1d00e00, 0x466a250), (0x636d050, 0x636b050, 0x250e70),
            (0x65beec0, 0x65bbec0, 0x026640)]
    HANDLER, HANDLER2, KCACHE, HASHER, KLONG = 0x2fd0e60, 0x2fd12c0, 0x357e960, 0x357f430, 0x1d70960
    ABSORB, SQUEEZE, KF, IOTAS = 0x6367d80, 0x6367e60, 0x6367ce0, 0x6367f40
    CACHE_GLOBAL, BUCKETS, CAP = 0x65befa8, 0x65e5580, 0x20000
    INTERNAL = {0x65a8850: ABSORB, 0x65a8858: SQUEEZE, 0x65a8860: KLONG}
    GOT_MEMCPY, GOT_MEMSET, GOT_BCMP = 0x65a82d0, 0x65a8350, 0x65a8300
    SECRET = 0xd35dc8
    CG_SLOT = 0x65a8848
    KF_LO, KF_HI = 0x6367a00, 0x6367cd8
    PAD_LONG = (0x1d70a3b, 'mov BYTE PTR [rsp+r15*1+0xd0],0x1', 'mov BYTE PTR [rsp+r15*1+0xcf],0x1')
    PAD_CACHE = (0x357eaa4, 'mov BYTE PTR [rsp+r14*1+0x100],0x1', 'mov BYTE PTR [rsp+r14*1+0xff],0x1')
    LENJNE = 0x357e9e8
    HFIX = {'ctx': {HANDLER: 0x2b8, HANDLER2: 0x2b8}, 'wordgas': 0x38, 'limit': 0x20, 'status': False}  # errors go through a call, rax is not a status


class Model:
    def __init__(self, binf, asmf, fault='none'):
        fb = bytearray(open(binf, 'rb').read())
        # apply the R_X86_64_RELATIVE relocations (readelf -r, saved as build/rel.txt) at link-time base 0
        relf = os.path.join(os.path.dirname(os.path.abspath(asmf)), 'rel.txt')
        for l in open(relf):
            a, v = (int(x, 16) for x in l.split())
            for va, off, sz in SEGS:
                if va <= a < va + sz:
                    fb[off + a - va:off + a - va + 8] = v.to_bytes(8, 'little')
        self.fb = bytes(fb)
        self.prog = Prog(rewrite_rip(open(asmf).read()))
        self.fault = fault
        self.state = {}
        self.visited = set()
        self.steps = 0
        self.faults = {}
        assert self.rd(CG_SLOT, 8) == CACHE_GLOBAL and self.rd(CACHE_GLOBAL, 8) == BUCKETS
        assert self.rd(CACHE_GLOBAL + 8, 8) == CAP
        if fault == 'iota':            # one wrong round constant (round 5)
            v = self.rd(IOTAS + 8 * 5, 8) ^ (1 << 7); self.wr(IOTAS + 8 * 5, 8, v)
        elif fault == 'rot':           # one rotation off by one inside __KeccakF1600
            for a in sorted(self.prog.ins):
                b = self.prog.ins[a]
                m = re.match(r'^rol\s+(\w+),0x([0-9a-f]+)$', b)
                if KF_LO <= a < KF_HI and m:
                    self.faults[a] = 'rol %s,0x%x' % (m.group(1), int(m.group(2), 16) + 1); break
        elif fault == 'pad':           # padding byte placed one byte early in the uncached routine (len >= 88)
            a, old, new = PAD_LONG; assert ' '.join(self.prog.ins[a].split()) == old
            self.faults[a] = new
        elif fault == 'padc':          # same in the cached routine (len 1..87)
            a, old, new = PAD_CACHE; assert ' '.join(self.prog.ins[a].split()) == old
            self.faults[a] = new
        elif fault == 'lenchk':        # cache hit without the length byte comparison
            a = LENJNE; assert self.prog.ins[a].startswith('jne')
            self.faults[a] = 'nop'
        elif fault not in ('none', 'bcmp8'):
            raise SystemExit('unknown fault ' + fault)

    # persistent memory (cache buckets, globals, planted entries)
    def rd(self, a, n):
        return Mem(self).read(a, n)

    def wr(self, a, n, v):
        for i in range(n):
            self.state[a + i] = (v >> (8 * i)) & 0xff

    def cpu(self):
        c = CPU3(self.prog, self.fb, 0, got=self.got(), faults=self.faults)
        c.mem = self.state
        c.write(c.fs + 0x28, 8, 0x1122334455667788)
        return c

    def got(self):
        fault = self.fault
        def memcpy(cpu):
            d, s, n = cpu.r['rdi'], cpu.r['rsi'], cpu.r['rdx']
            data = [cpu.read(s + i, 1) for i in range(n)]
            for i, v in enumerate(data): cpu.write(d + i, 1, v)
            cpu.r['rax'] = d
        def memset(cpu):
            d, c, n = cpu.r['rdi'], cpu.r['rsi'] & 0xff, cpu.r['rdx']
            for i in range(n): cpu.write(d + i, 1, c)
            cpu.r['rax'] = d
        def bcmp(cpu):
            a, b, n = cpu.r['rdi'], cpu.r['rsi'], cpu.r['rdx']
            if fault == 'bcmp8': n = max(0, n - 8)
            r = 0
            for i in range(n):
                if cpu.read(a + i, 1) != cpu.read(b + i, 1): r = 1; break
            cpu.r['rax'] = r
        return {GOT_MEMCPY: memcpy, GOT_MEMSET: memset, GOT_BCMP: bcmp}

    def run(self, fn, args, maxsteps=50_000_000):
        c = self.cpu()
        c.call(fn, args, maxsteps=maxsteps)
        self.visited |= c.visited
        self.steps += c.steps
        return c


class Mem:
    def __init__(self, m): self.m = m
    def read(self, a, n):
        st = self.m.state
        if any((a + i) in st for i in range(n)):
            return int.from_bytes(bytes(st.get(a + i, filebyte(self.m.fb, a + i)) for i in range(n)), 'little')
        return int.from_bytes(bytes(filebyte(self.m.fb, a + i) for i in range(n)), 'little')


def filebyte(fb, a):
    for va, off, sz in SEGS:
        if va <= a < va + sz:
            return fb[off + a - va]
    return 0


class CPU3(CPU2):
    def read(self, a, n):
        mem = self.mem
        hit = False
        for i in range(n):
            if (a + i) in mem: hit = True; break
        if not hit:
            for va, off, sz in SEGS:
                if va <= a and a + n <= va + sz:
                    return int.from_bytes(self.fb[off + a - va:off + a - va + n], 'little')
            return 0
        return int.from_bytes(bytes(mem[a + i] if (a + i) in mem else filebyte(self.fb, a + i) for i in range(n)), 'little')

    def step(self, pc):
        body = self.p.ins.get(pc, '')
        if body.startswith('repz ret'):
            self.visited.add(pc)
            a = self.read(self.r['rsp'], 8); self.r['rsp'] += 8; return a
        if body.startswith('rep movs BYTE PTR'):
            self.visited.add(pc)
            for _ in range(self.r['rcx']):
                self.write(self.r['rdi'], 1, self.read(self.r['rsi'], 1))
                self.r['rdi'] = (self.r['rdi'] + 1) & M64; self.r['rsi'] = (self.r['rsi'] + 1) & M64
            self.r['rcx'] = 0
            return self.p.nxt[pc]
        if body.startswith('lock '):
            saved = body
            self.p.ins[pc] = body[5:].strip()
            try:
                return super().step(pc)
            finally:
                self.p.ins[pc] = saved
        return super().step(pc)

    def i_rol(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]
        c = self._shcount(self.opnd(o[1]) if len(o) > 1 else ('i', 1, None), b)
        if c == 0: return
        x = self.get(d); r = ((x << c) | (x >> (b - c))) & ((1 << b) - 1)
        self.cf = r & 1; self.of = ((r >> (b - 1)) & 1) ^ self.cf
        self.put(d, r)

    def i_bswap(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]
        self.put(d, int.from_bytes(self.get(d).to_bytes(b // 8, 'little'), 'big'))

    def i_cmpxchg(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1]); b = d[2]
        cur = self.get(d)
        acc = self.r['rax'] & ((1 << b) - 1)
        self._sub(('r', 'rax' if b == 64 else 'eax', b), ('i', cur, None), 0, store=False)
        if acc == cur:
            self.zf = 1; self.put(d, self.get(s, b))
        else:
            self.zf = 0; self.setr('rax' if b == 64 else 'eax', cur)

    def i_call(self, o, pc, n):
        m = re.match(r'^QWORD PTR \[0x([0-9a-f]+)\]$', o[0])
        if m and int(m.group(1), 16) in INTERNAL:
            self.r['rsp'] -= 8; self.write(self.r['rsp'], 8, n); return INTERNAL[int(m.group(1), 16)]
        return super().i_call(o, pc, n)
