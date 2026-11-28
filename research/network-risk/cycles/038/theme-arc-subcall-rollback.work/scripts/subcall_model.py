"""Task 2 and 5: model of Arc's subcall life cycle on the revm journal rules, against a reference in which the child is an
ordinary call frame. Sources transcribed:
  journal: revm-context 16.0.1 src/journal/inner.rs checkpoint/checkpoint_commit/checkpoint_revert (lines 577-613),
           tstore (1046-1073), log (1077); entry revert: revm-context-interface 17.0.1 journaled_state/entry.rs 309-430.
  frames:  revm-handler 18.1.0 src/frame.rs make_call_frame 143-245 (checkpoint, value transfer, CallTooDeep), process_next_action
           418-420 (commit on ok, revert otherwise).
  arc:     arc-node v0.8.6 crates/evm/src/evm.rs frame_init 667-705 (allowed callers), init_subcall 897-1109 (loads, checkpoint
           1052 + commit 1053, child depth+1, continuation keyed by depth 1081-1091, immediate child 1096-1106),
           take_subcall_continuation 1114-1117, complete_subcall 1127-1238, revert_subcall_checkpoint 1249-1258,
           frame_return_result 729-785.
The PoolManager is modelled by its journal footprint: unlock sets the lock word, the callback takes (delta debit, count, token
balance moves or native balance move with the EIP-7708 face log), settles, swaps (slot writes), mints ERC-6909 claims, syncs a
currency (two transient words), may call CallFrom again or an ordinary call that reverts, and unlock ends by checking the count
and clearing the lock. Outcomes per CallFrom: child ok / revert / halt, completion ok / out of gas, CallTooDeep at the limit.
usage: python3 -I subcall_model.py <out.json> <seed> <count> [fault ...]"""
import sys, json, random, copy
CALL_STACK_LIMIT = 1024
PM, TOK, ATT, LP, MC, FACE = 'PM', 'TOKEN', 'ATTACKER', 'LP', 'MC3F', 'FACE3600'
LOCK, COUNT, SYNC_C, SYNC_R = 'lock', 'count', 'syncedCurrency', 'syncedReserves'
class Journal:
    def __init__(s, faults):
        s.storage = {}; s.bal = {}; s.t = {}; s.logs = []; s.j = []; s.depth = 0; s.warm = set(); s.f = faults
    def checkpoint(s):
        s.depth += 1; return (len(s.logs), len(s.j))
    def commit(s): s.depth = max(0, s.depth - 1)
    def revert(s, cp):
        s.depth = max(0, s.depth - 1)
        log_i, j_i = cp
        if not ('logs_kept' in s.f and s._in_subcall_revert): del s.logs[log_i:]
        ents = s.j[j_i:]; del s.j[j_i:]
        for e in reversed(ents):
            k = e[0]
            if k == 'warm': s.warm.discard(e[1])
            elif k == 'sstore': s.storage[e[1]] = e[2]
            elif k == 'tstore':
                if 'transient_skipped' in s.f and s._in_subcall_revert: s.j_skipped = True; continue
                if e[2] == 0: s.t.pop(e[1], None)
                else: s.t[e[1]] = e[2]
            elif k == 'xfer':
                s.bal[e[1]] += e[3]; s.bal[e[2]] -= e[3]
    _in_subcall_revert = False
    def load(s, a):
        if a not in s.warm: s.warm.add(a); s.j.append(('warm', a))
    def sstore(s, a, k, v):
        old = s.storage.get((a, k), 0)
        if old != v: s.storage[(a, k)] = v; s.j.append(('sstore', (a, k), old))
    def sload(s, a, k): return s.storage.get((a, k), 0)
    def tstore(s, a, k, v):
        old = s.t.get((a, k), 0)
        if old != v:
            if v == 0: s.t.pop((a, k), None)
            else: s.t[(a, k)] = v
            s.j.append(('tstore', (a, k), old))
    def tload(s, a, k): return s.t.get((a, k), 0)
    def transfer(s, fr, to, amt):
        if s.bal.get(fr, 0) < amt: return False
        s.bal[fr] -= amt; s.bal[to] = s.bal.get(to, 0) + amt; s.j.append(('xfer', fr, to, amt))
        if amt: s.logs.append(('Transfer7708', fr, to, amt))
        return True
    def snapshot(s):
        return {'storage': sorted((str(k), v) for k, v in s.storage.items() if v), 'bal': sorted(s.bal.items()),
                't': sorted((str(k), v) for k, v in s.t.items() if v), 'logs': list(map(str, s.logs)), 'warm': sorted(s.warm), 'depth': s.depth}

