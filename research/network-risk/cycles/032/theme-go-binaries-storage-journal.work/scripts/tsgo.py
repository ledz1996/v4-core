"""Cycle 32 (theme-go-binaries-storage-journal), task 1: the transient storage path of the shipped bsc v1.8.2, bor
v2.11.2 and avalanchego v1.15.3 binaries (cycle 31 downloads, read as data only) run in the cycle 31 x86-64 and
AArch64 models, with the Go runtime map calls stubbed in Python, against tools/opdiff/pyevm.py.

Run from the binary text: core/vm.opTstore and opTload, the vm.StateDB itab methods GetTransientState and
SetTransientState of the chosen StateDB type, (*StateDB).Snapshot and RevertToSnapshot (snapshot id lookup with
sort.Search inlined or called), the journal append and revert, every core/state function they call directly,
and the methods of the journalEntry itab of transientStorageChange (revert, dirtied, copy) read from the file.
The bor ParallelStateDB (BlockSTM V2 worker state) runs as a second StateDB type ('bor-par').

Stubbed Go runtime calls: mapaccess1, mapaccess2, mapassign, mapdelete, makemap_small, makemap (one Python dict per
map handle, keyed by the full key bytes of the size the map type descriptor gives), memequal, memmove, convT,
convTnoptr, growslice, newobject, mallocgc size classes. Every other runtime call stops the run (morestack, panics,
write barriers, which are only reached when the writeBarrier flag in .bss is set; it reads zero).

The driver feeds the cycle 31 Nitro theme's sequence generator (seed 31_1211_01, the same 20,007 sequences) and
compares every TLOAD with pyevm.
usage: python3 -I tsgo.py <target> <nseq> <out.json> [fault]
target: bsc-amd64 bsc-arm64 bor-amd64 bor-arm64 bor-par-amd64 bor-par-arm64 avax-amd64 avax-arm64
"""
import json, os, random, re, struct, subprocess, sys, time
C31 = '/home/user/v4-core/research/network-risk/cycles/031/theme-go-family-binary-lift.work/'
sys.path.insert(0, C31 + 'scripts')
sys.path.insert(0, C31 + 'scripts/emu')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import goshim as G
import targets
import models
from models import X64, Stop
import x86emu
from x86emu2 import rewrite_rip
from x86emu import Prog as XProg, M64
from a64emu import CPU as ACPU, Prog as AProg, Mem as AMem, Stop as AStop
import pyevm as PE
from evm import assemble, keccak

GE = 'github.com/ethereum/go-ethereum/'
LE = 'github.com/ava-labs/libevm/'
CFG = {
    'bsc': dict(tgt='bsc', P=GE, layout='arena', sdbType='state.StateDB', evmSdb=0xb8, interp=False,
                tmap=0x108, jptr=0x110, revs=None),
    'bor': dict(tgt='bor', P=GE, layout='fixed', sdbType='state.StateDB', evmSdb=0xb0, interp=False,
                tmap=0x118, jptr=0x120, revs=None),
    'bor-par': dict(tgt='bor', P=GE, layout='fixed', sdbType='state.ParallelStateDB', evmSdb=0xb0, interp=False,
                    tmap=0x98, jptr=None, revs=None),
    'avax': dict(tgt='avax', P=LE, layout='slice', sdbType='state.StateDB', evmSdb=0xb0, interp=True,
                 tmap=0x118, jptr=0x120, revs=None),
}

BASE, LIMIT = 0x20000000, 0x28000000
SCOPE, STACKOBJ, ARENA, DATA = BASE, BASE + 0x1000, BASE + 0x9000, BASE + 0x10000
CONTRACT, EVM, INTERP, PCPTR, ADDRBUF = BASE + 0x20000, BASE + 0x21000, BASE + 0x22000, BASE + 0x23000, BASE + 0x23100
STATEDB, JOURNAL = BASE + 0x30000, BASE + 0x32000
HEAP0 = BASE + 0x100000
GSTRUCT = 0x29000000
SP_TOP = 0x7ffff0000000
SP_LO = SP_TOP - 0x100000
NSLOT = 16
H0 = 0x5100000000000  # map handles

