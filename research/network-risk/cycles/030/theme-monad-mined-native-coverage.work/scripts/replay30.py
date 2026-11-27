"""Cycle 30 theme-monad-mined-native-coverage, Task 1: replay every PoolManager frame of a mined Monad transaction in
tools/opdiff/pyevm.py. The PoolManager's code runs in the reference interpreter with its storage and balance from the
transaction's prestate (prestateTracer, which on Monad is the state after the transactions before it in the block).
Every call the PoolManager makes is answered from the recorded call tree (callTracer): the call must match the recorded
child in target, input and value; the PoolManager frames inside that child's subtree run in the reference in order,
and the recorded success flag and return data are returned. A reverted subtree is rolled back. Program counters are
collected per transaction. Checks: success flag and return data of every PoolManager frame against the trace, the
PoolManager's logs against eth_getLogs (receipts, i.e. what consensus committed), and the storage written against the
diffMode post state. pyevm.py is used unchanged except for one textual patch, made at import, that keeps the topics
and data of LOG instructions (it otherwise only counts them)."""
import sys, os, json, gzip, types
OPD = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, OPD)
src = open(os.path.join(OPD, 'pyevm.py')).read()
OLD = "                    for _ in range(op - 0xa0): st.pop()\n                    self.logs += 1\n"
NEW = "                    _tp = [st.pop() for _ in range(op - 0xa0)]\n                    self.logs += 1; self.loglist.append((me, _tp, bytes(mem[off:off + size])))\n"
assert src.count(OLD) == 1
pyevm = types.ModuleType('pyevm30'); pyevm.__file__ = os.path.join(OPD, 'pyevm.py')
exec(compile(src.replace(OLD, NEW), 'pyevm.py(patched LOG)', 'exec'), pyevm.__dict__)
PM = int('0x188d586ddcf52439676ca21a244753fa19f9ea8e', 16)

class Mismatch(Exception): pass

def H(x): return int(x, 16) if x else 0
def B(x): return bytes.fromhex(x[2:]) if x and len(x) > 2 else b''

class RW(pyevm.World):
    def __init__(self, code, pre):
        super().__init__({PM: code}, {PM: H(pre.get('balance', '0x0'))})
        self.loglist = []
        for k, v in (pre.get('storage') or {}).items(): self.storage[(PM, int(k, 16))] = int(v, 16)
        self.stack = []; self.frames = []; self.mm = []
    def snapshot(self): return (dict(self.storage), dict(self.transient), dict(self.balances), self.logs)
    def restore(self, snap):
        super().restore(snap); del self.loglist[snap[3]:]
    # calls made by PoolManager code
    def call(self, caller, to, value, data, static, depth, code_addr=None, storage_addr=None, apparent=None):
        if caller != PM or code_addr is not None:
            raise Mismatch(f'unexpected call shape caller={caller:#x} code_addr={code_addr}')
        fr = self.stack[-1]; kids = fr['node'].get('calls', [])
        if fr['k'] >= len(kids): raise Mismatch(f'PoolManager made a call the trace does not have: to={to:#x} input={data[:4].hex()}')
        n = kids[fr['k']]; fr['k'] += 1
        if H(n['to']) != to or B(n.get('input')) != bytes(data) or H(n.get('value')) != value:
            raise Mismatch(f'call {fr["k"] - 1} differs: trace to={n["to"]} in={n.get("input","")[:10]} val={n.get("value")} / ref to={to:#x} in={bytes(data)[:4].hex()} val={value}')
        snap = self.snapshot()
        if value:
            if self.balances.get(PM, 0) < value: raise Mismatch('PoolManager balance below value sent')
            self.balances[PM] -= value; self.balances[to] = self.balances.get(to, 0) + value
        for c in n.get('calls', []): self.process(c, static or n['type'] == 'STATICCALL', depth + 1)
        ok = 'error' not in n
        if not ok: self.restore(snap)
        return ok, B(n.get('output'))
    def process(self, n, static, depth):
        t = n['type']
        if H(n.get('to')) == PM and t in ('CALL', 'STATICCALL'):
            return self.run_pm(n, static or t == 'STATICCALL', depth)
        if H(n.get('to')) == PM: raise Mismatch(f'{t} into the PoolManager')
        if t == 'SELFDESTRUCT': return
        snap = self.snapshot()
        for c in n.get('calls', []): self.process(c, static or t == 'STATICCALL', depth + 1)
        if 'error' in n: self.restore(snap)
    def run_pm(self, n, static, depth):
        caller = H(n['from']); value = H(n.get('value'))
        if value: self.balances[caller] = self.balances.get(caller, 0) + value  # the sender's balance is not tracked
        self.stack.append({'node': n, 'k': 0}); l0 = len(self.loglist)
        try:
            ok, ret = pyevm.World.call(self, caller, PM, value, B(n.get('input')), static, depth)
        finally:
            fr = self.stack.pop()
        want_ok = 'error' not in n; want = B(n.get('output'))
        rec = {'sel': n.get('input', '')[:10], 'ok': ok, 'traceOk': want_ok, 'retEq': ret == want, 'callsUsed': fr['k'], 'calls': len(n.get('calls', [])),
               'traceErr': n.get('error')}
        if ok != want_ok or ret != want or (ok and fr['k'] != len(n.get('calls', []))):
            rec.update(ret=ret.hex(), want=want.hex()); self.mm.append(rec)
        self.frames.append(rec)

