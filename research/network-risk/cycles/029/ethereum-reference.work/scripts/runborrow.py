"""Cycle 29 ethereum-reference, lead L-1180 part 1: the three getFeeGrowthInside borrow scripts of
cycles/028/hyperevm.work/scripts/borrow.py, with the Ethereum PoolManager bytecode (PM_FROM=1), against the
reference interpreter and each Ethereum endpoint by eth_call with state overrides. Each eth_call is sent in one
JSON-RPC batch with web3_clientVersion before and after it, so a backend that routes the batch as one names itself.
Errors per endpoint are recorded instead of stopping. Usage: python3 runborrow.py <out.json> <url> [...]"""
import sys, os, json, hashlib, urllib.request, ssl
os.environ.setdefault('PM_FROM', '1')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/028/hyperevm.work/scripts')
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import borrow as B
D = B.D
ctx = ssl.create_default_context(cafile=os.environ.get('SSL_CERT_FILE') or '/root/.ccr/ca-bundle.crt')
def batch(url, calls, timeout=180):
    body = json.dumps([{'jsonrpc': '2.0', 'id': i, 'method': m, 'params': p} for i, (m, p) in enumerate(calls)]).encode()
    req = urllib.request.Request(url, body, {'content-type': 'application/json', 'user-agent': 'curl/8'})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        res = json.loads(r.read())
    return {x['id']: x for x in res}
def main():
    out, urls = sys.argv[1], sys.argv[2:]
    code = B.P.fetch_code(); ov = B.D.overrides(code)
    res = {'codeSha256': hashlib.sha256(code).hexdigest(), 'scripts': {}, 'urls': {}}
    for name, data in B.scripts.items():
        wd = D.world(code); wd.max_steps = 40_000_000
        ok, ret = wd.call(0, D.DRV, 0, data, False, 0)
        rec = D.P.parse(D.unwrap(ret)); ref = hashlib.sha256(ret).hexdigest()
        res['scripts'][name] = {'refHash': ref, 'calls': len(rec), 'failed': [i for i, (k, _) in enumerate(rec) if not k]}
        print(name, 'reference calls', len(rec), flush=True)
        for url in urls:
            e = {}
            try:
                r = batch(url, [('web3_clientVersion', []), ('eth_call', [{'to': '0x' + D.DRV.to_bytes(20, 'big').hex(), 'data': '0x' + data.hex(), 'gas': hex(29_000_000)}, 'latest', ov]), ('web3_clientVersion', [])])
                e['before'] = r[0].get('result'); e['after'] = r[2].get('result')
                if 'result' in r[1]:
                    h = hashlib.sha256(bytes.fromhex(r[1]['result'][2:])).hexdigest(); e['equal'] = h == ref; e['retLen'] = len(r[1]['result']) // 2 - 1
                else: e['error'] = str(r[1].get('error'))[:300]
            except Exception as x: e['error'] = repr(x)[:300]
            res['urls'].setdefault(url, {})[name] = e
            print('  ', url, e, flush=True)
    json.dump(res, open(out, 'w'), indent=1)
if __name__ == '__main__': main()
