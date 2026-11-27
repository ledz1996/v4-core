"""Runs TSTORE / TLOAD sequences with snapshots and reverts through the Nitro b72783f transient storage path in the
x86-64 and AArch64 models (tsmodel.py) and compares every read with tools/opdiff/pyevm.py.

A sequence is a list of steps: ('st', addr, slot, value), ('ld', addr, slot), ('snap',), ('rev',) reverting the
newest open snapshot, ('commit',) dropping the newest open snapshot (inner frame returned). Snapshots in the model
are journal lengths, passed to the binary's (*journal).revert as revertToSnapshot passes revision.journalIndex.
In pyevm the reference is World.snapshot / World.restore, which its CALL frames use.

usage: python3 -I tsdrive.py <arch> <nseq> <out.json> [fault]
seed 31_1211_01 (sequence generator).
"""
import json, random, sys, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import tsmodel as T
from tsmodel import Stop, AStop
import pyevm as PE
from evm import assemble, keccak

arch, NSEQ, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]
FAULT = sys.argv[4] if len(sys.argv) > 4 else 'none'
SEED = 31_1211_01
M = (1 << 256) - 1
PM = 0x360e68faccca8ca495c1b759fd9eee466db9fb32
OTHER = 0x8366a39cc670b4001a1121b8f6a443a643e40951


def kw(*xs): return int.from_bytes(keccak(b''.join((x & M).to_bytes(32, 'big') for x in xs)), 'big')


# PoolManager slot shapes: CurrencyDelta._computeSlot (src/libraries/CurrencyDelta.sol:10-15), NONZERO_DELTA_COUNT_SLOT
# (NonzeroDeltaCount.sol:9-10), IS_UNLOCKED_SLOT (Lock.sol:8), RESERVES_OF_SLOT and CURRENCY_SLOT (CurrencyReserves.sol:11-13)
FIXED = [0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b,
         0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23,
         0x1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95,
         0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9]
TARGETS = [0x66a9893cc07d91d95644aedd05d03f95e1dba8af, 0xd21fe301, 0xdead, 0]
CURRENCIES = [0, 0xaf88d065e77c8cc2239327c5edb3a432268e5831, 0x82af49447d8a07e3bd95bd0d56f35241523fbab1, 0xC0FFEE31]
DELTAS = [kw(t, c) for t in TARGETS for c in CURRENCIES]
# slots that differ from a delta slot in one 64 bit limb or in one byte, to catch a key that drops part of the word
NEAR = [DELTAS[1] ^ (1 << 0), DELTAS[1] ^ (1 << 64), DELTAS[1] ^ (1 << 128), DELTAS[1] ^ (1 << 255), DELTAS[1] ^ (0xff << 96)]
SLOTS = FIXED + DELTAS + NEAR
VALUES = [0, 1, M, (1 << 255), (-10 ** 18) & M, 10 ** 18, (1 << 127) - 1, (-(1 << 127)) & M, 2, 3]


def gen(rnd):
    steps, depth = [], 0
    addrs = [PM, OTHER, PM ^ (1 << 100)]
    hist = {}
    for _ in range(rnd.randrange(4, 40)):
        r = rnd.random()
        a = addrs[0] if rnd.random() < 0.8 else rnd.choice(addrs)
        s = rnd.choice(SLOTS[:8] if rnd.random() < 0.5 else SLOTS)
        if r < 0.40:
            v = rnd.choice(VALUES) if rnd.random() < 0.6 else rnd.getrandbits(256)
            if rnd.random() < 0.15 and (a, s) in hist:
                v = hist[(a, s)]  # write of an equal value
            steps.append(('st', a, s, v)); hist[(a, s)] = v
        elif r < 0.70:
            steps.append(('ld', a, s))
        elif r < 0.82 and depth < 6:
            steps.append(('snap',)); depth += 1
        elif depth:
            steps.append(('rev',) if rnd.random() < 0.6 else ('commit',)); depth -= 1
    while depth:
        steps.append(('rev',) if rnd.random() < 0.5 else ('commit',)); depth -= 1
    steps += [('ld', a, s) for a in addrs[:2] for s in SLOTS[:8]]
    return steps


