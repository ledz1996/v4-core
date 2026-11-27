"""L-1058 on Celo: every failed receipt in a block window, traced with callTracer on stakely.io (which serves
debug_traceTransaction), kept when a frame enters the PoolManager. Read-only.
Usage: python3 failed_any.py <out.json> <nblocks> <maxTraces>"""
import sys, json, urllib.request, collections, time, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff'); import evm
PM = '0x288dc841a52fca2707c6947b3a777c5e56cd87bc'; U = 'https://forno.celo.org'; TR = 'https://celo-json-rpc.stakely.io'
def rpc(url, reqs, timeout=120):
    body = json.dumps([{'jsonrpc': '2.0', 'id': i, 'method': m, 'params': p} for i, (m, p) in enumerate(reqs)]).encode()
    for k in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=body, headers={'content-type': 'application/json', 'user-agent': 'curl/8'}), timeout=timeout, context=evm._ctx) as r:
                j = json.load(r)
                if isinstance(j, dict): raise RuntimeError(str(j)[:200])
                return {x['id']: x for x in j}
        except Exception: time.sleep(2 + k)
    return {}
out, n, mx = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
head = int(rpc(U, [('eth_blockNumber', [])])[0]['result'], 16)
fails = []
for s in range(head - n, head, 20):
    for x in rpc(U, [('eth_getBlockReceipts', [hex(b)]) for b in range(s, min(s + 20, head))]).values():
        for r in (x.get('result') or []):
            if r['status'] == '0x0': fails.append((r['transactionHash'], int(r['blockNumber'], 16), int(r['gasUsed'], 16), (r.get('to') or '')))
def walk(f, path, acc):
    if (f.get('to') or '').lower() == PM: acc.append({'path': path, 'type': f.get('type'), 'error': f.get('error'), 'out': (f.get('output') or '')[:10], 'in': (f.get('input') or '')[:10], 'gas': f.get('gas'), 'gasUsed': f.get('gasUsed')})
    for i, c in enumerate(f.get('calls') or []): walk(c, path + [i], acc)
def tr(item):
    h, bn, gu, to = item
    t = rpc(TR, [('web3_clientVersion', []), ('debug_traceTransaction', [h, {'tracer': 'callTracer'}]), ('eth_getTransactionByHash', [h])])
    top = (t.get(1) or {}).get('result'); tx = (t.get(2) or {}).get('result') or {}
    rec = {'hash': h, 'block': bn, 'gasUsed': gu, 'gasLimit': int(tx.get('gas', '0x0'), 16), 'to': to, 'client': (t.get(0) or {}).get('result')}
    if not top: rec['traceErr'] = str((t.get(1) or {}).get('error'))[:150]; return rec
    acc = []; walk(top, [], acc); rec['pm'] = acc; rec['topError'] = top.get('error'); rec['topOut'] = (top.get('output') or '')[:10]
    return rec
sample = fails[-mx:]
with cf.ThreadPoolExecutor(4) as ex: recs = list(ex.map(tr, sample))
pmrecs = [r for r in recs if r.get('pm')]
cls = collections.Counter()
for r in pmrecs:
    errs = [p for p in r['pm'] if p['error']]
    k = ('PoolManager frame failed: ' + ','.join(sorted(set(p['error'] + ' ' + p['out'] for p in errs)))) if errs else 'PoolManager frames returned, failure outside'
    if r['gasLimit'] and r['gasUsed'] >= 0.97 * r['gasLimit']: k += ' [gas used >= 97% of limit]'
    cls[k] += 1
res = {'head': head, 'blocks': n, 'failedReceipts': len(fails), 'traced': len(recs), 'traceErrors': sum(1 for r in recs if 'traceErr' in r), 'enterPoolManager': len(pmrecs), 'classes': cls, 'clients': collections.Counter(r.get('client') for r in recs), 'pmTxs': pmrecs}
json.dump(res, open(out, 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'pmTxs'}, indent=1))
