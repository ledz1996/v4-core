"""Transient storage model of the Nitro b72783f release binaries (cycle 31, theme-nitro-binary-storage-lift).

The binaries are read as data only. objdump / llvm-objdump print the text of the chosen functions and the cycle 30
x86-64 and AArch64 interpreters (copied from cycle 30's work directory by import, unchanged) interpret that text in
Python. Constants, itabs and type descriptors are read as bytes from the ELF file. Nothing from the binaries runs.

Run from the binary: core/vm.opTstore, core/vm.opTload, core/state.(*StateDB).SetTransientState,
(*StateDB).GetTransientState, (*journal).append, (*journal).revert, (*transientStorageChange).revert and .mutation
(the pointer wrappers the journalEntry itab names), transientStorageChange.revert and .mutation, and the
holiman/uint256 SetBytes family that opTload calls. The interface calls (StateDB itab of *state.StateDB, the
journalEntry itab of transientStorageChange) are dispatched through the real itabs read from the file.

Stubbed Go runtime symbols (Python): runtime.mapaccess1, runtime.mapassign, runtime.mapdelete (one dict per map
handle, keyed by the full key bytes of the size the map type descriptor gives), runtime.memequal, runtime.memmove,
runtime.convTnoptr (copy of type.Size_ bytes into a fresh heap block), runtime.growslice, runtime.mallocgc* small
size classes, runtime.newobject. runtime.gcWriteBarrier*, typeAssert, panics and morestack stop the run.
"""
import os, re, struct, sys
C30 = '/home/user/v4-core/research/network-risk/cycles/030/theme-nitro-binary-arith-lift.work/'
sys.path.insert(0, C30 + 'scripts')
sys.path.insert(0, C30 + 'scripts/emu')
import goshim as G
import x86emu
from x86emu2 import CPU2, rewrite_rip
from x86emu import Prog as XProg, Stop, M64
from a64emu import CPU as ACPU, Prog as AProg, Mem as AMem, Stop as AStop

VM = 'github.com/ethereum/go-ethereum/core/vm.'
ST = 'github.com/ethereum/go-ethereum/core/state.'
U = 'github.com/holiman/uint256.'
RUN = [VM + 'opTstore', VM + 'opTload', ST + '(*StateDB).SetTransientState', ST + '(*StateDB).GetTransientState',
       ST + '(*journal).append', ST + '(*journal).revert', ST + '(*transientStorageChange).revert',
       ST + '(*transientStorageChange).mutation', ST + 'transientStorageChange.revert',
       ST + 'transientStorageChange.mutation']
STUBS = ['runtime.mapaccess1', 'runtime.mapassign', 'runtime.mapdelete', 'runtime.memequal', 'runtime.memmove',
         'runtime.convTnoptr', 'runtime.growslice', 'runtime.newobject']
STOPS = ['runtime.morestack_noctxt', 'runtime.panicBounds', 'runtime.gopanic', 'runtime.panicwrap', 'runtime.typeAssert',
         'runtime.gcWriteBarrier1', 'runtime.gcWriteBarrier2', 'runtime.gcWriteBarrier3', 'fmt.Errorf', 'fmt.errorf',
         'runtime.convTslice', 'runtime.panicdivide']

BASE = 0x20000000
LIMIT = 0x20800000
SCOPE, STACKOBJ, ARENA, DATA = BASE + 0x0, BASE + 0x1000, BASE + 0x2000, BASE + 0x10000
CONTRACT, EVM, PCPTR = BASE + 0x3000, BASE + 0x4000, BASE + 0x5000
STATEDB, JOURNAL = BASE + 0x8000, BASE + 0x9000
TSMAP, MUTMAP = 0x5100000000aa, 0x5100000000bb
HEAP0 = BASE + 0x100000
GSTRUCT = 0x21000000
SP_TOP = 0x7ffff0000000
SP_LO = SP_TOP - 0x100000
NSLOT = 16


