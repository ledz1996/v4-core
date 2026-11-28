"""Cycle 38 copy (theme-frame-checkpoint-and-commit-lift): family F runs the frame code's own checkpoint, commit and revert (framepatch.py).
Cycle 37 copy (op-stack-eth, lead L-1289): adds MODE churn (argument 8), transient-only sequences that grow,
shrink and refill the two-level transient table so that the inner-map reserve and rehash routines run.
Task 2 and Task 3 harness: nested-frame storage and transient storage sequences through the lifted op-reth / Base
journal (rethj.py), checked after every commit and every revert against a transcription of the revm 43 journal
rules (journal length, present and original value of every slot in the tables, every transient word), and at the
end against pyevm.py run on bytecode that performs the same sequence (reads, final storage, final transient).

Slot and key shapes: the PoolManager slots of cycle 32 journal_seq.py (lock, nonzero delta count, reserves, deltas,
pool state at StateLibrary POOLS_SLOT 6) plus the cycle 30 Pool.State shapes. Frames are CALLs to the frame's own
account (A0 = PoolManager address, A1 and A2 other accounts) or DELEGATECALLs that act on the caller's account.

usage: python3 -I jrun.py <profile> <family> <n random> <seed> <out.json> [fault] [spec]
"""
import json, os, random, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/038/theme-frame-checkpoint-and-commit-lift.work/scripts')
import rethj, framepatch
framepatch.install(rethj, sys.argv[1])
from rethj import Machine, Stop, M, PROFILES
PROFILE_FDE = {k: v['fde'] for k, v in PROFILES.items()}
import pyevm as PE
from evm import assemble, keccak

PROF, FAM, NRAND, SEED, OUT = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
FAULT = sys.argv[6] if len(sys.argv) > 6 and sys.argv[6] != 'none' else None
SPEC = int(sys.argv[7]) if len(sys.argv) > 7 else 13
MODE = sys.argv[8] if len(sys.argv) > 8 else 'mixed'


def kw(*ws):
    return int.from_bytes(keccak(b''.join((w & M).to_bytes(32, 'big') for w in ws)), 'big')


A0 = 0x000000000004444c5dc75cb358380d2e3de08a90
A1 = 0x66a9893cc07d91d95644aedd05d03f95e1dba8af
A2 = 0xc0de0002
ADDRS = [A0, A1, A2]
CUR = [0, 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48, 0xb2000000000000000000002feb517dfec7415344]
LOCK = 0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23     # src/libraries/Lock.sol
NZDC = 0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b     # src/libraries/NonzeroDeltaCount.sol
RCUR = 0x1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95     # src/libraries/CurrencyReserves.sol
RVAL = 0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9
DELTAS = [kw(t, c) for t in (A0, A1, 0x1234) for c in CUR]                     # src/libraries/CurrencyDelta.sol
TKEYS = [LOCK, NZDC, RCUR, RVAL] + DELTAS
POOLID = kw(0xC0FFEE01, 0xC0FFEE02, 3000, 60, 0)
ST = kw(POOLID, 6)
SKEYS = [ST, ST + 1, ST + 2, ST + 3, kw((-887220) & M, ST + 4), kw(5, ST + 6), kw(A1, 7), 6, 0]
SQ = 79228162514264337593543950336
VALS = [0, 1, 2, M, M - 4, 10 ** 18, SQ | ((-1 & 0xffffff) << 160) | (3000 << 208), 1 << 255]


