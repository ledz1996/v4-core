"""Cycle 39, theme-ethereum-binaries-storage-journal: nested-frame storage sequences over the PoolManager's slot shapes,
the pyevm reference, and the runner shared by the geth, erigon and reth drivers.

Slot shapes (read from src/): transient IS_UNLOCKED_SLOT (src/libraries/Lock.sol:8), NONZERO_DELTA_COUNT_SLOT
(src/libraries/NonzeroDeltaCount.sol:9), CURRENCY_SLOT and RESERVES_OF_SLOT (src/libraries/CurrencyReserves.sol:11-13),
currency deltas keccak(target, currency) (src/libraries/CurrencyDelta.sol:12-14); persistent pool state at
keccak(poolId, 6) (src/libraries/StateLibrary.sol:11, :325) with liquidity at +3, a tick at keccak(tick, base+4), a
position at keccak(positionKey, base+6), an ERC-6909 balance at keccak(id, keccak(owner, 4)) (src/ERC6909.sol:17), and a
token's balance slot of the PoolManager keccak(PM, 0) in a token account (the settle shape, src/PoolManager.sol:349-364).

A step is ('tst', a, s, v), ('tld', a, s), ('sst', a, s, v), ('sld', a, s), ('snap',) (enter an inner frame),
('rev',) (the inner frame reverts), ('commit',) (the inner frame returns). After every frame return the runner reads
every touched transient and persistent slot and the original value of every touched persistent slot and compares them
with the reference; it also checks that a revert restores the journal length recorded at the snapshot.
Seed 39_1346_01 (random sequences), fixed sequences first.
"""
import random, sys
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import pyevm as PE
from evm import assemble, keccak

MW = (1 << 256) - 1
SEED = 39_1346_01
PM = 0x000000000004444c5dc75cB358380D2e3dE08A90
TOKEN = 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48
HOOK = 0x1234560000000000000000000000000000000080
ADDRS = [PM, TOKEN, HOOK]


def kw(*xs): return int.from_bytes(keccak(b''.join((x & MW).to_bytes(32, 'big') for x in xs)), 'big')


LOCK = 0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23
COUNT = 0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b
RES = 0x1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95
CUR = 0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9
LOCKER = 0x66a9893cc07d91d95644aedd05d03f95e1dba8af
DELTAS = [kw(t, c) for t in (LOCKER, HOOK) for c in (0, TOKEN)]
TSLOTS = [LOCK, COUNT, RES, CUR] + DELTAS
POOLID = 0x21c67e77068de97969ba93d4aab21826d33ca12bb9f565d8496e8fda8a82ca27
P0 = kw(POOLID, 6)
PSLOTS = [P0, P0 + 1, P0 + 2, P0 + 3, kw((-887220) & MW, P0 + 4), kw(60, P0 + 4) + 1, kw(0xabc, P0 + 6),
          kw(TOKEN, kw(LOCKER, 4)), kw(0, kw(HOOK, 4)), 2]
TOKBAL = kw(PM, 0)
VALUES = [0, 1, MW, 1 << 255, (-10 ** 18) & MW, 10 ** 18, (1 << 127) - 1, (-(1 << 127)) & MW, 2, 3,
          0x0000000000000000000000000000000000000000000000000000000000000001 << 160]


def initial_db(rnd):
    """Committed values below the state: about half the persistent slots start non-zero."""
    db = {}
    for s in PSLOTS + [TOKBAL]:
        for a in (PM, TOKEN):
            if rnd.random() < 0.5:
                db[(a, s)] = rnd.choice(VALUES[1:]) if rnd.random() < 0.6 else rnd.getrandbits(256)
    return db


