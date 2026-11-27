"""Task 2, second half: the PoolManager runtime of this checkout (research/network-risk/build/
PoolManager.json, via PM_BUILD) run in tools/opdiff/pyevm.py twice per scenario, once as is
and once with every SLOAD, SSTORE, TSTORE, value transfer, frame entry and exit and revert
routed through the erigon main cache model (cachemodel.py). Compared: the value every SLOAD
returned, in order; every SSTORE in order; the bytes the driver returns (the record of
every call's return data, including swap and modifyLiquidity deltas and extsload reads of
slot0, liquidity and fee growth after each step); and the final storage.

Shapes: a hook whose beforeSwap, beforeAddLiquidity, beforeRemoveLiquidity or beforeDonate
reenters the PoolManager on the same pool (through the driver's callback, so msg.sender is
the driver and the hook is called again on the nested operation) with a swap, a donate, an
add and remove of the same position (storage written back), a nested list that reverts, and
unlock-free functions (initialize of another pool, extsload, exttload, ERC-6909 approve,
setOperator, transfer). Analysis harness for a local reference interpreter only.
Usage: PM_BUILD=research/network-risk/build/PoolManager.json python3 -I pmshapes.py <out.json> [n] [fault]"""
import sys, os, json, random, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(HERE, '..', '..', '..', '..', 'tools', 'opdiff'))
from evm import assemble, keccak, MASK, u, s
import v4math as m
import pmdiff as P, pmdiff2 as Q, pmdiff3 as R
from pyevm import World
from cachemodel import Core

PMI, DRV = R.PMI, R.DRV
T0, T1 = R.T0, R.T1
HB = 0x00000000000000000000000000000000486D0000
FLAGS = (1 << 11) | (1 << 9) | (1 << 7) | (1 << 5)  # beforeAdd, beforeRemove, beforeSwap, beforeDonate
HK = HB | FLAGS
w = R.w; item = R.item; tail = R.tail
KEYSIG = P.KEY
SEL = {n: int.from_bytes(P.sel(sig), 'big') for n, sig in {
    'swap': f'beforeSwap(address,{KEYSIG},(bool,int256,uint160),bytes)',
    'add': f'beforeAddLiquidity(address,{KEYSIG},(int24,int24,int256,bytes32),bytes)',
    'remove': f'beforeRemoveLiquidity(address,{KEYSIG},(int24,int24,int256,bytes32),bytes)',
    'donate': f'beforeDonate(address,{KEYSIG},uint256,uint256,bytes)'}.items()}


def rhook(trig, k, blob):
    """pmdiff3's hook double with a prefix: on the k-th call with selector trig it calls the
    driver's unlockCallback with blob (a list of PoolManager calls) once, then answers as usual."""
    def prog(off):
        p = [('PUSH', 0), 'CALLDATALOAD', ('PUSH', 224), 'SHR', ('PUSHN', 4, trig), 'EQ', 'ISZERO', ('REF', 'skip'), 'JUMPI',
             ('PUSH', 8), 'TLOAD', ('PUSH', 1), 'ADD', 'DUP1', ('PUSH', 8), 'TSTORE', ('PUSHN', 1, k), 'EQ', 'ISZERO', ('REF', 'skip'), 'JUMPI',
             ('PUSHN', 2, len(blob)), ('PUSHN', 2, off), ('PUSHN', 2, 0x3000), ('RAW', b'\x39'),
             ('PUSH', 0), ('PUSH', 0), ('PUSHN', 2, len(blob)), ('PUSHN', 2, 0x3000), ('PUSH', 0), ('PUSHN', 20, DRV), 'GAS', 'CALL',
             ('PUSH', 10), 'TSTORE', ('LABEL', 'skip')]
        return p
    # the body of pmdiff3.hook, as a list, rebuilt here so its labels resolve in one program
    hp = [('PUSH', 0), 'CALLDATALOAD', ('PUSH', 224), 'SHR', 'DUP1', ('PUSH', 1), 'EQ', ('REF', 'set'), 'JUMPI',
          ('PUSH', 3), 'EQ', ('REF', 'fwd'), 'JUMPI',
          ('PUSH', 0), 'CALLDATALOAD', ('PUSH', 224), 'SHR', ('PUSH', 224), 'SHL', ('PUSH', 5), 'TLOAD', 'XOR', ('PUSH', 0), 'MSTORE',
          ('PUSH', 1), 'TLOAD', ('PUSH', 32), 'MSTORE', ('PUSH', 2), 'TLOAD', ('PUSH', 64), 'MSTORE',
          ('PUSH', 4), 'TLOAD', ('REF', 'rev'), 'JUMPI', ('PUSH', 3), 'TLOAD',
          'DUP1', ('PUSHN', 2, R.AUTO), 'EQ', 'ISZERO', ('REF', 'plain'), 'JUMPI',
          'POP', ('PUSH', 64), ('PUSH', 0), 'CALLDATALOAD', ('PUSH', 224), 'SHR', ('PUSHN', 4, R.BEFORE_SWAP), 'EQ', ('PUSH', 32), 'MUL', 'ADD',
          ('LABEL', 'plain'), ('PUSH', 0), 'RETURN',
          ('LABEL', 'rev'), ('PUSH', 3), 'TLOAD', ('PUSH', 0), 'REVERT',
          ('LABEL', 'fwd'), ('PUSH', 4), 'CALLDATASIZE', 'SUB', 'DUP1', ('PUSH', 4), ('PUSH', 0), 'CALLDATACOPY',
          ('PUSH', 0), ('PUSH', 0), 'DUP3', ('PUSH', 0), ('PUSH', 0), ('PUSHN', 20, PMI), 'GAS', 'CALL',
          'RETURNDATASIZE', ('PUSH', 0), ('PUSH', 0), 'RETURNDATACOPY', ('REF', 'fok'), 'JUMPI', 'RETURNDATASIZE', ('PUSH', 0), 'REVERT',
          ('LABEL', 'fok'), 'RETURNDATASIZE', ('PUSH', 0), 'RETURN',
          ('LABEL', 'set'), 'POP']
    for j in range(1, 6): hp += [('PUSH', 4 + 32 * (j - 1)), 'CALLDATALOAD', ('PUSH', j), 'TSTORE']
    hp += ['STOP']
    n0 = len(assemble(prog(0) + hp))
    code = assemble(prog(n0) + hp)
    assert len(code) == n0
    return code + blob


