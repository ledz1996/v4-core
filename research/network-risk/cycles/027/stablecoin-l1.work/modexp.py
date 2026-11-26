"""MODEXP (0x05) vectors with truncated inputs (the path evm2 7c9f3b6 rewrites: input ending before or inside the
modulus) and ordinary ones, compared with the EIP-198 definition (missing bytes read as zero). Read-only eth_call.
Usage: python3 -I modexp.py <out.json> <url>..."""
import sys, os, json, random, urllib.request, ssl
ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
def rpc(url, m, p):
    rq = urllib.request.Request(url, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': m, 'params': p}).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    with urllib.request.urlopen(rq, timeout=60, context=ctx) as r: j = json.load(r)
    if 'error' in j: raise RuntimeError(json.dumps(j['error']))
    return j['result']
def expect(inp):
    pad = lambda b, n: b + b'\0' * max(0, n - len(b))
    h = pad(inp[:96], 96); bl, el, ml = (int.from_bytes(h[i:i + 32], 'big') for i in (0, 32, 64))
    body = inp[96:]
    b = int.from_bytes(pad(body[:bl], bl), 'big') if bl else 0
    e = int.from_bytes(pad(body[bl:bl + el], el), 'big') if el else 0
    m = int.from_bytes(pad(body[bl + el:bl + el + ml], ml), 'big') if ml else 0
    if ml == 0: return b''
    return (pow(b, e, m) if m else 0).to_bytes(ml, 'big')
rnd = random.Random(20261126)
vecs = []
for _ in range(60):
    bl, el, ml = rnd.choice([1, 2, 31, 32, 33, 64]), rnd.choice([0, 1, 2, 32]), rnd.choice([1, 2, 32, 33, 64])
    full = b''.join(x.to_bytes(32, 'big') for x in (bl, el, ml)) + rnd.randbytes(bl + el + ml)
    cut = rnd.choice([96, 96 + bl, 96 + bl + el, 96 + bl + el + 1, 96 + bl + el + ml - 1, len(full), 96 + bl // 2])
    vecs.append(full[:cut])
res = {'vectors': len(vecs), 'byUrl': {}}
for url in sys.argv[2:]:
    bad = []; err = 0
    for v in vecs:
        try:
            got = bytes.fromhex(rpc(url, 'eth_call', [{'to': '0x0000000000000000000000000000000000000005', 'data': '0x' + v.hex(), 'gas': '0x1000000'}, 'latest'])[2:])
            if got != expect(v): bad.append(v.hex())
        except Exception as e:
            err += 1
    res['byUrl'][url] = {'mismatch': len(bad), 'errors': err, 'client': rpc(url, 'web3_clientVersion', []), 'bad': bad[:5]}
    print(url, res['byUrl'][url])
json.dump(res, open(sys.argv[1], 'w'), indent=1)