class Halt(Exception): pass
class Revert(Exception): pass

class Machine:
    """mode 'arc' runs CallFrom through the hand-built protocol; mode 'ref' runs the child as an ordinary frame whose
    final status is the precompile's final status."""
    def __init__(s, mode, faults=()):
        s.mode = mode; s.f = set(faults); s.J = Journal(s.f); s.conts = {}; s.events = []
        J = s.J
        for a in (PM, TOK, ATT, LP, MC, FACE): J.bal[a] = 0
        J.bal[PM] = 1000; J.bal[ATT] = 50
        J.storage[(TOK, ('bal', PM))] = 1000; J.storage[(TOK, ('bal', ATT))] = 50
        J.j = []
    # -- ordinary frame (revm make_call_frame + process_next_action)
    def frame(s, depth, caller, target, value, body):
        J = s.J
        if depth > CALL_STACK_LIMIT: return 'halt'
        cp = J.checkpoint()
        if value and not J.transfer(caller, target, value):
            J.revert(cp); return 'halt'
        try:
            body(depth); J.commit(); st = 'ok'
        except Revert: J.revert(cp); st = 'revert'
        except Halt: J.revert(cp); st = 'halt'
        if s.mode == 'arc':                               # frame_return_result (evm.rs 756-769): any finished frame
            c = s.conts.pop(depth - 1, None)              # take_subcall_continuation(finished_depth)
            if c is not None:
                c['result'] = s.complete(st, c); c['takenBy'] = depth
        return st
    # -- CallFrom (arc init_subcall / complete_subcall)
    def callfrom(s, depth, child_spec):
        """depth is the precompile call's depth; returns the precompile's final status to its caller (MC3F)."""
        J = s.J
        J.load(child_spec['sender']); J.load(PM)          # loads before the checkpoint (evm.rs 988-1042)
        if s.mode == 'ref':
            # reference: an ordinary frame at depth+1 that commits only if child ok and completion ok
            s.reached = False
            st = s.frame(depth + 1, child_spec['sender'], PM, 0, lambda d: s.run_child(d, child_spec, force_fail=(child_spec['completion'] == 'oog')))
            return 'oog' if s.reached else 'ok'   # reached: the child would have returned ok and completion ran out of gas
        if 'checkpoint_late' in s.f:
            pass
        else:
            cp = J.checkpoint(); J.commit()               # evm.rs 1052-1053
        key = depth if 'sibling_key' not in s.f else depth + 2
        if depth + 1 > CALL_STACK_LIMIT:                  # Immediate child (CallTooDeep), complete now (1096-1106)
            return s.complete('halt', {'cp': cp if 'checkpoint_late' not in s.f else None, 'spec': child_spec})
        cont = {'cp': None if 'checkpoint_late' in s.f else cp, 'spec': child_spec, 'depth': depth}
        s.conts[key] = cont
        def body(d):
            if 'checkpoint_late' in s.f:
                # fault: the saved checkpoint is taken after the first balance move it should cover
                s.run_child(d, child_spec, first_hook=lambda: s.conts[key].__setitem__('cp', (lambda c: (J.commit(), c)[1])(J.checkpoint())))
            else:
                s.run_child(d, child_spec)
        st = s.frame(depth + 1, child_spec['sender'], PM, 0, body)
        if 'result' not in cont:
            # the continuation was not taken by this child (fault sibling_key): raw child result goes up
            s.conts.pop(key, None)
            s.events.append(('continuation_missed', depth))
            return 'ok'
        return cont['result']
    def complete(s, child_status, c):
        J = s.J
        succeeded = child_status == 'ok'
        oog = c['spec']['completion'] == 'oog' and succeeded
        if oog:
            if succeeded: s.revert_subcall(c['cp'])
            return 'oog'
        return 'ok'
    def revert_subcall(s, cp):
        J = s.J; d0 = J.depth
        if cp is None: cp = (len(J.logs), len(J.j))     # fault checkpoint_late with no balance move: covers nothing
        dummy = J.checkpoint()
        target = dummy if 'wrong_index' in s.f else cp
        J._in_subcall_revert = True
        J.revert(target)
        J._in_subcall_revert = False
        assert J.depth == d0
    # -- the child: PoolManager.unlock with the attacker's callback
    def run_child(s, d, spec, force_fail=False, first_hook=None):
        J = s.J
        if J.tload(PM, LOCK): raise Revert()              # AlreadyUnlocked
        J.tstore(PM, LOCK, 1)
        hooked = [False]
        def hook():
            if first_hook and not hooked[0]: hooked[0] = True; first_hook()
        for op in spec['ops']:
            s.pm_op(d + 1, op, hook)                      # callback frame at d+1 calls PM at d+2: depth only matters for nesting
        if spec['end'] == 'revert': raise Revert()
        if spec['end'] == 'halt': raise Halt()
        if J.tload(PM, COUNT) != 0: raise Revert()        # CurrencyNotSettled
        J.tstore(PM, LOCK, 0)
        if force_fail: s.reached = True; raise Revert()
    def delta(s, cur, who, amt):
        J = s.J; k = ('delta', cur, who)
        old = J.tload(PM, k); new = (old + amt) % (1 << 256)
        if old == 0 and new != 0: J.tstore(PM, COUNT, J.tload(PM, COUNT) + 1)
        if old != 0 and new == 0: J.tstore(PM, COUNT, J.tload(PM, COUNT) - 1)
        J.tstore(PM, k, new)
    def pm_op(s, d, op, hook):
        J = s.J; k = op[0]
        if k == 'take_erc20':
            amt = op[1]; s.delta('TOK', ATT, -amt)
            b = J.sload(TOK, ('bal', PM))
            if b < amt: raise Revert()
            J.sstore(TOK, ('bal', PM), b - amt); J.sstore(TOK, ('bal', ATT), J.sload(TOK, ('bal', ATT)) + amt)
            J.logs.append(('Transfer', PM, ATT, amt)); hook()
        elif k == 'take_native':
            amt = op[1]; s.delta('USDC', ATT, -amt)
            if not J.transfer(PM, ATT, amt): raise Revert()
            J.logs.append(('FaceTransfer', PM, ATT, amt)); hook()
        elif k == 'settle_erc20':
            amt = op[1]; b = J.sload(TOK, ('bal', ATT))
            if b < amt: raise Revert()
            J.sstore(TOK, ('bal', ATT), b - amt); J.sstore(TOK, ('bal', PM), J.sload(TOK, ('bal', PM)) + amt)
            s.delta('TOK', ATT, amt)
        elif k == 'settle_native':
            amt = op[1]
            if not J.transfer(ATT, PM, amt): raise Revert()
            s.delta('USDC', ATT, amt); hook()
        elif k == 'swap':
            J.sstore(PM, ('slot0', op[1]), op[2]); J.sstore(PM, ('liq', op[1]), op[3]); J.logs.append(('Swap', op[1]))
            s.delta('TOK', ATT, op[4]); s.delta('TOK', ATT, -op[4])
        elif k == 'mint6909':
            J.sstore(PM, ('6909', ATT, op[1]), J.sload(PM, ('6909', ATT, op[1])) + op[2]); s.delta(op[1], ATT, -op[2]); s.delta(op[1], ATT, op[2])
            J.logs.append(('Transfer6909', ATT, op[2]))
        elif k == 'sync':
            J.tstore(PM, SYNC_C, op[1]); J.tstore(PM, SYNC_R, op[2])
        elif k == 'revert_call':
            s.frame(d + 1, ATT, LP, 0, lambda dd: (J.sstore(LP, 'x', 7), J.tstore(LP, 'y', 9), (_ for _ in ()).throw(Revert())))
        elif k == 'nested_callfrom':
            # callback -> MC3F (d+1) -> CallFrom precompile (d+2) -> child at d+3
            inner = op[1]
            def mcbody(dd):
                st = s.callfrom(dd + 1, inner)
                if st == 'oog' and inner.get('mcRevertsOnFail'): raise Revert()
            s.frame(d + 1, ATT, MC, 0, mcbody)
        elif k == 'deep':
            # nest CallFrom until the depth limit; the innermost child is refused with CallTooDeep
            inner = op[1]
            def mcbody(dd):
                s.callfrom(dd + 1, inner)
            s.frame(d + 1, ATT, MC, 0, mcbody)

