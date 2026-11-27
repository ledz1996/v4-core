"""Cycle 37, theme-celo-xlayer-arc-journal-lift: the storage, transient storage and journal routines of the published
celo-reth v1.0.10 (revm-context 18.0.3 family, glibc allocator, foldhash and seeded Fx hashers) run in the cycle 27-36
x86-64 model. Nothing from the downloaded binary is executed, loaded or dlopened: its objdump text is interpreted in
Python (x86emu.py / x86emu2.py / the cycle 36 rethj.py CPU and lazy program), and its bytes are read as data from a
memory image built with image.py (PT_LOAD segments, RELATIVE relocations applied).

Only these are modelled in Python:
  - glibc malloc, free, calloc, realloc, posix_memalign, memcpy, memmove, memset, bcmp, memcmp (GLOB_DAT slots);
  - the database read below the journal (`<&mut State<..> as Database>::storage`, stubbed: Ok(value) from a dict);
  - the foldhash global seed word and its Once flag, and the per-map hasher words (random from the seed);
  - the interpreter halt routines (a halt raises Stop, so no case can pass through one silently).
The account table, the per-account storage tables, the transient table, the journal vector and the depth counter are
real structures in model memory, built and changed only by the lifted code, except that the first account record of
each test address is placed in the account table by Python (put_account, hash transcribed from the lookup inlined at
0x1dde53e-0x1dde5a0) and is then found by the lifted lookup of every handler call.
"""
import os, random, re, sys
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/036/theme-worldchain-zora-journal-lift.work/scripts')
import rethj as R
from rethj import LazyProg, Stop, M, M64
import x86emu

HERE = os.path.dirname(os.path.abspath(__file__))
HOST, INTERP, GASP, STACK, HEAP, DBOBJ, ARGS, EXT = R.HOST, R.INTERP, R.GASP, R.STACK, R.HEAP, R.VTAB, R.ARGS, R.EXT
SP0 = R.SP0
CELO_BIN = '/home/user/v4-core/research/network-risk/cycles/035/theme-reth-keccak-asm-image-lift.work/dl/celo-v1.0.10/x/usr/local/bin/celo-reth'
CELO_FDE = '/home/user/v4-core/research/network-risk/cycles/036/theme-reth-images-handler-lift.work/build/celo.fde'

PROFILES = {
    # celo-reth v1.0.10 (ghcr image of cycle 35, binary sha256 ca81b870...cbfac, reth/v2.2.0-74cc8bb), symbols
    'celo': dict(
        bin=CELO_BIN, fde=CELO_FDE, img='img-celo.bin',
        got={0x52b83f8: 'malloc', 0x52b8418: 'free', 0x52b8420: 'memcpy', 0x52b8428: 'bcmp', 0x52b8430: 'memmove',
             0x52b8460: 'posix_memalign', 0x52b84c8: 'memcmp', 0x52b85d0: 'calloc', 0x52b8928: 'memset', 0x52b94c8: 'realloc'},
        # halt_oog, halt_fatal, halt (revm_interpreter::Interpreter::*), and the targets of the halt slots the handlers jump to
        halts=[0x35f47e0, 0x35f46d0, 0x35f4770], halt_slots=[0x52be360, 0x52be3a0, 0x52be388, 0x52be1e8, 0x52be390],
        panics=[], seed_word=0x5323e90, seed_once=0x5323e90 + 0x30, empty_group=0x6d5010,
        layout=dict(target=0x80, gas=0x190, static=0x1b0, spec=0x1b1, gasparams=0x378, J=0x550, err=0x520, err_none=0x2e,
                    db=0x680, txid=0x120),
        acct_stride=0xb8, acct_off=0x18, acct_storage=0x68, acct_status=0x98, acct_txid=0x90, slot_stride=0x70,
        families={
            # table 0x514d468: Context<.., &mut State<StateProviderDatabase<CachedStateProvider<..>>>, ..> (engine block
            # validation, reached through reth_execution_cache::cached_state::CachedStateProvider); DB read 0x36475d0
            'A': dict(table=0x514d468, SLOAD=0x1e5a260, SSTORE=0x1e62160, TLOAD=0x1e5bf90, TSTORE=0x1e63f10,
                      revert=0x1d61dd0, checkpoint=0x1f36450, commit=0x1f37e30, db=0x36475d0, db_ok=0x2d,
                      sstore_hooks=[0x1e622a5, 0x1e62347], sstore_out=0x60),
            # table 0x5151468: Context<.., &mut State<CachedReadsDbMut<..>>, ..> (payload builder, the sequencer)
            'P': dict(table=0x5151468, SLOAD=0x1e5a3b0, SSTORE=0x1e63330, TLOAD=0x1e5bf90, TSTORE=0x1e63f10,
                      revert=0x1d61dd0, checkpoint=0x1f36450, commit=0x1f37e30, db=0x3645490, db_ok=0x2d,
                      sstore_hooks=None, sstore_out=None),
        }),
}


