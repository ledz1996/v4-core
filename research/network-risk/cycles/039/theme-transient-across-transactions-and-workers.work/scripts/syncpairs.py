"""L-1354 / Task 1 and Task 4. Read-only: eth_getLogs, debug_traceBlockByNumber (callTracer, withLog), eth_getBlockReceipts,
web3_clientVersion before and after each batch.
For every mined block in [b0,b1] that holds a PoolManager log (newest first, up to maxBlocks), trace the block and record
every frame sent to the PoolManager in execution order with its selector, whether it or an ancestor failed, its value,
and for sync(address) its argument. Per transaction:
  openSync   = the ERC-20 currency synced by a non-failed sync frame and not followed by a non-failed settle/settleFor
               (sync(address(0)) resets the currency, src/PoolManager.sol:279-288, so it closes the slot)
  nativeSettleFirst = the first non-failed settle/settleFor of the tx comes before any non-failed sync and carries value > 0
  zeroSettleFirst   = same, value 0
  failedUnderUnlock = a frame under a PoolManager unlock failed (a reverted swap/settle/take that wrote transient storage)
Pairs: an earlier successful tx with openSync, a later tx of the same block with nativeSettleFirst or zeroSettleFirst.
Receipts of the producer (receiptsUrl, default the same endpoint) are compared with the traced execution: status, gasUsed
and the multiset of logs of frames that did not fail.
Usage: syncpairs.py <chainId> <traceUrl> <pm> <b0> <b1> <logStep> <maxBlocks> <threads> <out.json> [receiptsUrl]"""
import sys, json, time, os, collections, urllib.request, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
cid, url, pm, b0, b1, step, maxb, th, out = sys.argv[1], sys.argv[2], sys.argv[3].lower(), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7]), int(sys.argv[8]), sys.argv[9]
rurl = sys.argv[10] if len(sys.argv) > 10 else url
lurl = os.environ.get('LOGS_URL', url)  # endpoint for eth_getLogs when the trace endpoint limits log ranges
SIGS = ['unlock(bytes)', 'sync(address)', 'settle()', 'settleFor(address)', 'take(address,address,uint256)', 'clear(address,uint256)',
        'mint(address,uint256,uint256)', 'burn(address,uint256,uint256)', 'swap((address,address,uint24,int24,address),(bool,int256,uint160),bytes)',
        'modifyLiquidity((address,address,uint24,int24,address),(int24,int24,int256,bytes32),bytes)',
        'donate((address,address,uint24,int24,address),uint256,uint256,bytes)', 'initialize((address,address,uint24,int24,address),uint160)',
        'collectProtocolFees(address,address,uint256)']
SEL = {'0x' + keccak(s.encode())[:4].hex(): s.split('(')[0] for s in SIGS}
def rpc(u, m, p, tries=8):
    err = None
    for i in range(tries):
        try:
            r = urllib.request.Request(u, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'rpc-client'})
            d = json.loads(urllib.request.urlopen(r, timeout=180).read())
            if 'error' in d: raise RuntimeError(str(d['error'])[:300])
            return d['result']
        except Exception as e:
            err = e; time.sleep(2 * (i + 1))
    raise err
cvB = {'trace': rpc(url, 'web3_clientVersion', []), 'receipts': rpc(rurl, 'web3_clientVersion', [])}
blocks = set(); b = b1
while b >= b0 and len(blocks) < maxb:
    s = max(b - step + 1, b0)
    for l in rpc(lurl, 'eth_getLogs', [{'address': pm, 'fromBlock': hex(s), 'toBlock': hex(b)}]):
        blocks.add(int(l['blockNumber'], 16))
    b = s - 1
blocks = sorted(blocks, reverse=True)[:maxb]
def walk(f, failed, inU, acc):
    to = (f.get('to') or '').lower(); err = f.get('error'); failed = bool(err) or failed
    inp = f.get('input') or '0x'
    if to == pm:
        s = SEL.get(inp[:10], inp[:10]); arg = None
        if s == 'sync' and len(inp) >= 74: arg = '0x' + inp[34:74]
        acc['pm'].append((s, failed, int(f.get('value') or '0x0', 16), arg))
        if inU and failed: acc['failUnder'].append(s)
    inU2 = inU or (to == pm and inp[:10] == '0x48c89491')
    for l in f.get('logs') or []:
        if not failed: acc['okLog'].append((l['address'].lower(), tuple(l.get('topics') or []), l.get('data')))
    for c in f.get('calls') or []: walk(c, failed, inU2, acc)
