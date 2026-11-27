"""Cycle 33 (theme-persistent-storage-binary-lift), task 2 (L-1246): the persistent storage path of the shipped bor
v2.11.2 and avalanchego v1.15.3 binaries (cycle 31 downloads under cycles/031/theme-go-family-binary-lift.work/dl,
read as data only, never executed) run in the cycle 31 x86-64 and AArch64 models, against tools/opdiff/pyevm.py.

This extends cycles/032/theme-go-binaries-storage-journal.work/scripts/stgo.py (bsc only) with per-build StateDB and
stateObject offsets. Every offset below was read from the disassembly of the build (dis/st-<target>.txt in this work
directory; see the comments). Sequences, the reference, the checks and the seed (32_1226_02) are stgo.py's, unchanged,
so the case mix equals the cycle 32 bsc run: a slot written back to its original value, a slot written twice in one
frame, a slot first read after an inner revert, an account first touched inside a frame.

Targets:
  bor-amd64, bor-arm64          (*state.StateDB) with mvHashmap (StateDB+0x78) nil: the path a block import or eth_call
                                takes outside BlockSTM.
  bormv-amd64, bormv-arm64      the same StateDB with a non-nil mvHashmap, as a BlockSTM worker runs it. The call
                                blockstm.(*MVHashMap).Read is stubbed: it returns depIdx = -1, incarnation = -1, the
                                MVReadResultNone result, which is what the store returns when no lower transaction
                                index of the block has written the key. The worker then reads its own base state through
                                the closure, as in the binary. Writes go to the worker's own writeMap; they reach the
                                MVHashMap only through FlushMVWriteSet after the transaction ends (see the research file).
  avax-amd64, avax-arm64        libevm (*state.StateDB) of avalanchego v1.15.3; the StateDB the coreth/subnet-evm
                                interpreter wraps.
usage: python3 -I stgo2.py <target> <nseq> <out.json> [fault]
"""
import json, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
C32 = '/home/user/v4-core/research/network-risk/cycles/032/theme-go-binaries-storage-journal.work/scripts'
sys.path.insert(0, C32)
import tsgo as T
from tsgo import Stop, AStop, G, targets, XProg, AProg, rewrite_rip
import stgo as SG

GE = 'github.com/ethereum/go-ethereum/'
LE = 'github.com/ava-labs/libevm/'

# per build: StateDB field offsets and stateObject offsets, read from the disassembly
CONF = {
    # bor v2.11.2: getStateObject.func1 reads stateObjects at +0x58 (mapaccess1, mapassign after newObject),
    # stateObjectsDestruct +0x60, journal pointer +0x120 (journal.dirties at journal+0x18), reader itab/data +0x18/+0x20
    # (Account at itab+0x18, Storage at itab+0x30), flat diff +0x148 (nil), prefetcher +0x10 (nil), mvHashmap +0x78.
    # (*stateObject).GetCommittedState: mutex +0xe0, originStorage +0xe8, pendingStorage +0xf8; SetState: dirtyStorage +0xf0.
    'bor': dict(tgt='bor', P=GE, cfg='bor', objmap=0x58, maps=[0x60, 0x68, 0x70], jptr=0x120, reader=0x18,
                acct=0x18, stor=0x30, origin=0xe8, dirty=0xf0, pending=0xf8, mv=None),
    'bormv': dict(tgt='bor', P=GE, cfg='bor', objmap=0x58, maps=[0x60, 0x68, 0x70], jptr=0x120, reader=0x18,
                  acct=0x18, stor=0x30, origin=0xe8, dirty=0xf0, pending=0xf8, mv=0x78),
}


