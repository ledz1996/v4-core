"""Cycle 33 (theme-persistent-storage-binary-lift), task 1 (L-1246): the persistent storage path of the Nitro
v3.13.0-rc.9+b72783f release binaries (cycle 30 extraction under
cycles/030/theme-nitro-binary-arith-lift.work/dl/<arch>/usr/local/bin/nitro, sha256 a142fcbe...3962 amd64 and
ba1fec28...4923 arm64 as recorded in cycles/023/arbitrum-family.work/raw/nitro-binaries.sha256; read as data only)
run in the cycle 31 x86-64 and AArch64 models with the Go runtime map calls stubbed, against tools/opdiff/pyevm.py.

The binaries are stripped: function bounds come from .gopclntab (cycle 30 list build/all-<arch>.txt) and the
StateDB itab is found by scanning for the method pointer, as cycles/031/theme-nitro-binary-storage-lift.work did.

Run from the binary: core/vm.opSload, opSstore, the vm.StateDB itab methods GetState, SetState, GetCommittedState and
GetStateAndCommittedState of *state.StateDB, (*StateDB).Snapshot, RevertToSnapshot, (*journal).revert and every
core/state and core/types/bal function they reach by direct call (getStateObject, getOrNewStateObject, createObject,
newObject, (*stateObject).GetState, getState, GetCommittedState, SetState, setState, (*journal).storageChange,
append, storageChange.revert through the journalEntry itab, createObjectChange.revert, ...).

StateDB offsets (read from dis/st-nitro-<arch>.txt, relabelled with the pclntab names by scripts/ndump.py):
reader itab/data +0x20/+0x28 (Account at itab+0x18, Storage at itab+0x38), stateObjects +0x60,
stateObjectsDestruct +0x68, error +0x78, the EIP-7928 construction block access list pointer +0xe0 (nil, or a live
one in the 'bal' variant), journal pointer +0xf8 (journal: entries +0x8/+0x10/+0x18, dirties +0x20).
stateObject: db +0, address +8, originStorage +0xa0, dirtyStorage +0xa8, pendingStorage +0xb0.
EVM: StateDB interface +0xd8/+0xe0, readOnly +0x1a0 (cycle 31 tsdrive.py).
Sequences, reference, seed (32_1226_02) and checks are cycles/032 stgo.py's, unchanged (geth 1.16 dirty rule: a slot
written back to its original value leaves dirtyStorage).
usage: python3 -I stnitro.py <amd64|arm64|bal-amd64|bal-arm64> <nseq> <out.json> [fault]
"""
import json, os, re, struct, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stgo2 as S2
T, SG, G = S2.T, S2.SG, S2.G
from tsgo import Stop, AStop, XProg, AProg, rewrite_rip

D30 = '/home/user/v4-core/research/network-risk/cycles/030/theme-nitro-binary-arith-lift.work/dl/'
GE = 'github.com/ethereum/go-ethereum/'
ST, VM = GE + 'core/state.', GE + 'core/vm.'
K = dict(objmap=0x60, maps=[0x68], jptr=0xf8, reader=0x20, acct=0x18, stor=0x38, origin=0xa0, dirty=0xa8,
         pending=0xb0, bal=0xe0, mv=None, P=GE)
BALOBJ = T.BASE + 0x4a000
ARBX = T.BASE + 0x4b000


