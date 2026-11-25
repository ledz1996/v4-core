"""Task 2: cycle 13 whole-transaction reruns (theme-mined-branches.work/rerun.py, rows in raw/old/rerun-<cid>.jsonl)
with pyevm2.py corrected in memory so that a DELEGATECALL frame sees the call value of the frame that made it
(the fault cycle 16 found in tools/opdiff/pyevm.py, still present at pyevm2.py:247). Only transactions whose call
tree has a DELEGATECALL frame with a non-zero inherited value can change; those are rerun with both the original
and the corrected interpreter. Read-only RPC. usage: python3 rerun13_fixed.py <cid> <out.jsonl>"""
import sys, os, json, types, concurrent.futures as cf
W13 = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '013', 'theme-mined-branches.work'))
sys.path.insert(0, W13); sys.path.insert(0, os.path.abspath(os.path.join(W13, '..', '..', '..', 'tools', 'opdiff')))
src = open(os.path.join(W13, 'pyevm2.py')).read()
FIX = [("def call(self, caller, to, value, data, static, depth, code_addr=None, storage_addr=None):",
        "def call(self, caller, to, value, data, static, depth, code_addr=None, storage_addr=None, apparent=None):"),
       ("ok, ret = self.run(code_addr, to if storage_addr is None else storage_addr, caller, value, data, static, depth)",
        "ok, ret = self.run(code_addr, to if storage_addr is None else storage_addr, caller, value if apparent is None else apparent, data, static, depth)"),
       ("else: ok, rd = self.call(caller, me, 0, arg, static, depth + 1, code_addr=to, storage_addr=me)",
        "else: ok, rd = self.call(caller, me, 0, arg, static, depth + 1, code_addr=to, storage_addr=me, apparent=value)")]
def build(fixed):
    s = src
    if fixed:
        for a, b in FIX: assert s.count(a) == 1, a; s = s.replace(a, b)
    m = types.ModuleType('pyevm2'); m.__file__ = os.path.join(W13, 'pyevm2.py'); exec(compile(s, m.__file__, 'exec'), m.__dict__); return m
from common import rpc, TRACE
M_OLD, M_FIX = build(False), build(True)
sys.modules['pyevm2'] = M_OLD
import rerun as R

def affected(ct):
    hits = []
    def walk(n, apparent):
        t = n.get('type'); v = int(n.get('value') or '0x0', 16)
        eff = apparent if t == 'DELEGATECALL' else (0 if t == 'STATICCALL' else v)
        if t == 'DELEGATECALL' and eff: hits.append((n.get('to'), (n.get('input') or '')[:10]))
        for c in n.get('calls', []) or []: walk(c, eff)
    walk(ct, int(ct.get('value') or '0x0', 16)); return hits

def summ(r):
    return {k: r.get(k) for k in ('status', 'logs', 'frames', 'storageVsDiff', 'setAside', 'error')}

def one(cid, h):
    try:
        ct = rpc(TRACE[cid], 'debug_traceTransaction', [h, {'tracer': 'callTracer'}])
    except Exception as e: return {'tx': h, 'traceError': str(e)[:120]}
    hits = affected(ct)
    if not hits: return {'tx': h, 'affected': False}
    out = {'tx': h, 'affected': True, 'delegateFramesWithValue': hits[:5], 'nDelegateFramesWithValue': len(hits)}
    for nm, mod in (('original', M_OLD), ('fixed', M_FIX)):
        R.pyevm2 = mod; R.World = mod.World
        try: out[nm] = summ(R.rerun(cid, h, False))
        except Exception as e: out[nm] = {'error': str(e)[:160]}
    out['changed'] = out['original'] != out['fixed']
    return out

if __name__ == '__main__':
    cid, outp = int(sys.argv[1]), sys.argv[2]
    rows = [json.loads(l) for l in open(os.path.join(W13, 'raw', 'old', f'rerun-{cid}.jsonl'))]
    txs = list(dict.fromkeys(r['tx'] for r in rows))
    done = set()
    if os.path.exists(outp): done = {json.loads(l)['tx'] for l in open(outp)}
    todo = [h for h in txs if h not in done]
    print(cid, 'transactions', len(txs), 'to do', len(todo), file=sys.stderr)
    with open(outp, 'a') as f, cf.ThreadPoolExecutor(4) as ex:
        # rerun.py switches the module global, so reruns of affected transactions are done one at a time below
        cts = list(ex.map(lambda h: (h, rpc(TRACE[cid], 'debug_traceTransaction', [h, {'tracer': 'callTracer'}])), todo))
        for h, ct in cts:
            hits = affected(ct)
            if not hits: f.write(json.dumps({'tx': h, 'affected': False}) + '\n'); continue
            r = {'tx': h, 'affected': True, 'delegateFramesWithValue': hits[:5], 'nDelegateFramesWithValue': len(hits)}
            for nm, mod in (('original', M_OLD), ('fixed', M_FIX)):
                R.pyevm2 = mod; R.World = mod.World
                try: r[nm] = summ(R.rerun(cid, h, False))
                except Exception as e: r[nm] = {'error': str(e)[:160]}
            r['changed'] = r['original'] != r['fixed']
            f.write(json.dumps(r) + '\n'); f.flush()
            print(h[:12], r['changed'], r['original'].get('frames'), r['fixed'].get('frames'), file=sys.stderr)
