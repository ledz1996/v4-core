"""Cycle 31, theme-tempo-binary-call-rollback, Task 2 (L-1213) and Task 5 faults, x86_64 (the build behind
rpc.mainnet.tempo.xyz).

Runs the shipped tempo v1.19.1 x86_64 State::rollback 0x1e8d350 (jump table 0x65fe30) with its AccountChange
arm 0x1e8d4b7-0x1e8d612, the flags rule 0x1e8d398-0x1e8d401, the not-found arm 0x1e8d7af, the StorageChange and
StorageWarmed arms, the account map lookup 0x1e7bd20 and the slot map lookup 0x1e852c0, on real hashbrown
tables with SSE2 16-byte control groups (0x110 byte account buckets, 0x68 byte slot buckets) built in model
memory. Every record pointer comes from the lifted lookups.

Modelled in Python (stated in the results): table insert and resize (hashbrown find_insert_slot with 16-byte
groups and the triangular probe, hash transcribed from the lifted lookup), the journal writers (AccountChange
from AccountHandle::record_change and Drop; StorageChange and StorageWarmed with the layout the cycle 30 x86
SSSTORE segments wrote: tag 3 key +8 previous +0x28 address +0x48; tag 5 key +8 address +0x28), and the overlay
loads. The lock prefix of 'lock dec' is dropped when the text is loaded (single-threaded model). Transient
storage is not exercised here (cycle 30 ran the x86 transient arms).

usage: python3 -I acct_x64.py <bin> <c30 build dir> <out.json> [fault] [seed] [features]
"""
import json, os, random, sys
C30 = '/home/user/v4-core/research/network-risk/cycles/030/theme-tempo-binary-storage-journal.work/scripts'
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/029/theme-tempo-binary-keccak-transient.work/scripts')
from x86emu2 import CPU2, Prog, Stop, rewrite_rip, M64

BIN, BUILD30, OUT = sys.argv[1:4]
FAULT = sys.argv[4] if len(sys.argv) > 4 else 'none'
SEED = int(sys.argv[5]) if len(sys.argv) > 5 else 2026112741
FEATURES = int(sys.argv[6], 0) if len(sys.argv) > 6 else (1 << 14)
M = (1 << 256) - 1
TEXT_LO, TEXT_HI, TEXT_DELTA = 0x189bb00, 0x189bb00 + 0x521d110, 0x1000


class CPU(CPU2):
    def read(self, a, n):
        if TEXT_LO <= a and a + n <= TEXT_HI and (a not in self.mem):
            return int.from_bytes(self.fb[a - TEXT_DELTA:a - TEXT_DELTA + n], 'little')
        return super().read(a, n)

    def step(self, pc):
        self.steps += 1
        return super().step(pc)

    def i_jmp(self, o, pc, n):
        if o[0] in self.r:
            return self.r[o[0]]
        return super().i_jmp(o, pc, n)

    def i_pshuflw(self, o, pc, n):
        src = self._xget(self.opnd(o[1])); k = int(o[2], 16)
        w = [(src >> (16 * i)) & 0xffff for i in range(4)]
        lo = sum(w[(k >> (2 * i)) & 3] << (16 * i) for i in range(4))
        self._xput(self.opnd(o[0]), (src & (((1 << 64) - 1) << 64)) | lo)

    def i_call(self, o, pc, n):
        if o[0] in self.r:
            t = self.r[o[0]]
            if t in self.externs:
                self.externs[t](self); return n
            raise Stop('register call to %x' % t)
        return super().i_call(o, pc, n)


FILES = ['x64_0x1e7bd20.s', 'x64_0x1e852c0.s', 'x64_rollback.s', 'x64_0x1e8d9e0.s', 'x64_0x1e8dcc0.s']
fb = open(BIN, 'rb').read()
text = '\n'.join(open(os.path.join(BUILD30, f)).read() for f in FILES).replace('lock dec', 'dec')
prog = Prog(rewrite_rip(text))

