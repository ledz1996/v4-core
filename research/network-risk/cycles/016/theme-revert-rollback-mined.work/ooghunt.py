"""Read-only. In the call trees of the scan hits, list errors of frames below a PoolManager frame (hook, token,
callback) and the outcome of the enclosing PoolManager frame. Usage: python3 ooghunt.py <out.json> chain:url ..."""
import sys, json
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff'); sys.path.insert(0, '.')
import scan as S
nets = {n['chainId']: n for n in json.load(open('/home/user/v4-core/research/network-risk/state/networks.json'))['networks']}
res = {}
for arg in sys.argv[2:]:
    c, u = arg.split(':', 1); c = int(c); pm = nets[c]['poolManager'].lower(); rows = []
    for h in json.load(open(f'raw/scan_{c}.json'))['hits']:
        t = S.R(u, 'debug_traceTransaction', [h['tx'], {'tracer': 'callTracer'}])
        def walk(n, pmf):
            to = (n.get('to') or '').lower()
            if pmf is not None and 'error' in n: rows.append({'tx': h['tx'], 'pmSel': pmf[0], 'pmErr': pmf[1], 'to': to, 'sel': n.get('input', '')[:10], 'err': n['error']})
            if to == pm: pmf = (S.SEL.get(n.get('input', '')[2:10], ''), n.get('error'))
            for k in n.get('calls', []) or []: walk(k, pmf)
        walk(t, None)
    kinds = {}
    for r in rows: kinds[r['err'] + ' -> PM ' + str(r['pmErr'])] = kinds.get(r['err'] + ' -> PM ' + str(r['pmErr']), 0) + 1
    res[c] = {'rows': rows[:40], 'kinds': kinds}; print(c, kinds)
json.dump(res, open(sys.argv[1], 'w'), indent=1)
