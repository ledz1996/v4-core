"""Rerun, in smaller pieces, the sweep ranges of halt.py that exceeded the eth_call gas cap (Tempo and MegaETH,
where the successful attempt needs more gas). Read-only. Usage: python3 halt_fix.py <halt_all.json> <out.json>"""
import sys, json
sys.path.insert(0, '.')
import halt as H
R = json.load(open(sys.argv[1])); out = {}
for r in R:
    errs = [s for s in r['sweep'] if 'err' in s]
    if not errs: continue
    n = [x for x in H.nets if x['chainId'] == r['chain']][0]; url = n['rpc']; pm = n['poolManager']
    gs = r['successGas'][str(1)] if isinstance(list(r['successGas'].keys())[0], str) else r['successGas'][1]
    per = max(10, 22_000_000 // (gs + 30_000)); recs = []
    for e in errs:
        a, b, st = e['range']; x = a
        while x < b:
            y = min(b, x + per * st)
            try:
                o = H.words(H.call(url, '0x' + H.sel('sweep(address,uint256,uint256,uint256,uint256)') + H.addr(pm) + H.w(e['variant']) + H.w(x) + H.w(y) + H.w(st), 29_000_000))
                recs.append({'variant': e['variant'], 'range': [x, y, st], 'attempts': o[0], 'fails': o[1], 'leaks': o[2], 'successGas': None if o[4] == 2**256 - 1 else o[4]})
            except Exception as ex: recs.append({'variant': e['variant'], 'range': [x, y, st], 'err': str(ex)[:160]})
            x = y
    out[r['chain']] = {'records': recs, 'attempts': sum(q.get('attempts', 0) for q in recs), 'fails': sum(q.get('fails', 0) for q in recs),
                       'leaks': sum(q.get('leaks', 0) for q in recs), 'errors': sum('err' in q for q in recs),
                       'successes': [q['successGas'] for q in recs if q.get('successGas')]}
    print(r['chain'], {k: v for k, v in out[r['chain']].items() if k != 'records'}, flush=True)
json.dump(out, open(sys.argv[2], 'w'), indent=1)