class Img(G.Image):
    """goshim.Image plus NOBITS sections, which read as zero."""

    def __init__(self, path):
        super().__init__(path)
        f = self.f
        shoff, = struct.unpack_from('<Q', f, 0x28)
        shentsize, shnum = struct.unpack_from('<HH', f, 0x3a)
        self.bss = []
        for i in range(shnum):
            name, typ, flags, addr, off, size = struct.unpack_from('<IIQQQQ', f, shoff + i * shentsize)
            if typ == 8 and addr and (flags & 2):
                self.bss.append((addr, addr + size))

    def read(self, a, n):
        v = super().read(a, n)
        if v is None and any(lo <= a and a + n <= hi for lo, hi in self.bss):
            return 0
        return v


class World:
    """Python side of the stubs: Go maps by handle, heap, journal of stub calls."""

    def __init__(self, model):
        self.m = model
        self.maps = {TSMAP: {}, MUTMAP: {}}
        self.heap = HEAP0
        self.calls = []

    def alloc(self, n):
        a = self.heap
        self.heap += (n + 15) & ~15
        if self.heap > LIMIT:
            raise Stop('heap exhausted')
        return a

    def keysize(self, mtype):
        key = self.m.img.read(mtype + 0x30, 8)
        return self.m.img.read(key, 8)

    def elemsize(self, mtype):
        el = self.m.img.read(mtype + 0x38, 8)
        return self.m.img.read(el, 8)


