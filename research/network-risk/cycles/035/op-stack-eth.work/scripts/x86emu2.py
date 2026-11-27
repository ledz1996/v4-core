"""Extensions of the cycle 27 x86-64 model (x86emu.py, copied unchanged) for the tempo v1.19.1 routines.

Adds: rip-relative operands (rewritten to the absolute address objdump prints in its comment),
file-backed read-only memory for the binary's constants, calls and jumps through GOT slots to
modelled externs, and the SSE2 instructions the ruint and handler code of the release uses.
Nothing from the release binary is executed; its disassembly text is interpreted.
"""
import re
import x86emu
from x86emu import CPU, Prog, Stop, M64

M128 = (1 << 128) - 1


def rewrite_rip(text):
    out = []
    for line in text.splitlines():
        m = re.search(r'\[rip([+-]0x[0-9a-f]+)\]', line)
        if m:
            c = re.search(r'#\s*([0-9a-f]+)', line)
            if not c:
                raise Stop('rip operand without comment: ' + line)
            line = line[:m.start()] + '[0x%s]' % c.group(1) + line[m.end():]
        out.append(line)
    return '\n'.join(out)


def lanes(v, w, n):
    m = (1 << w) - 1
    return [(v >> (w * i)) & m for i in range(n)]


def pack(ls, w):
    v = 0
    for i, x in enumerate(ls):
        v |= (x & ((1 << w) - 1)) << (w * i)
    return v


