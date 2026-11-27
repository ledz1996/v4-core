"""Cycle 32 task 2 (L-1226, L-1227): the persistent storage path of the shipped bsc v1.8.2 binaries (amd64 and arm64,
cycle 31 downloads, read as data only) run in the cycle 31 models, against tools/opdiff/pyevm.py.

Run from the binary: core/vm.opSload and opSstore, (*StateDB).GetCommittedState (the original value the SSTORE gas
functions read), Snapshot and RevertToSnapshot, and every core/state function they reach by direct call
(getStateObject, getOrNewStateObject, createObject, newObject, (*stateObject).GetState, getState, GetCommittedState,
SetState, (*journal).storageChange, append, revert, revertToSnapshot, ...), plus the methods of the journalEntry itabs
of *storageChange and createObjectChange read from the file.

The StateDB is set up as a block's StateDB in the middle of a transaction: stateObjects (StateDB+0x80) holds live
objects for the PoolManager address and one other address, stateObjectsDestruct (+0x88) is empty, the reader
interface (+0x18) is a fake itab whose Account (+0x18) and Storage (+0x38) methods are Python stubs serving the base
state, prefetcher and stateReadList are nil, needBadSharedStorage (+0x78) is false. Offsets read from the
disassembly of getStateObject and (*stateObject).GetCommittedState (they are the same on both architectures).
stateObject: db +0, address +8, originStorage +0xa0, dirtyStorage +0xa8, pendingStorage +0xb0.

Python stubs in addition to tsgo.py's: sync.(*Pool).Get (a fresh zeroed *storageChange, typed with the type
descriptor the binary's assertion compares), time.Now, time.Since, the two reader methods.

Checks after every step: every SLOAD equals pyevm; GetCommittedState of every slot touched equals the value at
transaction start; the binary's dirtyStorage of each object equals {slot: value | value != original}; after each
revert the journal length equals the length at the snapshot and the journal dirties map has no address with count 0.
Cases: slot written back to its original value, slot written twice in one frame, slot first read after an inner
revert (originStorage empty for it until then), account first touched inside a frame (created through
getOrNewStateObject with the reader returning no account, then reverted).
usage: python3 -I stgo.py <bsc-amd64|bsc-arm64> <nseq> <out.json> [fault]    seed 32_1226_02
"""
import json, os, random, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tsgo as T
from tsgo import Stop, AStop, G, targets, XProg, AProg, rewrite_rip, M64
import pyevm as PE
from evm import assemble, keccak

SEED = 32_1226_02
MW = (1 << 256) - 1
GE = 'github.com/ethereum/go-ethereum/'
S, V = GE + 'core/state.', GE + 'core/vm.'
B = T.BASE
OBJ = [B + 0x40000, B + 0x41000]
READERITAB = B + 0x42000
FAKE = 0x7d000000
PM = 0x28e2ea090877bf75740558f6bfb36a5ffee9e9df
OTHER = 0x8366a39cc670b4001a1121b8f6a443a643e40951
NEWACCT = 0x00000000000000000000000000000000c0ffee77


def kw(*xs): return int.from_bytes(keccak(b''.join((x & MW).to_bytes(32, 'big') for x in xs)), 'big')


POOLID = 0x21c67e77068de97969ba93d4aab21826d33ca12bb9f565d8496e8fda8a82ca27
PS = kw(POOLID, 6)
SLOTS = [PS, PS + 1, PS + 2, PS + 3, kw(PS + 4 + 0, 0) if False else PS + 4, kw(0xd21fe301, kw(POOLID, 6) + 6),
         kw(kw(0xC0FFEE31, 4), 0xd21fe301), 2, 3, PS ^ (1 << 248), PS ^ 1]
VALUES = [0, 1, MW, 1 << 255, 10 ** 18, (1 << 160) - 1, 2]


