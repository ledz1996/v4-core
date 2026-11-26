"""Cycle 26, established-l1. Long MULMOD sequences with alternating and repeating moduli
inside one frame, with a nested STATICCALL frame that uses another modulus between two
parent MULMODs, for interpreters that keep MULMOD state across instructions (bor's
mulmod_memo.go on v2.12.0-beta and develop). Read-only: one eth_call per batch with
state overrides, nothing deployed, no transaction.

Record (160 bytes): kind, a, b, m, m2. Five words out per record:
  w1 = mulmod(a, b, 2^256-1)          (FullMath.sol:24 shape)
  w2 = mulmod(a, b, m)                (FullMath.sol:48 shape)
  w3 = mulmod(a, b, m2), in a child frame if kind&1 (the child first runs mulmod(5,3,2^256-1))
  w4 = mulmod(a^b, b, m)              (same modulus as w2, other operands)
  w5 = mulmod(m-1, m-1, m)
Usage: python3 -I memoseq.py <out.json> <seed> <nrecords> <label=url> ...
Each batch is sent as a JSON-RPC batch [web3_clientVersion, eth_call, web3_clientVersion].
"""
import sys, os, json, random, urllib.request, ssl, time
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import assemble, MASK

A = '0x00000000000000000000000000000000000c0de5'
B = '0x00000000000000000000000000000000000c0de6'
OUT = 0x1000
CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')


def ld(k, depth):
    return [f'DUP{depth}', ('PUSH', 32 * k), 'ADD', 'CALLDATALOAD']


STORE = ['DUP3', 'MSTORE', 'SWAP1', ('PUSH', 32), 'ADD', 'SWAP1']  # [w, off, optr] -> [off, optr+32]


def code_a():
    p = [('PUSH', OUT), ('PUSH', 0)]
    p += [('LABEL', 'loop'), 'DUP1', 'CALLDATASIZE', 'GT', 'ISZERO', ('REF', 'done'), 'JUMPI']
    p += ['PUSH0', 'NOT'] + ld(2, 2) + ld(1, 3) + ['MULMOD'] + STORE                      # w1
    p += ld(3, 1) + ld(2, 2) + ld(1, 3) + ['MULMOD'] + STORE                               # w2
    p += ld(0, 1) + [('PUSH', 1), 'AND', ('REF', 'child'), 'JUMPI']                        # w3
    p += ld(4, 1) + ld(1, 2) + ld(2, 3) + ['MULMOD'] + STORE + [('REF', 'join'), 'JUMP']
    p += [('LABEL', 'child')] + ld(1, 1) + ['PUSH0', 'MSTORE'] + ld(2, 1) + [('PUSH', 32), 'MSTORE'] + ld(4, 1) + [('PUSH', 64), 'MSTORE']
    p += [('PUSH', 32), 'PUSH0', ('PUSH', 96), 'PUSH0', ('PUSH', int(B, 16)), 'GAS', 'STATICCALL', 'POP', 'PUSH0', 'MLOAD'] + STORE
    p += [('LABEL', 'join')]
    p += ld(3, 1) + ld(2, 2) + ld(1, 3) + ld(2, 4) + ['XOR', 'MULMOD'] + STORE              # w4
    p += ld(3, 1) + [('PUSH', 1), 'DUP2', 'SUB', 'DUP1', 'MULMOD'] + STORE                 # w5
    p += [('PUSH', 160), 'ADD', ('REF', 'loop'), 'JUMP']
    p += [('LABEL', 'done'), 'POP', ('PUSH', OUT), 'SWAP1', 'SUB', ('PUSH', OUT), 'RETURN']
    return assemble(p)


def code_b():
    p = ['PUSH0', 'NOT', ('PUSH', 3), ('PUSH', 5), 'MULMOD', 'POP',
         ('PUSH', 64), 'CALLDATALOAD', ('PUSH', 32), 'CALLDATALOAD', 'PUSH0', 'CALLDATALOAD', 'MULMOD',
         'PUSH0', 'MSTORE', ('PUSH', 32), 'PUSH0', 'RETURN']
    return assemble(p)


def mm(a, b, m):
    return (a * b) % m if m else 0


def expected(r):
    k, a, b, m, m2 = r
    return [mm(a, b, MASK), mm(a, b, m), mm(a, b, m2), mm(a ^ b, b, m), mm((m - 1) & MASK, (m - 1) & MASK, m)]


