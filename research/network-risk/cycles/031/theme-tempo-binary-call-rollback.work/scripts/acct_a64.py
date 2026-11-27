"""Cycle 31, theme-tempo-binary-call-rollback, Task 2 (L-1213) and Task 5 faults, aarch64.

Runs the shipped tempo v1.19.1 aarch64 State::rollback 0x1d98170 with its AccountChange arm
(0x1d9826c-0x1d98354 and the not-found arm 0x1d98444-0x1d984a0), the StorageChange, StorageWarmed and
TransientStorageChange arms, the account map lookup 0x1d89598 and the slot map lookup 0x1d915f4, on real
hashbrown tables (ctrl bytes, mirrored tail group, 0x110 byte account buckets, 0x68 byte slot buckets)
built in model memory. No dict stands in for a lookup: every record pointer the harness uses, and every
pointer the rollback uses, comes from the lifted lookups. The SSTORE journal segments, State::tstore and
State::tload are the cycle 30 lifts (same addresses).

Modelled in Python (stated in the results): the table insert and the rehash on growth (hashbrown
find_insert_slot and resize, with the hash transcribed from the lifted lookup; a wrong transcription
makes lifted lookups miss and shows as a mismatch), the AccountChange writer (AccountHandle::record_change
clones present and flags, Drop pushes the 0x78 byte entry: previous at +0, address at +0x60, flags at
+0x74), the account and slot load into the overlay (unjournaled), and the outline atomic
__aarch64_ldadd8_rel 0x5c66c30 (fetch-add on [x1], returns the old value).

Nothing from the release is executed on a CPU or loaded; the disassembly text is interpreted.

usage: python3 -I acct_a64.py <bin> <c30 build dir> <c31 build dir> <out.json> [fault] [seed] [features]
"""
import json, os, random, sys
C30 = '/home/user/v4-core/research/network-risk/cycles/030/theme-tempo-binary-storage-journal.work/scripts'
sys.path.insert(0, C30)
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from a64emu import Prog, Mem, CPU as _CPU, Stop, M64, lanes, pack

BIN, BUILD30, BUILD31, OUT = sys.argv[1:5]
FAULT = sys.argv[5] if len(sys.argv) > 5 else 'none'
SEED = int(sys.argv[6]) if len(sys.argv) > 6 else 2026112731
FEATURES = int(sys.argv[7], 0) if len(sys.argv) > 7 else (1 << 14)
M = (1 << 256) - 1


