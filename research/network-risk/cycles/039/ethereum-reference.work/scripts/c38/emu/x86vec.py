"""Vector extension of the x86 model for the evm2 jump destination kernels of the tempo v1.19.1 x86_64 release.

Registers xmm/ymm/zmm 0..31 share one 512 bit value each. Legacy SSE writes keep the bits above 128,
VEX and EVEX writes clear the bits above the operand width. Opmask registers k0..k7 are 64 bit.
Only the instructions the three kernels and their dispatcher use are modelled; anything else raises.
"""
import re
from x86emu import Stop, ALIAS, M64
from x86emu2 import CPU2, lanes, pack

M512 = (1 << 512) - 1
VW = {'x': 128, 'y': 256, 'z': 512}


class VCPU(CPU2):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.z = [0] * 32
        self.k = [0] * 8

    # ---- registers
    def getr(self, name):
        m = re.match(r'^([xyz])mm(\d+)$', name)
        if m:
            b = VW[m.group(1)]
            return self.z[int(m.group(2))] & ((1 << b) - 1), b
        m = re.match(r'^k(\d)$', name)
        if m:
            return self.k[int(m.group(1))], 64
        return super().getr(name)

    def setr(self, name, v, vex_zero=True):
        m = re.match(r'^([xyz])mm(\d+)$', name)
        if m:
            b = VW[m.group(1)]
            self.z[int(m.group(2))] = v & ((1 << b) - 1)
            return
        m = re.match(r'^k(\d)$', name)
        if m:
            self.k[int(m.group(1))] = v & M64
            return
        return super().setr(name, v)

    def opnd(self, s):
        s = s.strip()
        m = re.match(r'^ZMMWORD PTR (.*)$', s)
        if m:
            return ('m', self.ea(m.group(1)), 512)
        if re.match(r'^[xyz]mm\d+$', s) or re.match(r'^k\d$', s):
            return ('r', s, self.getr(s)[1])
        return super().opnd(s)

    def _xget(self, o):
        if o[0] == 'r' and re.match(r'^[xyz]mm', o[1]):
            return self.getr(o[1])[0]
        if o[0] == 'm':
            return self.read(o[1], o[2] // 8)
        return self.get(o)

    def _xput(self, o, v):
        """Legacy SSE write: keeps the upper bits of the full register."""
        if o[0] == 'r' and o[1].startswith('xmm'):
            i = int(o[1][3:]); self.z[i] = (self.z[i] & ~((1 << 128) - 1)) | (v & ((1 << 128) - 1))
        elif o[0] == 'm':
            self.write(o[1], o[2] // 8, v)
        else:
            self.put(o, v)

    def _vput(self, o, v):
        """VEX or EVEX write: clears bits above the operand width."""
        if o[0] == 'm':
            self.write(o[1], o[2] // 8, v); return
        self.setr(o[1], v)

    @staticmethod
    def mask_of(s):
        m = re.match(r'^(.*?)\{(k\d)\}(\{z\})?$', s.strip())
        if m:
            return m.group(1), int(m.group(2)[1]), bool(m.group(3))
        return s.strip(), None, False

    def merge(self, d, new, kidx, zero, w=8):
        if kidx is None:
            return new
        old = self._xget(d)
        km = self.k[kidx]
        n = d[2] // w
        on = lanes(old, w, n); nn = lanes(new, w, n)
        return pack([nn[i] if (km >> i) & 1 else (0 if zero else on[i]) for i in range(n)], w)

    # ---- moves
    def _vmov(self, o, pc, n):
        ds, kidx, zero = self.mask_of(o[0])
        d = self.opnd(ds); s = self.opnd(o[1])
        v = self._xget(s)
        if d[0] == 'm':
            self.write(d[1], d[2] // 8, v); return
        if s[0] == 'm':
            v &= (1 << d[2]) - 1
        self._vput(d, self.merge(d, v, kidx, zero))
    i_vmovdqa = i_vmovdqu = i_vmovdqa64 = i_vmovdqu64 = i_vmovdqu8 = i_vmovdqa32 = i_vmovdqu32 = _vmov
    def i_vmovd(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1])
        if d[0] == 'r' and re.match(r'^[xyz]mm', d[1]):
            self._vput(('r', 'xmm' + d[1][3:], 128), self.get(s) & 0xffffffff)
        else:
            self.put(d, self._xget(s) & 0xffffffff)
    def i_vpbroadcastb(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1])
        b = (self._xget(s) if not (s[0] == 'r' and s[1] in ALIAS) else self.get(s)) & 0xff
        self._vput(d, pack([b] * (d[2] // 8), 8))
    def _bcast(self, o, w):
        # cycle 38: vpbroadcastd / vpbroadcastq from memory or from the low lane of a vector register
        d = self.opnd(o[0]); s = self.opnd(o[1])
        v = (self.read(s[1], w // 8) if s[0] == 'm' else self._xget(s)) & ((1 << w) - 1)
        self._vput(d, pack([v] * (d[2] // w), w))
    def i_vpbroadcastd(self, o, pc, n): self._bcast(o, 32)
    def i_vpbroadcastq(self, o, pc, n): self._bcast(o, 64)
    def i_vbroadcasti128(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1]); v = self.read(s[1], 16)
        self._vput(d, v | (v << 128))
    def i_vinserti128(self, o, pc, n):
        d = self.opnd(o[0]); s1 = self._xget(self.opnd(o[1])); s2 = self._xget(self.opnd(o[2])) & ((1 << 128) - 1)
        k = int(o[3], 0) & 1
        lo, hi = s1 & ((1 << 128) - 1), (s1 >> 128) & ((1 << 128) - 1)
        if k: hi = s2
        else: lo = s2
        self._vput(d, lo | (hi << 128))
    def i_vextracti128(self, o, pc, n):
        d = self.opnd(o[0]); s = self._xget(self.opnd(o[1])); k = int(o[2], 0) & 1
        self._vput(d, (s >> (128 * k)) & ((1 << 128) - 1))
    def i_pinsrw(self, o, pc, n):
        d = self.opnd(o[0]); v = self.get(self.opnd(o[1])) & 0xffff; k = int(o[2], 0) & 7
        x = self._xget(d) & ((1 << 128) - 1)
        x = (x & ~(0xffff << (16 * k))) | (v << (16 * k))
        self._xput(d, x)
    def i_vzeroupper(self, o, pc, n):
        for i in range(16):
            self.z[i] &= (1 << 128) - 1

    # ---- byte lane operations, legacy two operand form
    def _sse(self, o, fn):
        d = self.opnd(o[0]); s = self.opnd(o[1])
        a = self._xget(d) & ((1 << 128) - 1); b = self._xget(s) & ((1 << 128) - 1)
        self._xput(d, fn(a, b, 128))

    # VEX/EVEX three operand form with optional merge mask on the destination
    def _avx(self, o, fn):
        ds, kidx, zero = self.mask_of(o[0])
        d = self.opnd(ds); w = d[2]
        a = self._xget(self.opnd(o[1])) & ((1 << w) - 1); b = self._xget(self.opnd(o[2])) & ((1 << w) - 1)
        self._vput(d, self.merge(d, fn(a, b, w), kidx, zero))

    @staticmethod
    def bw(fn):
        return lambda a, b, w: pack([fn(x, y) for x, y in zip(lanes(a, 8, w // 8), lanes(b, 8, w // 8))], 8)

    @staticmethod
    def s8(x): return x - 256 if x & 0x80 else x

    @staticmethod
    def shuf(t, idx, w):
        tl = lanes(t, 8, w // 8); il = lanes(idx, 8, w // 8)
        out = []
        for i, x in enumerate(il):
            base = (i // 16) * 16
            out.append(0 if x & 0x80 else tl[base + (x & 15)])
        return pack(out, 8)

    def i_pshufb(self, o, pc, n): self._sse(o, lambda a, b, w: self.shuf(a, b, w))
    def i_vpshufb(self, o, pc, n): self._avx(o, lambda a, b, w: self.shuf(a, b, w))
    def i_pmaxub(self, o, pc, n): self._sse(o, self.bw(max))
    def i_vpmaxub(self, o, pc, n): self._avx(o, self.bw(max))
    def i_pminub(self, o, pc, n): self._sse(o, self.bw(min))
    def i_vpminub(self, o, pc, n): self._avx(o, self.bw(min))
    def i_pmaxsb(self, o, pc, n): self._sse(o, self.bw(lambda x, y: x if self.s8(x) >= self.s8(y) else y))
    def i_vpmaxsb(self, o, pc, n): self._avx(o, self.bw(lambda x, y: x if self.s8(x) >= self.s8(y) else y))
    def i_paddb(self, o, pc, n): self._sse(o, self.bw(lambda x, y: x + y))
    def i_vpaddb(self, o, pc, n): self._avx(o, self.bw(lambda x, y: x + y))
    def i_psubb(self, o, pc, n): self._sse(o, self.bw(lambda x, y: x - y))
    def i_vpsubb(self, o, pc, n): self._avx(o, self.bw(lambda x, y: x - y))
    def i_pcmpeqb(self, o, pc, n): self._sse(o, self.bw(lambda x, y: 0xff if x == y else 0))
    def i_pcmpgtb(self, o, pc, n): self._sse(o, self.bw(lambda x, y: 0xff if self.s8(x) > self.s8(y) else 0))
    def i_pxor(self, o, pc, n): self._sse(o, lambda a, b, w: a ^ b)
    def i_por(self, o, pc, n): self._sse(o, lambda a, b, w: a | b)
    def i_pand(self, o, pc, n): self._sse(o, lambda a, b, w: a & b)
    def i_pandn(self, o, pc, n): self._sse(o, lambda a, b, w: (~a & ((1 << w) - 1)) & b)
    def i_vpxor(self, o, pc, n): self._avx(o, lambda a, b, w: a ^ b)
    def i_vpor(self, o, pc, n): self._avx(o, lambda a, b, w: a | b)
    def i_vpand(self, o, pc, n): self._avx(o, lambda a, b, w: a & b)
    def i_vpandn(self, o, pc, n): self._avx(o, lambda a, b, w: (~a & ((1 << w) - 1)) & b)

    def i_vpcmpeqd(self, o, pc, n):
        self._avx(o, lambda a, b, w: pack([0xffffffff if x == y else 0 for x, y in zip(lanes(a, 32, w // 32), lanes(b, 32, w // 32))], 32))

    def _cmp_any(self, o, pred, signed=False):
        ds, kidx, zero = self.mask_of(o[0])
        if re.match(r'^k\d$', ds):  # EVEX compare into an opmask
            a = self._xget(self.opnd(o[1])); s2 = self.opnd(o[2]); w = self.opnd(o[1])[2]
            b = self._xget(s2) & ((1 << w) - 1)
            la, lb = lanes(a, 8, w // 8), lanes(b, 8, w // 8)
            if signed:
                la = [self.s8(x) for x in la]; lb = [self.s8(x) for x in lb]
            r = sum(1 << i for i, (x, y) in enumerate(zip(la, lb)) if pred(x, y))
            if kidx is not None:
                r &= self.k[kidx]
            self.setr(ds, r); return
        # VEX form into a vector register
        def fn(a, b, w):
            la, lb = lanes(a, 8, w // 8), lanes(b, 8, w // 8)
            if signed:
                la = [self.s8(x) for x in la]; lb = [self.s8(x) for x in lb]
            return pack([0xff if pred(x, y) else 0 for x, y in zip(la, lb)], 8)
        self._avx(o, fn)
    def i_vpcmpeqb(self, o, pc, n): self._cmp_any(o, lambda x, y: x == y)
    def i_vpcmpgtb(self, o, pc, n): self._cmp_any(o, lambda x, y: x > y, signed=True)
    def i_vpcmpltub(self, o, pc, n): self._cmp_any(o, lambda x, y: x < y)
    def i_vpcmpnltub(self, o, pc, n): self._cmp_any(o, lambda x, y: x >= y)
    def i_vpcmpleub(self, o, pc, n): self._cmp_any(o, lambda x, y: x <= y)
    def i_vpcmpnleub(self, o, pc, n): self._cmp_any(o, lambda x, y: x > y)

    def i_pblendvb(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1]); m = self.z[0] & ((1 << 128) - 1)
        a = self._xget(d) & ((1 << 128) - 1); b = self._xget(s) & ((1 << 128) - 1)
        self._xput(d, pack([y if mm & 0x80 else x for x, y, mm in zip(lanes(a, 8, 16), lanes(b, 8, 16), lanes(m, 8, 16))], 8))
    def i_vpblendvb(self, o, pc, n):
        d = self.opnd(o[0]); w = d[2]
        a = self._xget(self.opnd(o[1])); b = self._xget(self.opnd(o[2])); m = self._xget(self.opnd(o[3]))
        self._vput(d, pack([y if mm & 0x80 else x for x, y, mm in zip(lanes(a, 8, w // 8), lanes(b, 8, w // 8), lanes(m, 8, w // 8))], 8))
    def i_vpblendmb(self, o, pc, n):
        ds, kidx, zero = self.mask_of(o[0]); d = self.opnd(ds); w = d[2]
        a = self._xget(self.opnd(o[1])); b = self._xget(self.opnd(o[2]))
        km = self.k[kidx] if kidx is not None else M64
        self._vput(d, pack([y if (km >> i) & 1 else x for i, (x, y) in enumerate(zip(lanes(a, 8, w // 8), lanes(b, 8, w // 8)))], 8))
    def i_pmovmskb(self, o, pc, n):
        d = self.opnd(o[0]); a = self._xget(self.opnd(o[1])) & ((1 << 128) - 1)
        self.put(d, sum(((x >> 7) & 1) << i for i, x in enumerate(lanes(a, 8, 16))))
    def i_vpmovmskb(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1]); a = self._xget(s)
        self.put(d, sum(((x >> 7) & 1) << i for i, x in enumerate(lanes(a, 8, s[2] // 8))))
    def i_movd(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1])
        if d[0] == 'r' and d[1].startswith('xmm'):
            self._xput(d, self.get(s) & 0xffffffff)  # movd to xmm clears bits 127:32
        else:
            self.put(d, self._xget(s) & 0xffffffff)
    def i_movq(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1])
        if d[0] == 'r' and d[1].startswith('xmm'):
            v = self._xget(s) & M64 if (s[0] == 'r' and s[1].startswith('xmm')) or s[0] == 'm' else self.get(s)
            self._xput(d, v & M64)
        else:
            self.put(d, self._xget(s) & M64)

    # ---- permutes
    def i_vpermb(self, o, pc, n):
        ds, kidx, zero = self.mask_of(o[0]); d = self.opnd(ds); w = d[2]
        idx = lanes(self._xget(self.opnd(o[1])), 8, w // 8); tab = lanes(self._xget(self.opnd(o[2])), 8, w // 8)
        self._vput(d, self.merge(d, pack([tab[i & (w // 8 - 1)] for i in idx], 8), kidx, zero))
    def i_vpermt2b(self, o, pc, n):
        ds, kidx, zero = self.mask_of(o[0]); d = self.opnd(ds); w = d[2]; nb = w // 8
        t1 = lanes(self._xget(d), 8, nb); idx = lanes(self._xget(self.opnd(o[1])), 8, nb); t2 = lanes(self._xget(self.opnd(o[2])), 8, nb)
        self._vput(d, self.merge(d, pack([(t2 if i & nb else t1)[i & (nb - 1)] for i in idx], 8), kidx, zero))
    def i_vpermi2b(self, o, pc, n):
        ds, kidx, zero = self.mask_of(o[0]); d = self.opnd(ds); w = d[2]; nb = w // 8
        idx = lanes(self._xget(d), 8, nb); t1 = lanes(self._xget(self.opnd(o[1])), 8, nb); t2 = lanes(self._xget(self.opnd(o[2])), 8, nb)
        self._vput(d, self.merge(d, pack([(t2 if i & nb else t1)[i & (nb - 1)] for i in idx], 8), kidx, zero))

    # ---- opmask
    def i_kmovq(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1]); v = self.get(s) if s[0] != 'm' else self.read(s[1], 8)
        if d[0] == 'm':
            self.write(d[1], 8, v)
        else:
            self.put(d, v & M64)
    def i_kmovw(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1]); v = (self.get(s) if s[0] != 'm' else self.read(s[1], 2)) & 0xffff
        if d[0] == 'm':
            self.write(d[1], 2, v)
        else:
            self.put(d, v)
    def i_kmovd(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1]); v = (self.get(s) if s[0] != 'm' else self.read(s[1], 4)) & 0xffffffff
        if d[0] == 'm':
            self.write(d[1], 4, v)
        else:
            self.put(d, v)
    def i_korq(self, o, pc, n): self.setr(o[0], self.k[int(o[1][1])] | self.k[int(o[2][1])])
    def i_korw(self, o, pc, n): self.setr(o[0], (self.k[int(o[1][1])] | self.k[int(o[2][1])]) & 0xffff)
    def i_kortestq(self, o, pc, n):
        v = self.k[int(o[0][1])] | self.k[int(o[1][1])]
        self.zf = int(v == 0); self.cf = int(v == M64)
