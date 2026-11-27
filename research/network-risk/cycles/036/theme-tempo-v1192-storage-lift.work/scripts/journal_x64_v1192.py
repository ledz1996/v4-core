"""PORTED TO v1.19.2 by cycle 36 port_journal.py (addresses relocated). x86_64 counterpart of journal_a64.py: runs the storage, transient storage and journal routines of the
shipped tempo v1.19.1 x86_64 binary (the build behind rpc.mainnet.tempo.xyz) in the cycle 28 x86emu2 model
with the cycle 29 extensions, on the same sequences, faults and pyevm.py reference.

Routines run from their own disassembly (nothing from the release is executed or loaded):
  0x1e8c450  State::tstore host routine           0x1e8c860  transient map entry() probe
  0x1ec9530  52 byte key hash                     0x1e8c2b0  State::tload host routine
  0x1e8d350  State::rollback (jump table 0x65fe30) 0x1e8d9e0 transient insert  0x1e8dcc0 transient remove
  SSTORE handler 0x42a0d20: StorageWarmed push segment 0x42a1f54-0x42a1fea and write and StorageChange
  push segment 0x42a1fea-0x42a2148. bcmp is reached through the GLOB_DAT slot 0x6c84590 and modelled.
Modelled in Python, as in journal_a64.py: account map 0x1e7bd20 and slot map 0x1e852c0 lookups (dicts),
Vec grow and rehash (never reached).

usage: python3 -I journal_x64.py <bin> <build dir> <out.json> [fault] [hash=real|const] [seed]
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/029/theme-tempo-binary-keccak-transient.work/scripts')
from x86emu2 import CPU2, Prog, Stop, rewrite_rip, M64

BIN, BUILD, OUT = sys.argv[1:4]
FAULT = sys.argv[4] if len(sys.argv) > 4 else 'none'
HASH = sys.argv[5] if len(sys.argv) > 5 else 'real'
SEED = int(sys.argv[6]) if len(sys.argv) > 6 else 2026113011
M = (1 << 256) - 1
TEXT_LO, TEXT_HI, TEXT_DELTA = 0x18a4800, 0x18a4800 + 0x5250a10, 0x1000


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

    def i_shufpd(self, o, pc, n):
        d = self.opnd(o[0]); a = self._xget(d); b = self._xget(self.opnd(o[1])); k = int(o[2], 16)
        lo = (a >> 64) if k & 1 else (a & M64)
        hi = (b >> 64) if k & 2 else (b & M64)
        self._xput(d, lo | (hi << 64))

    def i_bswap(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]
        self.put(d, int.from_bytes(self.get(d).to_bytes(b // 8, 'little'), 'big'))

    def i_rol(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]
        c = self._shcount(self.opnd(o[1]) if len(o) > 1 else ('i', 1, None), b)
        if c == 0: return
        x = self.get(d); r = ((x << c) | (x >> (b - c))) & ((1 << b) - 1)
        self.cf = r & 1; self.put(d, r)

    def i_ror(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]
        c = self._shcount(self.opnd(o[1]) if len(o) > 1 else ('i', 1, None), b)
        if c == 0: return
        x = self.get(d); r = ((x >> c) | (x << (b - c))) & ((1 << b) - 1)
        self.cf = (r >> (b - 1)) & 1; self.put(d, r)


FILES = ['x64v2_1e8feb0.s', 'x64v2_1e902c0.s', 'x64v2_1ed1b70.s', 'x64v2_1e8fd10.s', 'x64v2_1e90db0.s',
         'x64v2_1e91440.s', 'x64v2_1e91720.s', 'x64v2_42b3290.s']
fb = open(BIN, 'rb').read()
prog = Prog(rewrite_rip('\n'.join(open(os.path.join(BUILD, f)).read() for f in FILES)))

FAULTS = {
    'cp_plus1': {0x1e90dc9: 'lea    r13,[rsi+0x1]'},
    'cp_minus1': {0x1e90dc9: 'lea    r13,[rsi-0x1]'},
    'tr_zero': {0x1e910d2: 'jmp    1e91278'},
    'skip_storage': {0x1e911c0: 'jmp    1e90e70'},
    'skip_transient': {0x1e91080: 'jmp    1e90e70'},
    'skip_warm': {0x1e91180: 'jmp    1e90e70'},
    'sstore_nojournal': {0x42b461c: 'jmp    42b46b8'},
    'sstore_prev_new': {0x42b467e: 'movaps xmm0,XMMWORD PTR [r14]', 0x42b4686: 'movdqa xmm1,XMMWORD PTR [r14+0x10]'},
}
faults = dict(FAULTS.get(FAULT, {}))
FORWARD = FAULT == 'forward'
if FAULT not in FAULTS and FAULT not in ('none', 'forward'):
    raise SystemExit('unknown fault')

EVM = 0x10000000; STATE = EVM + 0xe8
JBUF, JCAP = 0x20000000, 8192
TBL, NB = 0x30000000, 1024
CTRL = TBL + NB * 88
SLOTS = 0x40000000
ACCT = 0x50000000
SECRET = 0x6cf7b38
ARGS = 0x60000000
SP0 = 0x7ffff0000000


class MemView:
    def __init__(self, cpu): self.c = cpu
    def read(self, a, n): return self.c.read(a, n)
    def write(self, a, n, v): self.c.write(a, n, v)


def ext_bcmp(cpu):
    a, b, n = cpu.r['rdi'], cpu.r['rsi'], cpu.r['rdx']
    cpu.r['rax'] = 0 if all(cpu.read(a + i, 1) == cpu.read(b + i, 1) for i in range(n)) else 1


class Machine:
    def __init__(self):
        self.accounts = {}; self.slots = {}; self.backing = {}; self.nslot = 0
        ext = {0x1e7fa90: self.x_account, 0x1e88d20: self.x_slot, 0xb0b0b0: ext_bcmp}
        for a in (0x1e1d410, 0x1e28820, 0x1e1d290, 0x1a42110, 0x6af3ab0, 0x1e1dee0, 0x1e1df00, 0x1d4e9f3, 0x4af5b20):
            ext[a] = self.x_never(a)
        if HASH == 'const':
            ext[0x1ed1b70] = self.x_consthash
        self.cpu = CPU(prog, fb, 0x18a3800, externs=ext, got={0x6cc16d0: ext_bcmp}, faults=faults)
        self.m = MemView(self.cpu)
        self.m.write(0x6cc16d0, 8, 0xb0b0b0)   # GLOB_DAT slot of bcmp, resolved to the modelled bcmp
        rnd = random.Random(SEED)
        for i in range(0, 0x40, 8): self.m.write(SECRET + i, 8, rnd.getrandbits(64))
        for i in range(NB + 16): self.m.write(CTRL + i, 1, 0xff)
        w = self.m.write
        w(STATE + 0x20, 8, JCAP); w(STATE + 0x28, 8, JBUF); w(STATE + 0x30, 8, 0)
        w(STATE + 0x40, 8, 0x8); w(STATE + 0x48, 8, 0)
        w(STATE + 0x200, 8, CTRL); w(STATE + 0x208, 8, NB - 1); w(STATE + 0x210, 8, NB * 7 // 8)
        w(STATE + 0x218, 8, 0); w(STATE + 0x220, 8, rnd.getrandbits(64))

    def x_never(self, a):
        def f(cpu): raise Stop('extern %x reached' % a)
        return f

    def x_consthash(self, cpu):
        cpu.r['rax'] = 0x0123456789abcdef

    def rd_addr(self, p):
        return self.m.read(p, 16) | (self.m.read(p + 16, 4) << 128)

    def x_account(self, cpu):
        cpu.r['rax'] = self.accounts.get(self.rd_addr(cpu.r['rsi']), 0)

    def x_slot(self, cpu):
        acct = cpu.r['rdi'] - 0xc0
        a = [k for k, v in self.accounts.items() if v == acct]
        key = self.m.read(cpu.r['rsi'], 32)
        cpu.r['rax'] = self.slots.get((a[0], key), 0) if a else 0

    def run(self, entry, args, stop=None, regs=None, stack=None):
        c = self.cpu
        for k in list(c.r): c.r[k] = 0
        c.y = [0] * 16
        names = ['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9']
        for k, v in zip(names, args): c.r[k] = v & M64
        for k, v in (regs or {}).items(): c.r[k] = v & M64
        rsp = SP0 - 0x8
        if stop is None:
            c.write(rsp, 8, 0xdead0000); c.r['rsp'] = rsp; stop = 0xdead0000
        else:
            c.r['rsp'] = SP0 - 0x10000
        for off, (n, v) in (stack or {}).items(): c.write(c.r['rsp'] + off, n, v)
        pc = entry; k = 0
        while pc != stop:
            pc = c.step(pc); k += 1
            if k > 3_000_000: raise Stop('step limit')
        return c.r['rax']

    def call(self, entry, args): return self.run(entry, args)

    def put_word(self, p, v):
        for i in range(4): self.m.write(p + 8 * i, 8, (v >> (64 * i)) & M64)

    def get_word(self, p):
        return sum(self.m.read(p + 8 * i, 8) << (64 * i) for i in range(4))

    def put_addr(self, p, a):
        self.m.write(p, 16, a & ((1 << 128) - 1)); self.m.write(p + 16, 4, a >> 128)

    def jlen(self): return self.m.read(STATE + 0x30, 8)

    def tstore(self, addr, key, val):
        self.put_addr(ARGS, addr); self.put_word(ARGS + 0x40, key); self.put_word(ARGS + 0x80, val)
        self.call(0x1e8feb0, [STATE, ARGS, ARGS + 0x40, ARGS + 0x80])

    def tload(self, addr, key):
        self.put_addr(ARGS, addr); self.put_word(ARGS + 0x40, key)
        self.call(0x1e8fd10, [ARGS + 0x100, STATE, ARGS, ARGS + 0x40])
        return self.get_word(ARGS + 0x100)

    def slot(self, addr, key):
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
        return self.get_word(p + 0x20)

    def frame_stack(self, addr, key, valptr):
        st = {0x18: (8, EVM), 0x8: (8, valptr + 0x40), 0x0: (8, 0), 0x40: (8, 0),
              0x20: (16, addr & ((1 << 128) - 1)), 0x30: (4, addr >> 128)}
        for i in range(4): st[0x290 + 8 * i] = (8, (key >> (64 * i)) & M64)
        return st

    def sstore_warm(self, addr, key, p):
        self.put_word(ARGS + 0x80, self.get_word(p + 0x20))
        self.run(0x42b44c4, [], stop=0x42b455a, regs={'r12': p}, stack=self.frame_stack(addr, key, ARGS + 0x80))

    def sstore(self, addr, key, val):
        p = self.slot(addr, key)
        if not self.m.read(p + 0x40, 1):
            self.sstore_warm(addr, key, p)
        self.put_word(ARGS + 0x80, val)
        self.run(0x42b455a, [], stop=0x42b46b8, regs={'r12': p, 'rdi': ARGS + 0x80 + 0x40, 'rbx': 0},
                 stack=self.frame_stack(addr, key, ARGS + 0x80))

    def rollback(self, cp):
        if FORWARD:
            n = self.jlen()
            ents = [self.m.read(JBUF + 0x78 * i, 0x78) for i in range(cp, n)]
            for i, e in zip(range(cp, n), reversed(ents)): self.m.write(JBUF + 0x78 * i, 0x78, e)
        self.call(0x1e90db0, [STATE, cp, 0, 1 << 14])


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
    for f, lo, hi in (('tstore_host', 0x1e8feb0, 0x1e902be), ('rollback', 0x1e90db0, 0x1e9143b), ('tr_insert', 0x1e91440, 0x1e9171a),
                      ('tr_remove', 0x1e91720, 0x1e91934), ('tload_host', 0x1e8fd10, 0x1e8feac), ('entry', 0x1e902c0, 0x1e90474),
                      ('sstore_segments', 0x42b44c4, 0x42b46b8)):
        tot = [a for a in prog.ins if lo <= a < hi and not prog.ins[a].startswith('int3')]
        cov[f] = [len([a for a in tot if a in visited]), len(tot)]
    res['coverage'] = cov
    json.dump(res, open(OUT, 'w'), indent=1, default=str)
    print(FAULT, HASH, 'cases', res['cases'], 'mismatch', res['mismatch'], 'errors', res['errors'], 'steps', res['steps'], cov)