class SModel2(SG.SModel):
    def _closure(self, roots, text_patch):
        # tsgo's closure follows direct calls; here function values loaded by address (closures such as
        # getStateObject.func1 that the binary calls through a register) are followed as well
        import re
        want, seen, texts = list(roots), set(), {}
        stubaddr = {self.fns[n][0] for n in self.stub_names}
        P = self.k['P']
        while want:
            n = want.pop()
            if n in seen or n not in self.fns:
                continue
            seen.add(n)
            txt = G.disasm(self.bin, self.arch, [self.fns[n]])
            texts[n] = txt
            for m in re.finditer(r'\b(?:call|bl)\s+(?:0x)?([0-9a-f]+)\s*<([^>]+)>', txt):
                a = int(m.group(1), 16)
                callee = self.byaddr.get(a)
                if callee is None:
                    callee = re.sub(r'\+0x[0-9a-f]+$', '', m.group(2))
                if a in stubaddr or callee in self.stub_names or callee.endswith('crypto.Keccak256Hash') or \
                        callee.startswith('golang.org/x/crypto/sha3.(*state).'):
                    continue
                if callee.startswith('runtime.') and not callee.startswith(T.INCLUDE_RT):
                    continue
                if callee.startswith(('fmt.', 'sync.', 'internal/', 'reflect.', 'log', 'errors.', P + 'log.', P + 'metrics.')):
                    continue
                want.append(callee)
            refs = [int(m.group(1), 16) for m in re.finditer(r'(?:#|//)\s*(?:0x)?([0-9a-f]+)\s*<([^>+]+)>', txt)]
            page = {}
            for l in txt.splitlines():
                ma = re.search(r'\badrp\s+(x\d+),\s*0x([0-9a-f]+)', l)
                if ma:
                    page[ma.group(1)] = int(ma.group(2), 16); continue
                mb = re.search(r'\badd\s+(x\d+),\s*(x\d+),\s*#0x([0-9a-f]+)', l)
                if mb and mb.group(2) in page:
                    refs.append(page.pop(mb.group(2)) + int(mb.group(3), 16))
            for a in refs:
                nm = self.byaddr.get(a)
                if nm and nm.startswith(P + 'core/') and ('.func' in nm or 'deferwrap' in nm):
                    want.append(nm)
        text = '\n'.join(texts[n] for n in sorted(texts, key=lambda k: self.fns[k][0]))
        if text_patch:
            text = text_patch(text)
        return {n: self.fns[n] for n in texts}, text

    def __init__(self, name, text_patch=None):
        kind, arch = name.rsplit('-', 1)
        self.k = CONF[kind]
        self.kind, self.arch = kind, arch
        self.c = dict(T.CFG[self.k['cfg']])
        self.c['jptr'] = self.k['jptr']
        t = targets.get(self.k['tgt'] + '-' + arch)
        self.bin = t['bin']
        self.img = T.Img(self.bin)
        self.fns = G.fnlist(t['fns'])
        self.byaddr = {v[0]: k for k, v in self.fns.items()}
        self.sym = T.nm_symbols(self.bin)
        P = self.k['P']
        S, V = P + 'core/state.', P + 'core/vm.'
        self.S, self.V = S, V
        self.itab_sdb = self.sym['go:itab.*%score/state.StateDB,%score/vm.StateDB' % (P, P)]
        self.t_sc = None
        roots = [V + 'opSload', V + 'opSstore', S + '(*StateDB).GetCommittedState', S + '(*StateDB).Snapshot',
                 S + '(*StateDB).RevertToSnapshot']
        extra = set()
        for k, v in self.sym.items():
            if k.startswith('go:itab.') and k.endswith(',%score/state.journalEntry' % P) and \
                    ('storageChange' in k or 'createObjectChange' in k):
                for i in range(3):
                    a = self.img.read(v + 0x18 + 8 * i, 8)
                    if a in self.byaddr:
                        extra.add(self.byaddr[a])
        for i in range(160):
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

        def lock(cpu):
            self.stubbed.add('internal/sync.(*Mutex).Lock')
            p, = self.regs(cpu, 1)
            if self.rd(cpu, p, 4) != 0:
                raise Stop('Lock on a held mutex')
            self.wr(cpu, p, 4, 1)

        def mvread(cpu):
            # (*MVHashMap).Read(k Key, txIdx int) MVReadResult: return {depIdx: -1, incarnation: -1, value: nil}
            self.stubbed.add('blockstm.(*MVHashMap).Read')
            w.mvreads = getattr(w, 'mvreads', 0) + 1
            self.ret(cpu, (1 << 64) - 1, (1 << 64) - 1, 0, 0)
            if self.arch == 'amd64':
                cpu.r['rdi'] = 0

        def k256(cpu):
            # crypto.Keccak256Hash(data ...[]byte) common.Hash, reached only from newObject for the address hash of a
            # new account; the [32]byte result is returned on the stack (first result slot)
            self.stubbed.add('crypto.Keccak256Hash')
            p, n = self.regs(cpu, 2)
            data = b''
            for i in range(n):
                sp_, sl = self.rd(cpu, p + 24 * i, 8), self.rd(cpu, p + 24 * i + 8, 8)
                data += self.rbytes(cpu, sp_, sl)
            sp = cpu.r['rsp'] if self.arch == 'amd64' else cpu.x[31]
            self.wbytes(cpu, sp + (0 if self.arch == 'amd64' else 8), SG.keccak(data))

        def mclone(cpu):
            # internal/runtime/maps.(*Map).Clone(m *Map, typ *MapType) *Map, reached through maps.clone from
            # Storage.Copy when a BlockSTM worker deep-copies a base state object: a new handle with copies of every
            # element
            self.stubbed.add('maps.(*Map).Clone')
            h, t = self.regs(cpu, 2)
            src = w.maps.get(h, {}) if h else {}
            es = w.elemsize(t)
            n = w.newmap()
            for k, v in src.items():
                a = w.alloc(es); self.wbytes(cpu, a, self.rbytes(cpu, v, es)); w.maps[n][k] = a
            w.setlen(n)
            self.ret(cpu, n)

        for n, fn in (('internal/sync.(*Mutex).Lock', lock), ('internal/runtime/maps.(*Map).Clone', mclone), (GE + 'core/blockstm.(*MVHashMap).Read', mvread),
                      (self.k['P'] + 'crypto.Keccak256Hash', k256)):
            if n in f:
                ext[f[n][0]] = fn
        return ext