# ---------------------------------------------------------------- reference 1: revm 43 journal rules in Python
class RefJournal:
    """Transcription of revm-context 43.0.3 journal/inner.rs (checkpoint, checkpoint_commit, checkpoint_revert,
    tstore) and revm-context-interface 43.0.2 journaled_state/account.rs (sload_concrete_error,
    sstore_concrete_error) and entry.rs (revert), for an empty access list and accounts already warm."""
    def __init__(s, backing):
        s.backing = backing; s.slots = {}; s.tr = {}; s.j = []; s.depth = 0; s.touched = set()

    def _load(s, a, k):
        if (a, k) not in s.slots:
            v = s.backing.get((a, k), 0); s.slots[(a, k)] = [v, v, False]; s.j.append(('warm', a, k))
        else:
            sl = s.slots[(a, k)]
            if sl[2]: sl[2] = False; s.j.append(('warm', a, k))
        return s.slots[(a, k)]

    def sload(s, a, k): return s._load(a, k)[1]

    def sstore(s, a, k, v):
        if a not in s.touched: s.touched.add(a); s.j.append(('touch', a))
        sl = s._load(a, k); r = (sl[0], sl[1], v)
        if sl[1] != v: s.j.append(('chg', a, k, sl[1])); sl[1] = v
        return r

    def tload(s, a, k): return s.tr.get((a, k), 0)

    def tstore(s, a, k, v):
        prev = s.tr.get((a, k))
        if v == 0:
            if prev is not None: del s.tr[(a, k)]; s.j.append(('tchg', a, k, prev))
        else:
            s.tr[(a, k)] = v
            p = prev or 0
            if p != v: s.j.append(('tchg', a, k, p))

    def checkpoint(s): s.depth += 1; return len(s.j)
    def commit(s): s.depth = max(0, s.depth - 1)

    def revert(s, cp):
        s.depth = max(0, s.depth - 1)
        while len(s.j) > cp:
            e = s.j.pop()
            if e[0] == 'warm': s.slots[(e[1], e[2])][2] = True
            elif e[0] == 'touch': s.touched.discard(e[1])
            elif e[0] == 'chg': s.slots[(e[1], e[2])][1] = e[3]
            elif e[0] == 'tchg':
                if e[3] == 0: s.tr.pop((e[1], e[2]), None)
                else: s.tr[(e[1], e[2])] = e[3]


# ---------------------------------------------------------------- reference 2: pyevm.py on bytecode
def nreads(ops):
    return sum(1 if op[0] in ('sl', 'tl', 'ss') else nreads(op[3]) if op[0] == 'frame' else 0 for op in ops)


def ref_pyevm(seq, backing):
    """Each frame is a contract. ('frame', kind, revert, ops, target): kind 'call' runs on the target account's
    storage, 'dcall' on the caller's. Reads and SSTORE do not return the original value in bytecode, so 'ss' records
    nothing here (a zero placeholder keeps positions aligned). The frame returns or reverts with its record."""
    contracts = {}; counter = [0]

    def gen(ops, revert):
        p = []; i = 0
        for op in ops:
            k = op[0]
            if k == 'ss': p += [('PUSHN', 32, op[2]), ('PUSHN', 32, op[1]), 'SSTORE', ('PUSH', 0), ('PUSH', 32 * i), 'MSTORE']; i += 1
            elif k == 'ts': p += [('PUSHN', 32, op[2]), ('PUSHN', 32, op[1]), 'TSTORE']
            elif k in ('sl', 'tl'):
                p += [('PUSHN', 32, op[1]), 'SLOAD' if k == 'sl' else 'TLOAD', ('PUSH', 32 * i), 'MSTORE']; i += 1
            elif k == 'frame':
                counter[0] += 1; caddr = 0x7000 + counter[0]
                contracts[caddr] = gen(op[3], op[2])
                if op[1] == 'call':
                    # CALL into the code; the code runs on the target's storage: emulate with a tiny proxy account
                    pa = op[4]
                    p += [('PUSH', 0), ('PUSH', 0), ('PUSH', 0), ('PUSH', 0), ('PUSH', 0), ('PUSHN', 20, pa * 0 + caddr + 0x100000), 'GAS', 'CALL', 'POP']
                    proxies[caddr + 0x100000] = (caddr, pa)
                else:
                    p += [('PUSH', 0), ('PUSH', 0), ('PUSH', 0), ('PUSH', 0), ('PUSHN', 20, caddr), 'GAS', 'DELEGATECALL', 'POP']
                p += ['RETURNDATASIZE', ('PUSH', 0), ('PUSH', 32 * i), 'RETURNDATACOPY']
                i += nreads(op[3])
        p += [('PUSH', 32 * i), ('PUSH', 0), 'REVERT' if revert else 'RETURN']
        return assemble(p)
    proxies = {}
    top = gen(seq, False)
    codes = {A0: top}; codes.update(contracts)
    w = PE.World(codes)
    # a CALL to a proxy address runs the frame code against the target account's storage
    orig_call = w.call
    def call(caller, to, value, data, static, depth, code_addr=None, storage_addr=None, apparent=None):
        if to in proxies and code_addr is None:
            c, a = proxies[to]
            return orig_call(caller, a, value, data, static, depth, code_addr=c, storage_addr=a)
        return orig_call(caller, to, value, data, static, depth, code_addr, storage_addr, apparent)
    w.call = call
    for (a, k), v in backing.items(): w.storage[(a, k)] = v
    ok, ret = w.call(0xcafe, A0, 0, b'', False, 0)
    assert ok
    reads = [int.from_bytes(ret[j:j + 32], 'big') for j in range(0, len(ret), 32)]
    return reads, {k: v for k, v in w.storage.items() if v}, {k: v for k, v in w.transient.items() if v}


