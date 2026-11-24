"""Vectors for the ruint < 1.20.0 advisory RUSTSEC-2026-0220 (shift amounts truncated modulo 2^32
in wrapping_shl/wrapping_shr) and for the byte() fix of ruint #603. X Layer pins ruint 1.18.0.
SHL, SHR, SAR, BYTE and SIGNEXTEND with first operands k*2^32 + r for small r, 2^64 + r, 2^128 + r
and 2^255 + r, against values with both sign patterns. Each request is sent three times so that a
load balanced endpoint (forno) is likely to hit both backends.
Usage: python3 shift32.py <out.json> <chainId> [...]
"""
import sys, os, json, random
base = os.path.dirname(os.path.abspath(__file__)).rsplit('/', 4)[0]
sys.path.insert(0, base + '/tools/opdiff')
import battery as B
nets = {n['chainId']: n for n in json.load(open(base + '/state/networks.json'))['networks']}
rnd = random.Random(1101)
M = (1 << 256) - 1
vals = [M, 1, 1 << 255, (1 << 255) - 1, 0x8000000000000000ffffffffffffffff0000000000000001, rnd.getrandbits(256), rnd.getrandbits(256) | (1 << 255)]
amts = []
for hi in (1 << 32, 2 << 32, 0xffffffff << 32, 1 << 63, 1 << 64, 1 << 128, 1 << 255):
    for r in (0, 1, 2, 15, 31, 32, 63, 64, 127, 128, 200, 255):
        amts.append(hi + r)
amts += [0xffffffff, 0x100000000 - 1, (1 << 32) + (1 << 31)]
V = []
for op in ('SHL', 'SHR', 'SAR', 'BYTE', 'SIGNEXTEND'):
    for a in amts:
        for v in vals:
            V.append((op, a, v, 0))
if __name__ == '__main__':
    out = sys.argv[1]; cids = [int(x) for x in sys.argv[2:]]
    code = B.dispatcher(); res = {}
    for cid in cids:
        url = nets[cid]['rpc']; rounds = []
        for r in range(3):
            done, bad, errors = B.run(url, code, V, size=300)
            rounds.append({'ran': done, 'mismatches': bad[:20], 'mismatchCount': len(bad), 'errors': errors[:5]})
        res[cid] = {'vectors': len(V), 'rounds': rounds}
        print(cid, len(V), [(x['ran'], x['mismatchCount'], len(x['errors'])) for x in rounds], flush=True)
    json.dump(res, open(out, 'w'), indent=1)
