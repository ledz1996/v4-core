"""Cycle 39, theme-ethereum-binaries-storage-journal, task 2 (L-1347): the per-frame SLOAD cache of the released
erigon v3.8.2 linux/amd64 binary (cycle 38 download, read as data only, never executed, loaded or dlopened), run in
the x86-64 model on the cycle 36 reentry sequences (a)-(h), t, the random frame trees and the PoolManager reentry
shapes of cycles/036/theme-erigon-main-frame-cache.work/scripts (seqs.py, pmshapes.py).

Run from the binary text (functions disassembled on demand from their nm ranges):
  execution/vm.opSload 0x1df2f00            the handler with the cache arms (instructions.go:765-786)
  (*CallContext).lookupSlot 0x1dfa680        stamp compare and word match (interpreter.go:115-131)
  (*CallContext).memoStorageKey 0x1dfa9a0    key memo for the op
  (*frameSlots).put 0x1dfa820                fill, miss counter, stamp reset (interpreter.go:133-146)
  (*IntraBlockState).ReadStamp 0x1757b40     {len(journal.entries), journal.epoch} (read_paths.go:1813-1818)
  (*EVM).getCallContext 0x1dfab80, (*EVM).putCallContext 0x1dfade0   spare frame and pool hand-off, the clearing
                                             of slots.ok, slots.key and memoGen on reuse (interpreter.go:190-241)
The SSTORE gas phase (operations_acl.go:60-100) is driven from Python in the order it calls these routines:
lookupSlot, and on a miss ReadStamp and frameSlots.put from the binary.

Boundary stubs (Python): (*EVM).internStorageKey (key interning through unique.Make; it returns a distinct handle per
word, as interning does), (*IntraBlockState).GetState (the state read below the cache: it returns the word the
storage holds at that moment), sync.(*Pool).Get/Put (a list), the allocator. The journal length and epoch that
ReadStamp reads are written into the IntraBlockState's journal object in model memory from the cycle 36 journal
model (journal.go push and revert: an entry per change, truncation and epoch+1 on revert), before each binary call.
The interpreter loop's two writes that the cache depends on are done in Python as run() does them: slots.on from
ReadStamp's ok and misses = 0 at frame start (interpreter.go:515-516, vm_run_gen.go:31-32), cacheGen+1 per opcode
(interpreter.go:587, vm_run_gen.go:409). Faults are planted in the binary text (see FAULTS).
"""
import os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gethj as GJ
from x86emu import Stop, M64
C36 = '/home/user/v4-core/research/network-risk/cycles/036/theme-erigon-main-frame-cache.work/scripts'
sys.path.insert(0, C36)
import cachemodel as CM

BIN = GJ.C38 + 'dl/erigon/erigon_v3.8.2_linux_amd64/erigon'
CACHE = os.path.join(os.path.dirname(HERE), 'dis', 'erigon')
EV = 'github.com/erigontech/erigon/execution/vm.'
ST = 'github.com/erigontech/erigon/execution/state.'
CTX_SIZE = 0x8240
TYPE_PTR_CALLCONTEXT = 0x58e3200     # type:*vm.CallContext compared after Pool.Get (0x1dfabfb)

# planted faults in the binary text (pc -> replacement)
FAULTS = {
    # the stamp does not move on a nested write: the journal length read as 0 in lookupSlot (0x1dfa6ac), in opSload's
    # inlined ReadStamp before put (0x1df30da) and in ReadStamp (0x1757b55); only the epoch (reverts) moves it
    'stamp-frozen-len': {0x1dfa6ac: 'xor edx,edx', 0x1df30da: 'xor r10d,r10d', 0x1757b55: 'xor eax,eax'},
    # putCallContext keeps slots.ok across frame reuse: the clearing store at 0x1dfae77 is dropped
    'reuse-keeps-entry': {0x1dfae77: 'nop'},
    # frameSlots.put does not clear ok[] when the stamp changed (0x1dfa856)
    'put-no-reset': {0x1dfa856: 'nop'},
}


def load_fns():
    out = subprocess.run(['nm', '-n', BIN], capture_output=True, text=True).stdout
    syms = []
    for l in out.splitlines():
        p = l.split(None, 2)
        if len(p) == 3 and p[1] in 'tT':
            syms.append((int(p[0], 16), p[2]))
    rng, byname = [], {}
    for (a, n), (b, _) in zip(syms, syms[1:] + [(syms[-1][0] + 0x1000, '')]):
        if b > a:
            rng.append((a, b, n)); byname.setdefault(n, (a, b))
    return byname, rng