# ---------------------------------------------------------------- the lifted model and the per-boundary checks
from framepatch import FrameMismatch as Mismatch


def run_case(seq, backing, seed, stats):
    mc = Machine(PROF, FAM, seed, faults=FAULTS, spec=SPEC); mc.backing = dict(backing); stats['last'] = mc
    if MODE == 'discard': mc.wr(mc.INNER + 0x120, 4, 0xffffffff)   # TransactionId(NonMaxU32) stores id ^ u32::MAX: id 0
    for a in ADDRS: mc.put_account(a)
    ref = RefJournal(backing if FAM != 'B' else {}); reads = []; ssr = []
    seen = set(); tkeys = set()

    def check(where):
        stats['checks'] += 1
        if mc.jlen() != len(ref.j): raise Mismatch('%s: journal length %d, reference %d' % (where, mc.jlen(), len(ref.j)))
        if mc.depth() != ref.depth: raise Mismatch('%s: depth %d, reference %d' % (where, mc.depth(), ref.depth))
        for (a, k) in sorted(seen):
            rec = mc.slot_record(a, k); r = ref.slots[(a, k)]
            if rec is None: raise Mismatch('%s: slot %x/%x missing from table' % (where, a, k))
            if rec != (r[0], r[1]): raise Mismatch('%s: slot %x/%x original,present %s reference %s' % (where, a, k, [hex(x) for x in rec], [hex(x) for x in r[:2]]))
        for (a, k) in sorted(tkeys):
            v = mc.tload(a, k)
            if v != ref.tload(a, k): raise Mismatch('%s: transient %x/%x = %x reference %x' % (where, a, k, v, ref.tload(a, k)))

    def run(ops, addr):
        for op in ops:
            k = op[0]
            if k == 'ss':
                got = mc.sstore(addr, op[1], op[2]); exp = ref.sstore(addr, op[1], op[2]); seen.add((addr, op[1]))
                if mc.F['sstore_hooks'] and (got is None or got[:3] != exp): raise Mismatch('sstore result %s reference %s' % (got, exp))
                got = got or (0,)
                reads.append(0); ssr.append(got[0])
            elif k == 'sl':
                v = mc.sload(addr, op[1]); e = ref.sload(addr, op[1]); seen.add((addr, op[1]))
                if v != e: raise Mismatch('sload %x/%x = %x reference %x' % (addr, op[1], v, e))
                reads.append(v)
            elif k == 'ts':
                mc.tstore(addr, op[1], op[2]); ref.tstore(addr, op[1], op[2]); tkeys.add((addr, op[1]))
            elif k == 'tl':
                v = mc.tload(addr, op[1]); e = ref.tload(addr, op[1]); tkeys.add((addr, op[1]))
                if v != e: raise Mismatch('tload %x/%x = %x reference %x' % (addr, op[1], v, e))
                reads.append(v)
            elif k == 'frame':
                cp = mc.checkpoint(); rcp = ref.checkpoint()
                if cp[1] != rcp: raise Mismatch('checkpoint journal index %d reference %d' % (cp[1], rcp))
                run(op[3], op[4] if op[1] == 'call' else addr)
                if op[2]:
                    mc.revert(cp); ref.revert(rcp); stats['reverts'] += 1; check('after revert')
                else:
                    mc.commit(); ref.commit(); stats['commits'] += 1; check('after commit')
    run(seq, A0)
    check('end')
    stor = {}
    for (a, k) in seen:
        stor[(a, k)] = mc.slot_record(a, k)[1]
    for kk, v in backing.items(): stor.setdefault(kk, v if FAM != 'B' else 0)
    tr = {kk: mc.tload(*kk) for kk in tkeys}
    if MODE == 'discard':
        # revm-context 43.0.3 journal/inner.rs discard_tx: drain and revert every entry, clear transient storage,
        # depth 0, transaction id + 1 (lifted routine: the family's 'discard' address)
        tid = mc.rd(mc.INNER + 0x120, 4)
        mc.run(mc.F['discard'], [mc.INNER])
        stats['discards'] = stats.get('discards', 0) + 1
        if mc.jlen() != 0: raise Mismatch('discard: journal length %d' % mc.jlen())
        if mc.depth() != 0: raise Mismatch('discard: depth %d' % mc.depth())
        if mc.rd(mc.INNER + 0x120, 4) != tid - 1:   # stored form id ^ u32::MAX, so id + 1 is stored - 1
            raise Mismatch('discard: transaction id %d after %d' % (mc.rd(mc.INNER + 0x120, 4), tid))
        for (a, k) in sorted(seen):
            rec = mc.slot_record(a, k); o = ref.slots[(a, k)][0]
            if rec != (o, o): raise Mismatch('discard: slot %x/%x original,present %s, loaded value %x' % (a, k, [hex(x) for x in rec], o))
        for (a, k) in sorted(tkeys):
            if mc.tload(a, k) != 0: raise Mismatch('discard: transient %x/%x = %x' % (a, k, mc.tload(a, k)))
    for _k, _v in getattr(mc, 'fstats', {}).items(): stats[_k] = stats.get(_k, 0) + _v
    stats['steps'] += mc.cpu.steps; stats['fault_hits'] += mc.cpu.fault_hits
    stats['visited'] |= mc.cpu.visited
    return reads, {k: v for k, v in stor.items() if v}, {k: v for k, v in tr.items() if v}, mc


