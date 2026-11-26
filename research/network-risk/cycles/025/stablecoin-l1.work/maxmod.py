"""Cycle 25 vectors aimed at ruint 1.21.1 mul_mod: the end-around-carry path for modulus 2^256-1
(src/modular.rs lines 120-127 of the crate) and the skip test of rem_nxm_spare_limb (src/algorithms/div/knuth.rs
lines 131-136) with the top two limbs equal or one apart, plus FullMath-shaped inputs. Each record is (a, b, n);
the code returns mulmod(a,b,n), addmod(a,b,n) and the FullMath.mulDiv(a,b,n) high-half rebuild
(mulmod(a,b,not(0)) - a*b - lt). Read-only eth_call with a state override. usage: maxmod.py <out.json> [chainId ...]"""
import sys, json, random
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
from evm import call_code, networks, assemble
M = 2**256 - 1; R = random.Random(25_4217_5042)
prog = [('PUSH', 0),  # off
        ('LABEL', 'loop'), 'DUP1', 'CALLDATASIZE', 'GT', 'ISZERO', ('REF', 'end'), 'JUMPI',
        'DUP1', ('PUSH', 64), 'ADD', 'CALLDATALOAD',  # n off
        'DUP2', ('PUSH', 32), 'ADD', 'CALLDATALOAD',  # b n off
        'DUP3', 'CALLDATALOAD',  # a b n off
        'DUP3', 'DUP3', 'DUP3', 'MULMOD',  # mm a b n off
        'DUP5', 'MSTORE',  # a b n off   mem[off]=mm
        'DUP3', 'DUP3', 'DUP3', 'ADDMOD', 'DUP5', ('PUSH', 32), 'ADD', 'MSTORE',
        'DUP2', 'DUP2', 'MUL',  # prod0 a b n off
        'DUP3', 'DUP3', ('PUSH', 0), 'NOT', 'SWAP2', 'SWAP1', 'MULMOD',  # mm2 prod0 a b n off  (mulmod(a,b,not0))
        'DUP2', 'DUP2', 'LT', 'SWAP1', 'DUP3', 'SWAP1', 'SUB', 'SUB',  # prod1 prod0 a b n off
        'DUP6', ('PUSH', 64), 'ADD', 'MSTORE', 'POP', 'POP', 'POP', 'POP',  # off
        ('PUSH', 96), 'ADD', ('REF', 'loop'), 'JUMP',
        ('LABEL', 'end'), 'CALLDATASIZE', ('PUSH', 0), 'RETURN']
code = assemble(prog)
def rnd_limbs(): return R.getrandbits(64)
def vecs():
    V = []
    # modulus 2^256-1: products whose lo+hi land on MAX-1, MAX, MAX+1, 2^256, 2*MAX-1
    for _ in range(600):
        a = R.getrandbits(256) | 1; b = R.getrandbits(256)
        V.append((a, b, M))
    for k in (1, 2, 3, 2**128, 2**255, M, M - 1):
        for t in range(40):
            a = R.getrandbits(256); b = (M - a) if t % 2 else (a ^ M)
            V.append((a, b, M)); V.append((k, M - t, M)); V.append((M - t, M - k % 7, M))
    # sums lo+hi exactly MAX: choose a = 2^128+1, b = 2^128-1 -> a*b = 2^256-1 ; and multiples
    for j in range(1, 200):
        V.append((2**128 + 1, (2**128 - 1) * j % 2**256, M)); V.append((M, j, M)); V.append((j * (2**64 + 1), M // (2**64 + 1), M))
    # skip test: n of four limbs with nonzero top limb; a,b with nonzero top limbs; product top limbs near n's
    for _ in range(3000):
        n = R.getrandbits(256) | (1 << 255 >> R.randrange(0, 63)); n |= 1 << 192
        a = R.randrange(n // 2, n) if R.random() < .5 else R.getrandbits(256) | (1 << 192)
        # b near n*2^256/a so the product's top two limbs equal or straddle n's
        target = (n << 256) // max(a, 1)
        for d in (-1, 0, 1):
            b = (target + d * R.getrandbits(8)) % 2**256
            if b >> 192: V.append((a, b, n))
    # FullMath shapes: liquidity<<96 times price diff over price products
    for _ in range(1500):
        L = R.getrandbits(128); p = R.randrange(4295128739, 1461446703485210103287273052203988822378723970342)
        q = R.randrange(4295128739, 1461446703485210103287273052203988822378723970342)
        V.append((L << 96, abs(p - q), max(p, 1))); V.append((L, abs(p - q), 1 << 96)); V.append((p, q, M))
    return V
def ref(a, b, n):
    mm = (a * b) % n if n else 0; am = (a + b) % n if n else 0
    return [mm, am, (a * b) >> 256]
if __name__ == '__main__':
    out = sys.argv[1]; only = set(map(int, sys.argv[2:])); V = vecs(); res = {}
    for cid, name, url in networks():
        if only and cid not in only: continue
        mism = []; ran = 0; err = 0
        for i in range(0, len(V), 150):
            chunk = V[i:i + 150]; data = b''.join(x.to_bytes(32, 'big') for t in chunk for x in t)
            try:
                r = call_code(url, code, data, gas=30_000_000)
            except Exception as e:
                err += 1; continue
            r = bytes.fromhex(r[2:]) if isinstance(r, str) else r
            for j, t in enumerate(chunk):
                got = [int.from_bytes(r[96 * j + 32 * k:96 * j + 32 * k + 32], 'big') for k in range(3)]
                if got != ref(*t): mism.append({'v': [hex(x) for x in t], 'got': [hex(x) for x in got]})
                ran += 1
        res[cid] = {'name': name, 'vectors': len(V), 'ran': ran, 'mismatches': mism[:50], 'nMismatch': len(mism), 'errors': err}
        print(cid, name, 'ran', ran, '/', len(V), 'mismatches', len(mism), 'errors', err)
    json.dump({'vectors': len(V), 'results': res}, open(out, 'w'), indent=1)
