"""Task 3: the next simulated transaction. eth_simulateV1 with two calls in one block, both from E to E under the same
overrides as live.py: call 1 runs the CallFrom path (mode 1) at a driver gas X, call 2 runs the calibration target (mode 2)
and so only reads isOperator(E, BEEF) and the synced currency, lock and count words. X values: ample (a), child revert (b),
and one inside the measured completion out-of-gas window (c) and one inside the child-halt band, for N=65536.
usage: python3 -I simnext.py <out.json> <url> <X_c> <X_halt>"""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sv = list(sys.argv); sys.argv = ['live.py', 'none']; import live as L; sys.argv = sv
url = sys.argv[2]; Xc = int(sys.argv[3]); Xh = int(sys.argv[4]); N = 65536
def sim(X, rv):
    c1 = L.tx(1, X, N, rv); c2 = L.tx(2, 100000, 0, 0)
    for c in (c1, c2): c['gas'] = hex(8_000_000); c['maxFeePerGas'] = '0x0'; c['maxPriorityFeePerGas'] = '0x0'
    req = [{'blockStateCalls': [{'stateOverrides': L.OVR, 'calls': [c1, c2]}], 'validation': False}, 'latest']
    r = L.rpc(url, 'eth_simulateV1', req, 180)
    if 'result' not in r: return {'err': json.dumps(r)[:400]}
    calls = r['result'][0]['calls']; out = []
    for c in calls:
        d = {'status': c.get('status'), 'gasUsed': c.get('gasUsed'), 'logs': len(c.get('logs', []))}
        if c.get('returnData') and len(c['returnData']) >= 2 + 0x200:
            p, rd = L.parse(c['returnData']); d.update(p)
            if p['ok'] and p['rds']: d['entrySuccess'] = L.entry_success(rd)
        else: d['ret'] = c.get('returnData', '')[:200]
        out.append(d)
    return out
res = {'t': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'url': url, 'before': L.ver(url), 'N': N, 'cases': {}}
for name, X, rv in (('a_ample', 5_000_000, 0), ('b_child_revert', 5_000_000, 1), ('c_completion_oog', Xc, 0), ('halt_band', Xh, 0)):
    res['cases'][name] = {'X': X, 'calls': sim(X, rv)}
    print(name, json.dumps(res['cases'][name])[:700], flush=True)
res['after'] = L.ver(url)
json.dump(res, open(sys.argv[1], 'w'), indent=1)
