"""Run the six pmdiff script sets in the reference EVM (tools/opdiff/pyevm.py, unmodified file) with a call-tree
recorder added at run time, and write each script as one transaction in the line format of src/replay.cpp:
the PoolManager's storage and balance before the script (PRE, BAL), every call frame (N), the PoolManager's logs (LOG)
and its storage after the script (POST). replay.cpp then runs every PoolManager frame through Monad's interpreter and
through native code and answers every other call from this tree.
Usage: PM_BUILD=research/network-risk/build/PoolManager.json python3 sets2tx.py <out dir> [sets, default 123456]"""
import sys, os, random, inspect, json
OP = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, OP)
import pyevm
src = inspect.getsource(pyevm)
# record log contents (address, topics, data); restore() truncates the list with the counter
old = "                    for _ in range(op - 0xa0): st.pop()\n                    self.logs += 1\n"
assert src.count(old) == 1
src = src.replace(old, "                    tps = [st.pop() for _ in range(op - 0xa0)]\n                    self.logs += 1; self.loglist.append((me, tps, bytes(mem[off:off + size])))\n")
old2 = "    def restore(self, snap): self.storage, self.transient, self.balances, self.logs = snap\n"
assert src.count(old2) == 1
src = src.replace(old2, "    def restore(self, snap): self.storage, self.transient, self.balances, self.logs = snap; del self.loglist[self.logs:]\n")
exec(compile(src, pyevm.__file__, 'exec'), pyevm.__dict__)
W = pyevm.World
orig_init, orig_call = W.__init__, W.call
def __init__(self, *a, **k):
    orig_init(self, *a, **k); self.loglist = []; self.nodes = []; self.cur = []
def call(self, caller, to, value, data, static, depth, code_addr=None, storage_addr=None, apparent=None):
    nid = len(self.nodes); parent = self.cur[-1] if self.cur else -1
    typ = 'DELEGATECALL' if code_addr not in (None, to) else ('STATICCALL' if static else 'CALL')
    nd = {'id': nid, 'parent': parent, 'type': typ, 'to': to, 'from': caller, 'value': value if code_addr in (None, to) else 0, 'in': bytes(data)}
    self.nodes.append(nd); self.cur.append(nid)
    try:
        ok, ret = orig_call(self, caller, to, value, data, static, depth, code_addr, storage_addr, apparent)
    finally:
        self.cur.pop()
    nd['ok'] = ok; nd['out'] = ret
    return ok, ret
W.__init__ = __init__; W.call = call
import pmdiff as P, pmdiff2 as Q, pmdiff3 as R3, pmdiff6 as R6, pmdiff5 as R5, pmdiff4 as R4
from bytecode import worlds
PMI = int(P.PM, 16)
def hx(b): return b.hex() if b else '-'
def h32(x): return '%064x' % x
def write_tx(f, name, w, drv, data, max_steps, caller=0, delegate_from=None):
    pre = {k: v for (a, k), v in w.storage.items() if a == PMI}
    bal = w.balances.get(PMI, 0)
    w.max_steps = max_steps
    try:
        if delegate_from is None: ok, ret = w.call(caller, drv, 0, data, False, 0)
        else: ok, ret = w.call(caller, delegate_from, 0, data, False, 0, code_addr=drv, storage_addr=delegate_from)
    except TimeoutError:
        return 'heavy'
    except NotImplementedError as e:
        return 'unsupported'
    f.write(f"TX {name} {1 if ok else 0} 1 1700000000 - 0 0 - - 150000000\n")
    for k, v in sorted(pre.items()): f.write(f"PRE {h32(k)} {h32(v)}\n")
    f.write(f"BAL {bal:064x}\n")
    for n in w.nodes:
        pm = 1 if (n['to'] == PMI and n['type'] in ('CALL', 'STATICCALL')) or (delegate_from is not None and n['id'] == 0) else 0
        if delegate_from is not None and n['id'] == 0: n = dict(n, to=PMI, type='CALL')
        f.write(f"N {n['id']} {n['parent']} {pm} {n['type']} {n['to']:040x} {n['from']:040x} {n['value']:064x} 4000000000 0 {1 if n['ok'] else 0} 0 {hx(n['in'])} {hx(n['out'])}\n")
    if ok:
        for a, tps, d in w.loglist:
            if a == PMI: f.write(f"LOG {len(tps)} {' '.join(h32(t) for t in tps)} {hx(d)}\n")
    post = {k: v for (a, k), v in w.storage.items() if a == PMI} if ok else pre
    for k, v in sorted(post.items()):
        if v: f.write(f"POST {h32(k)} {h32(v)}\n")
    if not post or not any(post.values()): f.write(f"POST {h32(0)} {h32(0)}\n")
    return 'ok'
