"""Cycle 36, Tasks 1, 3 (rollback part) and 5 on the v1.19.2 x86_64 binary.

Runs, from the v1.19.2 disassembly (journal_x64_v1192.py, built by port_journal.py from cycle 30's model with every
address relocated by relocate.py), the SSTORE handler's StorageWarmed push and write and StorageChange push segments,
State::rollback with its log truncation and drop loop, and the transient routines, on the PoolManager's slot shapes:
slot0, liquidity, a tick word, a position's liquidity, protocolFeesAccrued[currency] and an ERC-6909 balance, with
every original, current and new value class and frames that revert at depth 1 to 3.

Checks after every step against tools/opdiff/pyevm.py and the evm2 rules:
  reads, final storage and transient storage equal pyevm.py; the original word (+0x00 of the slot entry) still equals
  the value at transaction start; each SSTORE adds exactly one StorageWarmed entry on first touch and one
  StorageChange entry iff the new value differs from the present one; each SLOAD adds one entry on first touch only;
  a rollback leaves the log Vec at the frame's log checkpoint and calls the drop routine once for each later log;
  the surviving log count equals pyevm.py's.
Logs are pushed by this driver into the State log Vec (+0x40 pointer, +0x48 length, 0x50 byte entries, the layout the
lifted rollback reads); the LOG handler itself is not lifted.

usage: python3 -I storage_v1192.py <v1.19.2 bin> <build dir> <out.json> <fault> <hash real|const> <seed> <ncases>
"""
import json, os, random, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
BIN, BUILD, OUT, FAULT, HASH, SEED, NC = sys.argv[1:8]
SEED = int(SEED); NC = int(NC)
sys.argv = [sys.argv[0], BIN, BUILD, OUT, 'none', HASH, str(SEED)]
sys.path.insert(0, HERE)
import journal_x64_v1192 as J
from journal_x64_v1192 import Stop, M64
import pyevm as PE
from evm import assemble, keccak

M = (1 << 256) - 1
PM = J.PMADDR
# v1.19.2 addresses (relocated): SSTORE write segment and rollback StorageChange arm and log truncation
FAULTS = {
    # Task 5 faults, one or two instructions each, in the in-memory copy of the v1.19.2 code
    'credit_on_word': {0x42b4617: 'movups XMMWORD PTR [r12],xmm1'},          # stored word's low half replaced
    'orig_overwritten': {0x42b4604: 'add    r12,0x0'},                         # write lands on the original word
    'change_no_journal': {0x42b461c: 'jmp    42b46b8'},                        # StorageChange entry skipped
    'same_value_entry': {0x42b45fe: 'nop'},                                    # no-change write records an entry
    'prev_is_new': {0x42b467e: 'movaps xmm0,XMMWORD PTR [r14]', 0x42b4686: 'movdqa xmm1,XMMWORD PTR [r14+0x10]'},
    'revert_to_committed': {0x1e911f8: 'movdqu xmm0,XMMWORD PTR [rax]', 0x1e911fd: 'movups xmm1,XMMWORD PTR [rax+0x10]'},
    'log_kept': {0x1e912f3: 'nop'},                                            # log Vec length not truncated
    'log_drop_short': {0x1e912fa: 'nop'},                                     # drop loop runs one time short
}
if FAULT not in FAULTS and FAULT != 'none': raise SystemExit('unknown fault')
J.faults.clear(); J.faults.update(FAULTS.get(FAULT, {}))

_orig_call = J.CPU.i_call
MEMIND = re.compile(r'^QWORD PTR \[(r\w+)\+0x([0-9a-f]+)\]$')


def i_call(self, o, pc, n):
    m = MEMIND.match(o[0])
    if m:
        t = self.read((self.r[m.group(1)] + int(m.group(2), 16)) & M64, 8)
        if t in self.externs:
            self.externs[t](self); return n
        raise Stop('memory indirect call to %x' % t)
    return _orig_call(self, o, pc, n)


J.CPU.i_call = i_call
LOGBUF, VT, DROP = 0x70000000, 0x71000000, 0xc0c0c0


