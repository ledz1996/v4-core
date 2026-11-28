"""L-1354 on Arc, where no public endpoint serves call traces. Read-only: eth_getLogs, eth_getBlockByNumber, eth_getBlockReceipts,
web3_clientVersion before and after.
For blocks with PoolManager logs (newest first, up to maxBlocks), list the transactions whose receipt has a PoolManager log or
whose `to` is the PoolManager, with sender, `to`, selector, status, and whether the calldata holds the sync(address) selector
0xa5841194 or the settle() selector 0x11da60b4 anywhere (a router that passes them as data or a direct call).
A direct sync(token) to the PoolManager by an EOA leaves the synced currency set when the transaction ends (src/PoolManager.sol:279-288).
Usage: arcscan.py <url> <pm> <b0> <b1> <logStep> <maxBlocks> <out.json>"""
import sys, json, time, urllib.request, collections
url, pm, b0, b1, step, maxb, out = sys.argv[1], sys.argv[2].lower(), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]), sys.argv[7]
def rpc(m, p):
    for i in range(8):
        try:
            r = urllib.request.Request(url, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'rpc-client'})
            d = json.loads(urllib.request.urlopen(r, timeout=120).read())
            if 'error' in d: raise RuntimeError(str(d['error'])[:300])
            return d['result']
        except Exception as e:
            err = e; time.sleep(2 * (i + 1))
    raise err
cv0 = rpc('web3_clientVersion', [])
blocks = set(); b = b1; logged = 0
while b >= b0 and len(blocks) < maxb:
    s = max(b - step + 1, b0)
    for l in rpc('eth_getLogs', [{'address': pm, 'fromBlock': hex(s), 'toBlock': hex(b)}]): blocks.add(int(l['blockNumber'], 16))
    logged += b - s + 1; b = s - 1
blocks = sorted(blocks, reverse=True)[:maxb]
seq = []; toC = collections.Counter(); directSync = []; syncInData = []; multi = 0; multiSenders = 0
for bn in blocks:
    blk = rpc('eth_getBlockByNumber', [hex(bn), True]); rc = {r['transactionHash']: r for r in rpc('eth_getBlockReceipts', [hex(bn)])}
    txs = []
    for i, t in enumerate(blk['transactions']):
        r = rc[t['hash']]
        touches = (t.get('to') or '').lower() == pm or any(l['address'].lower() == pm for l in r['logs'])
        if not touches: continue
        inp = t['input']; sel = inp[:10]
        rec = {'i': i, 'tx': t['hash'], 'from': t['from'], 'to': t.get('to'), 'sel': sel, 'status': int(r['status'], 16),
               'syncSelInData': 'a5841194' in inp[2:], 'settleSelInData': '11da60b4' in inp[2:]}
        toC[(t.get('to') or '').lower()] += 1
        if (t.get('to') or '').lower() == pm and sel == '0xa5841194': directSync.append({'block': bn, **rec})
        if rec['syncSelInData']: syncInData.append({'block': bn, **rec})
        txs.append(rec)
    if len(txs) >= 2: multi += 1
    if len({x['from'] for x in txs}) >= 2: multiSenders += 1
    seq.append({'block': bn, 'txs': txs})
cv1 = rpc('web3_clientVersion', [])
res = {'url': url, 'clientVersionBefore': cv0, 'clientVersionAfter': cv1, 'range': [b0, b1], 'blocksScannedForLogs': logged, 'blocksWithPmLogs': len(blocks),
       'pmTxs': sum(len(s['txs']) for s in seq), 'blocksWith2PlusPmTxs': multi, 'blocksWith2PlusSenders': multiSenders,
       'toCounts': toC.most_common(20), 'directSyncTxs': directSync, 'txsWithSyncSelectorInCalldata': len(syncInData),
       'syncSelectorExamples': syncInData[:20], 'seq': seq}
json.dump(res, open(out, 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ('seq', 'syncSelectorExamples')}, indent=0)[:3000])