STUBS = ['runtime.mapaccess1', 'runtime.mapaccess2', 'runtime.mapassign', 'runtime.mapdelete', 'runtime.makemap_small',
         'runtime.makemap', 'runtime.memequal', 'runtime.memmove', 'runtime.convT', 'runtime.convTnoptr',
         'runtime.growslice', 'runtime.newobject']
INCLUDE_RT = ('runtime.duffzero', 'runtime.duffcopy')


def nm_symbols(path):
    out = subprocess.run(['nm', path], capture_output=True, text=True, check=True).stdout
    d = {}
    for l in out.splitlines():
        p = l.split(None, 2)
        if len(p) == 3:
            d[p[2]] = int(p[0], 16)
    return d


class Img(G.Image):
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


class Model:
    def __init__(self, name, text_patch=None):
        kind, arch = name.rsplit('-', 1)
        self.kind, self.arch = kind, arch
        self.c = CFG[kind]
        t = targets.get(self.c['tgt'] + '-' + arch)
        self.bin = t['bin']
        self.img = Img(self.bin)
        self.fns = G.fnlist(t['fns'])
        self.byaddr = {v[0]: k for k, v in self.fns.items()}
        self.sym = nm_symbols(self.bin)
        P = self.c['P']
        self.S, self.V = P + 'core/state.', P + 'core/vm.'
        it = 'go:itab.*%score/%s,%score/vm.StateDB' % (P, self.c['sdbType'], P)
        self.itab_sdb = self.sym[it]
        self.itab_tsc = self.sym['go:itab.%score/state.transientStorageChange,%score/state.journalEntry' % (P, P)]
        sdbname = '(*%s)' % self.c['sdbType'].split('.')[1]
        roots = [self.V + 'opTstore', self.V + 'opTload', self.S + sdbname + '.Snapshot', self.S + sdbname + '.RevertToSnapshot']
        # methods reached through itabs: the vm.StateDB methods the roots call and every journalEntry method
        extra = set()
        for itab, n in ((self.itab_sdb, 120), (self.itab_tsc, 6)):
            for i in range(n):
                a = self.img.read(itab + 0x18 + 8 * i, 8)
                if a in self.byaddr:
                    nm = self.byaddr[a]
                    if any(k in nm for k in ('TransientState', 'revert', 'dirtied', 'copy', 'Snapshot')):
                        extra.add(nm)
        if self.c['interp']:
            ar = self.sym['go:itab.%score/vm.AccountRef,%score/vm.ContractRef' % (P, P)]
            self.itab_acct = ar
            extra.add(self.byaddr[self.img.read(ar + 0x18, 8)])
        self.roots = roots + sorted(extra)
        self.stub_names = [n for n in STUBS if n in self.fns]
        self.ranges, self.text = self._closure(self.roots, text_patch)
        self.prog = XProg(rewrite_rip(self.text)) if arch == 'amd64' else AProg([self.text])
        self.visited = set()
        self.stubbed = set()

    def _closure(self, roots, text_patch):
        want, seen, texts = list(roots), set(), {}
        stubaddr = {self.fns[n][0] for n in self.stub_names}
        while want:
            n = want.pop()
            if n in seen or n not in self.fns:
                continue
            seen.add(n)
            txt = G.disasm(self.bin, self.arch, [self.fns[n]])
            texts[n] = txt
            for m in re.finditer(r'\b(?:call|bl)\s+(?:0x)?([0-9a-f]+)\s*<([^>]+)>', txt):
                a = int(m.group(1), 16)
                callee = self.byaddr.get(a)
                if callee is None:
                    # call into the middle of a function (duffzero+0x..): include the whole function
                    callee = re.sub(r'\+0x[0-9a-f]+$', '', m.group(2))
                if a in stubaddr or callee in self.stub_names:
                    continue
                if callee.startswith('runtime.') and not callee.startswith(INCLUDE_RT):
                    continue
                if callee.startswith(('fmt.', 'sync.', 'internal/', 'reflect.', 'log', 'errors.')):
                    continue
                want.append(callee)
        text = '\n'.join(texts[n] for n in sorted(texts, key=lambda k: self.fns[k][0]))
        if text_patch:
            text = text_patch(text)
        return {n: self.fns[n] for n in texts}, text

    # ---- register ABI
    def regs(self, cpu, n):
        if self.arch == 'amd64':
            return [cpu.r[k] for k in ('rax', 'rbx', 'rcx', 'rdi', 'rsi', 'r8', 'r9')[:n]]
        return cpu.x[:n]

    def ret(self, cpu, *vals):
        if self.arch == 'amd64':
            for k, v in zip(('rax', 'rbx', 'rcx'), vals):
                cpu.r[k] = v & M64
        else:
            for i, v in enumerate(vals):
                cpu.x[i] = v & M64

    def rd(self, cpu, a, n):
        return cpu.read(a, n) if self.arch == 'amd64' else cpu.m.read(a, n)

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

    def externs(self, w):
        ext, f = {}, self.fns
        def stopper(n):
            def s(cpu): raise Stop('call ' + n)
            return s
        for n in f:
            if n.startswith('runtime.') and n not in self.stub_names and not n.startswith(INCLUDE_RT) \
                    and not n.startswith('runtime.mallocgc'):
                pass
        for n in f:
            if n.startswith('runtime.mallocgc') and n != 'runtime.mallocgc':
                def mal(cpu, n=n):
                    self.stubbed.add(n)
                    size = self.regs(cpu, 1)[0]
                    a = w.alloc(size); self.wbytes(cpu, a, bytes(size)); self.ret(cpu, a)
                ext[f[n][0]] = mal

        def key(cpu, t, kp):
            return self.rbytes(cpu, kp, w.keysize(t))

        def m_get(h):
            if h == 0:
                return {}
            if h not in w.maps:
                raise Stop('map call on unknown handle %x' % h)
            return w.maps[h]

        def m_access1(cpu):
            self.stubbed.add('runtime.mapaccess1')
            t, h, kp = self.regs(cpu, 3)
            k = key(cpu, t, kp); d = m_get(h)
            if k in d:
                self.ret(cpu, d[k])
            else:
                es = w.elemsize(t); z = w.alloc(es); self.wbytes(cpu, z, bytes(es)); self.ret(cpu, z)
            w.calls.append(('get', h, k))

        def m_access2(cpu):
            self.stubbed.add('runtime.mapaccess2')
            t, h, kp = self.regs(cpu, 3)
            k = key(cpu, t, kp); d = m_get(h)
            if k in d:
                self.ret(cpu, d[k], 1)
            else:
                es = w.elemsize(t); z = w.alloc(es); self.wbytes(cpu, z, bytes(es)); self.ret(cpu, z, 0)
            w.calls.append(('get2', h, k))

        def m_assign(cpu):
            self.stubbed.add('runtime.mapassign')
            t, h, kp = self.regs(cpu, 3)
            if h == 0:
                raise Stop('assignment to nil map')
            k = key(cpu, t, kp); d = m_get(h)
            if k not in d:
                es = w.elemsize(t); a = w.alloc(es); self.wbytes(cpu, a, bytes(es)); d[k] = a
                w.setlen(h)
            self.ret(cpu, d[k])
            w.calls.append(('assign', h, k))

        def m_delete(cpu):
            self.stubbed.add('runtime.mapdelete')
            t, h, kp = self.regs(cpu, 3)
            k = key(cpu, t, kp)
            if h:
                m_get(h).pop(k, None)
                w.setlen(h)
            w.calls.append(('delete', h, k))

        def m_small(cpu):
            self.stubbed.add('runtime.makemap_small')
            self.ret(cpu, w.newmap())

        def m_make(cpu):
            self.stubbed.add('runtime.makemap')
            t, hint, h = self.regs(cpu, 3)
            self.ret(cpu, w.newmap())

        def memeq(cpu):
            self.stubbed.add('runtime.memequal')
            a, b, n = self.regs(cpu, 3)
            self.ret(cpu, int(self.rbytes(cpu, a, n) == self.rbytes(cpu, b, n)))

        def memmove(cpu):
            self.stubbed.add('runtime.memmove')
            d, s, n = self.regs(cpu, 3)
            self.wbytes(cpu, d, self.rbytes(cpu, s, n))

        def conv(cpu, name='runtime.convT'):
            self.stubbed.add(name)
            t, p = self.regs(cpu, 2)
            size = self.img.read(t, 8)
            a = w.alloc(max(size, 1)); self.wbytes(cpu, a, self.rbytes(cpu, p, size)); self.ret(cpu, a)

        def grow(cpu):
            self.stubbed.add('runtime.growslice')
            old, newlen, oldcap, num, et = self.regs(cpu, 5)
            es = self.img.read(et, 8)
            cap = max(newlen, 2 * oldcap, 4)
            a = w.alloc(cap * es); self.wbytes(cpu, a, bytes(cap * es))
            oldlen = newlen - num
            if old and oldlen:
                self.wbytes(cpu, a, self.rbytes(cpu, old, oldlen * es))
            self.ret(cpu, a, newlen, cap)

        def newobj(cpu):
            self.stubbed.add('runtime.newobject')
            t, = self.regs(cpu, 1)
            size = self.img.read(t, 8)
            a = w.alloc(max(size, 1)); self.wbytes(cpu, a, bytes(size)); self.ret(cpu, a)

        table = {'runtime.mapaccess1': m_access1, 'runtime.mapaccess2': m_access2, 'runtime.mapassign': m_assign,
                 'runtime.mapdelete': m_delete, 'runtime.makemap_small': m_small, 'runtime.makemap': m_make,
                 'runtime.memequal': memeq, 'runtime.memmove': memmove,
                 'runtime.convT': conv, 'runtime.convTnoptr': lambda c: conv(c, 'runtime.convTnoptr'),
                 'runtime.growslice': grow, 'runtime.newobject': newobj}
        for n, fn in table.items():
            if n in f:
                ext[f[n][0]] = fn
        # every other runtime function that the program calls stops the run
        for m in re.finditer(r'\b(?:call|bl)\s+(?:0x)?([0-9a-f]+)\s*<([^>]+)>', self.text):
            a = int(m.group(1), 16)
            nm = self.byaddr.get(a, m.group(2))
            if a not in ext and nm.startswith(('runtime.', 'fmt.', 'sync.', 'internal/', 'reflect.', 'errors.')) \
                    and not nm.startswith(INCLUDE_RT) and not nm.startswith('runtime.mallocgc'):
                ext[a] = stopper(nm)
        return ext

    def cpu(self, w):
        ext = self.externs(w)
        if self.arch == 'amd64':
            c = XC(self.prog, self.img, ext, {})
            c.write(GSTRUCT, 8, 0); c.write(GSTRUCT + 0x10, 8, 0)
            return c
        mem = A64Mem(self.img)
        # cycle 32: 32 MB of model memory per state on arm64 (the first runs with 128 MB per state hit the memory limit)
        mem.add(BASE, 0x2000000)
        mem.add(GSTRUCT, 0x1000)
        mem.add(SP_LO, SP_TOP - SP_LO + 0x100)
        return AC(self.prog, mem, externs=ext, faults={})

    def call(self, c, entry, args):
        if self.arch == 'amd64':
            for k, v in zip(('rax', 'rbx', 'rcx', 'rdi', 'rsi'), args):
                c.r[k] = v & M64
            c.r['r14'] = GSTRUCT
            c.y[15] = 0
            x86emu.VISITED.clear()
            c.call(entry, [], maxsteps=3_000_000)
            self.visited |= x86emu.VISITED
            return c.r['rax'], c.r['rbx'], c.r['rcx']
        c.x[31] = SP_TOP
        c.x[28] = GSTRUCT
        c.x[29] = 0
        c.call(entry, list(args), maxsteps=3_000_000)
        self.visited |= c.visited
        return c.x[0], c.x[1], c.x[2]


