# L-787 / L-731: run the MUL, SIGNEXTEND, EQ (and ISZERO, NOT) handlers of the respected kona-client prestate,
# located through its dispatch table, in the cycle 13 MIPS64 emulator, on battery, targeted and random vectors (seed 19).
# Lead L-731: locate and run the arithmetic opcode handlers of the respected kona-client prestate
# (the image cycle 14 ran the shift handlers of) in the cycle 13 MIPS64 emulator. Candidates are
# function entries (the instruction after a preceding `jr ra` and its delay slot) whose body loads
# the stack length at 0x30($a0) within the first 64 instructions. Each candidate is run on two and
# three word stacks and its output compared with the reference semantics of tools/opdiff/battery.py.
# Usage: python3 -I find_handlers.py <prestate.bin> <tools/opdiff dir> <cycle13 kona dir> <out.json>
import sys, struct, json, random, collections
pre, opdir, c13, outp = sys.argv[1:5]
sys.path.insert(0, c13); sys.path.insert(1, opdir)
from mips64emu import Emu, Fault, RET_MAGIC
import battery
MASK = (1 << 256) - 1
class PagedMem:
    def __init__(self, pages): self.p = {k: bytearray(v) for k, v in pages.items()}
    def get(self, a, d=0):
        pg = self.p.get(a >> 12)
        return pg[a & 4095] if pg is not None else d
    def __getitem__(self, a): return self.get(a)
    def __setitem__(self, a, v):
        pg = self.p.get(a >> 12)
        if pg is None: pg = self.p[a >> 12] = bytearray(4096)
        pg[a & 4095] = v
    def __contains__(self, a): return (a >> 12) in self.p
d = open(pre, 'rb').read(); npages = struct.unpack('>Q', d[1:9])[0]; pages = {}; o = 9
for k in range(npages):
    idx = struct.unpack('>Q', d[o:o + 8])[0]; pages[idx] = d[o + 8:o + 8 + 4096]; o += 4104
INTERP, STACK, SP = 0x7000_0000, 0x7100_0000, 0x7f00_0000
E = Emu.__new__(Emu); E.faults = set(); E.sym = {}; E.decode_cache = {}; E.steps = 0
E.mem = PagedMem(pages); BASE = E.mem.p
def word(a):
    pg = BASE.get(a >> 12)
    return struct.unpack('>I', bytes(pg[(a & 4095):(a & 4095) + 4]))[0] if pg else None
def run(entry, words, gas=10**12):
    E.mem.p = dict(BASE)
    for pg in (INTERP >> 12, STACK >> 12, (SP >> 12) - 1, (SP >> 12) - 2, (SP >> 12) - 3): E.mem.p[pg] = bytearray(4096)
    E.wr(INTERP + 0x1c1, 1, 30); E.wr(INTERP + 0x28, 8, STACK); E.wr(INTERP + 0x30, 8, len(words))
    for i, w in enumerate(words): E.put256(STACK + 32 * i, w)
    R = [0] * 32; R[4] = INTERP; R[29] = SP; R[31] = RET_MAGIC; R[25] = entry
    E.run(R, entry, 200000)
    return E.get256(STACK), E.rd(INTERP + 0x30, 8)

import targeted
VB = battery.vectors(); VT = targeted.vectors()
ENTRIES = {'MUL': 0x12005fdb8, 'SIGNEXTEND': 0x12005f588, 'EQ': 0x12006aa18, 'ISZERO': 0x12006b858, 'NOT': 0x12006ad10}
ARITY = {'ISZERO': 1, 'NOT': 1}
res = {'table': '0x1203f4760 (8-byte big-endian handler pointers indexed by opcode; SUB and EXP entries equal the cycle 16 handlers)', 'sets': {}}
rnd2 = random.Random(19)
for op, ent in ENTRIES.items():
    V = [t for t in VB + VT if t[0] == op]
    V += [(op, rnd2.getrandbits(256), rnd2.getrandbits(256), 0) for _ in range(20000)]
    if op == 'SIGNEXTEND':
        V += [(op, k, rnd2.getrandbits(256), 0) for k in list(range(0, 40)) * 200]
        V += [(op, (1 << s_) + d_, rnd2.getrandbits(256), 0) for s_ in (32, 64, 128, 192, 255) for d_ in (0, 1, 2, 15)]
    if op == 'EQ':
        V += [(op, x, x ^ (1 << b_), 0) for b_ in range(256) for x in (rnd2.getrandbits(256), 0)]
        V += [(op, x, x, 0) for x in (rnd2.getrandbits(256) for _ in range(2000))]
    bad = []; n = 0; err = 0
    for t in V:
        _, a_, b_, c_ = t[:4]
        ws = [a_] if ARITY.get(op) == 1 else [b_, a_]
        try: got, ln = run(ent, ws)
        except Exception as e: err += 1; continue
        n += 1
        if got != battery.reference(op, a_, b_, c_, b'') or ln != 1: bad.append([hex(a_), hex(b_), hex(got), ln])
    res['sets'][op] = {'handler': hex(ent), 'ran': n, 'mismatch': len(bad), 'emuFaults': err, 'mismatches': bad[:200]}
    print(op, {k: v for k, v in res['sets'][op].items() if k != 'mismatches'}, bad[:2], flush=True)
# planted-fault check: same harness with a wrong reference must fail
pf = sum(1 for t in [x for x in VB if x[0] == 'MUL'][:200] if run(ENTRIES['MUL'], [t[2], t[1]])[0] != ((t[1] * t[2] + 1) & MASK))
res['plantedFaultDetected'] = pf
print('planted fault (MUL reference off by one) detected on', pf, 'of 200', flush=True)
json.dump(res, open(outp, 'w'), indent=1)
