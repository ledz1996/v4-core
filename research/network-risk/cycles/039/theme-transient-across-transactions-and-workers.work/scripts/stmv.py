"""Cycle 39, Task 2 (L-1358): the bor v2.11.2 ParallelStateDB storage path run from the shipped amd64 binary
(cycles/031/theme-go-family-binary-lift.work/dl/bor, GitCommit a4afe5a9 = tag v2.11.2, read as data, never executed)
in the cycle 32/33 x86-64 model, with the multi-version store PRELOADED with answers from other transactions.

This reuses cycles/033/theme-persistent-storage-binary-lift.work/scripts/stgo2.py (SModelPar, SBinPar, run_par's checks)
and replaces its ReadVersionFull stub, which always answered not-found, by one that answers from a per-sequence table:
  done     the slot holds a committed write of transaction 3, incarnation 1 (found, not an estimate). The pre-state of
           this transaction is that value; the reference (pyevm) starts from it.
  estimate the slot holds an ESTIMATE marker of transaction 2 with a stale value. In incarnation 0 handleEstimate
           returns false (parallel_statedb.go:383-393), so the read must fall through to the base state.
  change   the slot holds a committed write whose value is replaced by another value after the first read of the slot
           (another transaction re-executed and flushed). Reads of a slot this transaction never wrote must return the
           store's current value each time (no SLOAD result cache in front of the store); GetCommittedState keeps its
           first answer (committedCache, parallel_statedb.go:1003-1034).
Every other key (SuicidePath, CreatePath and so on) answers not-found.
Checks per step, as in run_par: SLOAD equals the reference, GetCommittedState equals the value at transaction start,
localStorage (what FlushToMVStore writes, parallel_statedb.go:495-524) equals the set of SSTOREs not undone by a revert,
journal length restored after each revert. Seed 39_1358_01.
The value buffers handed back in the `any` result sit at BASE+0x46000; the type word is the address the binary compares
with in GetState's val.(common.Hash) assertion (LEAQ 0x3892aaf(IP) at 0xaba92a, so 0x434d3e0).
usage: python3 -I stmv.py <nseq> <out.json>"""
import sys, os, json, random, time
C33 = '/home/user/v4-core/research/network-risk/cycles/033/theme-persistent-storage-binary-lift.work/scripts'
C32 = '/home/user/v4-core/research/network-risk/cycles/032/theme-go-binaries-storage-journal.work/scripts'
sys.path[:0] = [C33, C32, '/home/user/v4-core/research/network-risk/tools/opdiff']
import stgo2 as S2
import tsgo as T
import stgo as SG
from tsgo import Stop, AStop
GE = S2.GE
HASH_TYPE = 0x434d3e0
VBUF = T.BASE + 0x46000
SEED = 39_1358_01
# planted faults, to show the checks catch them: FAULT=stale returns a done value with its low bit flipped while the
# reference keeps the true value; FAULT=estleak hands an estimate entry back as a committed one (a stale read leaking).
FAULT = os.environ.get('FAULT', 'none')


class SModelMV(S2.SModelPar):
    def externs(self, w):
        ext = S2.SModelPar.externs(self, w)
        model = self

        def rvf(cpu):
            self.stubbed.add('blockstm.(*MVStore).ReadVersionFull')
            w.mvreads = getattr(w, 'mvreads', 0) + 1
            sp = cpu.r['rsp']
            off = getattr(w, 'keyoff', None)
            if off is None:
                for o in (0, 8, 16):
                    k = model.rbytes(cpu, sp + o, 54)
                    if k[53] in (1, 2, 3):
                        off = w.keyoff = o; break
                if off is None: raise Stop('MVStore key not found on stack')
            k = model.rbytes(cpu, sp + off, 54)
            ent = None
            if k[53] == 2:
                a = int.from_bytes(k[:20], 'big'); s = int.from_bytes(k[20:52], 'big')
                ent = w.mv.get((a, s))
                w.mvkeys.append((a, s, ent[0] if ent else None))
            if ent is None:
                vals = (0, 0, (1 << 64) - 1, 0, 0, 0)
            else:
                kind, cur = ent[0], ent[1]
                if kind == 'change':
                    n = w.changeReads.get(k, 0); w.changeReads[k] = n + 1
                    cur = ent[1] if n == 0 else ent[2]
                    w.lastStore[(int.from_bytes(k[:20], 'big'), int.from_bytes(k[20:52], 'big'))] = cur
                slot = w.vbuf.setdefault(k, VBUF + 32 * len(w.vbuf))
                model.wbytes(cpu, slot, cur.to_bytes(32, 'big'))
                writer, inc, est = (2, 0, 1) if kind == 'estimate' else (3, 1, 0)
                if FAULT == 'estleak' and kind == 'estimate': est = 0
                if FAULT == 'stale' and kind == 'done': model.wbytes(cpu, slot, (cur ^ 1).to_bytes(32, 'big'))
                vals = (HASH_TYPE, slot, writer, inc, 1, est)
            for r, v in zip(('rax', 'rbx', 'rcx', 'rdi', 'rsi', 'r8'), vals):
                cpu.r[r] = v
        n = GE + 'core/blockstm.(*MVStore).ReadVersionFull'
        if n in self.fns: ext[self.fns[n][0]] = rvf
        return ext


