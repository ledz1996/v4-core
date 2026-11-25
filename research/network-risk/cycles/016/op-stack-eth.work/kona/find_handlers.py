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
# text pages: those around the known shift handler 0x12006ad70
lo = 0x120000000; hi = 0x120000000 + 0x600000
JRRA = 0x03e00008
LD30 = lambda w: (w >> 26) == 0x37 and ((w >> 21) & 31) == 4 and (w & 0xFFFF) == 0x30
ents = set(); last_ret = None; a = lo
loads = []
while a < hi:
    w = word(a)
    if w is None: a = (a | 4095) + 1; last_ret = None; continue
    if w == JRRA: last_ret = a
    if LD30(w) and last_ret is not None and a - (last_ret + 8) <= 64 * 4: ents.add(last_ret + 8)
    a += 4
ents = sorted(ents)
print('candidates', len(ents), flush=True)
def run(entry, words, gas=10**12):
    E.mem.p = dict(BASE)
    for pg in (INTERP >> 12, STACK >> 12, (SP >> 12) - 1, (SP >> 12) - 2, (SP >> 12) - 3): E.mem.p[pg] = bytearray(4096)
    E.wr(INTERP + 0x1c1, 1, 30); E.wr(INTERP + 0x28, 8, STACK); E.wr(INTERP + 0x30, 8, len(words))
    for i, w in enumerate(words): E.put256(STACK + 32 * i, w)
    R = [0] * 32; R[4] = INTERP; R[29] = SP; R[31] = RET_MAGIC; R[25] = entry
    E.run(R, entry, 200000)
    return E.get256(STACK), E.rd(INTERP + 0x30, 8)
OPS2 = ['ADD','MUL','SUB','DIV','SDIV','MOD','SMOD','EXP','SIGNEXTEND','LT','GT','SLT','SGT','EQ','AND','OR','XOR','BYTE','SHL','SHR','SAR']
OPS3 = ['ADDMOD','MULMOD']
rnd = random.Random(16)
def probes():
    P = [(rnd.getrandbits(256), rnd.getrandbits(256), rnd.getrandbits(256)) for _ in range(3)]
    P += [(5, rnd.getrandbits(256), rnd.getrandbits(255) | 1), (30, (1 << 255) | 77, 12345), (3, 7, 11)]
    return P
PR = probes()
found = collections.defaultdict(list)
for ent in ents:
    for arity, ops in ((2, OPS2), (3, OPS3)):
        outs = []
        for a_, b_, c_ in PR:
            ws = [c_, b_, a_] if arity == 3 else [b_, a_]   # top of stack is the last word
            try: outs.append(run(ent, ws))
            except Exception: outs.append(None)
        if any(x is None for x in outs): continue
        for op in ops:
            if all(r[0] == battery.reference(op, a_, b_, c_, b'') and r[1] == 1 for r, (a_, b_, c_) in zip(outs, PR)):
                found[op].append(hex(ent))
print('identified', dict(found), flush=True)
res = {'candidates': len(ents), 'identified': dict(found), 'sets': {}}
# vectors: battery and targeted for each identified op, plus random
import targeted
VB = battery.vectors(); VT = targeted.vectors()
for op, el in found.items():
    ent = int(el[0], 16); arity = 3 if op in OPS3 else 2
    V = [t for t in VB + VT if t[0] == op]
    bad = []; n = 0; err = 0
    for t in V:
        _, a_, b_, c_ = t[:4]
        ws = [c_, b_, a_] if arity == 3 else [b_, a_]
        try: got, ln = run(ent, ws)
        except Exception: err += 1; continue
        n += 1
        if got != battery.reference(op, a_, b_, c_, b'') or ln != 1: bad.append([hex(a_), hex(b_), hex(c_), hex(got)])
    res['sets'][op] = {'handler': hex(ent), 'ran': n, 'mismatch': len(bad), 'emuFaults': err, 'first': bad[:3]}
    print(op, res['sets'][op], flush=True)
json.dump(res, open(outp, 'w'), indent=1)
