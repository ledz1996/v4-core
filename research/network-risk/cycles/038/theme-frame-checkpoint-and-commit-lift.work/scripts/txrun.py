"""Task 3: run the inlined end-of-transaction code of a shipped binary on a populated journal (cycle 37 machine,
family F so that frames carry logs): random storage and transient writes in nested frames, some frames left open
(depth > 0, as after a halt), then the commit_tx block (or the discard_tx block, or JournalInner::finalize) from
the binary. Afterwards every transient word must read zero through the lifted TLOAD handler, the transient map must
hold no item, the depth must be 0, the journal, logs and third list empty and the transaction id advanced (commit,
discard) or reset (finalize). A second transaction then writes and reads transient storage again.
usage: python3 -I txrun.py <profile> <kind> <n> <seed> <out.json> [fault]
Nothing from the binary is executed or loaded; its objdump text is interpreted."""
import json, os, random, sys, time
W = '/home/user/v4-core/research/network-risk/cycles/038/theme-frame-checkpoint-and-commit-lift.work'
sys.path.insert(0, W + '/c37celo/scripts'); sys.path.insert(0, W + '/scripts')
import importlib
PROF, KIND, N, SEED, OUT = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
FAULT = sys.argv[6] if len(sys.argv) > 6 else None
MOD = importlib.import_module({'celo': 'celoj', 'xlayer': 'xlj', 'arc': 'arcj'}[PROF])
import framepatch
framepatch.install(MOD, PROF)
import celoj
Machine, Stop, HOST, SP0 = MOD.Machine, MOD.Stop, celoj.HOST, celoj.SP0

# the end-of-transaction blocks (start, stop, base register = HOST), found by txclear.py and read in objdump text
TX = {
    'celo': {
        # <CeloHandler as Handler>::execution_result 0x1e9cbd0: commit_tx inlined, r14 = context, J = r14+0x550
        'commit': dict(start=0x1e9e44c, stop=0x1e9e639, reg='r14', frame='rbp', txid=+1),
        # JournalInner::finalize 0x1d66c80 (out of line): rdi = out (EvmState), rsi = journal
        'finalize': dict(fn=0x1d66c80, txid='zero'),
        # <CeloHandler as Handler>::catch_error 0x1e94290: checkpoint_revert 0x1d61dd0 with a zero record
        # (0x1e943a0-0x1e943aa, every entry undone), then the inlined clear 0x1e94653-0x1e94840
        'discard': dict(pre_revert=True, start=0x1e94653, stop=0x1e94840, reg='r14', frame='rbp', txid=+1),
    },
}
# planted faults in the commit_tx block
FAULTS = {
    'celo': {
        'commit_tx_keeps_transient': {0x1e9e454: 'jmp    1e9e4b7'},
        'commit_tx_keeps_journal': {0x1e9e4c2: 'nop'},
        'commit_tx_keeps_depth': {0x1e9e4b7: 'nop'},
        'commit_tx_keeps_txid': {0x1e9e5cb: 'nop'},
        'commit_tx_keeps_logs': {0x1e9e5e0: 'nop'},
        'discard_tx_keeps_transient': {0x1e94653: 'jmp    1e946c0'},
    },
}
LOCK = 0xc090fc4683624cfc3884e9d8de5eca132f2d0ec062aff75d43c0465d5ceeab23
NZDC = 0x7d4b3164c6e45b97e7d87b7125a44c5828d005af88f9d751cfd78729c5d99a0b
RCUR = 0x1e0745a7db1623981f0b2a5d4232364c00787266eb75ad546f190e6cebe9bd95
RVAL = 0x27e098c505d44ec3574004bca052aabf76bd35004c182099d8c575fb238593b9
A0 = 0x000000000004444c5dc75cb358380d2e3de08a90; A1 = 0x66a9893cc07d91d95644aedd05d03f95e1dba8af; A2 = 0xc0de0002
TKEYS = [LOCK, NZDC, RCUR, RVAL] + [random.Random(i).getrandbits(256) for i in range(12)]
SKEYS = [0, 6, 7, random.Random(99).getrandbits(256)]


class Bad(Exception):
    pass


