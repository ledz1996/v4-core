"""Second set for maxmod.py: products built so that, after normalisation, the top two limbs of the 512 bit
product equal those of the divisor (the ruint 1.21.0 fault condition, fixed in 1.21.1 knuth.rs 133-136), or exceed
or undercut them by one. usage: maxmod2.py <out.json> [chainId ...]"""
import sys, random
src = open(__file__.replace('maxmod2.py', 'maxmod.py')).read().split("if __name__")[0]
exec(src)
R2 = random.Random(2025_681)
def vecs():
    V = []; stats = {'eq': 0, 'plus1': 0, 'minus1': 0}
    while len(V) < 6000:
        s = R2.randrange(0, 60); top = R2.getrandbits(64 - s) | (1 << (63 - s))
        n = (top << 192) | R2.getrandbits(192); nn = n << s
        d = R2.choice((0, 0, 1, -1))
        Tn = (((nn >> 128) + d) << 320) + R2.getrandbits(318) + (1 << 318)
        P = Tn >> s
        a = R2.randrange(1 << 200, 1 << 256)
        b = P // a
        if not (b >> 192) or b >> 256: continue
        p = (a * b) << s
        if p >> 448: continue
        t2 = (p >> 320) & (2**128 - 1); dt = nn >> 128
        k = 'eq' if t2 == dt else 'plus1' if t2 == dt + 1 else 'minus1' if t2 == dt - 1 else None
        if not k: continue
        stats[k] += 1; V.append((a, b, n))
    print('constructed', stats)
    return V
if __name__ == '__main__':
    out = sys.argv[1]; only = set(map(int, sys.argv[2:])); V = vecs(); res = {}
    for cid, name, url in networks():
        if only and cid not in only: continue
        mism = []; ran = 0; err = 0
        for i in range(0, len(V), 150):
            chunk = V[i:i + 150]; data = b''.join(x.to_bytes(32, 'big') for t in chunk for x in t)
            try: r = call_code(url, code, data, gas=30_000_000)
            except Exception as e: err += 1; continue
            for j, t in enumerate(chunk):
                got = [int.from_bytes(r[96 * j + 32 * k:96 * j + 32 * k + 32], 'big') for k in range(3)]
                if got != ref(*t): mism.append({'v': [hex(x) for x in t], 'got': [hex(x) for x in got]})
                ran += 1
        res[cid] = {'name': name, 'vectors': len(V), 'ran': ran, 'mismatches': mism[:50], 'nMismatch': len(mism), 'errors': err}
        print(cid, name, 'ran', ran, '/', len(V), 'mismatches', len(mism), 'errors', err)
    json.dump({'vectors': len(V), 'results': res}, open(out, 'w'), indent=1)
