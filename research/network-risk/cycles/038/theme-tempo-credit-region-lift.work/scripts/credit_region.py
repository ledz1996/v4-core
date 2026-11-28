"""Cycle 38, theme-tempo-credit-region-lift, Tasks 1, 2 and 5 on the tempo v1.19.2 x86_64 binary.

Runs the TIP-1060 storage credit region of the SSTORE handler (0x42b3290) from its disassembly in the
cycle 28/29 x86-64 model: entry 0x42b46b8 (the point right after the slot write and its StorageChange
push) to the function exit 0x42b5095, through the credit sload/sstore calls, the transient credit state
calls, the dynamic gas, the EIP-8037 state gas block and the refund call. Nothing from the release is
executed or loaded; objdump text of it is interpreted.

Run from the binary (disassembly interpreted):
  0x42b46b8..0x42b5095 and its out-of-line blocks 0x42b50f1..0x42b5175 (credit region, gas tail, exit)
  0x42b44c4..0x42b455a StorageWarmed push and 0x42b455a..0x42b46b8 write + StorageChange push of the same
           handler, used for the PoolManager slot and, as stand-in for the outlined host copy, for the
           credit slot (cycle 36 segments)
  0x1e8fd10 tload host, 0x1e8feb0 tstore host (credit transient state words on real transient tables)
  0x4b632b9..0x4b633e7 SstoreTransitionFlags block of the outlined host sstore 0x4b62170
  0x2d26f80 sstore_refund
  0x1e90db0 State::rollback (Task 2)
Modelled in Python (named in the output):
  the body of 0x4b83c80 (credit sload: load_account + slot lookup; miss path = database read) and of
  0x4b62170 up to its flag block (slot lookup), replaced by the cycle 36 slot entries and the binary
  segments above; 0x5eb4b90/0x4293810/0x42b5390 (construction and drop of the Fatal error object) as
  stubs that hand back a distinct non-Ok tag; the account and slot map lookups (dicts, as in cycle 36).

usage: python3 -I credit_region.py <bin> <c36 build> <c38 build> <out.json> <fault> <seed> <nrand>
"""
import json, os, random, sys, copy
HERE = os.path.dirname(os.path.abspath(__file__))
BIN, B36, B38, OUT, FAULT, SEED, NR = sys.argv[1:8]
SEED = int(SEED); NR = int(NR)
C36 = '/home/user/v4-core/research/network-risk/cycles/036/theme-tempo-v1192-storage-lift.work/scripts'
sys.path.insert(0, C36)
sys.argv = [sys.argv[0], BIN, B36, OUT, 'none', 'real', str(SEED)]
import journal_x64_v1192 as J
from journal_x64_v1192 import Stop, M64
from x86emu2 import Prog, rewrite_rip

M = (1 << 256) - 1
U64 = (1 << 64) - 1
EXTRA = ['x64_2d26f80.s', 'x64_4b62170.s']
text = '\n'.join(open(os.path.join(B36, f)).read() for f in J.FILES)
text += '\n' + '\n'.join(open(os.path.join(B38, f)).read() for f in EXTRA)
J.prog = Prog(rewrite_rip(text))

FAULTS = {
    # crossing test reads the original word in place of the present word
    'cross_from_original': {0x42b479d: 'movdqu xmm0,XMMWORD PTR [rsp+0x60]', 0x42b47a6: 'movdqu xmm1,XMMWORD PTR [rsp+0x70]'},
    # crossing test reads the new word in place of the present word (credit computed from the new value)
    'cross_from_new': {0x42b479d: 'movdqu xmm0,XMMWORD PTR [rsp+0xa0]', 0x42b47a6: 'movdqu xmm1,XMMWORD PTR [rsp+0xb0]'},
    'mint_wraps': {0x42b4b7b: 'nop'},                                   # saturating add removed
    'cold_credit_free': {0x42b49e6: 'mov    r8d,DWORD PTR [rsp]', 0x42b49ea: 'jmp    42b4a05'},  # cold credit load not charged
    'budget_kept': {0x42b4cc2: 'nop'},                                  # Direct budget not decremented
    'preserve_as_direct': {0x42b4c96: 'cmp    edx,0x3'},               # Preserve handled as Direct
    'refund_pending_kept': {0x1e91080: 'jmp    1e90e70'},               # rollback skips transient arm (pending refund kept)
    'original_from_current': {0x42b4604: 'add    r12,0x0'},             # write lands on the original word
    'credit_no_journal': {0x42b461c: 'jmp    42b46b8'},                 # StorageChange entry skipped
    'clean_update_free': {0x42b4c09: 'cmp    r12b,0x9'},               # clean-update charge never taken
}
if FAULT not in FAULTS and FAULT != 'none': raise SystemExit('unknown fault')
J.faults.clear(); J.faults.update(FAULTS.get(FAULT, {}))

