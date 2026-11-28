"""L-1341: blocks that hold a PoolManager log and a failed deposit (type 0x7e, status 0) before it.
Usage: python3 faileddep.py <rpc> <poolManager> <blocksBack> <step> <out.json>"""
import sys, json, urllib.request, concurrent.futures as cf, time
url, pm, back, step, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
def rpc(m, p, t=60):
    for k in range(4):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(url, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'curl/8'}), timeout=t))
            if 'error' in r: raise Exception(r['error'])
            return r['result']
        except Exception as e:
            err = e; time.sleep(2 * (k + 1))
    raise err
head = int(rpc('eth_blockNumber', []), 16)
blocks = {}
for s in range(head - back, head, step):
    try:
        logs = rpc('eth_getLogs', [{'address': pm, 'fromBlock': hex(s), 'toBlock': hex(min(s + step - 1, head))}])
    except Exception as e:
        print('logs err', s, str(e)[:100]); continue
    for l in logs: blocks.setdefault(int(l['blockNumber'], 16), set()).add(int(l['transactionIndex'], 16))
print('head', head, 'blocks with PoolManager logs', len(blocks), flush=True)
def scan(b):
    rs = rpc('eth_getBlockReceipts', [hex(b)])
    dep = [(int(r['transactionIndex'], 16), r['status'], r.get('depositNonce'), r['from'], r['transactionHash']) for r in rs if r['type'] == '0x7e']
    return b, dep, len(rs)
hits = []; ndep = 0; nfail = 0
with cf.ThreadPoolExecutor(6) as ex:
    for b, dep, n in ex.map(scan, sorted(blocks)):
        ndep += len(dep)
        for (i, st, dn, fr, h) in dep:
            if st == '0x0':
                nfail += 1
                later = sorted(x for x in blocks[b] if x > i)
                hits.append({'block': b, 'depositIndex': i, 'depositTx': h, 'from': fr, 'pmTxIndexesAfter': later})
json.dump({'rpc': url, 'head': head, 'range': [head - back, head], 'pmBlocks': len(blocks), 'deposits': ndep, 'failedDeposits': nfail, 'hits': hits}, open(out, 'w'), indent=1)
print('deposits', ndep, 'failed', nfail, 'hits', hits[:5])