FAULTS = {
    # bytes 0x40..0x50 of present restored from entry+0x20 instead of entry+0x40
    'wrong_field': {0x1e8d54e: 'movups xmm0,XMMWORD PTR [rbp+0x20]'},
    # the 16 bytes at present+0x10..0x20 are not written back
    'skip_part': {0x1e8d5f6: 'nop'},
    # none of present is written back
    'skip_present': {0x1e8d5c9: 'nop', 0x1e8d5d2: 'nop', 0x1e8d5ed: 'nop', 0x1e8d5f1: 'nop', 0x1e8d5f6: 'nop', 0x1e8d5fb: 'nop'},
    # the flags byte is not written back
    'skip_flags': {0x1e8d3fa: 'nop'},
    # the precompile-3 rule inverted: mask set for every address except 3
    'touch_inverted': {0x1e8d3de: 'setne  al'},
    # account lookup gives up after the first group without a match
    'acct_probe_short': {0x1e7bdfe: 'jmp    1e7be23'},
    # account lookup ignores the last four address bytes
    'acct_key_short': {0x1e7bdce: 'movdqa xmm5,xmm4'},
    # slot lookup gives up after the first group without a match
    'slot_probe_short': {0x1e8539e: 'jmp    1e853c0'},
}
faults = dict(FAULTS.get(FAULT, {}))
if FAULT not in FAULTS and FAULT not in ('none', 'commit_on_revert'):
    raise SystemExit('unknown fault')

EVM = 0x10000000; STATE = EVM + 0xe8; ACCTMAP = STATE + 0x1d8
JBUF, JCAP = 0x20000000, 8192
SECRET = 0x6cba938
ARGS = 0x60000000
HEAP = 0x80000000
ARCS = 0x50000000
SP0 = 0x7ffff0000000
ABUCK, SBUCK, REC, PRES, SMAP, FLAGS = 0x110, 0x68, 0x18, 0x60, 0xc0, 0xf0
WARM, TOUCHED, CREATED = 1, 2, 16
OB, OH, ON = 0x10, 0x30, 0x50
GW = 16


def ab(a): return a.to_bytes(20, 'big')