def fixed_sequences():
    d, c = DELTAS[1], FIXED[0]
    yield [('st', PM, d, 5), ('snap',), ('st', PM, d, 7), ('rev',), ('ld', PM, d)]
    yield [('st', PM, d, 5), ('snap',), ('st', PM, d, 5), ('st', PM, d, 9), ('rev',), ('ld', PM, d)]
    yield [('snap',), ('st', PM, d, 5), ('snap',), ('st', PM, d, 0), ('rev',), ('ld', PM, d), ('rev',), ('ld', PM, d)]
    yield [('st', PM, c, 1), ('snap',), ('st', PM, c, 2), ('snap',), ('st', PM, c, 1), ('commit',), ('rev',), ('ld', PM, c)]
    yield [('st', PM, d, M), ('snap',), ('st', PM, d, 0), ('st', PM, d, 3), ('rev',), ('ld', PM, d), ('ld', OTHER, d)]
    yield [('st', PM, NEAR[i], 11 + i) for i in range(5)] + [('ld', PM, d)] + [('ld', PM, x) for x in NEAR]
    yield [('st', PM, d, 1), ('st', OTHER, d, 2), ('snap',), ('st', OTHER, d, 0), ('rev',), ('ld', PM, d), ('ld', OTHER, d)]


class Ref:
    CODE = assemble([('PUSH', 0), 'CALLDATALOAD', ('PUSH', 1), 'EQ', ('REF', 'st'), 'JUMPI',
                     ('PUSH', 32), 'CALLDATALOAD', 'TLOAD', ('PUSH', 0), 'MSTORE', ('PUSH', 32), ('PUSH', 0), 'RETURN',
                     ('LABEL', 'st'), ('PUSH', 64), 'CALLDATALOAD', ('PUSH', 32), 'CALLDATALOAD', 'TSTORE', 'STOP'])

    def __init__(self, addrs):
        self.w = PE.World({a: self.CODE for a in addrs})
        self.snaps = []

    def st(self, a, s, v):
        ok, _ = self.w.call(1, a, 0, (1).to_bytes(32, 'big') + s.to_bytes(32, 'big') + v.to_bytes(32, 'big'), False, 1)
        assert ok

    def ld(self, a, s):
        ok, r = self.w.call(1, a, 0, (2).to_bytes(32, 'big') + s.to_bytes(32, 'big'), False, 1)
        assert ok
        return int.from_bytes(r, 'big')

    def snap(self): self.snaps.append(self.w.snapshot())
    def rev(self): self.w.restore(self.snaps.pop())
    def commit(self): self.snaps.pop()


class Bin:
    def __init__(self, model):
        self.m = model
        self.w = T.World(model)
        self.c = model.cpu(self.w)
        m, c = model, self.c
        # EVM: readOnly byte at +0x1a0, StateDB interface (itab, data) at +0xd8 / +0xe0 (read from opTstore of both builds)
        m.wr(c, T.EVM + 0x1a0, 1, 0)
        m.wr(c, T.EVM + 0xd8, 8, model.itab_statedb)
        m.wr(c, T.EVM + 0xe0, 8, T.STATEDB)
        # StateDB: transientStorage map at +0xf0, journal pointer at +0xf8 (read from SetTransientState)
        m.wr(c, T.STATEDB + 0xf0, 8, T.TSMAP)
        m.wr(c, T.STATEDB + 0xf8, 8, T.JOURNAL)
        # journal: entries slice at +0x8/+0x10/+0x18, mutations map at +0x20 (read from append and revert)
        for o in (0x8, 0x10, 0x18):
            m.wr(c, T.JOURNAL + o, 8, 0)
        m.wr(c, T.JOURNAL + 0x20, 8, T.MUTMAP)
        m.wr(c, T.SCOPE + 8, 8, T.STACKOBJ)
        m.wr(c, T.SCOPE + 0x10, 8, T.CONTRACT)
        m.wr(c, T.STACKOBJ + 0x10, 8, T.ARENA)
        m.wr(c, T.ARENA, 8, T.DATA)
        m.wr(c, T.ARENA + 8, 8, T.NSLOT)
        self.snaps = []

    def _stack(self, words):
        m, c = self.m, self.c
        stack = [0xa5a5] * 2 + words  # last element is the top
        for i, x in enumerate(stack):
            m.wr(c, T.DATA + 32 * i, 32, x)
        m.wr(c, T.STACKOBJ + 8, 8, len(stack))
        m.wr(c, T.ARENA + 0x18, 8, len(stack))
        return len(stack)

    def _addr(self, a):
        self.m.wbytes(self.c, T.CONTRACT + 0x14, a.to_bytes(20, 'big'))

    def st(self, a, s, v):
        self._addr(a)
        n = self._stack([v, s])
        r = self.m.call(self.c, self.m.fns[T.VM + 'opTstore'][0], [T.PCPTR, T.EVM, T.SCOPE])
        if any(r): raise Stop('opTstore returned %s' % (r,))
        if self.m.rd(self.c, T.ARENA + 0x18, 8) != n - 2: raise Stop('stack top after TSTORE')

    def ld(self, a, s):
        self._addr(a)
        n = self._stack([s])
        r = self.m.call(self.c, self.m.fns[T.VM + 'opTload'][0], [T.PCPTR, T.EVM, T.SCOPE])
        if any(r): raise Stop('opTload returned %s' % (r,))
        if self.m.rd(self.c, T.ARENA + 0x18, 8) != n: raise Stop('stack top after TLOAD')
        return self.m.rd(self.c, T.DATA + 32 * (n - 1), 32)

    def jlen(self): return self.m.rd(self.c, T.JOURNAL + 0x10, 8)
    def snap(self): self.snaps.append(self.jlen())

    def rev(self):
        s = self.snaps.pop()
        self.m.call(self.c, self.m.fns[T.ST + '(*journal).revert'][0], [T.JOURNAL, T.STATEDB, s])
        # revertToSnapshot truncates validRevisions only; entries are truncated by revert itself (read from its tail)
        if self.jlen() != s: raise Stop('journal length %d after revert to %d' % (self.jlen(), s))

    def commit(self): self.snaps.pop()


