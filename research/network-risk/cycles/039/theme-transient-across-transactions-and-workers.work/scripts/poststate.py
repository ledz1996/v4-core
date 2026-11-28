"""Task 4 on Polygon: for blocks where two senders call the PoolManager and at least one PoolManager transaction failed
inside unlock or reverted (task4Blocks of syncpairs.py), take the serial re-execution of the block (prestateTracer, diffMode)
and compare the PoolManager words it reports as written with eth_getStorageAt at that block on the committed chain.
Read-only. Usage: poststate.py <in sp-137.json> <traceUrl> <stateUrl> <pm> <out.json>"""
import sys, json, time, urllib.request
src, turl, surl, pm, out = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].lower(), sys.argv[5]
def rpc(u, m, p):
    for i in range(8):
        try:
            r = urllib.request.Request(u, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'rpc-client'})
            d = json.loads(urllib.request.urlopen(r, timeout=180).read())
            if 'error' in d: raise RuntimeError(str(d['error'])[:300])
            return d['result']
        except Exception as e:
            err = e; time.sleep(2 * (i + 1))
    raise err
blocks = json.load(open(src))['task4Blocks']
cv0 = {'trace': rpc(turl, 'web3_clientVersion', []), 'state': rpc(surl, 'web3_clientVersion', [])}
res = []; words = 0; bad = []
for bn in blocks:
    tr = rpc(turl, 'debug_traceBlockByNumber', [hex(bn), {'tracer': 'prestateTracer', 'tracerConfig': {'diffMode': True}}])
    post = {}
    for t in tr:
        r = t.get('result') or {}
        for a, acct in (r.get('post') or {}).items():
            if a.lower() != pm: continue
            for k, v in (acct.get('storage') or {}).items(): post[k] = v
        for a, acct in (r.get('pre') or {}).items():
            if a.lower() != pm: continue
            for k in (acct.get('storage') or {}):
                if k not in (((r.get('post') or {}).get(a) or {}).get('storage') or {}): post.setdefault(k, None)  # cleared slot
    diffs = []
    for k, v in post.items():
        got = rpc(surl, 'eth_getStorageAt', [pm, k, hex(bn)])
        exp = v if v is not None else '0x' + '0' * 64
        words += 1
        if int(got, 16) != int(exp, 16): diffs.append({'slot': k, 'trace': exp, 'chain': got})
    res.append({'block': bn, 'pmWords': len(post), 'diffs': diffs})
    if diffs: bad.append(bn)
cv1 = {'trace': rpc(turl, 'web3_clientVersion', []), 'state': rpc(surl, 'web3_clientVersion', [])}
o = {'clientVersionBefore': cv0, 'clientVersionAfter': cv1, 'blocks': len(blocks), 'words': words, 'blocksWithDiff': bad, 'detail': res}
json.dump(o, open(out, 'w'), indent=1)
print(json.dumps({k: v for k, v in o.items() if k != 'detail'}))
