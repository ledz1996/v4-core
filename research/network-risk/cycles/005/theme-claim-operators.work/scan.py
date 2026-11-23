# OperatorSet and Approval logs of each PoolManager over its whole history (read-only eth_getLogs).
import sys, json, os, gzip, concurrent.futures as cf
from lib import *
from fetch import getlogs_range
from config import CFG
OP='0xceb576d9f15e4e200fdb5096d64d5dfd667e16def20c1eefd14256d8e3faa267'
AP='0xb3fd5071835887567a0671151121894ddccc2842f1d10bedad13e0d17cace9a7'
PRIOR = os.path.join(HERE, '..', '..', '004', 'theme-balance-reconcile.work', 'raw')
# endpoint, chunk, deploy block override
OVR = {8453: ('https://base.gateway.tenderly.co', 1000, None), 56: ('https://rpc-bsc.48.club', 5000, None)}
def deploy_block(url, pm, head):
    lo, hi = 0, head
    if rpc(url, 'eth_getCode', [pm, hex(1)]) not in ('0x', '0x0'): return 0
    while lo + 1 < hi:
        m = (lo + hi) // 2
        if rpc(url, 'eth_getCode', [pm, hex(m)]) in ('0x', '0x0'): lo = m
        else: hi = m
    return hi
def run(cid, workers=3):
    n = net(cid); pm = n['poolManager']; fn = 'raw/logs_%d.json' % cid
    if os.path.exists(os.path.join(HERE, fn)): return cid, 'cached'
    if cid in OVR: u, chunk, dep = OVR[cid]
    else: u, chunk, dep = CFG[cid]['init'], CFG[cid]['initChunk'], None
    head = int(rpc(u, 'eth_blockNumber', []), 16)
    if dep is None:
        try:
            dep = json.load(gzip.open(os.path.join(PRIOR, 'currencies_%d.json.gz' % cid), 'rt')).get('deployBlock')
        except Exception: dep = None
    if dep is None:
        for su in CFG[cid]['state'][::-1]:
            try: dep = deploy_block(su, pm, head); break
            except Exception as e: print(cid, 'deploy search failed', su, str(e)[:100], flush=True)
    logs = []
    st = getlogs_range(u, {'address': pm, 'topics': [[OP, AP]]}, dep or 0, head, chunk, workers=workers, on_logs=logs.extend, label='logs %d' % cid)
    o = dict(chainId=cid, poolManager=pm, url=u, fromBlock=dep or 0, toBlock=head, chunk=chunk, stats=st,
             logs=[dict(b=int(l['blockNumber'], 16), tx=l['transactionHash'], t=l['topics'], d=l['data']) for l in logs])
    json.dump(o, open(os.path.join(HERE, fn), 'w'))
    return cid, dep, head, len(logs), st['req'], st['fail'][:3]
if __name__ == '__main__':
    ids = [int(x) for x in sys.argv[1:]]
    with cf.ThreadPoolExecutor(len(ids)) as ex:
        for r in ex.map(run, ids): print(r, flush=True)
