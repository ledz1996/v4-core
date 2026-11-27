"""Cycle 36 copy of the cycle 35 rethj.py with a conduit-op-reth v2.5.1 profile added (theme-worldchain-zora-journal-lift).
Cycle 35, theme-reth-journal-binary-lift: the storage, transient storage and journal routines of a shipped
op-reth / Base x86-64 binary run in the cycle 27-30 x86-64 model (x86emu.py / x86emu2.py, objdump text interpreted
in Python). Nothing from the downloaded binary is executed, loaded or dlopened; its disassembly text is read with
objdump and interpreted, and its bytes are read as data.

Every routine reached is disassembled on demand from its .eh_frame range (lazy program). Only these are modelled:
  - the allocator entry points the GOT slots point at (jemalloc malloc, mallocx, rallocx, realloc, sdallocx) by a
    bump allocator that fills fresh blocks with 0xa5, and memcpy / memmove / memset / bcmp / memcmp;
  - the database read below the in-memory state (a Python dict), at the call that leaves the journal;
  - the runtime-initialised hasher seeds (a global word, its Once flag and the per-thread word), set from the seed.
The account table, every per-account storage table, the two-level transient table, the journal vector and the
depth counter are real structures in model memory, built and changed only by the lifted code, except that the
first account record of each test address is placed in the account table by Python (see put_account).
"""
import bisect, os, random, re, subprocess, sys
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/029/theme-tempo-binary-keccak-transient.work/scripts')
from x86emu2 import CPU2, Stop, rewrite_rip, M64
import x86emu

M = (1 << 256) - 1
HERE = os.path.dirname(os.path.abspath(__file__))


class LazyProg:
    def __init__(self, binf, fdes, cache_dir):
        self.bin = binf; self.ins = {}; self.nxt = {}; self.loaded = {}; self.cache = cache_dir
        self.f = sorted(tuple(int(x, 16) for x in re.split(r'\.\.+', l.strip())) for l in open(fdes))
        self.s = [a for a, b in self.f]
        self.patched = {}

    def text_of(self, lo, hi):
        p = os.path.join(self.cache, '%x.s' % lo)
        if os.path.exists(p):
            return open(p).read()
        out = subprocess.run(['objdump', '-d', '--no-show-raw-insn', '-M', 'intel', '--start-address=%#x' % lo,
                              '--stop-address=%#x' % hi, self.bin], capture_output=True, text=True).stdout
        t = rewrite_rip('\n'.join(l for l in out.splitlines() if re.match(r'^ *[0-9a-f]+:\s', l)))
        open(p, 'w').write(t)
        return t

    def load(self, pc):
        k = bisect.bisect_right(self.s, pc) - 1
        lo, hi = self.f[k]
        if not (lo <= pc < hi):
            raise Stop('pc %x outside any FDE' % pc)
        if lo in self.loaded:
            raise Stop('pc %x not an instruction start in %x' % (pc, lo))
        t = self.text_of(lo, hi)
        order = []
        for line in t.splitlines():
            m = re.match(r'^\s*([0-9a-f]+):\s+(.*)$', line)
            if not m: continue
            a = int(m.group(1), 16)
            body = re.sub(r'\s*<[^>]*>', '', m.group(2)).split('#')[0].strip()
            body = re.sub(r'^lock\s+', '', body)   # single-threaded model: the lock prefix changes nothing here
            if not body or body.startswith('(bad)'): continue
            self.ins[a] = body; order.append(a)
        order.sort()
        for a, b in zip(order, order[1:] + [None]): self.nxt[a] = b
        self.loaded[lo] = hi