EVM = J.EVM; STATE = J.STATE
IST = 0x58000000            # interpreter context (rbx in the handler)
NEWV = 0x59000000
OUTER_SP = J.SP0 - 0x400000
RET = 0xdead0000
GT = EVM + 0x340            # GasParams table, u32 per GasId (evm2 version/gas_params.rs order)
GID = dict(WarmStorageReadCost=15, SstoreStatic=16, SstoreSetWithoutLoadCost=17, SstoreResetWithoutColdLoadCost=18,
           SstoreClearingSlotRefund=19, CallStipend=21, ColdStorageAdditionalCost=23, ColdStorageCost=24,
           SstoreSetRefund=39, SstoreResetRefund=40, SstoreSetState=42)
GAS_TEMPO = dict(WarmStorageReadCost=100, SstoreStatic=0, SstoreSetWithoutLoadCost=5000, SstoreResetWithoutColdLoadCost=2900,
                 SstoreClearingSlotRefund=4800, CallStipend=2300, ColdStorageAdditionalCost=2000, ColdStorageCost=2100,
                 SstoreSetRefund=4900, SstoreResetRefund=2800, SstoreSetState=0)
GAS_DISTINCT = dict(WarmStorageReadCost=101, SstoreStatic=0, SstoreSetWithoutLoadCost=5003, SstoreResetWithoutColdLoadCost=2907,
                    SstoreClearingSlotRefund=4811, CallStipend=2300, ColdStorageAdditionalCost=2013, ColdStorageCost=2117,
                    SstoreSetRefund=4919, SstoreResetRefund=2833, SstoreSetState=0)
CREDIT_VALUE = 245000
# addresses as the cycle 36 machine stores them: integer whose little-endian bytes are the address bytes
CADDR = int.from_bytes(bytes.fromhex('1060' + '00' * 18), 'little')
PM = J.PMADDR


def addr_word(a):
    return int.from_bytes(a.to_bytes(20, 'little'), 'big')