class CPU(_CPU):
    def i_rev64(self, o):
        w, n = self._vw(o[0]); assert w == 8
        b = lanes(self.vget(o[1]), 8, n); out = []
        for i in range(0, n, 8): out += list(reversed(b[i:i + 8]))
        self.vset(o[0], pack(out, 8))

    def i_ext(self, o):
        w, n = self._vw(o[0]); assert w == 8
        k = int(o[3].lstrip('#'), 0)
        cat = self.vget(o[1]) | (self.vget(o[2]) << (8 * n))
        self.vset(o[0], (cat >> (8 * k)) & ((1 << (8 * n)) - 1))

    def i_rev(self, o):
        w = 64 if o[0].startswith('x') else 32
        v = self.rr(o[1]) & ((1 << w) - 1)
        self.wr(o[0], int.from_bytes(v.to_bytes(w // 8, 'little'), 'big'))

    def i_cmlt(self, o):
        w, n = self._vw(o[0])
        self.vset(o[0], pack([((1 << w) - 1) if x >> (w - 1) else 0 for x in lanes(self.vget(o[1]), w, n)], w))

    def i_dmb(self, o): pass


FILES30 = ['a64_tstore_host.s', 'a64_0x1d97914.s', 'a64_0x1dc85d4.s', 'a64_0x1d97448.s', 'a64_rollback.s',
           'a64_0x1d98608.s', 'a64_0x1d9883c.s', 'a64_sstore.s', 'a64_accounts_get.s', 'a64_slots_get.s']
fb = open(BIN, 'rb').read()
prog = Prog([open(os.path.join(BUILD30, f)).read() for f in FILES30])

# planted faults (Task 5): replaced instructions in the in-memory program only
FAULTS = {
    # balance restored from the wrong journal field: bytes 0x40..0x60 of present restored from entry+0x20
    'wrong_field': {0x1d982ac: ('ldp', ['q0', 'q1', '[x27, #0x20]'])},
    # the 16+16 bytes at present+0x20..0x40 (part of balance, code hash or nonce) are not written back
    'skip_part': {0x1d98348: ('nop', [])},
    # the whole present value is not written back (skipped balance and nonce undo)
    'skip_present': {0x1d98338: ('nop', []), 0x1d98340: ('nop', []), 0x1d98348: ('nop', [])},
    # the flags byte keeps the current value instead of the journaled one
    'skip_flags': {0x1d98208: ('nop', [])},
    # the precompile-3 touch rule inverted: every account keeps TOUCHED, address 3 does not
    'touch_inverted': {0x1d981f4: ('csel', ['w8', 'w8', 'wzr', 'ne'])},
    # account lookup gives up after the first probe group without a match
    'acct_probe_short': {0x1d8965c: ('b', ['0x1d89688'])},
    # slot lookup gives up after the first probe group without a match
    'slot_probe_short': {0x1d916bc: ('b', ['0x1d916e8'])},
    # account lookup ignores the last four address bytes
    'acct_key_short': {0x1d8963c: ('ccmp', ['x0', 'x0', '#0x0', 'eq'])},
}
faults = {a: (lambda cpu, mn, ops, rep=rep: rep) for a, rep in FAULTS.get(FAULT, {}).items()}
HARNESS_FAULTS = ('commit_on_revert', 'none')
if FAULT not in FAULTS and FAULT not in HARNESS_FAULTS:
    raise SystemExit('unknown fault')

EVM = 0x10000000; STATE = EVM + 0xe8
ACCTMAP = STATE + 0x1d8
JBUF, JCAP = 0x20000000, 8192
TBL, NB = 0x30000000, 1024
CTRL = TBL + NB * 88
STACK, STK = 0x70000000, 0x20000
SECRET = 0x5e84000
ARGS = 0x60000000
HEAP, HEAPSZ = 0x80000000, 0x4000000
ARCS = 0x50000000

ABUCK, SBUCK = 0x110, 0x68


def ab(a):
    return a.to_bytes(20, 'big')
REC = 0x18             # account record starts at bucket + 0x18; slot record at bucket + 0x20
PRES, SMAP, FLAGS = 0x60, 0xc0, 0xf0
WARM, TOUCHED, DESTROYED, CREATED = 1, 2, 8, 16
# AccountInfo inside Option<AccountInfo> (0x60 bytes). Offsets +0 (tag 0 code None, 1 code Some, 2 None),
# +8 code Arc and +0x58 extension Arc are read from the drop paths of the arm. The order of balance,
# code hash and nonce inside +0x10..+0x58 was not read; the harness names +0x10 balance, +0x30 code hash,
# +0x50 nonce, and every check compares all 96 bytes, so the naming does not matter for the result.
OB, OH, ON = 0x10, 0x30, 0x50


class Machine:
    def __init__(self, seed):
        self.m = Mem(fb, 0, 0x18742d8 + 0x43e2ed0)
        for lo, sz in ((EVM, 0x1000), (JBUF, 0x78 * JCAP), (TBL, NB * 88 + NB + 16), (STACK, STK), (SECRET, 0x1000),
                       (ARGS, 0x1000), (HEAP, HEAPSZ), (ARCS, 0x10000)):
            self.m.add(lo, sz)
        self.rnd = random.Random(seed)
        for i in range(0, 0x80, 8): self.m.write(SECRET + 0x200 + i, 8, self.rnd.getrandbits(64))
        self.S = self.m.read(SECRET + 0x210, 8)
        for i in range(NB + 8): self.m.write(CTRL + i, 1, 0xff)
        w = self.m.write
        w(STATE + 0x20, 8, JCAP); w(STATE + 0x28, 8, JBUF); w(STATE + 0x30, 8, 0)
        w(STATE + 0x40, 8, 0x8); w(STATE + 0x48, 8, 0)
        w(STATE + 0x200, 8, CTRL); w(STATE + 0x208, 8, NB - 1); w(STATE + 0x210, 8, NB * 7 // 8)
        w(STATE + 0x218, 8, 0); w(STATE + 0x220, 8, self.rnd.getrandbits(64))
        self.hp = HEAP
        self.grows = 0
        self.narc = 0
        self.new_table(ACCTMAP, 8, ABUCK, self.rnd.getrandbits(64))
        ext = {0x5c66c30: self.x_ldadd}
        for a in (0x1d397f8, 0x1d43324, 0x5c66bd0, 0x1d39620, 0x19e636c, 0x1c89614, 0x1885fc0):
            ext[a] = self.x_never(a)
        self.cpu = CPU(prog, self.m, externs=ext, faults=faults)
        self.backing = {}

    # ---- externs
    def x_never(self, a):
        def f(cpu): raise Stop('extern %x reached' % a)
        return f

    def x_ldadd(self, cpu):
        p = cpu.x[1]; old = self.m.read(p, 8)
        self.m.write(p, 8, (old + cpu.x[0]) & M64); cpu.x[0] = old

    # ---- heap and hashbrown tables (insert and resize modelled; lookups lifted)
    def alloc(self, n):
        p = (self.hp + 15) & ~15; self.hp = p + n
        if self.hp > HEAP + HEAPSZ: raise Stop('heap full')
        return p

    def new_table(self, hdr, nb, bs, seed):
        base = self.alloc(nb * bs + nb + 8); ctrl = base + nb * bs
        for i in range(nb + 8): self.m.write(ctrl + i, 1, 0xff)
        w = self.m.write
        w(hdr, 8, ctrl); w(hdr + 8, 8, nb - 1); w(hdr + 0x10, 8, nb * 7 // 8 if nb >= 8 else nb - 1)
        w(hdr + 0x18, 8, 0); w(hdr + 0x20, 8, seed)

    def h_acct(self, hdr, a):
        k = ab(a) if isinstance(a, int) else a
        k0, k1, k2 = int.from_bytes(k[0:8], 'little'), int.from_bytes(k[8:16], 'little'), int.from_bytes(k[16:20], 'little')
        seed = self.m.read(hdr + 0x20, 8)
        p = (k0 ^ seed) * (self.S ^ k1); x = (p >> 64) ^ (p & M64) ^ k2
        p = x * self.S; return ((p >> 64) ^ (p & M64)) & M64

    def h_slot(self, hdr, key):
        k = [(key >> (64 * i)) & M64 for i in range(4)]
        seed = self.m.read(hdr + 0x20, 8)
        p = (k[0] ^ seed) * (self.S ^ k[1]); x = (p >> 64) ^ (p & M64) ^ k[2]
        p = x * (k[3] ^ self.S); return ((p >> 64) ^ (p & M64)) & M64

    def find_slot(self, ctrl, mask, h):
        pos = h & mask; stride = 0
        while True:
            for b in range(8):
                i = (pos + b) & mask
                if self.m.read(ctrl + i, 1) & 0x80:
                    return i
            stride += 8; pos = (pos + stride) & mask

    def set_ctrl(self, ctrl, mask, i, v):
        self.m.write(ctrl + i, 1, v); self.m.write(ctrl + (((i - 8) & mask) + 8), 1, v)

    def table_insert(self, hdr, bs, h, keybytes, recbytes):
        ctrl = self.m.read(hdr, 8); mask = self.m.read(hdr + 8, 8)
        i = self.find_slot(ctrl, mask, h)
        was_empty = self.m.read(ctrl + i, 1) == 0xff
        if was_empty and self.m.read(hdr + 0x10, 8) == 0:
            self.grow(hdr, bs)
            return self.table_insert(hdr, bs, h, keybytes, recbytes)
        self.set_ctrl(ctrl, mask, i, h >> 57)
        b = ctrl - (i + 1) * bs
        self.m.write(b, len(keybytes), int.from_bytes(keybytes, 'little'))
        self.m.write(b + len(keybytes), len(recbytes), int.from_bytes(recbytes, 'little'))
        if was_empty: self.m.write(hdr + 0x10, 8, self.m.read(hdr + 0x10, 8) - 1)
        self.m.write(hdr + 0x18, 8, self.m.read(hdr + 0x18, 8) + 1)
        return b

    def table_delete(self, hdr, bs, b):
        """Marks the bucket DELETED (0x80), as hashbrown erase does when the group is full; used only to
        put tombstones into probe chains."""
        ctrl = self.m.read(hdr, 8); mask = self.m.read(hdr + 8, 8)
        i = (ctrl - b) // bs - 1
        self.set_ctrl(ctrl, mask, i, 0x80)
        self.m.write(hdr + 0x18, 8, self.m.read(hdr + 0x18, 8) - 1)

    def buckets(self, hdr, bs):
        ctrl = self.m.read(hdr, 8); mask = self.m.read(hdr + 8, 8)
        return [ctrl - (i + 1) * bs for i in range(mask + 1) if not (self.m.read(ctrl + i, 1) & 0x80)]

    def grow(self, hdr, bs):
        self.grows += 1
        old = [self.m.read(b, bs).to_bytes(bs, 'little') for b in self.buckets(hdr, bs)]
        nb = (self.m.read(hdr + 8, 8) + 1) * 2
        seed = self.m.read(hdr + 0x20, 8)
        self.new_table(hdr, nb, bs, seed)
        for raw in old:
            if bs == ABUCK: h = self.h_acct(hdr, raw[:20]); k = raw[:REC]
            else: h = self.h_slot(hdr, int.from_bytes(raw[:32], 'little')); k = raw[:0x20]
            self.table_insert(hdr, bs, h, k, raw[len(k):])

    # ---- lifted lookups
    def call(self, entry, args, stop=0xdead0000, regs=None):
        c = self.cpu
        c.x = [0] * 32; c.v = [0] * 32
        c.x[31] = STACK + STK - 0x2000
        for k, v in (regs or {}).items(): c.x[k] = v & M64
        for i, v in enumerate(args): c.x[i] = v & M64
        c.x[30] = 0xdead0000
        pc = entry; n = 0
        while pc != stop and pc != 0xdead0000:
            pc = c.step(pc); n += 1; c.steps += 1
            if n > 2_000_000: raise Stop('step limit')
        return c.x[0]

    def put_addr(self, p, a):
        # Address is a 20 byte array in big-endian order (alloy Address), so address 3 ends in byte 0x03
        self.m.write(p, 20, int.from_bytes(ab(a), 'little'))

    def put_word(self, p, v):
        for i in range(4): self.m.write(p + 8 * i, 8, (v >> (64 * i)) & M64)

    def get_word(self, p):
        return sum(self.m.read(p + 8 * i, 8) << (64 * i) for i in range(4))

    def lookup_acct(self, a):
        self.put_addr(ARGS + 0x300, a)
        return self.call(0x1d89598, [ACCTMAP, ARGS + 0x300])

    def lookup_slot(self, rec, key):
        self.put_word(ARGS + 0x340, key)
        return self.call(0x1d915f4, [rec + SMAP, ARGS + 0x340])

    # ---- overlay load (modelled, unjournaled) and account records
    def new_arc(self):
        p = ARCS + 0x10 * self.narc; self.narc += 1
        self.m.write(p, 8, 1); self.m.write(p + 8, 8, 0)
        return p

    def info_bytes(self, info):
        """info: None or dict(balance, nonce, codehash, code (arc ptr or 0), ext (arc ptr or 0))."""
        b = bytearray(0x60)
        if info is None:
            b[0:8] = (2).to_bytes(8, 'little'); return bytes(b)
        b[0:8] = (1 if info['code'] else 0).to_bytes(8, 'little')
        b[8:16] = info['code'].to_bytes(8, 'little')
        b[OB:OB + 32] = info['balance'].to_bytes(32, 'little')
        b[OH:OH + 32] = info['codehash'].to_bytes(32, 'little')
        b[ON:ON + 8] = info['nonce'].to_bytes(8, 'little')
        b[0x58:0x60] = info['ext'].to_bytes(8, 'little')
        return bytes(b)

    def read_info(self, p):
        tag = self.m.read(p, 8)
        if tag == 2: return None
        return {'balance': self.m.read(p + OB, 32), 'nonce': self.m.read(p + ON, 8), 'codehash': self.m.read(p + OH, 32),
                'code': self.m.read(p + 8, 8) if tag == 1 else 0, 'ext': self.m.read(p + 0x58, 8), 'tag': tag}

    def load_acct(self, a, info):
        rec = self.lookup_acct(a)
        if rec: return rec
        h = self.h_acct(ACCTMAP, a)
        ib = self.info_bytes(info)
        recb = bytearray(0xf8)
        recb[0:0x60] = ib; recb[PRES:PRES + 0x60] = ib
        if info:
            for k in ('code', 'ext'):
                if info[k]: self.m.write(info[k], 8, self.m.read(info[k], 8) + 2)   # original and present each hold one
        b = self.table_insert(ACCTMAP, ABUCK, h, ab(a) + bytes(4), bytes(recb))
        rec = b + REC
        self.new_table(rec + SMAP, 8, SBUCK, self.rnd.getrandbits(64))
        r2 = self.lookup_acct(a)
        if r2 != rec: raise Stop('lifted account lookup did not find the inserted account %x' % a)
        return rec

    def slot_rec(self, a, key):
        rec = self.lookup_acct(a)
        if not rec: raise Stop('account not loaded')
        p = self.lookup_slot(rec, key)
        if p: return p
        v = self.backing.get((a, key), 0)
        recb = v.to_bytes(32, 'little') + v.to_bytes(32, 'little') + bytes(8)
        self.table_insert(rec + SMAP, SBUCK, self.h_slot(rec + SMAP, key), key.to_bytes(32, 'little'), recb)
        p = self.lookup_slot(rec, key)
        if not p: raise Stop('lifted slot lookup did not find the inserted slot')
        return p

    # ---- AccountChange writer (modelled record_change + drop)
    def jlen(self): return self.m.read(STATE + 0x30, 8)

    def push_entry(self, raw):
        n = self.jlen()
        if n >= JCAP: raise Stop('journal full')
        self.m.write(JBUF + 0x78 * n, 0x78, int.from_bytes(raw, 'little')); self.m.write(STATE + 0x30, 8, n + 1)

    def mutate(self, a, fn):
        rec = self.lookup_acct(a)
        prev = self.m.read(rec + PRES, 0x60).to_bytes(0x60, 'little')
        flags = self.m.read(rec + FLAGS, 1)
        info = self.read_info(rec + PRES)
        if info:
            for k in ('code', 'ext'):
                if info[k]: self.m.write(info[k], 8, self.m.read(info[k], 8) + 1)   # clone held by the entry
        newinfo, newflags = fn(info, flags)
        if newinfo is not None and info is not None:
            for k in ('code', 'ext'):
                if newinfo[k] != info[k]:
                    if info[k]: self.m.write(info[k], 8, self.m.read(info[k], 8) - 1)
        self.m.write(rec + PRES, 0x60, int.from_bytes(self.info_bytes(newinfo), 'little'))
        self.m.write(rec + FLAGS, 1, newflags)
        self.push_entry(prev + ab(a) + bytes([flags]) + bytes(3))

    # ---- the cycle 30 lifted opcode routines (same register setup)
    def tstore(self, addr, key, val):
        self.put_addr(ARGS, addr); self.put_word(ARGS + 0x40, key); self.put_word(ARGS + 0x80, val)
        self.call(0x1d975ac, [STATE, ARGS, ARGS + 0x40, ARGS + 0x80])

    def tload(self, addr, key):
        self.put_addr(ARGS, addr); self.put_word(ARGS + 0x40, key)
        self.call(0x1d97448, [ARGS + 0x100, STATE, ARGS, ARGS + 0x40])
        return self.get_word(ARGS + 0x100)

    def frame_regs(self, addr, key):
        sp = STACK + STK - 0x2000
        self.put_word(sp + 0x4e0, key)
        self.m.write(sp + 0x60, 20, int.from_bytes(ab(addr), 'little'))
        return sp

    def sstore_warm(self, addr, key, p):
        sp = self.frame_regs(addr, key)
        regs = {31: sp, 21: p, 26: EVM, 28: 0, 22: ARGS + 0x80 + 0x40}
        self.put_word(ARGS + 0x80, self.get_word(p + 0x20))
        self.call(0x3b571a4, [], stop=0x3b57200, regs=regs)

    def sload(self, addr, key):
        p = self.slot_rec(addr, key)
        if not self.m.read(p + 0x40, 1): self.sstore_warm(addr, key, p)
        return self.get_word(p + 0x20)

    def sstore(self, addr, key, val):
        p = self.slot_rec(addr, key)
        if not self.m.read(p + 0x40, 1): self.sstore_warm(addr, key, p)
        p = self.slot_rec(addr, key)
        sp = self.frame_regs(addr, key)
        self.put_word(ARGS + 0x80, val)
        regs = {31: sp, 21: p, 26: EVM, 28: EVM, 22: ARGS + 0x80 + 0x40}
        self.call(0x3b57200, [], stop=0x3b572b8, regs=regs)

    def rollback(self, cp):
        self.call(0x1d98170, [STATE, cp, 0, FEATURES])


# ---------------------------------------------------------------- reference (snapshot semantics)
class Ref:
    """pyevm.py World semantics (whole-state snapshot before a frame, restore on failure), extended with
    nonces, code and the evm2 flag rule (state/mod.rs:891-901)."""
    def __init__(self):
        self.acct = {}    # addr -> [info or None, flags]
        self.stor = {}; self.tr = {}

    def snap(self):
        return ({a: [dict(v[0]) if v[0] else None, v[1]] for a, v in self.acct.items()}, dict(self.stor), dict(self.tr))

    def restore(self, s):
        cur = self.acct
        self.acct, self.stor, self.tr = s
        self.acct = {a: v for a, v in self.acct.items()}
        for a, v in cur.items():
            if a not in self.acct:
                # loaded during the frame: the overlay entry stays with its pre-frame value (loads are unjournaled);
                # the harness records the pre-frame value at load time
                self.acct[a] = [dict(self.loaded[a][0]) if self.loaded[a][0] else None, self.loaded[a][1]]
            if FEATURES & (1 << 14) and a == 3:
                self.acct[a][1] = (self.acct[a][1] & ~TOUCHED) | (v[1] & TOUCHED)


ADDRS = [0x33620f62c5b9b2086dd6b62f4a297a9f30347029, 0xcafe, 3]


def gen_case(rnd, colliding, extra_keys=()):
    """Ops: ('val', a, b, v) native value a->b with evm2 transfer rules (state/mod.rs:749-780),
    ('nonce', a), ('create', a), ('code', a), ('touch', a), ('ss', a, k, v), ('ts', a, k, v), ('sl', a, k),
    ('tl', a, k), ('frame', revert, ops)."""
    pool = list(ADDRS) + colliding[:]
    keys = [rnd.getrandbits(256) for _ in range(3)] + [0, 1, 6, M] + list(extra_keys)
    vals = [0, 1, 2, 10 ** 18, M, M - 3, rnd.getrandbits(256)]
    fresh = [rnd.getrandbits(160) for _ in range(12)]

    def ops(d):
        r = []
        for _ in range(rnd.randint(1, 8)):
            c = rnd.random(); a = rnd.choice(pool)
            if c < 0.18: r.append(('val', a, rnd.choice(pool + fresh[:2]), rnd.choice([0, 1, 5, 10 ** 18, 3 * 10 ** 18])))
            elif c < 0.26: r.append(('nonce', a))
            elif c < 0.32 and fresh: f = fresh.pop(); pool.append(f); r.append(('create', f))
            elif c < 0.36: r.append(('code', a))
            elif c < 0.40: r.append(('touch', a))
            elif c < 0.55: r.append(('ss', a, rnd.choice(keys), rnd.choice(vals)))
            elif c < 0.68: r.append(('ts', a, rnd.choice(keys), rnd.choice(vals)))
            elif c < 0.74: r.append(('sl', a, rnd.choice(keys)))
            elif c < 0.78: r.append(('tl', a, rnd.choice(keys)))
            elif d < 4: r.append(('frame', rnd.random() < 0.65, ops(d + 1)))
        return r
    return ops(0), keys


def colliding_addrs(mc, n, rnd):
    """Addresses whose hash has the same h2 byte and the same low five bits as ADDRS[0], so they start
    their probe at the same bucket in every table of up to 32 buckets, found with the transcribed hash."""
    hdr = ACCTMAP
    h0 = mc.h_acct(hdr, ADDRS[0]); out = []
    while len(out) < n:
        a = rnd.getrandbits(160); h = mc.h_acct(hdr, a)
        if (h >> 57) == (h0 >> 57) and (h & 31) == (h0 & 31): out.append(a)
    return out


def run_case(seed, ncoll, deletes):
    rnd = random.Random(seed)
    mc = Machine(seed)
    ref = Ref(); ref.loaded = {}
    coll = colliding_addrs(mc, ncoll, rnd) if ncoll else []
    init = {}
    order = ADDRS + coll
    infos = {}
    for a in order:
        infos[a] = {'balance': rnd.choice([0, 7, 2 * 10 ** 18, M]), 'nonce': rnd.choice([0, 1, 2 ** 64 - 1, 5]),
                    'codehash': rnd.getrandbits(256), 'code': mc.new_arc() if rnd.random() < 0.7 else 0,
                    'ext': mc.new_arc() if rnd.random() < 0.3 else 0}
        mc.load_acct(a, infos[a])
        ref.acct[a] = [dict(infos[a]), 0]; ref.loaded[a] = (dict(infos[a]), 0)
    # slot keys that share the h2 byte and probe group of key 6 in the first account's slot table
    ekeys = []
    if ncoll:
        hdr = mc.lookup_acct(ADDRS[0]) + SMAP; h0 = mc.h_slot(hdr, 6)
        while len(ekeys) < ncoll:
            k = rnd.getrandbits(256); h = mc.h_slot(hdr, k)
            if (h >> 57) == (h0 >> 57) and (h & 31) == (h0 & 31): ekeys.append(k)
    seq, keys = gen_case(rnd, coll, ekeys)
    for a in order:
        for k in keys:
            if rnd.random() < 0.4:
                mc.backing[(a, k)] = rnd.getrandbits(256)
    if ncoll:
        for k in keys: mc.slot_rec(ADDRS[0], k)   # unjournaled loads fill the slot table and its probe chains
    # tombstones in the probe chain: insert and delete scratch accounts that land in the same group
    if deletes:
        for a in colliding_addrs(mc, deletes, rnd):
            rec = mc.load_acct(a, None); mc.table_delete(ACCTMAP, ABUCK, rec - REC)
    reads_m, reads_r = [], []
    # second reference: the pyevm.py World (tools/opdiff/pyevm.py:41-81) driven through its own state
    # dictionaries, with its snapshot and restore around every frame (pyevm.py:57-58 and 62-80) and its
    # value rule (pyevm.py:63-65)
    import pyevm as PE
    W = PE.World({}, {a: infos[a]['balance'] for a in order})
    for (a, k), v in mc.backing.items(): W.storage[(a, k)] = v
    Wsat = set()

    def ensure(a):
        if mc.lookup_acct(a) == 0:
            mc.load_acct(a, None)
        if a not in ref.acct:
            ref.acct[a] = [None, 0]; ref.loaded[a] = (None, 0)

    def r_info(a): return ref.acct[a][0]

    def do(op, depth):
        k = op[0]
        if k == 'val':
            _, a, b, v = op; ensure(a); ensure(b)
            if v and W.balances.get(a, 0) >= v and a != b:
                W.balances[a] -= v; W.balances[b] = W.balances.get(b, 0) + v
                if W.balances[b] > M: Wsat.add(b)   # pyevm does not saturate at 2^256 - 1, evm2 does
            # evm2 State::transfer, state/mod.rs:749-780; the model decides from its own balances and the
            # reference from its own, so a model that kept a reverted debit shows as a mismatch
            def bal_m(x):
                i = mc.read_info(mc.lookup_acct(x) + PRES); return i['balance'] if i else 0
            def bal_r(x):
                i = ref.acct[x][0]; return i['balance'] if i else 0
            EMPTYH = 0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470
            def sub(i, f):
                i = dict(i) if i else {'balance': 0, 'nonce': 0, 'codehash': EMPTYH, 'code': 0, 'ext': 0}
                i['balance'] -= v; return i, f | TOUCHED
            def add(i, f):
                i = dict(i) if i else {'balance': 0, 'nonce': 0, 'codehash': EMPTYH, 'code': 0, 'ext': 0}
                i['balance'] = min(i['balance'] + v, M); return i, f | TOUCHED
            for side in ('m', 'r'):
                bal = bal_m(a) if side == 'm' else bal_r(a)
                if v == 0: steps = [(b, lambda i, f: (i, f | TOUCHED))]
                elif bal < v: steps = []
                elif a == b: steps = [(a, lambda i, f: (i, f | TOUCHED))]
                else: steps = [(a, sub), (b, add)]
                for x, fn in steps:
                    if side == 'm': mc.mutate(x, fn)
                    else:
                        ri, rf = fn(ref.acct[x][0], ref.acct[x][1]); ref.acct[x] = [ri, rf]
            return True
        if k == 'nonce':
            a = op[1]; ensure(a)
            def bump(i, f):
                i = dict(i) if i else {'balance': 0, 'nonce': 0, 'codehash': 0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470, 'code': 0, 'ext': 0}
                if i['nonce'] < 2 ** 64 - 1: i['nonce'] += 1
                return i, f | TOUCHED
            mc.mutate(a, bump); ri, rf = bump(ref.acct[a][0], ref.acct[a][1]); ref.acct[a] = [ri, rf]
        elif k == 'create':
            a = op[1]; ensure(a); arc = mc.new_arc()
            def cr(i, f, arc=arc):
                return {'balance': (i or {}).get('balance', 0), 'nonce': 1, 'codehash': 0x1234 + arc, 'code': arc, 'ext': 0}, f | CREATED | TOUCHED | WARM
            mc.mutate(a, cr); ri, rf = cr(ref.acct[a][0], ref.acct[a][1]); ref.acct[a] = [ri, rf]
            mc.m.write(arc, 8, mc.m.read(arc, 8) + 1)
        elif k == 'code':
            a = op[1]; ensure(a); arc = mc.new_arc()
            def sc(i, f, arc=arc):
                i = dict(i) if i else {'balance': 0, 'nonce': 0, 'codehash': 0, 'code': 0, 'ext': 0}
                i['code'] = arc; i['codehash'] = 0xabcd0000 + arc; return i, f | TOUCHED
            mc.mutate(a, sc); ri, rf = sc(ref.acct[a][0], ref.acct[a][1]); ref.acct[a] = [ri, rf]
            mc.m.write(arc, 8, mc.m.read(arc, 8) + 1)
        elif k == 'touch':
            a = op[1]; ensure(a)
            mc.mutate(a, lambda i, f: (i, f | TOUCHED | WARM)); ref.acct[a][1] |= TOUCHED | WARM
        elif k == 'ss':
            _, a, key, v = op; ensure(a); mc.sstore(a, key, v); ref.stor[(a, key)] = v; W.storage[(a, key)] = v
        elif k == 'ts':
            _, a, key, v = op; ensure(a); mc.tstore(a, key, v); ref.tr[(a, key)] = v; W.transient[(a, key)] = v
        elif k == 'sl':
            _, a, key = op; ensure(a); reads_m.append(mc.sload(a, key)); reads_r.append(ref.stor.get((a, key), mc.backing.get((a, key), 0)))
        elif k == 'tl':
            _, a, key = op; ensure(a); reads_m.append(mc.tload(a, key)); reads_r.append(ref.tr.get((a, key), 0))
        elif k == 'frame':
            cp = mc.jlen(); s = ref.snap(); ws = W.snapshot()
            for o in op[2]: do(o, depth + 1)
            if op[1]:
                if FAULT != 'commit_on_revert': mc.rollback(cp)
                ref.restore(s); W.restore(ws)
        return True
    for op in seq: do(op, 0)
    # final comparison: every loaded account, every slot touched, every transient key
    mism = []
    for a in ref.acct:
        rec = mc.lookup_acct(a)
        if not rec: mism.append(('account missing', hex(a))); continue
        mi = mc.read_info(rec + PRES)
        if mi: mi.pop('tag')
        ri = ref.acct[a][0]
        if (mi is None) != (ri is None) or (mi and ri and any(mi[x] != ri[x] for x in ('balance', 'nonce', 'codehash', 'code', 'ext'))):
            mism.append(('present', hex(a), repr(mi), repr(ri)))
        mf = mc.m.read(rec + FLAGS, 1)
        if mf != ref.acct[a][1]: mism.append(('flags', hex(a), mf, ref.acct[a][1]))
    for a in ref.acct:
        for key in keys:
            rec = mc.lookup_acct(a)
            p = mc.lookup_slot(rec, key) if rec else 0
            mv = mc.get_word(p + 0x20) if p else mc.backing.get((a, key), 0)
            rv = ref.stor.get((a, key), mc.backing.get((a, key), 0))
            if mv != rv: mism.append(('storage', hex(a), hex(key), hex(mv), hex(rv)))
            mt = mc.tload(a, key); rt = ref.tr.get((a, key), 0)
            if mt != rt: mism.append(('transient', hex(a), hex(key), hex(mt), hex(rt)))
    if reads_m != reads_r: mism.append(('reads', [hex(x) for x in reads_m], [hex(x) for x in reads_r]))
    # pyevm World comparison, skipping accounts whose pyevm balance once passed 2^256 - 1 (pyevm does not
    # saturate, evm2 does, state/mod.rs:775; those accounts are still compared with the evm2-rule reference)
    for a in ref.acct:
        rec = mc.lookup_acct(a); mi = mc.read_info(rec + PRES)
        mb = mi['balance'] if mi else 0; wb = W.balances.get(a, 0)
        if a not in Wsat and mb != wb: mism.append(('pyevm balance', hex(a), mb, wb))
        for key in keys:
            p = mc.lookup_slot(rec, key)
            mv = mc.get_word(p + 0x20) if p else mc.backing.get((a, key), 0)
            if mv != W.storage.get((a, key), 0): mism.append(('pyevm storage', hex(a), hex(key)))
            if mc.tload(a, key) != W.transient.get((a, key), 0): mism.append(('pyevm transient', hex(a), hex(key)))
    # Arc reference counts: each arc's count equals the references held by records (original and present)
    # and by journal entries still on the journal, plus the one the harness holds
    held = {}
    def add_ref(p):
        if p: held[p] = held.get(p, 0) + 1
    for b in mc.buckets(ACCTMAP, ABUCK):
        for off in (REC, REC + PRES):
            i = mc.read_info(b + off)
            if i: add_ref(i['code']); add_ref(i['ext'])
    for j in range(mc.jlen()):
        e = JBUF + 0x78 * j
        tag = mc.m.read(e, 8)
        if tag in (0, 1):
            i = mc.read_info(e); add_ref(i['code']); add_ref(i['ext'])
    for n in range(mc.narc):
        p = ARCS + 0x10 * n
        if mc.m.read(p, 8) != held.get(p, 0) + 1:
            mism.append(('arc count', hex(p), mc.m.read(p, 8), held.get(p, 0) + 1))
    return mism, seq, mc


if __name__ == '__main__':
    N = int(os.environ.get('NCASES', '600'))
    res = {'fault': FAULT, 'seed': SEED, 'features': FEATURES, 'cases': 0, 'mismatch': 0, 'errors': 0, 'records': [],
           'steps': 0, 'grows': 0, 'acct_change_entries_undone': 0}
    visited = set()
    master = random.Random(SEED)
    for c in range(N):
        s = master.getrandbits(48)
        ncoll = [0, 0, 3, 6, 10][c % 5]; dels = [0, 2, 0, 3, 1][c % 5]
        res['cases'] += 1
        try:
            mism, seq, mc = run_case(s, ncoll, dels)
            res['steps'] += mc.cpu.steps; visited |= mc.cpu.visited; res['grows'] += mc.grows
        except Stop as e:
            res['errors'] += 1; res['records'].append({'case': c, 'seed': s, 'error': str(e)}); continue
        if mism:
            res['mismatch'] += 1
            res['records'].append({'case': c, 'seed': s, 'ncoll': ncoll, 'deletes': dels, 'mismatch': mism[:20], 'seq': repr(seq)})
    # the not-found arm: an AccountChange entry whose address is not in the account map (the overlay never
    # removes an account inside a transaction, so this arm only frees the entry's Arcs)
    nf = {'cases': 0, 'bad': []}
    for c in range(50):
        mc = Machine(master.getrandbits(48))
        for a in ADDRS: mc.load_acct(a, {'balance': 1, 'nonce': 1, 'codehash': 1, 'code': mc.new_arc(), 'ext': 0})
        before = {a: mc.m.read(mc.lookup_acct(a), 0xf8) for a in ADDRS}
        ghost = master.getrandbits(160)
        arcs = [mc.new_arc() if master.random() < 0.6 else 0 for _ in range(2)]
        tag = master.choice([0, 1, 2]) if arcs[0] else master.choice([0, 2])
        info = None if tag == 2 else {'balance': 5, 'nonce': 2, 'codehash': 3, 'code': arcs[0] if tag == 1 else 0, 'ext': arcs[1]}
        for p in arcs:
            if p: mc.m.write(p, 8, 2)   # harness plus the entry
        mc.push_entry(mc.info_bytes(info) + ab(ghost) + bytes([3]) + bytes(3))
        try:
            mc.rollback(0)
        except Stop as e:
            nf['bad'].append(str(e)); continue
        visited |= mc.cpu.visited
        nf['cases'] += 1
        if mc.lookup_acct(ghost) != 0: nf['bad'].append('ghost inserted')
        if any(mc.m.read(mc.lookup_acct(a), 0xf8) != before[a] for a in ADDRS): nf['bad'].append('other account changed')
        if mc.jlen() != 0: nf['bad'].append('journal not popped')
        for i, p in enumerate(arcs):
            exp = 1 if (p and (i == 1 or tag == 1) and tag != 2) else 2 if p else None
            if p and mc.m.read(p, 8) != exp: nf['bad'].append('arc %d count %d expected %d tag %d' % (i, mc.m.read(p, 8), exp, tag))
    res['notfound'] = nf
    cov = {}
    for f, lo, hi in (('rollback', 0x1d98170, 0x1d98608), ('acct_arm', 0x1d9826c, 0x1d98358), ('acct_arm_notfound', 0x1d98444, 0x1d984a4),
                      ('flags_rule', 0x1d981c0, 0x1d9820c), ('acct_lookup', 0x1d89598, 0x1d8969c), ('slot_lookup', 0x1d915f4, 0x1d916fc)):
        tot = [a for a in prog.ins if lo <= a < hi]
        cov[f] = [len([a for a in tot if a in visited]), len(tot)]
        res.setdefault('unvisited', {})[f] = [hex(a) for a in sorted(tot) if a not in visited]
    res['coverage'] = cov
    json.dump(res, open(OUT, 'w'), indent=1, default=str)
    print(FAULT, hex(FEATURES), 'cases', res['cases'], 'mismatch', res['mismatch'], 'errors', res['errors'], 'steps', res['steps'], 'grows', res['grows'], cov)