def named():
    s = {}
    s['write_back_to_original'] = ([('sl', ST + 3), ('ss', ST + 3, 5), ('ss', ST + 3, 77), ('sl', ST + 3),
                                    ('frame', 'dcall', True, [('ss', ST + 3, 6), ('ss', ST + 3, 77)], A0), ('sl', ST + 3)], {(A0, ST + 3): 77})
    s['twice_in_one_frame'] = ([('frame', 'dcall', False, [('ss', ST, 1), ('ss', ST, 2), ('sl', ST)], A0), ('sl', ST),
                                ('frame', 'dcall', True, [('ss', ST, 3), ('ss', ST, 4)], A0), ('sl', ST)], {(A0, ST): 9})
    s['first_read_after_inner_revert'] = ([('frame', 'dcall', True, [('ss', ST + 1, 123), ('ss', ST + 2, 0)], A0),
                                           ('sl', ST + 1), ('sl', ST + 2), ('ss', ST + 1, 124), ('sl', ST + 1)],
                                          {(A0, ST + 1): 50, (A0, ST + 2): 60})
    s['commit_inside_revert'] = ([('ss', ST, 1), ('ts', DELTAS[1], 5),
                                  ('frame', 'dcall', True, [('frame', 'dcall', False, [('ss', ST, 2), ('ss', ST + 3, 8), ('ts', DELTAS[1], 6), ('ts', NZDC, 1)], A0),
                                                             ('sl', ST), ('tl', DELTAS[1])], A0),
                                  ('sl', ST), ('sl', ST + 3), ('tl', DELTAS[1]), ('tl', NZDC)], {(A0, ST + 3): 3})
    lock = [('ts', LOCK, 1)]
    for d in (1, 2, 3):
        inner = [('ts', NZDC, d), ('ts', DELTAS[1], (-d) & M), ('ts', LOCK, 0), ('tl', LOCK)]
        for _ in range(d - 1):
            inner = [('ts', DELTAS[2], d), ('frame', 'dcall', True, inner, A0), ('tl', NZDC), ('tl', DELTAS[1])]
        s['transient_revert_depth_%d' % d] = (lock + [('ts', NZDC, 1), ('frame', 'dcall', True, inner, A0),
                                                      ('tl', LOCK), ('tl', NZDC), ('tl', DELTAS[1]), ('tl', DELTAS[2])], {})
    many = [('ss', kw(i, 99), i + 1) for i in range(40)] + [('ts', kw(i, 98), i + 1) for i in range(40)]
    s['table_grows_in_reverted_frame'] = ([('ss', ST, 1), ('ts', LOCK, 1), ('frame', 'dcall', True, many + [('sl', kw(7, 99)), ('tl', kw(7, 98))], A0),
                                           ('sl', ST), ('sl', kw(7, 99)), ('tl', kw(7, 98)), ('tl', LOCK)] +
                                          [('sl', kw(i, 99)) for i in range(0, 40, 9)], {(A0, kw(3, 99)): 1234})
    s['table_grows_in_committed_frame'] = ([('frame', 'dcall', False, many, A0)] + [('sl', kw(i, 99)) for i in range(0, 40, 7)] +
                                           [('tl', kw(i, 98)) for i in range(0, 40, 7)], {})
    dense = [('ss', kw(i, 97), i + 1) for i in range(110)]
    s['dense_tables'] = ([('frame', 'dcall', False, dense, A0), ('frame', 'dcall', True, [('ss', kw(i, 97), 0) for i in range(0, 110, 3)], A0)] +
                         [('sl', kw(i, 97)) for i in range(109, -1, -1)] + [('ts', kw(i, 96), i + 1) for i in range(110)] +
                         [('frame', 'dcall', True, [('ts', kw(i, 96), 0) for i in range(0, 110, 2)], A0)] + [('tl', kw(i, 96)) for i in range(110)], {})
    s['three_accounts'] = ([('ss', ST, 1), ('frame', 'call', True, [('ss', ST, 2), ('ts', LOCK, 1), ('frame', 'call', False, [('ss', ST, 3), ('ts', LOCK, 2)], A2)], A1),
                            ('sl', ST), ('frame', 'call', False, [('sl', ST), ('tl', LOCK)], A1), ('frame', 'call', False, [('sl', ST), ('tl', LOCK)], A2)],
                           {(A1, ST): 40, (A2, ST): 41})
    # cycle 38: PoolManager reentry shapes (src/PoolManager.sol unlock 104-114, modifyLiquidity, swap, donate,
    # take 291-297, sync 279-288, settle 349-364). A0 = PoolManager, A1 = locker / hook, A2 = token or recipient.
    def unlock(inner):
        return [('ts', LOCK, 1), ('frame', 'call', False, inner, A1), ('tl', NZDC), ('ts', LOCK, 0), ('tl', LOCK)]
    pm_modify_swap = [('frame', 'call', False, [('sl', ST), ('ss', ST, 5), ('ss', ST + 3, 9), ('ts', DELTAS[1], 7), ('ts', NZDC, 1),
                                                 ('sl', ST + 3), ('ss', ST, 6), ('ts', DELTAS[1], 0), ('ts', DELTAS[2], 3)], A0)]
    for depth in (1, 2, 3, 4):
        # a hook frame at the given depth reenters swap and donate, then reverts; the outer frames commit
        hook = [('frame', 'call', False, [('ss', ST, 11), ('ts', DELTAS[2], 5), ('ts', NZDC, 2)], A0),
                ('frame', 'call', False, [('ss', ST + 2, 12), ('ts', DELTAS[2], 6)], A0)]
        inner = [('frame', 'call', True, hook, A1)]
        for _ in range(depth - 1):
            inner = [('ss', ST + 1, depth), ('ts', DELTAS[1], depth), ('frame', 'call', False, inner, A0)]
        s['pm_hook_reenters_swap_donate_revert_depth_%d' % depth] = (unlock(pm_modify_swap + inner) + [('sl', ST), ('sl', ST + 1), ('sl', ST + 2)] +
                                                                      [('tl', DELTAS[1]), ('tl', DELTAS[2]), ('tl', NZDC)], {(A0, ST): 3, (A0, ST + 2): 4})
    # take of a token whose transfer reverts: deltas were already written, the token frame reverts, the take frame reverts
    s['pm_take_token_transfer_reverts'] = (unlock([('frame', 'call', True, [('ts', DELTAS[1], M - 99), ('ts', NZDC, 1),
                                                                             ('frame', 'call', True, [('ss', kw(A0, 0), 1), ('ss', kw(A1, 0), 99)], A2)], A0)]) +
                                           [('tl', DELTAS[1]), ('tl', NZDC), ('frame', 'call', False, [('sl', kw(A0, 0)), ('sl', kw(A1, 0))], A2)],
                                           {(A2, kw(A0, 0)): 1000})
    # native payout to a recipient that reverts (value call with empty calldata), inside take at depth 2
    s['pm_native_payout_recipient_reverts'] = (unlock([('frame', 'call', False, [('ts', DELTAS[0], M - 5), ('ts', NZDC, 1),
                                                                                  ('frame', 'call', True, [('ss', 0, 1), ('ts', 0, 1)], A2), ('tl', DELTAS[0])], A0)]) +
                                               [('tl', DELTAS[0]), ('tl', NZDC)], {})
    # sync: a static balanceOf frame that only reads, then the reserves and the synced currency are written
    s['pm_sync_static_balanceof'] = ([('frame', 'call', False, [('sl', kw(A0, 0))], A2), ('ts', RCUR, CUR[1]), ('ts', RVAL, 1000),
                                      ('frame', 'call', True, [('frame', 'call', False, [('sl', kw(A0, 0))], A2), ('ts', RCUR, 0), ('ts', RVAL, 0)], A0),
                                      ('tl', RCUR), ('tl', RVAL)], {(A2, kw(A0, 0)): 1000})
    return s