class Mach(J.Machine):
    def __init__(self, gas_table, spec=0x0e, eip2200=True, eip8037=False):
        super().__init__()
        self.cbacking = {}
        self.dberr = None
        self.acct_warm = set()
        self.calls = []
        c = self.cpu
        c.externs[0x4b83c80] = self.x_csload
        c.externs[0x4b62170] = self.x_csstore
        c.externs[0x5eb4b90] = self.x_fatal_new
        c.externs[0x4293810] = lambda cpu: None
        c.externs[0x42b5390] = self.x_fatal_mode
        c.externs[0x2776cc0] = self.x_never(0x2776cc0)
        for k, v in gas_table.items(): self.m.write(GT + 4 * GID[k], 4, v)
        self.m.write(EVM + 0x611, 1, spec)
        self.gt = gas_table
        self.eip2200 = eip2200
        self.m.write(IST + 0xb0, 8, EVM)
        self.m.write(IST + 0x13b, 1, 4 if eip8037 else 0)
        self.m.write(IST + 0x30, 1, 0xff)

    # slot entries keyed by (address, key); backing per address
    def slot(self, addr, key):
        if addr not in self.accounts:
            self.accounts[addr] = J.ACCT + 0x1000 * len(self.accounts)
        k = (addr, key)
        if k not in self.slots:
            p = J.SLOTS + 0x50 * self.nslot; self.nslot += 1
            v = (self.backing if addr == PM else self.cbacking).get(key, 0)
            self.put_word(p, v); self.put_word(p + 0x20, v); self.m.write(p + 0x40, 1, 0)
            self.slots[k] = p
        return self.slots[k]

    def save(self):
        c = self.cpu
        return (dict(c.r), list(c.y), c.cf, c.zf, c.sf, c.of)

    def restore(self, s):
        c = self.cpu
        c.r.clear(); c.r.update(s[0]); c.y = list(s[1]); c.cf, c.zf, c.sf, c.of = s[2:]

    def x_csload(self, cpu):
        out, addr_p, key_p, skip = cpu.r['rdi'], cpu.r['rdx'], cpu.r['rcx'], cpu.r['r8'] & 0xff
        addr = self.rd_addr(addr_p); key = self.get_word(key_p)
        self.calls.append(('csload', addr, key, skip))
        if self.dberr == 'load':
            self.put_word(out, 0); self.m.write(out, 8, 0xDB01); self.m.write(out + 0x10, 8, 0x07); self.m.write(out + 0x20, 1, 2)
            return
        s = self.save()
        self.acct_warm.add(addr)
        p = self.slot(addr, key)
        cold = 0
        if not self.m.read(p + 0x40, 1):
            if skip:
                self.restore(s)
                self.put_word(out, 0); self.m.write(out, 1, 0x20); self.m.write(out + 0x10, 1, 0xff); self.m.write(out + 0x20, 1, 2)
                return
            self.sstore_warm(addr, key, p); cold = 1
        v = self.get_word(p + 0x20)
        self.restore(s)
        self.put_word(out, v); self.m.write(out + 0x20, 1, cold)

    def x_csstore(self, cpu):
        out, addr_p, key_p, val_p = cpu.r['rdi'], cpu.r['rdx'], cpu.r['rcx'], cpu.r['r8']
        addr = self.rd_addr(addr_p); key = self.get_word(key_p); val = self.get_word(val_p)
        self.calls.append(('csstore', addr, key, val))
        if self.dberr == 'store':
            self.m.write(out, 8, 0xDB02); self.m.write(out + 8, 8, 0); self.m.write(out + 0x10, 8, 0x07)
            return
        s = self.save()
        p = self.slot(addr, key)
        if not self.m.read(p + 0x40, 1):
            self.sstore_warm(addr, key, p)
        orig = self.get_word(p); present = self.get_word(p + 0x20)
        self.put_word(J.ARGS + 0x80, val)
        self.run(0x42b455a, [], stop=0x42b46b8, regs={'r12': p, 'rdi': J.ARGS + 0x80 + 0x40, 'rbx': 0},
                 stack=self.frame_stack(addr, key, J.ARGS + 0x80))
        # SstoreTransitionFlags block of 0x4b62170, run from the binary
        FB = J.ARGS + 0x400
        self.put_word(FB, val)
        st = {0x38: (8, out)}
        for i in range(4): st[0x3a0 + 8 * i] = (8, (present >> (64 * i)) & U64)
        o = [(orig >> (64 * i)) & U64 for i in range(4)]
        self.run(0x4b632b9, [], stop=0x4b633e7, regs={'r13': o[0], 'r12': o[1], 'rbx': o[2], 'rbp': o[3], 'r9': FB}, stack=st)
        self.restore(s)

    def x_fatal_new(self, cpu):
        o = cpu.r['rdi']; self.calls.append(('fatal', 'credit_word'))
        self.m.write(o, 8, 0xF1F1); self.m.write(o + 8, 8, 0); self.m.write(o + 0x10, 8, 0x22)

    def x_fatal_mode(self, cpu):
        o = cpu.r['rdi']; self.calls.append(('fatal', 'mode'))
        self.m.write(o, 8, 0xF2F2); self.m.write(o + 8, 8, 0); self.m.write(o + 0x10, 8, 0x29)

    # one SSTORE by address `addr` (default: the PoolManager), from the write to the handler's exit
    def sstore_full(self, key, new, gas, addr=PM):
        p = self.slot(addr, key)
        cold = 0
        if not self.m.read(p + 0x40, 1):
            self.sstore_warm(addr, key, p); cold = 1
        orig = self.get_word(p); present = self.get_word(p + 0x20)
        J.Machine.sstore(self, addr, key, new)
        self.put_word(NEWV, new)
        self.m.write(IST + 0xf8, 8, gas); self.m.write(IST + 0x120, 8, 0)
        for o in (0x108, 0x110, 0x118): self.m.write(IST + o, 8, 0)
        self.m.write(IST + 0x30, 1, 0xff)
        c = self.cpu
        sp = OUTER_SP
        st = {}
        for i in range(4): st[0x450 + 8 * i] = (8, (present >> (64 * i)) & U64)
        st[0x20] = (16, addr & ((1 << 128) - 1)); st[0x30] = (4, addr >> 128)
        st[0x50] = (8, 0x10000 if self.eip2200 else 0)
        for k in list(c.r): c.r[k] = 0
        c.y = [0] * 16
        o = [(orig >> (64 * i)) & U64 for i in range(4)]
        c.r.update({'rbp': o[0], 'r9': o[1], 'r15': o[2], 'r13': o[3], 'r14': NEWV, 'r8': cold, 'rbx': IST, 'rsp': sp})
        for off, (n, v) in st.items(): c.write(sp + off, n, v)
        c.write(sp + 0x598 + 0x30, 8, RET)
        pc = 0x42b46b8; k = 0
        while pc != RET:
            pc = c.step(pc); k += 1
            if k > 2_000_000: raise Stop('step limit')
        code = c.r['rax'] & 0xff
        return dict(code=code, gas=self.m.read(IST + 0xf8, 8), refund=self.m.read(IST + 0x120, 8),
                    cold=cold, orig=orig, present=present)


