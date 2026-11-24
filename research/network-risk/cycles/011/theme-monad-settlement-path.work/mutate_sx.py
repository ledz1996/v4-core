"""Planted faults in the SIGNEXTEND transcription; each must be seen. Usage: python3 -I mutate_sx.py <out.json>"""
import sys, os, json, random, types
here = os.path.dirname(os.path.abspath(__file__)); src = open(os.path.join(here, 'settlejit.py')).read()
MUT = [('0x06050403020100ff, 0x0e0d0c0b0a090807', '0x0605040302010000, 0x0e0d0c0b0a090807'), ('>> 2                     # vpsrld', '>> 3                     # vpsrld'),
       ('for lim, edge in ((0, 8), (1, 16), (2, 24)):', 'for lim, edge in ((0, 8), (1, 16), (2, 23)):'), ('zf = (ix & ((U - 1) << 5)) == 0', 'zf = (ix & ((U - 1) << 6)) == 0'),
       ('if rax > q: rax = q', 'if rax > q + 1: rax = q'), ('if below: shift = 63', 'if below: shift = 62')]
out = []
for a, b in MUT:
    assert src.count(a) == 1, a
    m = types.ModuleType('mut'); exec(compile(src.replace(a, b), 'mut', 'exec'), m.__dict__)
    rng = random.Random(3); bad = 0; n = 0
    for ix in list(range(40)) + [1 << 64, (1 << 64) + 1]:
        for _ in range(30):
            x = rng.getrandbits(256)
            for loc in ('gpr', 'avx', 'stack'):
                for f in (m.signextend_avx, m.signextend_gpr, m.signextend_mem):
                    n += 1
                    try: bad += f(m.bounded_rax(m.CPU(rng), loc, ix, False, True), x) != m.spec_signextend(ix, x)
                    except IndexError: bad += 1  # an index above 31 reads past the word
    out.append({'mutation': [a, b], 'cases': n, 'detected': bad}); print(a, '->', b, bad)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