import re as _re
# planted faults: (address, replacement instruction text) per architecture, applied to the in-memory disassembly
PLANT = {
    'revert_zero': {'amd64': [(0x12373a2, 'nop')], 'arm64': [(0x100d564, 'nop')]},            # revert always deletes
    'skip_journal': {'amd64': [(0x1214620, 'nop')], 'arm64': [(0xff0900, 'nop')]},          # no journal entry
    'snap_off_by_one': {'amd64': [(0x1206bf8, 'jge    1206ede')], 'arm64': [(0xfe5748, 'b.ge\t0xfe5988')]},
    'key_limb': {'amd64': [(0x1214885, 'nop')], 'arm64': [(0xff0adc, 'str\tq1, [x27, #0x10]')]},  # TLOAD key loses 16 bytes
    'equal_skip_inverted': {'amd64': [(0x1214507, 'je     12147a5')], 'arm64': [(0xff084c, 'tbz\tw3, #0x0, 0xff0a34')]},
}


def patcher(arch, fault):
    def patch(text):
        for a, ins in PLANT[fault][arch]:
            pat = _re.compile(r'^(\s*%x:\s+).*$' % a, _re.M)
            text, n = pat.subn(lambda m: m.group(1) + ins, text)
            assert n == 1, (fault, hex(a), n)
        return text
    return patch


FAULTS = {f: (lambda a, f=f: {'text_patch': patcher(a, f)}) for f in PLANT}


def main():
    model = T.Model(arch, **FAULTS.get(FAULT, lambda a: {})(arch)) if FAULT != 'none' else T.Model(arch)
    rnd = random.Random(SEED)
    seqs = list(fixed_sequences()) + [gen(rnd) for _ in range(NSEQ)]
    res = {'arch': arch, 'fault': FAULT, 'seed': SEED, 'sequences': len(seqs), 'steps': 0, 'reads': 0,
           'stores': 0, 'reverts': 0, 'equalWrites': 0, 'mismatches': [], 'errors': [], 'started': time.time()}
    for qi, seq in enumerate(seqs):
        ref = Ref([PM, OTHER, PM ^ (1 << 100)])
        try:
            b = Bin(model)
            last = {}
            for st in seq:
                res['steps'] += 1
                if st[0] == 'st':
                    if last.get((st[1], st[2])) == st[3]: res['equalWrites'] += 1
                    ref.st(*st[1:]); b.st(*st[1:]); res['stores'] += 1
                    last[(st[1], st[2])] = st[3]
                elif st[0] == 'ld':
                    x, y = ref.ld(*st[1:]), b.ld(*st[1:]); res['reads'] += 1
                    if x != y:
                        res['mismatches'].append({'seq': qi, 'steps': [list(map(lambda v: hex(v) if isinstance(v, int) else v, s)) for s in seq],
                                                  'at': [hex(v) if isinstance(v, int) else v for v in st], 'ref': hex(x), 'bin': hex(y)})
                        break
                elif st[0] == 'snap':
                    ref.snap(); b.snap()
                elif st[0] == 'rev':
                    ref.rev(); b.rev(); res['reverts'] += 1; last = {}
                else:
                    ref.commit(); b.commit()
        except (Stop, AStop) as e:
            res['errors'].append({'seq': qi, 'error': str(e)})
    res['visited'] = len(model.visited)
    res['stubbed'] = sorted(model.stubbed)
    res['elapsed'] = time.time() - res['started']
    json.dump(res, open(OUT, 'w'), indent=1)
    print(arch, FAULT, 'seqs', len(seqs), 'reads', res['reads'], 'reverts', res['reverts'], 'mismatches', len(res['mismatches']),
          'errors', len(res['errors']), (res['errors'][:1] or [''])[0])


if __name__ == '__main__':
    main()