class Machine(J.Machine):
    def __init__(self):
        super().__init__()
        self.dropped = []
        self.cpu.externs[DROP] = self.x_drop
        self.m.write(J.STATE + 0x40, 8, LOGBUF); self.m.write(J.STATE + 0x48, 8, 0)
        self.m.write(VT + 0x20, 8, DROP)
        self.errs = []

    def x_drop(self, cpu): self.dropped.append(cpu.r['rdi'])

    def nlogs(self): return self.m.read(J.STATE + 0x48, 8)

    def log(self, ident):
        n = self.nlogs(); e = LOGBUF + 0x50 * n
        for off in range(0, 0x50, 8): self.m.write(e + off, 8, 0)
        self.m.write(e + 0x18, 8, VT); self.m.write(e + 0x30, 8, ident)
        self.m.write(J.STATE + 0x48, 8, n + 1)

    def rollback2(self, cp, lcp):
        n = self.nlogs(); want = [self.m.read(LOGBUF + 0x50 * i + 0x30, 8) for i in range(lcp, n)]
        self.dropped = []
        self.call(0x1e90db0, [J.STATE, cp, lcp, 1 << 14])
        if self.nlogs() != lcp: self.errs.append('log length %d after rollback to %d' % (self.nlogs(), lcp))
        if sorted(self.dropped) != sorted(want): self.errs.append('dropped %s want %s' % (self.dropped, want))

    def check_orig(self, backing):
        for (a, k), p in self.slots.items():
            if self.get_word(p) != backing.get(k, 0): self.errs.append('original of %x changed' % k)

    def sstore_checked(self, addr, key, val):
        p = self.slot(addr, key); warm = self.m.read(p + 0x40, 1); cur = self.get_word(p + 0x20); n0 = self.jlen()
        self.sstore(addr, key, val)
        want = (0 if warm else 1) + (1 if val != cur else 0)
        if self.jlen() - n0 != want: self.errs.append('sstore %x %x->%x entries %d want %d' % (key, cur, val, self.jlen() - n0, want))

    def sload_checked(self, addr, key):
        p = self.slot(addr, key); warm = self.m.read(p + 0x40, 1); n0 = self.jlen()
        v = self.sload(addr, key)
        if self.jlen() - n0 != (0 if warm else 1): self.errs.append('sload entries')
        return v


def nreads(ops):
    return sum(1 if op[0] in ('sl', 'tl') else nreads(op[2]) if op[0] == 'frame' else 0 for op in ops)


def ref_run(seq, backing):
    contracts = {}; counter = [0]

    def gen(ops, revert):
        p = []; i = 0
        for op in ops:
            k = op[0]
            if k == 'ss': p += [('PUSHN', 32, op[2]), ('PUSHN', 32, op[1]), 'SSTORE']
            elif k == 'ts': p += [('PUSHN', 32, op[2]), ('PUSHN', 32, op[1]), 'TSTORE']
            elif k == 'lg': p += [('PUSHN', 32, op[1]), ('PUSH', 0), ('PUSH', 0), ('RAW', b'\xa1')]
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
    codes = {PM: top}; codes.update(contracts)
    w = PE.World(codes)
    for k, v in backing.items(): w.storage[(PM, k)] = v
    ok, ret = w.call(0xcafe, PM, 0, b'', False, 0)
    assert ok
    reads = [int.from_bytes(ret[j:j + 32], 'big') for j in range(0, len(ret), 32)]
    return (reads, {k: v for (a, k), v in w.storage.items() if a == PM and v},
            {k: v for (a, k), v in w.transient.items() if a == PM and v}, w.logs)


def model_run(seq, backing):
    mc = Machine(); mc.backing = dict(backing); reads = []; lid = [0]

    def run(ops):
        for op in ops:
            k = op[0]
            if k == 'ss': mc.sstore_checked(PM, op[1], op[2])
            elif k == 'ts': mc.tstore(PM, op[1], op[2])
            elif k == 'sl': reads.append(mc.sload_checked(PM, op[1]))
            elif k == 'tl': reads.append(mc.tload(PM, op[1]))
            elif k == 'lg': lid[0] += 1; mc.log(lid[0])
            elif k == 'frame':
                cp, lcp = mc.jlen(), mc.nlogs()
                run(op[2])
                if op[1]: mc.rollback2(cp, lcp)
            mc.check_orig(backing)
    run(seq)
    stor = {k: mc.get_word(p + 0x20) for (a, k), p in mc.slots.items()}
    for k, v in backing.items(): stor.setdefault(k, v)
    keys = set()
    def walk(ops):
        for op in ops:
            if op[0] in ('ts', 'tl'): keys.add(op[1])
            if op[0] == 'frame': walk(op[2])
    walk(seq)
    tr = {k: mc.tload(PM, k) for k in keys}
    return reads, {k: v for k, v in stor.items() if v}, {k: v for k, v in tr.items() if v}, mc.nlogs(), mc