class Machine:
    def __init__(self, seed):
        self.rnd = random.Random(seed)
        ext = {}
        for a in (0x1e192d0, 0x1e246e0, 0x1e19150, 0x1a3bc30, 0x6ab74b0, 0x1e19da0, 0x1e19dc0, 0x1d48ad3, 0x4cd3520):
            ext[a] = self.x_never(a)
        self.cpu = CPU(prog, fb, 0x189aab8, externs=ext, got={}, faults=faults)
        self.cpu.steps = 0
        for i in range(0, 0x40, 8): self.w(SECRET + i, 8, self.rnd.getrandbits(64))
        self.S = self.r(SECRET, 8)
        self.w(STATE + 0x20, 8, JCAP); self.w(STATE + 0x28, 8, JBUF); self.w(STATE + 0x30, 8, 0)
        self.w(STATE + 0x40, 8, 0x8); self.w(STATE + 0x48, 8, 0)
        self.hp = HEAP; self.narc = 0; self.grows = 0
        self.new_table(ACCTMAP, 16, ABUCK, self.rnd.getrandbits(64))
        self.backing = {}

    def r(self, a, n): return self.cpu.read(a, n)
    def w(self, a, n, v): self.cpu.write(a, n, v)

    def x_never(self, a):
        def f(cpu): raise Stop('extern %x reached' % a)
        return f

    def alloc(self, n):
        p = (self.hp + 15) & ~15; self.hp = p + n; return p

    def new_table(self, hdr, nb, bs, seed):
        base = self.alloc(nb * bs + nb + GW); ctrl = base + nb * bs
        for i in range(nb + GW): self.w(ctrl + i, 1, 0xff)
        self.w(hdr, 8, ctrl); self.w(hdr + 8, 8, nb - 1); self.w(hdr + 0x10, 8, nb * 7 // 8)
        self.w(hdr + 0x18, 8, 0); self.w(hdr + 0x20, 8, seed)

    def h_acct(self, hdr, a):
        k = ab(a) if isinstance(a, int) else a
        k0, k1, k2 = int.from_bytes(k[0:8], 'little'), int.from_bytes(k[8:16], 'little'), int.from_bytes(k[16:20], 'little')
        seed = self.r(hdr + 0x20, 8)
        p = (k0 ^ seed) * (self.S ^ k1); x = (p >> 64) ^ (p & M64) ^ k2
        p = x * self.S; return ((p >> 64) ^ (p & M64)) & M64

    def h_slot(self, hdr, key):
        k = [(key >> (64 * i)) & M64 for i in range(4)]
        seed = self.r(hdr + 0x20, 8)
        p = (k[0] ^ seed) * (self.S ^ k[1]); x = (p >> 64) ^ (p & M64) ^ k[2]
        p = x * (k[3] ^ self.S); return ((p >> 64) ^ (p & M64)) & M64

    def find_slot(self, ctrl, mask, h):
        pos = h & mask; stride = 0
        while True:
            for b in range(GW):
                i = (pos + b) & mask
                if self.r(ctrl + i, 1) & 0x80: return i
            stride += GW; pos = (pos + stride) & mask

    def set_ctrl(self, ctrl, mask, i, v):
        self.w(ctrl + i, 1, v); self.w(ctrl + (((i - GW) & mask) + GW), 1, v)

    def table_insert(self, hdr, bs, h, keyb, recb):
        ctrl = self.r(hdr, 8); mask = self.r(hdr + 8, 8)
        i = self.find_slot(ctrl, mask, h)
        empty = self.r(ctrl + i, 1) == 0xff
        if empty and self.r(hdr + 0x10, 8) == 0:
            self.grow(hdr, bs); return self.table_insert(hdr, bs, h, keyb, recb)
        self.set_ctrl(ctrl, mask, i, h >> 57)
        b = ctrl - (i + 1) * bs
        self.w(b, len(keyb), int.from_bytes(keyb, 'little')); self.w(b + len(keyb), len(recb), int.from_bytes(recb, 'little'))
        if empty: self.w(hdr + 0x10, 8, self.r(hdr + 0x10, 8) - 1)
        self.w(hdr + 0x18, 8, self.r(hdr + 0x18, 8) + 1)
        return b

    def table_delete(self, hdr, bs, b):
        ctrl = self.r(hdr, 8); mask = self.r(hdr + 8, 8)
        self.set_ctrl(ctrl, mask, (ctrl - b) // bs - 1, 0x80); self.w(hdr + 0x18, 8, self.r(hdr + 0x18, 8) - 1)

    def buckets(self, hdr, bs):
        ctrl = self.r(hdr, 8); mask = self.r(hdr + 8, 8)
        return [ctrl - (i + 1) * bs for i in range(mask + 1) if not (self.r(ctrl + i, 1) & 0x80)]

    def grow(self, hdr, bs):
        self.grows += 1
        old = [self.r(b, bs).to_bytes(bs, 'little') for b in self.buckets(hdr, bs)]
        nb = (self.r(hdr + 8, 8) + 1) * 2; seed = self.r(hdr + 0x20, 8)
        self.new_table(hdr, nb, bs, seed)
        for raw in old:
            if bs == ABUCK: h = self.h_acct(hdr, raw[:20]); k = raw[:REC]
            else: h = self.h_slot(hdr, int.from_bytes(raw[:32], 'little')); k = raw[:0x20]
            self.table_insert(hdr, bs, h, k, raw[len(k):])

    def run(self, entry, args):
        c = self.cpu
        for k in list(c.r): c.r[k] = 0
        c.y = [0] * 16
        for k, v in zip(['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9'], args): c.r[k] = v & M64
        rsp = SP0 - 0x8; c.write(rsp, 8, 0xdead0000); c.r['rsp'] = rsp
        pc = entry; k = 0
        while pc != 0xdead0000:
            pc = c.step(pc); k += 1
            if k > 3_000_000: raise Stop('step limit')
        return c.r['rax']

    def lookup_acct(self, a):
        self.w(ARGS + 0x300, 20, int.from_bytes(ab(a), 'little'))
        return self.run(0x1e7bd20, [ACCTMAP, ARGS + 0x300])

    def lookup_slot(self, rec, key):
        for i in range(4): self.w(ARGS + 0x340 + 8 * i, 8, (key >> (64 * i)) & M64)
        return self.run(0x1e852c0, [rec + SMAP, ARGS + 0x340])

    def new_arc(self):
        p = ARCS + 0x10 * self.narc; self.narc += 1; self.w(p, 8, 1); self.w(p + 8, 8, 0); return p

    def info_bytes(self, info):
        b = bytearray(0x60)
        if info is None: b[0:8] = (2).to_bytes(8, 'little'); return bytes(b)
        b[0:8] = (1 if info['code'] else 0).to_bytes(8, 'little'); b[8:16] = info['code'].to_bytes(8, 'little')
        b[OB:OB + 32] = info['balance'].to_bytes(32, 'little'); b[OH:OH + 32] = info['codehash'].to_bytes(32, 'little')
        b[ON:ON + 8] = info['nonce'].to_bytes(8, 'little'); b[0x58:0x60] = info['ext'].to_bytes(8, 'little')
        return bytes(b)

    def read_info(self, p):
        tag = self.r(p, 8)
        if tag == 2: return None
        return {'balance': self.r(p + OB, 32), 'nonce': self.r(p + ON, 8), 'codehash': self.r(p + OH, 32),
                'code': self.r(p + 8, 8) if tag == 1 else 0, 'ext': self.r(p + 0x58, 8)}

    def load_acct(self, a, info):
        rec = self.lookup_acct(a)
        if rec: return rec
        ib = self.info_bytes(info); recb = bytearray(0xf8); recb[0:0x60] = ib; recb[PRES:PRES + 0x60] = ib
        if info:
            for k in ('code', 'ext'):
                if info[k]: self.w(info[k], 8, self.r(info[k], 8) + 2)
        b = self.table_insert(ACCTMAP, ABUCK, self.h_acct(ACCTMAP, a), ab(a) + bytes(4), bytes(recb))
        self.new_table(b + REC + SMAP, 16, SBUCK, self.rnd.getrandbits(64))
        if self.lookup_acct(a) != b + REC: raise Stop('lifted account lookup missed an inserted account')
        return b + REC

    def slot_rec(self, a, key):
        rec = self.lookup_acct(a)
        p = self.lookup_slot(rec, key)
        if p: return p
        v = self.backing.get((a, key), 0)
        self.table_insert(rec + SMAP, SBUCK, self.h_slot(rec + SMAP, key), key.to_bytes(32, 'little'),
                          v.to_bytes(32, 'little') * 2 + bytes(8))
        p = self.lookup_slot(rec, key)
        if not p: raise Stop('lifted slot lookup missed an inserted slot')
        return p

    def jlen(self): return self.r(STATE + 0x30, 8)

    def push_entry(self, raw):
        n = self.jlen(); self.w(JBUF + 0x78 * n, 0x78, int.from_bytes(raw.ljust(0x78, b'\0'), 'little')); self.w(STATE + 0x30, 8, n + 1)

    def mutate(self, a, fn):
        rec = self.lookup_acct(a)
        prev = self.r(rec + PRES, 0x60).to_bytes(0x60, 'little'); flags = self.r(rec + FLAGS, 1)
        info = self.read_info(rec + PRES)
        if info:
            for k in ('code', 'ext'):
                if info[k]: self.w(info[k], 8, self.r(info[k], 8) + 1)
        ni, nf = fn(info, flags)
        if ni is not None and info is not None:
            for k in ('code', 'ext'):
                if ni[k] != info[k] and info[k]: self.w(info[k], 8, self.r(info[k], 8) - 1)
        self.w(rec + PRES, 0x60, int.from_bytes(self.info_bytes(ni), 'little')); self.w(rec + FLAGS, 1, nf)
        self.push_entry(prev + ab(a) + bytes([flags]))

    def sload(self, a, key):
        p = self.slot_rec(a, key)
        if not self.r(p + 0x40, 1):
            self.w(p + 0x40, 1, 1); self.push_entry((5).to_bytes(8, 'little') + key.to_bytes(32, 'little') + ab(a))
        return sum(self.r(p + 0x20 + 8 * i, 8) << (64 * i) for i in range(4))

    def sstore(self, a, key, v):
        cur = self.sload(a, key)
        if cur == v: return
        p = self.slot_rec(a, key)
        self.push_entry((3).to_bytes(8, 'little') + key.to_bytes(32, 'little') + cur.to_bytes(32, 'little') + ab(a))
        for i in range(4): self.w(p + 0x20 + 8 * i, 8, (v >> (64 * i)) & M64)

    def rollback(self, cp):
        self.run(0x1e8d350, [STATE, cp, 0, FEATURES])


EMPTYH = 0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470
ADDRS = [0x33620f62c5b9b2086dd6b62f4a297a9f30347029, 0xcafe, 3]


def run_case(seed, ncoll, dels):
    rnd = random.Random(seed); mc = Machine(seed)
    ref = {}; refst = {}; loaded = {}
    def coll_addrs(n):
        h0 = mc.h_acct(ACCTMAP, ADDRS[0]); out = []
        while len(out) < n:
            a = rnd.getrandbits(160); h = mc.h_acct(ACCTMAP, a)
            if (h >> 57) == (h0 >> 57) and (h & 63) == (h0 & 63): out.append(a)
        return out
    coll = coll_addrs(ncoll) if ncoll else []
    order = ADDRS + coll
    for a in order:
        info = {'balance': rnd.choice([0, 7, 2 * 10 ** 18, M]), 'nonce': rnd.choice([0, 1, 2 ** 64 - 1, 5]), 'codehash': rnd.getrandbits(256),
                'code': mc.new_arc() if rnd.random() < 0.7 else 0, 'ext': mc.new_arc() if rnd.random() < 0.3 else 0}
        mc.load_acct(a, info); ref[a] = [dict(info), 0]; loaded[a] = (dict(info), 0)
    keys = [rnd.getrandbits(256) for _ in range(3)] + [0, 1, 6, M]
    if ncoll:
        hdr = mc.lookup_acct(ADDRS[0]) + SMAP; h0 = mc.h_slot(hdr, 6)
        while len(keys) < 7 + 2 * ncoll:
            k = rnd.getrandbits(256); h = mc.h_slot(hdr, k)
            if (h >> 57) == (h0 >> 57) and (h & 63) == (h0 & 63): keys.append(k)
    for a in order:
        for k in keys:
            if rnd.random() < 0.4: mc.backing[(a, k)] = rnd.getrandbits(256)
    if ncoll:
        for k in keys: mc.slot_rec(ADDRS[0], k)
    if dels:
        for a in coll_addrs(dels):
            rec = mc.load_acct(a, None); mc.table_delete(ACCTMAP, ABUCK, rec - REC)
    pool = list(order); fresh = [rnd.getrandbits(160) for _ in range(12)]
    vals = [0, 1, 2, 10 ** 18, M, M - 3, rnd.getrandbits(256)]
    def gen(d):
        r = []
        for _ in range(rnd.randint(1, 8)):
            c = rnd.random(); a = rnd.choice(pool)
            if c < 0.2: r.append(('val', a, rnd.choice(pool + fresh[:2]), rnd.choice([0, 1, 5, 10 ** 18, 3 * 10 ** 18])))
            elif c < 0.28: r.append(('nonce', a))
            elif c < 0.34 and fresh: f = fresh.pop(); pool.append(f); r.append(('create', f))
            elif c < 0.38: r.append(('code', a))
            elif c < 0.43: r.append(('touch', a))
            elif c < 0.68: r.append(('ss', a, rnd.choice(keys), rnd.choice(vals)))
            elif c < 0.76: r.append(('sl', a, rnd.choice(keys)))
            elif d < 4: r.append(('frame', rnd.random() < 0.65, gen(d + 1)))
        return r
    seq = gen(0)
    reads = [[], []]

    def ensure(a):
        if not mc.lookup_acct(a): mc.load_acct(a, None)
        if a not in ref: ref[a] = [None, 0]; loaded[a] = (None, 0)

    def snap(): return ({a: [dict(v[0]) if v[0] else None, v[1]] for a, v in ref.items()}, dict(refst))

    def restore(s):
        cur = dict(ref); acc, st = s
        ref.clear(); ref.update(acc); refst.clear(); refst.update(st)
        for a, v in cur.items():
            if a not in ref: ref[a] = [dict(loaded[a][0]) if loaded[a][0] else None, loaded[a][1]]
            if FEATURES & (1 << 14) and a == 3: ref[a][1] = (ref[a][1] & ~TOUCHED) | (v[1] & TOUCHED)

    def do(op):
        k = op[0]
        if k == 'val':
            _, a, b, v = op; ensure(a); ensure(b)
            def sub(i, f):
                i = dict(i) if i else {'balance': 0, 'nonce': 0, 'codehash': EMPTYH, 'code': 0, 'ext': 0}; i['balance'] -= v; return i, f | TOUCHED
            def add(i, f):
                i = dict(i) if i else {'balance': 0, 'nonce': 0, 'codehash': EMPTYH, 'code': 0, 'ext': 0}; i['balance'] = min(i['balance'] + v, M); return i, f | TOUCHED
            for side in 'mr':
                if side == 'm': i0 = mc.read_info(mc.lookup_acct(a) + PRES)
                else: i0 = ref[a][0]
                bal = i0['balance'] if i0 else 0
                if v == 0: steps = [(b, lambda i, f: (i, f | TOUCHED))]
                elif bal < v: steps = []
                elif a == b: steps = [(a, lambda i, f: (i, f | TOUCHED))]
                else: steps = [(a, sub), (b, add)]
                for x, fn in steps:
                    if side == 'm': mc.mutate(x, fn)
                    else: ref[x] = list(fn(ref[x][0], ref[x][1]))
        elif k in ('nonce', 'create', 'code', 'touch'):
            a = op[1]; ensure(a)
            arc = mc.new_arc() if k in ('create', 'code') else 0
            if k == 'nonce':
                def fn(i, f):
                    i = dict(i) if i else {'balance': 0, 'nonce': 0, 'codehash': EMPTYH, 'code': 0, 'ext': 0}
                    if i['nonce'] < 2 ** 64 - 1: i['nonce'] += 1
                    return i, f | TOUCHED
            elif k == 'create':
                def fn(i, f): return {'balance': (i or {}).get('balance', 0), 'nonce': 1, 'codehash': 0x1234 + arc, 'code': arc, 'ext': 0}, f | CREATED | TOUCHED | WARM
            elif k == 'code':
                def fn(i, f):
                    i = dict(i) if i else {'balance': 0, 'nonce': 0, 'codehash': 0, 'code': 0, 'ext': 0}; i['code'] = arc; i['codehash'] = 0xabcd + arc; return i, f | TOUCHED
            else:
                def fn(i, f): return i, f | TOUCHED | WARM
            mc.mutate(a, fn); ref[a] = list(fn(ref[a][0], ref[a][1]))
            if arc: mc.w(arc, 8, mc.r(arc, 8) + 1)
        elif k == 'ss':
            _, a, key, v = op; ensure(a); mc.sstore(a, key, v); refst[(a, key)] = v
        elif k == 'sl':
            _, a, key = op; ensure(a); reads[0].append(mc.sload(a, key)); reads[1].append(refst.get((a, key), mc.backing.get((a, key), 0)))
        elif k == 'frame':
            cp = mc.jlen(); s = snap()
            for o in op[2]: do(o)
            if op[1]:
                if FAULT != 'commit_on_revert': mc.rollback(cp)
                restore(s)
    for op in seq: do(op)
    mism = []
    for a in ref:
        rec = mc.lookup_acct(a)
        if not rec: mism.append(('account missing', hex(a))); continue
        mi = mc.read_info(rec + PRES); ri = ref[a][0]
        if (mi is None) != (ri is None) or (mi and ri and any(mi[x] != ri[x] for x in ('balance', 'nonce', 'codehash', 'code', 'ext'))):
            mism.append(('present', hex(a), repr(mi), repr(ri)))
        if mc.r(rec + FLAGS, 1) != ref[a][1]: mism.append(('flags', hex(a), mc.r(rec + FLAGS, 1), ref[a][1]))
        for key in keys:
            p = mc.lookup_slot(rec, key)
            mv = sum(mc.r(p + 0x20 + 8 * i, 8) << (64 * i) for i in range(4)) if p else mc.backing.get((a, key), 0)
            rv = refst.get((a, key), mc.backing.get((a, key), 0))
            if mv != rv: mism.append(('storage', hex(a), hex(key), hex(mv), hex(rv)))
    if reads[0] != reads[1]: mism.append(('reads',))
    held = {}
    for b in mc.buckets(ACCTMAP, ABUCK):
        for off in (REC, REC + PRES):
            i = mc.read_info(b + off)
            if i:
                for x in (i['code'], i['ext']):
                    if x: held[x] = held.get(x, 0) + 1
    for j in range(mc.jlen()):
        e = JBUF + 0x78 * j
        if mc.r(e, 8) in (0, 1):
            i = mc.read_info(e)
            for x in (i['code'], i['ext']):
                if x: held[x] = held.get(x, 0) + 1
    for n in range(mc.narc):
        p = ARCS + 0x10 * n
        if mc.r(p, 8) != held.get(p, 0) + 1: mism.append(('arc count', hex(p), mc.r(p, 8), held.get(p, 0) + 1))
    return mism, seq, mc


if __name__ == '__main__':
    N = int(os.environ.get('NCASES', '300'))
    res = {'fault': FAULT, 'seed': SEED, 'features': FEATURES, 'cases': 0, 'mismatch': 0, 'errors': 0, 'records': [], 'steps': 0, 'grows': 0}
    visited = set(); master = random.Random(SEED)
    for c in range(N):
        s = master.getrandbits(48); ncoll = [0, 0, 3, 6, 10][c % 5]; dels = [0, 2, 0, 3, 1][c % 5]
        res['cases'] += 1
        try:
            mism, seq, mc = run_case(s, ncoll, dels)
            res['steps'] += mc.cpu.steps; visited |= mc.cpu.visited; res['grows'] += mc.grows
        except Stop as e:
            res['errors'] += 1; res['records'].append({'case': c, 'seed': s, 'error': str(e)}); continue
        if mism:
            res['mismatch'] += 1; res['records'].append({'case': c, 'seed': s, 'mismatch': mism[:20], 'seq': repr(seq)})
    cov = {}
    for f, lo, hi in (('rollback', 0x1e8d350, 0x1e8d9e0), ('acct_arm', 0x1e8d4b7, 0x1e8d617), ('flags_rule', 0x1e8d398, 0x1e8d404),
                      ('acct_lookup', 0x1e7bd20, 0x1e7be34), ('slot_lookup', 0x1e852c0, 0x1e853e0)):
        tot = [a for a in prog.ins if lo <= a < hi]
        cov[f] = [len([a for a in tot if a in visited]), len(tot)]
    res['coverage'] = cov
    json.dump(res, open(OUT, 'w'), indent=1, default=str)
    print(FAULT, hex(FEATURES), 'cases', res['cases'], 'mismatch', res['mismatch'], 'errors', res['errors'], 'steps', res['steps'], 'grows', res['grows'], cov)
