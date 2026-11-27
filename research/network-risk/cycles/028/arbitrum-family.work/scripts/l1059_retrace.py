"""Cycle 28 arbitrum-family, lead L-1059: re-trace the failed Arbitrum One PoolManager transactions of
cycles/024/theme-failed-tx-replay.work/raw/42161/tx with callTracer on the Pocket gateway, bracket each trace by
web3_clientVersion, and compare the call tree (without Arbitrum transfer hooks) with the stored cycle 24 trace,
keeping results per build. Read-only RPC. Usage: python3 l1059_retrace.py <out.json>"""
import json, gzip, glob, sys, urllib.request, os
U = 'https://arb-one.api.pocket.network'
D = '/home/user/v4-core/research/network-risk/cycles/024/theme-failed-tx-replay.work/raw/42161/tx'
def rpc(m, p):
    r = urllib.request.Request(U, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'curl/8.5.0'})
    j = json.load(urllib.request.urlopen(r, timeout=90)); return j.get('result'), j.get('error')
def strip(c):
    if isinstance(c, dict):
        return {k: strip(v) for k, v in c.items() if k not in ('beforeEVMTransfers', 'afterEVMTransfers')}
    if isinstance(c, list): return [strip(x) for x in c]
    return c
res = []
for f in sorted(glob.glob(D + '/*.json.gz')):
    d = json.load(gzip.open(f))
    if d.get('kind') != 'failed': continue
    want = strip(d['call']); seen = {}
    for t in range(8):
        try:
            b, _ = rpc('web3_clientVersion', []); tr, err = rpc('debug_traceTransaction', [d['hash'], {'tracer': 'callTracer'}]); a, _ = rpc('web3_clientVersion', [])
        except Exception as e: continue
        if a != b or tr is None: continue
        seen.setdefault(b, strip(tr) == want)
        if len(seen) >= 2: break
    res.append({'hash': d['hash'], 'block': d['block'], 'storedUrl': d['url'], 'byBuild': seen})
    print(d['hash'][:12], seen, flush=True)
json.dump(res, open(sys.argv[1], 'w'), indent=1)
