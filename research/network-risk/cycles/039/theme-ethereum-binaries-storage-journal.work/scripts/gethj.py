"""Cycle 39, theme-ethereum-binaries-storage-journal, task 1 (L-1346), geth part.

The released geth v1.17.10 linux/amd64 binary (cycle 38 download, read as data only, never executed, loaded or
dlopened) is interpreted instruction by instruction in the cycle 27-38 x86-64 model (x86emu.py / x86emu2.py, objdump
text interpreted in Python). Functions are disassembled on demand from their .gopclntab ranges (the cycle 38 list
dl/build/all-geth-amd64.txt), so every routine the lifted code reaches runs from the binary text, the Go swiss map
runtime (internal/runtime/maps: mapaccess1/2, mapassign, mapdelete, makemap_small, the group probing and the
fallback memhash) included.

Entry points called from Python: core/vm.opTstore, opTload, opSstore, opSload (through the real vm.StateDB itab of
*state.StateDB found in the file at 0x3f25020), (*StateDB).GetStateAndCommittedState for the original value, Snapshot,
RevertToSnapshot, and state.NewWithReader to build the StateDB with its maps, journal and transient map.

Stubbed (Python): the allocator (runtime.mallocgc and its generated size-class variants, filled with zero), the random
source runtime.rand (seeded, it only sets the per-map hash seed), the clock (time.Now, time.Since), and the database
below the state: Database.Type and Reader.Account / Reader.Storage through model itabs whose every slot is a stub.
Every other runtime call that is reached (panics, morestack, write barriers) stops the run with an error. The
write-barrier flag and the AES hash flag live in .bss and read zero, so the binary takes its no-barrier and
memHashFallback paths.

usage: python3 -I gethj.py <nseq> <out.json> [fault]
"""
import bisect, json, os, random, re, struct, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
C38 = '/home/user/v4-core/research/network-risk/cycles/038/theme-ethereum-client-binaries-lift.work/'
sys.path.insert(0, C38 + 'scripts/emu')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import x86emu
from x86emu2 import CPU2, rewrite_rip
from x86emu import Stop, M64

BIN = C38 + 'dl/geth/geth-linux-amd64-1.17.10-1df30b18/geth'
FNS = C38 + 'dl/build/all-geth-amd64.txt'
CACHE = os.path.join(os.path.dirname(HERE), 'dis', 'geth')
os.makedirs(CACHE, exist_ok=True)
GE = 'github.com/ethereum/go-ethereum/'
ITAB_VM_STATEDB = 0x3f25020   # go:itab.*state.StateDB,vm.StateDB (found by value scan, method order checked)

HEAP0, HEAP1 = 0xc000000000, 0xc010000000
STK_TOP = 0x7ffff0000000
GSTRUCT = 0x29000000
MODEL = 0x2a000000            # scope, stack, arena, contract, evm, itabs
STUB0 = 0x2f000000            # stub addresses
RET = 0xdead0000


def load_fns():
    byname, starts, rng = {}, [], []
    for l in open(FNS):
        p = l.split()
        n = ' '.join(p[:-4]); lo, hi = int(p[-4], 16), int(p[-3], 16)
        if n not in byname:
            byname[n] = (lo, hi)
        rng.append((lo, hi, n))
    rng.sort()
    return byname, rng


class Image:
    def __init__(self, path):
        f = open(path, 'rb').read(); self.f = f
        shoff, = struct.unpack_from('<Q', f, 0x28); se, sn = struct.unpack_from('<HH', f, 0x3a)
        self.secs, self.bss = [], []
        for i in range(sn):
            name, typ, flags, addr, off, size = struct.unpack_from('<IIQQQQ', f, shoff + i * se)
            if not addr or not (flags & 2): continue
            if typ == 8: self.bss.append((addr, addr + size))
            else: self.secs.append((addr, addr + size, off))

    def read(self, a, n):
        for lo, hi, off in self.secs:
            if lo <= a and a + n <= hi:
                return int.from_bytes(self.f[off + a - lo: off + a - lo + n], 'little')
        for lo, hi in self.bss:
            if lo <= a and a + n <= hi:
                return 0
        return None


