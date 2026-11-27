"""L-1058: failed mined transactions sent to the PoolManager or its periphery (PositionManager, Universal Routers)
on Celo and X Layer. Read-only: eth_getBlockReceipts, eth_getTransactionByHash, debug_traceTransaction (callTracer,
Celo on stakely) or eth_call at the parent block (X Layer, which serves no traces).
Usage: python3 failed_scan.py <chainId> <out.json> <nblocks>"""
import sys, json, urllib.request, collections, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff'); import evm
cid, out, n = int(sys.argv[1]), sys.argv[2], int(sys.argv[3])
NET = [x for x in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks' if isinstance(json.load(open('/home/user/v4-core/research/network-risk/state/networks.json')), dict) else None] if x['chainId'] == cid][0] if False else None
nets = json.load(open('/home/user/v4-core/research/network-risk/state/networks.json')); nets = nets if isinstance(nets, list) else nets.get('networks')
NET = [x for x in nets if x['chainId'] == cid][0]
PM = NET['poolManager'].lower()
ENTRY = {v.lower(): k for k, v in NET['contracts'].items() if k not in ('PoolManager', 'Permit2', 'StateView', 'Quoter', 'PositionDescriptor', 'ReservesLens')}
ENTRY[PM] = 'PoolManager'
U = NET['rpc']; TR = 'https://celo-json-rpc.stakely.io' if cid == 42220 else None
def rpc(url, reqs, timeout=90):
    body = json.dumps([{'jsonrpc': '2.0', 'id': i, 'method': m, 'params': p} for i, (m, p) in enumerate(reqs)]).encode()
    for k in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=body, headers={'content-type': 'application/json', 'user-agent': 'curl/8'}), timeout=timeout, context=evm._ctx) as r:
                j = json.load(r)
                if isinstance(j, dict): raise RuntimeError(str(j)[:200])
                return {x['id']: x for x in j}
        except Exception as e:
            time.sleep(2 + k)
    return {}
head = int(rpc(U, [('eth_blockNumber', [])])[0]['result'], 16)
fails = []; scanned = 0; entryTx = 0
STEP = 10 if cid == 196 else 20
for s in range(head - n, head, STEP):
    res = rpc(U, [('eth_getBlockReceipts', [hex(b)]) for b in range(s, min(s + STEP, head))])
    for x in res.values():
        for r in (x.get('result') or []):
            scanned += 1
            to = (r.get('to') or '').lower()
            if to in ENTRY:
                entryTx += 1
                if r['status'] == '0x0': fails.append({'hash': r['transactionHash'], 'block': int(r['blockNumber'], 16), 'to': ENTRY[to], 'gasUsed': int(r['gasUsed'], 16)})
def walk(f, path, acc):
    if (f.get('to') or '').lower() == PM: acc.append({'path': path, 'error': f.get('error'), 'out': (f.get('output') or '')[:10], 'in': (f.get('input') or '')[:10]})
    for i, c in enumerate(f.get('calls') or []): walk(c, path + [i], acc)
for f in fails:
    t = rpc(U, [('eth_getTransactionByHash', [f['hash']])]).get(0, {}).get('result') or {}
    f['gasLimit'] = int(t.get('gas', '0x0'), 16); f['type'] = t.get('type'); f['from'] = t.get('from')
    if TR:
        tr = rpc(TR, [('web3_clientVersion', []), ('debug_traceTransaction', [f['hash'], {'tracer': 'callTracer'}])], 120)
        f['client'] = (tr.get(0) or {}).get('result'); top = (tr.get(1) or {}).get('result')
        if top:
            acc = []; walk(top, [], acc)
            f['topError'] = top.get('error'); f['topOut'] = (top.get('output') or '')[:10]; f['pmFrames'] = acc
        else: f['traceErr'] = str((tr.get(1) or {}).get('error'))[:200]
    else:
        c = {'from': t.get('from'), 'to': t.get('to'), 'data': t.get('input'), 'value': t.get('value'), 'gas': t.get('gas')}
        r = rpc(U, [('eth_call', [c, hex(f['block'] - 1)])]).get(0, {})
        f['callAtParent'] = r.get('result', '')[:10] if 'result' in r else None
        f['callErr'] = (r.get('error') or {}).get('message', '')[:120] if 'error' in r else None
        f['callErrData'] = str((r.get('error') or {}).get('data', ''))[:10] if 'error' in r else None
    f['oogLike'] = f['gasLimit'] > 0 and f['gasUsed'] >= f['gasLimit'] * 0.97
cls = collections.Counter()
for f in fails:
    if 'pmFrames' in f:
        if not f['pmFrames']: k = 'no PoolManager frame'
        elif any(p['error'] for p in f['pmFrames']): k = 'PoolManager frame failed: ' + ','.join(sorted(set((p['error'] or '') + ' ' + p['out'] for p in f['pmFrames'] if p['error'])))
        else: k = 'PoolManager frames succeeded, failure outside'
    elif TR: k = 'no trace'
    else: k = 'eth_call at parent: ' + (('revert ' + (f['callErrData'] or '') + ' ' + (f['callErr'] or '')[:40]) if f.get('callErr') is not None else 'succeeds')
    if f['oogLike']: k += ' [gas used >= 97% of limit]'
    cls[k] += 1
json.dump({'chainId': cid, 'head': head, 'blocks': n, 'receipts': scanned, 'entryTx': entryTx, 'failed': len(fails), 'classes': cls, 'txs': fails}, open(out, 'w'), indent=1)
print(json.dumps({'chainId': cid, 'blocks': n, 'receipts': scanned, 'entryTx': entryTx, 'failed': len(fails), 'classes': cls}, indent=1))
