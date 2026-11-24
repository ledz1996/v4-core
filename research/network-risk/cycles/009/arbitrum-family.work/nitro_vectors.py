"""Extra vectors for chain ids 42161, 4663, 99901, aimed at the branches of holiman/uint256 v1.3.2
and of the Nitro fork's instructions.go (commit 0e44603) read in cycle 9:
AddMod fast path (m >= 2^192, operands in [m, 2m)), SAR at shift 255/256/257 (guard GtUint64(256) then SRsh),
SIGNEXTEND and BYTE with indexes above 2^64, EXP with even base and exponent bit length 8/9 and limb borders,
shifts by 2^64+k, MulMod through reduce4 (m[3]!=0) and through udivrem (m < 2^192, product > 2^256),
and signed division at MIN and -1. Uses the dispatcher and reference of tools/opdiff/battery.py.
Usage: python3 -I nitro_vectors.py <out.json>   (run from this directory, adds tools/opdiff to the path)"""
import sys, os, json, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'opdiff'))
from evm import MASK
from battery import dispatcher, run
R = random.Random(9_42161)
M = MASK; MIN = 1 << 255
def rnd(b): return R.getrandbits(b)
V = []
for _ in range(3000):  # AddMod fast path
    m = rnd(256) | (1 << (192 + R.randrange(64)))
    x = m + rnd(R.choice((8, 64, 190))) if R.random() < 0.6 else rnd(256) % m
    y = m + rnd(R.choice((8, 64, 190))) if R.random() < 0.6 else rnd(256) % m
    if (x >> 192) <= (m >> 192) and (y >> 192) <= (m >> 192) and x <= M and y <= M:
        V.append(('ADDMOD', x, y, m))
    V.append(('ADDMOD', M - rnd(8), M - rnd(8), m))
for sh in (254, 255, 256, 257, 511, 1 << 64, (1 << 64) + 1, M):
    for v in (MIN, M, 1, MIN - 1, MIN | 1, 0, rnd(256)):
        V.append(('SAR', sh, v, 0)); V.append(('SHL', sh, v, 0)); V.append(('SHR', sh, v, 0))
for i in (29, 30, 31, 32, 1 << 64, (1 << 64) + 2, M):
    for v in (0x80 << 232, 0x7f << 240, M, rnd(256), 0x8000, 0xff7fff):
        V.append(('SIGNEXTEND', i, v, 0)); V.append(('BYTE', i, v, 0))
for base in (2, 4, 6, 3, 5, M, M - 1, MIN, rnd(256) | 1, rnd(256) & ~1):
    for e in (0, 1, 127, 128, 255, 256, 257, 63, 64, 65, 191, 192, 193, (1 << 64) - 1, 1 << 64, (1 << 128) + 3, M):
        V.append(('EXP', base, e, 0))
for _ in range(4000):  # MulMod paths
    m = rnd(256) | (1 << 255) if R.random() < 0.3 else rnd(193 + R.randrange(63))
    if m == 0: m = 1
    V.append(('MULMOD', rnd(256), rnd(256), m))
    V.append(('MULMOD', rnd(256), rnd(256), rnd(R.randrange(1, 192)) or 3))
    V.append(('MULMOD', rnd(256), rnd(256), M))
    V.append(('MULDIV512', rnd(256), rnd(256), rnd(256) | 1))
for a in (MIN, MIN + 1, M, 1, 0, rnd(256)):
    for b in (M, 1, MIN, 0, 2, M - 1):
        for op in ('SDIV', 'SMOD', 'DIV', 'MOD'): V.append((op, a, b, 0))
code = dispatcher(); out = {'vectors': len(V), 'results': []}
for cid, url in ((42161, 'https://arb1.arbitrum.io/rpc'), (4663, 'https://rpc.mainnet.chain.robinhood.com'), (99901, 'https://rpc.elysium.kinetiq.xyz')):
    done, bad, errors = run(url, code, V, size=500)
    print(cid, 'ran', done, '/', len(V), 'mismatches', len(bad), 'errors', errors[:2])
    out['results'].append({'chainId': cid, 'ran': done, 'mismatches': bad[:50], 'errors': errors[:10]})
json.dump(out, open(sys.argv[1], 'w'), indent=1)