class Erigon:
    def __init__(self, fault=None):
        self.byname, rng = load_fns()
        self.img = GJ.Image(BIN)
        self.prog = GJ.LazyProg(rng, binpath=BIN, cache=CACHE)
        self.fault = fault or {}
        self.fault_hits = 0
        self.visited = set()
        self.stubbed = set()

    def fn(self, n): return self.byname[n][0]

    def new(self):
        self.heap = GJ.HEAP0
        ext = {}
        for n, (lo, hi) in self.byname.items():
            if n.startswith('runtime.mallocgc'):
                ext[lo] = self._malloc
        for n in ('runtime.morestack_noctxt.abi0', 'runtime.panicBounds', 'runtime.gcWriteBarrier1', 'runtime.gcWriteBarrier2',
                  'runtime.gcWriteBarrier3', 'runtime.wbZero', 'runtime.wbMove', 'fmt.Sprintf', 'runtime.gopanic'):
            if n in self.byname:
                ext[self.fn(n)] = (lambda c, n=n: (_ for _ in ()).throw(Stop('call ' + n)))
        ext[self.fn(EV + '(*EVM).internStorageKey')] = self._intern
        ext[self.fn(ST + '(*IntraBlockState).GetState')] = self._getstate
        ext[self.fn('sync.(*Pool).Get')] = self._pget
        ext[self.fn('sync.(*Pool).Put')] = self._pput
        self.cpu = GJ.CPU(self.prog, self.img, ext)
        self.cpu.faults_ms = self.fault
        c = self.cpu
        c.write(GJ.GSTRUCT + 0x10, 8, 0); c.write(c.fs - 8, 8, GJ.GSTRUCT)
        self.pool = []; self.handles = {}; self.words = {}
        self.EVM = self.alloc(0x200); self.IBS = self.alloc(0x200); self.JOURNAL = self.alloc(0x40)
        c.write(self.EVM + 0x120, 8, self.IBS)       # evm.intraBlockState (opSload 0x1df2ff7)
        c.write(self.IBS + 0x110, 8, self.JOURNAL)   # ibs.journal (opSload 0x1df30d3)
        c.write(self.EVM + 0x1d0, 8, 0)              # evm.spareFrame (getCallContext 0x1dfab9a)
        self.addrh = {}
        return self

    def alloc(self, n):
        a = self.heap; self.heap += max((n + 15) & ~15, 16)
        for i in range(0, (n + 7) & ~7, 8): self.cpu.write(a + i, 8, 0) if hasattr(self, 'cpu') else None
        return a

    def _malloc(self, c):
        self.stubbed.add('runtime.mallocgc*'); c.r['rax'] = self.alloc(c.r['rax'])

    def _intern(self, c):
        self.stubbed.add('internStorageKey')
        w = c.read(c.r['rbx'], 32)
        h = self.handles.get(w)
        if h is None:
            h = self.alloc(32); c.write(h, 32, w); self.handles[w] = h; self.words[h] = w
        c.r['rax'] = h

    def _getstate(self, c):
        self.stubbed.add('IntraBlockState.GetState'); self.gs_calls += 1
        addr = self.addr_of[c.r['rbx']]; word = self.words[c.r['rcx']]
        v = self.reader(addr, word)
        c.write(c.r['rsp'], 32, v)                   # uint256 result on the caller's stack (opSload 0x1df3066)
        c.r['rax'] = 0; c.r['rbx'] = 0

    def _pget(self, c):
        self.stubbed.add('sync.Pool'); ctx = self.pool.pop() if self.pool else self.alloc(CTX_SIZE)
        c.r['rax'] = TYPE_PTR_CALLCONTEXT; c.r['rbx'] = ctx

    def _pput(self, c):
        self.stubbed.add('sync.Pool'); self.pool.append(c.r['rcx'])

    def call(self, name, regs, stack=b''):
        c = self.cpu
        entry = self.fn(name)
        for k, v in zip(('rax', 'rbx', 'rcx', 'rdi', 'rsi', 'r8', 'r9'), regs): c.r[k] = v & M64
        c.r['r14'] = GJ.GSTRUCT; c.y[15] = 0
        sp = GJ.STK_TOP - 0x2000; c.r['rsp'] = sp; c.write(sp, 8, GJ.RET)
        for i, x in enumerate(stack): c.write(sp + 8 + i, 1, x)
        c.budget = 0; pc = entry
        while pc != GJ.RET: pc = c.step(pc)
        self.visited |= c.visited; self.fault_hits += c.fault_hits; c.fault_hits = 0
        return c.r['rax'], c.r['rbx'], c.r['rcx']


