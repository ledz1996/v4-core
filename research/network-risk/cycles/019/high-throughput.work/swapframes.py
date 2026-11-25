"""L-836: list the PoolManager swap frames of one mined transaction (callTracer), with the pool key decoded from the
input, the output delta, and the calls the swap frame itself made (hook calls, by selector). Read-only RPC.
usage: python3 swapframes.py <rpc> <txhash> <poolManager>"""
import json, sys, urllib.request
U, H, PM = sys.argv[1], sys.argv[2], sys.argv[3].lower()


def rpc(m, p):
    rq = urllib.request.Request(U, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(),
                                headers={'content-type': 'application/json', 'user-agent': 'curl/8.5.0'})
    r = json.load(urllib.request.urlopen(rq, timeout=120))
    if 'error' in r: raise Exception(r['error'])
    return r['result']


t = rpc('debug_traceTransaction', [H, {'tracer': 'callTracer'}])
out = []; idx = [0]


def walk(n):
    if (n.get('to') or '').lower() == PM and n.get('type') in ('CALL', 'STATICCALL'):
        i = idx[0]; idx[0] += 1
        inp = (n.get('input') or '0x')[2:]
        if inp[:8] == 'f3cd914c':
            w = [inp[8 + 64 * k: 8 + 64 * (k + 1)] for k in range(8)]
            out.append({'pmIndex': i, 'currency0': '0x' + w[0][24:], 'currency1': '0x' + w[1][24:], 'fee': int(w[2], 16), 'tickSpacing': int(w[3], 16),
                        'hooks': '0x' + w[4][24:], 'zeroForOne': int(w[5], 16), 'amountSpecified': w[6], 'output': (n.get('output') or '')[:130],
                        'subcalls': [((c.get('to') or ''), (c.get('input') or '')[:10], c.get('type'), 'error' not in c) for c in n.get('calls', []) or []]})
    for c in n.get('calls', []) or []: walk(c)


walk(t)
print(json.dumps({'tx': H, 'swaps': out}, indent=1))