def cb(items, ret_ok):
    data = b''.join(items) + ((1).to_bytes(20, 'big') if ret_ok else (2).to_bytes(20, 'big')) + b'\0\0'
    return P.S_CB + w(0x20) + w(len(data)) + data + bytes(-len(data) % 32)


class RefWorld(World):
    def __init__(self, codes, balances):
        super().__init__(codes, balances)
        self.storage = LogStore(self); self.sl = []; self.ss = []
    def restore(self, snap):
        self.logs = snap[3]; self.transient, self.balances = snap[1], snap[2]
        dict.clear(self.storage); dict.update(self.storage, snap[0])


class LogStore(dict):
    def __init__(self, wd): super().__init__(); self.wd = wd
    def get(self, k, d=0):
        v = dict.get(self, k, d); self.wd.sl.append((k[0], k[1], v)); return v
    def __setitem__(self, k, v):
        if self.wd.storage is self and hasattr(self.wd, 'ss'): self.wd.ss.append((k[0], k[1], v))
        dict.__setitem__(self, k, v)


class CStore(dict):
    def __init__(self, wd): super().__init__(); self.wd = wd
    def get(self, k, d=0):
        wd = self.wd
        v = wd.core.sload(k[0], k[1]) if wd.core.frames else dict.get(self, k, d)
        wd.sl.append((k[0], k[1], v)); return v
    def __setitem__(self, k, v):
        wd = self.wd
        if wd.core.frames:
            wd.ss.append((k[0], k[1], v))
            if sum(1 for f in wd.core.frames if f.addr == k[0]) > 2: wd.reentrant_writes += 1  # a PoolManager frame inside a hook inside a PoolManager operation
            wd.core.sstore(k[0], k[1], v)
        else: dict.__setitem__(self, k, v)


class JDict(dict):
    def __init__(self, wd, init=()): super().__init__(init); self.wd = wd
    def __setitem__(self, k, v): self.wd.core.journalled_set(self, k, v)


class CachedWorld(World):
    def __init__(self, codes, balances, fault=None):
        super().__init__(codes, {})
        self.sl = []; self.ss = []; self.reentrant_writes = 0; self.reentrant_frames = 0
        self.storage = CStore(self); self.core = Core(self.storage, fault)
        self.transient = JDict(self); self.balances = JDict(self, balances or {})
    def snapshot(self): return (dict(self.storage), dict(self.transient), dict(self.balances), self.logs, self.core.n)
    def restore(self, snap):
        for d, src in ((self.storage, snap[0]), (self.transient, snap[1]), (self.balances, snap[2])):
            dict.clear(d); dict.update(d, src)
        self.logs = snap[3]; self.core.revert_to(snap[4])
    def run(self, code_addr, me, caller, value, data, static, depth):
        if sum(1 for f in self.core.frames if f.addr == me) >= 2: self.reentrant_frames += 1  # unlock frame, the operation that called the hook, then this one
        self.core.enter(me)
        try: return super().run(code_addr, me, caller, value, data, static, depth)
        finally: self.core.leave()


