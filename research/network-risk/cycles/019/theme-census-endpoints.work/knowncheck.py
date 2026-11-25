"""Known-block log check. Takes the transaction list an earlier census traced, samples N transactions (seed
'<chainId>-known' in Python's random), finds each one's block with eth_getTransactionByHash, and on every endpoint
compares eth_getLogs for that single block (every PoolManager log, no topic filter) with the PoolManager logs in
the endpoint's own receipts of the block (eth_getBlockReceipts, or eth_getTransactionReceipt per transaction), and
checks that the receipts cover every transaction of the block. Read only.
Usage: knowncheck.py <chainId> <pm> <txlist.json> <N> <out.json> <url> [<url>...]"""
import sys, os, json, time, random
sys.argv, A = sys.argv[:1], sys.argv[1:]
cid, PM, lst, N, out = int(A[0]), A[1].lower(), A[2], int(A[3]), A[4]; URLS = A[5:]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gapcheck2.py')).read()
g = {'__name__': 'g'}; sys.argv = ['x', str(cid), PM, '/dev/null'] + URLS
exec(src.split("R = {'chainId'")[0], g)
rpc, receipts = g['rpc'], g['receipts']
txs = json.load(open(lst)); txs = list(txs) if not isinstance(txs, dict) else list(txs)
rnd = random.Random(f'{cid}-known'); samp = rnd.sample(txs, min(N, len(txs)))
R = {'chainId': cid, 'pm': PM, 'list': lst, 'listSize': len(txs), 'urls': URLS, 'clientVersion': {}, 'rows': []}
for u in URLS:
    try: R['clientVersion'][u + ' start ' + time.strftime('%H:%M:%S', time.gmtime())] = rpc(u, 'web3_clientVersion', [], tries=3)
    except Exception as e: R['clientVersion'][u + ' start'] = 'error ' + str(e)[:80]
def pmc(rc): return sum(1 for r in rc for l in r['logs'] if l['address'].lower() == PM)
for h in samp:
    row = {'tx': h, 'getLogs': {}, 'receipts': {}, 'txCount': {}}
    for u in URLS:
        try:
            t = rpc(u, 'eth_getTransactionByHash', [h], tries=4)
            if t: row['block'] = int(t['blockNumber'], 16); break
        except Exception: pass
    if 'block' not in row: row['error'] = 'no endpoint returned the transaction'; R['rows'].append(row); continue
    bn = row['block']
    for u in URLS:
        try: row['getLogs'][u] = len(rpc(u, 'eth_getLogs', [{'address': PM, 'fromBlock': hex(bn), 'toBlock': hex(bn)}], tries=5))
        except Exception as e: row['getLogs'][u] = 'error ' + str(e)[:100]
        try:
            m, rc, ntx = receipts(u, bn); row['receipts'][u] = pmc(rc); row['txCount'][u] = [len(rc), ntx]
        except Exception as e: row['receipts'][u] = 'error ' + str(e)[:100]
    vals = [v for v in list(row['getLogs'].values()) + list(row['receipts'].values()) if isinstance(v, int)]
    row['agree'] = len(set(vals)) == 1 and all(a == b for a, b in row['txCount'].values())
    R['rows'].append(row)
    if not row['agree']: print('DIFF', json.dumps(row), flush=True)
    json.dump(R, open(out, 'w'), indent=1)
for u in URLS:
    try: R['clientVersion'][u + ' end ' + time.strftime('%H:%M:%S', time.gmtime())] = rpc(u, 'web3_clientVersion', [], tries=3)
    except Exception as e: R['clientVersion'][u + ' end'] = 'error ' + str(e)[:80]
ok = [r for r in R['rows'] if 'error' not in r]
R['summary'] = {'sampled': len(R['rows']), 'located': len(ok), 'agree': sum(1 for r in ok if r['agree']),
                'perEndpointAnswered': {u: sum(1 for r in ok if isinstance(r['getLogs'].get(u), int)) for u in URLS},
                'perEndpointShort': {u: sum(1 for r in ok if isinstance(r['getLogs'].get(u), int) and any(isinstance(v, int) and r['getLogs'][u] < v for v in r['receipts'].values())) for u in URLS}}
json.dump(R, open(out, 'w'), indent=1); print(json.dumps(R['summary']), flush=True)
