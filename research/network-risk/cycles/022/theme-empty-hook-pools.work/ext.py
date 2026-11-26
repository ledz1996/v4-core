"""Extend the Initialize history of one network from the end of the earlier scan to head-20. Read only (eth_getLogs).
Rows: [block, poolId topic, currency0, currency1, fee, tickSpacing, hooks, txHash, logIndex].
usage: ext.py <chainId> <url> <chunk> <fromBlock> [workers]"""
import sys, json, gzip, threading, time, concurrent.futures as cf
from ep import rpc, NETS, INIT
cid, url, chunk, lo = int(sys.argv[1]), sys.argv[2], int(sys.argv[3]), int(sys.argv[4]); W = int(sys.argv[5]) if len(sys.argv) > 5 else 4
pm = NETS[cid]['poolManager']
cv0 = rpc(url, 'web3_clientVersion', []); head = int(rpc(url, 'eth_blockNumber', []), 16) - 20
rows = []; lock = threading.Lock(); st = {'req': 0, 'split': 0, 'fail': []}
def get(a, b, d=0):
    for k in range(6):
        try:
            st['req'] += 1
            return rpc(url, 'eth_getLogs', [{'address': pm, 'topics': [INIT], 'fromBlock': hex(a), 'toBlock': hex(b)}], tries=3)
        except Exception as e:
            m = str(e).lower()
            if b > a and any(x in m for x in ('range', 'too many', 'exceed', 'too large', 'limit', '10000', 'size', 'max', 'timeout', 'response')) and 'rate' not in m:
                st['split'] += 1; mid = (a + b) // 2; return get(a, mid, d + 1) + get(mid + 1, b, d + 1)
            time.sleep(3 * (k + 1)); last = e
    st['fail'].append([a, b, str(last)[:150]]); return []
def one(a):
    b = min(head, a + chunk - 1); L = get(a, b)
    with lock:
        for l in L:
            if l.get('removed'): continue
            d = l['data'][2:]; t = l['topics']
            rows.append([int(l['blockNumber'], 16), t[1], '0x' + t[2][-40:], '0x' + t[3][-40:], int(d[0:64], 16), int(d[64:128], 16), '0x' + d[128:192][-40:], l['transactionHash'], int(l['logIndex'], 16)])
with cf.ThreadPoolExecutor(W) as ex: list(ex.map(one, range(lo, head + 1, chunk)))
cv1 = rpc(url, 'web3_clientVersion', [])
rows.sort()
json.dump({'chainId': cid, 'url': url, 'lo': lo, 'hi': head, 'clientVersionStart': cv0, 'clientVersionEnd': cv1, 'finished': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), **st, 'rows': rows}, gzip.open('raw/initext_%d.json.gz' % cid, 'wt'))
print(cid, 'lo', lo, 'hi', head, 'rows', len(rows), 'req', st['req'], 'split', st['split'], 'fail', len(st['fail']), flush=True)