class SBin2(SG.SBin):
    def __init__(self, model, base, base_accounts):
        K = model.k
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
        m.wr(c, T.STATEDB + K['jptr'], 8, T.JOURNAL)
        m.wr(c, T.JOURNAL + 0x18, 8, self.w.newmap())
        m.wr(c, T.STATEDB + K['reader'], 8, SG.READERITAB)
        m.wr(c, T.STATEDB + K['reader'] + 8, 8, T.BASE + 0x43000)
        m.wr(c, SG.READERITAB + K['acct'], 8, SG.FAKE + 0x18)
        m.wr(c, SG.READERITAB + K['stor'], 8, SG.FAKE + 0x38)
        if K['mv']:
            m.wr(c, T.STATEDB + K['mv'], 8, T.BASE + 0x44000)  # opaque non-nil *MVHashMap, only passed to the stub
        self.objmap = self.w.newmap()
        m.wr(c, T.STATEDB + K['objmap'], 8, self.objmap)
        for o in K['maps']:
            m.wr(c, T.STATEDB + o, 8, self.w.newmap())
        for i, a in enumerate(sorted(base_accounts)):
            o = SG.OBJ[i]
            m.wr(c, o, 8, T.STATEDB)
            m.wbytes(c, o + 8, a.to_bytes(20, 'big'))
            for off in (K['origin'], K['dirty'], K['pending']):
                m.wr(c, o + off, 8, self.w.newmap())
            self.w.maps[self.objmap][a.to_bytes(20, 'big')] = self._box(o)
        m.wr(c, T.SCOPE + 8, 8, T.STACKOBJ)
        m.wr(c, T.SCOPE + 0x10, 8, T.CONTRACT)
        L = C['layout']
        if L == 'arena':
            m.wr(c, T.STACKOBJ + 0x10, 8, T.ARENA)
            m.wr(c, T.ARENA, 8, T.DATA)
            m.wr(c, T.ARENA + 8, 8, T.NSLOT)
        if C['interp']:
            m.wr(c, T.INTERP, 8, T.EVM)
            m.wr(c, T.CONTRACT + 0x28, 8, model.itab_acct)
            m.wr(c, T.CONTRACT + 0x30, 8, T.ADDRBUF)
        self.snaps, self.jl = [], []
        self.sdbname = '(*StateDB)'

    def dirty(self, addr):
        o = self.obj(addr)
        if not o:
            return None
        h = self.m.rd(self.c, o + self.m.k['dirty'], 8)
        return {int.from_bytes(k, 'big'): int.from_bytes(self.m.rbytes(self.c, v, 32), 'big') for k, v in self.w.maps.get(h, {}).items()}

    # Bin._stack / _top / _addr / _arg2 of tsgo handle the bor 'fixed' and avalanche 'slice' layouts
    _stack = T.Bin._stack
    _top = T.Bin._top
    _addr = T.Bin._addr
    _arg2 = T.Bin._arg2

    def sst(self, a, s, v):
        self._addr(a)
        n, base = self._stack([v, s])
        r = self.m.call(self.c, self.m.fns[self.m.V + 'opSstore'][0], [T.PCPTR, self._arg2(), T.SCOPE])
        if any(r): raise Stop('opSstore returned %s' % (r,))
        if self._top() != n - 2: raise Stop('stack top after SSTORE')

    def sld(self, a, s):
        self._addr(a)
        n, base = self._stack([s])
        r = self.m.call(self.c, self.m.fns[self.m.V + 'opSload'][0], [T.PCPTR, self._arg2(), T.SCOPE])
        if any(r): raise Stop('opSload returned %s' % (r,))
        if self._top() != n: raise Stop('stack top after SLOAD')
        return self.m.rd(self.c, base + 32 * (n - 1), 32)


def run(name, nseq, out, text_patch=None, fault='none'):
    SG.SModel = lambda arch, tp=None: SModel2(name, tp)
    SG.SBin = SBin2
    res = SG.run(name.split('-')[-1], nseq, out, text_patch, fault)
    res['target'] = name
    json.dump(res, open(out, 'w'), indent=1)
    return res




# ---------------------------------------------------------------------------------------------------------------
# bor v2.11.2 ParallelStateDB, the BlockSTM V2 worker state ('borpar-amd64', 'borpar-arm64').
# Offsets read from dis/par-bor-<arch>.txt: base *SafeBase +0x10, store *MVStore +0x20, localStorage +0x38
# (map[Address]map[Hash]Hash), journalEntries slice +0xc8/+0xd0/+0xd8, trackReads +0x110, priorDestructedAt caches
# +0x1b0/+0x1b8, committedCache +0x1c0, base read error +0x250.
# Stubs: blockstm.(*MVStore).ReadVersionFull returns (nil, -1, 0, false, false): no transaction with a lower index
# in the block has written the key, which is what the store returns for the first transaction of a block and for
# every key no earlier transaction wrote. (*SafeBase).GetState returns the base word and a nil error; it is the
# mutex-guarded read of the pre-block StateDB and plays the role of reader.Storage in the serial path.
# Checks: every SLOAD equals pyevm; GetCommittedState equals the value at transaction start; after every step the
# binary's localStorage of each address equals the write set the journal must leave (every SSTORE not undone by a
# revert, kept even when it equals the original value, as SetState and FlushToMVStore treat it); the journal length
# after each revert equals the length at the snapshot.
PAR = dict(base=0x10, store=0x20, local=0x38, jptr=0xc8, jlen=0xd0, track=0x110, maps=[0x1b0, 0x1b8, 0x1c0])