class World:
    def __init__(self, model):
        self.m = model
        self.maps = {}
        self.nexth = H0
        self.heap = HEAP0
        self.calls = []

    def newmap(self):
        # a map handle is a 0x40 byte header in model memory whose first word is the element count, as the
        # inlined len(m) of the swiss map runtime reads it (internal/runtime/maps.Map.used at offset 0)
        h = self.alloc(0x40)
        self.maps[h] = {}
        self.m.wbytes(self.cpu, h, bytes(0x40))
        return h

    def setlen(self, h):
        self.m.wr(self.cpu, h, 8, len(self.maps[h]))

    def alloc(self, n):
        a = self.heap
        self.heap += (n + 15) & ~15
        if self.heap > BASE + 0x2000000:
            raise Stop('heap exhausted')
        return a

    def keysize(self, mtype):
        return self.m.img.read(self.m.img.read(mtype + 0x30, 8), 8)

    def elemsize(self, mtype):
        return self.m.img.read(self.m.img.read(mtype + 0x38, 8), 8)


class XC(X64):
    def __init__(self, prog, img, externs, faults):
        super().__init__(prog, img, externs, faults)

    def read(self, a, n):
        if (BASE <= a and a + n <= LIMIT) or (GSTRUCT <= a < GSTRUCT + 0x1000) or (SP_LO <= a <= SP_TOP + 0x100) or a in self.mem:
            return super(models.CPU2, self).read(a, n)
        v = self.img.read(a, n)
        if v is None:
            raise Stop('read %d at %x outside memory' % (n, a))
        return v

    def write(self, a, n, v):
        if (BASE <= a and a + n <= LIMIT) or (GSTRUCT <= a < GSTRUCT + 0x1000) or (SP_LO <= a and a + n <= SP_TOP + 0x100) \
                or a == 0x7f0000000028:
            return super(models.CPU2, self).write(a, n, v)
        raise Stop('write %d at %x outside memory' % (n, a))

    def i_bswap(self, o, pc, n):
        d = self.opnd(o[0])
        w = d[2] // 8
        self.put(d, int.from_bytes(self.get(d).to_bytes(w, 'little'), 'big'))
        return n

    def i_lock(self, o, pc, n):
        # lock xadd mem, reg (atomic.Int64.Add): single-threaded model
        parts = o[0].split(None, 1)
        if parts[0] != 'xadd':
            raise Stop('lock ' + parts[0])
        ops = [parts[1]] + o[1:]
        d, r = self.opnd(ops[0]), self.opnd(ops[1])
        old = self.get(d)
        self.put(d, (old + self.get(r)) & ((1 << d[2]) - 1))
        self.put(r, old)
        return n

    def i_jmp(self, o, pc, n):
        s = o[0].strip()
        if 'PTR' in s:
            # jump table of a switch (parallelJournalEntry.revert): target read through the operand
            return self.get(self.opnd(s))
        return super().i_jmp(o, pc, n)

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