# ---------------- reference: accounting.rs, instructions.rs and gas_params.rs as read
class RefState:
    def __init__(self, backing, cbacking):
        self.st = dict(backing); self.orig = dict(backing)          # PoolManager storage
        self.cst = dict(cbacking); self.corig = dict(cbacking)       # credit precompile storage
        self.tr = {}                                                 # credit precompile transient words
        self.warm = set()                                            # (addr, key)
        self.dberr = None

    def snap(self): return copy.deepcopy((self.st, self.cst, self.tr, self.warm))

    def back(self, s): self.st, self.cst, self.tr, self.warm = copy.deepcopy(s)


def dyn_gas(g, e2200, o, p, n, cold):
    if not e2200:
        return g['SstoreSetWithoutLoadCost'] if (p == 0 and n != 0) else g['SstoreResetWithoutColdLoadCost']
    d = g['ColdStorageCost'] if cold else 0
    if p != n and o == p:
        d += g['SstoreSetWithoutLoadCost'] if o == 0 else g['SstoreResetWithoutColdLoadCost']
    return d


def refund(g, e2200, o, p, n):
    c = g['SstoreClearingSlotRefund']
    if not e2200: return c if (p != 0 and n == 0) else 0
    if p == n: return 0
    if o == p and n == 0: return c
    r = 0
    if o != 0:
        if p == 0: r -= c
        elif n == 0: r += c
    if o == n:
        r += g['SstoreSetRefund'] if o == 0 else g['SstoreResetRefund']
    return r


def ref_sstore(R, g, key, new, gas, t7=True, e2200=True, addr=PM):
    """returns (code, gas, refund); code 0 ok, 0x20 OutOfGas halt, 0x34 fatal recorded through state.fail"""
    stor = R.st if addr == PM else R.cst
    origd = R.orig if addr == PM else R.corig
    cold = (addr, key) not in R.warm
    R.warm.add((addr, key)); R.info = dict(pmcold=cold, ccold=False, cchange=False, tchange=False)
    o = origd.get(key, 0); p = stor.get(key, 0); n = new
    stor[key] = n
    if t7 and ((p == 0) != (n == 0)) and addr != CADDR:
        if gas < g['WarmStorageReadCost']: return (0x20, None, None)
        gas -= g['WarmStorageReadCost']
        ck = addr_word(addr)
        skip = gas < g['ColdStorageAdditionalCost']
        ccold = (CADDR, ck) not in R.warm
        if R.dberr == 'load': return (0x34, None, None)
        if ccold and skip: return (0x20, None, None)
        R.warm.add((CADDR, ck)); R.info['ccold'] = ccold
        if ccold:
            if gas < g['ColdStorageAdditionalCost']: return (0x20, None, None)
            gas -= g['ColdStorageAdditionalCost']
        cw = R.cst.get(ck, 0)
        if cw >> 64: return (0x34, None, None)
        credit = cw; changed = False
        if p != 0 and n == 0:
            credit = min(credit + 1, U64); changed = True
        else:
            t = R.tr.get(ck, 0)
            mode = t & 0xff; budget = (t >> 64) & U64; pend = (t >> 192) & U64
            if mode > 2: return (0x34, None, None)
            if mode == 2 and credit > 0 and budget > 0:
                credit -= 1; changed = True
                if budget != U64:
                    budget -= 1
                    nw = 2 | (budget << 64) | (pend << 192); R.info['tchange'] = nw != t; R.tr[ck] = nw
            elif mode in (1, 2):
                if gas < CREDIT_VALUE: return (0x20, None, None)
                gas -= CREDIT_VALUE
            else:
                if gas < CREDIT_VALUE: return (0x20, None, None)
                gas -= CREDIT_VALUE
                pend = min(pend + 1, U64)
                nw = 0 | (budget << 64) | (pend << 192); R.info['tchange'] = nw != t; R.tr[ck] = nw
        if changed:
            if R.dberr == 'store': return (0x34, None, None)
            co = R.corig.get(ck, 0); cp = R.cst.get(ck, 0)
            R.cst[ck] = credit; R.info['cchange'] = cp != credit
            if cp != credit and co == cp:
                if gas < g['SstoreResetWithoutColdLoadCost']: return (0x20, None, None)
                gas -= g['SstoreResetWithoutColdLoadCost']
    d = dyn_gas(g, e2200, o, p, n, cold)
    if gas < d: return (0x20, None, None)
    gas -= d
    return (0, gas, refund(g, e2200, o, p, n) & U64)


