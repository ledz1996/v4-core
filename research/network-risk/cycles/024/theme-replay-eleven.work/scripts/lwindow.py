"""Window for gdrive.py: newest PoolManager transactions with a log, newest first, from eth_getLogs on the PoolManager.
usage: lwindow.py <cid> <url> <target> <span> <out.json>"""
import sys, json, time
from rpcu import call
from eps import NETS
cid, url, target, span, outp = int(sys.argv[1]), sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
PM = NETS[cid]['poolManager']
cv0 = call(url, 'web3_clientVersion', [])
head = int(call(url, 'eth_blockNumber', [])[0], 16); hi = head; txs = {}; pmtx = {}; errs = []; nlogs = 0
while len(txs) < target and hi > 0:
    lo = max(0, hi - span + 1)
    r, e = call(url, 'eth_getLogs', [{'address': PM, 'fromBlock': hex(lo), 'toBlock': hex(hi)}], 90)
    if e:
        errs.append([lo, hi, e[:200]]); time.sleep(2)
        if len(errs) > 200: break
        if 'range' in e or 'large' in e or 'limit' in e or 'exceed' in e: span = max(10, span // 2)
        continue
    for l in r:
        b = int(l['blockNumber'], 16); i = int(l['transactionIndex'], 16); nlogs += 1
        txs.setdefault(l['transactionHash'], (b, i)); pmtx.setdefault(b, set()).add(i)
    hi = lo - 1
order = sorted(txs.items(), key=lambda kv: (-kv[1][0], -kv[1][1]))[:target]
json.dump({'chainId': cid, 'url': url, 'head': head, 'scannedDownTo': hi + 1, 'logs': nlogs, 'clientBefore': cv0, 'clientAfter': call(url, 'web3_clientVersion', []),
           'txs': [[h, b, i] for h, (b, i) in order], 'pmTx': {str(b): sorted(v) for b, v in pmtx.items()}, 'errors': errs[:50], 'nErrors': len(errs),
           'time': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, open(outp, 'w'))
print(cid, 'window', len(order), 'blocks', order[-1][1] if order else None, order[0][1] if order else None, 'errors', len(errs))