def rand_seq(rnd):
    def ops(depth, addr):
        r = []
        for _ in range(rnd.randint(1, 7)):
            c = rnd.random()
            if c < 0.24: r.append(('ss', rnd.choice(SKEYS), rnd.choice(VALS)))
            elif c < 0.48: r.append(('ts', rnd.choice(TKEYS), rnd.choice(VALS)))
            elif c < 0.6: r.append(('sl', rnd.choice(SKEYS)))
            elif c < 0.72: r.append(('tl', rnd.choice(TKEYS)))
            elif depth < 4:
                if rnd.random() < 0.3:
                    t = rnd.choice(ADDRS); r.append(('frame', 'call', rnd.random() < 0.55, ops(depth + 1, t), t))
                else:
                    r.append(('frame', 'dcall', rnd.random() < 0.55, ops(depth + 1, addr), addr))
        return r
    backing = {(a, k): rnd.choice(VALS[1:]) for a in ADDRS for k in SKEYS if rnd.random() < 0.3}
    seq = ops(0, A0) + [('sl', k) for k in SKEYS[:5]] + [('tl', k) for k in TKEYS[:6]]
    return seq, backing


def churn_seq(rnd):
    """Transient-only: one to three accounts, a pool of 20 to 400 keys, long runs of inserts then deletes (value 0)
    and re-inserts, so tables cross the growth thresholds 3, 7, 14, 28, 56, 112, 224 and 448 and fill with
    tombstones that force a rehash in place; nested frames revert or commit at random."""
    pool = {a: [kw(a, i, rnd.getrandbits(32)) for i in range(rnd.choice((20, 60, 120, 250, 400)))] for a in ADDRS}
    def ops(depth, addr, n):
        r = []
        keys = pool[addr]
        for _ in range(n):
            c = rnd.random()
            if c < 0.5: r.append(('ts', rnd.choice(keys), rnd.choice(VALS[1:])))
            elif c < 0.8: r.append(('ts', rnd.choice(keys), 0))
            elif c < 0.95: r.append(('tl', rnd.choice(keys)))
            elif depth < 3:
                t = rnd.choice(ADDRS) if rnd.random() < 0.3 else addr
                r.append(('frame', 'call' if t != addr else 'dcall', rnd.random() < 0.5, ops(depth + 1, t, rnd.randint(5, 80)), t))
        return r
    seq = []
    for a in ADDRS[:rnd.randint(1, 3)]:
        ks = pool[a]
        fill = [('ts', k, i + 1) for i, k in enumerate(ks)]
        seq.append(('frame', 'call', False, fill, a) if a != A0 else ('frame', 'dcall', False, fill, A0))
    seq += ops(0, A0, rnd.randint(100, 500))
    seq += [('tl', k) for k in pool[A0][::3]]
    return seq, {}