def gen(rnd, db):
    steps, depth, hist = [], 0, {}
    if rnd.random() < 0.35:
        # filler keys so that the maps leave their small form (Go swiss maps hold 8 entries in one group) and grow
        # tables: random slots and slots one bit away from a delta slot
        for _ in range(rnd.randrange(9, 48)):
            s = rnd.getrandbits(256) if rnd.random() < 0.7 else DELTAS[1] ^ (1 << rnd.randrange(256))
            steps.append((rnd.choice(('tst', 'sst')), PM, s, rnd.getrandbits(256) or 1))
    for _ in range(rnd.randrange(6, 40)):
        r = rnd.random()
        a = PM if rnd.random() < 0.75 else rnd.choice(ADDRS)
        if r < 0.22:
            s = rnd.choice(TSLOTS); v = rnd.choice(VALUES) if rnd.random() < 0.6 else rnd.getrandbits(256)
            if rnd.random() < 0.2 and ('t', a, s) in hist: v = hist[('t', a, s)]
            steps.append(('tst', a, s, v)); hist[('t', a, s)] = v
        elif r < 0.44:
            s = rnd.choice(PSLOTS + [TOKBAL]); v = rnd.choice(VALUES) if rnd.random() < 0.6 else rnd.getrandbits(256)
            if rnd.random() < 0.25: v = db.get((a, s), 0)        # written back to its original value
            elif rnd.random() < 0.15 and ('s', a, s) in hist: v = hist[('s', a, s)]
            steps.append(('sst', a, s, v)); hist[('s', a, s)] = v
        elif r < 0.56:
            steps.append(('tld', a, rnd.choice(TSLOTS)))
        elif r < 0.68:
            steps.append(('sld', a, rnd.choice(PSLOTS + [TOKBAL])))
        elif r < 0.82 and depth < 4:
            steps.append(('snap',)); depth += 1
        elif depth:
            steps.append(('rev',) if rnd.random() < 0.6 else ('commit',)); depth -= 1
    while depth:
        steps.append(('rev',) if rnd.random() < 0.5 else ('commit',)); depth -= 1
    return steps


def settle_shape(db, credit, revert=True):
    """sync (currency and reserves), an inner frame that moves the token balance and credits the delta, then reverts."""
    bal = db.get((TOKEN, TOKBAL), 0)
    d = DELTAS[1]
    s = [('tst', PM, LOCK, 1), ('tst', PM, CUR, TOKEN), ('tst', PM, RES, bal), ('snap',),
         ('sld', TOKEN, TOKBAL), ('sst', TOKEN, TOKBAL, (bal + credit) & MW), ('tld', PM, CUR), ('tld', PM, RES),
         ('tst', PM, d, credit), ('tst', PM, COUNT, 1), ('tst', PM, CUR, 0), ('rev',) if revert else ('commit',),
         ('tld', PM, d), ('tld', PM, COUNT), ('tld', PM, CUR), ('tld', PM, RES), ('sld', TOKEN, TOKBAL)]
    return s


def fixed_sequences(db):
    d, p = DELTAS[1], P0 + 3
    o = db.get((PM, p), 0)
    yield [('sst', PM, p, 5), ('snap',), ('sst', PM, p, 7), ('rev',), ('sld', PM, p)]
    yield [('snap',), ('sst', PM, p, 5), ('sst', PM, p, 9), ('rev',), ('sld', PM, p)]           # written twice in a frame
    yield [('sst', PM, p, 5), ('snap',), ('sst', PM, p, o), ('rev',), ('sld', PM, p)]           # back to original, reverted
    yield [('snap',), ('sst', PM, p, 5), ('rev',), ('sld', PM, p)]                               # first read after a revert
    yield [('snap',), ('snap',), ('sst', PM, p, 5), ('tst', PM, d, 3), ('commit',), ('rev',), ('sld', PM, p), ('tld', PM, d)]
    yield [('snap',), ('snap',), ('snap',), ('snap',), ('sst', PM, p, 1), ('tst', PM, LOCK, 1), ('rev',), ('rev',), ('rev',),
           ('rev',), ('sld', PM, p), ('tld', PM, LOCK)]                                           # depth 4
    yield [('tst', PM, d, 5), ('snap',), ('tst', PM, d, 7), ('rev',), ('tld', PM, d)]
    yield [('tst', PM, d, 5), ('snap',), ('tst', PM, d, 0), ('rev',), ('tld', PM, d)]
    yield [('sst', PM, p, o), ('snap',), ('sst', PM, p, (o + 1) & MW), ('sst', PM, p, o), ('commit',), ('sld', PM, p)]
    for c in (1, 10 ** 18, (1 << 127) - 1, MW):
        yield settle_shape(db, c, True)
        yield settle_shape(db, c, False)


