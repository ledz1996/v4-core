"""Small x86-64 interpreter over objdump -M intel text.

It is a model written for this review: it reads the disassembly text of a few
routines from the package and interprets it in Python. No machine code from the
package is run on the CPU. Unknown instructions raise, so a gap shows up as an
error and never as a silent wrong result.
"""
import re

M64 = (1 << 64) - 1

REG64 = ['rax', 'rcx', 'rdx', 'rbx', 'rsp', 'rbp', 'rsi', 'rdi'] + ['r%d' % i for i in range(8, 16)]
ALIAS = {}
for i, r in enumerate(REG64):
    ALIAS[r] = (r, 64)
legacy = {'rax': 'a', 'rcx': 'c', 'rdx': 'd', 'rbx': 'b'}
for r, l in legacy.items():
    ALIAS['e%sx' % l] = (r, 32); ALIAS['%sx' % l] = (r, 16); ALIAS['%sl' % l] = (r, 8)
for r, n in [('rsi', 'si'), ('rdi', 'di'), ('rbp', 'bp'), ('rsp', 'sp')]:
    ALIAS['e' + n] = (r, 32); ALIAS[n] = (r, 16); ALIAS[n + 'l'] = (r, 8)
for i in range(8, 16):
    ALIAS['r%dd' % i] = ('r%d' % i, 32); ALIAS['r%dw' % i] = ('r%d' % i, 16); ALIAS['r%db' % i] = ('r%d' % i, 8)

SIZEKW = {'BYTE': 8, 'WORD': 16, 'DWORD': 32, 'QWORD': 64, 'XMMWORD': 128, 'YMMWORD': 256}


VISITED = set()


class Stop(Exception):
    pass


class Prog:
    def __init__(self, text):
        self.ins = {}
        self.order = []
        self.labels = {}
        for line in text.splitlines():
            m = re.match(r'^\s*([0-9a-f]+):\s+(.*)$', line)
            if m:
                a = int(m.group(1), 16)
                body = re.sub(r'\s*<[^>]*>', '', m.group(2)).strip()
                body = body.split('#')[0].strip()
                if not body:
                    continue
                self.ins[a] = body
                self.order.append(a)
                continue
            m = re.match(r'^([0-9a-f]+) <(.*)>:', line)
            if m:
                self.labels[m.group(2)] = int(m.group(1), 16)
        self.order.sort()
        self.nxt = {a: b for a, b in zip(self.order, self.order[1:] + [None])}