class SModelPar(SModel2):
    def __init__(self, name, text_patch=None, track=True):
        kind, arch = name.rsplit('-', 1)
        self.k = dict(CONF['bor'])
        self.track = track
        self.kind, self.arch = kind, arch
        self.c = dict(T.CFG['bor-par'])
        t = targets.get('bor-' + arch)
        self.bin = t['bin']
        self.img = T.Img(self.bin)
        self.fns = G.fnlist(t['fns'])
        self.byaddr = {v[0]: k for k, v in self.fns.items()}
        self.sym = T.nm_symbols(self.bin)
        P = GE
        S, V = P + 'core/state.', P + 'core/vm.'
        self.S, self.V = S, V
        self.itab_sdb = self.sym['go:itab.*%score/state.ParallelStateDB,%score/vm.StateDB' % (P, P)]
        self.t_sc = None
        roots = [V + 'opSload', V + 'opSstore', S + '(*ParallelStateDB).GetCommittedState', S + '(*ParallelStateDB).Snapshot',
                 S + '(*ParallelStateDB).RevertToSnapshot']
        for i in range(160):
            a = self.img.read(self.itab_sdb + 0x18 + 8 * i, 8)
            nm = self.byaddr.get(a, '')
            if nm.endswith(('.GetState', '.SetState', '.GetCommittedState', '.GetStateAndCommittedState')):
                roots.append(nm)
        self.roots = roots
        self.stub_names = [n for n in T.STUBS if n in self.fns]
        self.ranges, self.text = self._closure(self.roots, text_patch)
        self.prog = XProg(rewrite_rip(self.text)) if arch == 'amd64' else AProg([self.text])
        self.visited = set()
        self.stubbed = set()

    def externs(self, w):
        ext = SModel2.externs(self, w)
        f = self.fns

        def sp(cpu):
            return cpu.r['rsp'] if self.arch == 'amd64' else cpu.x[31]

        def rvf(cpu):
            self.stubbed.add('blockstm.(*MVStore).ReadVersionFull')
            w.mvreads = getattr(w, 'mvreads', 0) + 1
            if self.arch == 'amd64':
                for k, v in zip(('rax', 'rbx', 'rcx', 'rdi', 'rsi', 'r8'), (0, 0, (1 << 64) - 1, 0, 0, 0)):
                    cpu.r[k] = v
            else:
                for i, v in enumerate((0, 0, (1 << 64) - 1, 0, 0, 0)):
                    cpu.x[i] = v

        def sbget(cpu):
            # (*SafeBase).GetState(addr Address, key Hash) (Hash, error): arrays on the stack, Hash result after them
            self.stubbed.add('(*SafeBase).GetState')
            base = sp(cpu) + (0 if self.arch == 'amd64' else 8)
            addr = int.from_bytes(self.rbytes(cpu, base, 20), 'big')
            key = int.from_bytes(self.rbytes(cpu, base + 0x14, 32), 'big')
            w.base_reads.append(('slot', addr, key))
            v = w.base.get((addr, key), 0)
            self.wbytes(cpu, base + 0x38, v.to_bytes(32, 'big'))
            self.ret(cpu, 0, 0, 0)

        for n, fn in ((GE + 'core/blockstm.(*MVStore).ReadVersionFull', rvf), (GE + 'core/state.(*SafeBase).GetState', sbget)):
            if n in f:
                ext[f[n][0]] = fn
        return ext

    def _closure(self, roots, text_patch):
        # SafeBase.GetState and MVStore.ReadVersionFull are stubs: keep them out of the program text
        keep = self.stub_names
        self.stub_names = keep + [GE + 'core/state.(*SafeBase).GetState', GE + 'core/blockstm.(*MVStore).ReadVersionFull']
        r = SModel2._closure(self, roots, text_patch)
        self.stub_names = keep
        return r


class SBinPar(SG.SBin):
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
        m.wr(c, T.STATEDB + PAR['base'], 8, T.BASE + 0x43000)   # opaque *SafeBase, only passed to the stub
        m.wr(c, T.STATEDB + PAR['store'], 8, T.BASE + 0x44000)  # opaque *MVStore, only passed to the stub
        self.local = self.w.newmap()
        m.wr(c, T.STATEDB + PAR['local'], 8, self.local)
        m.wr(c, T.STATEDB + C['tmap'], 8, self.w.newmap())
        m.wr(c, T.STATEDB + PAR['track'], 1, 1 if model.track else 0)
        m.wr(c, T.SCOPE + 8, 8, T.STACKOBJ)
        m.wr(c, T.SCOPE + 0x10, 8, T.CONTRACT)
        self.snaps, self.jl = [], []
        self.sdbname = '(*ParallelStateDB)'

    _stack = T.Bin._stack
    _top = T.Bin._top
    _addr = T.Bin._addr
    _arg2 = T.Bin._arg2
    sst = SBin2.sst
    sld = SBin2.sld

    def dirty(self, addr):
        d = self.w.maps[self.local]
        k = addr.to_bytes(20, 'big')
        if k not in d:
            return None
        h = self.m.rd(self.c, d[k], 8)
        return {int.from_bytes(kk, 'big'): int.from_bytes(self.m.rbytes(self.c, v, 32), 'big') for kk, v in self.w.maps.get(h, {}).items()}

    def committed(self, a, s):
        m, c = self.m, self.c
        top = T.SP_TOP
        o = 0 if m.arch == 'amd64' else 8
        m.wbytes(c, top + o, a.to_bytes(20, 'big')); m.wbytes(c, top + o + 0x14, s.to_bytes(32, 'big'))
        m.wbytes(c, top + o + 0x38, b'\xa5' * 32)
        m.call(c, m.fns[GE + 'core/state.(*ParallelStateDB).GetCommittedState'][0], [T.STATEDB])
        return int.from_bytes(m.rbytes(c, top + o + 0x38, 32), 'big')

    def jlen(self): return self.m.rd(self.c, T.STATEDB + PAR['jlen'], 8)

    def rev(self):
        T.Bin.rev(self)
        j = self.jl.pop()
        if self.jlen() != j: raise Stop('journal length %d after revert, %d at snapshot' % (self.jlen(), j))