class AC(ACPU):
    # exclusive load and store of the LL/SC atomics (internal/cpu.ARM64.HasATOMICS reads 0 from .bss, so the
    # binary takes this path); single-threaded model: the store always succeeds
    def i_ldaxr(self, o):
        return self.i_ldr(o)

    def i_stlxr(self, o):
        r = self.i_str(o[1:])
        self.wr(o[0], 0)
        return r

    def i_br(self, o):
        return self.rr(o[0])

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


class Bin:
    """One transaction's state in the model: EVM, scope, contract, StateDB, journal."""

    def __init__(self, model):
        self.m = model
        self.w = World(model)
        self.c = model.cpu(self.w)
        self.w.cpu = self.c
        m, c, C = model, self.c, model.c
        m.wr(c, EVM + C['evmSdb'], 8, model.itab_sdb)
        m.wr(c, EVM + C['evmSdb'] + 8, 8, STATEDB)
        m.wr(c, INTERP, 8, EVM)
        m.wr(c, STATEDB + C['tmap'], 8, self.w.newmap())
        if C['jptr'] is not None:
            m.wr(c, STATEDB + C['jptr'], 8, JOURNAL)
            m.wr(c, JOURNAL + 0x18, 8, self.w.newmap())  # dirties
        m.wr(c, SCOPE + 8, 8, STACKOBJ)
        m.wr(c, SCOPE + 0x10, 8, CONTRACT)
        L = C['layout']
        if L == 'arena':
            m.wr(c, STACKOBJ + 0x10, 8, ARENA)
            m.wr(c, ARENA, 8, DATA)
            m.wr(c, ARENA + 8, 8, NSLOT)
        if C['interp']:
            m.wr(c, CONTRACT + 0x28, 8, model.itab_acct)
            m.wr(c, CONTRACT + 0x30, 8, ADDRBUF)
        self.snaps = []
        self.sdbname = '(*%s)' % C['sdbType'].split('.')[1]

    def _stack(self, words):
        m, c, L = self.m, self.c, self.m.c['layout']
        stack = [0xa5a5] * 2 + words
        base = STACKOBJ + 8 if L == 'fixed' else DATA
        for i, x in enumerate(stack):
            m.wr(c, base + 32 * i, 32, x)
        if L == 'arena':
            m.wr(c, STACKOBJ, 8, 0)
            m.wr(c, STACKOBJ + 8, 8, len(stack))
            m.wr(c, ARENA + 0x18, 8, len(stack))
        elif L == 'fixed':
            m.wr(c, STACKOBJ, 8, len(stack))
        else:
            m.wr(c, STACKOBJ, 8, DATA)
            m.wr(c, STACKOBJ + 8, 8, len(stack))
            m.wr(c, STACKOBJ + 0x10, 8, NSLOT)
        return len(stack), base

    def _top(self):
        m, c, L = self.m, self.c, self.m.c['layout']
        if L == 'arena':
            return m.rd(c, ARENA + 0x18, 8)
        if L == 'fixed':
            return m.rd(c, STACKOBJ, 8)
        return m.rd(c, STACKOBJ + 8, 8)

    def _addr(self, a):
        if self.m.c['interp']:
            self.m.wbytes(self.c, ADDRBUF, a.to_bytes(20, 'big'))
        else:
            self.m.wbytes(self.c, CONTRACT + 0x14, a.to_bytes(20, 'big'))

    def _arg2(self):
        return INTERP if self.m.c['interp'] else EVM

    def st(self, a, s, v):
        self._addr(a)
        n, base = self._stack([v, s])
        r = self.m.call(self.c, self.m.fns[self.m.V + 'opTstore'][0], [PCPTR, self._arg2(), SCOPE])
        if any(r): raise Stop('opTstore returned %s' % (r,))
        if self._top() != n - 2: raise Stop('stack top after TSTORE')

    def ld(self, a, s):
        self._addr(a)
        n, base = self._stack([s])
        r = self.m.call(self.c, self.m.fns[self.m.V + 'opTload'][0], [PCPTR, self._arg2(), SCOPE])
        if any(r): raise Stop('opTload returned %s' % (r,))
        if self._top() != n: raise Stop('stack top after TLOAD')
        return self.m.rd(self.c, base + 32 * (n - 1), 32)

    def snap(self):
        r = self.m.call(self.c, self.m.fns[self.m.S + self.sdbname + '.Snapshot'][0], [STATEDB])
        self.snaps.append(r[0])

    def rev(self):
        rid = self.snaps.pop()
        self.m.call(self.c, self.m.fns[self.m.S + self.sdbname + '.RevertToSnapshot'][0], [STATEDB, rid])

    def commit(self):
        self.snaps.pop()