class SModel(T.Model):
    def __init__(self, arch, text_patch=None):
        self.kind, self.arch = 'bsc', arch
        self.c = dict(T.CFG['bsc'])
        t = targets.get('bsc-' + arch)
        self.bin = t['bin']
        self.img = T.Img(self.bin)
        self.fns = G.fnlist(t['fns'])
        self.byaddr = {v[0]: k for k, v in self.fns.items()}
        self.sym = T.nm_symbols(self.bin)
        self.S, self.V = S, V
        self.itab_sdb = self.sym['go:itab.*%score/state.StateDB,%score/vm.StateDB' % (GE, GE)]
        # *storageChange type descriptor the assertion after sync.(*Pool).Get compares (journal.storageChange:
        # amd64 10bf006 lea rcx,[rip+..] -> 0x2946ac0; arm64 f230b8 adrp/add x2 -> 0x24ead80)
        self.t_sc = {'amd64': 0x2946ac0, 'arm64': 0x24ead80}[arch]
        roots = [V + 'opSload', V + 'opSstore', S + '(*StateDB).GetCommittedState', S + '(*StateDB).Snapshot',
                 S + '(*StateDB).RevertToSnapshot']
        extra = set()
        for k, v in self.sym.items():
            if k.startswith('go:itab.') and k.endswith(',%score/state.journalEntry' % GE) and \
                    ('storageChange' in k or 'createObjectChange' in k):
                for i in range(3):
                    a = self.img.read(v + 0x18 + 8 * i, 8)
                    if a in self.byaddr:
                        extra.add(self.byaddr[a])
        for i in range(120):
            a = self.img.read(self.itab_sdb + 0x18 + 8 * i, 8)
            nm = self.byaddr.get(a, '')
            if nm.endswith(('.GetState', '.SetState', '.GetCommittedState', '.GetStateAndCommittedState')):
                extra.add(nm)
        self.roots = roots + sorted(extra)
        self.stub_names = [n for n in T.STUBS if n in self.fns]
        self.ranges, self.text = self._closure(self.roots, text_patch)
        self.prog = XProg(rewrite_rip(self.text)) if arch == 'amd64' else AProg([self.text])
        self.visited = set()
        self.stubbed = set()

    def externs(self, w):
        ext = super().externs(w)
        f = self.fns

        def pool_get(cpu):
            self.stubbed.add('sync.(*Pool).Get')
            size = self.img.read(self.img.read(self.t_sc + 0x30, 8), 8) if False else 0x80
            a = w.alloc(size); self.wbytes(cpu, a, bytes(size)); self.ret(cpu, self.t_sc, a)

        def tnow(cpu):
            self.stubbed.add('time.Now'); self.ret(cpu, 0, 0, 0)

        def tsince(cpu):
            self.stubbed.add('time.Since'); self.ret(cpu, 0)

        def sp(cpu):
            return cpu.r['rsp'] if self.arch == 'amd64' else cpu.x[31]

        def r_account(cpu):
            # Account(addr) (*types.StateAccount, error): nil, nil -> the account does not exist in the base state
            self.stubbed.add('reader.Account')
            base = sp(cpu) + (0 if self.arch == 'amd64' else 8)
            addr = int.from_bytes(self.rbytes(cpu, base, 20), 'big')
            w.base_reads.append(('acct', addr))
            if addr in w.base_accounts:
                raise Stop('Account read for an existing address %x' % addr)
            self.ret(cpu, 0, 0, 0)

        def r_storage(cpu):
            self.stubbed.add('reader.Storage')
            # stub reached from the caller's register call: the stack args start at the caller's SP on amd64 and
            # at SP+8 on arm64 (the Go arm64 frame keeps the link slot at 0)
            base = sp(cpu) + (0 if self.arch == 'amd64' else 8)
            addr = int.from_bytes(self.rbytes(cpu, base, 20), 'big')
            key = int.from_bytes(self.rbytes(cpu, base + 0x14, 32), 'big')
            w.base_reads.append(('slot', addr, key))
            v = w.base.get((addr, key), 0)
            self.wbytes(cpu, base + 0x38, v.to_bytes(32, 'big'))
            self.ret(cpu, 0, 0, 0)

        for n, fn in (('sync.(*Pool).Get', pool_get), ('time.Now', tnow), ('time.Since', tsince)):
            if n in f:
                ext[f[n][0]] = fn
        ext[FAKE + 0x18] = r_account
        ext[FAKE + 0x38] = r_storage
        return ext


