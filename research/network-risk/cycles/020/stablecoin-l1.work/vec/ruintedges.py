# Cycle 20, stablecoin-l1: vectors aimed at the ruint 1.21.1 branches read this cycle (add_mod fast path,
# mul_mod 2^256-1 end-around carry, div_nx1 single-limb x86 asm path and its reciprocal, div_nx2, knuth with
# spare limb, the 1.21.0 mul_mod fault shape), run as creation code through eth_call (read-only) on
# Tempo and Arc, and on Tempo also through eth_simulateV1 at a block time after T14.
# Usage: python3 -I ruintedges.py <out.json>
import json, random, sys, urllib.request, ssl, os
M = (1 << 256) - 1
RPC = {4217: 'https://rpc.mainnet.tempo.xyz', 5042: 'https://rpc.mainnet.arc.io'}
T14 = 1796742000 + 3600
ctx = ssl.create_default_context(cafile=os.environ.get('SSL_CERT_FILE') or '/root/.ccr/ca-bundle.crt')
def rpc(url, method, params):
    req = urllib.request.Request(url, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    with urllib.request.urlopen(req, timeout=120, context=ctx) as r: j = json.load(r)
    if 'error' in j: raise RuntimeError(str(j['error'])[:300])
    return j['result']
OPS = {'DIV': 0x04, 'MOD': 0x06, 'ADDMOD': 0x08, 'MULMOD': 0x09, 'SDIV': 0x05, 'SMOD': 0x07, 'LT': 0x10, 'GT': 0x11}
def s(x): return x - (1 << 256) if x >> 255 else x
def ref(op, a, b, n):
    if op == 'DIV': return 0 if b == 0 else a // b
    if op == 'MOD': return 0 if b == 0 else a % b
    if op == 'ADDMOD': return 0 if n == 0 else (a + b) % n
    if op == 'MULMOD': return 0 if n == 0 else (a * b) % n
    if op == 'SDIV':
        if b == 0: return 0
        q = abs(s(a)) // abs(s(b)); q = -q if (s(a) < 0) != (s(b) < 0) else q; return q & M
    if op == 'SMOD':
        if b == 0: return 0
        r = abs(s(a)) % abs(s(b)); return (-r if s(a) < 0 else r) & M
    if op == 'LT': return int(a < b)
    if op == 'GT': return int(a > b)
R = random.Random(20020)
def limb(): return R.choice([0, 1, 2, (1 << 64) - 1, (1 << 64) - 2, 1 << 63, (1 << 63) - 1, (1 << 63) + 1, R.getrandbits(64), R.getrandbits(64), R.getrandbits(R.randint(1, 64))])
def word(nl=None):
    nl = R.randint(0, 4) if nl is None else nl
    return sum(limb() << (64 * i) for i in range(nl)) & M
vecs = []
for _ in range(1500):  # add_mod fast path: high limbs of a and b at most that of n, operands in [0, 2n)
    n = word(4) | (1 << 192); hi = n >> 192
    a = (R.randint(0, hi) << 192) | R.getrandbits(192); b = (R.randint(0, hi) << 192) | R.getrandbits(192)
    if R.random() < 0.3: a = (hi << 192) | R.getrandbits(192)
    if R.random() < 0.2: a, b = n, n - 1
    vecs.append(('ADDMOD', a & M, b & M, n))
for _ in range(1500):  # mul_mod with n = 2^256 - 1, including products whose folded sum is exactly n or carries
    a = word(); b = word()
    if R.random() < 0.3: a = M; b = R.choice([M, 1, 2, word()])
    if R.random() < 0.2:  # make lo + hi land on M: a*b = k*(2^256-1) for small k
        k = R.randint(1, 1 << 64); a = M; b = k
    vecs.append(('MULMOD', a, b, M))
for _ in range(2000):  # single-limb divisors: normalized and not, numerator top limb below, equal and above
    d = R.choice([1, 2, 3, (1 << 64) - 1, 1 << 63, (1 << 63) + 1, R.getrandbits(64) | 1, R.getrandbits(R.randint(1, 63)) | 1])
    a = word(R.randint(1, 4))
    if R.random() < 0.3: a = (a & ~((1 << 64) - 1 << 192 * 0)) | 0; a = (d - 1) << 192 | R.getrandbits(192)
    vecs.append((R.choice(['DIV', 'MOD', 'SDIV', 'SMOD']), a & M, d, 0))
for _ in range(2000):  # two and three limb divisors (div_nx2 and knuth paths)
    nl = R.choice([2, 3]); d = word(nl) | (1 << (64 * (nl - 1))); a = word(4)
    if R.random() < 0.3: a = (d << (64 * (4 - nl))) - R.randint(0, 3)
    vecs.append((R.choice(['DIV', 'MOD']), a & M, d & M, 0))
for _ in range(1500):  # 1.21.0 mul_mod fault shape and mul_mod fast path with all high limbs nonzero
    a = word(4) | (1 << 192); b = word(4) | (1 << 192); hi = (a * b) >> 256
    n = ((hi >> 128) << 128) | R.getrandbits(128)
    if n >> 192 == 0: n |= 1 << 192
    vecs.append(('MULMOD', a, b, n))
for _ in range(500):  # comparisons on words that differ in one limb only
    a = word(4); l = R.randint(0, 3); b = a ^ (R.choice([1, 1 << 63, R.getrandbits(64)]) << (64 * l))
    vecs.append((R.choice(['LT', 'GT']), a, b & M, 0))
def code(batch):
    c = bytearray()
    for i, (op, a, b, n) in enumerate(batch):
        if op in ('ADDMOD', 'MULMOD'): c += b'\x7f' + n.to_bytes(32, 'big')
        c += b'\x7f' + b.to_bytes(32, 'big') + b'\x7f' + a.to_bytes(32, 'big') + bytes([OPS[op]]) + b'\x61' + (32 * i).to_bytes(2, 'big') + b'\x52'
    c += b'\x61' + (32 * len(batch)).to_bytes(2, 'big') + b'\x60\x00\xf3'
    return '0x' + c.hex()
def call(cid, data, t14):
    if not t14: return rpc(RPC[cid], 'eth_call', [{'data': data, 'gas': hex(20_000_000)}, 'latest'])
    r = rpc(RPC[cid], 'eth_simulateV1', [{'blockStateCalls': [{'calls': [{'data': data, 'gas': hex(20_000_000)}], 'blockOverrides': {'time': hex(T14)}}], 'validation': False}, 'latest'])
    assert int(r[0]['timestamp'], 16) == T14; c = r[0]['calls'][0]; assert c['status'] == '0x1', c; return c['returnData']
out = {'vectors': len(vecs), 'byOp': {}, 'runs': {}}
for v in vecs: out['byOp'][v[0]] = out['byOp'].get(v[0], 0) + 1
planted = 0
for cid, t14 in ((4217, False), (4217, True), (5042, False)):
    bad = []; ran = 0
    for k in range(0, len(vecs), 150):
        batch = vecs[k:k + 150]; ret = bytes.fromhex(call(cid, code(batch), t14)[2:])
        for i, (op, a, b, n) in enumerate(batch):
            got = int.from_bytes(ret[32 * i:32 * i + 32], 'big'); ran += 1
            if got != ref(op, a, b, n): bad.append([op, hex(a), hex(b), hex(n), hex(got)])
    out['runs'][f'{cid}{"-T14" if t14 else ""}'] = {'ran': ran, 'mismatches': len(bad), 'first': bad[:5]}
    print(cid, 'T14' if t14 else 'now', 'ran', ran, 'mismatches', len(bad), flush=True)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
