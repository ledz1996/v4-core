# Hook census: read the Initialize logs of the PoolManager and count pools per hook address.
# Read-only: eth_getLogs, eth_blockNumber, eth_getCode.
# usage: python3 init_census.py <chainId> [url] [chunk] [fromBlock] [toBlock] [workers]
import sys, json, gzip, threading, collections
from lib import *
from config import CFG
from fetch import getlogs_range
INIT = '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'
def deploy_block(urls, pm, head):
    for u in urls:
        try:
            lo, hi = 0, head
            if rpc(u, 'eth_getCode', [pm, hex(1)]) not in ('0x', None): return 0
            while lo < hi:
                m = (lo + hi) // 2
                c = rpc(u, 'eth_getCode', [pm, hex(m)])
                if c and c != '0x': hi = m
                else: lo = m + 1
            return lo
        except Exception as e:
            print('deploy search failed on', u, repr(e)[:150], flush=True)
    return 0
def run(cid, url=None, chunk=None, lo=None, hi=None, workers=4, tag=''):
    n = net(cid); c = CFG[cid]; pm = n['poolManager']
    url = url or c['init']; chunk = chunk or c['initChunk']
    head = int(rpc(url, 'eth_blockNumber', []), 16)
    if hi is None: hi = head - 5
    if lo is None: lo = deploy_block(c['state'] + [url], pm, head)
    print(cid, n['name'], 'url', url, 'lo', lo, 'hi', hi, 'chunk', chunk, flush=True)
    rows = []; lock = threading.Lock()
    def on(logs):
        with lock:
            for l in logs:
                if l.get('removed'): continue
                d = l['data'][2:]; t = l['topics']
                rows.append((int(l['blockNumber'], 16), t[1], '0x' + t[2][-40:], '0x' + t[3][-40:], int(d[0:64], 16), int(d[64:128], 16), '0x' + d[128:192][-40:], l['transactionHash']))
    st = getlogs_range(url, {'address': pm, 'topics': [INIT]}, lo, hi, chunk, workers=workers, on_logs=on, label='%d init' % cid)
    rows.sort()
    fn = 'raw/init_%d%s.json.gz' % (cid, tag)
    json.dump(dict(chainId=cid, url=url, lo=lo, hi=hi, nFail=len(st['fail']), fail=st['fail'][:20], req=st['req'], rows=rows), gzip.open(fn, 'wt'))
    cnt = collections.Counter(r[6] for r in rows)
    print(cid, n['name'], 'pools', len(rows), 'hooks', len(cnt), 'fail', len(st['fail']), 'req', st['req'])
    for h, k in cnt.most_common(12): print('   ', h, k)
if __name__ == '__main__':
    a = sys.argv
    run(int(a[1]), a[2] if len(a) > 2 and a[2] != '-' else None, int(a[3]) if len(a) > 3 and a[3] != '-' else None,
        int(a[4]) if len(a) > 4 and a[4] != '-' else None, int(a[5]) if len(a) > 5 and a[5] != '-' else None, int(a[6]) if len(a) > 6 else 4, a[7] if len(a) > 7 else '')