def records(seed, n):
    rnd = random.Random(seed)
    full = lambda: (rnd.getrandbits(64) | 1 << 63 >> rnd.randrange(0, 63)) << 192 | rnd.getrandbits(192)
    narrow = lambda: rnd.getrandbits(rnd.choice((1, 64, 96, 128, 160, 191, 192))) or 7
    fixed = [MASK, MASK - 1, 1 << 192, (1 << 192) + 1, 1 << 255, (1 << 255) + 1, (1 << 256) - (1 << 192), 0, 1, 2,
             1 << 96, 1 << 128, (1 << 160) - 1, 0x30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000001]
    def op():
        c = rnd.random()
        if c < 0.08: return 0
        if c < 0.16: return MASK - rnd.getrandbits(rnd.choice((1, 8, 64, 130)))
        if c < 0.24: return rnd.getrandbits(rnd.choice((64, 96, 128, 160, 192)))
        return rnd.getrandbits(256)
    def near(m):  # same modulus except one limb
        l = rnd.randrange(4)
        return m ^ (1 << (64 * l + rnd.randrange(64))) if m else 1 << 200
    def ruint_shape(m):  # a, b whose high half shares the top 128 bits of m
        while True:
            a = rnd.getrandbits(256) | 1 << 255
            hi = m >> 128 << 128 | rnd.getrandbits(128)
            b = (hi << 256) // a
            if b < 1 << 256 and (a * b) >> 384 == m >> 128: return a, b
    R = []
    prev = MASK
    while len(R) < n:
        pat = rnd.randrange(7)
        L = rnd.randrange(4, 40)
        mods = [full(), full(), narrow(), rnd.choice(fixed)]
        for i in range(L):
            if pat == 0: m = mods[0]                       # long run, one modulus
            elif pat == 1: m = mods[i % 2]                 # alternate two full-width moduli
            elif pat == 2: m = (MASK, mods[0], mods[1])[i % 3]
            elif pat == 3: m = mods[i % 4]                 # full, full, narrow, fixed
            elif pat == 4: m = near(prev) if i % 2 else prev  # one limb apart
            elif pat == 5: m = rnd.choice(fixed + mods)
            else: m = mods[0] if i % 5 else 0
            m2 = rnd.choice((m, MASK, near(m), mods[1], narrow(), full()))
            if pat == 1 and rnd.random() < 0.3 and m >> 192:
                a, b = ruint_shape(m)
            else:
                a, b = op(), op()
            R.append((rnd.randrange(2), a, b, m & MASK, m2 & MASK))
            prev = m & MASK or prev
    return R[:n]


def enc(batch):
    return b''.join(b''.join(x.to_bytes(32, 'big') for x in r) for r in batch)


def post(url, body, timeout=90):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'content-type': 'application/json', 'user-agent': 'curl/8'})
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        raw = r.read()
    return json.loads(raw)


def main():
    out, seed, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    eps = [x.split('=', 1) for x in sys.argv[4:]]
    ca, cb = code_a(), code_b()
    R = records(seed, n)
    res = {'seed': seed, 'records': n, 'codeA': ca.hex(), 'codeB': cb.hex(), 'endpoints': {}}
    size = 300
    for label, url in eps:
        e = {'url': url, 'batches': 0, 'words': 0, 'mismatches': [], 'errors': [], 'tags': {}}
        for i in range(0, len(R), size):
            batch = R[i:i + size]
            tx = {'to': A, 'data': '0x' + enc(batch).hex(), 'gas': hex(30_000_000)}
            body = [{'jsonrpc': '2.0', 'id': 1, 'method': 'web3_clientVersion', 'params': []},
                    {'jsonrpc': '2.0', 'id': 2, 'method': 'eth_call', 'params': [tx, 'latest', {A: {'code': '0x' + ca.hex()}, B: {'code': '0x' + cb.hex()}}]},
                    {'jsonrpc': '2.0', 'id': 3, 'method': 'web3_clientVersion', 'params': []}]
            try:
                j = post(url, body)
                d = {x['id']: x for x in j}
            except Exception as ex:  # noqa
                e['errors'].append([i, str(ex)[:200]]); time.sleep(2); continue
            t1, t3 = d[1].get('result', 'ERR'), d[3].get('result', 'ERR')
            tag = t1 if t1 == t3 else f'{t1} | {t3}'
            e['tags'][tag] = e['tags'].get(tag, 0) + 1
            if 'error' in d[2]:
                e['errors'].append([i, json.dumps(d[2]['error'])[:200]]); continue
            got = bytes.fromhex(d[2]['result'][2:])
            if len(got) != 160 * len(batch):
                e['errors'].append([i, f'short {len(got)}']); continue
            for k, r in enumerate(batch):
                exp = expected(r)
                for w in range(5):
                    g = int.from_bytes(got[160 * k + 32 * w:160 * k + 32 * w + 32], 'big')
                    if g != exp[w]:
                        e['mismatches'].append({'rec': i + k, 'word': w + 1, 'r': [hex(x) for x in r], 'got': hex(g), 'want': hex(exp[w]), 'tag': tag})
            e['batches'] += 1; e['words'] += 5 * len(batch)
        res['endpoints'][label] = e
        print(label, e['batches'], 'batches', e['words'], 'words', len(e['mismatches']), 'mismatches', len(e['errors']), 'errors', e['tags'], flush=True)
    json.dump(res, open(out, 'w'), indent=1)


if __name__ == '__main__':
    main()