# ---------------- case generation
from journal_x64_v1192 import SLOT0, LIQ, TICK, FG0, FG1, S0v, kw
POS = kw(kw(0xabc, 0xdef), STATE_SLOT6 := (kw(J.POOLID, 6) + 6))      # positions[...] word of the pool
PFEE = kw(0xC0FFEE01, 1)                                               # protocolFeesAccrued[currency]
BAL = kw(0xC0FFEE01, kw(0xbeef, 4))                                    # ERC-6909 balanceOf[owner][id]
PMKEYS = [SLOT0, LIQ, TICK, FG0, POS, PFEE, BAL]
CK = addr_word(PM)
CREDITS = [0, 1, 2, 20, (1 << 64) - 2, (1 << 64) - 1, 1 << 64, (1 << 64) + 5, M]
MODES = [0, 0 | (7 << 64) | (3 << 192), 1, 1 | (5 << 64), 2 | (U64 << 64), 2 | (1 << 64) | (9 << 192), 2 | (0 << 64), 2 | (5 << 64),
         3, 0xff, 0x100 | 2 | (5 << 64), (U64 << 192)]


def vclass(c, orig, rnd):
    return 0 if c == 0 else (orig if c == 1 else rnd.choice([1, 7, 10 ** 18, S0v, M]))


def gas_points(g):
    """gas values around every check the credit and dynamic gas code makes"""
    pts = set()
    w, ca, cr, rs, cs, st = (g['WarmStorageReadCost'], g['ColdStorageAdditionalCost'], CREDIT_VALUE,
                             g['SstoreResetWithoutColdLoadCost'], g['ColdStorageCost'], g['SstoreSetWithoutLoadCost'])
    for base in (0, w, w + ca, w + cr, w + ca + cr, w + rs, w + ca + rs, w + ca + rs + cs + st, w + ca + cr + cs + st,
                 w + cs + st, cs + st, cs + rs, rs, st, cr + st + w + ca + cs):
        for d in (-1, 0, 1):
            if base + d >= 0: pts.add(base + d)
    pts |= {10 ** 7, 3 * 10 ** 6}
    return sorted(pts)


def cases_task1(rnd, n_rand):
    out = []
    for gname, g in (('tempo', GAS_TEMPO), ('distinct', GAS_DISTINCT)):
        gp = gas_points(g)
        for key in PMKEYS:
            for oc in (0, 2):
                orig = 0 if oc == 0 else rnd.choice([3, 10 ** 18, S0v])
                for pc in (0, 1, 2):
                    for ncl in (0, 1, 2):
                        for cw in CREDITS:
                            for md in MODES:
                                for warm in (0, 1):
                                    gas = rnd.choice(gp) if rnd.random() < 0.7 else 10 ** 7
                                    out.append(dict(g=gname, key=key, orig=orig, pc=pc, nc=ncl, cw=cw, mode=md, warm=warm,
                                                    cwarm=rnd.random() < 0.3, gas=gas, t7=True, e2200=True,
                                                    seed=rnd.getrandbits(32)))
    rnd.shuffle(out)
    if n_rand: out = out[:n_rand]
    ngrid = len(out)
    # exhaustive gas sweep on fixed shapes, both T7 and pre-T7, EIP-2200 on and off, owner == credit address
    for gname, g in (('tempo', GAS_TEMPO), ('distinct', GAS_DISTINCT)):
        for (o, pc, ncl) in [(0, 0, 2), (5, 1, 0), (5, 2, 0), (0, 2, 0), (5, 0, 2), (5, 1, 2), (5, 0, 1), (0, 2, 1)]:
            for md in (0, 1, 2 | (U64 << 64), 2 | (3 << 64)):
                for cw in (0, 3, U64):
                    for gas in gas_points(g):
                        for warm in (0, 1):
                            for cwarm in (False, True):
                                out.append(dict(g=gname, key=LIQ, orig=o, pc=pc, nc=ncl, cw=cw, mode=md, warm=warm, cwarm=cwarm,
                                                gas=gas, t7=True, e2200=True, e8037=rnd.random() < 0.25, seed=rnd.getrandbits(32)))
        for dberr in ('load', 'store'):
            for (o, pc, ncl) in [(0, 0, 2), (5, 1, 0), (5, 2, 0)]:
                for md in (0, 2 | (U64 << 64)):
                    for cw in (0, 5):
                        out.append(dict(g=gname, key=LIQ, orig=o, pc=pc, nc=ncl, cw=cw, mode=md, warm=0, cwarm=False, gas=10 ** 7,
                                        t7=True, e2200=True, dberr=dberr, seed=rnd.getrandbits(32)))
        for t7, e2200, own in ((False, True, PM), (True, False, PM), (True, True, CADDR), (False, False, PM)):
            for (o, pc, ncl) in [(0, 0, 2), (5, 1, 0), (5, 2, 0), (5, 0, 2), (5, 1, 1)]:
                for gas in gas_points(g)[::3]:
                    out.append(dict(g=gname, key=LIQ, orig=o, pc=pc, nc=ncl, cw=4, mode=0, warm=0, cwarm=False, gas=gas,
                                    t7=t7, e2200=e2200, owner=own, seed=rnd.getrandbits(32)))
    k = int(os.environ.get('SWEEPSTEP', '1'))
    return out[:ngrid] + out[ngrid::k]


