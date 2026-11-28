"""Cycle 38: the generated interpreter loop of the released geth v1.17.10 binary, (*EVM).execUntraced
(core/vm/interpreter_gen.go:18), run whole in the x86-64 model. This is the loop that block import and eth_call take
when no tracer is set. The release is built with -pgo=default.pgo, so the bodies of the hot handlers (ADD, MUL, SUB,
DIV, MULMOD, SIGNEXTEND, LT, GT, SLT, SGT, EQ, ISZERO, AND, OR, NOT, SHL, SHR, SAR, PUSH*, JUMP, JUMPI, ...) are
inlined into this one function and are different machine code from the out-of-line op* functions that drive.py runs.

The binary is read as data only: objdump prints the text, constants are read from the file image. Nothing from it is
executed, loaded or mapped executable; the text is interpreted by the model CPU of emu/x86emu*.py.

Model state (all in the SCOPE region of goshim): ScopeContext {Memory, Stack, Contract}; Stack {bottom, size, inner};
stackArena {data ptr, len, cap, top}; Contract with Code at +0x50, analysis at +0x38 and Gas.ExecutionGas at +0xa8,
read from execUntraced, validJumpdest and isCode of this build; EVM with the jump table pointer at +0xc8. Opcodes
that the switch sends to the table (default case) get an operation {execute funcval, constantGas, dynamicGas nil,
minStack, maxStack, memorySize nil}; their execute points at the real out-of-line op function of the build (SDIV,
MOD, SMOD, ADDMOD, EXP, BYTE, ...), so those run inside the loop as well. STOP's execute points at a model address
that ends the run. The .bss/.noptrbss sections read as zero (the write barrier flag is off).
"""
import os, re, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, 'emu'))
import goshim as G
import models
from models import X64, SP_TOP, SP_LO
import x86emu
from x86emu2 import rewrite_rip
from x86emu import Prog as XProg, Stop, M64

VM = 'github.com/ethereum/go-ethereum/core/vm.'
S = G.SCOPE
SCOPEC, STACKO, ARENAO, CONTRACT, MEMO, EVMA, TABLE, OPS, FVALS = S, S + 0x100, S + 0x200, S + 0x400, S + 0x800, S + 0x1000, S + 0x3000, S + 0x4000, S + 0x9000
BITMAP, CODE, SDATA, HEAP, HEAP_END = S + 0xa000, S + 0x20000, S + 0x40000, S + 0x100000, S + 0x200000
DONE = 0x10
NSTACK = 1025
RULES = [1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0]


class Done(Exception):
    pass


def nobits(path):
    f = open(path, 'rb').read()
    shoff, = struct.unpack_from('<Q', f, 0x28)
    se, sn = struct.unpack_from('<HH', f, 0x3a)
    out = []
    for i in range(sn):
        name, typ, flags, addr, off, size = struct.unpack_from('<IIQQQQ', f, shoff + i * se)
        if typ == 8 and addr and (flags & 2):
            out.append((addr, addr + size))
    return out


class LoopCPU(X64):
    def __init__(self, prog, img, externs, faults, bss):
        self.bss = bss
        super().__init__(prog, img, externs, faults)

    def read(self, a, n):
        a &= M64
        if self.fs - 0x100 <= a < self.fs + 0x100:  # TLS block: the g pointer at fs-0x10 (Go on linux/amd64)
            return super(X64, self).read(a, n)
        for lo, hi in self.bss:
            if lo <= a and a + n <= hi:
                return super(X64, self).read(a, n)
        return super().read(a, n)

    def _target(self, s):
        if re.match(r'^(0x)?[0-9a-f]+$', s):
            return int(s, 16)
        return self.get(self.opnd(s))  # register or memory operand: computed target (switch tables, funcvals)

    def i_call(self, o, pc, n):
        t = self._target(o[0])
        if t in self.externs:
            self.externs[t](self); return n
        self.r['rsp'] -= 8; self.write(self.r['rsp'], 8, n); return t

    def i_jmp(self, o, pc, n):
        t = self._target(o[0])
        if t in self.externs:
            self.externs[t](self)
            a = self.read(self.r['rsp'], 8); self.r['rsp'] += 8; return a
        return t

    def _rot(self, o, left):
        d = self.opnd(o[0]); w = d[2]
        k = self.get(self.opnd(o[1])) % w if len(o) > 1 else 1
        v = self.get(d)
        if k:
            v = ((v << k) | (v >> (w - k))) & ((1 << w) - 1) if left else ((v >> k) | (v << (w - k))) & ((1 << w) - 1)
            self.cf = (v & 1) if left else (v >> (w - 1)) & 1
        self.put(d, v)

    def i_rol(self, o, pc, n): self._rot(o, True)
    def i_ror(self, o, pc, n): self._rot(o, False)

    def i_bswap(self, o, pc, n):
        d = self.opnd(o[0])
        w = d[2] // 8
        self.put(d, int.from_bytes(self.get(d).to_bytes(w, 'little'), 'big'))

    def write(self, a, n, v):
        a &= M64
        if self.fs - 0x100 <= a < self.fs + 0x100:
            return super(X64, self).write(a, n, v)
        for lo, hi in self.bss:
            if lo <= a and a + n <= hi:
                return super(X64, self).write(a, n, v)
        return super().write(a, n, v)