def run_par(name, nseq, out, text_patch=None, fault='none'):
    """stgo.run's loop with the write-set check of a ParallelStateDB in place of the dirtyStorage check."""
    import gc
    model = SModelPar(name, text_patch)
    rnd = random.Random(SG.SEED)
    res = {'target': name, 'fault': fault, 'seed': SG.SEED, 'functions': sorted(model.ranges), 'sequences': 0,
           'steps': 0, 'reads': 0, 'stores': 0, 'reverts': 0, 'committedChecks': 0, 'writeSetChecks': 0,
           'newAccountSteps': 0, 'baseReads': 0, 'mvReads': 0, 'mismatches': [], 'errors': [], 'started': time.time()}
    seqs = []
    for q in range(nseq + 5):
        base = {}
        for a in (SG.PM, SG.OTHER):
            for s in SG.SLOTS:
                if rnd.random() < 0.6:
                    base[(a, s)] = rnd.choice(SG.VALUES[1:]) if rnd.random() < 0.6 else rnd.getrandbits(256)
        seqs.append(base)
    fx = list(SG.fixed(seqs[0]))
    hx = lambda st: [hex(v) if isinstance(v, int) else v for v in st]
    for qi, base in enumerate(seqs):
        if qi % 200 == 0:
            gc.collect()
        seq = fx[qi] if qi < len(fx) else SG.gen(rnd, base)
        res['sequences'] += 1
        ref = SG.Ref(base)
        try:
            b = SBinPar(model, base, {SG.PM, SG.OTHER})
            orig = dict(base)
            ws, wstack = {}, []
            bad = None
            for st in seq:
                res['steps'] += 1
                if st[0] in ('st', 'ld') and st[1] == SG.NEWACCT:
                    res['newAccountSteps'] += 1
                if st[0] == 'st':
                    ref.st(*st[1:]); b.sst(*st[1:]); res['stores'] += 1
                    ws[(st[1], st[2])] = st[3]
                elif st[0] == 'ld':
                    x, y = ref.ld(*st[1:]), b.sld(*st[1:]); res['reads'] += 1
                    if x != y:
                        bad = {'at': hx(st), 'ref': hex(x), 'bin': hex(y)}
                elif st[0] == 'snap':
                    ref.snap(); b.snap(); wstack.append(dict(ws))
                elif st[0] == 'rev':
                    ref.rev(); b.rev(); res['reverts'] += 1; ws = wstack.pop()
                else:
                    ref.commit(); b.commit(); wstack.pop()
                if not bad:
                    for a in (SG.PM, SG.OTHER, SG.NEWACCT):
                        d = b.dirty(a) or {}
                        want = {s: v for (aa, s), v in ws.items() if aa == a}
                        res['writeSetChecks'] += 1
                        if d != want:
                            bad = {'at': hx(st), 'writeSet': hex(a), 'bin': {hex(k): hex(v) for k, v in d.items()},
                                   'ref': {hex(k): hex(v) for k, v in want.items()}}
                            break
                if not bad and st[0] in ('st', 'ld'):
                    res['committedChecks'] += 1
                    x = b.committed(st[1], st[2])
                    if x != orig.get((st[1], st[2]), 0):
                        bad = {'at': hx(st), 'committed': hex(st[2]), 'bin': hex(x), 'ref': hex(orig.get((st[1], st[2]), 0))}
                if bad:
                    bad.update({'seq': qi, 'steps': [hx(s) for s in seq]})
                    res['mismatches'].append(bad)
                    break
            res['baseReads'] += len(b.w.base_reads)
            res['mvReads'] += getattr(b.w, 'mvreads', 0)
        except (Stop, AStop) as e:
            res['errors'].append({'seq': qi, 'error': str(e)})
            if len(res['errors']) > 30:
                break
    res['visited'] = len(model.visited)
    res['stubbed'] = sorted(model.stubbed)
    res['elapsed'] = time.time() - res['started']
    json.dump(res, open(out, 'w'), indent=1)
    print(name, fault, {k: res[k] for k in ('sequences', 'reads', 'stores', 'reverts', 'committedChecks', 'writeSetChecks',
                                            'newAccountSteps', 'baseReads', 'mvReads')},
          'mismatches', len(res['mismatches']), 'errors', len(res['errors']), (res['errors'][:1] or [''])[0])
    return res