class Model:
    def __init__(self, arch, faults=None, text_patch=None):
        self.arch = arch
        D = C30 + 'dl/'
        self.bin = D + '%s/usr/local/bin/nitro' % arch
        self.img = Img(self.bin)
        self.fns = G.fnlist(D + 'build/all-%s.txt' % arch)
        names = list(RUN) + [k for k in self.fns if k.startswith(U + '(*Int).SetBytes')]
        self.ranges = {n: self.fns[n] for n in names}
        text = G.disasm(self.bin, arch, self.ranges.values())
        if text_patch:
            text = text_patch(text)
        self.text = text
        self.prog = XProg(rewrite_rip(text)) if arch == 'amd64' else AProg([text])
        self.faults = faults or {}
        self.visited = set()
        self.stubbed = set()
        self.itab_statedb = self._find_itab(ST + '(*StateDB).SetTransientState', 0x1e0)
        self.mutation_seen = set()

    def _find_itab(self, fn, off):
        t = self.fns[fn][0]
        pat = struct.pack('<Q', t)
        hits = []
        for lo, hi, o in self.img.secs:
            data = self.img.f[o:o + hi - lo]
            i = data.find(pat)
            while i >= 0:
                if i % 8 == 0 and i >= off:
                    hits.append(lo + i - off)
                i = data.find(pat, i + 1)
        assert len(hits) == 1, hits
        return hits[0]

    # ---- argument access, both ABIs
    def regs(self, cpu, n):
        if self.arch == 'amd64':
            return [cpu.r[k] for k in ('rax', 'rbx', 'rcx', 'rdi', 'rsi', 'r8')[:n]]
        return cpu.x[:n]

    def ret(self, cpu, *vals):
        if self.arch == 'amd64':
            for k, v in zip(('rax', 'rbx', 'rcx'), vals):
                cpu.r[k] = v & M64
        else:
            for i, v in enumerate(vals):
                cpu.x[i] = v & M64

    def rd(self, cpu, a, n):
        if self.arch == 'amd64':
            return cpu.read(a, n)
        return cpu.m.read(a, n)

    def wr(self, cpu, a, n, v):
        if self.arch == 'amd64':
            cpu.write(a, n, v)
        else:
            cpu.m.write(a, n, v)

    def rbytes(self, cpu, a, n):
        return bytes(self.rd(cpu, a + i, 1) for i in range(n))

    def wbytes(self, cpu, a, b):
        for i, x in enumerate(b):
            self.wr(cpu, a + i, 1, x)

    # ---- stubs
    def externs(self, w):
        ext = {}
        f = self.fns
        def stopper(n):
            def s(cpu): raise Stop('call ' + n)
            return s
        for n in STOPS:
            if n in f:
                ext[f[n][0]] = stopper(n)
        for n in f:
            if n.startswith('runtime.mallocgc') and n != 'runtime.mallocgc':
                def mal(cpu, n=n):
                    self.stubbed.add(n)
                    size = self.regs(cpu, 1)[0]
                    a = w.alloc(size)
                    self.wbytes(cpu, a, bytes(size))
                    self.ret(cpu, a)
                ext[f[n][0]] = mal
        def m_access(cpu):
            self.stubbed.add('runtime.mapaccess1')
            t, h, kp = self.regs(cpu, 3)
            if h not in w.maps: raise Stop('mapaccess1 on unknown map %x' % h)
            k = self.rbytes(cpu, kp, w.keysize(t))
            es = w.elemsize(t)
            d = w.maps[h]
            if k in d:
                self.ret(cpu, d[k])
            else:
                z = w.alloc(es); self.wbytes(cpu, z, bytes(es)); self.ret(cpu, z)
            w.calls.append(('get', h, k))
        def m_assign(cpu):
            self.stubbed.add('runtime.mapassign')
            t, h, kp = self.regs(cpu, 3)
            if h not in w.maps: raise Stop('mapassign on unknown map %x' % h)
            k = self.rbytes(cpu, kp, w.keysize(t))
            es = w.elemsize(t)
            d = w.maps[h]
            if k not in d:
                a = w.alloc(es); self.wbytes(cpu, a, bytes(es)); d[k] = a
            self.ret(cpu, d[k])
            w.calls.append(('assign', h, k))
        def m_delete(cpu):
            self.stubbed.add('runtime.mapdelete')
            t, h, kp = self.regs(cpu, 3)
            if h not in w.maps: raise Stop('mapdelete on unknown map %x' % h)
            k = self.rbytes(cpu, kp, w.keysize(t))
            w.maps[h].pop(k, None)
            w.calls.append(('delete', h, k))
        def memeq(cpu):
            self.stubbed.add('runtime.memequal')
            a, b, n = self.regs(cpu, 3)
            self.ret(cpu, int(self.rbytes(cpu, a, n) == self.rbytes(cpu, b, n)))
        def memmove(cpu):
            self.stubbed.add('runtime.memmove')
            d, s, n = self.regs(cpu, 3)
            self.wbytes(cpu, d, self.rbytes(cpu, s, n))
        def convT(cpu):
            self.stubbed.add('runtime.convTnoptr')
            t, p = self.regs(cpu, 2)
            size = self.img.read(t, 8)
            a = w.alloc(size)
            self.wbytes(cpu, a, self.rbytes(cpu, p, size))
            self.ret(cpu, a)
            w.calls.append(('box', t, size, a))
        def grow(cpu):
            self.stubbed.add('runtime.growslice')
            old, newlen, oldcap, num, et = self.regs(cpu, 5)
            es = self.img.read(et, 8)
            cap = max(newlen, 2 * oldcap, 4)
            a = w.alloc(cap * es)
            self.wbytes(cpu, a, bytes(cap * es))
            oldlen = newlen - num
            if old and oldlen:
                self.wbytes(cpu, a, self.rbytes(cpu, old, oldlen * es))
            self.ret(cpu, a, newlen, cap)
        def newobj(cpu):
            self.stubbed.add('runtime.newobject')
            t, = self.regs(cpu, 1)
            size = self.img.read(t, 8)
            a = w.alloc(size); self.wbytes(cpu, a, bytes(size)); self.ret(cpu, a)
        for n, fn in (('runtime.mapaccess1', m_access), ('runtime.mapassign', m_assign), ('runtime.mapdelete', m_delete),
                      ('runtime.memequal', memeq), ('runtime.memmove', memmove), ('runtime.convTnoptr', convT),
                      ('runtime.growslice', grow), ('runtime.newobject', newobj)):
            ext[f[n][0]] = fn
        return ext

    # ---- CPUs
    def cpu(self, w):
        ext = self.externs(w)
        if self.arch == 'amd64':
            c = XCPU(self.prog, self.img, ext, self.faults)
            c.write(GSTRUCT, 8, 0); c.write(GSTRUCT + 0x10, 8, 0)
            return c
        mem = A64Mem(self.img)
        mem.add(BASE, LIMIT - BASE)
        mem.add(GSTRUCT, 0x1000)
        mem.add(SP_LO, SP_TOP - SP_LO + 0x100)
        c = ACPU2(self.prog, mem, externs=ext, faults=self.faults)
        return c

    def call(self, c, entry, args):
        if self.arch == 'amd64':
            for k, v in zip(('rax', 'rbx', 'rcx', 'rdi', 'rsi'), args):
                c.r[k] = v & M64
            c.r['r14'] = GSTRUCT
            c.y[15] = 0
            x86emu.VISITED.clear()
            c.call(entry, [], maxsteps=2_000_000)
            self.visited |= x86emu.VISITED
            return c.r['rax'], c.r['rbx'], c.r['rcx']
        c.x[31] = SP_TOP
        c.x[28] = GSTRUCT
        c.x[29] = 0
        c.call(entry, list(args), maxsteps=2_000_000)
        self.visited |= c.visited
        return c.x[0], c.x[1], c.x[2]


