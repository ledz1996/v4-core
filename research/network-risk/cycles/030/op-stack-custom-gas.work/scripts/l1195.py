"""Cycle 30 op-stack-custom-gas, lead L-1195: the three getFeeGrowthInside borrow scripts (cycles/028/hyperevm.work/
scripts/borrow.py, with this chain's deployed PoolManager bytecode via PM_FROM) by eth_call, and the 23 scen28
scenarios (cycles/028/theme-monad-native-unentered-blocks.work/scripts/scen28.py, build of this checkout) by
eth_simulateV1, each request sent as one JSON-RPC batch [web3_clientVersion, call, web3_clientVersion] and retried
until both version strings contain the wanted build. Results compared with the pyevm reference. Read-only.
Usage: PM_FROM=<chainId> python3 l1195.py <out.json> <url> <build substring> [borrow|scen|both]"""
import sys, os, json, time, hashlib, urllib.request, ssl
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/028/hyperevm.work/scripts')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/028/theme-monad-native-unentered-blocks.work/scripts')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/029/op-stack-eth.work/scripts')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
def batch(url, m, p, timeout=240):
    body = json.dumps([{'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []}, {'jsonrpc': '2.0', 'id': 2, 'method': m, 'params': p},
                       {'jsonrpc': '2.0', 'id': 3, 'method': 'web3_clientVersion', 'params': []}]).encode()
    req = urllib.request.Request(url, body, {'content-type': 'application/json', 'user-agent': 'curl/8'})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r: return {x['id']: x for x in json.loads(r.read())}
def pinned(url, want, m, p, tries=200):
    seen = {}
    for t in range(tries):
        try: r = batch(url, m, p)
        except Exception as e: seen['transport'] = seen.get('transport', 0) + 1; time.sleep(2); continue
        v1, v3 = str(r[1].get('result')), str(r[3].get('result')); seen[v1] = seen.get(v1, 0) + 1
        if want in v1 and want in v3: return r[2], v1, t + 1, seen
        time.sleep(0.4)
    return None, None, tries, seen
def main():
    out, url, want = sys.argv[1], sys.argv[2], sys.argv[3]; mode = sys.argv[4] if len(sys.argv) > 4 else 'both'
    res = {'url': url, 'build': want, 'pmFrom': os.environ.get('PM_FROM'), 'borrow': {}, 'scen': {}}
    if mode in ('borrow', 'both'):
        import borrow as B
        D = B.D; code = B.P.fetch_code(); ov = D.overrides(code); res['codeSha256'] = hashlib.sha256(code).hexdigest()
        for name, data in B.scripts.items():
            wd = D.world(code); wd.max_steps = 40_000_000
            ok, ret = wd.call(0, D.DRV, 0, data, False, 0); ref = hashlib.sha256(ret).hexdigest()
            rec = D.P.parse(D.unwrap(ret))
            r2, v, n, seen = pinned(url, want, 'eth_call', [{'to': '0x' + D.DRV.to_bytes(20, 'big').hex(), 'data': '0x' + data.hex(), 'gas': hex(29_000_000)}, 'latest', ov])
            e = {'refHash': ref, 'calls': len(rec), 'tries': n, 'seen': seen, 'client': v}
            if r2 is not None:
                if 'result' in r2: e['equal'] = hashlib.sha256(bytes.fromhex(r2['result'][2:])).hexdigest() == ref
                else: e['error'] = str(r2.get('error'))[:300]
            res['borrow'][name] = e; print('borrow', name, {k: e.get(k) for k in ('equal', 'error', 'tries', 'client')}, flush=True)
    if mode in ('scen', 'both'):
        import scen28 as X, scen_rpc as SR
        gas = 25_000_000
        for nm, sc in X.SCEN.items():
            ref_outs, _ = X.ref(sc); blocks = []
            for i, tx in enumerate(sc['txs']):
                b = {'calls': [{'from': '0x%040x' % X.EOA, 'to': '0x%040x' % X.addr(tx['to']), 'data': '0x' + tx['data'], 'gas': hex(gas)}]}
                if i == 0: b['stateOverrides'] = SR.ov_for(sc)
                blocks.append(b)
            r2, v, n, seen = pinned(url, want, 'eth_simulateV1', [{'blockStateCalls': blocks, 'validation': False}, 'latest'])
            e = {'ntx': len(sc['txs']), 'tries': n, 'seen': seen, 'client': v}
            if r2 is not None and 'result' in r2:
                sim = r2['result']
                got = [(c['status'] == '0x1', (c['returnData'] if c['status'] == '0x1' else (c.get('error') or {}).get('data') or '0x')[2:]) for b in sim for c in b['calls']]
                diffs = [i for i, (a, g) in enumerate(zip(ref_outs, got)) if a != g]
                if len(got) != len(ref_outs): diffs.append('count')
                e['diffs'] = diffs; e['bytesCompared'] = sum(len(x[1]) // 2 for x in ref_outs)
            elif r2 is not None: e['error'] = str(r2.get('error'))[:300]
            res['scen'][nm] = e; print('scen', nm, {k: e.get(k) for k in ('diffs', 'error', 'tries', 'client', 'bytesCompared')}, flush=True)
    json.dump(res, open(out, 'w'), indent=1)
if __name__ == '__main__': main()