class LazyProg:
    def __init__(self, rng, text_patch=None, binpath=None, cache=None):
        self.bin = binpath or BIN; self.cache = cache or CACHE
        os.makedirs(self.cache, exist_ok=True)
        self.ins, self.nxt, self.loaded = {}, {}, set()
        self.rng = rng; self.starts = [r[0] for r in rng]
        self.patch = text_patch or {}
        self.names = {}

    def fn_at(self, pc):
        k = bisect.bisect_right(self.starts, pc) - 1
        if k < 0: return None
        lo, hi, n = self.rng[k]
        return (lo, hi, n) if lo <= pc < hi else None

    def load(self, pc):
        f = self.fn_at(pc)
        if f is None: raise Stop('pc %x outside any function' % pc)
        lo, hi, n = f
        if lo in self.loaded: raise Stop('pc %x not an instruction start in %s' % (pc, n))
        p = os.path.join(self.cache, '%x.s' % lo)
        if os.path.exists(p):
            t = open(p).read()
        else:
            out = subprocess.run(['objdump', '-d', '--no-show-raw-insn', '-M', 'intel', '--start-address=%#x' % lo,
                                  '--stop-address=%#x' % hi, self.bin], capture_output=True, text=True).stdout
            t = rewrite_rip('\n'.join(l for l in out.splitlines() if re.match(r'^ *[0-9a-f]+:\s', l)))
            open(p, 'w').write(t)
        order = []
        for line in t.splitlines():
            m = re.match(r'^\s*([0-9a-f]+):\s+(.*)$', line)
            if not m: continue
            a = int(m.group(1), 16)
            body = re.sub(r'\s*<[^>]*>', '', m.group(2)).split('#')[0].strip()
            body = re.sub(r'^lock\s+', '', body)
            if not body or body.startswith('(bad)'): continue
            self.ins[a] = self.patch.get(a, body); order.append(a)
        order.sort()
        for a, b in zip(order, order[1:] + [None]): self.nxt[a] = b
        self.loaded.add(lo); self.names[lo] = n