# ---- sequences: the cycle 31 Nitro theme generator, unchanged (tsdrive.py), seed 31_1211_01
SEED = 31_1211_01
MW = (1 << 256) - 1
PM = 0x360e68faccca8ca495c1b759fd9eee466db9fb32
OTHER = 0x8366a39cc670b4001a1121b8f6a443a643e40951


def kw(*xs): return int.from_bytes(keccak(b''.join((x & MW).to_bytes(32, 'big') for x in xs)), 'big')


FIXED = [0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b,
         0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23,
         0x1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95,
         0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9]
TARGETS = [0x66a9893cc07d91d95644aedd05d03f95e1dba8af, 0xd21fe301, 0xdead, 0]
CURRENCIES = [0, 0xaf88d065e77c8cc2239327c5edb3a432268e5831, 0x82af49447d8a07e3bd95bd0d56f35241523fbab1, 0xC0FFEE31]
DELTAS = [kw(t, c) for t in TARGETS for c in CURRENCIES]
NEAR = [DELTAS[1] ^ (1 << 0), DELTAS[1] ^ (1 << 64), DELTAS[1] ^ (1 << 128), DELTAS[1] ^ (1 << 255), DELTAS[1] ^ (0xff << 96),
        DELTAS[1] ^ (1 << 248)]  # cycle 32: bit 248, the bit Avalanche clears in SLOAD and SSTORE keys