class Ref:
    CODE = assemble([('PUSH', 0), 'CALLDATALOAD', 'DUP1', ('PUSH', 1), 'EQ', ('REF', 'tst'), 'JUMPI',
                     'DUP1', ('PUSH', 3), 'EQ', ('REF', 'sst'), 'JUMPI',
                     ('PUSH', 2), 'EQ', ('REF', 'tld'), 'JUMPI',
                     ('PUSH', 32), 'CALLDATALOAD', 'SLOAD', ('PUSH', 0), 'MSTORE', ('PUSH', 32), ('PUSH', 0), 'RETURN',
                     ('LABEL', 'tld'), ('PUSH', 32), 'CALLDATALOAD', 'TLOAD', ('PUSH', 0), 'MSTORE', ('PUSH', 32), ('PUSH', 0), 'RETURN',
                     ('LABEL', 'tst'), ('PUSH', 64), 'CALLDATALOAD', ('PUSH', 32), 'CALLDATALOAD', 'TSTORE', 'STOP',
                     ('LABEL', 'sst'), ('PUSH', 64), 'CALLDATALOAD', ('PUSH', 32), 'CALLDATALOAD', 'SSTORE', 'STOP'])

    def __init__(self, db):
        self.w = PE.World({a: self.CODE for a in ADDRS})
        self.w.storage = dict(db)
        self.db = dict(db)
        self.snaps = []

    def _c(self, cmd, a, s, v=0):
        ok, r = self.w.call(1, a, 0, cmd.to_bytes(32, 'big') + s.to_bytes(32, 'big') + v.to_bytes(32, 'big'), False, 1)
        assert ok
        return int.from_bytes(r, 'big') if r else None

    def tst(self, a, s, v): self._c(1, a, s, v)
    def tld(self, a, s): return self._c(2, a, s)
    def sst(self, a, s, v): self._c(3, a, s, v)
    def sld(self, a, s): return self._c(4, a, s)
    def orig(self, a, s): return self.db.get((a, s), 0)
    def snap(self): self.snaps.append(self.w.snapshot())
    def rev(self): self.w.restore(self.snaps.pop())
    def commit(self): self.snaps.pop()


def hx(v): return hex(v) if isinstance(v, int) else v


def run_seq(mk, seq, db, res, qi):
    """mk(db) -> machine with tst/tld/sst/sld/orig(a,s)->(cur,orig)/snap()->id/revert(id)/jlen(); returns None or mismatch"""
    ref = Ref(db); m = mk(db)
    snaps, touched_t, touched_s = [], set(), set()

    def bad(at, what, x, y):
        return {'seq': qi, 'steps': [[hx(v) for v in s] for s in seq], 'db': {'%x:%x' % k: hex(v) for k, v in db.items()},
                'at': at, 'what': what, 'ref': hx(x), 'bin': hx(y)}

    def check(at):
        for (a, s) in sorted(touched_t):
            x, y = ref.tld(a, s), m.tld(a, s); res['reads'] += 1
            if x != y: return bad(at, 'transient %x %x' % (a, s), x, y)
        for (a, s) in sorted(touched_s):
            x, y = ref.sld(a, s), m.sld(a, s); res['reads'] += 1
            if x != y: return bad(at, 'storage %x %x' % (a, s), x, y)
            cur, org = m.orig(a, s); res['origChecks'] += 1
            if cur != x or org != ref.orig(a, s): return bad(at, 'original %x %x' % (a, s), (x, ref.orig(a, s)), (cur, org))
        return None

    for i, st in enumerate(seq):
        res['steps'] += 1
        k = st[0]
        if k in ('tst', 'sst'):
            getattr(ref, k)(*st[1:]); getattr(m, k)(*st[1:]); res['writes'] += 1
            (touched_t if k == 'tst' else touched_s).add((st[1], st[2]))
        elif k in ('tld', 'sld'):
            x, y = getattr(ref, k)(*st[1:]), getattr(m, k)(*st[1:]); res['reads'] += 1
            (touched_t if k == 'tld' else touched_s).add((st[1], st[2]))
            if x != y: return bad(i, k, x, y)
        elif k == 'snap':
            ref.snap(); snaps.append((m.snap(), m.jlen()))
        elif k == 'rev':
            ref.rev(); rid, jl = snaps.pop(); m.revert(rid); res['reverts'] += 1
            if m.jlen()[0] != jl[0]: return bad(i, 'journal length after revert', jl, m.jlen())
            r = check(i)
            if r: return r
        elif k == 'commit':
            ref.commit(); snaps.pop(); res['commits'] += 1
            if hasattr(m, 'commit'): m.commit()
            r = check(i)
            if r: return r
    return check(len(seq))


def sequences(n):
    rnd = random.Random(SEED)
    out = []
    db0 = initial_db(random.Random(SEED + 1))
    for s in fixed_sequences(db0): out.append((s, db0))
    for _ in range(n):
        db = initial_db(rnd)
        out.append((gen(rnd, db), db))
    return out