class CPU(CPU2):
    def __init__(self, prog, img, externs):
        super().__init__(prog, b'', 0, externs=externs)
        self.img = img
        self.visited = set(); self.budget = 0
        self.fs = 0x7f0000000000
        self.faults_ms = {}; self.fault_hits = 0

    def read(self, a, n):
        a &= M64
        mem = self.mem
        if a in mem or (a + n - 1) in mem:
            v = 0
            for i in range(n):
                x = mem.get(a + i)
                if x is None:
                    x = 0 if self._ram(a + i) else self.img.read(a + i, 1)
                    if x is None: raise Stop('read %d at %x partly outside memory' % (n, a))
                v |= x << (8 * i)
            return v
        if self._ram(a):
            return 0
        v = self.img.read(a, n)
        if v is None: raise Stop('read %d at %x outside memory' % (n, a))
        return v

    def _ram(self, a):
        return HEAP0 <= a < HEAP1 or STK_TOP - 0x200000 <= a <= STK_TOP or MODEL <= a < MODEL + 0x100000 \
            or GSTRUCT <= a < GSTRUCT + 0x1000 or self.fs - 0x100 <= a < self.fs + 0x100

    def write(self, a, n, v):
        a &= M64
        ok = HEAP0 <= a < HEAP1 or STK_TOP - 0x200000 <= a <= STK_TOP or MODEL <= a < MODEL + 0x100000 \
            or GSTRUCT <= a < GSTRUCT + 0x1000 or self.fs - 0x100 <= a < self.fs + 0x100 \
            or any(lo <= a < hi for lo, hi in self.img.bss)
        if not ok: raise Stop('write %d at %x outside writable memory' % (n, a))
        mem = self.mem
        for i in range(n):
            mem[a + i] = (v >> (8 * i)) & 0xff

    def step(self, pc):
        if pc not in self.p.ins:
            self.p.load(pc)
        self.budget += 1
        if self.budget > 4_000_000: raise Stop('step limit')
        self.visited.add(pc)
        f = self.faults_ms.get(pc)
        if f is not None:
            # planted fault: the instruction at pc is replaced by one or more instructions (';' separated)
            self.fault_hits += 1
            saved = self.p.ins[pc]; parts = [x.strip() for x in f.split(';')]
            try:
                for part in parts[:-1]:
                    self.p.ins[pc] = part; x86emu.CPU.step(self, pc)
                self.p.ins[pc] = parts[-1]
                return x86emu.CPU.step(self, pc)
            finally:
                self.p.ins[pc] = saved
        return super().step(pc)

    def _target(self, s):
        s = s.strip()
        if re.match(r'^(0x)?[0-9a-f]+$', s): return int(s, 16)
        return self.get(self.opnd(s))

    def i_call(self, o, pc, n):
        t = self._target(o[0])
        if t in self.externs:
            self.externs[t](self); return n
        self.r['rsp'] = (self.r['rsp'] - 8) & M64; self.write(self.r['rsp'], 8, n); return t

    def i_jmp(self, o, pc, n):
        t = self._target(o[0])
        if t in self.externs:
            self.externs[t](self)
            a = self.read(self.r['rsp'], 8); self.r['rsp'] += 8; return a
        return t

    def i_bswap(self, o, pc, n):
        d = self.opnd(o[0]); w = d[2] // 8
        self.put(d, int.from_bytes(self.get(d).to_bytes(w, 'little'), 'big'))
        return n

    def _rot(self, o, left):
        d = self.opnd(o[0]); w = d[2]
        k = self.get(self.opnd(o[1])) % w if len(o) > 1 else 1
        v = self.get(d)
        if k:
            v = ((v << k) | (v >> (w - k))) & ((1 << w) - 1) if left else ((v >> k) | (v << (w - k))) & ((1 << w) - 1)
            self.cf = (v & 1) if left else (v >> (w - 1)) & 1
        self.put(d, v)

    def i_rol(self, o, pc, n): self._rot(o, True); return n
    def i_ror(self, o, pc, n): self._rot(o, False); return n

    def i_movsx(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1]); w = s[2]; v = self.get(s)
        if v >> (w - 1) & 1: v -= 1 << w
        self.put(d, v & ((1 << d[2]) - 1)); return n

    def i_bts(self, o, pc, n):
        d = self.opnd(o[0]); s = self.opnd(o[1])
        if d[0] != 'r': raise Stop('bts with memory destination')
        w = d[2]; k = self.get(s) % w; v = self.get(d)
        self.cf = (v >> k) & 1; self.put(d, v | (1 << k)); return n

    def i_prefetcht0(self, o, pc, n): return n
    def i_prefetchnta(self, o, pc, n): return n

    def i_pshuflw(self, o, pc, n):
        src = self._xget(self.opnd(o[1])); k = int(o[2], 16)
        w = [(src >> (16 * i)) & 0xffff for i in range(4)]
        lo = sum(w[(k >> (2 * i)) & 3] << (16 * i) for i in range(4))
        self._xput(self.opnd(o[0]), (src & (((1 << 64) - 1) << 64)) | lo)

    def i_pcmpgtb(self, o, pc, n):
        sx = lambda v: v - 256 if v & 0x80 else v
        d = self.opnd(o[0]); s = self.opnd(o[1])
        a = self.y[int(d[1][3:])] & ((1 << 128) - 1)
        b = self.read(s[1], 16) if s[0] == 'm' else self.y[int(s[1][3:])] & ((1 << 128) - 1)
        r = 0
        for i in range(16):
            x, y = (a >> (8 * i)) & 0xff, (b >> (8 * i)) & 0xff
            if sx(x) > sx(y): r |= 0xff << (8 * i)
        i = int(d[1][3:]); self.y[i] = (self.y[i] & ~((1 << 128) - 1)) | r
        return n


