"""Trace mined blocks that hold PoolManager logs and record every frame sent to the PoolManager.
Read-only: eth_getLogs, debug_traceBlockByNumber (callTracer, withLog), eth_getBlockReceipts.
Usage: python3 pmtrace.py <chainId> <rpc> <pm> <fromBlock> <toBlock> <logStep> <maxBlocks> <out.json>
Records per chain: selector counts of PoolManager frames (clear, settleFor, ERC-6909 transfer...), failed
frames under a PoolManager unlock, receipt logs against logs of frames that did not fail, and per block
the order of transactions that leave a sync open and later transactions that settle."""
import sys, json, time, urllib.request, os, collections
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import keccak
cid, url, pm, b0, b1, step, maxb, out = sys.argv[1], sys.argv[2], sys.argv[3].lower(), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7]), sys.argv[8]
SIGS = ['unlock(bytes)', 'sync(address)', 'settle()', 'settleFor(address)', 'take(address,address,uint256)', 'clear(address,uint256)',
        'mint(address,uint256,uint256)', 'burn(address,uint256,uint256)', 'transfer(address,uint256,uint256)',
        'transferFrom(address,address,uint256,uint256)', 'approve(address,uint256,uint256)', 'setOperator(address,bool)',
        'swap((address,address,uint24,int24,address),(bool,int256,uint160),bytes)',
        'modifyLiquidity((address,address,uint24,int24,address),(int24,int24,int256,bytes32),bytes)',
        'donate((address,address,uint24,int24,address),uint256,uint256,bytes)', 'initialize((address,address,uint24,int24,address),uint160)',
        'extsload(bytes32)', 'extsload(bytes32,uint256)', 'extsload(bytes32[])', 'exttload(bytes32)', 'exttload(bytes32[])']
SEL = {'0x' + keccak(s.encode())[:4].hex(): s.split('(')[0] + ('' if s.count('(') == 1 and s != 'extsload(bytes32[])' and s != 'exttload(bytes32[])' else '') for s in SIGS}
SEL = {'0x' + keccak(s.encode())[:4].hex(): s for s in SIGS}
def rpc(m, p, tries=10):
    time.sleep(float(os.environ.get('PMT_SLEEP', '0')))
    for i in range(tries):
        try:
            r = urllib.request.Request(url, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'opdiff'})
            d = json.loads(urllib.request.urlopen(r, timeout=120).read())
            if 'error' in d: raise RuntimeError(d['error'])
            return d['result']
        except Exception as e:
            err = e; time.sleep(1.5 * (i + 1))
    raise err
blocks = []
b = b0
while b <= b1 and len(blocks) < maxb:
    e = min(b + step - 1, b1)
    for l in rpc('eth_getLogs', [{'address': pm, 'fromBlock': hex(b), 'toBlock': hex(e)}]):
        n = int(l['blockNumber'], 16)
        if not blocks or blocks[-1] != n: blocks.append(n)
    b = e + 1
blocks = sorted(set(blocks))[:maxb]
sel = collections.Counter(); failedUnderUnlock = []; logMismatch = []; seq = []; txs = 0; pmtx = 0; statusMismatch = []
def walk(f, ctx, acc):
    to = (f.get('to') or '').lower(); err = f.get('error'); failed = bool(err) or ctx['failed']
    if to == pm:
        s = SEL.get((f.get('input') or '0x')[:10], (f.get('input') or '0x')[:10])
        acc['pm'].append((s, failed, int(f.get('value') or '0x0', 16), bool(err)))
        if ctx['inUnlock'] and failed: acc['failUnder'].append((s, err))
    inU = ctx['inUnlock'] or (to == pm and (f.get('input') or '')[:10] == '0x48c89491')
    for l in f.get('logs') or []:
        (acc['flog'] if failed else acc['okLog']).append((l['address'].lower(), tuple(l.get('topics') or []), l.get('data')))
    for c in f.get('calls') or []:
        walk(c, {'failed': failed, 'inUnlock': inU}, acc)
