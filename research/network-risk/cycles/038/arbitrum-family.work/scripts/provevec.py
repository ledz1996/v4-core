"""Cycle 36 arbitrum-family, lead L-1280. Vectors aimed at what a time-travelling proof in the go1.25.12 prove pass
(Go issues 80517 / 80618, fixed in go1.25.13) could break on amd64: a branch on the shift count removed, or a shift
marked bounded so that SHLQ/SHRQ/SARQ mask the count to 6 bits. Every shift count 0..320 plus counts near 2^64 and
2^255 for SHL, SHR, SAR; every BYTE index and SIGNEXTEND width 0..40; DIV, MOD, SDIV, SMOD, ADDMOD, MULMOD with
divisors of 1 to 4 limbs whose top limb has 1, 32 and 64 significant bits. Runs the battery.py dispatcher by eth_call.
Usage: python3 provevec.py <out.json> <url> [<url> ...]"""
import sys, json, random
sys.path.insert(0, '/home/user/v4-core/research/network-risk/tools/opdiff')
import battery as B
from evm import rpc, MASK
rnd = random.Random(20261127)
def r(k): return rnd.getrandbits(k)
ops = [(1 << 256) - 1, 1, 1 << 255, (1 << 255) - 1, 0x8000000000000000_0000000000000000_0000000000000000_0000000000000001,
       0xffffffffffffffff, 0xffffffffffffffff << 64, 0xffffffffffffffff << 128, 0xffffffffffffffff << 192,
       0x5555555555555555555555555555555555555555555555555555555555555555] + [r(256) for _ in range(8)] + [MASK - r(70) for _ in range(4)]
counts = list(range(0, 321)) + [(1 << 64) + k for k in (-1, 0, 1, 63, 64)] + [(1 << 32) + 1, 1 << 128, (1 << 255) + 1, MASK, MASK - 63]
V = []
for op in ('SHL', 'SHR', 'SAR'):
    for a in counts:
        for b in ops: V.append((op, a, b, 0))
for a in list(range(0, 40)) + [(1 << 64) + 3, MASK]:
    for b in ops: V += [('BYTE', a, b, 0), ('SIGNEXTEND', a, b, 0)]
divs = []
for limbs in (1, 2, 3, 4):
    for top in (1, 32, 64):
        for _ in range(4):
            d = (r(top) | (1 << (top - 1))) << (64 * (limbs - 1)) | r(64 * (limbs - 1)) if limbs > 1 else (r(top) | (1 << (top - 1)))
            divs.append(d & MASK)
nums = [MASK, MASK - 1, 1 << 255, (1 << 192) - 1, (1 << 128) + 1] + [r(256) for _ in range(10)] + [r(130), r(64)]
for d in divs:
    for n in nums:
        for op in ('DIV', 'MOD', 'SDIV', 'SMOD'): V.append((op, n, d, 0))
        V += [('ADDMOD', n, MASK - r(60), d), ('MULMOD', n, MASK - r(100), d), ('MULMOD', n, r(256), d), ('MULDIV512', n, r(256), d)]
code = B.dispatcher(); res = {'vectors': len(V), 'urls': {}}
print('vectors', len(V), flush=True)
for url in sys.argv[2:]:
    cv = rpc(url, 'web3_clientVersion', [], 20)
    done, bad, errors = B.run(url, code, V, size=400)
    cv2 = rpc(url, 'web3_clientVersion', [], 20)
    res['urls'][url] = {'cvBefore': cv, 'cvAfter': cv2, 'done': done, 'mismatches': bad[:50], 'nbad': len(bad), 'errors': errors[:10]}
    print(url, cv, cv2, 'done', done, 'bad', len(bad), 'errors', len(errors), flush=True)
json.dump(res, open(sys.argv[1], 'w'), indent=1)