class CPU(CPU2):
    def __init__(self, prog, img, externs, got, faults, hooks):
        super().__init__(prog, img, len(img), externs=externs, got=got, faults={})
        self.myfaults = faults; self.fault_hits = 0
        self.hooks = hooks; self.visited = set(); self.steps = 0; self.budget = 0

    def ea(self, s):
        return super().ea(s) & M64

    def read(self, a, n):
        mem = self.mem
        if a + n <= self.fhi:
            if not any((a + i) in mem for i in range(n)):
                return int.from_bytes(self.fb[a:a + n], 'little')
        v = 0
        for i in range(n):
            x = mem.get(a + i)
            if x is None:
                x = self.fb[a + i] if a + i < self.fhi else 0
            v |= x << (8 * i)
        return v

    def step(self, pc):
        if pc not in self.p.ins:
            self.p.load(pc)
        self.steps += 1; self.budget += 1
        if self.budget > 5_000_000: raise Stop('step limit')
        h = self.hooks.get(pc)
        if h: h(self)
        f = self.myfaults.get(pc)
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

    def i_jmp(self, o, pc, n):
        if o[0] in self.r:
            t = self.r[o[0]]
            if t in self.externs:
                self.externs[t](self); a = self.read(self.r['rsp'], 8); self.r['rsp'] += 8; return a
            return t
        return super().i_jmp(o, pc, n)

    def i_call(self, o, pc, n):
        if o[0] in self.r:
            t = self.r[o[0]]
            if t in self.externs:
                self.externs[t](self); return n
            self.r['rsp'] -= 8; self.write(self.r['rsp'], 8, n); return t
        m = re.match(r'^QWORD PTR (\[.*\])$', o[0])
        if m and not re.match(r'^\[0x[0-9a-f]+\]$', m.group(1)):
            t = self.read(self.ea(m.group(1)), 8)
            if t in self.externs:
                self.externs[t](self); return n
            self.r['rsp'] -= 8; self.write(self.r['rsp'], 8, n); return t
        return super().i_call(o, pc, n)

    def i_pshuflw(self, o, pc, n):
        src = self._xget(self.opnd(o[1])); k = int(o[2], 16)
        w = [(src >> (16 * i)) & 0xffff for i in range(4)]
        lo = sum(w[(k >> (2 * i)) & 3] << (16 * i) for i in range(4))
        self._xput(self.opnd(o[0]), (src & (((1 << 64) - 1) << 64)) | lo)

    def i_shufpd(self, o, pc, n):
        d = self.opnd(o[0]); a = self._xget(d); s = self.opnd(o[1])
        b = self.read(s[1], 16) if s[0] == 'm' else self._xget(s); k = int(o[2], 16)
        lo = (a >> 64) if k & 1 else (a & M64)
        hi = (b >> 64) if k & 2 else (b & M64)
        self._xput(d, lo | (hi << 64))

    def i_bswap(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]
        self.put(d, int.from_bytes(self.get(d).to_bytes(b // 8, 'little'), 'big'))

    def i_rol(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]
        c = self._shcount(self.opnd(o[1]) if len(o) > 1 else ('i', 1, None), b)
        if c == 0: return
        x = self.get(d); r = ((x << c) | (x >> (b - c))) & ((1 << b) - 1)
        self.cf = r & 1; self.put(d, r)

    def i_ror(self, o, pc, n):
        d = self.opnd(o[0]); b = d[2]
        c = self._shcount(self.opnd(o[1]) if len(o) > 1 else ('i', 1, None), b)
        if c == 0: return
        x = self.get(d); r = ((x >> c) | (x << (b - c))) & ((1 << b) - 1)
        self.cf = (r >> (b - 1)) & 1; self.put(d, r)

    def i_prefetcht0(self, o, pc, n): pass
    def i_ud1(self, o, pc, n): raise Stop('ud1 at %x' % pc)


# ---------------------------------------------------------------- binary profiles
PROFILES = {
    # op-reth v2.10.0-rc.4 x86-64 (us-docker.pkg.dev/oplabs-tools-artifacts/images/op-reth, revision 65e80332)
    'opreth': dict(
        bin='/home/user/v4-core/research/network-risk/cycles/032/theme-opstack-reth-binary-lift.work/dl/opreth/x/amd64/usr/local/bin/op-reth',
        fde='/home/user/v4-core/research/network-risk/cycles/032/theme-opstack-reth-binary-lift.work/build/opreth-amd64.fde',
        seed_word=0x5b8c328, seed_once=0x5b8c358, tls_word=0xfffffffffffff6b0, empty_group=0x17acb40,
        got={0x5b67778: 'malloc', 0x5b67790: 'mallocx', 0x5b67798: 'rallocx', 0x5b677a0: 'realloc', 0x5b677c8: 'sdallocx',
             0x5b68390: 'memcpy', 0x5b68078: 'memmove', 0x5b682f8: 'memset', 0x5b682c0: 'bcmp', 0x5b682d8: 'memcmp'},
        panics=[0x1852500, 0x38bdbd3, 0x38b7db0, 0x38bd330, 0x32449e1, 0x32449ce, 0x38bdb10, 0x38bdb90],
        layout=dict(inner=0x468, target=0x88, gas=0x190, static=0x1c8, spec=0x1c9, gasparams=0x440),
        acct_get=0x4a4e6e0, slot_entry=0x44e83f0,
        families={
            # table 0x5aea7c0: dyn state-provider database (call [vtable+0x30]), frame code 0x456dc20 / 0x4570fd0
            'A': dict(table=0x5aea7c0, SLOAD=0x457ef30, SSTORE=0x457f080, TLOAD=0x457fc00, TSTORE=0x457fc90,
                      revert=0x44daef0, checkpoint=0x4579590, commit=(0x4571114, 0x457112a), db='dyn30',
                      sstore_hooks=[0x457f261, 0x457f353], sstore_out=0xd0),
            # table 0x5a0e458 (the table cycle 32 ran): database reads compiled out (zero), frame revert 0x2d07000
            'B': dict(table=0x5a0e458, SLOAD=0x1e9d700, SSTORE=0x1e9e530, TLOAD=0x1e9e380, TSTORE=0x1ea4290,
                      revert=0x2d07000, checkpoint=0x4579590, commit=(0x4571114, 0x457112a), db='none',
                      sstore_hooks=[0x1e9e68b, 0x1e9e6d7], sstore_out=0x90),
        }),
    # Base v1.5.6 x86-64 (ghcr.io/base/node-reth), revm 42.0.1
    'base': dict(
        bin='/home/user/v4-core/research/network-risk/cycles/032/theme-opstack-reth-binary-lift.work/dl/base/x/amd64/app/base',
        fde='/home/user/v4-core/research/network-risk/cycles/032/theme-opstack-reth-binary-lift.work/build/base-amd64.fde',
        seed_word=0x93477a8, seed_once=0x93477d8, tls_word=0xfffffffffffff7b0, empty_group=0x6d16e0,
        got={0x9315ef0: 'malloc', 0x9315ee8: 'mallocx', 0x9315f00: 'rallocx', 0x9315f08: 'realloc', 0x9315ef8: 'sdallocx',
             0x9315f28: 'memcpy', 0x9315f20: 'memmove', 0x9315f70: 'memset', 0x9315f30: 'bcmp', 0x9315f68: 'memcmp'},
        panics=[0x9126f10, 0x775e733, 0x831f832, 0x75540d0, 0x775a890],
        layout=dict(inner=0x590, target=0x80, gas=0x188, static=0x1c0, spec=0x1c1, gasparams=0x730),
        acct_get=0x6c1fce0, slot_entry=0x4e2acf0,
        families={
            # table 0x91562b0 (the table cycle 32 ran): State<DB> database, storage read 0x6a6dd30
            'A': dict(table=0x91562b0, SLOAD=0x3d00230, SSTORE=0x3d010b0, TLOAD=0x682f1e0, TSTORE=0x3d06440,
                      revert=0x35be370, checkpoint=0x4dcf7d0, commit=(0x35c6550, 0x35c6566), commit_reg='rcx',
                      db='call:6a6dd30', db_ok_tag=0x2f, sstore_hooks=[0x3d0127d, 0x3d0137a], sstore_out=0xa0),
        }),
    # world-chain v2.8.2 x86-64 (ghcr.io/worldcoin/world-chain:v2.8.2, binary sha256 731d5c3b...707c, symbols), revm 43
    'worldchain': dict(
        bin='/home/user/v4-core/research/network-risk/cycles/035/op-stack-eth.work/dl/wc282/x/usr/local/bin/world-chain',
        fde='/home/user/v4-core/research/network-risk/cycles/035/theme-reth-journal-binary-lift.work/build/wc-amd64.fde',
        seed_word=0x5420ef8, seed_once=0x5420f28, tls_word=0xfffffffffffff860, empty_group=0x1f1670,
        got={0x53fb228: 'malloc', 0x53fb238: 'mallocx', 0x53fb528: 'rallocx', 0x53fb390: 'realloc', 0x53fb240: 'sdallocx',
             0x53fb2d8: 'calloc', 0x53fb230: 'memcpy', 0x53fb2a0: 'memmove', 0x53fb2c8: 'memset', 0x53fb290: 'bcmp', 0x53fb288: 'memcmp'},
        panics=[0x52ce9d0, 0x33224ff, 0x33224ec, 0x3551c20, 0x3551470, 0x3551c60, 0x3551cc0, 0x3551d23, 0x354ddf8, 0x3551ce0,
                0x354c424, 0x3551d13, 0x3551d30, 0x354ddc0, 0x354c560],
        layout=dict(inner=0x410, target=0x88, gas=0x190, static=0x1c8, spec=0x1c9, gasparams=0x5b0),
        acct_get=0x1ab8460, slot_entry=0x3e06640,
        families={
            # table 0x52f92a0: Context<.., &mut State<StateProviderDatabase<Box<dyn StateProvider>>>, Journal<..>> (symbols);
            # the database read below the journal is BalState::storage 0x29422e0 (stubbed), frame commit 0x1be722d-0x1be7245
            'A': dict(table=0x52f92a0, SLOAD=0x1f25060, SSTORE=0x1f28630, TLOAD=0x1f25810, TSTORE=0x1f2b740,
                      revert=0x2dafb40, checkpoint=0x4759ad0, commit=(0x1be722d, 0x1be7245), db='bal:29422e0',
                      sstore_hooks=[0x1f28811, 0x1f2890e], sstore_out=0x90),
        }),
    # conduit-op-reth v2.5.1 x86-64 (ghcr.io/conduitxyz/conduit-op-reth:v2.5.1, sha256 08b0e74a6242f365...), revm 43
    'conduit': dict(
        bin='/home/user/v4-core/research/network-risk/cycles/035/op-stack-eth.work/dl/conduit251/x/app/conduit-op-reth',
        fde='/home/user/v4-core/research/network-risk/cycles/035/op-stack-eth.work/build/c251.fde',
        seed_word=0x5c0bda8, seed_once=0x5c0bdd8, tls_word=0xfffffffffffff6e0, empty_group=0x4d47e0,
        got={0x5be4450: 'malloc', 0x5be4448: 'mallocx', 0x5be4460: 'rallocx', 0x5be4468: 'realloc', 0x5be4458: 'sdallocx',
             0x5be4470: 'calloc', 0x5be4488: 'memcpy', 0x5be4480: 'memmove', 0x5be44c8: 'memset', 0x5be4490: 'bcmp', 0x5be44b8: 'memcmp'},
        panics=[0x5a7db90, 0x406a2f3, 0x40665f0, 0x343ef99],
        layout=dict(inner=0x468, target=0x88, gas=0x190, static=0x1c8, spec=0x1c9, gasparams=0x440),
        acct_get=0x3b77b50, slot_entry=0x493b360, db_vt_off=0xd0, db_ok=0x31, err_none=0x32,
        families={
            # table 0x5aea5c0: dyn database (call [vtable+0xd0]), frame return 0x401a346 (commit 0x401a34d-0x401a363)
            'A': dict(table=0x5aea5c0, SLOAD=0x4025aa0, SSTORE=0x4025bf0, TLOAD=0x4026590, TSTORE=0x4026620,
                      revert=0x3b71260, checkpoint=0x3c1e230, commit=(0x401a34d, 0x401a363), db='dyn30',
                      sstore_hooks=[0x4025dbd, 0x4025eaf], sstore_out=0xd0),
        }),
}

HOST, INTERP, GASP, STACK, HEAP, VTAB, ARGS, EXT = 0x10000000, 0x11000000, 0x12000000, 0x13000000, 0x200000000, 0x14000000, 0x15000000, 0x16000000
SP0 = 0x7ffff0000000


_IMG = {}


class Machine:
    def __init__(self, prof, fam, seed, faults=None, spec=13, cache=None):
        P = PROFILES[prof]; self.P = P; self.F = P['families'][fam]; self.fam = fam
        L = dict(P['layout']); L.update(self.F.get('layout', {})); self.L = L
        INNER = HOST + L['inner']; self.INNER = INNER
        if prof not in _IMG: _IMG[prof] = open(os.path.join(HERE, '..', 'build', 'img-%s.bin' % prof), 'rb').read()
        img = _IMG[prof]
        cache = cache or os.path.join(HERE, '..', 'build', 'dis-%s' % prof)
        os.makedirs(cache, exist_ok=True)
        self.prog = LazyProg(P['bin'], P['fde'], cache)
        self.backing = {}; self.dbcalls = 0; self.allocs = {}; self.brk = HEAP
        ext = {}; got = {}
        names = {'malloc': self.x_malloc, 'mallocx': self.x_mallocx, 'rallocx': self.x_rallocx, 'realloc': self.x_realloc,
                 'sdallocx': self.x_sdallocx, 'memcpy': self.x_memcpy, 'memmove': self.x_memcpy, 'memset': self.x_memset,
                 'bcmp': self.x_bcmp, 'memcmp': self.x_memcmp, 'calloc': self.x_calloc}
        for i, (slot, nm) in enumerate(P['got'].items()):
            ext[EXT + 0x10 * i] = names[nm]; got[slot] = names[nm]
        for a in P['panics']: ext[a] = self.x_stop(a)
        ext[EXT + 0x800] = self.x_db
        self.slotmagic = {slot: EXT + 0x10 * i for i, slot in enumerate(P['got'])}
        self.hooks = {}
        self.cpu = CPU(self.prog, img, ext, got, faults or {}, self.hooks)
        w = self.cpu.write
        for slot, mg in self.slotmagic.items(): w(slot, 8, mg)
        rnd = random.Random(seed); self.rnd = rnd
        self.seeds = {'global': rnd.getrandbits(64), 'tls': rnd.getrandbits(64)}
        w(P['seed_word'], 8, self.seeds['global']); w(P['seed_once'], 1, 2)
        w((self.cpu.fs + P['tls_word']) & M64, 8, self.seeds['tls'])
        # interpreter frame
        w(INTERP + 0x30, 8, STACK); w(INTERP + 0x38, 8, 0)
        w(INTERP + L['gas'], 8, 30_000_000); w(INTERP + L['static'], 1, 0); w(INTERP + L['spec'], 1, spec)
        # host: gas parameter table pointer, journal inner, access list, database
        w(HOST + L['gasparams'], 8, GASP)
        self.vec_empty(INNER + 0x0, 8); self.vec_empty(INNER + 0x18, 8); self.vec_empty(INNER + 0x30, 1)
        for m in (INNER + 0xc8, INNER + 0xf0, INNER + 0x70):
            self.map_empty(m)
        w(INNER + 0x118, 8, 0); w(INNER + 0x120, 4, 1); w(INNER + 0x126, 1, spec)
        w(INNER + 0x128, 8, 0x77770000); w(INNER + 0x130, 8, VTAB); w(VTAB + P.get('db_vt_off', 0x30), 8, EXT + 0x800)
        if self.F['db'] == 'dyn30': w(INNER + 0x138, 1, P.get('err_none', 0xfe))
        if self.F['db'].startswith('bal:'): self.cpu.externs[int(self.F['db'][4:], 16)] = self.x_db_bal
        if self.F['db'].startswith('call:'): ext_db_target = int(self.F['db'][5:], 16); self.cpu.externs[ext_db_target] = self.x_db_state
        self.accounts = {}

    # ---- helpers
    def vec_empty(self, p, align):
        self.cpu.write(p, 8, 0); self.cpu.write(p + 8, 8, align); self.cpu.write(p + 0x10, 8, 0)

    def map_empty(self, p):
        w = self.cpu.write
        w(p, 8, self.P['empty_group']); w(p + 8, 8, 0); w(p + 0x10, 8, 0); w(p + 0x18, 8, 0); w(p + 0x20, 8, self.rnd.getrandbits(64))

    def rd(self, a, n): return self.cpu.read(a, n)
    def wr(self, a, n, v): self.cpu.write(a, n, v)
    def word(self, p): return self.rd(p, 32)
    def put_word(self, p, v): self.wr(p, 32, v & M)
    def put_addr(self, p, a): self.wr(p, 20, a)

    # ---- externs
    def x_stop(self, a):
        def f(cpu): raise Stop('panic path %x reached' % a)
        return f

    def _alloc(self, size, align=16):
        align = max(align, 16)
        self.brk = (self.brk + align - 1) // align * align
        p = self.brk; self.brk += max(size, 1) + 64
        if size <= 0x20000:
            self.cpu.write(p, size, int.from_bytes(b'\xa5' * size, 'little')) if size else None
        self.allocs[p] = size
        return p

    def x_malloc(self, cpu): cpu.r['rax'] = self._alloc(cpu.r['rdi'])
    def x_calloc(self, cpu):
        n = cpu.r['rdi'] * cpu.r['rsi']; p = self._alloc(n)
        if n: cpu.write(p, n, 0)
        cpu.r['rax'] = p

    def x_mallocx(self, cpu): cpu.r['rax'] = self._alloc(cpu.r['rdi'], 1 << (cpu.r['rsi'] & 0x3f))

    def _realloc(self, cpu, ptr, size, align):
        old = self.allocs.get(ptr)
        if old is None: raise Stop('realloc of unknown block %x' % ptr)
        q = self._alloc(size, align)
        n = min(old, size)
        if n: cpu.write(q, n, cpu.read(ptr, n))
        del self.allocs[ptr]
        return q

    def x_rallocx(self, cpu): cpu.r['rax'] = self._realloc(cpu, cpu.r['rdi'], cpu.r['rsi'], 1 << (cpu.r['rdx'] & 0x3f))
    def x_realloc(self, cpu): cpu.r['rax'] = self._realloc(cpu, cpu.r['rdi'], cpu.r['rsi'], 16)

    def x_sdallocx(self, cpu):
        p = cpu.r['rdi']
        if p not in self.allocs: raise Stop('free of unknown block %x' % p)
        if self.allocs[p] != cpu.r['rsi']: raise Stop('sized free with wrong size %x %x' % (self.allocs[p], cpu.r['rsi']))
        del self.allocs[p]

    def x_memcpy(self, cpu):
        d, s, n = cpu.r['rdi'], cpu.r['rsi'], cpu.r['rdx']
        if n: cpu.write(d, n, cpu.read(s, n))
        cpu.r['rax'] = d

    def x_memset(self, cpu):
        d, c, n = cpu.r['rdi'], cpu.r['rsi'] & 0xff, cpu.r['rdx']
        if n: cpu.write(d, n, int.from_bytes(bytes([c]) * n, 'little'))
        cpu.r['rax'] = d

    def x_bcmp(self, cpu):
        a, b, n = cpu.r['rdi'], cpu.r['rsi'], cpu.r['rdx']
        cpu.r['rax'] = 0 if cpu.read(a, n) == cpu.read(b, n) else 1

    def x_memcmp(self, cpu):
        a, b, n = cpu.r['rdi'], cpu.r['rsi'], cpu.r['rdx']
        x = cpu.read(a, n).to_bytes(n, 'little'); y = cpu.read(b, n).to_bytes(n, 'little')
        cpu.r['rax'] = 0 if x == y else (1 if x > y else M64)

    def x_db(self, cpu):
        """dyn database storage(out, self, &address, &key_be) -> Result<Option<U256>>: Ok(Some(v)), from the dict."""
        out, addrp, keyp = cpu.r['rdi'], cpu.r['rdx'], cpu.r['rcx']
        addr = cpu.read(addrp, 20)
        key = int.from_bytes(cpu.read(keyp, 32).to_bytes(32, 'little'), 'big')
        self.dbcalls += 1
        v = self.backing.get((addr, key), 0)
        cpu.write(out, 1, self.P.get('db_ok', 0xff)); cpu.write(out + 8, 1, 1); cpu.write(out + 0x10, 32, v)

    def x_db_state(self, cpu):
        """State<DB>::storage(out, self, address, key) of revm-database (the cache and bundle below the journal),
        stubbed: Ok(value) from the dict. The address and key arguments are checked against the frame's."""
        out = cpu.r['rdi']; a1, a2 = cpu.r['rdx'], cpu.r['rcx']
        addr = cpu.read(a1, 20); key = cpu.read(a2, 32)
        if addr not in self.accounts: raise Stop('state storage stub: address argument not recognised %x' % addr)
        self.dbcalls += 1
        v = self.backing.get((addr, key), 0)
        cpu.write(out, 1, self.F['db_ok_tag']); cpu.write(out + 0x08, 32, v)

    def x_db_bal(self, cpu):
        """World Chain: BalState::storage(out, self, &address, &key) -> Result<Option<U256>> below the journal,
        stubbed: Ok(Some(value)) from the dict (tag 0xff at out, Some flag 1 at out+8, value at out+0x10, as the
        caller sload_concrete_error 0x3e05a10 reads them at 0x3e06176-0x3e06265)."""
        out, a1, a2 = cpu.r['rdi'], cpu.r['rdx'], cpu.r['rcx']
        addr = cpu.read(a1, 20); key = cpu.read(a2, 32)
        if addr not in self.accounts: raise Stop('bal storage stub: address argument not recognised %x' % addr)
        self.dbcalls += 1
        v = self.backing.get((addr, key), 0)
        cpu.write(out, 1, 0xff); cpu.write(out + 8, 8, 1); cpu.write(out + 0x10, 32, v)

    # ---- running
    def run(self, entry, args, stop=None, regs=None):
        c = self.cpu
        for k in list(c.r): c.r[k] = 0
        c.y = [0] * 16
        for k, v in zip(['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9'], args): c.r[k] = v & M64
        for k, v in (regs or {}).items(): c.r[k] = v & M64
        rsp = SP0 - 0x8; ret = 0xdead0000
        c.write(rsp, 8, ret); c.r['rsp'] = rsp
        stop = ret if stop is None else stop
        pc = entry; c.budget = 0
        while pc != stop:
            pc = c.step(pc)
        return c.r['rax']

    def put_account(self, addr):
        """Places an account record (warm, not created, empty storage table, account_id None) in the account
        table, at the bucket the lifted lookup 0x4a4e6e0 probes for it (hash transcribed from that lookup)."""
        if addr in self.accounts: return
        INNER = self.INNER; P = INNER + 0xc8
        ctrl, mask, growth, items, seed = [self.rd(P + 8 * i, 8) for i in range(5)]  # same layout and hash in conduit 0x3b77b50 (identical body)
        if mask == 0:
            nb = 64
            size = nb * 0xa8 + nb + 16
            base = self._alloc(size, 16)
            ctrl = base + nb * 0xa8
            self.wr(ctrl, nb + 16, int.from_bytes(b'\xff' * (nb + 16), 'little'))
            mask = nb - 1; growth = nb * 7 // 8; items = 0
        a0 = addr & M64; a1 = (addr >> 64) & M64; a2 = addr >> 128
        g = self.seeds['global']
        x = ((a1 ^ g) * (a0 ^ seed)); lo, hi = x & M64, x >> 64
        y = (lo ^ (a2 ^ hi)) * g; h = ((y >> 64) ^ (y & M64)) & M64
        h2 = h >> 57; pos = h & mask; stride = 0
        while True:
            grp = [self.rd(ctrl + ((pos + i) & mask) if False else ctrl + pos + i, 1) for i in range(16)]
            e = [i for i, b in enumerate(grp) if b & 0x80]
            if e:
                idx = (pos + e[0]) & mask; break
            stride += 16; pos = (pos + stride) & mask
        self.wr(ctrl + idx, 1, h2); self.wr(ctrl + ((idx - 16) & mask) + 16, 1, h2)
        bucket = ctrl - (idx + 1) * 0xa8
        self.wr(bucket, 0xa8, 0)
        self.put_addr(bucket, addr)
        acct = bucket + 0x18
        self.map_empty(acct)                 # storage table at +0x00
        self.wr(acct + 0x88, 4, self.rd(INNER + 0x120, 4))   # transaction id
        self.wr(acct + 0x8c, 1, 0)           # status: warm, not created, not touched
        self.wr(P + 0, 8, ctrl); self.wr(P + 8, 8, mask); self.wr(P + 0x10, 8, growth - 1); self.wr(P + 0x18, 8, items + 1)
        self.accounts[addr] = acct
        got = self.run(self.P['acct_get'], [P, self._addr_arg(addr)])
        if got != acct: raise Stop('placed account not found by lifted lookup: %x vs %x' % (got, acct))

    def _addr_arg(self, addr):
        self.put_addr(ARGS, addr); return ARGS

    def set_target(self, addr):
        self.put_addr(INTERP + self.L['target'], addr)

    def push(self, v):
        n = self.rd(INTERP + 0x38, 8); self.put_word(STACK + 32 * n, v); self.wr(INTERP + 0x38, 8, n + 1)

    def pop(self):
        n = self.rd(INTERP + 0x38, 8) - 1; self.wr(INTERP + 0x38, 8, n); return self.word(STACK + 32 * n)

    def handler(self, name):
        r = self.run(self.F[name], [INTERP, HOST]) & 0xff
        if r != 0: raise Stop('%s returned %#x' % (name, r))

    def sload(self, addr, key):
        self.set_target(addr); self.push(key); self.handler('SLOAD'); return self.pop()

    def tload(self, addr, key):
        self.set_target(addr); self.push(key); self.handler('TLOAD'); return self.pop()

    def tstore(self, addr, key, val):
        self.set_target(addr); self.push(val); self.push(key); self.handler('TSTORE')

    def sstore(self, addr, key, val):
        res = []
        def grab(cpu):
            o = cpu.r['rsp'] + self.F['sstore_out']
            res.append((self.word(o), self.word(o + 0x20), self.word(o + 0x40), self.rd(o + 0x60, 1)))
        for h in self.F['sstore_hooks']: self.hooks[h] = grab
        self.set_target(addr); self.push(val); self.push(key); self.wr(INTERP + self.L['gas'], 8, 30_000_000)
        self.handler('SSTORE')
        for h in self.F['sstore_hooks']: self.hooks.pop(h, None)
        return res[0] if res else None

    def checkpoint(self):
        self.wr(ARGS + 0x200, 8, self.INNER)
        self.run(self.F['checkpoint'], [ARGS + 0x100, ARGS + 0x200])
        return tuple(self.rd(ARGS + 0x100 + 8 * i, 8) for i in range(3))

    def commit(self):
        a, b = self.F['commit']
        self.run(a, [], stop=b, regs={self.F.get('commit_reg', 'rdx'): HOST})

    def revert(self, cp):
        for i, v in enumerate(cp): self.wr(ARGS + 0x300 + 8 * i, 8, v)
        self.run(self.F['revert'], [self.INNER, ARGS + 0x300])

    def depth(self): return self.rd(self.INNER + 0x118, 8)
    def jlen(self): return self.rd(self.INNER + 0x28, 8)

    def entries(self):
        p = self.rd(self.INNER + 0x20, 8); n = self.jlen()
        return [self.rd(p + 0x58 * i, 0x58).to_bytes(0x58, 'little') for i in range(n)]

    def slot_record(self, addr, key):
        """Reads the slot record (original, present) through the storage table of the account (lifted entry())."""
        acct = self.accounts[addr]
        self.put_word(ARGS + 0x40, key)
        self.run(self.P['slot_entry'], [ARGS + 0x80, acct, ARGS + 0x40])
        occ = self.rd(ARGS + 0x80, 8)
        if occ != 0: return None
        b = self.rd(ARGS + 0x88, 8)
        return self.word(b - 0x48), self.word(b - 0x28)