def run_task1(cases):
    res = dict(cases=0, mismatch=0, errors=0, records=[], by_code={}, by_path={})
    steps = 0; visited = set()
    for cs in cases:
        res['cases'] += 1
        g = GAS_TEMPO if cs['g'] == 'tempo' else GAS_DISTINCT
        r = random.Random(cs['seed'])
        own = cs.get('owner', PM)
        key = cs['key']
        present = vclass(cs['pc'], cs['orig'], r)
        new = vclass(cs['nc'], cs['orig'], r)
        if cs['pc'] == 2 and cs['nc'] == 2 and r.random() < 0.5: new = present
        try:
            mc = Mach(g, spec=0x0e if cs['t7'] else 0x0a, eip2200=cs['e2200'], eip8037=cs.get('e8037', False))
            if own == PM: mc.backing = {key: cs['orig']} if cs['orig'] else {}
            else: mc.cbacking = {key: cs['orig']} if cs['orig'] else {}
            mc.cbacking[CK] = mc.cbacking.get(CK, 0) if own == CADDR else cs['cw']
            R = RefState(mc.backing, mc.cbacking)
            mc.dberr = R.dberr = cs.get('dberr')
            # bring the slot to `present` inside the transaction (a prior write in the same transaction)
            if present != cs['orig']:
                if own == PM:
                    J.Machine.sstore(mc, PM, key, present); R.st[key] = present
                else:
                    J.Machine.sstore(mc, CADDR, key, present); R.cst[key] = present
                R.warm.add((own, key))
            elif cs['warm']:
                mc.sload(own, key); R.warm.add((own, key))
            if cs['cwarm'] and own == PM:
                mc.sload(CADDR, CK); R.warm.add((CADDR, CK))
            if cs['mode'] and own == PM:
                mc.tstore(CADDR, CK, cs['mode']); R.tr[CK] = cs['mode']
            jl0 = mc.jlen()
            got = mc.sstore_full(key, new, cs['gas'], addr=own)
            exp = ref_sstore(R, g, key, new, cs['gas'], t7=cs['t7'], e2200=cs['e2200'], addr=own)
            steps += mc.cpu.steps; visited |= mc.cpu.visited
        except Stop as e:
            res['errors'] += 1; res['records'].append(dict(case=cs, error=str(e))); continue
        p = mc.slots[(own, key)]
        gw = dict(code=got['code'], word=mc.get_word(p + 0x20), orig_word=mc.get_word(p))
        ew = dict(code=exp[0], word=new, orig_word=cs['orig'])
        if exp[0] == 0:
            gw.update(gas=got['gas'], refund=got['refund']); ew.update(gas=exp[1], refund=exp[2])
        # credit word and transient state (only meaningful when the handler did not halt)
        cp = mc.slots.get((CADDR, CK))
        gw['credit'] = mc.get_word(cp + 0x20) if cp else mc.cbacking.get(CK, 0)
        gw['credit_orig'] = mc.get_word(cp) if cp else mc.cbacking.get(CK, 0)
        ew['credit_orig'] = R.corig.get(CK, 0)
        gw['tstate'] = mc.tload(CADDR, CK)
        if exp[0] == 0:
            ew['credit'] = R.cst.get(CK, 0); ew['tstate'] = R.tr.get(CK, 0)
        else:
            # a halt ends the frame and the frame's checkpoint undoes these writes; compare only what
            # was written before the halt by replaying the reference's partial state
            ew['credit'] = R.cst.get(CK, 0); ew['tstate'] = R.tr.get(CK, 0)
        # journal: entries the PoolManager write and the credit write left
        ents = [mc.m.read(J.JBUF + 0x78 * i, 8) for i in range(jl0, mc.jlen())]
        gw['journal'] = ents
        ewj = []
        # expected: warm entry (tag of first-touch) on cold PM slot, change entry iff present != new,
        # then for the credit slot: warm entry if cold and loaded, change entry iff credit changed
        res['by_code'][got['code']] = res['by_code'].get(got['code'], 0) + 1
        path = ('cross' if (present == 0) != (new == 0) else 'nocross', cs['mode'] & 0xff if present == 0 and new else 'x0')
        res['by_path'][str(path)] = res['by_path'].get(str(path), 0) + 1
        gw_j = gw.pop('journal')
        jexp = journal_expect(R, present, new, exp)
        jok = jexp is None or jexp == gw_j
        if gw != ew or not jok:
            res['mismatch'] += 1
            res['records'].append(dict(case={k: (hex(v) if isinstance(v, int) else v) for k, v in cs.items()},
                                       present=hex(present), new=hex(new), got={k: (hex(v) if isinstance(v, int) else v) for k, v in gw.items()},
                                       exp={k: (hex(v) if isinstance(v, int) else v) for k, v in ew.items()},
                                       journal=[gw_j, jexp], calls=[str(x) for x in mc.calls]))
    return res, steps, visited


