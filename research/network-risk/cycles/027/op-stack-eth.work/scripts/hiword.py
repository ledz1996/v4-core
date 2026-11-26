"""Cycle 27 op-stack-eth: vectors whose index or shift operand has small low limbs
and nonzero high limbs (the shape a library that truncates the operand to 32 or 64
bits before clamping would get wrong), EXP with exponents that have only high limbs,
SIGNEXTEND/BYTE with such indices, and MULMOD/ADDMOD with modulus 2^256-1 and
2^256-2 against operands near the modulus. Uses battery.py's dispatcher and reference.
Usage: python3 hiword.py <out.json> [chainId ...] [--rounds N]
"""
import sys, os, json, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'opdiff'))
import battery
from evm import MASK, networks

def vectors():
    rnd = random.Random(20261127)
    lows = [0, 1, 2, 7, 8, 15, 16, 30, 31, 32, 33, 63, 64, 127, 128, 200, 255]
    idx = []
    for hi in (32, 33, 40, 63, 64, 65, 96, 127, 128, 129, 160, 192, 200, 224, 248, 255):
        for k in lows:
            idx.append(((1 << hi) + k) & MASK)
    idx += [(MASK ^ 0xff) | k for k in lows] + [((1 << 64) - 1) << 64 | k for k in lows]
    vals = [MASK, 1, 1 << 255, (1 << 255) | 1, 0x0102030405060708091011121314151617181920212223242526272829303132,
            0x8000000000000000000000000000000000000000000000000000000000000080, 0xfffcb933bd6fad37aa2d162d1a594001]
    V = []
    for op in ('SHL', 'SHR', 'SAR', 'BYTE', 'SIGNEXTEND'):
        for a in idx:
            for b in vals:
                V.append((op, a, b, 0))
    for base in (0, 1, 2, 3, MASK, 1 << 128, 0xfffcb933bd6fad37aa2d162d1a594001):
        for e in idx[:120]:
            V.append(('EXP', base, e, 0))
    near = [MASK, MASK - 1, MASK - 2, 1 << 255, (1 << 255) - 1, (1 << 128) - 1, 1 << 128, ((1 << 128) - 1) << 128]
    for m in (MASK, MASK - 1, MASK - 2, (1 << 255) + 1, ((1 << 128) - 1) << 128 | 1):
        for a in near:
            for b in near:
                V.append(('MULMOD', a, b, m)); V.append(('ADDMOD', a, b, m)); V.append(('MULDIV512', a, b, m))
        for _ in range(300):
            a = MASK - rnd.getrandbits(rnd.choice((1, 64, 128, 192))); b = MASK - rnd.getrandbits(rnd.choice((1, 64, 128, 192)))
            V.append(('MULMOD', a, b, m)); V.append(('MULDIV512', a, b, m))
    return V

if __name__ == '__main__':
    args = sys.argv[1:]; rounds = 1
    if '--rounds' in args:
        i = args.index('--rounds'); rounds = int(args[i + 1]); del args[i:i + 2]
    out = args[0]; only = set(map(int, args[1:]))
    code = battery.dispatcher(); V = vectors()
    print('vectors', len(V))
    res = []
    for cid, name, url in networks():
        if only and cid not in only: continue
        for r in range(rounds):
            done, bad, errors = battery.run(url, code, V, size=300)
            print(f'{cid:>8} {name:16} round {r+1} ran {done}/{len(V)} mismatches {len(bad)} errors {len(errors)} {errors[:1]}')
            res.append({'chainId': cid, 'round': r + 1, 'ran': done, 'vectors': len(V), 'mismatches': bad[:50], 'errors': errors[:5]})
    json.dump(res, open(out, 'w'), indent=1)
