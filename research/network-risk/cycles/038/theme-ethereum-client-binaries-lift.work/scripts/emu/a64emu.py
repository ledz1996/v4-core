"""Small AArch64 interpreter over llvm-objdump text, written for this review.

It reads the disassembly text of a few routines of the shipped Tempo aarch64
release binary and interprets it in Python. No machine code from the release is
run on any CPU, and the binary is never loaded: constants it references are read
as plain bytes from the file with Python. Unknown instructions or operand forms
raise Stop, so a gap shows up as an error and never as a silent wrong result.

Only the integer and NEON instructions that the lifted routines use are modelled.
"""
import re

M64 = (1 << 64) - 1
M32 = (1 << 32) - 1
M128 = (1 << 128) - 1


class Stop(Exception):
    pass


class Prog:
    """Instructions keyed by address, from llvm-objdump --no-show-raw-insn text."""

    def __init__(self, texts):
        self.ins = {}
        for text in texts:
            for line in text.splitlines():
                m = re.match(r'^\s*([0-9a-f]+):\s+(\S+)\s*(.*)$', line)
                if not m:
                    continue
                a = int(m.group(1), 16)
                mn = m.group(2)
                rest = re.sub(r'\s*<[^>]*>', '', m.group(3))
                rest = rest.split('//')[0].strip()
                self.ins[a] = (mn, rest)
        self.dec = {}

    def decoded(self, a):
        d = self.dec.get(a)
        if d is None:
            if a not in self.ins:
                raise Stop('pc %x not in program' % a)
            mn, rest = self.ins[a]
            d = (mn, split_ops(rest))
            self.dec[a] = d
        return d


def split_ops(s):
    out, depth, cur = [], 0, ''
    for ch in s:
        if ch in '[{':
            depth += 1
        if ch in ']}':
            depth -= 1
        if ch == ',' and depth == 0:
            out.append(cur.strip()); cur = ''
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def imm(s):
    s = s.strip()
    if s.startswith('#'):
        s = s[1:]
    return int(s, 0)


class Mem:
    """Flat little-endian memory: writable regions as bytearrays, plus read-only file bytes."""

    def __init__(self, filebytes=None, file_lo=0, file_hi=0):
        self.regions = []  # (lo, hi, bytearray)
        self.fb = filebytes
        self.flo = file_lo
        self.fhi = file_hi
        self.reads = 0

    def add(self, lo, size):
        b = bytearray(size)
        self.regions.append((lo, lo + size, b))
        return b

    def _find(self, a, n):
        for lo, hi, b in self.regions:
            if lo <= a and a + n <= hi:
                return b, a - lo
        return None, None

    def read(self, a, n):
        b, o = self._find(a, n)
        if b is not None:
            return int.from_bytes(b[o:o + n], 'little')
        if self.fb is not None and self.flo <= a and a + n <= self.fhi:
            return int.from_bytes(self.fb[a:a + n], 'little')
        raise Stop('read %d at %x outside memory' % (n, a))

    def write(self, a, n, v):
        b, o = self._find(a, n)
        if b is None:
            raise Stop('write %d at %x outside memory' % (n, a))
        b[o:o + n] = (v & ((1 << (8 * n)) - 1)).to_bytes(n, 'little')


COND = {
    'eq': lambda n, z, c, v: z, 'ne': lambda n, z, c, v: not z,
    'hs': lambda n, z, c, v: c, 'cs': lambda n, z, c, v: c,
    'lo': lambda n, z, c, v: not c, 'cc': lambda n, z, c, v: not c,
    'mi': lambda n, z, c, v: n, 'pl': lambda n, z, c, v: not n,
    'vs': lambda n, z, c, v: v, 'vc': lambda n, z, c, v: not v,
    'hi': lambda n, z, c, v: c and not z, 'ls': lambda n, z, c, v: (not c) or z,
    'ge': lambda n, z, c, v: n == v, 'lt': lambda n, z, c, v: n != v,
    'gt': lambda n, z, c, v: (not z) and n == v, 'le': lambda n, z, c, v: z or n != v,
    'al': lambda n, z, c, v: True,
}

VLANE = {'16b': (8, 16), '8b': (8, 8), '8h': (16, 8), '4h': (16, 4), '4s': (32, 4),
         '2s': (32, 2), '2d': (64, 2), '1d': (64, 1)}
SCAL = {'b': 8, 'h': 16, 's': 32, 'd': 64, 'q': 128}


def lanes(v, w, n):
    m = (1 << w) - 1
    return [(v >> (w * i)) & m for i in range(n)]


def pack(ls, w):
    v = 0
    m = (1 << w) - 1
    for i, x in enumerate(ls):
        v |= (x & m) << (w * i)
    return v


