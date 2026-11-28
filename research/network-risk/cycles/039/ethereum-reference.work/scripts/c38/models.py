"""Cycle 39 copy (adds the erigon handler call on arm64: pc in x0, evm in x1, scope in x2; results x0..x5 must be zero). Cycle 31 copy of the cycle 30 Nitro models, extended with the bor (fixed array) and libevm (slice) stack layouts.
Model CPUs for the shipped Go functions: the cycle 27/28 x86-64 model (x86emu.py, x86emu2.py, copied unchanged
into emu/) and the cycle 28 AArch64 model (a64emu.py, copied unchanged), each wrapped with the Go register ABI and the
core/vm stack shim described in goshim.py. Text comes from objdump; constants from goshim.Image."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emu'))
import goshim as G
import x86emu
from x86emu2 import CPU2, rewrite_rip
from x86emu import Prog as XProg, Stop, M64
import a64emu
from a64emu import CPU as ACPU, Prog as AProg, Mem as AMem

SP_TOP = 0x7ffff0000000
SP_LO = SP_TOP - 0x100000
OK_RANGES = [(G.SCOPE, G.SCOPE + 0x200000), (G.GSTRUCT, G.GSTRUCT + 0x1000), (SP_LO, SP_TOP + 0x100)]


class X64(CPU2):
    def __init__(self, prog, img, externs, faults):
        super().__init__(prog, None, 0, externs=externs, faults=faults)
        self.img = img
        self.memreads = []

    def read(self, a, n):
        if a in self.mem:
            return super(CPU2, self).read(a, n)
        for lo, hi in OK_RANGES:
            if lo <= a and a + n <= hi:
                return super(CPU2, self).read(a, n)
        v = self.img.read(a, n)
        if v is None:
            raise Stop('read %d at %x outside memory' % (n, a))
        self.memreads.append(a)
        return v

    def i_bts(self, o, pc, n):
        # bit test and set, register destination only (bit index modulo the operand width)
        d = self.opnd(o[0]); s = self.opnd(o[1])
        if d[0] != 'r':
            raise Stop('bts with memory destination')
        w = d[2]; k = self.get(s) % w; v = self.get(d)
        self.cf = (v >> k) & 1
        self.put(d, v | (1 << k))

    def i_movsx(self, o, pc, n):
        # sign extension from the source operand width to the destination width
        d = self.opnd(o[0]); s = self.opnd(o[1])
        w = s[2]; v = self.get(s)
        if v >> (w - 1) & 1:
            v -= 1 << w
        self.put(d, v & ((1 << d[2]) - 1))

    def write(self, a, n, v):
        for lo, hi in OK_RANGES:
            if lo <= a and a + n <= hi:
                return super(CPU2, self).write(a, n, v)
        if a == 0x7f0000000028:  # canary slot the base model writes at start
            return super(CPU2, self).write(a, n, v)
        raise Stop('write %d at %x outside memory' % (n, a))


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


class Model:
    def __init__(self, arch, binpath, fnpath, faults=None, text_patch=None, layout='arena'):
        self.arch = arch
        self.layout = layout
        self.img = G.Image(binpath)
        self.fns = G.fnlist(fnpath)
        ranges, self.missing, self.stops = G.collect(arch, self.fns)
        self.ranges = ranges
        text = G.disasm(binpath, arch, ranges.values())
        if text_patch:
            text = text_patch(text)
        self.text = text
        self.faults = faults or {}
        self.memmove = self.fns.get('runtime.memmove', (None,))[0]
        if arch == 'amd64':
            self.prog = XProg(rewrite_rip(text))
        else:
            self.prog = AProg([text])
        self.visited = set()

    def entry(self, name):
        return self.fns[name][0]

    # ---- amd64
    def _x64(self):
        ext = {}
        for a, n in self.stops.items():
            def stop(cpu, n=n): raise Stop('call ' + n)
            ext[a] = stop
        def memmove(cpu):
            d, s_, n = cpu.r['rax'], cpu.r['rbx'], cpu.r['rcx']
            data = [cpu.read(s_ + i, 1) for i in range(n)]
            for i, v in enumerate(data):
                cpu.write(d + i, 1, v)
        ext[self.memmove] = memmove
        cpu = X64(self.prog, self.img, ext, self.faults)
        cpu.write(G.GSTRUCT, 8, 0); cpu.write(G.GSTRUCT + 0x10, 8, 0)
        return cpu

    def _x64call(self, cpu, entry, regs):
        for k, v in regs.items():
            cpu.r[k] = v & M64
        cpu.r['r14'] = G.GSTRUCT
        cpu.y[15] = 0
        x86emu.VISITED.clear()
        cpu.call(entry, [], maxsteps=2_000_000)
        self.visited |= x86emu.VISITED

    # ---- arm64
    def _a64(self):
        mem = A64Mem(self.img)
        mem.add(G.SCOPE, 0x200000)
        mem.add(G.GSTRUCT, 0x1000)
        mem.add(SP_LO, SP_TOP - SP_LO + 0x100)
        ext = {}
        for a, n in self.stops.items():
            def stop(cpu, n=n): raise Stop('call ' + n)
            ext[a] = stop
        def memmove(cpu):
            d, s_, n = cpu.x[0], cpu.x[1], cpu.x[2]
            data = [cpu.m.read(s_ + i, 1) for i in range(n)]
            for i, v in enumerate(data):
                cpu.m.write(d + i, 1, v)
        ext[self.memmove] = memmove
        cpu = ACPU(self.prog, mem, externs=ext, faults=self.faults)
        return cpu

    def _a64call(self, cpu, entry, regs):
        cpu.x[31] = SP_TOP
        cpu.x[28] = G.GSTRUCT
        cpu.x[29] = 0
        cpu.call(entry, regs, maxsteps=2_000_000)
        self.visited |= cpu.visited

    # ---- public
    def wr(self, cpu, a, v, n=32):
        if self.arch == 'amd64':
            cpu.write(a, n, v)
        else:
            cpu.m.write(a, n, v)

    def rd(self, cpu, a, n=32):
        return cpu.read(a, n) if self.arch == 'amd64' else cpu.m.read(a, n)

    def run_handler(self, op, a, b, c=0):
        """Runs the core/vm handler on a modelled stack. a is the top of the stack."""
        k = G.ARITY.get(op, 2)
        words = [a, b, c][:k]
        cpu = self._x64() if self.arch == 'amd64' else self._a64()
        stack = [G.GUARD, G.GUARD] + list(reversed(words))
        L = self.layout
        # base of slot 0: arena and slice layouts keep data at G.DATA; the bor layout keeps it inline at Stack+8
        base = G.STACKOBJ + 8 if L == 'fixed' else (G.SCOPE + 0x230 if L == 'erigon' else G.DATA)
        self._base = base
        for i, w in enumerate(stack):
            self.wr(cpu, base + 32 * i, w)
        for i in range(len(stack), G.NSLOT):
            self.wr(cpu, base + 32 * i, G.GUARD)
        if L != 'erigon':
            self.wr(cpu, G.SCOPE + 8, G.STACKOBJ, 8)
        if L == 'erigon':
            # cycle 38: erigon v3.8.2 CallContext keeps Stack inline: data [1024]uint256.Int at +0x230, top at +0x8230
            self.wr(cpu, G.SCOPE + 0x8230, len(stack), 8)
        elif L == 'arena':
            self.wr(cpu, G.STACKOBJ, 0, 8)
            self.wr(cpu, G.STACKOBJ + 8, len(stack), 8)
            self.wr(cpu, G.STACKOBJ + 0x10, G.ARENA, 8)
            self.wr(cpu, G.ARENA, G.DATA, 8)
            self.wr(cpu, G.ARENA + 8, G.NSLOT, 8)
            self.wr(cpu, G.ARENA + 0x18, len(stack), 8)
        elif L == 'fixed':
            self.wr(cpu, G.STACKOBJ, len(stack), 8)
        elif L == 'slice':
            self.wr(cpu, G.STACKOBJ, G.DATA, 8)
            self.wr(cpu, G.STACKOBJ + 8, len(stack), 8)
            self.wr(cpu, G.STACKOBJ + 0x10, G.NSLOT, 8)
        entry = self.entry(G.VM + G.HANDLERS[op])
        if self.arch == 'amd64' and L == 'erigon':
            # erigon handler: (pc uint64, evm *EVM, scope *CallContext) (uint64, []byte, error); pc 0 in, pc 0 out
            self._x64call(cpu, entry, {'rax': 0, 'rbx': G.SCOPE + 0x180000, 'rcx': G.SCOPE})
            err = (cpu.r['rax'], cpu.r['rbx'], cpu.r['rcx'], cpu.r['rdi'], cpu.r['rsi'], cpu.r['r8'])
        elif self.arch == 'amd64':
            self._x64call(cpu, entry, {'rax': G.SCOPE + 0x800, 'rbx': G.SCOPE + 0x900, 'rcx': G.SCOPE})
            err = (cpu.r['rax'], cpu.r['rbx'], cpu.r['rcx'], cpu.r['rdi'], cpu.r['rsi'])
        elif L == 'erigon':
            self._a64call(cpu, entry, [0, G.SCOPE + 0x180000, G.SCOPE])
            err = tuple(cpu.x[0:6])
        else:
            self._a64call(cpu, entry, [G.SCOPE + 0x800, G.SCOPE + 0x900, G.SCOPE])
            err = tuple(cpu.x[0:5])
        if any(err):
            raise Stop('handler returned non-nil %s' % (err,))
        if L == 'erigon':
            top = cnt = self.rd(cpu, G.SCOPE + 0x8230, 8)
        elif L == 'arena':
            top = self.rd(cpu, G.ARENA + 0x18, 8)
            cnt = self.rd(cpu, G.STACKOBJ + 8, 8)
        elif L == 'fixed':
            top = cnt = self.rd(cpu, G.STACKOBJ, 8)
        else:
            top = cnt = self.rd(cpu, G.STACKOBJ + 8, 8)
            if self.rd(cpu, G.STACKOBJ, 8) != G.DATA or self.rd(cpu, G.STACKOBJ + 0x10, 8) != G.NSLOT:
                raise Stop('slice header changed')
        if top != len(stack) - k + 1 or cnt != top:
            raise Stop('stack top %d count %d' % (top, cnt))
        for i in range(2):
            if self.rd(cpu, base + 32 * i) != G.GUARD:
                raise Stop('guard word %d changed' % i)
        for i in range(len(stack), G.NSLOT):
            if self.rd(cpu, base + 32 * i) != G.GUARD:
                raise Stop('slot %d above the stack changed' % i)
        return self.rd(cpu, base + 32 * (top - 1)), cpu.steps

    def run_direct(self, op, a, b, c=0):
        """Calls the uint256 method directly: z.Op(x, y[, m]) with z, x, y, m distinct buffers."""
        cpu = self._x64() if self.arch == 'amd64' else self._a64()
        Z, X, Y, Mo = G.OPND, G.OPND + 0x40, G.OPND + 0x80, G.OPND + 0xc0
        self.wr(cpu, Z, G.GUARD); self.wr(cpu, X, a); self.wr(cpu, Y, b); self.wr(cpu, Mo, c)
        self.wr(cpu, G.OPND + 0x100, G.GUARD)
        entry = self.entry(G.U + G.DIRECT[op])
        cmp = op in ('SLT', 'SGT', 'LT', 'GT')
        if cmp:
            args = [X, Y]
        elif op in ('ADDMOD', 'MULMOD'):
            args = [Z, X, Y, Mo]
        else:
            args = [Z, X, Y]
        if self.arch == 'amd64':
            self._x64call(cpu, entry, dict(zip(['rax', 'rbx', 'rcx', 'rdi'], args)))
            r0 = cpu.r['rax']
        else:
            self._a64call(cpu, entry, args)
            r0 = cpu.x[0]
        if self.rd(cpu, X) != a or self.rd(cpu, Y) != b or self.rd(cpu, Mo) != c or self.rd(cpu, G.OPND + 0x100) != G.GUARD:
            raise Stop('input or guard changed')
        if cmp:
            if self.rd(cpu, Z) != G.GUARD:
                raise Stop('z written by comparison')
            return r0 & 1, cpu.steps
        if r0 != Z:
            raise Stop('returned pointer %x' % r0)
        return self.rd(cpu, Z), cpu.steps