# PoolManager slot shapes (src/PoolManager.sol:93 _pools at slot 6; ProtocolFees.sol:21 protocolFeesAccrued at slot 1;
# ERC6909.sol:17 balanceOf at slot 4; Pool.State fields Pool.sol:83-91; Position.State Position.sol:19-24)
kw = J.kw
C0, C1 = 0xC0FFEE01, 0xC0FFEE02
POOLID = J.POOLID; PS = J.STATE_SLOT
SLOT0, LIQ = PS, PS + 3
TICK_LO = kw((-600) & M, PS + 4); TICK_HI = kw(600, PS + 4)
BITMAP = kw(((-600 // 60) >> 8) & M, PS + 5)
POSKEY = int.from_bytes(keccak(bytes.fromhex('%040x' % 0xd21fe301) + ((-600) & 0xffffff).to_bytes(3, 'big') + (600).to_bytes(3, 'big') + bytes(32)), 'big')
POS = kw(POSKEY, PS + 6)
PFEE = kw(C0, 1)
BAL = kw(C1, kw(0xd21fe301, 4))
SKEYS = {'slot0': SLOT0, 'liquidity': LIQ, 'tickLower': TICK_LO, 'tickUpper': TICK_HI, 'bitmap': BITMAP,
         'position': POS, 'protocolFeesAccrued': PFEE, 'erc6909Balance': BAL}
TKEYS = [J.D0, J.D1, J.NZDC, J.UNLOCKED]


def gen_case(rnd, i):
    keys = list(SKEYS.values())
    backing = {k: rnd.choice([J.S0v, 10 ** 18, 1, M, (1 << 128) - 1 | (((-5) & ((1 << 128) - 1)) << 128)]) for k in keys if rnd.random() < 0.5}
    cur = dict(backing)

    def val(k):
        c = rnd.random(); o = backing.get(k, 0); p = cur.get(k, 0)
        if c < 0.2: v = 0                                    # x -> 0 (or 0 -> 0)
        elif c < 0.4: v = o                                  # restore to original
        elif c < 0.55: v = p                                 # no change
        elif c < 0.75: v = rnd.choice([1, 10 ** 18, J.S0v, M]) # 0 -> x or x -> y
        else: v = rnd.getrandbits(rnd.choice([8, 64, 128, 256]))
        return v

    def ops(depth):
        r = []
        for _ in range(rnd.randint(1, 6)):
            c = rnd.random()
            if c < 0.35:
                k = rnd.choice(keys); v = val(k); r.append(('ss', k, v))
            elif c < 0.45: r.append(('sl', rnd.choice(keys)))
            elif c < 0.55: r.append(('ts', rnd.choice(TKEYS), rnd.choice([0, 1, M, 7])))
            elif c < 0.6: r.append(('tl', rnd.choice(TKEYS)))
            elif c < 0.72: r.append(('lg', 0))
            elif depth < 3: r.append(('frame', rnd.random() < 0.6, ops(depth + 1)))
        return r
    seq = ops(0) + [('sl', k) for k in keys] + [('tl', k) for k in TKEYS]
    return 'rand%d' % i, seq, backing


def named():
    S = SKEYS
    return [
        ('slot0_first_write', [('ss', S['slot0'], J.S0v), ('frame', True, [('ss', S['slot0'], J.S0v + 1), ('lg', 0)]), ('sl', S['slot0']), ('lg', 0)], {}),
        ('tick_init_clear_init', [('ss', S['tickLower'], 10 ** 18), ('ss', S['tickLower'], 0), ('frame', True, [('ss', S['tickLower'], 5), ('lg', 0), ('frame', True, [('ss', S['tickLower'], 0), ('lg', 0)])]), ('sl', S['tickLower']), ('ss', S['tickLower'], 10 ** 18), ('sl', S['tickLower'])], {}),
        ('position_zero_and_back', [('ss', S['position'], 0), ('frame', True, [('ss', S['position'], 10 ** 18), ('frame', False, [('ss', S['position'], 0)]), ('lg', 0)]), ('sl', S['position']), ('ss', S['position'], 10 ** 18)], {S['position']: 10 ** 18}),
        ('protocol_fee_restore', [('ss', S['protocolFeesAccrued'], 99), ('ss', S['protocolFeesAccrued'], 7), ('frame', True, [('ss', S['protocolFeesAccrued'], 0)]), ('sl', S['protocolFeesAccrued'])], {S['protocolFeesAccrued']: 7}),
        ('erc6909_burn_to_zero_reverted_depth3', [('frame', True, [('frame', True, [('frame', True, [('ss', S['erc6909Balance'], 0), ('lg', 0)]), ('lg', 0)]), ('lg', 0)]), ('sl', S['erc6909Balance']), ('lg', 0)], {S['erc6909Balance']: 12345}),
        ('liquidity_no_change', [('ss', S['liquidity'], 77), ('frame', True, [('ss', S['liquidity'], 77)]), ('sl', S['liquidity'])], {S['liquidity']: 77}),
    ]


def main():
    rnd = random.Random(SEED)
    cases = named() + [gen_case(rnd, i) for i in range(NC)]
    res = {'fault': FAULT, 'hash': HASH, 'seed': SEED, 'cases': 0, 'mismatch': 0, 'errors': 0, 'checkFailures': 0, 'records': [],
           'ops': {'ss': 0, 'sl': 0, 'frameRevert': 0, 'frameOk': 0, 'lg': 0, 'maxDepth': 0}, 'steps': 0,
           'classes': {'0->0': 0, '0->x': 0, 'x->0': 0, 'x->y': 0, 'same': 0, 'restore': 0}}
    visited = set()
    for name, seq, backing in cases:
        res['cases'] += 1
        cur = dict(backing)
        def count(ops, d):
            res['ops']['maxDepth'] = max(res['ops']['maxDepth'], d)
            for op in ops:
                if op[0] == 'ss':
                    res['ops']['ss'] += 1; o = backing.get(op[1], 0); p = cur.get(op[1], 0); v = op[2]
                    res['classes']['same' if v == p else 'restore' if v == o else '0->0' if p == 0 and v == 0 else '0->x' if p == 0 else 'x->0' if v == 0 else 'x->y'] += 1
                    cur[op[1]] = v
                elif op[0] in ('sl', 'lg'): res['ops'][op[0]] += 1
                elif op[0] == 'frame':
                    res['ops']['frameRevert' if op[1] else 'frameOk'] += 1; count(op[2], d + 1)
        count(seq, 0)
        try:
            rr = ref_run(seq, backing)
            mr = model_run(seq, backing)
            mc = mr[4]; res['steps'] += mc.cpu.steps; visited |= mc.cpu.visited
        except Stop as e:
            res['errors'] += 1; res['records'].append({'case': name, 'error': str(e), 'seq': repr(seq), 'backing': {hex(k): hex(v) for k, v in backing.items()}}); continue
        except Exception as e:
            res['errors'] += 1; res['records'].append({'case': name, 'error': 'python ' + repr(e), 'seq': repr(seq)}); continue
        same = tuple(rr) == tuple(mr[:4])
        if not same or mc.errs:
            if not same: res['mismatch'] += 1
            if mc.errs: res['checkFailures'] += 1
            res['records'].append({'case': name, 'seq': repr(seq), 'backing': {hex(k): hex(v) for k, v in backing.items()},
                                   'ref': [rr[0], {hex(k): hex(v) for k, v in rr[1].items()}, {hex(k): hex(v) for k, v in rr[2].items()}, rr[3]],
                                   'model': [mr[0], {hex(k): hex(v) for k, v in mr[1].items()}, {hex(k): hex(v) for k, v in mr[2].items()}, mr[3]],
                                   'checks': mc.errs[:20]})
    cov = {}
    for f, lo, hi in (('sstore_segments', 0x42b44c4, 0x42b46b8), ('rollback', 0x1e90db0, 0x1e9143b)):
        tot = [a for a in J.prog.ins if lo <= a < hi and not J.prog.ins[a].startswith('int3')]
        cov[f] = [len([a for a in tot if a in visited]), len(tot)]
    res['coverage'] = cov
    res['caught'] = (res['mismatch'] + res['checkFailures'] + res['errors']) > 0
    json.dump(res, open(OUT, 'w'), indent=1, default=str)
    print(FAULT, HASH, 'cases', res['cases'], 'mismatch', res['mismatch'], 'checkFailures', res['checkFailures'], 'errors', res['errors'],
          'ops', res['ops'], 'classes', res['classes'], 'cov', cov)


main()