class SBin(T.Bin):
    def __init__(self, model, base, base_accounts):
        self.m = model
        self.w = T.World(model)
        self.w.base = base
        self.w.base_accounts = base_accounts
        self.w.base_reads = []
        self.c = model.cpu(self.w)
        self.w.cpu = self.c
        m, c, C = model, self.c, model.c
        m.wr(c, T.EVM + C['evmSdb'], 8, model.itab_sdb)
        m.wr(c, T.EVM + C['evmSdb'] + 8, 8, T.STATEDB)
        m.wr(c, T.STATEDB + C['jptr'], 8, T.JOURNAL)
        m.wr(c, T.JOURNAL + 0x18, 8, self.w.newmap())
        m.wr(c, T.STATEDB + 0x18, 8, READERITAB)
        m.wr(c, T.STATEDB + 0x20, 8, B + 0x43000)
        for o in (0x18, 0x38):
            m.wr(c, READERITAB + o, 8, FAKE + o)
        self.objmap = self.w.newmap()
        m.wr(c, T.STATEDB + 0x80, 8, self.objmap)
        m.wr(c, T.STATEDB + 0x88, 8, self.w.newmap())
        for i, a in enumerate(sorted(base_accounts)):
            o = OBJ[i]
            m.wr(c, o, 8, T.STATEDB)
            m.wbytes(c, o + 8, a.to_bytes(20, 'big'))
            for off in (0xa0, 0xa8, 0xb0):
                m.wr(c, o + off, 8, self.w.newmap())
            self.w.maps[self.objmap][a.to_bytes(20, 'big')] = self._box(o)
        m.wr(c, T.SCOPE + 8, 8, T.STACKOBJ)
        m.wr(c, T.SCOPE + 0x10, 8, T.CONTRACT)
        m.wr(c, T.STACKOBJ + 0x10, 8, T.ARENA)
        m.wr(c, T.ARENA, 8, T.DATA)
        m.wr(c, T.ARENA + 8, 8, T.NSLOT)
        self.snaps, self.jl = [], []
        self.sdbname = '(*StateDB)'

    def _box(self, v):
        a = self.w.alloc(8); self.m.wr(self.c, a, 8, v); return a

    def obj(self, addr):
        k = addr.to_bytes(20, 'big')
        d = self.w.maps[self.objmap]
        if k not in d:
            return None
        return self.m.rd(self.c, d[k], 8)

    def dirty(self, addr):
        o = self.obj(addr)
        if not o:
            return None
        h = self.m.rd(self.c, o + 0xa8, 8)
        return {int.from_bytes(k, 'big'): int.from_bytes(self.m.rbytes(self.c, v, 32), 'big') for k, v in self.w.maps.get(h, {}).items()}

    def sst(self, a, s, v):
        self._addr(a)
        n, base = self._stack([v, s])
        r = self.m.call(self.c, self.m.fns[V + 'opSstore'][0], [T.PCPTR, T.EVM, T.SCOPE])
        if any(r): raise Stop('opSstore returned %s' % (r,))
        if self._top() != n - 2: raise Stop('stack top after SSTORE')

    def sld(self, a, s):
        self._addr(a)
        n, base = self._stack([s])
        r = self.m.call(self.c, self.m.fns[V + 'opSload'][0], [T.PCPTR, T.EVM, T.SCOPE])
        if any(r): raise Stop('opSload returned %s' % (r,))
        return self.m.rd(self.c, base + 32 * (n - 1), 32)

    def committed(self, a, s):
        m, c = self.m, self.c
        # (*StateDB).GetCommittedState(addr [20]byte, key [32]byte) [32]byte: arrays on the stack, result after them
        top = T.SP_TOP
        if m.arch == 'amd64':
            m.wbytes(c, top, a.to_bytes(20, 'big')); m.wbytes(c, top + 0x14, s.to_bytes(32, 'big'))
            m.wbytes(c, top + 0x38, b'\xa5' * 32)
            m.call(c, m.fns[S + '(*StateDB).GetCommittedState'][0], [T.STATEDB])
            return int.from_bytes(m.rbytes(c, top + 0x38, 32), 'big')
        m.wbytes(c, top + 8, a.to_bytes(20, 'big')); m.wbytes(c, top + 0x1c, s.to_bytes(32, 'big'))
        m.wbytes(c, top + 0x40, b'\xa5' * 32)
        m.call(c, m.fns[S + '(*StateDB).GetCommittedState'][0], [T.STATEDB])
        return int.from_bytes(m.rbytes(c, top + 0x40, 32), 'big')

    def jlen(self): return self.m.rd(self.c, T.JOURNAL + 8, 8)

    def snap(self):
        super().snap(); self.jl.append(self.jlen())

    def rev(self):
        super().rev()
        j = self.jl.pop()
        if self.jlen() != j: raise Stop('journal length %d after revert, %d at snapshot' % (self.jlen(), j))
        h = self.m.rd(self.c, T.JOURNAL + 0x18, 8)
        for k, v in self.w.maps[h].items():
            if self.m.rd(self.c, v, 8) == 0:
                raise Stop('dirties entry with count 0 kept')

    def commit(self):
        super().commit(); self.jl.pop()