# ---------------------------------------------------------------------------------------------------------------
# avalanchego v1.15.3 ('avax-amd64', 'avax-arm64'): libevm v1.13.15-0.20261028200218-d398bc4dbe41 core/state under the
# C-Chain wrapper vms/saevm/cchain/libevm/extstate.StateDB, the only type besides *state.StateDB with a vm.StateDB itab.
# The EVM holds the wrapper's itab; the wrapper embeds *state.StateDB at +0 and preAP1 (false, post-AP1) at +0x20.
# The C-Chain hook is registered as RegisterExtras(partitionStateKeysHook{}) does: core/state.registeredExtras (a
# pointer in .bss) points to {itab partitionStateKeysHook/StateDBHooks, data &runtime.zerobase}, so transformStateKey and
# the hook run from the binary.
# Offsets from dis/st-avax-amd64.txt: StateDB.db (Database itab/data) +0/+8 (OpenStorageTrie at itab+0x38), prefetcher
# +0x10 (nil), trie +0x18/+0x20 (GetAccount at itab+0x30), snap +0x48 (nil: the trie path), stateObjects +0x98,
# stateObjectsDestruct +0xb0, journal pointer +0x120 (entries +0/+8, dirties +0x18). stateObject: db +0, address +8,
# trie +0x98/+0xa0 (GetStorage at itab+0x40), originStorage +0xc0, pendingStorage +0xc8, dirtyStorage +0xd0.
# Stubs: the account trie's GetAccount returns (nil, nil) (no account) and is only reached for the new account; the
# storage trie's GetStorage(addr, key []byte) returns the trimmed big-endian word of the base state for the physical
# key the binary asks for, as StateTrie.GetStorage returns the content of the RLP string; Database.OpenStorageTrie
# returns that storage trie (reached for the new account only).
# Reference: pyevm with every SLOAD and SSTORE key passed through key[0] &^= 1 (bit 248 cleared), the base state
# defined on physical keys. Dirty check in the libevm 1.13 form: dirtyStorage holds every slot that saw a
# value-changing SetState in the transaction, reverted or not, with its current value.
AVX = {'amd64': dict(regx=0x45a0258, hookitab=0x25cb500, zerobase=0x461f780),
       'arm64': dict(regx=0x415b4d8, hookitab=0x21edd60, zerobase=0x4221b60)}
B248 = 1 << 248
AVX_STITAB, AVX_DBITAB, AVX_WRAP, AVX_REG = T.BASE + 0x47000, T.BASE + 0x47100, T.BASE + 0x45000, T.BASE + 0x46000


class SModelAvax(SModel2):
    def __init__(self, name, text_patch=None, hook=True):
        kind, arch = name.rsplit('-', 1)
        self.k = dict(objmap=0x98, maps=[], jptr=0x120, reader=0x18, acct=0x30, stor=None,
                      origin=0xc0, dirty=0xd0, pending=0xc8, trie=0x98, mv=None, P=LE)
        self.hook = hook
        self.kind, self.arch = kind, arch
        self.c = dict(T.CFG['avax'])
        t = targets.get('avax-' + arch)
        self.bin = t['bin']
        self.img = T.Img(self.bin)
        self.fns = G.fnlist(t['fns'])
        self.byaddr = {v[0]: k for k, v in self.fns.items()}
        self.sym = T.nm_symbols(self.bin)
        S, V = LE + 'core/state.', LE + 'core/vm.'
        self.S, self.V = S, V
        X = 'github.com/ava-labs/avalanchego/vms/saevm/cchain/libevm/extstate.'
        self.X = X
        self.itab_sdb = self.sym['go:itab.*%sStateDB,%score/vm.StateDB' % (X, LE)]
        self.itab_acct = self.sym['go:itab.%score/vm.AccountRef,%score/vm.ContractRef' % (LE, LE)]
        self.t_sc = None
        roots = [V + 'opSload', V + 'opSstore', X + '(*StateDB).GetCommittedState', S + '(*StateDB).Snapshot',
                 S + '(*StateDB).RevertToSnapshot', self.byaddr[self.img.read(AVX[arch]['hookitab'] + 0x18, 8)],
                 self.byaddr[self.img.read(self.itab_acct + 0x18, 8)]]
        for k, v in self.sym.items():
            if k.startswith('go:itab.') and k.endswith(',%score/state.journalEntry' % LE) and \
                    ('storageChange' in k or 'createObjectChange' in k):
                for i in range(3):
                    a = self.img.read(v + 0x18 + 8 * i, 8)
                    if a in self.byaddr:
                        roots.append(self.byaddr[a])
        for i in range(160):
            a = self.img.read(self.itab_sdb + 0x18 + 8 * i, 8)
            nm = self.byaddr.get(a, '')
            if nm.endswith(('.GetState', '.SetState', '.GetCommittedState')):
                roots.append(nm)
        self.roots = roots
        self.stub_names = [n for n in T.STUBS if n in self.fns]
        self.ranges, self.text = self._closure(self.roots, text_patch)
        self.prog = XProg(rewrite_rip(self.text)) if arch == 'amd64' else AProg([self.text])
        self.visited = set()
        self.stubbed = set()

    def cpu(self, w):
        c = SModel2.cpu(self, w)
        if self.hook:
            r = AVX[self.arch]['regx']
            if self.arch == 'amd64':
                super(T.models.CPU2, c).write(r, 8, AVX_REG)
            else:
                c.m.add(r, 8)
                c.m.write(r, 8, AVX_REG)
        return c

    def externs(self, w):
        ext = SModel2.externs(self, w)

        def sp(cpu):
            return cpu.r['rsp'] if self.arch == 'amd64' else cpu.x[31]

        def getstorage(cpu):
            self.stubbed.add('Trie.GetStorage')
            base = sp(cpu) + (0 if self.arch == 'amd64' else 8)
            addr = int.from_bytes(self.rbytes(cpu, base, 20), 'big')
            _, kp, kl = self.regs(cpu, 3)
            if kl != 32:
                raise Stop('GetStorage key length %d' % kl)
            key = int.from_bytes(self.rbytes(cpu, kp, 32), 'big')
            w.base_reads.append(('slot', addr, key))
            v = w.base.get((addr, key), 0)
            b = v.to_bytes(32, 'big').lstrip(b'\0')
            a = w.alloc(32); self.wbytes(cpu, a, b)
            self.ret(cpu, a, len(b), 32, 0, 0)
            if self.arch == 'amd64':
                cpu.r['rdi'] = 0; cpu.r['rsi'] = 0

        def opentrie(cpu):
            self.stubbed.add('Database.OpenStorageTrie')
            self.ret(cpu, AVX_STITAB, T.BASE + 0x48000, 0, 0)
            if self.arch == 'amd64':
                cpu.r['rdi'] = 0

        itabs = {}
        for k, v in self.sym.items():
            if k.startswith('go:itab.'):
                itabs[(self.img.read(v, 8), self.img.read(v + 8, 8))] = v

        def tassert(cpu):
            # runtime.typeAssert(s *abi.TypeAssert, t *_type) *itab: the slow path behind the inline itab cache (the
            # cache in .data reads empty); returns the itab the linker emitted for (s.Inter, t)
            self.stubbed.add('runtime.typeAssert')
            sa, t = self.regs(cpu, 2)
            inter = self.img.read(sa + 8, 8)
            if (inter, t) not in itabs:
                raise Stop('typeAssert without a static itab')
            self.ret(cpu, itabs[(inter, t)])

        hs = {}

        def swrite(cpu):
            # golang.org/x/crypto/sha3.(*state).Write and Read: the Keccak-256 of the 20-byte address that newObject
            # stores as addrHash (Python keccak; the shipped routine is assembly the model does not run)
            self.stubbed.add('sha3.(*state).Write')
            st, p, n = self.regs(cpu, 3)
            hs[st] = hs.get(st, b'') + self.rbytes(cpu, p, n)
            self.ret(cpu, n, 0, 0)

        def sread(cpu):
            self.stubbed.add('sha3.(*state).Read')
            st, p, n = self.regs(cpu, 3)
            self.wbytes(cpu, p, SG.keccak(hs.pop(st, b''))[:n])
            self.ret(cpu, n, 0, 0)

        for n, fn in (('golang.org/x/crypto/sha3.(*state).Write', swrite), ('golang.org/x/crypto/sha3.(*state).Read', sread)):
            if n in self.fns:
                ext[self.fns[n][0]] = fn
        if 'runtime.typeAssert' in self.fns:
            ext[self.fns['runtime.typeAssert'][0]] = tassert
        ext[SG.FAKE + 0x40] = getstorage
        ext[SG.FAKE + 0x58] = opentrie
        return ext