def key(fee=3000, sp=60, hk=HK): return w(T0) + w(T1) + w(fee) + w(sp) + w(hk)
def i_swap(k, zfo, amt, limit=None):
    if limit is None: limit = m.MIN_SQRT_PRICE + 1 if zfo else m.MAX_SQRT_PRICE - 1
    return item(PMI, P.S_SWAP + k + w(int(zfo)) + w(amt) + w(limit) + w(0x120) + tail(b''))
def i_mod(k, lo, hi, d, salt=0): return item(PMI, P.S_MOD + k + w(lo) + w(hi) + w(d) + w(salt) + w(0x140) + tail(b''))
def i_don(k, a0, a1): return item(PMI, P.S_DONATE + k + w(a0) + w(a1) + w(0x100) + tail(b''))
def i_ext(slot): return item(PMI, P.S_EXTSLOAD + w(slot))


def state_reads(k):
    pid = keccak(k); base = int.from_bytes(keccak(pid + w(6)), 'big')
    out = [i_ext((base + j) & MASK) for j in range(4)]
    out += [item(PMI, P.S_EXTTLOAD + w(P.delta_slot(DRV, T0))), item(PMI, P.S_EXTTLOAD + w(P.delta_slot(DRV, T1)))]
    return out


def scenario(rnd, idx):
    """Returns (description, outer script bytes, hook code)."""
    k = key(); sp = 60
    t0 = rnd.choice([0, 0, rnd.randrange(-3000, 3000)]); price = m.get_sqrt_price_at_tick(t0)
    base_t = t0 // sp * sp
    pos = [(base_t - 600, base_t + 600, 10 ** 18), (base_t - 120, base_t + 180, rnd.choice([10 ** 17, 10 ** 19])), (base_t + 60, base_t + 1200, 10 ** 18)]
    trig = rnd.choice(['swap', 'swap', 'add', 'remove', 'donate'])
    mag = rnd.choice([10 ** 12, 10 ** 15, 10 ** 17, 3 * 10 ** 18]); zfo = rnd.random() < 0.5
    nested_kind = rnd.choice(['swap', 'swap-both', 'donate', 'addremove', 'revert', 'unlockfree', 'mix'])
    nk = []
    if nested_kind in ('swap', 'mix'): nk += [i_swap(k, rnd.random() < 0.5, -rnd.choice([10 ** 14, 10 ** 16, 10 ** 18]))]
    if nested_kind == 'swap-both': nk += [i_swap(k, True, -mag), i_swap(k, False, mag // 2 or 1), i_swap(k, False, -mag)]
    if nested_kind in ('donate', 'mix'): nk += [i_don(k, rnd.getrandbits(40), rnd.getrandbits(40))]
    if nested_kind in ('addremove', 'mix'):
        lo, hi = base_t - 60 * rnd.randrange(1, 5), base_t + 60 * rnd.randrange(1, 5); L = rnd.choice([10 ** 15, 10 ** 18])
        nk += [i_mod(k, lo, hi, L, 7), i_mod(k, lo, hi, -L, 7)]
    if nested_kind == 'revert': nk += [i_swap(k, zfo, -mag), i_mod(k, base_t - 60, base_t + 60, 10 ** 18, 9), i_don(k, 5, 5)]
    if nested_kind in ('unlockfree', 'mix'):
        k2 = key(500, 10, 0)
        nk += [item(PMI, P.S_INIT + k2 + w(m.get_sqrt_price_at_tick(rnd.randrange(-100, 100)))), item(PMI, R.S['approve'] + w(R.OTHER) + w(T1) + w(5)),
               item(PMI, R.S['setOperator'] + w(R.OTHER) + w(1)), item(PMI, R.S['transfer'] + w(R.OTHER) + w(T1) + w(1)), item(PMI, R.S['extN'] + w(int.from_bytes(keccak(keccak(k) + w(6)), 'big')) + w(4))]
    nk += state_reads(k)
    blob = cb(nk, ret_ok=(nested_kind != 'revert'))
    trig_k = {'swap': 1, 'add': len(pos) + 1, 'remove': 1, 'donate': 1}[trig]
    hook = rhook(SEL[trig], trig_k, blob)
    items = [item(HK, Q.S_SET + w(0) + w(0) + w(R.AUTO) + w(0) + w(0)), item(PMI, P.S_INIT + k + w(price))]
    for lo, hi, L in pos: items.append(i_mod(k, lo, hi, L))
    items += state_reads(k)
    if trig == 'add': items.append(i_mod(k, base_t - 240, base_t + 240, rnd.choice([10 ** 16, 10 ** 18])))
    if trig == 'remove': items.append(i_mod(k, pos[1][0], pos[1][1], -(pos[1][2] // rnd.choice([1, 2, 3]))))
    if trig == 'donate': items.append(i_don(k, rnd.getrandbits(50), rnd.getrandbits(50)))
    if trig == 'swap': items.append(i_swap(k, zfo, -mag if rnd.random() < 0.7 else mag))
    items += state_reads(k)
    items.append(i_swap(k, not zfo, -mag)); items += state_reads(k)
    data = b''.join(items) + (2).to_bytes(20, 'big') + b'\0\0'  # revert with the record: nothing has to be settled
    return f'{idx}: trig={trig}#{trig_k} nested={nested_kind} t0={t0} zfo={zfo} mag={mag}', data, hook


def codes(pm, hook):
    c = {PMI: pm, DRV: R.driver(), T0: Q.token(), T1: Q.token(), HK: hook}
    return c


def run(world_cls, pm, hook, data, **kw):
    wd = world_cls(codes(pm, hook), {PMI: 10 ** 19}, **kw)
    dict.__setitem__(wd.storage, (PMI, 0), DRV)
    ok, ret = wd.call(0, DRV, 0, data, False, 0)
    return wd, ok, ret


if __name__ == '__main__':
    out = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 120; fault = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != 'none' else None
    pm = P.fetch_code(); SEED = 36_2026_11_27 + 1
    rnd = random.Random(SEED)
    res = {'seed': SEED, 'fault': fault, 'pmCodeSha256': hashlib.sha256(pm).hexdigest(), 'pmCodeLen': len(pm), 'scenarios': [], 'mismatches': []}
    tot = {'scenarios': 0, 'sloads': 0, 'pmSloads': 0, 'hits': 0, 'sstores': 0, 'stale': 0, 'mismatch': 0, 'nestedCallsOk': 0, 'nestedReverted': 0, 'callsInRecord': 0, 'okInRecord': 0, 'reentrantPmFrames': 0, 'reentrantPmWrites': 0, 'scenariosWithReentrantWrite': 0}
    for i in range(n):
        desc, data, hook = scenario(rnd, i)
        rw, ok1, ret1 = run(RefWorld, pm, hook, data)
        cw, ok2, ret2 = run(CachedWorld, pm, hook, data, fault=fault)
        rec = P.parse(ret1)
        same = {'ret': ret1 == ret2 and ok1 == ok2, 'sloads': rw.sl == cw.sl, 'sstores': rw.ss == cw.ss, 'final': dict(rw.storage) == dict(cw.storage)}
        sc = {'desc': desc, 'sloads': len(cw.sl), 'pmSloads': sum(1 for a, _, _ in cw.sl if a == PMI), 'hits': cw.core.hits, 'sstores': len(cw.ss), 'stale': len(cw.core.stale), 'same': same,
              'calls': len(rec), 'ok': sum(1 for kk, _ in rec if kk), 'reentrantPmFrames': cw.reentrant_frames, 'reentrantPmWrites': cw.reentrant_writes, 'retSha256': hashlib.sha256(ret1).hexdigest()}
        res['scenarios'].append(sc)
        tot['scenarios'] += 1; tot['sloads'] += sc['sloads']; tot['pmSloads'] += sc['pmSloads']; tot['hits'] += sc['hits']; tot['sstores'] += sc['sstores']; tot['stale'] += sc['stale']
        tot['reentrantPmFrames'] += cw.reentrant_frames; tot['reentrantPmWrites'] += cw.reentrant_writes; tot['scenariosWithReentrantWrite'] += cw.reentrant_writes > 0
        tot['callsInRecord'] += sc['calls']; tot['okInRecord'] += sc['ok']
        if not all(same.values()) or cw.core.stale:
            tot['mismatch'] += 1
            first = next((j for j, (x, y) in enumerate(zip(rw.sl, cw.sl)) if x != y), None)
            res['mismatches'].append({'desc': desc, 'same': same, 'stale': cw.core.stale, 'firstSloadDiff': first,
                                      'ref': [hex(v) for v in rw.sl[first]] if first is not None else None, 'cached': [hex(v) for v in cw.sl[first]] if first is not None else None,
                                      'ret1': ret1.hex(), 'ret2': ret2.hex(), 'data': data.hex(), 'hook': hook.hex()})
    res['totals'] = tot
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps(tot))
