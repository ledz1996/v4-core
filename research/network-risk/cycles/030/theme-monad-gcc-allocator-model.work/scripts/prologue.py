"""Cycle 30, Task 1: Emitter::block_prologue (0x392cd0) of the gcc 15.2.0 build in the x86 model, for a block that
is not a jump destination and with runtime tracing off. It emits the EVM stack bound checks. For every pair of
min_delta and max_delta and both did_* flags the recorded instructions must be: jmp to the error label when
max_delta - min_delta > 1024; otherwise cmp [rsp+48], -min_delta with jb when min_delta decreased, and
cmp [rsp+48], 1024 - max_delta with ja when max_delta increased (emitter.cpp:1325-1360 at v0.16.7).
usage: python3 -I prologue.py <outdir>"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from allocdrv import *
OUT = sys.argv[1]
bad = []; n = 0
vals = list(range(-1030, -1000)) + list(range(-40, 41)) + [-1024, -1023, -512, 0, 1, 1023, 1024, 1025]
for mind in vals:
    for maxd in [mind + k for k in (0, 1, 2, 17, 1023, 1024, 1025, 1026)] + [0, 1024]:
        if maxd < mind: continue
        for dmin in (0, 1):
            for dmax in (0, 1):
                m = Model([0x392cd0], {})
                c = m.c
                c.write(E + 0x4c0, 8, 0); c.write(E + 0x4b8, 8, 0); c.write(E + 0x3e0, 1, 0); c.write(E + 0x180, 1, 0)
                c.write(S + 0xc, 4, mind & 0xffffffff); c.write(S + 0x10, 4, maxd & 0xffffffff)
                c.write(S + 0x18, 1, dmin); c.write(S + 0x19, 1, dmax)
                blk = m.alloc(0x40); c.write(blk + 0x28, 8, 0x1234)
                r = c.call(0x392cd0, [E, blk], maxsteps=100000) & 0xff
                got = [(mn, [optext(o) if o[0] != 'raw' else 'label' for o in ops]) for mn, ops in m.emitted]
                if maxd - mind > 1024: want = [('jmp', ['label'])]; wr = 0
                else:
                    want = []; wr = 1
                    if dmin: want += [('cmp', ['QWORD PTR [rsp+0x30]', hex((-mind) & ((1 << 64) - 1))]), ('jb', ['label'])]
                    if dmax: want += [('cmp', ['QWORD PTR [rsp+0x30]', hex((1024 - maxd) & ((1 << 64) - 1))]), ('ja', ['label'])]
                n += 1
                if got != want or r != wr: bad.append({'min': mind, 'max': maxd, 'dmin': dmin, 'dmax': dmax, 'got': got, 'want': want, 'ret': r})
json.dump({'cases': n, 'bad': bad[:50], 'nBad': len(bad)}, open(os.path.join(OUT, 'prologue.json'), 'w'), indent=0)
print('cases', n, 'bad', len(bad)); print(bad[:3])