class Ref:
    CODE = assemble([('PUSH', 0), 'CALLDATALOAD', ('PUSH', 1), 'EQ', ('REF', 'st'), 'JUMPI',
                     ('PUSH', 32), 'CALLDATALOAD', 'SLOAD', ('PUSH', 0), 'MSTORE', ('PUSH', 32), ('PUSH', 0), 'RETURN',
                     ('LABEL', 'st'), ('PUSH', 64), 'CALLDATALOAD', ('PUSH', 32), 'CALLDATALOAD', 'SSTORE', 'STOP'])

    def __init__(self, base):
        self.w = PE.World({a: self.CODE for a in (PM, OTHER, NEWACCT)})
        self.w.storage = dict(base)
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


def gen(rnd, base):
    steps, depth, hist = [], 0, {}
    addrs = [PM, PM, PM, OTHER, NEWACCT]
    for _ in range(rnd.randrange(4, 36)):
        r = rnd.random()
        a = rnd.choice(addrs)
        s = rnd.choice(SLOTS)
        if r < 0.42:
            x = rnd.random()
            if x < 0.25 and (a, s) in base:
                v = base[(a, s)]  # back to the original value
            elif x < 0.4 and (a, s) in hist:
                v = hist[(a, s)]  # equal to the current value
            elif x < 0.7:
                v = rnd.choice(VALUES)
            else:
                v = rnd.getrandbits(256)
            steps.append(('st', a, s, v)); hist[(a, s)] = v
            if rnd.random() < 0.2:
                steps.append(('st', a, s, rnd.choice(VALUES)))  # second write in the same frame
        elif r < 0.68:
            steps.append(('ld', a, s))
        elif r < 0.8 and depth < 6:
            steps.append(('snap',)); depth += 1
        elif depth:
            steps.append(('rev',) if rnd.random() < 0.6 else ('commit',)); depth -= 1
    while depth:
        steps.append(('rev',) if rnd.random() < 0.5 else ('commit',)); depth -= 1
    steps += [('ld', a, s) for a in (PM, OTHER) for s in SLOTS]
    return steps


def fixed(base):
    s0 = SLOTS[0]
    o = base.get((PM, s0), 0)
    yield [('snap',), ('st', PM, s0, 7), ('st', PM, s0, o), ('rev',), ('ld', PM, s0)]
    yield [('st', PM, s0, 9), ('snap',), ('st', PM, s0, o), ('rev',), ('ld', PM, s0)]
    yield [('snap',), ('st', PM, SLOTS[3], 1), ('rev',), ('ld', PM, SLOTS[3]), ('st', PM, SLOTS[3], 2), ('ld', PM, SLOTS[3])]
    yield [('snap',), ('st', NEWACCT, s0, 5), ('ld', NEWACCT, s0), ('rev',), ('ld', NEWACCT, s0), ('st', NEWACCT, s0, 6), ('ld', NEWACCT, s0)]
    yield [('snap',), ('ld', PM, SLOTS[5]), ('st', PM, SLOTS[5], 3), ('rev',), ('ld', PM, SLOTS[5])]