def one(seed, faults):
    r = random.Random(seed)
    mc = Machine(PROF, 'F', seed, faults=faults, spec=0x12)
    for a in (A0, A1, A2): mc.put_account(a)
    J = mc.J; written = set()
    open_frames = []
    for _ in range(r.randint(1, 40)):
        c = r.random(); a = r.choice((A0, A1, A2))
        if c < 0.4:
            k = r.choice(TKEYS); mc.tstore(a, k, r.choice((1, 2, (1 << 256) - 1, r.getrandbits(256)))); written.add((a, k))
        elif c < 0.6:
            mc.sstore(a, r.choice(SKEYS), r.getrandbits(64))
        elif c < 0.8 and len(open_frames) < 6:
            open_frames.append(mc.checkpoint())
        elif open_frames:
            cp = open_frames.pop()
            if r.random() < 0.5: mc.revert(cp)
            else: mc.commit()
    if not written:
        mc.tstore(A0, LOCK, 1); written.add((A0, LOCK))
    tw = mc.transient_words()
    tid0 = mc.rd(J + 0x120, 8); depth0 = mc.depth()
    t = TX[PROF][KIND]
    if 'fn' in t:
        mc.run(t['fn'], [celoj.ARGS + 0x800, J])
    else:
        if t.get('pre_revert'):
            rec = SP0 - 0x50000
            for i in range(3): mc.wr(rec + 8 * i, 8, 0)
            mc.run(0x1d61dd0, [J, rec])
        regs = {t['reg']: HOST}
        if t['frame'] == 'rbp': regs['rbp'] = SP0 - 0x40000
        mc.run(t['start'], [], stop=t['stop'], regs=regs)
    st = dict(depth_before=depth0, transient_before=len(tw), logs_before=None)
    if mc.depth() != 0: raise Bad('depth %d after %s' % (mc.depth(), KIND))
    if mc.jlen() != 0: raise Bad('journal length %d after %s' % (mc.jlen(), KIND))
    if mc.rd(J + 0x10, 8) != 0: raise Bad('logs %d after %s' % (mc.rd(J + 0x10, 8), KIND))
    if mc.rd(J + 0x40, 8) != 0: raise Bad('third list %d after %s' % (mc.rd(J + 0x40, 8), KIND))
    if mc.rd(J + 0xf0 + 0x18, 8) != 0: raise Bad('transient map items %d after %s' % (mc.rd(J + 0x108, 8), KIND))
    tid = mc.rd(J + 0x120, 8)
    if t['txid'] == 'zero':
        if tid != 0: raise Bad('transaction id %d after finalize' % tid)
    elif tid != tid0 + 1: raise Bad('transaction id %d after %d' % (tid, tid0))
    if KIND == 'finalize': return st, mc
    # next transaction: every word written before reads zero through the lifted TLOAD; new writes work
    for (a, k) in sorted(written):
        v = mc.tload(a, k)
        if v != 0: raise Bad('next transaction reads transient %x/%x = %x' % (a, k, v))
    mc.tstore(A0, LOCK, 1)
    if mc.tload(A0, LOCK) != 1: raise Bad('next transaction cannot write transient')
    return st, mc


if __name__ == '__main__':
    faults = {}
    if FAULT: faults = FAULTS[PROF][FAULT]
    res = dict(profile=PROF, kind=KIND, seed=SEED, fault=FAULT, cases=0, bad=0, errors=0, records=[],
               started=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), transient_words_cleared=0, open_depth_max=0)
    for i in range(N):
        res['cases'] += 1
        try:
            st, mc = one(SEED * 1000003 + i, faults)
            res['transient_words_cleared'] += st['transient_before']; res['open_depth_max'] = max(res['open_depth_max'], st['depth_before'])
        except Bad as e:
            res['bad'] += 1; res['records'].append(dict(case=i, seed=SEED * 1000003 + i, detail=str(e)))
            if FAULT: break
        except Stop as e:
            res['errors'] += 1; res['records'].append(dict(case=i, seed=SEED * 1000003 + i, stop=str(e)))
            if FAULT: break
    res['finished'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    json.dump(res, open(OUT, 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != 'records'}), res['records'][:2])