def gen_child(rng, level, deep_ok=True):
    ops = []
    for _ in range(rng.randint(0, 6)):
        r = rng.random()
        if r < 0.15: ops.append(('take_erc20', rng.choice([1, 5, 100])))
        elif r < 0.30: ops.append(('take_native', rng.choice([1, 5, 100])))
        elif r < 0.42: ops.append(('settle_erc20', rng.choice([1, 5, 100])))
        elif r < 0.54: ops.append(('settle_native', rng.choice([1, 5, 40])))
        elif r < 0.64: ops.append(('swap', rng.randint(0, 2), rng.randint(1, 9), rng.randint(1, 9), rng.randint(1, 9)))
        elif r < 0.72: ops.append(('mint6909', rng.choice(['TOK', 'USDC']), rng.randint(1, 9)))
        elif r < 0.80: ops.append(('sync', rng.choice(['TOK', 'USDC']), rng.randint(1, 999)))
        elif r < 0.86: ops.append(('revert_call',))
        elif r < 0.97 and level < 3: ops.append(('nested_callfrom', gen_child(rng, level + 1)))
    # balanced variant: settle what was taken so unlock can succeed
    if rng.random() < 0.6:
        t_e = sum(o[1] for o in ops if o[0] == 'take_erc20') - sum(o[1] for o in ops if o[0] == 'settle_erc20')
        t_n = sum(o[1] for o in ops if o[0] == 'take_native') - sum(o[1] for o in ops if o[0] == 'settle_native')
        if t_e > 0: ops.append(('settle_erc20', t_e))
        if t_e < 0: ops.append(('take_erc20', -t_e))
        if t_n > 0: ops.append(('settle_native', t_n))
        if t_n < 0: ops.append(('take_native', -t_n))
    return {'sender': ATT, 'ops': ops, 'end': rng.choice(['ok', 'ok', 'ok', 'revert', 'halt']),
            'completion': rng.choice(['ok', 'oog', 'oog']), 'mcRevertsOnFail': rng.random() < 0.3}