for bn in blocks:
    tr = rpc('debug_traceBlockByNumber', [hex(bn), {'tracer': 'callTracer', 'tracerConfig': {'withLog': True}}])
    rc = rpc('eth_getBlockReceipts', [hex(bn)])
    rmap = {r['transactionHash']: r for r in rc}
    bseq = []
    for i, t in enumerate(tr):
        txs += 1; acc = {'pm': [], 'failUnder': [], 'okLog': [], 'flog': []}
        walk(t['result'], {'failed': False, 'inUnlock': False}, acc)
        r = rmap.get(t.get('txHash'))
        if r is None and i < len(rc): r = rc[i]
        if not acc['pm']: continue
        pmtx += 1
        for s, fl, v, own in acc['pm']: sel[(s, 'failed' if fl else 'ok')] += 1
        st = int(r['status'], 16)
        if st != (0 if t['result'].get('error') else 1): statusMismatch.append((bn, t.get('txHash')))
        rl = collections.Counter((l['address'].lower(), tuple(l['topics']), l['data']) for l in r['logs'])
        ol = collections.Counter(acc['okLog']) if st == 1 else collections.Counter()
        fl = collections.Counter(acc['flog'])
        if rl != ol or any(rl[k] for k in fl if k not in ol): logMismatch.append({'block': bn, 'tx': t.get('txHash'), 'receipt': sum(rl.values()), 'okFrames': sum(ol.values()), 'failedFrames': sum(fl.values())})
        if acc['failUnder']: failedUnderUnlock.append({'block': bn, 'tx': t.get('txHash'), 'status': st, 'frames': acc['failUnder'][:6], 'failedFrameLogs': sum(fl.values()), 'receiptLogs': len(r['logs'])})
        # sync state at the end of the tx (frames that did not fail, in order)
        open_ = None
        for s, f_, v, own in acc['pm']:
            if f_: continue
            if s == 'sync(address)': open_ = 'sync'
            elif s in ('settle()', 'settleFor(address)'): open_ = None
        firstSettleNoSync = None
        seen_sync = False
        for s, f_, v, own in acc['pm']:
            if f_: continue
            if s == 'sync(address)': seen_sync = True
            if s in ('settle()', 'settleFor(address)') and not seen_sync: firstSettleNoSync = v; break
        bseq.append({'innerUnlockFailed': any(x[0]=='unlock(bytes)' and x[1] for x in acc['pm']), 'unlockOk': any(x[0]=='unlock(bytes)' and not x[1] for x in acc['pm']), 'i': i, 'tx': t.get('txHash'), 'status': st, 'leavesSyncOpen': open_ == 'sync', 'settleBeforeSync': firstSettleNoSync is not None, 'settleValue': firstSettleNoSync, 'gasUsedTrace': int(t['result'].get('gasUsed', '0x0'), 16), 'gasUsedReceipt': int(r['gasUsed'], 16)})
    seq.append({'block': bn, 'txs': bseq})
# pairs: an earlier tx leaves sync open and a later tx of the block settles before its own sync
pairs = []
for b in seq:
    for j, t in enumerate(b['txs']):
        if t['settleBeforeSync'] and any(p['leavesSyncOpen'] and p['status'] == 1 for p in b['txs'][:j]):
            pairs.append({'block': b['block'], 'tx': t['tx'], 'status': t['status'], 'settleValue': t['settleValue']})
after = []
for b in seq:
    for j, t in enumerate(b['txs']):
        if t['innerUnlockFailed'] or t['status'] == 0:
            later = [u for u in b['txs'][j+1:] if u['unlockOk'] and u['status'] == 1]
            if later: after.append({'block': b['block'], 'failedTx': t['tx'], 'failedTxStatus': t['status'], 'laterOkUnlockTxs': len(later)})
res = {'afterFailedUnlock': after, 'afterFailedUnlockCount': len(after), 'chainId': int(cid), 'rpc': url, 'range': [b0, b1], 'blocksTraced': len(blocks), 'firstBlock': blocks[0] if blocks else None, 'lastBlock': blocks[-1] if blocks else None,
       'txsTraced': txs, 'pmTxs': pmtx, 'selectors': {f'{k[0]}|{k[1]}': v for k, v in sorted(sel.items())},
       'statusMismatch': statusMismatch, 'logMismatch': logMismatch, 'failedUnderUnlock': failedUnderUnlock[:200], 'failedUnderUnlockCount': len(failedUnderUnlock),
       'syncLeftOpenThenSettle': pairs, 'txsLeavingSyncOpen': sum(t['leavesSyncOpen'] for b in seq for t in b['txs']),
       'gasMismatch': [(b['block'], t['tx'], t['gasUsedTrace'], t['gasUsedReceipt']) for b in seq for t in b['txs'] if t['gasUsedTrace'] != t['gasUsedReceipt']][:50]}
res['seq'] = seq
json.dump(res, open(out, 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ('seq', 'afterFailedUnlock', 'failedUnderUnlock', 'syncLeftOpenThenSettle', 'logMismatch', 'gasMismatch')}, indent=1))
print('logMismatch', len(logMismatch), 'pairs', len(pairs), 'gasMismatch', len(res['gasMismatch']))