def one(bn):
    tr = rpc(url, 'debug_traceBlockByNumber', [hex(bn), {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}])
    rc = rpc(rurl, 'eth_getBlockReceipts', [hex(bn)])
    rmap = {r['transactionHash']: r for r in rc}
    txs = []
    for i, t in enumerate(tr):
        acc = {'pm': [], 'failUnder': [], 'okLog': []}
        res = t.get('result') or {}
        walk(res, False, False, acc)
        if not acc['pm']: continue
        h = t.get('txHash'); r = rmap.get(h) if h else None
        if r is None and len(rc) == len(tr): r = rc[i]; h = h or r['transactionHash']
        st = int(r['status'], 16) if r else None
        openS = None
        for s, f_, v, a in acc['pm']:
            if f_: continue
            if s == 'sync': openS = a if a and int(a, 16) != 0 else None
            elif s in ('settle', 'settleFor'): openS = None
        first = None
        for s, f_, v, a in acc['pm']:
            if f_: continue
            if s == 'sync': break
            if s in ('settle', 'settleFor'): first = v; break
        mism = None
        if r is not None:
            rl = collections.Counter((l['address'].lower(), tuple(l['topics']), l['data']) for l in r['logs'])
            ol = collections.Counter(acc['okLog']) if st == 1 else collections.Counter()
            tst = 0 if res.get('error') else 1
            gt = int(res.get('gasUsed', '0x0'), 16); gr = int(r['gasUsed'], 16)
            if rl != ol or st != tst or gt != gr: mism = {'statusReceipt': st, 'statusTrace': tst, 'gasReceipt': gr, 'gasTrace': gt, 'logsReceipt': sum(rl.values()), 'logsTrace': sum(ol.values())}
        txs.append({'i': i, 'tx': h, 'from': (r or {}).get('from'), 'status': st, 'openSync': openS if st == 1 else None, 'firstSettleValue': first,
                    'failedUnderUnlock': len(acc['failUnder']), 'frames': [x[0] + ('!' if x[1] else '') for x in acc['pm']][:40], 'mismatch': mism})
    return {'block': bn, 'txCount': len(tr), 'pmTxs': txs}
seq = []; errs = {}
with cf.ThreadPoolExecutor(th) as ex:
    fs = {ex.submit(one, bn): bn for bn in blocks}
    for f in cf.as_completed(fs):
        try: seq.append(f.result())
        except Exception as e: errs[fs[f]] = str(e)[:200]
seq.sort(key=lambda x: x['block'])
cvA = {'trace': rpc(url, 'web3_clientVersion', []), 'receipts': rpc(rurl, 'web3_clientVersion', [])}
pairs = []; opens = []; multi = []
for b in seq:
    for j, t in enumerate(b['pmTxs']):
        if t['openSync']: opens.append({'block': b['block'], 'tx': t['tx'], 'currency': t['openSync'], 'frames': t['frames']})
        if t['firstSettleValue'] is not None:
            prev = [p for p in b['pmTxs'][:j] if p['openSync']]
            if prev: pairs.append({'block': b['block'], 'earlier': [p['tx'] for p in prev], 'currency': prev[-1]['openSync'], 'later': t['tx'], 'laterStatus': t['status'], 'settleValue': t['firstSettleValue']})
    senders = {t['from'] for t in b['pmTxs']}
    if len(b['pmTxs']) >= 2 and len(senders) >= 2 and any(t['failedUnderUnlock'] or t['status'] == 0 for t in b['pmTxs']): multi.append(b['block'])
res = {'chainId': int(cid), 'traceUrl': url, 'logsUrl': lurl, 'receiptsUrl': rurl, 'clientVersionBefore': cvB, 'clientVersionAfter': cvA, 'range': [b0, b1],
       'blocksWithPmLogs': len(blocks), 'blocksTraced': len(seq), 'errors': errs, 'txsInTracedBlocks': sum(b['txCount'] for b in seq),
       'pmTxs': sum(len(b['pmTxs']) for b in seq), 'blocksWith2PlusPmTxs': sum(len(b['pmTxs']) >= 2 for b in seq),
       'txsWithFailedFrameUnderUnlock': sum(1 for b in seq for t in b['pmTxs'] if t['failedUnderUnlock']),
       'revertedPmTxs': sum(1 for b in seq for t in b['pmTxs'] if t['status'] == 0),
       'txsLeavingErc20SyncOpen': opens, 'pairs': pairs,
       'laterSettleBeforeSyncTxs': sum(1 for b in seq for t in b['pmTxs'] if t['firstSettleValue'] is not None),
       'laterNativeSettleBeforeSyncTxs': sum(1 for b in seq for t in b['pmTxs'] if (t['firstSettleValue'] or 0) > 0),
       'task4Blocks': multi, 'mismatches': [dict(block=b['block'], **t) for b in seq for t in b['pmTxs'] if t['mismatch']], 'seq': seq}
json.dump(res, open(out, 'w'), indent=1)
print(json.dumps({k: (len(v) if isinstance(v, (list, dict)) and k not in ('clientVersionBefore', 'clientVersionAfter', 'range') else v) for k, v in res.items() if k != 'seq'}))