WARM_TAG, CHANGE_TAG, TR_TAG = None, None, 4
VIS = set()


def journal_expect(R, present, new, exp):
    """Entry tags (cycle 36 shape check: StorageWarmed and StorageChange) the write and the credit code must
    leave, in order; checked when the handler did not halt."""
    if exp[0] != 0: return None
    e = []
    if R.info['pmcold']: e.append(WARM_TAG)
    if present != new: e.append(CHANGE_TAG)
    if R.info['ccold']: e.append(WARM_TAG)
    if R.info['tchange']: e.append(TR_TAG)
    if R.info['cchange']: e.append(CHANGE_TAG)
    return e


def tags():
    mc = Mach(GAS_TEMPO); mc.backing = {LIQ: 500}
    mc.sload(PM, LIQ); w = mc.m.read(J.JBUF, 8)
    mc.sstore(PM, LIQ, 501); c = mc.m.read(J.JBUF + 0x78 * (mc.jlen() - 1), 8)
    return w, c


def check_journal(res_rec):
    return res_rec


# ---------------- Task 2: credit writes inside frames that revert at depth 1 to 3
def task2(rnd, n):
    res = dict(cases=0, mismatch=0, errors=0, records=[], credit_kept_after_revert=0)
    for i in range(n):
        g = GAS_TEMPO
        keys = rnd.sample(PMKEYS, 4)
        backing = {k: rnd.choice([0, 0, 5, 10 ** 18]) for k in keys}
        backing = {k: v for k, v in backing.items() if v}
        cw = rnd.choice([0, 1, 7, U64 - 1, U64])
        mode = rnd.choice([0, 1, 2 | (U64 << 64), 2 | (2 << 64), 2 | (0 << 64)])

        def ops(depth):
            r = []
            for _ in range(rnd.randint(1, 5)):
                c = rnd.random()
                if c < 0.65: r.append(('ss', rnd.choice(keys), rnd.choice([0, 0, 1, 9, 10 ** 18])))
                elif depth < 3: r.append(('frame', rnd.random() < 0.7, ops(depth + 1)))
            return r
        seq = [('frame', True, ops(1))] + ops(0) + [('frame', rnd.random() < 0.5, ops(1))]
        try:
            mc = Mach(g); mc.backing = dict(backing); mc.cbacking = {CK: cw}
            R = RefState(backing, {CK: cw})
            if mode:
                mc.tstore(CADDR, CK, mode); R.tr[CK] = mode
            bad = []

            def run(opl, depth):
                for op in opl:
                    if op[0] == 'ss':
                        got = mc.sstore_full(op[1], op[2], 10 ** 7)
                        exp = ref_sstore(R, g, op[1], op[2], 10 ** 7)
                        if (got['code'], got['gas'] if exp[0] == 0 else None) != (exp[0], exp[1]):
                            bad.append(('sstore', depth, op, got['code'], got['gas'], exp))
                        if exp[0] != 0:
                            raise Stop('halt inside sequence')
                    else:
                        cp = mc.jlen(); snap = R.snap()
                        cbefore = (mc.get_word(mc.slots[(CADDR, CK)] + 0x20) if (CADDR, CK) in mc.slots else cw, mc.tload(CADDR, CK))
                        pmbefore = {k: (mc.get_word(mc.slots[(PM, k)] + 0x20) if (PM, k) in mc.slots else backing.get(k, 0)) for k in keys}
                        run(op[2], depth + 1)
                        if op[1]:
                            mc.rollback(cp); R.back(snap)
                            cafter = (mc.get_word(mc.slots[(CADDR, CK)] + 0x20) if (CADDR, CK) in mc.slots else cw, mc.tload(CADDR, CK))
                            pmafter = {k: (mc.get_word(mc.slots[(PM, k)] + 0x20) if (PM, k) in mc.slots else backing.get(k, 0)) for k in keys}
                            if cafter != cbefore:
                                res['credit_kept_after_revert'] += 1
                                bad.append(('credit_after_revert', depth + 1, [hex(x) for x in cbefore], [hex(x) for x in cafter]))
                            if pmafter != pmbefore: bad.append(('pm_after_revert', depth + 1))
                            if mc.jlen() != cp: bad.append(('journal_len', mc.jlen(), cp))
                            # warm flags must be undone too: credit slot cold again iff it was cold before
                            for (a, k), p in mc.slots.items():
                                wf = mc.m.read(p + 0x40, 1)
                                if bool(wf) != ((a, k) in R.warm): bad.append(('warm_flag', hex(k), wf))
            run(seq, 0)
            # final words
            for k in keys:
                gwd = mc.get_word(mc.slots[(PM, k)] + 0x20) if (PM, k) in mc.slots else backing.get(k, 0)
                if gwd != R.st.get(k, 0): bad.append(('final_pm', hex(k)))
            fc = mc.get_word(mc.slots[(CADDR, CK)] + 0x20) if (CADDR, CK) in mc.slots else cw
            if fc != R.cst.get(CK, 0): bad.append(('final_credit', hex(fc), hex(R.cst.get(CK, 0))))
            if mc.tload(CADDR, CK) != R.tr.get(CK, 0): bad.append(('final_tstate',))
            VIS.update(mc.cpu.visited)
        except Stop as e:
            if str(e) == 'halt inside sequence':
                res['cases'] += 1; continue
            res['errors'] += 1; res['records'].append(dict(seq=repr(seq), error=str(e))); continue
        res['cases'] += 1
        if bad:
            res['mismatch'] += 1
            res['records'].append(dict(seq=repr(seq), backing={hex(k): hex(v) for k, v in backing.items()}, cw=hex(cw),
                                       mode=hex(mode), bad=[repr(b) for b in bad]))
    return res


