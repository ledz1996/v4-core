"""Extra vectors for this cycle, aimed at holiman/uint256 v1.3.2 (Celo op-geth backend) and ruint 1.18/1.20:
the even-base shortcut of Exp added in v1.3.2, Exp exponents that cross 64-bit limbs, SRsh at every limb edge,
SDiv/SMod at INT_MIN and -1, ExtendSign for every byte index, Byte for every index, AddMod fast path (m >= 2^192).
Usage: python3 extra.py <out.json> <chainId>   (DUAL_* env as in dual.py)"""
import sys, os, random, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dual  # patches evm.rpc
import battery
M = (1 << 256) - 1
rnd = random.Random(9_2026_11_24)
V = []
evens = [0, 2, 4, 6, 8, 10, 1 << 64, 1 << 128, 1 << 255, (1 << 256) - 2, 0x1000000000000000000000000000000000000000000000000000000000000000, rnd.getrandbits(256) & ~1]
odds = [1, 3, 5, 7, 0xffff, M, M - 2, (1 << 255) + 1, rnd.getrandbits(256) | 1, rnd.getrandbits(256) | 1]
exps = list(range(0, 300, 7)) + [63, 64, 65, 127, 128, 129, 191, 192, 193, 255, 256, 257, 511, (1 << 64) - 1, 1 << 64, (1 << 64) + 1,
                                  1 << 128, 1 << 192, M, rnd.getrandbits(256), rnd.getrandbits(80), rnd.getrandbits(140), rnd.getrandbits(200)]
for b in evens + odds:
    for e in exps: V.append(('EXP', b, e, 0))
negs = [1 << 255, M, M - 1, (1 << 255) | 1, (M << 64) & M, (M << 128) & M, (M << 192) & M, rnd.getrandbits(256) | (1 << 255)]
for x in negs + [0, 1, (1 << 255) - 1]:
    for n in [0, 1, 63, 64, 65, 127, 128, 129, 191, 192, 193, 254, 255, 256, 257, 1 << 64, M]:
        V.append(('SAR', n, x, 0)); V.append(('SHL', n, x, 0)); V.append(('SHR', n, x, 0))
for a in [1 << 255, M, 1, 0, (1 << 255) - 1, 887272, (M - 887271) , rnd.getrandbits(256)]:
    for b in [M, 1, 1 << 255, 0, 2, M - 1, 60, (M - 59), 1 << 64, rnd.getrandbits(256)]:
        V.append(('SDIV', a, b, 0)); V.append(('SMOD', a, b, 0)); V.append(('SLT', a, b, 0)); V.append(('SGT', a, b, 0))
for i in list(range(0, 33)) + [1 << 64, M]:
    for x in [0x80 << (8 * min(i, 31)), (0x80 << (8 * min(i, 31))) - 1, M, rnd.getrandbits(256), 0x7fffff, 0x800000, 0xff7fffff]:
        V.append(('SIGNEXTEND', i, x, 0)); V.append(('BYTE', i, x, 0))
for m in [M, M - 1, 1 << 192, (1 << 192) + 1, (1 << 255), rnd.getrandbits(256) | (1 << 192)]:
    for x in [m - 1, m, m + 1 if m < M else 0, M, 0, 1 << 255]:
        for y in [m - 1, 1, M, m]:
            V.append(('ADDMOD', x & M, y & M, m)); V.append(('MULMOD', x & M, y & M, m))
if __name__ == '__main__':
    out, cid = sys.argv[1], int(sys.argv[2])
    url = [n for n in dual.evm.networks() if n[0] == cid][0][2]
    t0 = time.time(); code = battery.dispatcher()
    done, bad, errors = battery.run(url, code, V, size=300)
    r = {'vectors': len(V), 'ran': done, 'mismatchCount': len(bad), 'mismatches': bad[:100], 'errors': errors[:20], 'chainId': cid, 'rpc': url, 'seconds': round(time.time() - t0), 'dual': dual.LOG}
    json.dump(r, open(out, 'w'), indent=1); print(json.dumps({k: v for k, v in r.items() if k != 'mismatches'})[:1200])