SLOTS = FIXED + DELTAS + NEAR
VALUES = [0, 1, MW, (1 << 255), (-10 ** 18) & MW, 10 ** 18, (1 << 127) - 1, (-(1 << 127)) & MW, 2, 3]
ADDRS = [PM, OTHER, PM ^ (1 << 100)]


def gen(rnd):
    steps, depth, hist = [], 0, {}
    for _ in range(rnd.randrange(4, 40)):
        r = rnd.random()
        a = ADDRS[0] if rnd.random() < 0.8 else rnd.choice(ADDRS)
        s = rnd.choice(SLOTS[:8] if rnd.random() < 0.5 else SLOTS)
        if r < 0.40:
            v = rnd.choice(VALUES) if rnd.random() < 0.6 else rnd.getrandbits(256)
            if rnd.random() < 0.15 and (a, s) in hist:
                v = hist[(a, s)]
            steps.append(('st', a, s, v)); hist[(a, s)] = v
        elif r < 0.70:
            steps.append(('ld', a, s))
        elif r < 0.82 and depth < 6:
            steps.append(('snap',)); depth += 1
        elif depth:
            steps.append(('rev',) if rnd.random() < 0.6 else ('commit',)); depth -= 1
    while depth:
        steps.append(('rev',) if rnd.random() < 0.5 else ('commit',)); depth -= 1
    steps += [('ld', a, s) for a in ADDRS[:2] for s in SLOTS[:8]]
    return steps