def inplace_cases():
    """Transient tables filled to exactly their capacity (224 keys: 256 buckets, 448 keys: 512 buckets), so that growth
    is used up, then most keys deleted (tombstones in full groups) and new keys inserted until growth runs out again with
    fewer than half the capacity in use, which sends hashbrown reserve to rehash in place; once at top level and once
    inside a frame that reverts or commits."""
    out = {}
    for n, dele in ((224, 150), (448, 300)):
        ks = [kw(0xAB, n, i) for i in range(n)]; new = [kw(0xCD, n, i) for i in range(dele)]
        fill = [('ts', k, i + 1) for i, k in enumerate(ks)]
        churn = [('ts', k, 0) for k in ks[:dele]] + [('ts', k, 7) for k in new]
        reads = [('tl', k) for k in ks[::5]] + [('tl', k) for k in new[::5]]
        out['inplace_top_%d' % n] = (fill + churn + reads, {})
        out['inplace_reverted_%d' % n] = (fill + [('frame', 'dcall', True, churn + reads, A0)] + reads, {})
        out['inplace_committed_%d' % n] = (fill + [('frame', 'dcall', False, churn, A0)] + reads, {})
    return out


FAULTS = {}
if FAULT:
    FAULTS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'faults.json')))['%s-%s' % (PROF, FAM)][FAULT]
    FAULTS = {int(k, 16): v for k, v in FAULTS.items()}