class CCPU(R.CPU):
    """rethj CPU with calls and jumps through absolute memory words (GOT slots, RELATIVE or modelled) followed."""
    def _slot(self, s):
        m = re.match(r'^QWORD PTR \[0x([0-9a-f]+)\]$', s)
        return int(m.group(1), 16) if m else None

    def i_call(self, o, pc, n):
        sl = self._slot(o[0])
        if sl is not None:
            t = self.read(sl, 8)
            if t in self.externs: self.externs[t](self); return n
            if t == 0: raise Stop('call through empty slot %x' % sl)
            self.r['rsp'] -= 8; self.write(self.r['rsp'], 8, n); return t
        return super().i_call(o, pc, n)

    def i_jmp(self, o, pc, n):
        sl = self._slot(o[0])
        if sl is not None:
            t = self.read(sl, 8)
            if t in self.externs:
                self.externs[t](self); a = self.read(self.r['rsp'], 8); self.r['rsp'] += 8; return a
            if t == 0: raise Stop('jump through empty slot %x' % sl)
            return t
        if o[0] not in self.r and re.match(r'^[0-9a-f]+$', o[0]):
            t = int(o[0], 16)
            if t in self.externs:
                self.externs[t](self); a = self.read(self.r['rsp'], 8); self.r['rsp'] += 8; return a
        return super().i_jmp(o, pc, n)


_IMG = {}