class Loop:
    TABLE_OPS = {}  # opcode -> (handler name, minStack, maxStack)

    def __init__(self, binpath, fnpath, faults=None, text_patch=None):
        self.img = G.Image(binpath)
        self.fns = G.fnlist(fnpath)
        names = [n for n in self.fns if n.startswith(('github.com/holiman/uint256.', 'math/bits.'))
                 and 'type:' not in n]
        names += [n for n in self.fns if n.startswith(VM) and (n[len(VM):].startswith(('op', '(*Contract).', '(*Stack).', 'makePush', 'makeDup', 'makeSwap', 'codeBitmap', '(*EVM).execUntraced', 'BitVec', 'bitvec')))]
        self.names = sorted(set(names))
        ranges = [self.fns[n] for n in self.names]
        text = G.disasm(binpath, 'amd64', ranges)
        if text_patch:
            text = text_patch(text)
        self.text = text
        self.prog = XProg(rewrite_rip(text))
        self.faults = faults or {}
        self.bss = nobits(binpath)
        self.entry = self.fns[VM + '(*EVM).execUntraced'][0]
        self.visited = set()
        self.ext = {}
        stopnames = ['runtime.morestack_noctxt', 'runtime.panicBounds', 'runtime.panicdivide', 'runtime.panicoverflow',
                     'runtime.gopanic', 'runtime.panicwrap', 'runtime.panicshift', 'runtime.growslice', 'runtime.makeslice',
                     'runtime.panicmakeslicelen', 'runtime.gcWriteBarrier2', 'runtime.ifaceeq',
                     'github.com/ethereum/go-ethereum/crypto.Keccak256Hash']
        for n in self.fns:
            if n in stopnames or n.startswith('runtime.mallocgc'):
                a = self.fns[n][0]
                self.ext[a] = (lambda cpu, n=n: (_ for _ in ()).throw(Stop('call ' + n)))
        for n, (a, b) in self.fns.items():
            if n == 'runtime.newobject':
                self.ext[a] = self._newobject
            if n == 'runtime.memmove':
                self.ext.setdefault(a, self._memmove)
            if n == 'runtime.memclrNoHeapPointers':
                self.ext[a] = self._memclr

        def done(cpu):
            raise Done()
        self.ext[DONE] = done

    # runtime stand-ins
    def _newobject(self, cpu):
        size = self.img.read(cpu.r['rax'], 8)
        p = self.heap
        self.heap += (size + 15) & ~15
        if self.heap > HEAP_END:
            raise Stop('model heap full')
        for i in range(0, size, 8):
            cpu.write(p + i, 8, 0)
        cpu.r['rax'] = p

    def _memmove(self, cpu):
        d, s_, n = cpu.r['rax'], cpu.r['rbx'], cpu.r['rcx']
        data = [cpu.read(s_ + i, 1) for i in range(n)]
        for i, v in enumerate(data):
            cpu.write(d + i, 1, v)

    def _memclr(self, cpu):
        d, n = cpu.r['rax'], cpu.r['rbx']
        for i in range(n):
            cpu.write(d + i, 1, 0)

    def run(self, code, gas=1 << 40, bitmap=None, init_stack=()):
        """Runs execUntraced on code. Returns (stack words bottom first, pc-independent status, steps, gas used)."""
        self.heap = HEAP
        cpu = LoopCPU(self.prog, self.img, self.ext, self.faults, self.bss)
        cpu.write(G.GSTRUCT, 8, 0); cpu.write(G.GSTRUCT + 0x10, 8, 0); cpu.write(cpu.fs - 0x10, 8, G.GSTRUCT)
        w = cpu.write
        # scope
        w(SCOPEC, 8, MEMO); w(SCOPEC + 8, 8, STACKO); w(SCOPEC + 0x10, 8, CONTRACT)
        for i in range(0, 0x40, 8):
            w(MEMO + i, 8, 0)
        # stack and arena
        w(STACKO, 8, 0); w(STACKO + 8, 8, len(init_stack)); w(STACKO + 0x10, 8, ARENAO)
        w(ARENAO, 8, SDATA); w(ARENAO + 8, 8, NSTACK); w(ARENAO + 0x10, 8, NSTACK); w(ARENAO + 0x18, 8, len(init_stack))
        for i, v in enumerate(init_stack):
            w(SDATA + 32 * i, 32, v)
        # contract
        for i in range(0, 0xe0, 8):
            w(CONTRACT + i, 8, 0)
        for i in range(0, len(code), 8):
            w(CODE + i, 8, int.from_bytes(code[i:i + 8].ljust(8, b'\0'), 'little'))
        w(CONTRACT + 0x50, 8, CODE); w(CONTRACT + 0x58, 8, len(code)); w(CONTRACT + 0x60, 8, len(code))
        if bitmap is not None:
            for i in range(0, len(bitmap), 8):
                w(BITMAP + i, 8, int.from_bytes(bitmap[i:i + 8].ljust(8, b'\0'), 'little'))
            w(CONTRACT + 0x38, 8, BITMAP); w(CONTRACT + 0x40, 8, len(bitmap)); w(CONTRACT + 0x48, 8, len(bitmap))
        w(CONTRACT + 0xa8, 8, gas)
        # evm
        for i in range(0, 0x400, 8):
            w(EVMA + i, 8, 0)
        w(EVMA + 0xc8, 8, TABLE)
        # chainRules (params.Rules, 20 bools) at +0xe0: mainnet at Osaka; EIP-4762, Amsterdam, Bogota and UBT off
        for i, b in enumerate(RULES):
            w(EVMA + 0xe0 + i, 1, b)
        self._table(cpu)
        cpu.r['rax'] = EVMA; cpu.r['rbx'] = SCOPEC
        cpu.r['r14'] = G.GSTRUCT
        cpu.y[15] = 0
        x86emu.VISITED.clear()
        status = 'returned'
        try:
            cpu.call(self.entry, [], maxsteps=20_000_000)
        except Done:
            status = 'stop'
        self.visited |= x86emu.VISITED
        top = cpu.read(ARENAO + 0x18, 8)
        size = cpu.read(STACKO + 8, 8)
        if top != size:
            raise Stop('arena top %d != stack size %d' % (top, size))
        if cpu.read(ARENAO, 8) != SDATA:
            raise Stop('arena data moved')
        words = [cpu.read(SDATA + 32 * i, 32) for i in range(size)]
        return words, status, cpu.steps, gas - cpu.read(CONTRACT + 0xa8, 8), cpu

    def _table(self, cpu):
        w = cpu.write
        for op in range(256):
            w(TABLE + 8 * op, 8, 0)
        k = 0
        for op, (hname, mn, mx) in self.TABLE_OPS.items():
            o = OPS + 0x40 * k; fv = FVALS + 8 * k; k += 1
            code = DONE if hname is None else self.fns[VM + hname][0]
            w(fv, 8, code)
            w(o, 8, fv); w(o + 8, 8, 0); w(o + 0x10, 8, 0); w(o + 0x18, 8, mn); w(o + 0x20, 8, mx); w(o + 0x28, 8, 0); w(o + 0x30, 8, 0)
            w(TABLE + 8 * op, 8, o)


# opcodes the generated switch does not handle itself, with the table entry the model gives them
Loop.TABLE_OPS = {
    0x00: (None, 0, 1024),
    0x05: ('opSdiv', 2, 1024), 0x06: ('opMod', 2, 1024), 0x07: ('opSmod', 2, 1024), 0x08: ('opAddmod', 3, 1024),
    0x0a: ('opExp', 2, 1024), 0x1a: ('opByte', 2, 1024), 0x18: ('opXor', 2, 1024),
}
