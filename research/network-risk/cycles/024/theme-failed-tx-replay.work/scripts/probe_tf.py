"""Probe which public endpoints serve trace_filter (toAddress = PoolManager) on a recent block of the cycle 23 window. Read-only."""
import json, sys, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/023/theme-state-replay.work/scripts')
from rpcu import call
from eps import NETS, CAND
W = '/home/user/v4-core/research/network-risk/cycles/023/theme-state-replay.work/raw/%d/window.json'
EXTRA = {1: ['https://eth.api.pocket.network'], 8453: ['https://base.api.pocket.network'], 130: ['https://unichain.api.pocket.network'],
         42161: ['https://arb-one.api.pocket.network'], 56: ['https://bsc.api.pocket.network'], 43114: ['https://avax.api.pocket.network'],
         137: ['https://poly.api.pocket.network'], 143: [], 4326: [], 999: ['https://rpc.purroofgroup.com']}
out = {}
for cid in [1, 8453, 130, 42161, 56, 43114, 137, 143, 4326, 999]:
    w = json.load(open(W % cid)); b = w['lastBlock']; pm = NETS[cid]['poolManager']
    for u in EXTRA[cid] + CAND[cid]:
        v, e0 = call(u, 'web3_clientVersion', [], 20)
        r, e = call(u, 'trace_filter', [{'fromBlock': hex(b - 20), 'toBlock': hex(b), 'toAddress': [pm]}], 60)
        out.setdefault(cid, []).append({'url': u, 'client': v, 'n': len(r) if r is not None else None, 'err': (e or '')[:160]})
        print(cid, u, v, len(r) if r is not None else None, (e or '')[:120], flush=True)
json.dump(out, open('../raw/probe_trace_filter.json', 'w'), indent=1)
