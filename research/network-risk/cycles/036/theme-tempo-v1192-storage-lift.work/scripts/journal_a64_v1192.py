"""PORTED TO v1.19.2 aarch64 by cycle 36 port_journal_a64.py (addresses relocated)."""
"""Runs the storage, transient storage and journal routines of the shipped tempo v1.19.1 aarch64 binary in
the cycle 28 a64emu model (extended here), and compares PoolManager-shaped sequences with pyevm.py.

Routines run from their own disassembly (nothing from the release is executed on a CPU or loaded):
  0x1d975ac  State::tstore host routine (hashbrown entry, inlined insert/erase, journal push)
  0x1d97914  transient map entry() probe          0x1dc85d4  52 byte key hash (rapidhash style)
  0x1d97448  State::tload host routine            0x1d98170  State::rollback (journal pop loop)
  0x1d98608  transient map insert (rollback arm)  0x1d9883c  transient map remove (rollback arm)
  SSTORE handler 0x3b563d4: the StorageWarmed push segment 0x3b571a4-0x3b57200 and the write and
  StorageChange push segment 0x3b57200-0x3b572b8.
Modelled in Python (said so in the results): the account map lookup 0x1d89598 and the storage slot map lookup
0x1d915f4 (both hashbrown get_mut over foldhash; here a dict from address and key to a slot record placed in
model memory with the binary's layout: original at +0, current at +0x20, is_warm at +0x40), the Vec grow
routines (never reached: capacity is preallocated; reaching them raises), and the account load before a
slot is first touched (the slot record is created with original = current = the backing value, as
into_slot_inner does, evm2 crates/evm2/src/evm/state/storage.rs:197-235). The transient map is the real
hashbrown table, built in model memory and driven only by the lifted code.

usage: python3 -I journal_a64.py <bin> <build dir> <out.json> [fault] [hash=real|const] [seed]
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
sys.path.insert(1, '/home/user/v4-core/research/network-risk/cycles/030/theme-tempo-binary-storage-journal.work/scripts')
from a64emu import Prog, Mem, CPU as _CPU, Stop, M64, lanes, pack

BIN, BUILD, OUT = sys.argv[1:4]
FAULT = sys.argv[4] if len(sys.argv) > 4 else 'none'
HASH = sys.argv[5] if len(sys.argv) > 5 else 'real'
SEED = int(sys.argv[6]) if len(sys.argv) > 6 else 2026113001
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


FILES = ['a64v2_1db106c.s', 'a64v2_1db13d4.s', 'a64v2_1de8338.s', 'a64v2_1db0f08.s', 'a64v2_1db1c30.s',
         'a64v2_1db20c8.s', 'a64v2_1db22fc.s', 'a64v2_3b0a918.s']
fb = open(BIN, 'rb').read()
prog = Prog([open(os.path.join(BUILD, f)).read() for f in FILES])

# ---- planted faults (Task 3); each is one or two replaced instructions, or a harness-level rewrite
FAULTS = {
    # rollback undoes one entry too few: the checkpoint index is taken as journal_len + 1
    'cp_plus1': {0x1db1c58: ('add', ['x21', 'x1', '#0x1'])},
    # rollback undoes one entry too many
    'cp_minus1': {0x1db1c58: ('sub', ['x21', 'x1', '#0x1'])},
    # a transient entry is always restored by removing the slot (restore to zero)
    'tr_zero': {0x1db1e40: ('b', ['0x1db1f64'])},
    # the StorageChange arm is skipped (one entry kind not undone)
    'skip_storage': {0x1db1d28: ('cbnz', ['x8', '0x1db1cd0'])},
    # the TransientStorageChange arm is skipped
    'skip_transient': {0x1db1e20: ('b', ['0x1db1cd0'])},
    # the StorageWarmed arm is skipped (changes warmth, so gas, and no value: expected to give no value mismatch)
    'skip_warm': {0x1db1e1c: ('b.ne', ['0x1db1cd0'])},
    # SSTORE writes but records no StorageChange entry when the value changes
    'sstore_nojournal': {0x3b0b794: ('b', ['0x3b0b7fc'])},
    # SSTORE journals the new value as the previous one
    'sstore_prev_new': {0x3b0b7bc: ('ldr', ['q1', '[x27]']), 0x3b0b7c4: ('ldp', ['q0', 'q3', '[x27]'])},
}
faults = {}
for a, rep in FAULTS.get(FAULT, {}).items():
    faults[a] = (lambda cpu, mn, ops, rep=rep: rep)
FORWARD = FAULT == 'forward'   # harness level: rollback walks entries oldest first
if FAULT not in FAULTS and FAULT not in ('none', 'forward'):
    raise SystemExit('unknown fault')

# ---- memory map
EVM = 0x10000000; STATE = EVM + 0xe8
JBUF, JCAP = 0x20000000, 8192
TBL, NB = 0x30000000, 1024            # transient table: buckets then ctrl bytes
CTRL = TBL + NB * 88
SLOTS = 0x40000000
ACCT = 0x50000000
STACK, STK = 0x70000000, 0x20000
SECRET = 0x5eb6000
ARGS = 0x60000000


class Machine:
    def __init__(self):
        self.m = Mem(fb, 0, 0x187c5c8 + 0x440c9a0)
        self.m.add(EVM, 0x1000); self.m.add(JBUF, 0x78 * JCAP); self.m.add(TBL, NB * 88 + NB + 16)
        self.m.add(SLOTS, 0x100000); self.m.add(ACCT, 0x100000); self.m.add(STACK, STK)
        self.m.add(SECRET, 0x1000); self.m.add(ARGS, 0x1000)
        rnd = random.Random(SEED)
        for i in range(0, 0x80, 8): self.m.write(SECRET + 0xb80 + i, 8, rnd.getrandbits(64))
        for i in range(NB + 8): self.m.write(CTRL + i, 1, 0xff)
        w = self.m.write
        w(STATE + 0x20, 8, JCAP); w(STATE + 0x28, 8, JBUF); w(STATE + 0x30, 8, 0)      # journal Vec
        w(STATE + 0x40, 8, 0x8); w(STATE + 0x48, 8, 0)                                   # logs Vec, empty
        w(STATE + 0x200, 8, CTRL); w(STATE + 0x208, 8, NB - 1); w(STATE + 0x210, 8, NB * 7 // 8)
        w(STATE + 0x218, 8, 0); w(STATE + 0x220, 8, rnd.getrandbits(64))
        self.accounts = {}   # address -> account record address (modelled map)
        self.slots = {}      # (address, key) -> slot record address (modelled map)
        self.backing = {}    # (address, key) -> committed value
        self.nslot = 0
        ext = {0x1da32a8: self.x_account, 0x1dab0b4: self.x_slot}
        for a in (0x1d53594, 0x1d5d0c0, 0x5c989f0, 0x5c98990, 0x1d533bc, 0x19fff88, 0x1ca2b2c, 0x188e2b0):
            ext[a] = self.x_never(a)
        if HASH == 'const':
            ext[0x1de8338] = self.x_consthash
        self.cpu = CPU(prog, self.m, externs=ext, faults=faults)

    def x_never(self, a):
        def f(cpu): raise Stop('extern %x reached' % a)
        return f

    def x_consthash(self, cpu):
        cpu.x[0] = 0x0123456789abcdef  # every transient key falls in one probe chain with the same tag

    def rd_addr(self, p):
        return self.m.read(p, 16) | (self.m.read(p + 16, 4) << 128)

    def x_account(self, cpu):
        a = self.rd_addr(cpu.x[1])
        cpu.x[0] = self.accounts.get(a, 0)

    def x_slot(self, cpu):
        acct = cpu.x[0] - 0xc0
        a = [k for k, v in self.accounts.items() if v == acct]
        key = self.m.read(cpu.x[1], 32)
        cpu.x[0] = self.slots.get((a[0], key), 0) if a else 0

    # ---- helpers
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

    def put_word(self, p, v):
        for i in range(4): self.m.write(p + 8 * i, 8, (v >> (64 * i)) & M64)

    def get_word(self, p):
        return sum(self.m.read(p + 8 * i, 8) << (64 * i) for i in range(4))

    def put_addr(self, p, a):
        self.m.write(p, 16, a & ((1 << 128) - 1)); self.m.write(p + 16, 4, a >> 128)

    def jlen(self): return self.m.read(STATE + 0x30, 8)

    # ---- the opcodes
    def tstore(self, addr, key, val):
        self.put_addr(ARGS, addr); self.put_word(ARGS + 0x40, key); self.put_word(ARGS + 0x80, val)
        self.call(0x1db106c, [STATE, ARGS, ARGS + 0x40, ARGS + 0x80])

    def tload(self, addr, key):
        self.put_addr(ARGS, addr); self.put_word(ARGS + 0x40, key)
        self.call(0x1db0f08, [ARGS + 0x100, STATE, ARGS, ARGS + 0x40])
        return self.get_word(ARGS + 0x100)

    def slot(self, addr, key):
        """The overlay record that the account and slot lookup would produce on first access."""
        if addr not in self.accounts:
            self.accounts[addr] = ACCT + 0x1000 * len(self.accounts)
        k = (addr, key)
        if k not in self.slots:
            p = SLOTS + 0x50 * self.nslot; self.nslot += 1
            v = self.backing.get(key, 0)
            self.put_word(p, v); self.put_word(p + 0x20, v); self.m.write(p + 0x40, 1, 0)
            self.slots[k] = p
        return self.slots[k]

    def sload(self, addr, key):
        p = self.slot(addr, key)
        if not self.m.read(p + 0x40, 1):
            self.sstore_warm(addr, key, p)
        return self.get_word(p + 0x20)   # SLoad.value = slot.current() (evm/mod.rs:2041)

    def frame_regs(self, addr, key, p):
        sp = STACK + STK - 0x2000
        self.put_word(sp + 0x4e0, key)
        self.m.write(sp + 0x60, 16, addr & ((1 << 128) - 1)); self.m.write(sp + 0x70, 4, addr >> 128)
        return sp

    def sstore_warm(self, addr, key, p):
        sp = self.frame_regs(addr, key, p)
        self.cpu.x = [0] * 32
        regs = {31: sp, 21: p, 26: EVM, 28: 0, 22: ARGS + 0x80 + 0x40}
        self.put_word(ARGS + 0x80, self.get_word(p + 0x20))
        # run the StorageWarmed segment only: stop where the write segment would start
        self.call(0x3b0b6e8, [], stop=0x3b0b744, regs=regs)

    def sstore(self, addr, key, val):
        p = self.slot(addr, key)
        if not self.m.read(p + 0x40, 1):
            self.sstore_warm(addr, key, p)
        sp = self.frame_regs(addr, key, p)
        self.put_word(ARGS + 0x80, val)
        regs = {31: sp, 21: p, 26: EVM, 28: EVM, 22: ARGS + 0x80 + 0x40}
        self.call(0x3b0b744, [], stop=0x3b0b7fc, regs=regs)

    def rollback(self, cp):
        if FORWARD:
            # rewrite the journal so the shipped loop, which pops from the end, meets the oldest entry first
            n = self.jlen()
            ents = [self.m.read(JBUF + 0x78 * i, 0x78) for i in range(cp, n)]
            for i, e in zip(range(cp, n), reversed(ents)): self.m.write(JBUF + 0x78 * i, 0x78, e)
        features = 1 << 14
        self.call(0x1db1c30, [STATE, cp, 0, features])


# ---- reference: pyevm.py frames (World.snapshot and restore around a reverting CALL)
import pyevm as PE
from evm import assemble


def nreads(ops):
    return sum(1 if op[0] in ('sl', 'tl') else nreads(op[2]) if op[0] == 'frame' else 0 for op in ops)


PMADDR = 0x33620f62c5b9b2086dd6b62f4a297a9f30347029


def ref_run(seq, backing):
    """Runs the sequence as bytecode in pyevm.py: each nested frame is a DELEGATECALL into code that works
    on the same account's storage and transient storage, and ends with RETURN or REVERT of the words it
    read; the parent copies them from return data, so reads made inside a reverted frame are kept."""
    contracts = {}; counter = [0]

    def gen(ops, revert):
        p = []; i = 0
        for op in ops:
            k = op[0]
            if k == 'ss': p += [('PUSHN', 32, op[2]), ('PUSHN', 32, op[1]), 'SSTORE']
            elif k == 'ts': p += [('PUSHN', 32, op[2]), ('PUSHN', 32, op[1]), 'TSTORE']
            elif k in ('sl', 'tl'):
                p += [('PUSHN', 32, op[1]), 'SLOAD' if k == 'sl' else 'TLOAD', ('PUSH', 32 * i), 'MSTORE']; i += 1
            elif k == 'frame':
                counter[0] += 1; addr = 0x1000 + counter[0]
                contracts[addr] = gen(op[2], op[1])
                p += [('PUSH', 0), ('PUSH', 0), ('PUSH', 0), ('PUSH', 0), ('PUSHN', 20, addr), 'GAS', 'DELEGATECALL', 'POP',
                      'RETURNDATASIZE', ('PUSH', 0), ('PUSH', 32 * i), 'RETURNDATACOPY']
                i += nreads(op[2])
        p += [('PUSH', 32 * i), ('PUSH', 0), 'REVERT' if revert else 'RETURN']
        return assemble(p)
    top = gen(seq, False)
    codes = {PMADDR: top}; codes.update(contracts)
    w = PE.World(codes)
    for k, v in backing.items(): w.storage[(PMADDR, k)] = v
    ok, ret = w.call(0xcafe, PMADDR, 0, b'', False, 0)
    assert ok
    reads = [int.from_bytes(ret[j:j + 32], 'big') for j in range(0, len(ret), 32)]
    return reads, {k: v for (a, k), v in w.storage.items() if a == PMADDR and v}, {k: v for (a, k), v in w.transient.items() if a == PMADDR and v}


def model_run(seq, backing, addr):
    mc = Machine(); mc.backing = dict(backing); reads = []

    def run(ops):
        for op in ops:
            k = op[0]
            if k == 'ss': mc.sstore(addr, op[1], op[2])
            elif k == 'ts': mc.tstore(addr, op[1], op[2])
            elif k == 'sl': reads.append(mc.sload(addr, op[1]))
            elif k == 'tl': reads.append(mc.tload(addr, op[1]))
            elif k == 'frame':
                cp = mc.jlen()
                run(op[2])
                if op[1]: mc.rollback(cp)
    run(seq)
    return reads, mc


def model_full(seq, backing):
    reads, mc = model_run(seq, backing, PMADDR)
    stor = {k: mc.get_word(p + 0x20) for (a, k), p in mc.slots.items()}
    for k, v in backing.items(): stor.setdefault(k, v)
    keys = set()
    def walk(ops):
        for op in ops:
            if op[0] in ('ts', 'tl'): keys.add(op[1])
            if op[0] == 'frame': walk(op[2])
    walk(seq)
    tr = {k: mc.tload(PMADDR, k) for k in keys}
    return reads, {k: v for k, v in stor.items() if v}, {k: v for k, v in tr.items() if v}, mc


# ---- PoolManager shaped slots (the layout of src/: pools mapping at slot 6, Pool.State fields)
from evm import keccak
def kw(*xs): return int.from_bytes(keccak(b''.join((x & M).to_bytes(32, 'big') for x in xs)), 'big')
POOLID = kw(0xC0FFEE01, 0xC0FFEE02, 3000, 60, 0)
STATE_SLOT = kw(POOLID, 6)
SLOT0, FG0, FG1, LIQ = STATE_SLOT, STATE_SLOT + 1, STATE_SLOT + 2, STATE_SLOT + 3
TICK = kw((-887220) & M, STATE_SLOT + 4)     # ticks mapping, word 0 of Tick.Info
NZDC = 0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b
UNLOCKED = 0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23
D0 = kw(0xd21fe001, 0xC0FFEE01); D1 = kw(0xd21fe001, 0xC0FFEE02)
SQ = 79228162514264337593543950336
S0v = SQ | ((-1 & 0xffffff) << 160) | (3000 << 208)


def named_sequences():
    neg = lambda x: x & M
    seqs = {}
    seqs['task_storage'] = ([('ss', SLOT0, S0v), ('ss', LIQ, 10 ** 18), ('ss', TICK, 5 * 10 ** 17),
                             ('sl', SLOT0), ('sl', LIQ), ('sl', TICK),
                             ('frame', True, [('ss', SLOT0, S0v + 7), ('ss', LIQ, 2 * 10 ** 18), ('sl', SLOT0), ('sl', LIQ)]),
                             ('sl', SLOT0), ('sl', LIQ), ('sl', TICK)], {})
    seqs['task_transient'] = ([('ts', UNLOCKED, 1), ('ts', D0, neg(-5)), ('ts', D1, 7), ('ts', NZDC, 2),
                               ('frame', True, [('ts', D0, 0), ('ts', NZDC, 1), ('tl', D0), ('tl', NZDC)]),
                               ('tl', D0), ('tl', D1), ('tl', NZDC), ('tl', UNLOCKED)], {})
    seqs['nested_revert_in_revert'] = ([('ss', LIQ, 1), ('ts', D0, 9),
                                        ('frame', True, [('ss', LIQ, 2), ('ts', D0, 10),
                                                         ('frame', True, [('ss', LIQ, 3), ('ts', D0, 11), ('sl', LIQ), ('tl', D0)]),
                                                         ('sl', LIQ), ('tl', D0), ('ss', LIQ, 4), ('ts', D0, 12)]),
                                        ('sl', LIQ), ('tl', D0)], {LIQ: 77})
    seqs['ok_inside_revert'] = ([('ss', SLOT0, 1), ('frame', True, [('frame', False, [('ss', SLOT0, 2), ('ts', D1, 5)]),
                                                                   ('sl', SLOT0), ('tl', D1)]), ('sl', SLOT0), ('tl', D1)], {})
    seqs['same_value_write'] = ([('sl', LIQ), ('ss', LIQ, 500), ('frame', True, [('ss', LIQ, 500), ('ss', LIQ, 501), ('ss', LIQ, 500)]),
                                 ('sl', LIQ), ('frame', True, [('ss', LIQ, 500)]), ('sl', LIQ),
                                 ('ts', D0, 3), ('frame', True, [('ts', D0, 3), ('ts', D0, 4), ('ts', D0, 3)]), ('tl', D0)], {LIQ: 500})
    seqs['restore_not_zero'] = ([('ts', D0, neg(-123)), ('ts', D1, 456),
                                 ('frame', True, [('ts', D0, 0), ('ts', D1, 0), ('ts', D0, 9), ('tl', D0), ('tl', D1)]),
                                 ('tl', D0), ('tl', D1), ('ss', FG0, 0), ('frame', True, [('ss', FG0, 0), ('ss', FG1, 3)]),
                                 ('sl', FG0), ('sl', FG1)], {FG0: 11, FG1: 12})
    seqs['zero_nonzero_zero'] = ([('frame', True, [('ts', NZDC, 1), ('ts', NZDC, 0), ('ts', NZDC, 2)]), ('tl', NZDC),
                                  ('ts', NZDC, 1), ('frame', False, [('ts', NZDC, 0)]), ('tl', NZDC),
                                  ('frame', True, [('ts', NZDC, 5)]), ('tl', NZDC)], {})
    return seqs


def random_sequences(n, rnd):
    skeys = [SLOT0, LIQ, TICK, FG0, FG1]
    tkeys = [D0, D1, NZDC, UNLOCKED, kw(0xd21fe002, 0xC0FFEE01), kw(0xC0FFEE01, 0xd21fe001)]
    vals = [0, 1, 2, M, M - 4, 10 ** 18, S0v]
    out = []
    def ops(depth):
        r = []
        for _ in range(rnd.randint(1, 7)):
            c = rnd.random()
            if c < 0.25: r.append(('ss', rnd.choice(skeys), rnd.choice(vals)))
            elif c < 0.5: r.append(('ts', rnd.choice(tkeys), rnd.choice(vals)))
            elif c < 0.62: r.append(('sl', rnd.choice(skeys)))
            elif c < 0.74: r.append(('tl', rnd.choice(tkeys)))
            elif depth < 4: r.append(('frame', rnd.random() < 0.6, ops(depth + 1)))
        return r
    for i in range(n):
        backing = {k: rnd.choice(vals) for k in skeys if rnd.random() < 0.5}
        out.append(('rand%d' % i, ops(0) + [('sl', k) for k in skeys] + [('tl', k) for k in tkeys], backing))
    return out


if __name__ == '__main__':
    rnd = random.Random(SEED)
    cases = [(k, s, b) for k, (s, b) in named_sequences().items()] + random_sequences(int(os.environ.get('NRAND', '300')), rnd)
    res = {'fault': FAULT, 'hash': HASH, 'seed': SEED, 'cases': 0, 'mismatch': 0, 'errors': 0, 'records': [], 'steps': 0}
    visited = set()
    for name, seq, backing in cases:
        res['cases'] += 1
        try:
            rr, rs, rt = ref_run(seq, backing)
            mr, ms, mt, mc = model_full(seq, backing)
            res['steps'] += mc.cpu.steps; visited |= mc.cpu.visited
        except Stop as e:
            res['errors'] += 1; res['records'].append({'case': name, 'error': str(e), 'seq': repr(seq)}); continue
        if (rr, rs, rt) != (mr, ms, mt):
            res['mismatch'] += 1
            res['records'].append({'case': name, 'seq': repr(seq), 'backing': {hex(k): hex(v) for k, v in backing.items()},
                                   'ref': [rr, {hex(k): v for k, v in rs.items()}, {hex(k): v for k, v in rt.items()}],
                                   'model': [mr, {hex(k): v for k, v in ms.items()}, {hex(k): v for k, v in mt.items()}]})
    # journal shape checks on the entries the lifted writers leave (layout read by the lifted rollback)
    mc = Machine(); mc.backing = {LIQ: 500}
    shape = {}
    def ent(i):
        b = mc.m.read(JBUF + 0x78 * i, 0x78).to_bytes(0x78, 'little')
        return b
    mc.sload(PMADDR, LIQ); shape['first_sload_entries'] = mc.jlen()
    e = ent(0); shape['warm_entry_tag'] = int.from_bytes(e[0:8], 'little'); shape['warm_entry_key_ok'] = int.from_bytes(e[8:40], 'little') == LIQ
    n0 = mc.jlen(); mc.sstore(PMADDR, LIQ, 500); shape['same_value_sstore_new_entries'] = mc.jlen() - n0
    mc.sstore(PMADDR, LIQ, 501); e = ent(mc.jlen() - 1)
    shape['change_entry_tag'] = int.from_bytes(e[0:8], 'little'); shape['change_entry_key_ok'] = int.from_bytes(e[8:40], 'little') == LIQ
    shape['change_entry_previous'] = int.from_bytes(e[40:72], 'little')
    shape['change_entry_address_ok'] = int.from_bytes(e[72:92], 'little') == PMADDR
    n0 = mc.jlen(); mc.tstore(PMADDR, D0, 0); shape['tstore_zero_on_empty_entries'] = mc.jlen() - n0
    mc.tstore(PMADDR, D0, 5); e = ent(mc.jlen() - 1)
    shape['tstore_new_tag'] = [int.from_bytes(e[0:8], 'little'), int.from_bytes(e[8:16], 'little')]
    mc.tstore(PMADDR, D0, 6); e = ent(mc.jlen() - 1)
    shape['tstore_change_tag'] = [int.from_bytes(e[0:8], 'little'), int.from_bytes(e[8:16], 'little')]
    shape['tstore_change_previous'] = int.from_bytes(e[16:48], 'little')
    n0 = mc.jlen(); mc.tstore(PMADDR, D0, 6); shape['tstore_same_value_entries'] = mc.jlen() - n0
    shape['transient_items_after'] = mc.m.read(STATE + 0x218, 8)
    mc.tstore(PMADDR, D0, 0); shape['transient_items_after_zero'] = mc.m.read(STATE + 0x218, 8)
    res['shape'] = shape
    cov = {}
    for f, lo, hi in (('tstore_host', 0x1db106c, 0x1db13d4), ('rollback', 0x1db1c30, 0x1db20c8), ('tr_insert', 0x1db20c8, 0x1db22fc),
                      ('tr_remove', 0x1db22fc, 0x1db24dc), ('tload_host', 0x1db0f08, 0x1db106c), ('entry', 0x1db13d4, 0x1db1534),
                      ('sstore_segments', 0x3b0b6e8, 0x3b0b7fc)):
        tot = [a for a in prog.ins if lo <= a < hi]
        cov[f] = [len([a for a in tot if a in visited]), len(tot)]
    res['coverage'] = cov
    json.dump(res, open(OUT, 'w'), indent=1, default=str)
    print(FAULT, HASH, 'cases', res['cases'], 'mismatch', res['mismatch'], 'errors', res['errors'], 'steps', res['steps'], cov)