def logs_of_pm(n, out, alive=True):
    """the PoolManager logs callTracer attaches to frames, in execution order (position = number of child calls before the log)"""
    alive = alive and 'error' not in n
    kids = n.get('calls', []); lg = sorted(n.get('logs', []), key=lambda x: int(x.get('position', '0x0'), 16) if isinstance(x.get('position'), str) else x.get('position', 0))
    j = 0
    for k in range(len(kids) + 1):
        while j < len(lg) and (int(lg[j].get('position', '0x0'), 16) if isinstance(lg[j].get('position'), str) else lg[j].get('position', 0)) == k:
            if H(lg[j]['address']) == PM and alive: out.append((lg[j]['topics'], lg[j]['data']))
            j += 1
        if k < len(kids): logs_of_pm(kids[k], out, alive)
    return out

def replay_tx(code, t, mined_logs=None):
    """t: one record of fetch30 (call, pre, diff). mined_logs: list of (topics, data) of the tx from eth_getLogs or None."""
    w = RW(code, t['pre'] or {})
    res = {'hash': t['hash'], 'i': t['i'], 'txError': t['call'].get('error')}
    try:
        w.process(t['call'], False, 0)
        res['status'] = 'ok' if not w.mm else 'frame-mismatch'
    except Mismatch as e:
        res['status'] = 'call-mismatch'; res['detail'] = str(e)
    except NotImplementedError as e:
        res['status'] = 'not-implemented'; res['detail'] = str(e)
    except pyevm.Halt as e:
        res['status'] = 'halt'; res['detail'] = str(e)
    res['frames'] = len(w.frames); res['sels'] = sorted({f['sel'] for f in w.frames})
    res['frameMismatch'] = w.mm[:5]
    res['failedFrames'] = sum(1 for f in w.frames if not f['traceOk'])
    got = [(['0x%064x' % x for x in tp], '0x' + d.hex()) for (a, tp, d) in w.loglist if a == PM]
    tr = logs_of_pm(t['call'], [])
    res['logsN'] = len(got); res['logsEqTrace'] = got == [(list(a), b) for a, b in tr]
    if mined_logs is not None: res['logsEqMined'] = got == mined_logs
    # storage written against the diffMode post state
    pre = {int(k, 16): int(v, 16) for k, v in ((t['pre'] or {}).get('storage') or {}).items()}
    post = {int(k, 16): int(v, 16) for k, v in (((t['diff'] or {}).get('post') or {}).get('storage') or {}).items()}
    dpre = {int(k, 16): int(v, 16) for k, v in (((t['diff'] or {}).get('pre') or {}).get('storage') or {}).items()}
    mine = {k: v for (a, k), v in w.storage.items() if a == PM}
    changed = {k: v for k, v in mine.items() if v != pre.get(k, 0)}
    want = {k: post.get(k, 0) for k in set(post) | set(dpre)}  # a slot in pre but not in post was set to zero
    res['slotsWritten'] = len(changed); res['storageEq'] = changed == want
    if not res['storageEq']:
        res['storageDiff'] = {hex(k): [hex(changed.get(k, -1)) if k in changed else None, hex(want[k]) if k in want else None]
                              for k in set(changed) | set(want) if changed.get(k) != want.get(k)}
    res['written'] = {hex(k): hex(v) for k, v in changed.items()}
    res['pcs'] = sorted(w.cover.get(PM, set()))
    return res