if __name__ == '__main__':
    rnd = random.Random(SEED)
    gen = churn_seq if MODE == 'churn' else rand_seq
    cases = [(k, s, b) for k, (s, b) in named().items()] if NRAND >= 0 and MODE != 'churn' else []
    cases += [('%s%d' % (MODE, i),) + gen(rnd) for i in range(abs(NRAND))]
    if MODE == 'inplace': cases = [(k, s_, b) for k, (s_, b) in inplace_cases().items()]
    stats = {'fault_hits': 0, 'checks': 0, 'reverts': 0, 'commits': 0, 'steps': 0, 'visited': set()}
    res = {'profile': PROF, 'family': FAM, 'fault': FAULT, 'seed': SEED, 'spec': SPEC, 'cases': 0, 'mismatch': 0, 'errors': 0,
           'pyevm_mismatch': 0, 'records': [], 'started': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    for i, (name, seq, backing) in enumerate(cases):
        res['cases'] += 1
        try:
            mr, ms, mt, mc = run_case(seq, backing, SEED * 100003 + i, stats)
        except Mismatch as e:
            stats['fault_hits'] += stats['last'].cpu.fault_hits
            res['mismatch'] += 1; res['records'].append({'case': name, 'kind': 'journal', 'detail': str(e), 'seq': repr(seq), 'backing': repr(backing)})
            if FAULT: break
            continue
        except Stop as e:
            stats['fault_hits'] += stats['last'].cpu.fault_hits
            res['errors'] += 1; res['records'].append({'case': name, 'kind': 'stop', 'detail': str(e), 'seq': repr(seq), 'backing': repr(backing)})
            if FAULT: break
            continue
        if FAM != 'B':
            rr, rs, rt = ref_pyevm(seq, backing)
            if (rr, rs, rt) != (mr, ms, mt):
                res['pyevm_mismatch'] += 1
                res['records'].append({'case': name, 'kind': 'pyevm', 'seq': repr(seq), 'backing': repr(backing),
                                       'ref': repr((rr, rs, rt)), 'model': repr((mr, ms, mt))})
                if FAULT: break
    res.update({k: v for k, v in stats.items() if k not in ('visited', 'last')}); res['instructions_visited'] = len(stats['visited'])
    import bisect
    fl = sorted(tuple(int(x, 16) for x in __import__('re').split(r'\.\.+', l.strip())) for l in open(PROFILE_FDE[PROF])); fs = [a for a, b in fl]
    fv = {}
    for pc in stats['visited']:
        lo = fl[bisect.bisect_right(fs, pc) - 1][0]; fv[lo] = fv.get(lo, 0) + 1
    res['functions_visited'] = {hex(k): v for k, v in sorted(fv.items())}
    res['finished'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    json.dump(res, open(OUT, 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != 'records'}))
    for r in res['records'][:3]: print(r)