def fixed_sequences():
    d, c = DELTAS[1], FIXED[0]
    yield [('st', PM, d, 5), ('snap',), ('st', PM, d, 7), ('rev',), ('ld', PM, d)]
    yield [('st', PM, d, 5), ('snap',), ('st', PM, d, 5), ('st', PM, d, 9), ('rev',), ('ld', PM, d)]
    yield [('snap',), ('st', PM, d, 5), ('snap',), ('st', PM, d, 0), ('rev',), ('ld', PM, d), ('rev',), ('ld', PM, d)]
    yield [('st', PM, c, 1), ('snap',), ('st', PM, c, 2), ('snap',), ('st', PM, c, 1), ('commit',), ('rev',), ('ld', PM, c)]
    yield [('st', PM, d, MW), ('snap',), ('st', PM, d, 0), ('st', PM, d, 3), ('rev',), ('ld', PM, d), ('ld', OTHER, d)]
    yield [('st', PM, NEAR[i], 11 + i) for i in range(6)] + [('ld', PM, d)] + [('ld', PM, x) for x in NEAR]
    yield [('st', PM, d, 1), ('st', OTHER, d, 2), ('snap',), ('st', OTHER, d, 0), ('rev',), ('ld', PM, d), ('ld', OTHER, d)]
    # snapshot ids out of order: revert an outer snapshot while inner ones are open (the call family never does
    # this, but the id lookup must still find the right journal index)
    yield [('st', PM, d, 1), ('snap',), ('st', PM, d, 2), ('snap',), ('st', PM, d, 3), ('snap',), ('st', PM, d, 4),
           ('rev',), ('ld', PM, d), ('rev',), ('ld', PM, d), ('rev',), ('ld', PM, d)]