class SBinAvax(SBin2):
    def __init__(self, model, base, base_accounts):
        K = model.k
        self.m = model
        self.w = T.World(model)
        self.w.base = base
        self.w.base_accounts = base_accounts
        self.w.base_reads = []
        self.c = model.cpu(self.w)
        self.w.cpu = self.c
        m, c, C = model, self.c, model.c
        m.wr(c, T.EVM + C['evmSdb'], 8, model.itab_sdb)
        m.wr(c, T.EVM + C['evmSdb'] + 8, 8, AVX_WRAP)
        m.wr(c, AVX_WRAP, 8, T.STATEDB)
        m.wr(c, AVX_REG, 8, AVX[model.arch]['hookitab'])
        m.wr(c, AVX_REG + 8, 8, AVX[model.arch]['zerobase'])
        m.wr(c, T.STATEDB, 8, AVX_DBITAB)
        m.wr(c, T.STATEDB + 8, 8, T.BASE + 0x49000)
        m.wr(c, AVX_DBITAB + 0x38, 8, SG.FAKE + 0x58)
        m.wr(c, T.STATEDB + K['jptr'], 8, T.JOURNAL)
        m.wr(c, T.JOURNAL + 0x18, 8, self.w.newmap())
        m.wr(c, T.STATEDB + K['reader'], 8, SG.READERITAB)
        m.wr(c, T.STATEDB + K['reader'] + 8, 8, T.BASE + 0x43000)
        m.wr(c, SG.READERITAB + K['acct'], 8, SG.FAKE + 0x18)
        m.wr(c, AVX_STITAB + 0x40, 8, SG.FAKE + 0x40)
        self.objmap = self.w.newmap()
        m.wr(c, T.STATEDB + K['objmap'], 8, self.objmap)
        for i, a in enumerate(sorted(base_accounts)):
            o = SG.OBJ[i]
            m.wr(c, o, 8, T.STATEDB)
            m.wbytes(c, o + 8, a.to_bytes(20, 'big'))
            m.wr(c, o + K['trie'], 8, AVX_STITAB)
            m.wr(c, o + K['trie'] + 8, 8, T.BASE + 0x48000)
            for off in (K['origin'], K['dirty'], K['pending']):
                m.wr(c, o + off, 8, self.w.newmap())
            self.w.maps[self.objmap][a.to_bytes(20, 'big')] = self._box(o)
        m.wr(c, T.SCOPE + 8, 8, T.STACKOBJ)
        m.wr(c, T.SCOPE + 0x10, 8, T.CONTRACT)
        m.wr(c, T.INTERP, 8, T.EVM)
        m.wr(c, T.CONTRACT + 0x28, 8, model.itab_acct)
        m.wr(c, T.CONTRACT + 0x30, 8, T.ADDRBUF)
        self.snaps, self.jl = [], []
        self.sdbname = '(*StateDB)'

    def committed(self, a, s):
        # extstate.(*StateDB).GetCommittedState(addr, key, opts ...StateDBStateOption): receiver and the nil opts
        # slice in registers, addr and key on the stack, the Hash result after them
        m, c = self.m, self.c
        top = T.SP_TOP
        o = 0 if m.arch == 'amd64' else 8
        m.wbytes(c, top + o, a.to_bytes(20, 'big')); m.wbytes(c, top + o + 0x14, s.to_bytes(32, 'big'))
        m.wbytes(c, top + o + 0x38, b'\xa5' * 32)
        m.call(c, m.fns[m.X + '(*StateDB).GetCommittedState'][0], [AVX_WRAP, 0, 0, 0])
        return int.from_bytes(m.rbytes(c, top + o + 0x38, 32), 'big')


