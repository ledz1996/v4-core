"""Cycle 39, theme-end-of-transaction-clear-lift, Tasks 1 and 5.

Runs the out-of-line JournalInner::commit_tx and JournalInner::discard_tx of a shipped reth-derived binary (found by
txpanic.py and callers.py; every TransactionId increment of the binary sits in one of them) on a populated journal,
in the cycle 27-38 x86-64 model (objdump text interpreted in Python; nothing from the binary is executed or loaded).

State before the routine, built by the lifted handlers and frame code (TSTORE, SSTORE, checkpoint, commit, revert),
except where marked "by hand":
  - transient words of the PoolManager: the lock (Lock.sol slot), the nonzero delta count, three currency deltas,
    the synced currency and reserves, plus random keys on two other accounts; values 1, 2, 2^256-1 or random;
  - storage writes in nested frames, some frames reverted, some committed, some left open (depth > 0, as after a
    halt that unwinds without commit);
  - by hand: 0 to 5 logs (topics vector allocated from the model allocator, data Bytes with a vtable whose drop is
    counted), the third list (+0x30, selfdestructed addresses), the access list map (+0x70, inner key sets allocated
    or empty), the coinbase flag (+0xb0) and a random transaction id.
Checks afterwards: transient map holds no item and every control byte is EMPTY, every written transient word reads
zero through the lifted TLOAD, depth 0, journal length 0, logs length 0 with every topic block freed and every data
drop called, third list length 0, access list empty with every inner block freed, coinbase flag 0, transaction id
advanced by one; for discard every storage slot is back at its original value, for commit every slot keeps its
present value. A next transaction then writes the lock through the lifted TSTORE and reads it back.

usage: python3 -I txrun39.py <profile> <kind:commit|discard> <fn hex> <n> <seed> <out.json> [fault-json-key]
"""
import json, os, random, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(HERE)
PROF, KIND, FN, N, SEED, OUT = sys.argv[1], sys.argv[2], int(sys.argv[3], 16), int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
FAULT = sys.argv[7] if len(sys.argv) > 7 else None

RETH = {'opreth2100': ('opreth', 'A'), 'opreth281': ('opreth281', 'B'), 'base156': ('base', 'A'),
        'wc282': ('worldchain', 'A'), 'conduit251': ('conduit', 'A')}
CEL = {'xlayer0073': ('xlj', 'xlayer', 'A'), 'arc086': ('arcj', 'arc', 'A'), 'celo1010': ('celoj', 'celo', 'A')}
if PROF in RETH:
    sys.path.insert(0, W + '/m/scripts')
    import rethj as MOD
    MP, FAM = RETH[PROF]
    TXSZ = 4
else:
    sys.path.insert(0, W + '/mc/scripts')
    import importlib
    MOD = importlib.import_module(CEL[PROF][0]); MP, FAM = CEL[PROF][1], CEL[PROF][2]
    TXSZ = MOD.PROFILES[MP]['layout'].get('txid_size', 8)
Machine, Stop = MOD.Machine, MOD.Stop
M64 = (1 << 64) - 1

LOCK = 0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23   # src/libraries/Lock.sol IS_UNLOCKED_SLOT
NZDC = 0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b   # NonzeroDeltaCount.sol slot
RCUR = 0x1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95   # CurrencyReserves.sol currency slot
RVAL = 0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9   # CurrencyReserves.sol reserves slot
A0 = 0x000000000004444c5dc75cb358380d2e3de08a90; A1 = 0x66a9893cc07d91d95644aedd05d03f95e1dba8af; A2 = 0xc0de0002
DELTAS = [random.Random(7000 + i).getrandbits(256) for i in range(3)]      # three currency delta words
TKEYS = [LOCK, NZDC, RCUR, RVAL] + DELTAS + [random.Random(i).getrandbits(256) for i in range(9)]
SKEYS = [0, 6, 7, random.Random(99).getrandbits(256)]
EMPTY_CTRL = 0xff


class Bad(Exception):
    pass