class NModel(S2.SModel2):
    def __init__(self, name, text_patch=None):
        self.bal = name.startswith('bal')
        arch = name.split('-')[-1]
        self.k = dict(K)
        self.kind, self.arch = 'nitro', arch
        self.c = dict(T.CFG['bsc'])  # arena stack layout, contract address at CONTRACT+0x14, as in Nitro (cycle 31)
        self.c['evmSdb'] = 0xd8
        self.bin = D30 + '%s/usr/local/bin/nitro' % arch
        self.img = T.Img(self.bin)
        self.fns = G.fnlist(D30 + 'build/all-%s.txt' % arch)
        self.byaddr = {v[0]: k for k, v in self.fns.items()}
        self.sym = {}
        self.S, self.V = ST, VM
        self.itab_sdb = self._find_itab(ST + '(*StateDB).SetTransientState', 0x1e0)
        self.t_sc = None
        roots = [VM + 'opSload', VM + 'opSstore', ST + '(*StateDB).GetCommittedState', ST + '(*StateDB).Snapshot',
                 ST + '(*StateDB).RevertToSnapshot', ST + '(*journal).revert']
        roots += [n for n in self.fns if re.match(re.escape(ST) + r'\(?\*?(storageChange|createObjectChange|createContractChange)\)?\.', n)]
        for i in range(160):
            a = self.img.read(self.itab_sdb + 0x18 + 8 * i, 8)
            nm = self.byaddr.get(a or 0, '')
            if nm.endswith(('.GetState', '.SetState', '.GetCommittedState', '.GetStateAndCommittedState')):
                roots.append(nm)
        self.roots = roots
        self.stub_names = [n for n in T.STUBS if n in self.fns]
        self.ranges, self.text = self._closure(self.roots, text_patch)
        self.prog = XProg(rewrite_rip(self.text)) if arch == 'amd64' else AProg([self.text])
        self.visited = set()
        self.stubbed = set()

    def _find_itab(self, fn, off):
        t = self.fns[fn][0]
        pat = struct.pack('<Q', t)
        hits = []
        for lo, hi, o in self.img.secs:
            data = self.img.f[o:o + hi - lo]
            i = data.find(pat)
            while i >= 0:
                if i % 8 == 0 and i >= off:
                    hits.append(lo + i - off)
                i = data.find(pat, i + 1)
        assert len(hits) == 1, hits
        return hits[0]


    def externs(self, w):
        ext = S2.SModel2.externs(self, w)
        cache = self.__dict__.setdefault('_tacache', {})

        def tassert(cpu):
            # runtime.typeAssert(s *abi.TypeAssert, t *_type) *itab, the slow path behind the inline cache (which reads
            # empty from .data). Reached from isZombie (journal_arbitrum.go:90-93), entry.(possibleZombie), in
            # (*journal).append and revert. The stub returns the static itab for (s.Inter, t) found by scanning the
            # file, nil when there is none and s.CanFail is set. Only createZombieChange has an isZombie method in this
            # binary (pclntab), and no step here creates one.
            self.stubbed.add('runtime.typeAssert')
            sa, t = self.regs(cpu, 2)
            inter = self.img.read(sa + 8, 8)
            canfail = self.img.read(sa + 0x10, 1)
            if (inter, t) not in cache:
                pat = struct.pack('<QQ', inter, t)
                hit = 0
                for lo, hi, o in self.img.secs:
                    i = self.img.f.find(pat, o, o + hi - lo)
                    if i >= 0 and (i - o) % 8 == 0:
                        hit = lo + i - o
                        break
                cache[(inter, t)] = hit
            r = cache[(inter, t)]
            if not r and not canfail:
                raise Stop('typeAssert without a static itab')
            self.ret(cpu, r)

        ext[self.fns['runtime.typeAssert'][0]] = tassert
        return ext


class NBin(S2.SBin2):
    def __init__(self, model, base, base_accounts):
        S2.SBin2.__init__(self, model, base, base_accounts)
        m, c = model, self.c
        m.wr(c, T.EVM + 0x1a0, 1, 0)
        m.wr(c, T.JOURNAL + 0x18, 8, 0)
        m.wr(c, T.JOURNAL + 0x20, 8, self.w.newmap())
        # Arbitrum-only: StateDB+0 is *arbExtraData, whose first field unexpectedBalanceDelta (*big.Int, zero) the
        # journal copies into every revision and restores on revert (journal.snapshot / revertToSnapshot)
        m.wr(c, T.STATEDB, 8, ARBX)
        m.wr(c, ARBX, 8, ARBX + 0x100)
        self.arbx = ARBX
        if model.bal:
            m.wr(c, T.STATEDB + K['bal'], 8, BALOBJ)
            m.wr(c, BALOBJ, 8, self.w.newmap())  # ConstructionBlockAccessList.Accounts map[Address]*ConstructionAccountAccess

    def jlen(self): return self.m.rd(self.c, T.JOURNAL + 0x10, 8)

    def rev(self):
        T.Bin.rev(self)
        j = self.jl.pop()
        if self.jlen() != j: raise Stop('journal length %d after revert, %d at snapshot' % (self.jlen(), j))
        h = self.m.rd(self.c, T.JOURNAL + 0x20, 8)
        for k, v in self.w.maps[h].items():
            if self.m.rd(self.c, v, 8) == 0:
                raise Stop('dirties entry with count 0 kept')


def run(name, nseq, out, text_patch=None, fault='none'):
    SG.SModel = lambda arch, tp=None: NModel(name, tp)
    SG.SBin = NBin
    res = SG.run(name.split('-')[-1], nseq, out, text_patch, fault)
    res['target'] = 'nitro-' + name
    json.dump(res, open(out, 'w'), indent=1)
    return res


if __name__ == '__main__':
    run(sys.argv[1], int(sys.argv[2]), sys.argv[3])