class Ref:
    CODE = assemble([('PUSH', 0), 'CALLDATALOAD', ('PUSH', 1), 'EQ', ('REF', 'st'), 'JUMPI',
                     ('PUSH', 32), 'CALLDATALOAD', 'TLOAD', ('PUSH', 0), 'MSTORE', ('PUSH', 32), ('PUSH', 0), 'RETURN',
                     ('LABEL', 'st'), ('PUSH', 64), 'CALLDATALOAD', ('PUSH', 32), 'CALLDATALOAD', 'TSTORE', 'STOP'])

    def __init__(self):
        self.w = PE.World({a: self.CODE for a in ADDRS})
        self.snaps = []

    def st(self, a, s, v):
        ok, _ = self.w.call(1, a, 0, (1).to_bytes(32, 'big') + s.to_bytes(32, 'big') + v.to_bytes(32, 'big'), False, 1)
        assert ok

    def ld(self, a, s):
        ok, r = self.w.call(1, a, 0, (2).to_bytes(32, 'big') + s.to_bytes(32, 'big'), False, 1)
        assert ok
        return int.from_bytes(r, 'big')

    def snap(self): self.snaps.append(self.w.snapshot())
    def rev(self): self.w.restore(self.snaps.pop())
    def commit(self): self.snaps.pop()


def run(target, nseq, out, text_patch=None, fault='none'):
    model = Model(target, text_patch=text_patch)
    rnd = random.Random(SEED)
    seqs = list(fixed_sequences()) + [gen(rnd) for _ in range(nseq)]
    res = {'target': target, 'fault': fault, 'seed': SEED, 'bin': model.bin, 'itabStateDB': hex(model.itab_sdb),
           'functions': sorted(model.ranges), 'sequences': len(seqs), 'steps': 0, 'reads': 0, 'stores': 0,
           'reverts': 0, 'equalWrites': 0, 'mismatches': [], 'errors': [], 'started': time.time()}
    keyinfo = None
    import gc
    for qi, seq in enumerate(seqs):
        if qi % 200 == 0:
            gc.collect()
        ref = Ref()
        try:
            b = Bin(model)
            last = {}
            for st in seq:
                res['steps'] += 1
                if st[0] == 'st':
                    if last.get((st[1], st[2])) == st[3]: res['equalWrites'] += 1
                    ref.st(*st[1:]); b.st(*st[1:]); res['stores'] += 1
                    last[(st[1], st[2])] = st[3]
                elif st[0] == 'ld':
                    x, y = ref.ld(*st[1:]), b.ld(*st[1:]); res['reads'] += 1
                    if x != y:
                        res['mismatches'].append({'seq': qi, 'steps': [[hex(v) if isinstance(v, int) else v for v in s] for s in seq],
                                                  'at': [hex(v) if isinstance(v, int) else v for v in st], 'ref': hex(x), 'bin': hex(y)})
                        break
                elif st[0] == 'snap':
                    ref.snap(); b.snap()
                elif st[0] == 'rev':
                    ref.rev(); b.rev(); res['reverts'] += 1; last = {}
                else:
                    ref.commit(); b.commit()
            if keyinfo is None:
                keyinfo = sorted({(c[0], len(c[2])) for c in b.w.calls})
        except (Stop, AStop) as e:
            res['errors'].append({'seq': qi, 'error': str(e)})
            if len(res['errors']) > 50:
                break
    res['mapKeySizes'] = keyinfo
    res['visited'] = len(model.visited)
    res['textInstructions'] = len(model.prog.ins) if hasattr(model.prog, 'ins') else None
    res['stubbed'] = sorted(model.stubbed)
    res['elapsed'] = time.time() - res['started']
    json.dump(res, open(out, 'w'), indent=1)
    print(target, fault, 'seqs', len(seqs), 'reads', res['reads'], 'reverts', res['reverts'], 'mismatches',
          len(res['mismatches']), 'errors', len(res['errors']), (res['errors'][:1] or [''])[0], 'keys', keyinfo)
    return res


if __name__ == '__main__':
    run(sys.argv[1], int(sys.argv[2]), sys.argv[3])