def new_machine(seed, faults):
    if PROF in RETH:
        return Machine(MP, FAM, seed, faults=faults)
    return Machine(MP, FAM, seed, faults=faults, spec=0x12)


def J_of(mc):
    return mc.INNER


def alloc(mc, n, align=16):
    return mc._alloc(n, align)


def build_hand_state(mc, r, drops):
    """Logs, third list, access list, coinbase flag and transaction id placed by hand (see module docstring)."""
    J = J_of(mc)
    ext = (MOD.EXT if hasattr(MOD, 'EXT') else sys.modules['celoj'].EXT) + 0xf00
    mc.cpu.externs[ext] = lambda cpu: drops.append(cpu.r['rdi'])
    vt = alloc(mc, 0x40); mc.wr(vt, 0x40, 0); mc.wr(vt + 0x20, 8, ext)
    nlog = r.randint(0, 5); topics = []
    if nlog:
        lp = alloc(mc, nlog * 0x50, 8)
        for i in range(nlog):
            e = lp + 0x50 * i; mc.wr(e, 0x50, 0)
            nt = r.randint(0, 4)
            if nt:
                tp = alloc(mc, nt * 32); mc.wr(e, 8, nt); mc.wr(e + 8, 8, tp); mc.wr(e + 0x10, 8, nt); topics.append(tp)
            else:
                mc.wr(e + 8, 8, 8)
            mc.wr(e + 0x18, 8, vt); mc.wr(e + 0x20, 8, 0x1234500 + i); mc.wr(e + 0x28, 8, r.randint(0, 200)); mc.wr(e + 0x30, 8, 0xabc000 + i)
            mc.put_addr(e + 0x38, r.choice((A0, A1, A2)))
        mc.wr(J + 0x0, 8, nlog); mc.wr(J + 0x8, 8, lp); mc.wr(J + 0x10, 8, nlog)
    nsd = r.randint(0, 3)
    if nsd:
        sp = alloc(mc, nsd * 20, 1); mc.wr(sp, nsd * 20, r.getrandbits(160 * nsd))
        mc.wr(J + 0x30, 8, nsd); mc.wr(J + 0x38, 8, sp); mc.wr(J + 0x40, 8, nsd)
    # access list: hashbrown table of (Address, HashSet<U256>) buckets of 0x40 bytes
    inner_blocks = []
    nal = r.randint(0, 6)
    if nal:
        nb = 8; cap = 7
        base = alloc(mc, nb * 0x40 + nb + 16); ctrl = base + nb * 0x40
        mc.wr(ctrl, nb + 16, int.from_bytes(b'\xff' * (nb + 16), 'little'))
        slots = r.sample(range(nb), nal)
        for i in slots:
            h2 = r.randint(0, 0x7f); mc.wr(ctrl + i, 1, h2); mc.wr(ctrl + ((i - 16) & (nb - 1)) + 16, 1, h2)
            e = ctrl - (i + 1) * 0x40; mc.wr(e, 0x40, 0); mc.put_addr(e, r.getrandbits(160))
            if r.random() < 0.6:
                m = 3; sz = (m + 1) * 32 + (m + 1) + 16; blk = alloc(mc, sz); ic = blk + (m + 1) * 32
                mc.wr(ic, m + 1 + 16, int.from_bytes(b'\xff' * (m + 1 + 16), 'little')); mc.wr(ic, 1, 0x11)
                mc.wr(e + 0x18, 8, ic); mc.wr(e + 0x20, 8, m); mc.wr(e + 0x28, 8, 2); mc.wr(e + 0x30, 8, 1)
                inner_blocks.append(blk)
            else:
                mc.wr(e + 0x18, 8, mc.P['empty_group']); mc.wr(e + 0x20, 8, 0); mc.wr(e + 0x28, 8, 0); mc.wr(e + 0x30, 8, 0)
            mc.wr(e + 0x38, 8, r.getrandbits(64))
        mc.wr(J + 0x70, 8, ctrl); mc.wr(J + 0x78, 8, nb - 1); mc.wr(J + 0x80, 8, cap - nal); mc.wr(J + 0x88, 8, nal)
    mc.wr(J + 0xb0, 1, 1)
    # transaction id: NonMaxU32 stored as id ^ 0xffffffff (TXSZ 4) or a plain usize (TXSZ 8)
    if TXSZ == 4: mc.wr(J + 0x120, 4, r.randint(2, 0xffffffff))
    else: mc.wr(J + 0x120, 8, r.getrandbits(r.choice((8, 32, 62))))
    return dict(nlog=nlog, topics=topics, nsd=nsd, nal=nal, inner=inner_blocks)