class BinCore(CM.Core):
    """cachemodel.Core with enter, leave, the SLOAD cache and the SSTORE gas-phase cache step run from the binary.
    The journal model (n, epoch, push, revert_to, journalled_set, the storage write) is Core's."""
    shared_machine = None

    def __init__(self, raw, fault=None):
        super().__init__(raw, None)
        if BinCore.shared_machine is None or BinCore.shared_machine.fault != (FAULTS.get(fault) or {}):
            BinCore.shared_machine = Erigon(FAULTS.get(fault)) if fault else Erigon()
        self.e = BinCore.shared_machine.new()
        self.e.reader = lambda a, w: dict.get(self.raw, (a, w), 0)
        self.e.addr_of = {}; self.e.gs_calls = 0
        self.bin_fault = fault

    def _sync(self):
        c = self.e.cpu
        c.write(self.e.JOURNAL + 0x10, 8, self.n); c.write(self.e.JOURNAL + 0x20, 8, self.epoch)
        c.write(self.e.EVM + 0x130, 8, len(self.frames))   # evm.depth (putCallContext 0x1dfaf9c)

    def enter(self, addr):
        e = self.e
        self._sync()
        h = e.addrh.get(addr)
        if h is None: h = e.alloc(32); e.addrh[addr] = h; e.addr_of[h] = addr
        contract = bytearray(0x90); contract[8:16] = h.to_bytes(8, 'little')   # Contract.address at +0x8 (ctx+0x90)
        ctx = e.call(EV + '(*EVM).getCallContext', [e.EVM, 0, 0, 0, 0, 0], stack=bytes(contract))[0]
        c = e.cpu
        c.write(ctx + 0x160, 1, 1); c.write(ctx + 0x168, 8, 0)     # slots.on = ReadStamp ok; slots.misses = 0
        f = CM.Ctx(); f.addr = addr; f.ptr = ctx
        self.frames.append(f)
        return f

    def leave(self):
        e = self.e
        self._sync()                                             # depth still counts the frame
        f = self.frames[-1]
        e.call(EV + '(*EVM).putCallContext', [e.EVM, f.ptr])
        self.frames.pop()

    def _op(self, f, word):
        c = self.e.cpu
        c.write(f.ptr + 0x60, 8, c.read(f.ptr + 0x60, 8) + 1)    # cacheGen++ for this opcode
        c.write(f.ptr + 0x230, 32, word); c.write(f.ptr + 0x8230, 8, 1)   # stack: one word

    def sload(self, addr, word, where=''):
        f = self.frames[-1]; assert f.addr == addr
        true = dict.get(self.raw, (addr, word), 0); self.reads += 1
        self._sync(); self._op(f, word)
        e = self.e; g0 = e.gs_calls
        e.call(EV + 'opSload', [0, e.EVM, f.ptr])
        v = e.cpu.read(f.ptr + 0x230, 32)
        if e.gs_calls == g0:
            self.hits += 1
            if v != true:
                self.stale.append({'addr': hex(addr), 'slot': hex(word), 'cached': hex(v), 'true': hex(true), 'depth': len(self.frames), 'where': where})
        elif v != true:
            self.stale.append({'addr': hex(addr), 'slot': hex(word), 'read': hex(v), 'true': hex(true), 'where': where, 'note': 'state read'})
        return v

    def sstore(self, addr, word, v):
        f = self.frames[-1]; assert f.addr == addr
        true = dict.get(self.raw, (addr, word), 0)
        e = self.e; c = e.cpu
        self._sync(); self._op(f, word)
        if c.read(f.ptr + 0x160, 1):
            j = e.call(EV + '(*CallContext).lookupSlot', [f.ptr, e.EVM])[0]
            j = j - (1 << 64) if j >> 63 else j
            if j >= 0:
                cv = c.read(f.ptr + 0x1f0 + 32 * j, 32)
                if cv != true: self.gas_stale.append({'addr': hex(addr), 'slot': hex(word), 'cached': hex(cv), 'true': hex(true)})
            else:
                jl, ep, _ = e.call(ST + '(*IntraBlockState).ReadStamp', [e.IBS])
                key = e.handles.get(word)
                if key is None:
                    key = e.alloc(32); c.write(key, 32, word); e.handles[word] = key; e.words[key] = word
                e.call(EV + '(*frameSlots).put', [f.ptr + 0x160, jl, ep, key],
                       stack=word.to_bytes(32, 'little') + true.to_bytes(32, 'little'))
                self.fills += 1
        if true != v:
            self.push()
            dict.__setitem__(self.raw, (addr, word), v)


def find_faults():
    """stamp-ignored: in lookupSlot the two stamp compares are replaced so the stamp always matches."""
    out = subprocess.run(['objdump', '-d', '--no-show-raw-insn', '-M', 'intel', '--start-address=0x1dfa680',
                          '--stop-address=0x1dfa820', BIN], capture_output=True, text=True).stdout
    return [l for l in out.splitlines() if re.match(r'^ *[0-9a-f]+:\s', l)]