def sx(v, w):
    return v - (1 << w) if v >> (w - 1) & 1 else v


class CPU:
    def __init__(self, prog, mem, externs=None, faults=None):
        self.p = prog
        self.m = mem
        self.x = [0] * 32  # x31 is sp
        self.v = [0] * 32
        self.n = self.z = self.c = self.vf = False
        self.externs = externs or {}
        self.faults = faults or {}   # addr -> callable(cpu, mn, ops) -> (mn, ops)
        self.steps = 0
        self.visited = set()
        self.count = {}

    # ---- general registers
    def rr(self, s):
        if s in ('xzr', 'wzr'):
            return 0
        if s == 'sp':
            return self.x[31]
        if s == 'wsp':
            return self.x[31] & M32
        if s[0] == 'x':
            return self.x[int(s[1:])]
        if s[0] == 'w':
            return self.x[int(s[1:])] & M32
        raise Stop('reg ' + s)

    def wr(self, s, val):
        if s in ('xzr', 'wzr'):
            return
        if s == 'sp':
            self.x[31] = val & M64; return
        if s[0] == 'x':
            self.x[int(s[1:])] = val & M64; return
        if s[0] == 'w':
            self.x[int(s[1:])] = val & M32; return
        raise Stop('reg ' + s)

    @staticmethod
    def width(s):
        if s in ('sp', 'xzr') or s[0] == 'x':
            return 64
        if s in ('wsp', 'wzr') or s[0] == 'w':
            return 32
        raise Stop('width ' + s)

    # ---- vector registers
    def vreg(self, s):
        s = s.strip().strip('{} ')
        m = re.match(r'^v(\d+)\.(\w+)$', s)
        if m:
            return int(m.group(1)), m.group(2)
        m = re.match(r'^([bhsdq])(\d+)$', s)
        if m:
            return int(m.group(2)), m.group(1)
        raise Stop('vreg ' + s)

    def vget(self, s):
        i, k = self.vreg(s)
        if k in SCAL:
            return self.v[i] & ((1 << SCAL[k]) - 1)
        w, n = VLANE[k]
        return self.v[i] & ((1 << (w * n)) - 1)

    def vset(self, s, val):
        i, k = self.vreg(s)
        if k in SCAL:
            self.v[i] = val & ((1 << SCAL[k]) - 1)
        else:
            w, n = VLANE[k]
            self.v[i] = val & ((1 << (w * n)) - 1)

    # ---- operand helpers
    def shifted(self, ops, base_w):
        """Value of ops[0] with an optional shift or extend in ops[1]."""
        v = self.rr(ops[0])
        if len(ops) == 1:
            return v
        sh = ops[1].split()
        kind = sh[0]
        amt = imm(sh[1]) if len(sh) > 1 else 0
        if kind == 'lsl':
            return (v << amt) & ((1 << base_w) - 1)
        if kind == 'lsr':
            return v >> amt
        if kind == 'asr':
            return (sx(v, self.width(ops[0])) >> amt) & ((1 << base_w) - 1)
        if kind == 'ror':
            w = self.width(ops[0])
            return ((v >> amt) | (v << (w - amt))) & ((1 << w) - 1)
        ext = {'uxtb': (8, False), 'uxth': (16, False), 'uxtw': (32, False), 'uxtx': (64, False),
               'sxtb': (8, True), 'sxth': (16, True), 'sxtw': (32, True), 'sxtx': (64, True)}
        if kind in ext:
            w, s = ext[kind]
            v &= (1 << w) - 1
            if s:
                v = sx(v, w)
            return (v << amt) & ((1 << base_w) - 1)
        raise Stop('shift ' + ops[1])

    def operand2(self, ops, w):
        if ops[0].startswith('#'):
            v = imm(ops[0])
            if len(ops) > 1:
                sh = ops[1].split()
                assert sh[0] == 'lsl'
                v <<= imm(sh[1])
            return v & ((1 << w) - 1)
        return self.shifted(ops, w)

    def addr(self, ops):
        """Returns (address, writeback register or None, new value)."""
        a = ops[0]
        assert a.startswith('['), ops
        pre = a.endswith('!')
        inner = a.strip('!')[1:-1]
        parts = [p.strip() for p in inner.split(',')]
        base = self.rr(parts[0])
        off = 0
        if len(parts) >= 2:
            if parts[1].startswith('#'):
                off = imm(parts[1])
            else:
                off = self.shifted(parts[1:], 64)
        if len(ops) > 1:  # post-index
            return base, parts[0], (base + imm(ops[1])) & M64
        ea = (base + off) & M64
        if pre:
            return ea, parts[0], ea
        return ea, None, None

    def flags_add(self, x, y, carry, w):
        mask = (1 << w) - 1
        t = x + y + carry
        r = t & mask
        self.n = bool(r >> (w - 1))
        self.z = r == 0
        self.c = t > mask
        sxv, syv, srv = x >> (w - 1), y >> (w - 1), r >> (w - 1)
        self.vf = sxv == syv and srv != sxv
        return r

    # ---- run
    def call(self, entry, args, ret=0xdead0000, maxsteps=5_000_000):
        for i, a in enumerate(args):
            self.x[i] = a & M64
        self.x[30] = ret
        pc = entry
        while pc != ret:
            self.steps += 1
            if self.steps > maxsteps:
                raise Stop('step limit')
            pc = self.step(pc)
        return self.x[0]

    def step(self, pc):
        self.visited.add(pc)
        mn, ops = self.p.decoded(pc)
        if pc in self.faults:
            mn, ops = self.faults[pc](self, mn, ops)
        nxt = pc + 4
        f = getattr(self, 'i_' + mn.replace('.', '_'), None)
        if f is None:
            if mn.startswith('b.'):
                cc = mn[2:]
                return int(ops[0], 16) if COND[cc](self.n, self.z, self.c, self.vf) else nxt
            raise Stop('mnemonic %s at %x: %s' % (mn, pc, ops))
        try:
            r = f(ops)
        except Stop as e:
            raise Stop('%s [at %x: %s %s]' % (e, pc, mn, ','.join(ops)))
        return nxt if r is None else r

    # control
    def i_b(self, o):
        t = int(o[0], 16)
        if t in self.externs:
            self.externs[t](self)
            return self.x[30]
        return t
    def i_bl(self, o):
        t = int(o[0], 16)
        if t in self.externs:
            self.externs[t](self)
            return None
        self.x[30] = self._pc_next
        return t
    def i_ret(self, o): return self.x[30]
    def i_cbz(self, o): return int(o[1], 16) if self.rr(o[0]) == 0 else None
    def i_cbnz(self, o): return int(o[1], 16) if self.rr(o[0]) != 0 else None
    def i_tbz(self, o): return int(o[2], 16) if not (self.rr(o[0]) >> imm(o[1])) & 1 else None
    def i_tbnz(self, o): return int(o[2], 16) if (self.rr(o[0]) >> imm(o[1])) & 1 else None
    def i_nop(self, o): pass

    # moves
    def i_mov(self, o):
        if re.match(r'^v\d+\.\w\[\d+\]$', o[1]):
            if o[0].startswith('v'):
                raise Stop('mov element to vector')
            e, ew = self._elem(o[1]); self.wr(o[0], e); return
        if re.match(r'^v\d+\.\w\[\d+\]$', o[0]):
            m = re.match(r'^v(\d+)\.(\w)\[(\d+)\]$', o[0]); i = int(m.group(1)); ew = SCAL[m.group(2)]; k = int(m.group(3))
            val = self.rr(o[1]) & ((1 << ew) - 1)
            self.v[i] = (self.v[i] & ~(((1 << ew) - 1) << (ew * k))) | (val << (ew * k)); return
        if o[0].startswith('v'):
            self.vset(o[0], self.vget(o[1])); return
        w = self.width(o[0])
        if o[1].startswith('#'):
            self.wr(o[0], imm(o[1]) & ((1 << w) - 1))
        else:
            self.wr(o[0], self.rr(o[1]))
    def i_movz(self, o):
        w = self.width(o[0]); self.wr(o[0], self.operand2(o[1:], w))
    def i_movn(self, o):
        w = self.width(o[0]); self.wr(o[0], ~self.operand2(o[1:], w) & ((1 << w) - 1))
    def i_movk(self, o):
        w = self.width(o[0]); sh = imm(o[2].split()[1]) if len(o) > 2 else 0
        old = self.rr(o[0]); val = imm(o[1])
        self.wr(o[0], (old & ~(0xffff << sh)) | (val << sh))
    def i_adrp(self, o): self.wr(o[0], imm(o[1]) if not o[1].startswith('0x') else int(o[1], 16))
    def i_adr(self, o): self.wr(o[0], int(o[1], 16))

    # arithmetic
    def _addsub(self, o, sub, setf, carry_in=None):
        w = self.width(o[0])
        mask = (1 << w) - 1
        x = self.rr(o[1]) & mask
        y = self.operand2(o[2:], w) & mask
        if sub:
            y = ~y & mask
            cin = 1 if carry_in is None else carry_in
        else:
            cin = 0 if carry_in is None else carry_in
        if setf:
            r = self.flags_add(x, y, cin, w)
        else:
            r = (x + y + cin) & mask
        self.wr(o[0], r)
    def i_add(self, o):
        if o[0].startswith('v'):
            w, n = VLANE[self.vreg(o[0])[1]]
            a = lanes(self.vget(o[1]), w, n); b = lanes(self.vget(o[2]), w, n)
            self.vset(o[0], pack([x + y for x, y in zip(a, b)], w)); return
        self._addsub(o, False, False)
    def i_adds(self, o): self._addsub(o, False, True)
    def i_sub(self, o):
        if o[0].startswith('v'):
            w, n = VLANE[self.vreg(o[0])[1]]
            a = lanes(self.vget(o[1]), w, n); b = lanes(self.vget(o[2]), w, n)
            self.vset(o[0], pack([x - y for x, y in zip(a, b)], w)); return
        self._addsub(o, True, False)
    def i_subs(self, o): self._addsub(o, True, True)
    def i_adc(self, o): self._addsub(o, False, False, int(self.c))
    def i_adcs(self, o): self._addsub(o, False, True, int(self.c))
    def i_sbc(self, o): self._addsub(o, True, False, int(self.c))
    def i_sbcs(self, o): self._addsub(o, True, True, int(self.c))
    def i_cmp(self, o): self._addsub(['xzr' if self.width(o[0]) == 64 else 'wzr'] + o, True, True)
    def i_cmn(self, o): self._addsub(['xzr' if self.width(o[0]) == 64 else 'wzr'] + o, False, True)
    def i_neg(self, o):
        if o[0].startswith('v'):
            w, n = VLANE[self.vreg(o[0])[1]]
            self.vset(o[0], pack([-x for x in lanes(self.vget(o[1]), w, n)], w)); return
        z = 'xzr' if self.width(o[0]) == 64 else 'wzr'
        self._addsub([o[0], z] + o[1:], True, False)
    def i_negs(self, o):
        z = 'xzr' if self.width(o[0]) == 64 else 'wzr'
        self._addsub([o[0], z] + o[1:], True, True)
    def i_ngc(self, o):
        z = 'xzr' if self.width(o[0]) == 64 else 'wzr'
        self._addsub([o[0], z] + o[1:], True, False, int(self.c))
    def i_ngcs(self, o):
        z = 'xzr' if self.width(o[0]) == 64 else 'wzr'
        self._addsub([o[0], z] + o[1:], True, True, int(self.c))
    def i_mul(self, o):
        w = self.width(o[0]); self.wr(o[0], (self.rr(o[1]) * self.rr(o[2])) & ((1 << w) - 1))
    def i_madd(self, o):
        w = self.width(o[0]); self.wr(o[0], (self.rr(o[1]) * self.rr(o[2]) + self.rr(o[3])) & ((1 << w) - 1))
    def i_msub(self, o):
        w = self.width(o[0]); self.wr(o[0], (self.rr(o[3]) - self.rr(o[1]) * self.rr(o[2])) & ((1 << w) - 1))
    def i_mneg(self, o):
        w = self.width(o[0]); self.wr(o[0], (-self.rr(o[1]) * self.rr(o[2])) & ((1 << w) - 1))
    def i_umulh(self, o): self.wr(o[0], (self.rr(o[1]) * self.rr(o[2])) >> 64)
    def i_smulh(self, o): self.wr(o[0], ((sx(self.rr(o[1]), 64) * sx(self.rr(o[2]), 64)) >> 64) & M64)
    def i_umull(self, o):
        if o[0].startswith('v'):
            raise Stop('vector umull')
        self.wr(o[0], self.rr(o[1]) * self.rr(o[2]))
    def i_umaddl(self, o): self.wr(o[0], (self.rr(o[1]) * self.rr(o[2]) + self.rr(o[3])) & M64)
    def i_udiv(self, o):
        d = self.rr(o[2]); self.wr(o[0], 0 if d == 0 else self.rr(o[1]) // d)
    def i_sdiv(self, o):
        w = self.width(o[0]); a = sx(self.rr(o[1]), w); b = sx(self.rr(o[2]), w)
        if b == 0:
            self.wr(o[0], 0); return
        q = abs(a) // abs(b)
        if (a < 0) != (b < 0): q = -q
        self.wr(o[0], q & ((1 << w) - 1))

    # logic
    def _logic(self, o, fn, setf=False, inv=False):
        if o[0].startswith('v'):
            a = self.vget(o[1]); b = self.vget(o[2])
            w, n = VLANE[self.vreg(o[0])[1]]
            m = (1 << (w * n)) - 1
            if inv: b = ~b & m
            self.vset(o[0], fn(a, b) & m); return
        w = self.width(o[0]); mask = (1 << w) - 1
        x = self.rr(o[1]); y = self.operand2(o[2:], w)
        if inv: y = ~y & mask
        r = fn(x, y) & mask
        if setf:
            self.n = bool(r >> (w - 1)); self.z = r == 0; self.c = False; self.vf = False
        self.wr(o[0], r)
    def i_and(self, o): self._logic(o, lambda a, b: a & b)
    def i_ands(self, o): self._logic(o, lambda a, b: a & b, True)
    def i_orr(self, o): self._logic(o, lambda a, b: a | b)
    def i_eor(self, o): self._logic(o, lambda a, b: a ^ b)
    def i_bic(self, o): self._logic(o, lambda a, b: a & b, inv=True)
    def i_bics(self, o): self._logic(o, lambda a, b: a & b, True, inv=True)
    def i_orn(self, o): self._logic(o, lambda a, b: a | b, inv=True)
    def i_eon(self, o): self._logic(o, lambda a, b: a ^ b, inv=True)
    def i_tst(self, o): self._logic(['xzr' if self.width(o[0]) == 64 else 'wzr'] + o, lambda a, b: a & b, True)
    def i_mvn(self, o):
        if o[0].startswith('v'):
            w, n = VLANE[self.vreg(o[0])[1]]
            self.vset(o[0], ~self.vget(o[1]) & ((1 << (w * n)) - 1)); return
        w = self.width(o[0]); self.wr(o[0], ~self.operand2(o[1:], w) & ((1 << w) - 1))

    # shifts and bit fields
    def i_lsl(self, o):
        w = self.width(o[0]); s = imm(o[2]) if o[2].startswith('#') else self.rr(o[2]) % w
        self.wr(o[0], (self.rr(o[1]) << s) & ((1 << w) - 1))
    def i_lsr(self, o):
        w = self.width(o[0]); s = imm(o[2]) if o[2].startswith('#') else self.rr(o[2]) % w
        self.wr(o[0], self.rr(o[1]) >> s)
    def i_asr(self, o):
        w = self.width(o[0]); s = imm(o[2]) if o[2].startswith('#') else self.rr(o[2]) % w
        self.wr(o[0], (sx(self.rr(o[1]), w) >> s) & ((1 << w) - 1))
    def i_ror(self, o):
        w = self.width(o[0]); s = imm(o[2]) if o[2].startswith('#') else self.rr(o[2]) % w
        v = self.rr(o[1]); self.wr(o[0], ((v >> s) | (v << (w - s))) & ((1 << w) - 1))
    def i_extr(self, o):
        w = self.width(o[0]); s = imm(o[3])
        v = (self.rr(o[1]) << w) | self.rr(o[2]); self.wr(o[0], (v >> s) & ((1 << w) - 1))
    def i_ubfx(self, o):
        lsb, wd = imm(o[2]), imm(o[3]); self.wr(o[0], (self.rr(o[1]) >> lsb) & ((1 << wd) - 1))
    def i_sbfx(self, o):
        w = self.width(o[0]); lsb, wd = imm(o[2]), imm(o[3])
        self.wr(o[0], sx((self.rr(o[1]) >> lsb) & ((1 << wd) - 1), wd) & ((1 << w) - 1))
    def i_ubfiz(self, o):
        w = self.width(o[0]); lsb, wd = imm(o[2]), imm(o[3])
        self.wr(o[0], ((self.rr(o[1]) & ((1 << wd) - 1)) << lsb) & ((1 << w) - 1))
    def i_sbfiz(self, o):
        w = self.width(o[0]); lsb, wd = imm(o[2]), imm(o[3])
        self.wr(o[0], (sx(self.rr(o[1]) & ((1 << wd) - 1), wd) << lsb) & ((1 << w) - 1))
    def i_bfi(self, o):
        w = self.width(o[0]); lsb, wd = imm(o[2]), imm(o[3]); m = ((1 << wd) - 1) << lsb
        self.wr(o[0], (self.rr(o[0]) & ~m) | ((self.rr(o[1]) << lsb) & m))
    def i_bfxil(self, o):
        lsb, wd = imm(o[2]), imm(o[3]); m = (1 << wd) - 1
        self.wr(o[0], (self.rr(o[0]) & ~m) | ((self.rr(o[1]) >> lsb) & m))
    def i_sxtb(self, o): self.wr(o[0], sx(self.rr(o[1]) & 0xff, 8) & ((1 << self.width(o[0])) - 1))
    def i_sxth(self, o): self.wr(o[0], sx(self.rr(o[1]) & 0xffff, 16) & ((1 << self.width(o[0])) - 1))
    def i_sxtw(self, o): self.wr(o[0], sx(self.rr(o[1]) & M32, 32) & M64)
    def i_uxtb(self, o): self.wr(o[0], self.rr(o[1]) & 0xff)
    def i_uxth(self, o): self.wr(o[0], self.rr(o[1]) & 0xffff)
    def i_clz(self, o):
        w = self.width(o[0]); self.wr(o[0], w - self.rr(o[1]).bit_length())
    def i_rbit(self, o):
        w = self.width(o[0]); v = self.rr(o[1])
        self.wr(o[0], int(format(v, '0%db' % w)[::-1], 2))

    # conditional
    def cc(self, s): return COND[s](self.n, self.z, self.c, self.vf)
    def i_csel(self, o): self.wr(o[0], self.rr(o[1]) if self.cc(o[3]) else self.rr(o[2]))
    def i_csinc(self, o):
        w = self.width(o[0]); self.wr(o[0], self.rr(o[1]) if self.cc(o[3]) else (self.rr(o[2]) + 1) & ((1 << w) - 1))
    def i_csinv(self, o):
        w = self.width(o[0]); self.wr(o[0], self.rr(o[1]) if self.cc(o[3]) else ~self.rr(o[2]) & ((1 << w) - 1))
    def i_csneg(self, o):
        w = self.width(o[0]); self.wr(o[0], self.rr(o[1]) if self.cc(o[3]) else (-self.rr(o[2])) & ((1 << w) - 1))
    def i_cset(self, o): self.wr(o[0], 1 if self.cc(o[1]) else 0)
    def i_csetm(self, o):
        w = self.width(o[0]); self.wr(o[0], ((1 << w) - 1) if self.cc(o[1]) else 0)
    def i_cinc(self, o):
        w = self.width(o[0]); v = self.rr(o[1]); self.wr(o[0], (v + 1) & ((1 << w) - 1) if self.cc(o[2]) else v)
    def i_cinv(self, o):
        w = self.width(o[0]); v = self.rr(o[1]); self.wr(o[0], ~v & ((1 << w) - 1) if self.cc(o[2]) else v)
    def i_cneg(self, o):
        w = self.width(o[0]); v = self.rr(o[1]); self.wr(o[0], (-v) & ((1 << w) - 1) if self.cc(o[2]) else v)
    def _ccmp(self, o, neg):
        if self.cc(o[3]):
            w = self.width(o[0])
            x = self.rr(o[0]) & ((1 << w) - 1)
            y = imm(o[1]) if o[1].startswith('#') else self.rr(o[1])
            y &= (1 << w) - 1
            if neg:
                self.flags_add(x, y, 0, w)
            else:
                self.flags_add(x, ~y & ((1 << w) - 1), 1, w)
        else:
            f = imm(o[2])
            self.n, self.z, self.c, self.vf = bool(f & 8), bool(f & 4), bool(f & 2), bool(f & 1)
    def i_ccmp(self, o): self._ccmp(o, False)
    def i_ccmn(self, o): self._ccmp(o, True)

    # loads and stores
    def _ld(self, o, n, signed=False, vec=False):
        a, wb, nv = self.addr(o[1:])
        v = self.m.read(a, n)
        if vec:
            self.vset(o[0], v)
        else:
            if signed:
                v = sx(v, 8 * n) & ((1 << self.width(o[0])) - 1)
            self.wr(o[0], v)
        if wb: self.wr(wb, nv)
    def _regsize(self, r):
        if r[0] in 'xw' or r in ('xzr', 'wzr', 'sp'):
            return self.width(r) // 8, False
        return SCAL[r[0]] // 8, True
    def i_ldr(self, o):
        n, vec = self._regsize(o[0]); self._ld(o, n, vec=vec)
    i_ldur = i_ldr
    i_ldar = i_ldr
    def i_ldrb(self, o): self._ld(o, 1)
    i_ldurb = i_ldrb
    def i_ldrh(self, o): self._ld(o, 2)
    i_ldurh = i_ldrh
    def i_ldrsb(self, o): self._ld(o, 1, True)
    def i_ldrsh(self, o): self._ld(o, 2, True)
    def i_ldrsw(self, o): self._ld(o, 4, True)
    def i_ldp(self, o):
        n, vec = self._regsize(o[0])
        a, wb, nv = self.addr(o[2:])
        v0 = self.m.read(a, n); v1 = self.m.read(a + n, n)
        if vec:
            self.vset(o[0], v0); self.vset(o[1], v1)
        else:
            self.wr(o[0], v0); self.wr(o[1], v1)
        if wb: self.wr(wb, nv)
    def _st(self, o, n, vec=False):
        a, wb, nv = self.addr(o[1:])
        v = self.vget(o[0]) if vec else self.rr(o[0])
        self.m.write(a, n, v)
        if wb: self.wr(wb, nv)
    def i_str(self, o):
        n, vec = self._regsize(o[0]); self._st(o, n, vec)
    i_stur = i_str
    def i_strb(self, o): self._st(o, 1)
    i_sturb = i_strb
    def i_strh(self, o): self._st(o, 2)
    i_sturh = i_strh
    def i_stp(self, o):
        n, vec = self._regsize(o[0])
        a, wb, nv = self.addr(o[2:])
        if vec:
            v0, v1 = self.vget(o[0]), self.vget(o[1])
        else:
            v0, v1 = self.rr(o[0]), self.rr(o[1])
        self.m.write(a, n, v0); self.m.write(a + n, n, v1)
        if wb: self.wr(wb, nv)

    # ---- NEON
    def _vw(self, s):
        return VLANE[self.vreg(s)[1]]
    def i_movi(self, o):
        i, k = self.vreg(o[0])
        s = o[1].lstrip('#')
        if k == '2d':
            v = int(s, 16) if not s.startswith('0x') else int(s, 16)
            # #0000000000000000 style: bytes of 0x00 or 0xff
            v = int(s, 16)
            self.vset(o[0], pack([v, v], 64)); return
        w, n = VLANE[k]
        val = int(s, 0)
        if len(o) > 2:
            sh = o[2].split(); assert sh[0] == 'lsl'; val <<= imm(sh[1])
        self.vset(o[0], pack([val] * n, w))
    def i_dup(self, o):
        w, n = self._vw(o[0])
        m = re.match(r'^v(\d+)\.(\w)\[(\d+)\]$', o[1])
        if m:
            src = self.v[int(m.group(1))]; ew = SCAL[m.group(2)]; idx = int(m.group(3))
            e = (src >> (ew * idx)) & ((1 << ew) - 1)
        else:
            e = self.rr(o[1])
        self.vset(o[0], pack([e] * n, w))
    def _elem(self, s):
        m = re.match(r'^v(\d+)\.(\w)\[(\d+)\]$', s)
        if not m: raise Stop('elem ' + s)
        ew = SCAL[m.group(2)]; idx = int(m.group(3))
        return (self.v[int(m.group(1))] >> (ew * idx)) & ((1 << ew) - 1), ew
    def i_umov(self, o):
        e, ew = self._elem(o[1]); self.wr(o[0], e)
    def i_smov(self, o):
        e, ew = self._elem(o[1]); self.wr(o[0], sx(e, ew) & ((1 << self.width(o[0])) - 1))
    def i_fmov(self, o):
        if o[0][0] in 'xw' and o[1][0] in 'dsh':
            self.wr(o[0], self.vget(o[1])); return
        if o[0][0] in 'dsh' and o[1][0] in 'xw':
            self.vset(o[0], self.rr(o[1])); return
        raise Stop('fmov ' + str(o))
    def _lanewise(self, o, fn, signed=False):
        w, n = self._vw(o[0])
        a = lanes(self.vget(o[1]), w, n); b = lanes(self.vget(o[2]), w, n)
        if signed:
            a = [sx(x, w) for x in a]; b = [sx(x, w) for x in b]
        self.vset(o[0], pack([fn(x, y, w) for x, y in zip(a, b)], w))
    def i_smax(self, o): self._lanewise(o, lambda x, y, w: max(x, y), True)
    def i_smin(self, o): self._lanewise(o, lambda x, y, w: min(x, y), True)
    def i_umax(self, o): self._lanewise(o, lambda x, y, w: max(x, y))
    def i_umin(self, o): self._lanewise(o, lambda x, y, w: min(x, y))
    def i_cmeq(self, o):
        if o[2].startswith('#'):
            w, n = self._vw(o[0]); z = imm(o[2])
            self.vset(o[0], pack([((1 << w) - 1) if x == z else 0 for x in lanes(self.vget(o[1]), w, n)], w)); return
        self._lanewise(o, lambda x, y, w: ((1 << w) - 1) if x == y else 0)
    def i_cmhi(self, o): self._lanewise(o, lambda x, y, w: ((1 << w) - 1) if x > y else 0)
    def i_cmhs(self, o): self._lanewise(o, lambda x, y, w: ((1 << w) - 1) if x >= y else 0)
    def i_cmgt(self, o): self._lanewise(o, lambda x, y, w: ((1 << w) - 1) if x > y else 0, True)
    def i_cmge(self, o): self._lanewise(o, lambda x, y, w: ((1 << w) - 1) if x >= y else 0, True)
    def i_bsl(self, o):
        d = self.vget(o[0]); a = self.vget(o[1]); b = self.vget(o[2])
        self.vset(o[0], (a & d) | (b & ~d))
    def i_bit(self, o):
        d = self.vget(o[0]); a = self.vget(o[1]); m = self.vget(o[2])
        self.vset(o[0], (a & m) | (d & ~m))
    def i_bif(self, o):
        d = self.vget(o[0]); a = self.vget(o[1]); m = self.vget(o[2])
        self.vset(o[0], (a & ~m) | (d & m))
    def i_tbx(self, o):
        tab = self.vget(o[1]); idx = self.vget(o[2]); d = self.vget(o[0])
        w, n = self._vw(o[0])
        tl = lanes(tab, 8, 16); il = lanes(idx, 8, n); dl = lanes(d, 8, n)
        self.vset(o[0], pack([tl[i] if i < 16 else dl[k] for k, i in enumerate(il)], 8))
    def i_tbl(self, o):
        tab = self.vget(o[1]); idx = self.vget(o[2])
        w, n = self._vw(o[0])
        tl = lanes(tab, 8, 16); il = lanes(idx, 8, n)
        self.vset(o[0], pack([tl[i] if i < 16 else 0 for i in il], 8))
    def i_addp(self, o):
        if o[0][0] == 'd':  # addp d, v.2d
            a = lanes(self.vget(o[1]), 64, 2); self.vset(o[0], (a[0] + a[1]) & M64); return
        w, n = self._vw(o[0])
        a = lanes(self.vget(o[1]), w, n); b = lanes(self.vget(o[2]), w, n)
        cat = a + b
        self.vset(o[0], pack([cat[2 * i] + cat[2 * i + 1] for i in range(n)], w))
    def i_smaxv(self, o):
        w, n = self._vw(o[1]); a = [sx(x, w) for x in lanes(self.vget(o[1]), w, n)]
        self.vset(o[0], max(a) & ((1 << w) - 1))
    def i_umaxv(self, o):
        w, n = self._vw(o[1]); self.vset(o[0], max(lanes(self.vget(o[1]), w, n)))
    def i_uzp1(self, o):
        w, n = self._vw(o[0]); cat = lanes(self.vget(o[1]), w, n) + lanes(self.vget(o[2]), w, n)
        self.vset(o[0], pack(cat[0::2], w))
    def i_uzp2(self, o):
        w, n = self._vw(o[0]); cat = lanes(self.vget(o[1]), w, n) + lanes(self.vget(o[2]), w, n)
        self.vset(o[0], pack(cat[1::2], w))
    def i_cnt(self, o):
        w, n = self._vw(o[0]); self.vset(o[0], pack([bin(x).count('1') for x in lanes(self.vget(o[1]), 8, n)], 8))
    def i_uaddlp(self, o):
        wd, nd = self._vw(o[0]); ws, ns = self._vw(o[1]); a = lanes(self.vget(o[1]), ws, ns)
        self.vset(o[0], pack([a[2 * i] + a[2 * i + 1] for i in range(nd)], wd))
    def i_uadalp(self, o):
        wd, nd = self._vw(o[0]); ws, ns = self._vw(o[1]); a = lanes(self.vget(o[1]), ws, ns)
        d = lanes(self.vget(o[0]), wd, nd)
        self.vset(o[0], pack([d[i] + a[2 * i] + a[2 * i + 1] for i in range(nd)], wd))
    def i_ushl(self, o):
        if o[0][0] == 'd':
            v = self.vget(o[1]); s = sx(self.vget(o[2]) & 0xff, 8)
            self.vset(o[0], ((v << s) if s >= 0 else (v >> -s)) & M64 if abs(s) < 64 else 0); return
        w, n = self._vw(o[0]); a = lanes(self.vget(o[1]), w, n); b = lanes(self.vget(o[2]), w, n)
        out = []
        for x, y in zip(a, b):
            s = sx(y & 0xff, 8)
            out.append(0 if abs(s) >= w else ((x << s) if s >= 0 else (x >> -s)))
        self.vset(o[0], pack(out, w))
    def i_st1(self, o):
        m = re.match(r'^\{\s*v(\d+)\.(\w)\s*\}\[(\d+)\]$', o[0])
        if not m: raise Stop('st1 ' + o[0])
        ew = SCAL[m.group(2)]; idx = int(m.group(3))
        e = (self.v[int(m.group(1))] >> (ew * idx)) & ((1 << ew) - 1)
        a, wb, nv = self.addr(o[1:])
        self.m.write(a, ew // 8, e)
        if wb: self.wr(wb, nv)


def run_step_with_link(cpu):
    """Patch: bl needs the return address, which step() knows."""
    pass


# bl needs the address of the next instruction; wrap step to record it.
_orig_step = CPU.step


def _step(self, pc):
    self._pc_next = pc + 4
    return _orig_step(self, pc)


CPU.step = _step