if __name__ == '__main__':
    rnd = random.Random(SEED)
    WARM_TAG, CHANGE_TAG = tags()
    out = dict(fault=FAULT, seed=SEED, binary_sha256='27a42f86b4f3c1d3c5e8623d597c80ea6299920ec9c70f3a303b4083bc023ddd',
               tags=[WARM_TAG, CHANGE_TAG])
    c1 = cases_task1(rnd, NR)
    r1, steps, visited = run_task1(c1)
    out['task1'] = r1
    out['task2'] = task2(rnd, int(os.environ.get('NT2', '400')))
    visited |= VIS
    cov = {}
    for f, lo, hi in (('credit_region', 0x42b46b8, 0x42b5096), ('credit_tail_blocks', 0x42b50f1, 0x42b5176),
                      ('flags_block', 0x4b632b9, 0x4b633e7), ('refund', 0x2d26f80, 0x2d2710c),
                      ('tload_host', 0x1e8fd10, 0x1e8feac), ('tstore_host', 0x1e8feb0, 0x1e902be), ('rollback', 0x1e90db0, 0x1e9143b)):
        tot = [a for a in J.prog.ins if lo <= a < hi and not J.prog.ins[a].startswith('int3') and not J.prog.ins[a].startswith('nop')]
        cov[f] = [len([a for a in tot if a in visited]), len(tot)]
    out['coverage_task1'] = cov
    out['unvisited_credit_region'] = sorted(hex(a) for a in J.prog.ins if 0x42b46b8 <= a < 0x42b5096 and a not in visited
                                            and not J.prog.ins[a].startswith('nop'))
    out['steps_task1'] = steps
    json.dump(out, open(OUT, 'w'), indent=1, default=str)
    print(FAULT, 'task1', r1['cases'], 'mm', r1['mismatch'], 'err', r1['errors'], r1['by_code'],
          'task2', out['task2']['cases'], 'mm', out['task2']['mismatch'], 'err', out['task2']['errors'],
          'kept', out['task2']['credit_kept_after_revert'], cov)
