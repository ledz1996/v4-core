"""Runs the transcriptions of settlejit.py against the specification.
Usage: python3 -I run_units.py <out.json> [randomCases]"""
import sys, os, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import settlejit as J

U = 1 << 256


def main():
    out = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 200000
    rng = random.Random(11_2026_11_24)
    res = {}
    # 1. CALLDATALOAD: every calldata length 0..300, every offset 0..len+40, each operand location
    fails = []; cases = 0; oob = 0
    locs = [('lit', None), ('gpr', (True, 0)), ('gpr', (False, 1)), ('gpr', (True, 2)), ('avx', (None, 3)), ('stack', (None, 5))]
    for L in range(0, 301):
        cd = bytes(rng.getrandbits(8) for _ in range(L))
        offs = list(range(0, L + 41)) + [L + 1000, (1 << 31) - 1, 1 << 31, (1 << 32) - 1, 1 << 32, (1 << 32) + 3, 1 << 64, U - 1, (1 << 255)]
        for off in offs:
            for loc, live in locs:
                cpu = J.CPU(rng)
                got = J.calldataload(cpu, cd, off, loc, live)
                exp = J.spec_calldataload(cd, off)
                cases += 1
                if cpu.oob: oob += 1
                if got != exp and len(fails) < 20: fails.append({'len': L, 'off': hex(off), 'loc': loc, 'got': hex(got), 'exp': hex(exp)})
    # random words with high limbs set but low 32 bits small, and offsets near the size
    for _ in range(n):
        L = rng.choice([0, 1, 4, 31, 32, 33, 36, 68, 100, 132, 164, 196, 228, 292, 324, 356, 420, 1000, 5000])
        cd = bytes(rng.getrandbits(8) for _ in range(L))
        k = rng.randrange(5)
        if k == 0: off = rng.randrange(L + 64)
        elif k == 1: off = (rng.getrandbits(224) << 32) | rng.randrange(L + 64)
        elif k == 2: off = rng.getrandbits(256)
        elif k == 3: off = (1 << rng.randrange(32, 256)) | rng.randrange(L + 1)
        else: off = (rng.getrandbits(32) << 32) | rng.randrange(L + 1)
        loc, live = rng.choice(locs)
        cpu = J.CPU(rng)
        got = J.calldataload(cpu, cd, off, loc, live); exp = J.spec_calldataload(cd, off); cases += 1
        if cpu.oob: oob += 1
        if got != exp and len(fails) < 20: fails.append({'len': L, 'off': hex(off), 'loc': loc, 'got': hex(got), 'exp': hex(exp)})
    res['calldataload'] = {'cases': cases, 'failures': len(fails), 'firstFailures': fails, 'casesReadingOutsideCalldata': oob}
    # 2. CALLER: random and edge addresses
    fails = 0; c = 0
    edges = [bytes(20), b'\xff' * 20, b'\x80' + bytes(19), bytes(19) + b'\x01', bytes(3) + b'\x01' + bytes(16), bytes(4) + b'\x01' + bytes(15),
             bytes(11) + b'\x01' + bytes(8), bytes(12) + b'\x01' + bytes(7)]
    for i in range(n):
        a = edges[i] if i < len(edges) else bytes(rng.getrandbits(8) for _ in range(20))
        got = J.read_context_address(J.CPU(rng), a, rng.random() < 0.5); c += 1
        if got != int.from_bytes(a, 'big'): fails += 1
    res['caller'] = {'cases': c, 'failures': fails}
    # 3. CALLVALUE: both destinations
    fails = 0; c = 0
    for i in range(n):
        v = [0, 1, U - 1, 1 << 255, 10 ** 18, (1 << 128) - 1][i] if i < 6 else rng.getrandbits(rng.randrange(1, 257))
        be = v.to_bytes(32, 'big')
        for gpr in (True, False):
            got = J.read_context_word(J.CPU(rng), be, gpr); c += 1
            if got != v: fails += 1
    res['callvalue'] = {'cases': c, 'failures': fails}
    # 4. RETURNDATASIZE: the 64 bit field read through its low 32 bits
    fails = 0; c = 0
    for v in list(range(0, 4097)) + [rng.randrange(1 << 24) for _ in range(n // 10)] + [M - 1 for M in [1 << 32]]:
        got = J.read_context_uint32_to_word(J.CPU(rng), v); c += 1
        if got != v: fails += 1
    res['returndatasize'] = {'cases': c, 'failures': fails,
                             'note': 'sizes below 2^32; the field is uint64 and only its low 32 bits are read, which cannot matter below 2^32 bytes of return data'}
    # 5. bswap_to_ymm alone
    fails = 0
    for _ in range(n):
        v = rng.getrandbits(256)
        if J.bswap_to_ymm(v) != J.bswap256(v): fails += 1
    res['bswap_to_ymm'] = {'cases': n, 'failures': fails}
    res['coverage'] = J.COV
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps({k: (v if k == 'coverage' else {kk: vv for kk, vv in v.items() if kk != 'firstFailures'}) for k, v in res.items()}, indent=1))
    print('first calldataload failures:', res['calldataload']['firstFailures'][:5])


main()
