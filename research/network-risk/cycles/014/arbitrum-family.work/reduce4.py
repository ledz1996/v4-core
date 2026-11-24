"""Vectors aimed at holiman/uint256 v1.3.2 (pinned by the Nitro go-ethereum fork):
MulMod with a four limb modulus goes through reduce4 with a reciprocal (uint256.go
lines 720-730), and Div/Mod/MulMod with smaller moduli go through udivrem (Knuth D with
the add-back correction). The vectors put the remainder at 0, 1, m-1 and m-2 with
quotients at the bottom, middle and top of the range, for moduli whose top limb is 1,
small, 2^63, 2^63+1, all ones, and moduli of the shape the PoolManager uses
(2^256-1, 2^96, 2^128, and Q96 prices). Run through the dispatcher of battery.py.

Usage: python3 reduce4.py <out.json> [chainId ...]   (run from tools/opdiff on sys.path)
"""
import sys, os, json, random, concurrent.futures as cf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../tools/opdiff'))
from evm import *
from battery import dispatcher, run

M = (1 << 256) - 1


def moduli(rnd):
    out = []
    L = 1 << 64
    for top in (1, 2, 3, 0xff, (1 << 32) - 1, 1 << 63, (1 << 63) + 1, L - 1, L - 2):
        for low in ('zero', 'ones', 'rand', 'one'):
            lo = {'zero': 0, 'ones': (1 << 192) - 1, 'rand': rnd.getrandbits(192), 'one': 1}[low]
            out.append((top << 192) | lo)
    for _ in range(40):
        out.append(rnd.getrandbits(256) | (1 << 192))
    # two and three limb divisors with Knuth D edge shapes
    for n in (1, 2, 3):
        for top in (1, 1 << 63, (1 << 63) + 1, L - 1):
            out.append((top << (64 * (n - 1))) | ((1 << (64 * (n - 1))) - 1))
            out.append((top << (64 * (n - 1))))
    out += [M, M - 1, 1 << 96, 1 << 128, (1 << 160) - 1, 79228162514264337593543950336, 1461446703485210103287273642352763350603345539]
    return out


def vectors(seed=1302):
    rnd = random.Random(seed); V = []
    for m in moduli(rnd):
        qmax = (1 << 512) // m
        for qsel in ('one', 'two', 'mid', 'top', 'top1', 'rand'):
            q = {'one': 1, 'two': 2, 'mid': qmax // 2, 'top': qmax, 'top1': max(qmax - 1, 1), 'rand': rnd.randrange(1, qmax + 1)}[qsel]
            for rsel in ('r0', 'r1', 'rm1', 'rm2'):
                r = {'r0': 0, 'r1': 1, 'rm1': m - 1, 'rm2': m - 2}[rsel]
                target = q * m + r
                if target >> 512 or target <= 0: continue
                for _ in range(3):
                    a = rnd.choice((rnd.getrandbits(256) | (1 << 255), M - rnd.getrandbits(rnd.choice((1, 16, 64, 128))), rnd.getrandbits(rnd.choice((130, 192, 255))) | 1))
                    if a == 0: continue
                    b = target // a
                    for bb in (b, b + 1, b - 1):
                        if 0 < bb <= M:
                            V.append(('MULMOD', a, bb, m))
                            if m > 1: V.append(('MULDIV512', a, bb, m))
                if target <= M:
                    V.append(('MOD', target, m, 0)); V.append(('DIV', target, m, 0))
                    V.append(('ADDMOD', target >> 1, target - (target >> 1), m))
        # reduced operands near the modulus
        for da in (1, 2, 3):
            for db in (1, 2, 3):
                if m > 3: V.append(('MULMOD', m - da, m - db, m))
    return V


if __name__ == '__main__':
    out = sys.argv[1]; only = set(map(int, sys.argv[2:]))
    code = dispatcher(); V = vectors()
    per = {}
    for t in V: per[t[0]] = per.get(t[0], 0) + 1
    print(len(V), 'vectors', per, flush=True)
    nets = [n for n in networks() if not only or n[0] in only]

    def work(n):
        cid, name, url = n
        done, bad, errors = run(url, code, V)
        return {'chainId': cid, 'name': name, 'vectors': len(V), 'ran': done, 'mismatchCount': len(bad), 'mismatches': bad[:100], 'errors': errors[:10]}

    res = []
    with cf.ThreadPoolExecutor(4) as ex:
        for r in ex.map(work, nets):
            print(f"{r['chainId']:>8} {r['name']:16} ran {r['ran']}/{r['vectors']} mismatches {r['mismatchCount']} errors {len(r['errors'])}", flush=True); res.append(r)
    json.dump({'vectors': len(V), 'perOp': per, 'results': res}, open(out, 'w'), indent=1)
