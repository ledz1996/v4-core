# Complete currency list for a network from the Initialize logs of the PoolManager (currency0 and currency1 are topics 2 and 3).
# Cycle 4 had no such list for Base, BNB Smart Chain and X Layer; its lists there hold only tokens that moved in its window.
import sys, json, gzip, os
from concurrent.futures import ThreadPoolExecutor
from base import *
INIT = '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'
LOGURL = {8453: 'https://base.gateway.tenderly.co', 56: 'https://bsc-rpc.publicnode.com'}   # publicnode serves recent blocks only
ARCH = {8453: ['https://base.gateway.tenderly.co', 'https://base.drpc.org'], 56: ['https://bsc-mainnet.public.blastapi.io', 'https://bsc.drpc.org', 'https://bsc-rpc.publicnode.com']}
def deploy_block(cid, pm, head):
    for u in ARCH[cid]:
        try:
            lo, hi = 0, head
            while lo + 1 < hi:
                m = (lo + hi) // 2
                if rpc(u, 'eth_getCode', [pm, hex(m)], timeout=30, tries=3) in ('0x', '0x0'): lo = m
                else: hi = m
            return hi
        except Exception as e: print('deploy search failed', u, str(e)[:100], flush=True)
    return None
def run(cid, span=1000, workers=12):
    pm = net(cid)['poolManager']; u = LOGURL[cid]
    head = int(rpc(u, 'eth_blockNumber', []), 16)
    dep = deploy_block(cid, pm, head)
    print(cid, 'deploy block', dep, 'head', head, flush=True)
    cur = {}; nlog = 0; fails = []
    def get(a, b, depth=0):
        for k in range(6):
            try:
                j = post(u, {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_getLogs', 'params': [{'address': pm, 'topics': [INIT], 'fromBlock': hex(a), 'toBlock': hex(b)}]}, timeout=90, tries=1)
                if 'result' in j: return j['result']
                msg = str(j.get('error'))[:120]
                if depth < 8 and b > a and any(s in msg for s in ('too many', 'limit', 'size', 'range', '10000', 'exceed')):
                    m = (a + b) // 2
                    return get(a, m, depth + 1) + get(m + 1, b, depth + 1)
            except Exception as e: msg = str(e)[:100]
            time.sleep(1 + k)
        fails.append((a, b, msg)); return []
    rngs = [(a, min(head, a + span - 1)) for a in range(dep, head + 1, span)]
    with ThreadPoolExecutor(workers) as ex:
        for i, logs in enumerate(ex.map(lambda r: get(*r), rngs)):
            for l in logs:
                if len(l['topics']) == 4:
                    nlog += 1
                    for t in l['topics'][2:4]:
                        a = '0x' + t[-40:]; cur[a] = cur.get(a, 0) + 1
            if i % 2000 == 0: print(cid, i, len(rngs), 'logs', nlog, 'currencies', len(cur), 'fails', len(fails), flush=True)
    json.dump(dict(chainId=cid, url=u, deployBlock=dep, toBlock=head, nInit=nlog, currencies=cur, fails=fails), gzip.open(os.path.join(RAW6, 'census_%d.json.gz' % cid), 'wt'))
    print(cid, 'done logs', nlog, 'currencies', len(cur), 'fails', len(fails), fails[:3], flush=True)
if __name__ == '__main__':
    run(int(sys.argv[1]))