class CPU2(CPU):
    def __init__(self, prog, filebytes, file_hi, externs=None, got=None, faults=None):
        super().__init__(prog, externs)
        self.fb = filebytes
        self.fhi = file_hi
        self.got = got or {}
        self.faults = faults or {}
        self.visited = set()

    def read(self, a, n):
        if a + n <= self.fhi and not any((a + i) in self.mem for i in range(n)):
            return int.from_bytes(self.fb[a:a + n], 'little')
        return super().read(a, n)

    def step(self, pc):
        self.visited.add(pc)
        if pc in self.faults:
            saved = self.p.ins[pc]
            self.p.ins[pc] = self.faults[pc]
            try:
                return super().step(pc)
            finally:
                self.p.ins[pc] = saved
        return super().step(pc)

    def _indirect(self, s):
        m = re.match(r'^QWORD PTR \[0x([0-9a-f]+)\]$', s)
        if m:
            slot = int(m.group(1), 16)
            if slot in self.got:
                return self.got[slot]
            raise Stop('indirect through %x' % slot)
        return None

    def i_call(self, o, pc, n):
        f = self._indirect(o[0])
        if f is not None:
            f(self); return n
        t = int(o[0], 16)
        if t in self.externs:
            self.externs[t](self); return n
        self.r['rsp'] -= 8; self.write(self.r['rsp'], 8, n); return t

    def i_jmp(self, o, pc, n):
        f = self._indirect(o[0])
        if f is not None:
            f(self)
            a = self.read(self.r['rsp'], 8); self.r['rsp'] += 8; return a
        t = int(o[0], 16)
        if t in self.externs:
            self.externs[t](self)
            a = self.read(self.r['rsp'], 8); self.r['rsp'] += 8; return a
        return t

    def i_int3(self, o, pc, n): raise Stop('int3 reached')
    def i_ud2(self, o, pc, n): raise Stop('ud2 reached')
    def i_xchg(self, o, pc, n):
        a = self.opnd(o[0]); b = self.opnd(o[1]); va, vb = self.get(a), self.get(b); self.put(a, vb); self.put(b, va)
    def i_cdqe(self, o, pc, n):
        v = self.r['rax'] & 0xffffffff
        self.r['rax'] = (v - (1 << 32)) & M64 if v >> 31 else v
    def i_bsr(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]; x = self.get(self.opnd(o[1]), b)
        if x == 0:
            self.zf = 1; return  # destination undefined; keep it
        self.zf = 0; self.put(d, x.bit_length() - 1)
    def i_bsf(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]; x = self.get(self.opnd(o[1]), b)
        if x == 0:
            self.zf = 1; return
        self.zf = 0; self.put(d, (x & -x).bit_length() - 1)
    def i_bt(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]; x = self.get(d); k = self.get(self.opnd(o[1]), b) % b
        self.cf = (x >> k) & 1

    # SSE moves: legacy encodings keep the upper ymm half; the model keeps 128 bit values
    def _x(self, s):
        o = self.opnd(s)
        return o
    def _xget(self, o):
        if o[0] == 'r' and o[1].startswith('xmm'):
            return self.y[int(o[1][3:])] & M128
        return self.get(o)
    def _xput(self, o, v):
        if o[0] == 'r' and o[1].startswith('xmm'):
            i = int(o[1][3:]); self.y[i] = (self.y[i] & ~M128) | (v & M128)
        else:
            self.put(o, v)
    def _mov128(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1])
        if s[0] == 'm':
            v = self.read(s[1], 16)
        else:
            v = self._xget(s)
        if d[0] == 'm':
            self.write(d[1], 16, v)
        else:
            self._xput(d, v)
    i_movdqu = i_movdqa = i_movups = i_movaps = i_movapd = i_movupd = _mov128
    def i_movq(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1])
        if s[0] == 'r' and s[1].startswith('xmm'):
            v = self.y[int(s[1][3:])] & M64
        elif s[0] == 'm':
            v = self.read(s[1], 8)
        else:
            v = self.get(s)
        if d[0] == 'r' and d[1].startswith('xmm'):
            self._xput(d, v & M64)
        elif d[0] == 'm':
            self.write(d[1], 8, v)
        else:
            self.put(d, v & M64)
    def i_movd(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1])
        if s[0] == 'r' and s[1].startswith('xmm'):
            v = self.y[int(s[1][3:])] & 0xffffffff
        elif s[0] == 'm':
            v = self.read(s[1], 4)
        else:
            v = self.get(s) & 0xffffffff
        if d[0] == 'r' and d[1].startswith('xmm'):
            self._xput(d, v)
        else:
            self.put(d, v)
    def i_movsd(self, o, pc, n):
        d = self.opnd(o[0]); src = self.opnd(o[1])
        if src[0] == 'm' and d[0] == 'r':
            self._xput(d, self.read(src[1], 8))  # load zeroes bits 127:64
        elif d[0] == 'm':
            self.write(d[1], 8, self._xget(src) & M64)
        else:
            self._xput(d, (self._xget(d) & ~M64 & M128) | (self._xget(src) & M64))
    def _bin128(self, o, fn):
        d = self.opnd(o[0]); s = self.opnd(o[1])
        a = self._xget(d); b = self.read(s[1], 16) if s[0] == 'm' else self._xget(s)
        self._xput(d, fn(a, b) & M128)
    def i_pxor(self, o, pc, n): self._bin128(o, lambda a, b: a ^ b)
    i_xorps = i_xorpd = i_pxor
    def i_por(self, o, pc, n): self._bin128(o, lambda a, b: a | b)
    i_orps = i_por
    def i_pand(self, o, pc, n): self._bin128(o, lambda a, b: a & b)
    i_andps = i_pand
    def i_pandn(self, o, pc, n): self._bin128(o, lambda a, b: (~a & M128) & b)
    i_andnps = i_pandn
    def _lw(self, o, w, fn):
        self._bin128(o, lambda a, b: pack([fn(x, y) for x, y in zip(lanes(a, w, 128 // w), lanes(b, w, 128 // w))], w))
    def i_pcmpeqb(self, o, pc, n): self._lw(o, 8, lambda x, y: 0xff if x == y else 0)
    def i_pcmpeqw(self, o, pc, n): self._lw(o, 16, lambda x, y: 0xffff if x == y else 0)
    def i_pcmpeqd(self, o, pc, n): self._lw(o, 32, lambda x, y: 0xffffffff if x == y else 0)
    def i_paddb(self, o, pc, n): self._lw(o, 8, lambda x, y: x + y)
    def i_psubb(self, o, pc, n): self._lw(o, 8, lambda x, y: x - y)
    def i_paddq(self, o, pc, n): self._lw(o, 64, lambda x, y: x + y)
    def i_psubq(self, o, pc, n): self._lw(o, 64, lambda x, y: x - y)
    def i_punpcklqdq(self, o, pc, n): self._bin128(o, lambda a, b: (a & M64) | ((b & M64) << 64))
    def i_punpckhqdq(self, o, pc, n): self._bin128(o, lambda a, b: (a >> 64) | ((b >> 64) << 64))
    def i_movlhps(self, o, pc, n): self._bin128(o, lambda a, b: (a & M64) | ((b & M64) << 64))
    def i_punpcklbw(self, o, pc, n):
        self._bin128(o, lambda a, b: pack([v for p in zip(lanes(a, 8, 8), lanes(b, 8, 8)) for v in p], 8))
    def i_packsswb(self, o, pc, n):
        def sat(x):
            x = x - 65536 if x >> 15 else x
            return max(-128, min(127, x)) & 0xff
        self._bin128(o, lambda a, b: pack([sat(x) for x in lanes(a, 16, 8) + lanes(b, 16, 8)], 8))
    def i_psadbw(self, o, pc, n):
        def f(a, b):
            la, lb = lanes(a, 8, 16), lanes(b, 8, 16)
            s0 = sum(abs(x - y) for x, y in zip(la[:8], lb[:8])); s1 = sum(abs(x - y) for x, y in zip(la[8:], lb[8:]))
            return s0 | (s1 << 64)
        self._bin128(o, f)
    def _shiftimm(self, o, w, left):
        d = self.opnd(o[0]); k = int(o[1], 0)
        a = self._xget(d)
        ls = lanes(a, w, 128 // w)
        ls = [0 if k >= w else ((x << k) if left else (x >> k)) for x in ls]
        self._xput(d, pack(ls, w))
    def i_psrlw(self, o, pc, n): self._shiftimm(o, 16, False)
    def i_psllw(self, o, pc, n): self._shiftimm(o, 16, True)
    def i_psrlq(self, o, pc, n): self._shiftimm(o, 64, False)
    def i_psllq(self, o, pc, n): self._shiftimm(o, 64, True)
    def i_pshufd(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1]); k = int(o[2], 0)
        a = self.read(s[1], 16) if s[0] == 'm' else self._xget(s)
        ls = lanes(a, 32, 4)
        self._xput(d, pack([ls[(k >> (2 * i)) & 3] for i in range(4)], 32))
    def i_movmskps(self, o, pc, n):
        d = self.opnd(o[0]); a = self._xget(self.opnd(o[1]))
        self.put(d, sum(((x >> 31) & 1) << i for i, x in enumerate(lanes(a, 32, 4))))
    def i_pmovmskb(self, o, pc, n):
        d = self.opnd(o[0]); a = self._xget(self.opnd(o[1]))
        self.put(d, sum(((x >> 7) & 1) << i for i, x in enumerate(lanes(a, 8, 16))))

    def i_div(self, o, pc, n):
        s = self.opnd(o[0]); b = s[2]
        dv = self.get(s)
        if dv == 0:
            raise Stop('#DE divide by zero')
        if b == 64:
            num = (self.r['rdx'] << 64) | self.r['rax']
            q, r = divmod(num, dv)
            if q > M64:
                raise Stop('#DE quotient overflow')
            self.r['rax'] = q; self.r['rdx'] = r
        elif b == 32:
            num = ((self.r['rdx'] & 0xffffffff) << 32) | (self.r['rax'] & 0xffffffff)
            q, r = divmod(num, dv)
            if q > 0xffffffff:
                raise Stop('#DE quotient overflow')
            self.r['rax'] = q; self.r['rdx'] = r
        else:
            raise Stop('div width %d' % b)

    def i_mul(self, o, pc, n):
        s = self.opnd(o[0]); b = s[2]
        if b == 64:
            return super().i_mul(o, pc, n)
        if b == 32:
            t = (self.r['rax'] & 0xffffffff) * self.get(s)
            self.r['rax'] = t & 0xffffffff; self.r['rdx'] = (t >> 32) & 0xffffffff
            self.cf = self.of = int(self.r['rdx'] != 0); return
        raise Stop('mul width %d' % b)