def one(seed, faults):
    r = random.Random(seed)
    mc = new_machine(seed, faults)
    J = J_of(mc)
    for a in (A0, A1, A2): mc.put_account(a)
    written = set(); slots = {}
    opened = []
    for _ in range(r.randint(1, 40)):
        c = r.random(); a = r.choice((A0, A0, A1, A2))
        if c < 0.4:
            k = r.choice(TKEYS); mc.tstore(a, k, r.choice((1, 2, (1 << 256) - 1, r.getrandbits(256)))); written.add((a, k))
        elif c < 0.6:
            k = r.choice(SKEYS); mc.sstore(a, k, r.getrandbits(64)); slots[(a, k)] = None
        elif c < 0.8 and len(opened) < 6:
            opened.append(mc.checkpoint())
        elif opened:
            cp = opened.pop()
            if r.random() < 0.5: mc.revert(cp)
            else: mc.commit()
    for k in (LOCK, NZDC, RCUR, DELTAS[0]):
        if (A0, k) not in written:
            mc.tstore(A0, k, 1); written.add((A0, k))
    before = {s: mc.slot_record(*s) for s in slots}
    drops = []
    hs = build_hand_state(mc, r, drops)
    depth0, jlen0 = mc.depth(), mc.jlen()
    titems0 = mc.rd(J + 0x108, 8)
    tid0 = mc.rd(J + 0x120, TXSZ)
    if KIND == 'finalize':
        # Task 3 (L-1350): finalize takes the state map with mem::take, whose HashMap::default() reads the
        # per-thread hasher keys through slot 0x52b8b08 -> 0x50b23b0 (std RandomState::new: TLS flag at fs-0x80,
        # k0 at fs-0x88 incremented). With the flag set, as on every thread after its first map, no initialiser
        # (0x50b23f0, the getrandom path) runs. fs:0 holds the thread pointer itself, as on x86-64 Linux.
        fs = mc.cpu.fs; mc.wr(fs, 8, fs); mc.wr(fs - 0x80, 1, 1); k0 = r.getrandbits(64) & ~1; mc.wr(fs - 0x88, 8, k0)
        st_hdr = [mc.rd(J + 0xc8 + 8 * i, 8) for i in range(4)]
        out = MOD.ARGS + 0x800 if hasattr(MOD, 'ARGS') else sys.modules['celoj'].ARGS + 0x800
        mc.run(FN, [out, J])
        if [mc.rd(out + 8 * i, 8) for i in range(4)] != st_hdr: raise Bad('finalize: returned state is not the old table')
        if mc.rd(J + 0xe0, 8) != 0 or mc.rd(J + 0xd0, 8) != 0: raise Bad('finalize: journal state map not empty')
        if mc.rd(fs - 0x88, 8) != (k0 + 1) & M64: raise Bad('finalize: thread key not advanced')
        if mc.rd(J + 0x120, TXSZ) != 0: raise Bad('finalize: transaction id %x not reset' % mc.rd(J + 0x120, TXSZ))
        tid0 = None
    else:
        mc.run(FN, [J])
    # ---- checks
    if mc.depth() != 0: raise Bad('depth %d after %s (was %d)' % (mc.depth(), KIND, depth0))
    if mc.jlen() != 0: raise Bad('journal length %d after %s (was %d)' % (mc.jlen(), KIND, jlen0))
    if mc.rd(J + 0x10, 8) != 0: raise Bad('logs length %d after %s' % (mc.rd(J + 0x10, 8), KIND))
    if mc.rd(J + 0x40, 8) != 0: raise Bad('third list length %d after %s' % (mc.rd(J + 0x40, 8), KIND))
    if mc.rd(J + 0x108, 8) != 0: raise Bad('transient items %d after %s (was %d)' % (mc.rd(J + 0x108, 8), KIND, titems0))
    tc, tm = mc.rd(J + 0xf0, 8), mc.rd(J + 0xf8, 8)
    if tm and any(mc.rd(tc + i, 1) != EMPTY_CTRL for i in range(tm + 1)): raise Bad('transient control byte not EMPTY')
    if mc.rd(J + 0x88, 8) != 0: raise Bad('access list items %d after %s' % (mc.rd(J + 0x88, 8), KIND))
    if mc.rd(J + 0xb0, 1) != 0: raise Bad('coinbase flag %d after %s' % (mc.rd(J + 0xb0, 1), KIND))
    for t in hs['topics'] + hs['inner']:
        if t in mc.allocs: raise Bad('block %x not freed by %s' % (t, KIND))
    if len(drops) != hs['nlog']: raise Bad('%d of %d log data drops called' % (len(drops), hs['nlog']))
    tid = mc.rd(J + 0x120, TXSZ)
    exp = None if tid0 is None else ((tid0 - 1) if TXSZ == 4 else (tid0 + 1) & M64)
    if tid0 is not None and tid != exp: raise Bad('transaction id stored %x after %x, expected %x' % (tid, tid0, exp))
    if KIND == 'finalize':
        before = {}; mc.accounts = {}
        for a in (A0, A1, A2): mc.put_account(a)
    for s, rec in before.items():
        now = mc.slot_record(*s)
        if KIND == 'discard':
            if now is None or now[0] != now[1]: raise Bad('discard: slot %x/%x original,present %s' % (s[0], s[1], now))
        elif now != rec: raise Bad('commit: slot %x/%x %s became %s' % (s[0], s[1], rec, now))
    for (a, k) in sorted(written):
        v = mc.tload(a, k)
        if v != 0: raise Bad('next transaction reads transient %x/%x = %x' % (a, k, v))
    mc.tstore(A0, LOCK, 1)
    if mc.tload(A0, LOCK) != 1: raise Bad('next transaction cannot write transient')
    return dict(depth0=depth0, jlen0=jlen0, titems0=titems0, nlog=hs['nlog'], nal=hs['nal'], nsd=hs['nsd'], words=len(written))


