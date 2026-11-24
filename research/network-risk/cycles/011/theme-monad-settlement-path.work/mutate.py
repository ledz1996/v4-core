"""Plants faults into settlejit.py source text and checks that the CALLDATALOAD cases see each one.
Usage: python3 -I mutate.py <out.json>"""
import sys, os, json, random, types
here = os.path.dirname(os.path.abspath(__file__)); src = open(os.path.join(here, 'settlejit.py')).read()
MUT = [('if rsi < 25:', 'if rsi < 24:'), ('if rsi > 16:', 'if rsi >= 16:'), ('ecx = ((16 - rsi) << 3) & M32', 'ecx = ((15 - rsi) << 3) & M32'),
       ('if cpu.jl():', 'if cpu.jg():'), ("cpu.r['rsi'] = cpu.ld(CTX + OFF_INPUT_SIZE, 4)", "cpu.r['rsi'] = cpu.ld(CTX + OFF_INPUT_SIZE, 2)"),
       ('mask = M64 ^ M32', 'mask = M64 ^ ((1 << 31) - 1)'), ('if lit <= 0x7fffffff:', 'if lit <= 0xffffffff:'),
       ('cpu.r[g[2]] = int.from_bytes(cpu.ld(m, 4)', 'cpu.r[g[2]] = int.from_bytes(cpu.ld(m + 1, 4)'), ('return vpshufb(vpermq(src, 27), BSWAP_CTL)', 'return vpshufb(vpermq(src, 0x1e), BSWAP_CTL)'),
       ('edx = edx >> (ecx & 31)', 'edx = edx >> (ecx & 15)')]
out = []
for a, b in MUT:
    assert src.count(a) == 1, a
    m = types.ModuleType('mut'); exec(compile(src.replace(a, b), 'mut', 'exec'), m.__dict__)
    rng = random.Random(5); bad = 0; n = 0
    for L in range(0, 80):
        cd = bytes(rng.getrandbits(8) for _ in range(L))
        for off in list(range(0, L + 40)) + [(1 << 31) + 5, (1 << 32) + 1]:
            for loc, live in [('lit', None), ('gpr', (True, 0)), ('gpr', (False, 1)), ('avx', (None, 3)), ('stack', (None, 5))]:
                n += 1
                if m.calldataload(m.CPU(rng), cd, off, loc, live) != m.spec_calldataload(cd, off): bad += 1
    for _ in range(2000):
        a20 = bytes(rng.getrandbits(8) for _ in range(20)); n += 1
        if m.read_context_address(m.CPU(rng), a20, False) != int.from_bytes(a20, 'big'): bad += 1
    out.append({'mutation': [a, b], 'cases': n, 'detected': bad})
    print(a, '->', b, bad)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
