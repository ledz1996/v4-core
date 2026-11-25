"""Per-path input batteries for harness.cpp: for one path at a time, a scenario
sets up a pool, liquidity, claims and allowances, then sends many calls of that
path with random and edge inputs. Usage: gen_mass.py <path> <seed> <scenarios> <calls>"""
import random, sys
import gen
from gen import PM, A, B, C, T1, T2, NATIVE, SEL, M256, MIN_SQRT, MAX_SQRT, w, a32, key, call, unlock, tx, CLOSE, CLEAREXACT, edge, small

USERS = [A, B, C]


def amt(r):
    k = r.random()
    if k < 0.3: return small(r)
    if k < 0.6: return edge(r)
    if k < 0.8:
        e = r.choice([127, 128, 159, 160, 161, 255, 256])
        return ((1 << e) + r.randint(-3, 3)) & M256
    return r.getrandbits(256)


def setup(r, lines, kind):
    if kind in ('fallback',):
        ts = r.choice([16384, 32767]); lo, hi = -(887272 // ts * ts), 0
        sqrtp = (1 << 96) - (1 << r.randint(40, 70)); liq = r.randint(1 << 98, 1 << 106); fee = r.choice([0, 500, 3000])
    elif kind in ('big1',):
        ts = r.choice([16384, 32767]); lo, hi = 0, 887272 // ts * ts
        sqrtp = (1 << 96) + (1 << r.randint(40, 70)); liq = r.randint(1 << 98, 1 << 106); fee = r.choice([0, 500, 3000])
    else:
        ts = r.choice([1, 10, 60, 200]); lo, hi = -(887272 // ts * ts), 887272 // ts * ts
        sqrtp = r.choice([1 << 96, r.randint(MIN_SQRT, MAX_SQRT - 1)]); liq = r.choice([10 ** 18, 1 << 80, r.getrandbits(70) | 1])
        fee = r.choice([0, 500, 3000, 10000])
    c0, c1 = (NATIVE, T1) if r.random() < 0.5 else (T1, T2)
    k = key(c0, c1, fee, ts)
    lines.append(tx(A, SEL['initialize'] + k + w(sqrtp)))
    steps = [call(PM, 'modifyLiquidity', k + w(lo) + w(hi) + w(liq) + w(0) + w(32 * 10) + w(0), gas=10_000_000), CLOSE(c0), CLOSE(c1)]
    for v in USERS:
        for c in (c0, c1):
            steps.append(call(PM, 'mint', a32(v) + a32(c) + w(r.getrandbits(r.randint(100, 126)))))
    steps += [CLOSE(c0), CLOSE(c1)]
    lines.append(tx(A, unlock(steps)))
    for s in USERS:
        for t in USERS:
            if s != t and r.random() < 0.7:
                lines.append(tx(s, SEL['approve'] + a32(t) + a32(c0) + w(r.choice([M256, amt(r), r.getrandbits(120)]))))
                lines.append(tx(s, SEL['approve'] + a32(t) + a32(c1) + w(r.choice([M256, amt(r), r.getrandbits(120)]))))
            if s != t and r.random() < 0.3:
                lines.append(tx(s, SEL['setOperator'] + a32(t) + w(1)))
    return k, c0, c1


def body(path, r, k, c0, c1, n):
    out = []
    cid = lambda: a32(r.choice([c0, c1]))
    per = 20
    if path == 'approve':
        for _ in range(n):
            s, t = r.choice(USERS), r.choice(USERS)
            out.append(tx(s, SEL['approve'] + a32(t) + cid() + w(amt(r))))
            if r.random() < 0.3: out.append(tx(s, SEL['allowance'] + a32(s) + a32(t) + cid()))
    elif path == 'transferFrom':
        for _ in range(n):
            s, t = r.choice(USERS), r.choice(USERS)
            if r.random() < 0.15:
                out.append(tx(s, SEL['approve'] + a32(t) + cid() + w(r.choice([M256, amt(r), r.getrandbits(110)]))))
            if r.random() < 0.05:
                out.append(tx(s, SEL['setOperator'] + a32(t) + w(r.randint(0, 1))))
            out.append(tx(t, SEL['transferFrom'] + a32(s) + a32(r.choice(USERS)) + cid() + w(r.choice([amt(r), r.getrandbits(r.randint(1, 110))]))))
    else:
        done = 0
        while done < n:
            steps = []
            for _ in range(per):
                if path == 'burn':
                    steps.append(call(PM, 'burn', a32(r.choice(USERS)) + cid() + w(r.choice([amt(r), r.getrandbits(r.randint(1, 110))]))))
                elif path == 'clear':
                    if r.random() < 0.5:
                        c = r.choice([c0, c1])
                        v = r.getrandbits(r.randint(1, 120)) | 1
                        if c == NATIVE:
                            steps.append(call(PM, 'settle', '', value=v))
                        else:
                            steps += [call(PM, 'sync', a32(c)), call(c, 'erc20transfer', a32(PM) + w(v)), call(PM, 'settle')]
                        steps.append(CLEAREXACT(c))
                    else:
                        steps.append(call(PM, 'clear', cid() + w(amt(r))))
                elif path == 'donate':
                    steps.append(call(PM, 'donate', k + w(amt(r)) + w(amt(r)) + w(32 * 8) + w(0), gas=8_000_000))
                elif path in ('fallback', 'big1', 'swap'):
                    if path == 'fallback':
                        zf1 = True; a = -r.randint(1 << 160, 1 << r.randint(161, 170))
                    elif path == 'big1':
                        zf1 = False; a = -r.randint(1 << 160, 1 << r.randint(161, 170))
                    else:
                        zf1 = r.random() < 0.5; a = amt(r) % (1 << 255); a = -a if r.random() < 0.6 else a
                    lim = MIN_SQRT + 1 if zf1 else MAX_SQRT - 1
                    steps.append(call(PM, 'swap', k + w(int(zf1)) + w(a) + w(lim) + w(32 * 9) + w(0), gas=25_000_000))
                elif path == 'take':
                    steps.append(call(PM, 'take', cid() + a32(r.choice(USERS)) + w(amt(r))))
                    if r.random() < 0.3: steps.append(call(PM, 'mint', a32(r.choice(USERS)) + cid() + w(amt(r))))
                done += 1
            steps += [CLOSE(c0), CLOSE(c1)]
            out.append(tx(r.choice(USERS), unlock(steps)))
    return out


def main():
    path, seed, ns, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    r = random.Random(seed)
    with open('mass-%s-%d.txt' % (path, seed), 'w') as f:
        for i in range(ns):
            lines = ['SCEN %s-%d' % (path, i)]
            k, c0, c1 = setup(r, lines, path if path in ('fallback', 'big1') else 'plain')
            lines += body(path, r, k, c0, c1, n)
            f.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