class CPU:
    def __init__(self, prog, externs=None):
        self.p = prog
        self.r = {k: 0 for k in REG64}
        self.y = [0] * 16
        self.mem = {}
        self.cf = self.zf = self.sf = self.of = 0
        self.fs = 0x7f0000000000
        self.write(self.fs + 0x28, 8, 0x1122334455667788)
        self.externs = externs or {}
        self.count = {}
        self.steps = 0

    # memory
    def read(self, a, n):
        v = 0
        for i in range(n):
            v |= self.mem.get(a + i, 0) << (8 * i)
        return v

    def write(self, a, n, v):
        for i in range(n):
            self.mem[a + i] = (v >> (8 * i)) & 0xff

    # registers
    def getr(self, name):
        if name in ALIAS:
            r, b = ALIAS[name]
            return self.r[r] & ((1 << b) - 1), b
        m = re.match(r'^([xy])mm(\d+)$', name)
        if m:
            b = 128 if m.group(1) == 'x' else 256
            return self.y[int(m.group(2))] & ((1 << b) - 1), b
        raise Stop('reg ' + name)

    def setr(self, name, v, vex_zero=True):
        if name in ALIAS:
            r, b = ALIAS[name]
            if b == 64:
                self.r[r] = v & M64
            elif b == 32:
                self.r[r] = v & 0xffffffff
            else:
                mask = (1 << b) - 1
                self.r[r] = (self.r[r] & ~mask & M64) | (v & mask)
            return
        m = re.match(r'^([xy])mm(\d+)$', name)
        if m:
            b = 128 if m.group(1) == 'x' else 256
            # VEX encoded writes zero the upper bits
            self.y[int(m.group(2))] = v & ((1 << b) - 1)
            return
        raise Stop('reg ' + name)

    def ea(self, s):
        s = s.strip()
        seg = 0
        if s.startswith('fs:'):
            return self.fs + int(s[3:], 16)
        assert s[0] == '[' and s[-1] == ']', s
        s = s[1:-1]
        tot = 0
        for tok in re.findall(r'[+-]?[^+-]+', s):
            sign = -1 if tok.startswith('-') else 1
            tok = tok.lstrip('+-')
            if '*' in tok:
                rg, sc = tok.split('*')
                tot += sign * self.getr(rg)[0] * int(sc)
            elif tok.startswith('0x'):
                tot += sign * int(tok, 16)
            elif tok in ALIAS:
                tot += sign * self.getr(tok)[0]
            elif tok == 'rip':
                raise Stop('rip relative')
            else:
                tot += sign * int(tok, 0)
        return tot & M64

    def opnd(self, s):
        s = s.strip()
        m = re.match(r'^(BYTE|WORD|DWORD|QWORD|XMMWORD|YMMWORD) PTR (.*)$', s)
        if m:
            return ('m', self.ea(m.group(2)), SIZEKW[m.group(1)])
        if s in ALIAS or re.match(r'^[xy]mm\d+$', s):
            return ('r', s, self.getr(s)[1])
        if re.match(r'^-?0x[0-9a-f]+$|^-?\d+$', s):
            return ('i', int(s, 0), None)
        raise Stop('operand ' + s)

    def get(self, o, size=None):
        if o[0] == 'r':
            return self.getr(o[1])[0]
        if o[0] == 'm':
            return self.read(o[1], (size or o[2]) // 8)
        v = o[1]
        b = size or 64
        return v & ((1 << b) - 1)

    def put(self, o, v):
        if o[0] == 'r':
            self.setr(o[1], v)
        elif o[0] == 'm':
            self.write(o[1], o[2] // 8, v & ((1 << o[2]) - 1))
        else:
            raise Stop('store to imm')

    def szf(self, v, b):
        v &= (1 << b) - 1
        self.zf = int(v == 0)
        self.sf = (v >> (b - 1)) & 1

    def split_ops(self, s):
        out, depth, cur = [], 0, ''
        for ch in s:
            if ch == '[':
                depth += 1
            if ch == ']':
                depth -= 1
            if ch == ',' and depth == 0:
                out.append(cur); cur = ''
            else:
                cur += ch
        if cur.strip():
            out.append(cur)
        return [x.strip() for x in out]

    def cond(self, cc):
        c = {'e': self.zf, 'z': self.zf, 'ne': 1 - self.zf, 'nz': 1 - self.zf,
             'b': self.cf, 'c': self.cf, 'nae': self.cf, 'ae': 1 - self.cf, 'nb': 1 - self.cf, 'nc': 1 - self.cf,
             'a': int(not self.cf and not self.zf), 'be': int(self.cf or self.zf),
             's': self.sf, 'ns': 1 - self.sf, 'o': self.of, 'no': 1 - self.of,
             'l': int(self.sf != self.of), 'ge': int(self.sf == self.of),
             'g': int(not self.zf and self.sf == self.of), 'le': int(self.zf or self.sf != self.of)}
        if cc not in c:
            raise Stop('cc ' + cc)
        return c[cc]

    def call(self, entry, args, ret_addr=0xdead0000, maxsteps=10_000_000):
        regs = ['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9']
        for k, v in zip(regs, args):
            self.r[k] = v & M64
        self.r['rsp'] = 0x7ffff0000000
        self.r['rsp'] -= 8
        self.write(self.r['rsp'], 8, ret_addr)
        pc = entry
        while pc != ret_addr:
            self.steps += 1
            if self.steps > maxsteps:
                raise Stop('step limit')
            pc = self.step(pc)
        return self.r['rax']

    def step(self, pc):
        VISITED.add(pc)
        if pc not in self.p.ins:
            raise Stop('pc %x not in program' % pc)
        body = self.p.ins[pc]
        nxt = self.p.nxt[pc]
        parts = body.split(None, 1)
        mn = parts[0]
        while mn in ('cs', 'data16', 'ds', 'notrack', 'bnd', 'rex.W') and len(parts) > 1:
            parts = parts[1].split(None, 1); mn = parts[0]
        ops = self.split_ops(parts[1]) if len(parts) > 1 else []
        self.count[mn] = self.count.get(mn, 0) + 1
        f = getattr(self, 'i_' + mn, None)
        if f is None:
            if mn.startswith('j') and mn != 'jmp':
                if self.cond(mn[1:]):
                    return int(ops[0], 16)
                return nxt
            if mn.startswith('set'):
                o = self.opnd(ops[0]); self.put(o, self.cond(mn[3:])); return nxt
            if mn.startswith('cmov'):
                d = self.opnd(ops[0]); s = self.opnd(ops[1])
                if self.cond(mn[4:]):
                    self.put(d, self.get(s, d[2]))
                elif d[2] == 32:
                    self.put(d, self.get(d))
                return nxt
            raise Stop('mnemonic %s at %x: %s' % (mn, pc, body))
        r = f(ops, pc, nxt)
        return nxt if r is None else r

    # control
    def i_endbr64(self, o, pc, n): pass
    def i_nop(self, o, pc, n): pass
    def i_vzeroupper(self, o, pc, n):
        for i in range(16):
            self.y[i] &= (1 << 128) - 1
    def i_jmp(self, o, pc, n): return int(o[0], 16)
    def i_ret(self, o, pc, n):
        a = self.read(self.r['rsp'], 8); self.r['rsp'] += 8; return a
    def i_call(self, o, pc, n):
        t = int(o[0], 16)
        if t in self.externs:
            self.externs[t](self)
            return n
        self.r['rsp'] -= 8; self.write(self.r['rsp'], 8, n); return t
    def i_push(self, o, pc, n):
        v = self.get(self.opnd(o[0])); self.r['rsp'] -= 8; self.write(self.r['rsp'], 8, v)
    def i_pop(self, o, pc, n):
        v = self.read(self.r['rsp'], 8); self.r['rsp'] += 8; self.put(self.opnd(o[0]), v)
    def i_leave(self, o, pc, n):
        self.r['rsp'] = self.r['rbp']; self.r['rbp'] = self.read(self.r['rsp'], 8); self.r['rsp'] += 8

    # data movement
    def i_mov(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1])
        b = d[2]
        v = self.get(s, b)
        if s[0] == 'i' and b == 64:
            v = s[1] & M64  # sign extended imm32 or plain
        self.put(d, v)
    i_movabs = i_mov
    def i_movzx(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1]); self.put(d, self.get(s))
    def i_movsxd(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1]); v = self.get(s)
        if v >> 31: v -= 1 << 32
        self.put(d, v & M64)
    def i_lea(self, o, pc, n):
        d = self.opnd(o[0]); a = self.ea(o[1]); self.put(d, a)

    # arithmetic helpers
    def _add(self, d, s, carry):
        b = d[2]; mask = (1 << b) - 1
        x = self.get(d); y = self.get(s, b) & mask
        t = x + y + carry
        r = t & mask
        self.cf = int(t > mask)
        sx, sy, sr = x >> (b - 1), y >> (b - 1), r >> (b - 1)
        self.of = int(sx == sy and sr != sx)
        self.szf(r, b); self.put(d, r)
    def _sub(self, d, s, borrow, store=True):
        b = d[2]; mask = (1 << b) - 1
        x = self.get(d); y = self.get(s, b) & mask
        t = x - y - borrow
        r = t & mask
        self.cf = int(t < 0)
        sx, sy, sr = x >> (b - 1), y >> (b - 1), r >> (b - 1)
        self.of = int(sx != sy and sr != sx)
        self.szf(r, b)
        if store: self.put(d, r)
    def i_add(self, o, pc, n): self._add(self.opnd(o[0]), self.opnd(o[1]), 0)
    def i_adc(self, o, pc, n): self._add(self.opnd(o[0]), self.opnd(o[1]), self.cf)
    def i_sub(self, o, pc, n): self._sub(self.opnd(o[0]), self.opnd(o[1]), 0)
    def i_sbb(self, o, pc, n): self._sub(self.opnd(o[0]), self.opnd(o[1]), self.cf)
    def i_cmp(self, o, pc, n): self._sub(self.opnd(o[0]), self.opnd(o[1]), 0, store=False)
    def i_neg(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]; x = self.get(d)
        r = (-x) & ((1 << b) - 1)
        self.cf = int(x != 0); self.of = int(x == 1 << (b - 1)); self.szf(r, b); self.put(d, r)
    def i_inc(self, o, pc, n):
        cf = self.cf; self._add(self.opnd(o[0]), ('i', 1, None), 0); self.cf = cf
    def i_dec(self, o, pc, n):
        cf = self.cf; self._sub(self.opnd(o[0]), ('i', 1, None), 0); self.cf = cf
    def _logic(self, o, fn, store=True):
        d = self.opnd(o[0]); s = self.opnd(o[1]); b = d[2]
        r = fn(self.get(d), self.get(s, b)) & ((1 << b) - 1)
        self.cf = self.of = 0; self.szf(r, b)
        if store: self.put(d, r)
    def i_and(self, o, pc, n): self._logic(o, lambda a, b: a & b)
    def i_or(self, o, pc, n): self._logic(o, lambda a, b: a | b)
    def i_xor(self, o, pc, n): self._logic(o, lambda a, b: a ^ b)
    def i_test(self, o, pc, n): self._logic(o, lambda a, b: a & b, store=False)
    def i_not(self, o, pc, n):
        d = self.opnd(o[0]); self.put(d, ~self.get(d) & ((1 << d[2]) - 1))
    def i_imul(self, o, pc, n):
        if len(o) == 1:
            raise Stop('imul one operand')
        d = self.opnd(o[0]); b = d[2]
        if len(o) == 2:
            x = self.get(d); y = self.get(self.opnd(o[1]), b)
        else:
            x = self.get(self.opnd(o[1]), b); y = self.get(self.opnd(o[2]), b)
        def sg(v):
            return v - (1 << b) if v >> (b - 1) else v
        t = sg(x) * sg(y)
        r = t & ((1 << b) - 1)
        self.cf = self.of = int(sg(r) != t)
        self.put(d, r)
    def i_mul(self, o, pc, n):
        s = self.opnd(o[0]); assert s[2] == 64
        t = self.r['rax'] * self.get(s)
        self.r['rax'] = t & M64; self.r['rdx'] = t >> 64
        self.cf = self.of = int(self.r['rdx'] != 0)
    def i_mulx(self, o, pc, n):
        hi = self.opnd(o[0]); lo = self.opnd(o[1]); s = self.opnd(o[2])
        t = self.r['rdx'] * self.get(s)
        # Intel: when hi and lo name the same register the high half is written
        self.put(lo, t & M64); self.put(hi, t >> 64)
    def i_div(self, o, pc, n):
        s = self.opnd(o[0]); assert s[2] == 64
        dv = self.get(s)
        if dv == 0:
            raise Stop('#DE divide by zero')
        num = (self.r['rdx'] << 64) | self.r['rax']
        q = num // dv
        if q > M64:
            raise Stop('#DE quotient overflow')
        self.r['rax'] = q; self.r['rdx'] = num % dv
    def _shcount(self, s, b):
        c = self.get(s, 8)
        return c & (63 if b == 64 else 31)
    def i_shl(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]
        c = self._shcount(self.opnd(o[1]) if len(o) > 1 else ('i', 1, None), b)
        if c == 0: return
        x = self.get(d); t = x << c
        r = t & ((1 << b) - 1)
        self.cf = (x >> (b - c)) & 1; self.szf(r, b); self.of = ((r >> (b - 1)) & 1) ^ self.cf
        self.put(d, r)
    def i_shr(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]
        c = self._shcount(self.opnd(o[1]) if len(o) > 1 else ('i', 1, None), b)
        if c == 0: return
        x = self.get(d); r = x >> c
        self.cf = (x >> (c - 1)) & 1; self.szf(r, b); self.of = (x >> (b - 1)) & 1
        self.put(d, r)
    def i_sar(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]
        c = self._shcount(self.opnd(o[1]) if len(o) > 1 else ('i', 1, None), b)
        if c == 0: return
        x = self.get(d); sx = x - (1 << b) if x >> (b - 1) else x
        r = (sx >> c) & ((1 << b) - 1)
        self.cf = (sx >> (c - 1)) & 1; self.szf(r, b); self.of = 0
        self.put(d, r)
    def i_shld(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1]); b = d[2]
        c = self._shcount(self.opnd(o[2]), b)
        if c == 0: return
        x = self.get(d); y = self.get(s)
        t = ((x << b) | y) << c
        r = (t >> b) & ((1 << b) - 1)
        self.cf = (x >> (b - c)) & 1; self.szf(r, b); self.of = ((r ^ x) >> (b - 1)) & 1
        self.put(d, r)
    def i_shrd(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1]); b = d[2]
        c = self._shcount(self.opnd(o[2]), b)
        if c == 0: return
        x = self.get(d); y = self.get(s)
        t = ((y << b) | x) >> c
        r = t & ((1 << b) - 1)
        self.cf = (x >> (c - 1)) & 1; self.szf(r, b); self.of = ((r ^ x) >> (b - 1)) & 1
        self.put(d, r)
    def i_shlx(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]
        x = self.get(self.opnd(o[1]), b); c = self.get(self.opnd(o[2])) & (b - 1)
        self.put(d, (x << c) & ((1 << b) - 1))
    def i_shrx(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]
        x = self.get(self.opnd(o[1]), b); c = self.get(self.opnd(o[2])) & (b - 1)
        self.put(d, x >> c)
    def i_sarx(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]
        x = self.get(self.opnd(o[1]), b); c = self.get(self.opnd(o[2])) & (b - 1)
        sx = x - (1 << b) if x >> (b - 1) else x
        self.put(d, (sx >> c) & ((1 << b) - 1))
    def i_lzcnt(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]; x = self.get(self.opnd(o[1]), b)
        c = b - x.bit_length()
        self.cf = int(x == 0); self.zf = int(c == 0); self.put(d, c)
    def i_tzcnt(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]; x = self.get(self.opnd(o[1]), b)
        c = b if x == 0 else (x & -x).bit_length() - 1
        self.cf = int(x == 0); self.zf = int(c == 0); self.put(d, c)

    # vector
    def i_vmovdqu(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1]); self.put(d, self.get(s))
    i_vmovdqa = i_vmovdqu
    i_vmovups = i_vmovdqu
    i_vmovaps = i_vmovdqu
    def i_vmovq(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1])
        v = self.get(s) & M64
        self.put(d, v)
    def i_vpxor(self, o, pc, n):
        d = self.opnd(o[0]); self.put(d, self.get(self.opnd(o[1])) ^ self.get(self.opnd(o[2])))
    def i_vpinsrq(self, o, pc, n):
        d = self.opnd(o[0]); s1 = self.get(self.opnd(o[1])) & ((1 << 128) - 1)
        v = self.get(self.opnd(o[2]), 64); k = int(o[3], 0) & 1
        s1 &= ~(M64 << (64 * k)) & ((1 << 128) - 1)
        self.put(d, s1 | (v << (64 * k)))
    def i_vpextrq(self, o, pc, n):
        d = self.opnd(o[0]); s = self.get(self.opnd(o[1])); k = int(o[2], 0) & 1
        self.put(d, (s >> (64 * k)) & M64)
    def i_vinserti128(self, o, pc, n):
        d = self.opnd(o[0]); s1 = self.get(self.opnd(o[1])); s2 = self.get(self.opnd(o[2]), 128) & ((1 << 128) - 1)
        k = int(o[3], 0) & 1
        lo = s1 & ((1 << 128) - 1); hi = (s1 >> 128) & ((1 << 128) - 1)
        if k: hi = s2
        else: lo = s2
        self.put(d, lo | (hi << 128))
    def i_vextracti128(self, o, pc, n):
        d = self.opnd(o[0]); s = self.get(self.opnd(o[1])); k = int(o[2], 0) & 1
        self.put(d, (s >> (128 * k)) & ((1 << 128) - 1))
    def i_vpor(self, o, pc, n):
        d = self.opnd(o[0]); self.put(d, self.get(self.opnd(o[1])) | self.get(self.opnd(o[2])))
    def i_vpand(self, o, pc, n):
        d = self.opnd(o[0]); self.put(d, self.get(self.opnd(o[1])) & self.get(self.opnd(o[2])))
    def i_vptest(self, o, pc, n):
        a = self.get(self.opnd(o[0])); b = self.get(self.opnd(o[1]))
        self.zf = int(a & b == 0); self.cf = int(~a & b == 0); self.sf = self.of = 0