def run_top(mode, faults, spec, start_depth, parent_ops):
    m = Machine(mode, faults); J = m.J
    out = {}
    def mc_body(d):
        J.sstore(MC, 'pre', 1); J.tstore(MC, 'pre', 1)
        st = m.callfrom(d + 1, spec)
        out['precompile'] = st
        out['after_precompile'] = {'lock': J.tload(PM, LOCK), 'count': J.tload(PM, COUNT),
                                   'deltas': sorted((str(k), v) for (a, k), v in J.t.items() if a == PM and isinstance(k, tuple) and v)}
        if parent_ops == 'revert_after': raise Revert()
    st = m.frame(start_depth, ATT, MC, 0, mc_body)
    out['mc'] = st; out['state'] = J.snapshot(); out['events'] = m.events
    return out

def deep_spec(levels, end='halt', completion='ok'):
    spec = {'sender': ATT, 'ops': [('take_native', 5), ('settle_native', 5)], 'end': end, 'completion': completion}
    for _ in range(levels):
        spec = {'sender': ATT, 'ops': [('take_erc20', 5), ('deep', spec), ('settle_erc20', 5)], 'end': 'ok', 'completion': 'ok'}
    return spec

def check(a, r):
    bad = []
    if a['state'] != r['state']:
        for k in a['state']:
            if a['state'][k] != r['state'][k]: bad.append(k)
    if a.get('precompile') != r.get('precompile'): bad.append('precompile_status')
    if a['mc'] != r['mc']: bad.append('mc_status')
    ap = a.get('after_precompile') or {}
    if ap and (ap['lock'] or ap['count'] or ap['deltas']): bad.append('open_lock_or_delta_after_precompile')
    return bad

def main():
    out_path, seed, count = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); faults = sys.argv[4:]
    rng = random.Random(seed)
    res = {'seed': seed, 'count': count, 'faults': faults, 'mismatches': [], 'n': 0, 'byOutcome': {}}
    cases = []
    for i in range(count):
        cases.append((gen_child(rng, 0), rng.choice([1, 1, 5, 1015, 1019, 1020, 1021, 1022, 1023]), rng.choice(['none', 'none', 'revert_after'])))
    # depth-limit sequences: chains of CallFrom ending at the limit
    for lv in range(1, 8):
        for sd in (1000, 1005, 1010, 1012, 1014, 1016, 1018, 1020):
            for end in ('ok', 'halt', 'revert'):
                for comp in ('ok', 'oog'):
                    cases.append((deep_spec(lv, end, comp), sd, 'none'))
    for spec, sd, po in cases:
        a = run_top('arc', faults, spec, sd, po); r = run_top('ref', (), spec, sd, po)
        res['n'] += 1
        key = f"{spec['end']}/{spec['completion']}/{a.get('precompile')}"
        res['byOutcome'][key] = res['byOutcome'].get(key, 0) + 1
        bad = check(a, r)
        if bad:
            res['mismatches'].append({'spec': spec, 'startDepth': sd, 'parent': po, 'diff': bad, 'arc': a, 'ref': r})
    res['mismatchCount'] = len(res['mismatches'])
    full = res['mismatches']; res['mismatches'] = full[:50]; res['mismatchesStored'] = len(res['mismatches'])
    json.dump(res, open(out_path, 'w'), indent=1, default=str)
    print(json.dumps({'faults': faults, 'n': res['n'], 'mismatches': res['mismatchCount'], 'byOutcome': res['byOutcome'] if not faults else None}))
if __name__ == '__main__':
    main()