# ------------------------------------------------------------------------------------------------ the machine
class Geth:
    def __init__(self, text_patch=None, seed=0):
        self.byname, rng = load_fns()
        self.img = Image(BIN)
        self.prog = LazyProg(rng)
        self.fault = text_patch or {}
        self.fault_hits = 0
        self.rnd = random.Random(seed)
        self.stubbed = set()
        self.calls = {}
        self.visited = set()

    def fn(self, n):
        return self.byname[n][0]

    def new(self):
        """A fresh transaction state: CPU, heap, stub itabs, StateDB built by NewWithReader."""
        self.heap = HEAP0
        self.db = {}      # (addr, slot) -> committed value
        self.dbreads = []
        self.accts = {}   # addr -> StateAccount pointer in model memory (created on first Account call)
        ext = {}
        for n, (lo, hi) in self.byname.items():
            if n.startswith('runtime.mallocgc'):
                ext[lo] = self._malloc(n)
        ext[self.fn('runtime.rand')] = self._rand
        ext[self.fn('time.Now')] = self._now
        ext[self.fn('time.Since')] = self._since
        for n in ('runtime.morestack_noctxt', 'runtime.morestack', 'runtime.panicBounds', 'runtime.gopanic',
                  'runtime.gcWriteBarrier1', 'runtime.gcWriteBarrier2', 'runtime.gcWriteBarrier3', 'runtime.gcWriteBarrier4',
                  'runtime.gcWriteBarrier5', 'runtime.gcWriteBarrier6', 'runtime.gcWriteBarrier7', 'runtime.gcWriteBarrier8',
                  'runtime.throw', 'runtime.fatal', 'runtime.panicdivide', 'runtime.panicshift', 'runtime.bulkBarrierPreWrite',
                  'runtime.panicwrap', 'runtime.panicnildottype', 'runtime.panicdottypeE', 'runtime.panicdottypeI',
                  'runtime.sigpanic', 'runtime.panicmem', 'runtime.panicIndex', 'runtime.goPanicIndex'):
            if n in self.byname:
                ext[self.fn(n)] = (lambda c, n=n: (_ for _ in ()).throw(Stop('call ' + n)))
        # model itabs: Database and Reader; every slot a stub that records its index
        self.ext = ext
        self.cpu = CPU(self.prog, self.img, ext)
        self.cpu.faults_ms = self.fault
        c = self.cpu
        c.write(GSTRUCT, 8, 0); c.write(GSTRUCT + 0x8, 8, 0); c.write(GSTRUCT + 0x10, 8, 0)
        c.write(c.fs - 8, 8, GSTRUCT)
        self.itab_db = MODEL + 0x80000; self.itab_rd = MODEL + 0x81000
        for k in range(64):
            ext[STUB0 + 0x100 * k] = self._dbstub(k)
            ext[STUB0 + 0x10000 + 0x100 * k] = self._rdstub(k)
            c.write(self.itab_db + 0x18 + 8 * k, 8, STUB0 + 0x100 * k)
            c.write(self.itab_rd + 0x18 + 8 * k, 8, STUB0 + 0x10000 + 0x100 * k)
        self.dbobj = self.alloc(64); self.rdobj = self.alloc(64)
        # state.NewWithReader(root Hash [stack], db Database [rax,rbx], reader Reader [rcx,rdi])
        root = 0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421
        rax, rbx, rcx = self.call(GE + 'core/state.NewWithReader', [self.itab_db, self.dbobj, self.itab_rd, self.rdobj],
                                  stack=root.to_bytes(32, 'big'))
        if rbx: raise Stop('NewWithReader returned an error')
        self.sdb = rax
        self._scope()
        return self

    # ---- allocator, clock and rand stubs
    def alloc(self, n):
        a = self.heap
        self.heap += max((n + 15) & ~15, 16)
        if self.heap > HEAP1: raise Stop('heap exhausted')
        return a

    def _malloc(self, name):
        def f(c):
            self.stubbed.add('runtime.mallocgc*')
            size = c.r['rax']
            a = self.alloc(size)
            for i in range(0, (size + 7) & ~7, 8): c.write(a + i, 8, 0)
            c.r['rax'] = a
        return f

    def _rand(self, c):
        self.stubbed.add('runtime.rand'); c.r['rax'] = self.rnd.getrandbits(64)

    def _now(self, c):
        self.stubbed.add('time.Now'); c.r['rax'] = 0; c.r['rbx'] = 0; c.r['rcx'] = 0

    def _since(self, c):
        self.stubbed.add('time.Since'); c.r['rax'] = 0

    def _dbstub(self, k):
        def f(c):
            self.calls[('db', k)] = self.calls.get(('db', k), 0) + 1
            self.stubbed.add('Database itab slot %d' % k)
            c.r['rax'] = 0; c.r['rbx'] = 0; c.r['rcx'] = 0
        return f

    def _rdstub(self, k):
        def f(c):
            self.calls[('rd', k)] = self.calls.get(('rd', k), 0) + 1
            h = self.reader_slots.get(k)
            if h is None: raise Stop('Reader itab slot %d called' % k)
            h(c)
        return f

    # Reader.Account(addr Address) (*types.StateAccount, error): addr on the stack at the caller's [rsp], result in rax, error rbx/rcx
    # Reader.Storage(addr Address, slot Hash) (Hash, error): addr [rsp], slot [rsp+0x14], Hash result on the stack
    # after the arguments at [rsp+0x38] (caller's rsp; Reader itab slot 4 = itab+0x38, call at 0x9bbdb6), error in rax/rbx. Slot numbers and stack offsets are read from the call sites
    # in getStateObject (0x9c2bdb) and GetCommittedState (see the research file).
    def _account(self, c):
        self.stubbed.add('Reader.Account (itab slot 0)')
        sp = c.r['rsp']
        addr = int.from_bytes(self.rb(sp, 20), 'big')   # externs run without a pushed return address
        a = self.accts.get(addr)
        if a is None:
            a = self.alloc(72); bal = self.alloc(32); ch = self.alloc(32)
            for i in range(0, 72, 8): c.write(a + i, 8, 0)
            for i in range(0, 32, 8): c.write(bal + i, 8, 0)
            c.write(a + 8, 8, bal)
            self.wb(a + 16, (0x1111 + addr % 997).to_bytes(32, 'big'))      # a non-empty storage root
            self.wb(ch, (0xc0de).to_bytes(32, 'big'))
            c.write(a + 48, 8, ch); c.write(a + 56, 8, 32); c.write(a + 64, 8, 32)
            self.accts[addr] = a
        c.r['rax'] = a; c.r['rbx'] = 0; c.r['rcx'] = 0

    def _storage(self, c):
        self.stubbed.add('Reader.Storage (itab slot 4)')
        sp = c.r['rsp']
        addr = int.from_bytes(self.rb(sp, 20), 'big'); slot = int.from_bytes(self.rb(sp + 20, 32), 'big')
        self.dbreads.append((addr, slot))
        self.wb(sp + 0x38, self.db.get((addr, slot), 0).to_bytes(32, 'big'))
        c.r['rax'] = 0; c.r['rbx'] = 0

    @property
    def reader_slots(self):
        return {0: self._account, 4: self._storage}

    def rb(self, a, n):
        return bytes(self.cpu.read(a + i, 1) for i in range(n))

    def wb(self, a, b):
        for i, x in enumerate(b): self.cpu.write(a + i, 1, x)

    def call(self, name, regs, stack=b'', ret_stack=0):
        c = self.cpu
        entry = self.fn(name) if isinstance(name, str) else name
        for k, v in zip(('rax', 'rbx', 'rcx', 'rdi', 'rsi', 'r8', 'r9', 'r10', 'r11'), regs):
            c.r[k] = v & M64
        c.r['r14'] = GSTRUCT
        c.y[15] = 0
        sp = STK_TOP - 0x1000
        c.r['rsp'] = sp
        c.write(sp, 8, RET)
        if stack: self.wb(sp + 8, stack)
        c.budget = 0
        pc = entry
        while pc != RET:
            pc = c.step(pc)
        self.visited |= c.visited
        self.fault_hits += c.fault_hits; c.fault_hits = 0
        self.last_sp = sp
        return c.r['rax'], c.r['rbx'], c.r['rcx']

    # ---- EVM, scope and stack for the op handlers (layout read from opTstore 0x9e7960)
    # evm: StateDB itab +0xb8, data +0xc0, readOnly +0x158; scope: Stack +0x8, Contract +0x10;
    # Stack: size +0x8, arena +0x10; arena: data +0x0, cap +0x8, top +0x18; Contract: address +0x14.
    def _scope(self):
        c = self.cpu
        self.EVM, self.SCOPE, self.STACK, self.ARENA, self.CONTRACT, self.DATA, self.PCP = \
            MODEL, MODEL + 0x1000, MODEL + 0x1100, MODEL + 0x1200, MODEL + 0x1300, MODEL + 0x2000, MODEL + 0x1400
        c.write(self.EVM + 0xb8, 8, ITAB_VM_STATEDB); c.write(self.EVM + 0xc0, 8, self.sdb)
        c.write(self.EVM + 0x158, 1, 0)
        c.write(self.SCOPE + 0x8, 8, self.STACK); c.write(self.SCOPE + 0x10, 8, self.CONTRACT)
        c.write(self.STACK + 0x10, 8, self.ARENA)
        c.write(self.ARENA, 8, self.DATA); c.write(self.ARENA + 0x8, 8, 64)

    def _push(self, words):
        c = self.cpu
        base = [0xa5a5] * 2
        st = base + words
        for i, x in enumerate(st): c.write(self.DATA + 32 * i, 32, x)
        c.write(self.STACK + 0x8, 8, len(st)); c.write(self.ARENA + 0x18, 8, len(st))
        return len(st)

    def _top(self):
        return self.cpu.read(self.ARENA + 0x18, 8)

    def _addr(self, a):
        self.wb(self.CONTRACT + 0x14, a.to_bytes(20, 'big'))

    def op(self, name, addr, words, outn):
        self._addr(addr)
        n = self._push(words)
        r = self.call(GE + 'core/vm.' + name, [self.PCP, self.EVM, self.SCOPE])
        if r[0] or r[1] or r[2]: raise Stop('%s returned %s' % (name, [hex(x) for x in r]))
        t = self._top()
        if t != n - len(words) + outn: raise Stop('%s stack top %d' % (name, t))
        return self.cpu.read(self.DATA + 32 * (t - 1), 32) if outn else None

    def tst(self, a, s, v): self.op('opTstore', a, [v, s], 0)
    def tld(self, a, s): return self.op('opTload', a, [s], 1)
    def sst(self, a, s, v): self.op('opSstore', a, [v, s], 0)
    def sld(self, a, s): return self.op('opSload', a, [s], 1)

    def orig(self, a, s):
        """(*StateDB).GetStateAndCommittedState(addr, slot) -> (current, original); both Hash results on the stack."""
        self.call(GE + 'core/state.(*StateDB).GetStateAndCommittedState', [self.sdb],
                  stack=a.to_bytes(20, 'big') + s.to_bytes(32, 'big'))
        sp = self.last_sp + 8
        off = 56   # 20 + 32 = 52 bytes of arguments, results start at the next 8 byte boundary
        cur = int.from_bytes(self.rb(sp + off, 32), 'big'); org = int.from_bytes(self.rb(sp + off + 32, 32), 'big')
        return cur, org

    def snap(self):
        r = self.call(GE + 'core/state.(*StateDB).Snapshot', [self.sdb])
        return r[0]

    def revert(self, rid):
        self.call(GE + 'core/state.(*StateDB).RevertToSnapshot', [self.sdb, rid])

    def jlen(self):
        j = self.cpu.read(self.sdb + 240, 8)
        return self.cpu.read(j + 8, 8), self.cpu.read(j + 32 + 8, 8)