class XCPU(CPU2):
    def __init__(self, prog, img, externs, faults):
        super().__init__(prog, None, 0, externs=externs, faults=faults)
        self.img = img

    def read(self, a, n):
        if a in self.mem or (BASE <= a < LIMIT) or (GSTRUCT <= a < GSTRUCT + 0x1000) or (SP_LO <= a <= SP_TOP + 0x100):
            return super(CPU2, self).read(a, n)
        v = self.img.read(a, n)
        if v is None:
            raise Stop('read %d at %x outside memory' % (n, a))
        return v

    def write(self, a, n, v):
        if (BASE <= a and a + n <= LIMIT) or (GSTRUCT <= a < GSTRUCT + 0x1000) or (SP_LO <= a and a + n <= SP_TOP + 0x100) \
                or a == 0x7f0000000028:
            return super(CPU2, self).write(a, n, v)
        raise Stop('write %d at %x outside memory' % (n, a))

    def i_bswap(self, o, pc, n):
        d = self.opnd(o[0])
        w = d[2] // 8
        self.put(d, int.from_bytes(self.get(d).to_bytes(w, 'little'), 'big'))
        return n

    def i_call(self, o, pc, n):
        s = o[0].strip()
        if re.match(r'^r[a-z0-9]+$', s):
            t = self.get(self.opnd(s))
            if t in self.externs:
                self.externs[t](self); return n
            self.r['rsp'] -= 8; self.write(self.r['rsp'], 8, n); return t
        return super().i_call(o, pc, n)


class A64Mem(AMem):
    def __init__(self, img):
        super().__init__(None, 0, 0)
        self.img = img

    def read(self, a, n):
        b, o = self._find(a, n)
        if b is not None:
            return int.from_bytes(b[o:o + n], 'little')
        v = self.img.read(a, n)
        if v is None:
            raise Stop('read %d at %x outside memory' % (n, a))
        return v


class ACPU2(ACPU):
    def i_rev(self, o):
        w = 8 if o[0].startswith('x') else 4
        self.wr(o[0], int.from_bytes(self.rr(o[1]).to_bytes(w, 'little'), 'big'))

    def i_blr(self, o):
        t = self.rr(o[0])
        if t in self.externs:
            self.externs[t](self)
            return None
        self.x[30] = self._pc_next
        return t
