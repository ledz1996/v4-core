"""theme-speculative-commit, task 3. For a network, scan PoolManager logs backwards from head over WINDOW blocks
(chunked), keep blocks with two or more distinct PoolManager transactions, trace each transaction of such a block
(prestateTracer diffMode) in block order, fold the PoolManager post words and native balance across the block, and
compare them with eth_getStorageAt / eth_getBalance at that block. Also counts blocks where two transactions touch the
same pool id (Swap/ModifyLiquidity/Initialize topic1) and blocks where one tx's PoolManager ERC-6909 / currency words
are touched by a later one. Deterministic: no sampling, newest blocks first, stops at MAXB blocks.
usage: sameblock.py <chainId> <rpc> <window> <chunk> <maxb> <out.json>"""
import json, sys, time, urllib.request, ssl, collections
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
cid, U, WINDOW, CHUNK, MAXB, OUT = int(sys.argv[1]), sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
NETS = json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))
NETS = NETS if isinstance(NETS, list) else NETS['networks']
PM = next(n['poolManager'] for n in NETS if n['chainId'] == cid).lower()
def rpc(m, p, t=120):
    for k in range(4):
        try:
            rq = urllib.request.Request(U, json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), {'content-type': 'application/json', 'user-agent': 'rpc-client'})
            r = json.loads(urllib.request.urlopen(rq, timeout=t, context=CTX).read())
            if 'error' in r: raise RuntimeError(json.dumps(r['error'])[:300])
            return r['result']
        except Exception as e:
            err = str(e)
            if 'not found' in err or 'range' in err.lower(): raise
            time.sleep(1 + k)
    raise RuntimeError(err)
POOLTOPICS = {'0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f', '0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec', '0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438'}
res = {'chainId': cid, 'url': U, 'clientBefore': rpc('web3_clientVersion', []), 'head': None, 'window': WINDOW,
       'blocksWithLogs': 0, 'multiTxBlocks': 0, 'samePoolBlocks': 0, 'sameWordBlocks': 0, 'checkedBlocks': 0,
       'words': 0, 'balances': 0, 'mismatch': [], 'traceErrors': [], 'skipped': 0}
head = int(rpc('eth_blockNumber', []), 16); res['head'] = head
byblk = collections.defaultdict(lambda: collections.defaultdict(list))
hi = head
while hi > head - WINDOW:
    lo = max(hi - CHUNK + 1, head - WINDOW + 1)
    try:
        logs = rpc('eth_getLogs', [{'address': PM, 'fromBlock': hex(lo), 'toBlock': hex(hi)}])
    except Exception as e:
        res['traceErrors'].append(['getLogs', lo, hi, str(e)[:200]]); hi = lo - 1; continue
    for l in logs:
        byblk[int(l['blockNumber'], 16)][(int(l['transactionIndex'], 16), l['transactionHash'])].append(l)
    hi = lo - 1
res['blocksWithLogs'] = len(byblk)
for b in sorted(byblk, reverse=True):
    txs = sorted(byblk[b].items())
    if len(txs) < 2: continue
    res['multiTxBlocks'] += 1
    pools = collections.Counter()
    for (i, h), ls in txs:
        for p in {l['topics'][1] for l in ls if l['topics'][0] in POOLTOPICS and len(l['topics']) > 1}: pools[p] += 1
    same_pool = any(c >= 2 for c in pools.values())
    res['samePoolBlocks'] += same_pool
    if res['checkedBlocks'] >= MAXB: continue
    final = {}; bal = None; touched = collections.Counter(); ok = True
    for (i, h), _ in txs:
        try:
            d = rpc('debug_traceTransaction', [h, {'tracer': 'prestateTracer', 'tracerConfig': {'diffMode': True}}])
        except Exception as e:
            res['traceErrors'].append([b, h, str(e)[:200]]); ok = False; break
        pre = next((v for k, v in d['pre'].items() if k.lower() == PM), {})
        post = next((v for k, v in d['post'].items() if k.lower() == PM), {})
        for s in set(pre.get('storage') or {}) | set(post.get('storage') or {}):
            final[int(s, 16)] = int((post.get('storage') or {}).get(s, '0x0'), 16); touched[int(s, 16)] += 1
        if 'balance' in post: bal = int(post['balance'], 16)
    if not ok: res['skipped'] += 1; continue
    res['sameWordBlocks'] += any(c >= 2 for c in touched.values())
    for s, v in sorted(final.items()):
        got = int(rpc('eth_getStorageAt', [PM, hex(s), hex(b)]), 16); res['words'] += 1
        if got != v: res['mismatch'].append({'block': b, 'slot': hex(s), 'traced': hex(v), 'committed': hex(got), 'txs': [h for (_, h), _ in txs]})
    if bal is not None:
        got = int(rpc('eth_getBalance', [PM, hex(b)]), 16); res['balances'] += 1
        if got != bal: res['mismatch'].append({'block': b, 'balance': True, 'traced': hex(bal), 'committed': hex(got)})
    res['checkedBlocks'] += 1
res['clientAfter'] = rpc('web3_clientVersion', [])
json.dump(res, open(OUT, 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ('traceErrors',)} | {'traceErrors': len(res['traceErrors']), 'mismatch': len(res['mismatch'])}))