def run(arch, nseq, out, text_patch=None, fault='none'):
    model = SModel(arch, text_patch)
    rnd = random.Random(SEED)
    res = {'target': 'bsc-' + arch, 'fault': fault, 'seed': SEED, 'functions': sorted(model.ranges), 'sequences': 0,
           'steps': 0, 'reads': 0, 'stores': 0, 'reverts': 0, 'committedChecks': 0, 'dirtyChecks': 0, 'newAccountSteps': 0,
           'baseReads': 0, 'mismatches': [], 'errors': [], 'started': time.time()}
    seqs = []
    for q in range(nseq + 5):
        base = {}
        for a in (PM, OTHER):
            for s in SLOTS:
                if rnd.random() < 0.6:
                    base[(a, s)] = rnd.choice(VALUES[1:]) if rnd.random() < 0.6 else rnd.getrandbits(256)
        seqs.append((base, None))
    fx = list(fixed(seqs[0][0]))
    import gc
    for qi, (base, _) in enumerate(seqs):
        if qi % 200 == 0:
            gc.collect()
        seq = fx[qi] if qi < len(fx) else gen(rnd, base)
        res['sequences'] += 1
        ref = Ref(base)
        try:
            b = SBin(model, base, {PM, OTHER})
            orig = dict(base)

            def check(st):
                for a in (PM, OTHER, NEWACCT):
                    d = b.dirty(a)
                    if d is None:
                        continue
                    want = {s: v for (aa, s), v in ref.w.storage.items() if aa == a and v != orig.get((a, s), 0)}
                    # slots written back to zero are absent from pyevm's dict only when never written; compare both ways
                    for (aa, s) in list(orig):
                        if aa == a and ref.w.storage.get((a, s), 0) != orig[(a, s)]:
                            want[s] = ref.w.storage.get((a, s), 0)
                    want = {s: v for s, v in want.items() if v != orig.get((a, s), 0)}
                    res['dirtyChecks'] += 1
                    if d != want:
                        return {'dirty': a, 'bin': {hex(k): hex(v) for k, v in d.items()}, 'ref': {hex(k): hex(v) for k, v in want.items()}}
                if st[0] in ('st', 'ld'):
                    res['committedChecks'] += 1
                    x = b.committed(st[1], st[2])
                    if x != orig.get((st[1], st[2]), 0):
                        return {'committed': hex(st[2]), 'bin': hex(x), 'ref': hex(orig.get((st[1], st[2]), 0))}
                return None

            for st in seq:
                res['steps'] += 1
                if st[0] in ('st', 'ld') and st[1] == NEWACCT:
                    res['newAccountSteps'] += 1
                if st[0] == 'st':
                    ref.st(*st[1:]); b.sst(*st[1:]); res['stores'] += 1
                elif st[0] == 'ld':
                    x, y = ref.ld(*st[1:]), b.sld(*st[1:]); res['reads'] += 1
                    if x != y:
                        res['mismatches'].append({'seq': qi, 'at': [hex(v) if isinstance(v, int) else v for v in st], 'ref': hex(x), 'bin': hex(y),
                                                  'steps': [[hex(v) if isinstance(v, int) else v for v in s] for s in seq]})
                        break
                elif st[0] == 'snap':
                    ref.snap(); b.snap()
                elif st[0] == 'rev':
                    ref.rev(); b.rev(); res['reverts'] += 1
                else:
                    ref.commit(); b.commit()
                bad = check(st)
                if bad:
                    bad.update({'seq': qi, 'at': [hex(v) if isinstance(v, int) else v for v in st],
                                'steps': [[hex(v) if isinstance(v, int) else v for v in s] for s in seq]})
                    res['mismatches'].append(bad)
                    break
            res['baseReads'] += len(b.w.base_reads)
        except (Stop, AStop) as e:
            res['errors'].append({'seq': qi, 'error': str(e)})
            if len(res['errors']) > 30:
                break
    res['visited'] = len(model.visited)
    res['stubbed'] = sorted(model.stubbed)
    res['elapsed'] = time.time() - res['started']
    json.dump(res, open(out, 'w'), indent=1)
    print(res['target'], fault, {k: res[k] for k in ('sequences', 'reads', 'stores', 'reverts', 'committedChecks', 'dirtyChecks', 'newAccountSteps', 'baseReads')},
          'mismatches', len(res['mismatches']), 'errors', len(res['errors']), (res['errors'][:1] or [''])[0])
    return res


if __name__ == '__main__':
    run(sys.argv[1].split('-')[-1], int(sys.argv[2]), sys.argv[3])
