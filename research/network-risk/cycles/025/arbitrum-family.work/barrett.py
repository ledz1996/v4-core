"""Cycle 25 vectors aimed at the Barrett reduction of holiman/uint256 v1.3.2, which
Nitro's go-ethereum fork pins (MulMod -> Reciprocal + reduce4 for every modulus with
m[3] != 0, which includes the modulus 2^256-1 of FullMath.mulDiv). Reciprocal has
special branches: a power of two, a top 32 bit word of exactly 0x80000000 after
left alignment (r0 = 0xffffffff), and the r1/r2 overflow guards. Products are placed
at exact multiples of m, one below, one above, and m-1 above, with large quotients.
Runs through the dispatcher of battery.py. Read-only eth_call with state override.
Usage: python3 barrett.py <out.json> [chainId ...]   (alternative endpoints via ALT env)"""
import sys, os, json, random, concurrent.futures as cf
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import evm
from evm import *
from battery import dispatcher, run

def moduli(rnd):
    M = []
    for p in range(192, 256):
        base = 1 << p
        M += [base, base + 1, base - 1 if p > 192 else base + 3, base + (1 << (p - 33)), base + (1 << (p - 32)) - 1,
              base + rnd.getrandbits(p - 32), (1 << (p + 1)) - 1, (1 << (p + 1)) - (1 << (p - 31)),
              base | rnd.getrandbits(p), base + (1 << (p - 64)), base + (1 << (p - 128)) + 1]
    M += [(1 << 256) - 1, (1 << 256) - 2, (1 << 256) - (1 << 64) - 1, (1 << 255) + (1 << 254)]
    return [m for m in M if (m >> 192) and m < (1 << 256)]

def vectors(seed=2511):
    rnd = random.Random(seed); V = []
    for m in moduli(rnd):
        pairs = [(m, rnd.getrandbits(256)), (m - 1, m - 1), (m + 1 if m + 1 < 2**256 else m - 2, m - 1), (MASK, m - 1),
                 (MASK, MASK), (m - 1, MASK), ((m >> 1) + 1, 2), (m - 1, 2), (rnd.getrandbits(256), rnd.getrandbits(256))]
        for k in range(6):
            q = rnd.choice([MASK, MASK - 1, m - 1, rnd.getrandbits(256), 1 << 255, rnd.getrandbits(200)])
            r = rnd.choice([0, 1, m - 1, m - 2, rnd.randrange(m)])
            t = q * m + r
            if t >> 512: t = (m - 1) * m + r
            x = rnd.getrandbits(256) | (1 << 255)
            y = t // x
            if y < 2**256: pairs.append((x, y)); pairs.append((x, y + 1 if y + 1 < 2**256 else y))
        for a, b in pairs:
            a &= MASK; b &= MASK
            V.append(('MULMOD', a, b, m))
            V.append(('ADDMOD', a, b, m))
            V.append(('MULDIV512', a, b, m))
    return V

if __name__ == '__main__':
    out = sys.argv[1]; only = set(map(int, sys.argv[2:]))
    code = dispatcher(); V = vectors()
    per = {}
    for t in V: per[t[0]] = per.get(t[0], 0) + 1
    print(len(V), 'vectors', per, flush=True)
    nets = [n for n in networks() if n[0] in only]
    if os.environ.get('ALT'):
        nets += [(4216101, 'Arb1 publicnode', 'https://arbitrum-one-rpc.publicnode.com'), (4216102, 'Arb1 pocket', 'https://arb-one.api.pocket.network')]
    def work(n):
        cid, name, url = n
        done, bad, errors = run(url, code, V)
        if errors and done < len(V):
            retry = [t for i, _ in errors for t in V[i:i + 600]]
            d2, b2, e2 = run(url, code, retry, size=150); done += d2; bad += b2; errors = e2
        return {'chainId': cid, 'name': name, 'rpc': url, 'vectors': len(V), 'ran': done, 'mismatchCount': len(bad), 'mismatches': bad[:100], 'errors': errors[:10]}
    res = []
    with cf.ThreadPoolExecutor(5) as ex:
        for r in ex.map(work, nets):
            print(f"{r['chainId']:>8} {r['name']:16} ran {r['ran']}/{r['vectors']} mismatches {r['mismatchCount']} errors {len(r['errors'])}", flush=True); res.append(r)
    json.dump({'vectors': len(V), 'perOp': per, 'results': res}, open(out, 'w'), indent=1)
