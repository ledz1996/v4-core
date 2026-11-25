"""Cycle 21 copy of cycle 17 pushdup.py, endpoints narrowed to the geth v1.17.10 go1.27.3 backend.
Vectors for the geth v1.17.9 generated dispatch (PUSH1..PUSH32 by SetBytesN) and v1.17.10 merged DUP/SWAP cases.
Each program runs by eth_call with a code override and returns its whole stack; the expected words are computed here."""
import json, sys, urllib.request, random
EPS = {'geth v1.17.10 go1.27.3 (nownodes)': 'https://public-eth.nownodes.io'}
A = '0x00000000000000000000000000000000000c0de2'
random.seed(17)
def ret_stack(depth):  # store `depth` stack words at 0,32,... (top first) and return them
    c = b''
    for k in range(depth):
        c += bytes([0x61]) + (32 * k).to_bytes(2, 'big') + b'\x52'  # PUSH2 off MSTORE  (value is top)
    c += bytes([0x61]) + (32 * depth).to_bytes(2, 'big') + b'\x5f\xf3'
    return c
progs = []
for n in range(1, 33):
    for pat in (b'\xff' * n, bytes(range(1, n + 1)), bytes([random.randrange(256) for _ in range(n)]), b'\x00' * (n - 1) + b'\x01', b'\x80' + b'\x00' * (n - 1)):
        code = bytes([0x5f + n]) + pat + ret_stack(1)
        progs.append(('PUSH%d' % n, code, [int.from_bytes(pat, 'big')]))
base = [random.getrandbits(256) for _ in range(17)]
pushes = b''.join(b'\x7f' + v.to_bytes(32, 'big') for v in base)  # base[16] is top
for n in range(1, 17):
    st = base[:]  # bottom..top
    st.append(st[-n]); code = pushes + bytes([0x7f + n]) + ret_stack(18)
    progs.append(('DUP%d' % n, code, list(reversed(st))))
for n in range(1, 17):
    st = base[:]; st[-1], st[-1 - n] = st[-1 - n], st[-1]
    code = pushes + bytes([0x8f + n]) + ret_stack(17)
    progs.append(('SWAP%d' % n, code, list(reversed(st))))
# chains: random DUP/SWAP sequences
for t in range(40):
    st = base[:]; code = pushes
    for _ in range(30):
        if random.random() < 0.5 and len(st) < 40:
            n = random.randint(1, 16); st.append(st[-n]); code += bytes([0x7f + n])
        else:
            n = random.randint(1, 16); st[-1], st[-1 - n] = st[-1 - n], st[-1]; code += bytes([0x8f + n])
    code += ret_stack(len(st)); progs.append(('CHAIN%d' % t, code, list(reversed(st))))
def call(url, code):
    body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_call', 'params': [{'to': A, 'gas': '0x1000000'}, 'latest', {A: {'code': '0x' + code.hex()}}]}).encode()
    r = json.load(urllib.request.urlopen(urllib.request.Request(url, body, {'content-type': 'application/json', 'user-agent': 'review-client'}), timeout=30))
    return r.get('result'), r.get('error')
res = {}
for name, url in EPS.items():
    ok = bad = err = 0; bads = []
    for lab, code, exp in progs:
        try:
            r, e = call(url, code)
        except Exception as ex:
            err += 1; continue
        if r is None: err += 1; continue
        b = bytes.fromhex(r[2:]); got = [int.from_bytes(b[32 * i:32 * i + 32], 'big') for i in range(len(b) // 32)]
        if got == exp: ok += 1
        else: bad += 1; bads.append(lab)
    res[name] = {'rpc': url, 'programs': len(progs), 'match': ok, 'mismatch': bad, 'errors': err, 'bad': bads[:20]}
    print(name, res[name])
json.dump(res, open(sys.argv[1], 'w'), indent=1)