class Machine(R.Machine):
    def __init__(self, prof, fam, seed, faults=None, spec=0x12, cache=None):
        P = PROFILES[prof]; self.P = P; self.F = P['families'][fam]; self.fam = fam
        L = dict(P['layout']); self.L = L
        self.J = HOST + L['J']; self.INNER = self.J
        if prof not in _IMG: _IMG[prof] = open(os.path.join(HERE, '..', 'build', P['img']), 'rb').read()
        img = _IMG[prof]
        cache = cache or os.path.join(HERE, '..', 'build', 'dis-%s' % prof)
        os.makedirs(cache, exist_ok=True)
        self.prog = LazyProg(P['bin'], P['fde'], cache)
        self.backing = {}; self.dbcalls = 0; self.allocs = {}; self.brk = HEAP
        names = {'malloc': self.x_malloc, 'free': self.x_free, 'mallocx': self.x_mallocx, 'rallocx': self.x_rallocx,
                 'sdallocx': self.x_sdallocx, 'memcpy': self.x_memcpy, 'memmove': self.x_memcpy,
                 'memset': self.x_memset, 'bcmp': self.x_bcmp, 'memcmp': self.x_memcmp, 'calloc': self.x_calloc,
                 'realloc': self.x_realloc, 'posix_memalign': self.x_posix_memalign}
        ext = {}
        for i, (slot, nm) in enumerate(P['got'].items()): ext[EXT + 0x10 * i] = names[nm]
        for a in P['halts'] + P['panics']: ext[a] = self.x_stop(a)
        ext[self.F['db']] = self.x_db_celo
        for a in self.F.get('db_other', []): ext[a] = self.x_stop(a)
        for nm, a in P.get('alloc_fns', {}).items(): ext[a] = names[nm]
        self.hooks = {}
        self.cpu = CCPU(self.prog, img, ext, {}, faults or {}, self.hooks)
        w = self.cpu.write
        for i, slot in enumerate(P['got']): w(slot, 8, EXT + 0x10 * i)
        for s in P['halt_slots']:
            t = self.cpu.read(s, 8); ext[t] = self.x_stop(t)
        rnd = random.Random(seed); self.rnd = rnd
        self.seeds = {'global': rnd.getrandbits(64)}
        w(P['seed_word'], 8, self.seeds['global'])
        if P.get('seed_once'): w(P['seed_once'], 1, 2)
        if P.get('empty_group') is None:
            P = dict(P); self.P = P; P['empty_group'] = self._alloc(32, 16)
            w(P['empty_group'], 32, (1 << 256) - 1)
        # interpreter
        w(INTERP + 0x30, 8, STACK); w(INTERP + 0x38, 8, 0)
        w(INTERP + L['gas'], 8, 30_000_000); w(INTERP + L['static'], 1, 0); w(INTERP + L['spec'], 1, spec)
        # host: gas parameter table (zero), error slot empty, database pointer, journal inner
        w(HOST + L['gasparams'], 8, GASP); w(HOST + L['err'], 1, L['err_none']); w(HOST + L['db'], 8, DBOBJ)
        J = self.J
        self.vec_empty(J + 0x0, 8); self.vec_empty(J + 0x18, 8); self.vec_empty(J + 0x30, 8)
        self.map_empty(J + 0x70); self.map_empty(J + 0xc8); self.map_empty(J + 0xf0)
        w(J + 0x118, 8, 0); w(J + L['txid'], L.get('txid_size', 8), 1); w(J + L.get('jspec', 0x12a), 1, spec)
        self.accounts = {}

    def map_empty(self, p):
        w = self.cpu.write
        w(p, 8, self.P['empty_group']); w(p + 8, 8, 0); w(p + 0x10, 8, 0); w(p + 0x18, 8, 0); w(p + 0x20, 8, self.rnd.getrandbits(64))

    # ---- glibc allocator
    def x_free(self, cpu):
        p = cpu.r['rdi']
        if p == 0: return
        if p not in self.allocs: raise Stop('free of unknown block %x' % p)
        del self.allocs[p]

    def x_posix_memalign(self, cpu):
        out, al, n = cpu.r['rdi'], cpu.r['rsi'], cpu.r['rdx']
        cpu.write(out, 8, self._alloc(n, al)); cpu.r['rax'] = 0

    def x_db_celo(self, cpu):
        """`<&mut State<..> as Database>::storage(out, &db, &address, &key)` stubbed: Ok(value) (tag at out, U256
        limbs at out+8, as sload_concrete_error 0x35f9114-0x35f912a reads them). Address and key are checked."""
        out, a1, a2 = cpu.r['rdi'], cpu.r['rdx'], cpu.r['rcx']
        selfp = cpu.r['rsi'] if self.F.get('db_self_direct') else cpu.read(cpu.r['rsi'], 8)
        if selfp != DBOBJ: raise Stop('db stub: self argument not the database pointer')
        addr = cpu.read(a1, 20); key = cpu.read(a2, 32)
        if addr not in self.accounts: raise Stop('db stub: address argument not recognised %x' % addr)
        self.dbcalls += 1
        cpu.write(out, self.F.get('db_ok_size', 1), self.F['db_ok']); cpu.write(out + 8, 32, self.backing.get((addr, key), 0))

    # ---- accounts
    def put_account(self, addr):
        if addr in self.accounts: return
        P = self.J + 0xc8; S = self.P['acct_stride']
        ctrl, mask, growth, items, seed = [self.rd(P + 8 * i, 8) for i in range(5)]
        if mask == 0:
            nb = 64; base = self._alloc(nb * S + nb + 16, 16); ctrl = base + nb * S
            self.wr(ctrl, nb + 16, int.from_bytes(b'\xff' * (nb + 16), 'little'))
            mask = nb - 1; growth = nb * 7 // 8; items = 0
        K = 0xf1357aea2e62a9c5
        a0 = addr & M64; a1 = (addr >> 64) & M64; a2 = addr >> 128
        x = (((((a0 + seed) & M64) * K) & M64) + a1) & M64
        x = (((x * K) & M64) + a2) & M64
        x = (x * K) & M64
        h = ((x << 26) | (x >> 38)) & M64
        h2 = h >> 57; pos = h & mask; stride = 0
        while True:
            grp = [self.rd(ctrl + ((pos + i) & mask), 1) for i in range(16)]
            e = [i for i, b in enumerate(grp) if b & 0x80]
            if e: idx = (pos + e[0]) & mask; break
            stride += 16; pos = (pos + stride) & mask
        self.wr(ctrl + idx, 1, h2); self.wr(ctrl + ((idx - 16) & mask) + 16, 1, h2)
        bucket = ctrl - (idx + 1) * S
        self.wr(bucket, S, 0); self.put_addr(bucket, addr)
        acct = bucket + self.P['acct_off']
        self.map_empty(acct + self.P['acct_storage'])
        ts = self.L.get('txid_size', 8)
        self.wr(acct + self.P['acct_txid'], ts, self.rd(self.J + self.L['txid'], ts))
        self.wr(acct + self.P['acct_status'], 1, 0)
        self.wr(P + 0, 8, ctrl); self.wr(P + 8, 8, mask); self.wr(P + 0x10, 8, growth - 1); self.wr(P + 0x18, 8, items + 1)
        self.accounts[addr] = acct

    def handler(self, name):
        r = self.run(self.F[name], [INTERP, HOST]) & 0xff
        if self.P.get('status_return') and r != 0: raise Stop('%s returned %#x' % (name, r))

    def checkpoint(self):
        self.wr(ARGS + 0x200, 8, self.J)
        self.run(self.F['checkpoint'], [ARGS + 0x100, ARGS + 0x200])
        return tuple(self.rd(ARGS + 0x100 + 8 * i, 8) for i in range(3))

    def commit(self):
        self.wr(ARGS + 0x208, 8, self.J)
        self.run(self.F['commit'], [ARGS + 0x208])

    def revert(self, cp):
        for i, v in enumerate(cp): self.wr(ARGS + 0x300 + 8 * i, 8, v)
        self.run(self.F['revert'], [self.J, ARGS + 0x300])

    def depth(self): return self.rd(self.J + 0x118, 8)
    def jlen(self): return self.rd(self.J + 0x28, 8)

    def entries(self):
        p = self.rd(self.J + 0x20, 8); n = self.jlen()
        return [self.rd(p + 0x58 * i, 0x58).to_bytes(0x58, 'little') for i in range(n)]

    def slot_record(self, addr, key):
        """(original, present) of the slot, read from the account's storage table by walking its control bytes."""
        m = self.accounts[addr] + self.P['acct_storage']
        ctrl, mask = self.rd(m, 8), self.rd(m + 8, 8)
        if mask == 0: return None
        S = self.P['slot_stride']
        for i in range(mask + 1):
            if self.rd(ctrl + i, 1) & 0x80: continue
            b = ctrl - (i + 1) * S
            if self.word(b) == key: return self.word(b + 0x20), self.word(b + 0x40)
        return None

    def transient_words(self):
        m = self.J + 0xf0; ctrl, mask = self.rd(m, 8), self.rd(m + 8, 8); out = {}
        if mask == 0: return out
        for i in range(mask + 1):
            if self.rd(ctrl + i, 1) & 0x80: continue
            b = ctrl - (i + 1) * 0x58
            out[(self.rd(b, 20), self.word(b + 0x18))] = self.word(b + 0x38)
        return out


def _sstore(self, addr, key, val):
    if self.F.get('sstore_hooks'):
        return R.Machine.sstore(self, addr, key, val)
    # handler with the SStoreResult inlined into its gas code (X Layer): no hook; the caller checks the slot record
    self.set_target(addr); self.push(val); self.push(key); self.wr(INTERP + self.L['gas'], 8, 30_000_000)
    self.handler('SSTORE')
    return None


Machine.sstore = _sstore
