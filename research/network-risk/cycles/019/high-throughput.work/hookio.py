"""L-836 (variant of firstpm.py): watch the frames of a chosen address (a hook) instead of the PoolManager.
For one mined transaction, rerun it with cycles/017/theme-reference-interpreter-audit.work/replay17.py
(read, not changed) and record the input and output of every PoolManager frame in start order, then compare with the
chain's callTracer frames of the PoolManager. Reports the first PoolManager frame whose input differs (the divergence
started in the caller) or whose output differs for the same input (the divergence is inside the PoolManager).
Read-only RPC. usage: python3 hookio.py <chainId> <rpc> <txhash> <out.json> <address>"""
import sys, os, json
NR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
A17 = os.path.join(NR, 'cycles', '017', 'theme-reference-interpreter-audit.work')
sys.path.insert(0, A17)
import replay17 as R17
P = R17.P
orig = P.World.call


def call(self, caller, to, value, data, static, depth, code_addr=None, storage_addr=None):
    rec = None
    if to in WATCH and code_addr is None:
        rec = [depth, bytes(data).hex(), None, None]
        self.__dict__.setdefault('io', []).append(rec)
    ok, ret = orig(self, caller, to, value, data, static, depth, code_addr, storage_addr)
    if rec is not None: rec[2] = bool(ok); rec[3] = bytes(ret).hex()
    return ok, ret


WATCH = {int(sys.argv[5], 16)}
P.World.call = call
holder = {}
origW = P.World.__init__


def init(self, *a, **k):
    origW(self, *a, **k); holder['w'] = self


P.World.__init__ = init


def chain_frames(node, pm, acc, depth=0):
    if int(node.get("to") or "0x0", 16) in WATCH and node.get("type") in ("CALL", "STATICCALL"):
        acc.append([depth, (node.get('input') or '0x')[2:].lower(), 'error' not in node, (node.get('output') or '0x')[2:].lower()])
    for c in node.get('calls', []) or []: chain_frames(c, pm, acc, depth + 1)


if __name__ == '__main__':
    cid, url, h, out = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
    nets = {n['chainId']: n for n in json.load(open(os.path.join(NR, 'state', 'networks.json')))['networks']}
    pm = nets[cid]['poolManager'].lower()
    r = R17.one(cid, url, pm, h)
    w = holder.get('w'); ref = getattr(w, 'io', []) if w else []
    ct = R17.R(url, 'debug_traceTransaction', [h, {'tracer': 'callTracer'}])
    ch = []; chain_frames(ct, pm, ch)
    first = None
    for i in range(max(len(ch), len(ref))):
        if i >= len(ch) or i >= len(ref):
            first = {'index': i, 'kind': 'frame count', 'chainFrames': len(ch), 'refFrames': len(ref)}; break
        c, x = ch[i], ref[i]
        if c[1] != x[1]:
            first = {'index': i, 'kind': 'input differs', 'selector': c[1][:8], 'chainInput': c[1][:200], 'refInput': x[1][:200]}; break
        # unlock returns whatever the caller's unlockCallback returned, so its output is the caller's, not the PoolManager's
        if c[2] != x[2] or (c[2] and c[3] != x[3]):
            first = {'index': i, 'kind': 'output differs for the same input', 'selector': c[1][:8], 'chainOk': c[2], 'refOk': x[2], 'chainOut': c[3][:200], 'refOut': x[3][:200]}; break
    res = {'tx': h, 'chainId': cid, 'statusChain': r.get('statusChain'), 'statusRef': r.get('statusRef'), 'forcedOOG': r.get('forcedOOG'),
           'pmFramesChain': len(ch), 'pmFramesRef': len(ref), 'firstPmDivergence': first, 'unsupported': r.get('unsupported'),
           'unlockOutputsDiffer': [i for i in range(min(len(ch), len(ref))) if ch[i][1][:8] == '48c89491' and ch[i][1] == ref[i][1] and ch[i][3] != ref[i][3]],
           'chainFrames': [[c[1][:200], c[3][:200]] for c in ch], 'refFrames': [[x[1][:200], (x[3] or '')[:200]] for x in ref], 'refAllFramesStatus': [x[2] for x in ref], 'chainAllFramesStatus': [c[2] for c in ch]}
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps(res)[:400])