def run_avax(name, nseq, out, text_patch=None, fault='none', hook=True):
    import gc
    model = SModelAvax(name, text_patch, hook)
    X = (lambda s: s & ~B248) if hook else (lambda s: s)
    rnd = random.Random(SG.SEED)
    res = {'target': name, 'fault': fault, 'seed': SG.SEED, 'hookRegistered': hook, 'functions': sorted(model.ranges),
           'sequences': 0, 'steps': 0, 'reads': 0, 'stores': 0, 'reverts': 0, 'committedChecks': 0, 'dirtyChecks': 0,
           'newAccountSteps': 0, 'baseReads': 0, 'bit248Steps': 0, 'mismatches': [], 'errors': [], 'started': time.time()}
    seqs = []
    for q in range(nseq + 5):
        base = {}
        for a in (SG.PM, SG.OTHER):
            for s in SG.SLOTS:
                if rnd.random() < 0.6:
                    base[(a, s)] = rnd.choice(SG.VALUES[1:]) if rnd.random() < 0.6 else rnd.getrandbits(256)
        seqs.append(base)
    fx = list(SG.fixed(seqs[0]))
    hx = lambda st: [hex(v) if isinstance(v, int) else v for v in st]
    for qi, base in enumerate(seqs):
        if qi % 200 == 0:
            gc.collect()
        seq = fx[qi] if qi < len(fx) else SG.gen(rnd, base)
        # the generator's base state is drawn on logical keys; the chain stores physical keys. A physical key keeps
        # the value of the logical key with bit 248 clear when both are drawn.
        phys = {}
        for (a, s), v in sorted(base.items(), key=lambda kv: (kv[0][0], kv[0][1] & B248 == 0)):
            phys[(a, X(s))] = v
        res['sequences'] += 1
        ref = SG.Ref(phys)
        try:
            b = SBinAvax(model, phys, {SG.PM, SG.OTHER})
            orig = dict(phys)
            # cycle 33 correction after the first 5,005-sequence run (216 sequences flagged, all on the new account):
            # an account created inside a frame that reverts is removed with its whole dirtyStorage by
            # createObjectChange.revert, so its slots leave the 'ever written' set of the libevm 1.13 dirty rule
            ever, estack, newexists = set(), [], False
            bad = None
            for st in seq:
                res['steps'] += 1
                if st[0] in ('st', 'ld') and st[1] == SG.NEWACCT:
                    res['newAccountSteps'] += 1
                if st[0] in ('st', 'ld') and st[2] & B248:
                    res['bit248Steps'] += 1
                if st[0] == 'st':
                    a, s, v = st[1:]
                    if a == SG.NEWACCT:
                        newexists = True
                    if ref.ld(a, X(s)) != v:
                        ever.add((a, X(s)))
                    ref.st(a, X(s), v); b.sst(a, s, v); res['stores'] += 1
                elif st[0] == 'ld':
                    x, y = ref.ld(st[1], X(st[2])), b.sld(st[1], st[2]); res['reads'] += 1
                    if x != y:
                        bad = {'at': hx(st), 'ref': hex(x), 'bin': hex(y)}
                elif st[0] == 'snap':
                    ref.snap(); b.snap(); estack.append(newexists)
                elif st[0] == 'rev':
                    ref.rev(); b.rev(); res['reverts'] += 1
                    newexists = estack.pop()
                    if not newexists:
                        ever = {k for k in ever if k[0] != SG.NEWACCT}
                else:
                    ref.commit(); b.commit(); estack.pop()
                if not bad:
                    for a in (SG.PM, SG.OTHER, SG.NEWACCT):
                        d = b.dirty(a)
                        if d is None:
                            continue
                        want = {s: ref.w.storage.get((a, s), 0) for (aa, s) in ever if aa == a}
                        res['dirtyChecks'] += 1
                        if d != want:
                            bad = {'at': hx(st), 'dirty': hex(a), 'bin': {hex(k): hex(v) for k, v in d.items()},
                                   'ref': {hex(k): hex(v) for k, v in want.items()}}
                            break
                if not bad and st[0] in ('st', 'ld'):
                    res['committedChecks'] += 1
                    x = b.committed(st[1], st[2])
                    if x != orig.get((st[1], X(st[2])), 0):
                        bad = {'at': hx(st), 'committed': hex(st[2]), 'bin': hex(x), 'ref': hex(orig.get((st[1], X(st[2])), 0))}
                if bad:
                    bad.update({'seq': qi, 'steps': [hx(s) for s in seq]})
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
    print(name, fault, {k: res[k] for k in ('sequences', 'reads', 'stores', 'reverts', 'committedChecks', 'dirtyChecks',
                                            'newAccountSteps', 'baseReads', 'bit248Steps')},
          'mismatches', len(res['mismatches']), 'errors', len(res['errors']), (res['errors'][:1] or [''])[0])
    return res


if __name__ == '__main__':
    n = sys.argv[1]
    f = run_par if n.startswith('borpar') else run_avax if n.startswith('avax') else run
    f(n, int(sys.argv[2]), sys.argv[3])