def run(nseq, out):
    model = SModelMV('borpar-amd64')
    rnd = random.Random(SEED)
    res = {'target': 'borpar-amd64 with preloaded MVStore', 'seed': SEED, 'fault': FAULT, 'sequences': 0, 'steps': 0, 'reads': 0, 'stores': 0,
           'reverts': 0, 'committedChecks': 0, 'writeSetChecks': 0, 'mvReads': 0, 'mvStateReads': {'done': 0, 'estimate': 0, 'change': 0},
           'baseReads': 0, 'changeChecks': 0, 'mismatches': [], 'errors': [], 'started': time.time()}
    hx = lambda st: [hex(v) if isinstance(v, int) else v for v in st]
    for qi in range(nseq):
        base, mv = {}, {}
        for a in (SG.PM, SG.OTHER):
            for s in SG.SLOTS:
                if rnd.random() < 0.6: base[(a, s)] = rnd.choice(SG.VALUES[1:]) if rnd.random() < 0.6 else rnd.getrandbits(256)
                r = rnd.random()
                if r < 0.25: mv[(a, s)] = ('done', rnd.choice(SG.VALUES) if rnd.random() < 0.5 else rnd.getrandbits(256))
                elif r < 0.4: mv[(a, s)] = ('estimate', rnd.getrandbits(256))
                elif r < 0.5: mv[(a, s)] = ('change', rnd.getrandbits(256), rnd.choice(SG.VALUES))
        eff = dict(base)
        for k, e in mv.items():
            if e[0] in ('done', 'change'): eff[k] = e[1]
        changed = {k for k, e in mv.items() if e[0] == 'change'}
        seq = SG.gen(rnd, eff)
        res['sequences'] += 1
        ref = SG.Ref(eff)
        try:
            b = S2.SBinPar(model, base, {SG.PM, SG.OTHER})
            b.w.mv, b.w.mvkeys, b.w.vbuf, b.w.changeReads, b.w.lastStore = mv, [], {}, {}, {}
            ws, wstack, bad = {}, [], None
            written = set()
            for st in seq:
                res['steps'] += 1
                if st[0] == 'st':
                    ref.st(*st[1:]); b.sst(*st[1:]); res['stores'] += 1; ws[(st[1], st[2])] = st[3]; written.add((st[1], st[2]))
                elif st[0] == 'ld':
                    k = (st[1], st[2]); y = b.sld(*st[1:]); res['reads'] += 1
                    if k in changed and k not in ws:
                        # an unwritten slot whose store entry changed: the read must be the store's current answer
                        res['changeChecks'] += 1
                        mvv = mv[k]
                        want = b.w.lastStore.get(k, mvv[1])
                        if y != want: bad = {'at': hx(st), 'change': True, 'bin': hex(y), 'store': hex(want)}
                    elif k in changed:
                        x = ref.ld(*st[1:])
                        if x != y: bad = {'at': hx(st), 'ref': hex(x), 'bin': hex(y)}
                    else:
                        x = ref.ld(*st[1:])
                        if x != y: bad = {'at': hx(st), 'ref': hex(x), 'bin': hex(y)}
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
                            bad = {'at': hx(st), 'writeSet': hex(a), 'bin': {hex(k): hex(v) for k, v in d.items()}, 'ref': {hex(k): hex(v) for k, v in want.items()}}
                            break
                if not bad and st[0] in ('st', 'ld') and (st[1], st[2]) not in changed:
                    res['committedChecks'] += 1
                    x = b.committed(st[1], st[2])
                    if x != eff.get((st[1], st[2]), 0):
                        bad = {'at': hx(st), 'committed': hex(st[2]), 'bin': hex(x), 'ref': hex(eff.get((st[1], st[2]), 0))}
                if bad:
                    bad.update({'seq': qi, 'steps': [hx(s) for s in seq], 'mv': {hex(k[0]) + ':' + hex(k[1]): [e[0]] + [hex(v) for v in e[1:]] for k, e in mv.items()},
                                'base': {hex(k[0]) + ':' + hex(k[1]): hex(v) for k, v in base.items()}})
                    res['mismatches'].append(bad); break
            res['baseReads'] += len(b.w.base_reads); res['mvReads'] += getattr(b.w, 'mvreads', 0)
            for a, s, kind in b.w.mvkeys:
                if kind: res['mvStateReads'][kind] += 1
        except (Stop, AStop) as e:
            res['errors'].append({'seq': qi, 'error': str(e)})
            if len(res['errors']) > 30: break
    res['stubbed'] = sorted(model.stubbed)
    res['elapsed'] = time.time() - res['started']
    json.dump(res, open(out, 'w'), indent=1)
    print(FAULT, {k: res[k] for k in ('sequences', 'reads', 'stores', 'reverts', 'committedChecks', 'writeSetChecks', 'mvReads', 'mvStateReads', 'baseReads', 'changeChecks')},
          'mismatches', len(res['mismatches']), 'errors', len(res['errors']), (res['errors'][:1] or [''])[0])


if __name__ == '__main__':
    run(int(sys.argv[1]), sys.argv[2])
