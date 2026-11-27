"""L-1149: does any eth_simulateV1 or eth_call response carry a build-specific shape? Sends one simulate request
(one call that returns the GAS word, one call that halts on purpose) to single-build endpoints and repeatedly to the
Pocket gateway, and records a shape signature per response. Read-only. Usage: python3 simshape.py <out.json> <n>"""
import sys, json, urllib.request, ssl, hashlib, collections
ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
def post(url, body):
    req = urllib.request.Request(url, json.dumps(body).encode(), {'content-type': 'application/json', 'user-agent': 'curl/8'})
    try:
        with urllib.request.urlopen(req, timeout=60, context=ctx) as r: return json.loads(r.read())
    except urllib.error.HTTPError as e: return {'http': e.code, 'body': e.read()[:300].decode('latin1')}
    except Exception as e: return {'exc': repr(e)[:200]}
A = '0x00000000000000000000000000000000000c0de1'
CODE_GAS = '0x5a60005260206000f3'          # GAS PUSH0.. MSTORE RETURN 32
CODE_HALT = '0x6001630fffffffff6000f3'.replace('6000f3', 'f3')  # RETURN at offset 2^36-1 len 1: memory limit halt
def sig(x):
    def shape(o):
        if isinstance(o, dict): return {k: shape(v) for k, v in sorted(o.items()) if k not in ('id',)}
        if isinstance(o, list): return [shape(v) for v in o[:3]]
        return type(o).__name__
    return x
SIM = {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_simulateV1', 'params': [{'blockStateCalls': [{'stateOverrides': {A: {'code': CODE_GAS}, '0x00000000000000000000000000000000000c0de2': {'code': CODE_HALT}},
       'calls': [{'to': A, 'data': '0x'}, {'to': '0x00000000000000000000000000000000000c0de2', 'data': '0x'}]}]}, 'latest']}
CALLH = {'jsonrpc': '2.0', 'id': 2, 'method': 'eth_call', 'params': [{'to': '0x00000000000000000000000000000000000c0de2', 'data': '0x'}, 'latest', {'0x00000000000000000000000000000000000c0de2': {'code': CODE_HALT}}]}
CALLG = {'jsonrpc': '2.0', 'id': 3, 'method': 'eth_call', 'params': [{'to': A, 'data': '0x'}, 'latest', {A: {'code': CODE_GAS}}]}
CV = {'jsonrpc': '2.0', 'id': 4, 'method': 'web3_clientVersion', 'params': []}
def summarize(r):
    out = {}
    for x in (r if isinstance(r, list) else [r]):
        i = x.get('id')
        if i == 1 and 'result' in x:
            blk = x['result'][0]; calls = blk.get('calls', [])
            out['simBlockKeys'] = sorted(blk.keys()); out['simCalls'] = [{k: (v if k in ('status', 'error', 'returnData') else '...') for k, v in c.items()} for c in calls]
        elif i == 1: out['simError'] = x.get('error')
        elif i == 2: out['haltCall'] = x.get('error') or x.get('result')
        elif i == 3: out['gasWord'] = x.get('result') or x.get('error')
        elif i == 4: out['cv'] = x.get('result')
        else: out['raw'] = str(x)[:300]
    return out
def main():
    out, n = sys.argv[1], int(sys.argv[2]); res = {}
    singles = {'publicnode reth v2.11.0': 'https://ethereum-rpc.publicnode.com', 'blastapi reth v2.10.0': 'https://eth-mainnet.public.blastapi.io',
               'blockpi geth v1.17.9': 'https://ethereum.public.blockpi.network/v1/rpc/public', 'mevblocker geth v1.17.10': 'https://rpc.mevblocker.io'}
    for k, u in singles.items():
        res[k] = [summarize(post(u, [CV, SIM, CALLH, CALLG])), summarize(post(u, [CV, SIM, CALLH, CALLG]))]
        print(k, json.dumps(res[k][0])[:900], flush=True)
    res['pocket-separate'] = []
    for i in range(n):
        s = {}
        for b in (CV, SIM, CALLH, CALLG): s.update(summarize(post('https://eth.api.pocket.network', b)))
        res['pocket-separate'].append(s)
    c = collections.Counter(json.dumps({k: v for k, v in s.items() if k != 'cv'}, sort_keys=True) for s in res['pocket-separate'])
    res['pocketShapes'] = [[v, json.loads(k)] for k, v in c.most_common()]
    res['pocketCv'] = collections.Counter(s.get('cv') for s in res['pocket-separate'])
    for v, k in res['pocketShapes']: print('POCKET', v, json.dumps(k)[:900])
    print(res['pocketCv'])
    json.dump(res, open(out, 'w'), indent=1)
main()