def load_faults():
    if not FAULT: return {}
    f = json.load(open(os.path.join(W, 'out', 'faults39.json')))['%s:%x' % (PROF, FN)][FAULT]
    return {int(k, 16): v for k, v in f.items()}


if __name__ == '__main__':
    faults = load_faults()
    res = dict(profile=PROF, kind=KIND, fn='%#x' % FN, seed=SEED, fault=FAULT, cases=0, bad=0, errors=0, records=[],
               started=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), max_depth=0, max_jlen=0, transient_words=0,
               logs=0, access_list_entries=0, open_depth_cases=0)
    for i in range(N):
        res['cases'] += 1; sd = SEED * 1000003 + i
        try:
            st = one(sd, faults)
            res['max_depth'] = max(res['max_depth'], st['depth0']); res['max_jlen'] = max(res['max_jlen'], st['jlen0'])
            res['transient_words'] += st['words']; res['logs'] += st['nlog']; res['access_list_entries'] += st['nal']
            res['open_depth_cases'] += st['depth0'] > 0
        except Bad as e:
            res['bad'] += 1; res['records'].append(dict(case=i, seed=sd, detail=str(e)))
            if FAULT: break
        except Stop as e:
            res['errors'] += 1; res['records'].append(dict(case=i, seed=sd, stop=str(e)))
            if FAULT or res['errors'] > 5: break
    res['fault_hits'] = None
    res['finished'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    json.dump(res, open(OUT, 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != 'records'}), res['records'][:2])