def main():
    out = sys.argv[1]; sets = sys.argv[2] if len(sys.argv) > 2 else '123456'
    os.makedirs(out, exist_ok=True)
    code = P.fetch_code(); w1, w2 = worlds(code)
    open(os.path.join(out, 'pm-build-at-504d0001.hex'), 'w').write(code.hex())
    stats = {}
    todo = []
    if '1' in sets:
        rnd = random.Random(7_2026_11_24); todo.append(('set1', [(P.script(rnd)[0], w1, int(P.DRV, 16)) for _ in range(250)], 3_000_000))
    if '2' in sets:
        rnd = random.Random(11_2026_11_24); todo.append(('set2', [(Q.script(rnd, i)[0], w2, int(P.DRV, 16)) for i in range(300)], 3_000_000))
    if '3' in sets:
        rnd = random.Random(3_2026_11_24); todo.append(('set3', [(R3.build(rnd, i, code)[0], (lambda: R3.world(code)), R3.DRV) for i in range(300)], 20_000_000))
    if '4' in sets:
        rnd = random.Random(3_2026_11_24); base = [R3.build(rnd, i, code) for i in range(300)]
        rnd = random.Random(4_2026_11_24); selectors = list(R3.S.values()) + [P.S_INIT, P.S_MOD, P.S_SWAP, P.S_DONATE, P.S_MINT, P.S_BURN, P.S_TAKE, P.S_SETTLE, P.S_CLEAR, P.S_EXTSLOAD, P.S_UNLOCK]
        sc = []
        for blob, kinds, meta in base:
            items = R4.split(blob)
            for it in items:
                if int.from_bytes(it[0], 'big') == R3.PMI and rnd.random() < 0.35: it[1] = bytearray(R4.damage(rnd, bytes(it[1]), selectors))
            sc.append(b''.join(a + len(d).to_bytes(2, 'big') + bytes(d) for a, d in items if len(d)) + b'\0' * 22)
        todo.append(('set4', [(d, (lambda: R3.world(code)), R3.DRV) for d in sc], 20_000_000))
    if '5' in sets:
        drv5 = P.driver(); todo.append(('set5', [(d, (lambda: pyevm.World({PMI: code, R5.DRV: drv5})), R5.DRV) for d in R5.scripts()], 8_000_000))
    if '6' in sets:
        todo.append(('set6', [(d, (lambda: R6.world(code)), R6.DRV) for nm, d in R6.scripts()], 20_000_000))
    for name, scripts, ms in todo:
        st = {}
        with open(os.path.join(out, name + '.txt'), 'w') as f:
            print('start', name, len(scripts), flush=True)
            for i, (data, mk, drv) in enumerate(scripts):
                if os.environ.get('HEAVY_ONLY'):
                    # second pass: only the scripts that exceeded the step limit of the first pass, with a larger limit
                    import io
                    if write_tx(io.StringIO(), '-', mk(), drv, data, ms) != 'heavy': continue
                    r = write_tx(f, f'{name}-{i}', mk(), drv, data, int(os.environ['HEAVY_ONLY']))
                    st[r] = st.get(r, 0) + 1; continue
                r = write_tx(f, f'{name}-{i}', mk(), drv, data, ms)
                st[r] = st.get(r, 0) + 1
        stats[name] = st; print(name, st, flush=True)
    json.dump(stats, open(os.path.join(out, 'stats.json'), 'w'), indent=1)
if __name__ == "__main__": main()
