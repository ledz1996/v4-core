# Lead L-695: run the SHL, SHR and SAR opcode handlers of the respected kona-client prestate itself
# (0x03e5a548...37c9, all 1,244 memory pages as published) in the Cannon-semantics MIPS64 emulator of cycle 13.
# The handlers were located by pattern in the text segment (no symbols are in the image): each loads the
# spec byte at 0x1c1, the stack length at 0x30 and the stack data pointer at 0x28 of the interpreter in $4,
# checks the top word < 256 and writes four limbs to the new top. Which one is SHL, SHR or SAR is found
# by running them, then every shift vector of tools/opdiff/targeted.py and battery.py plus every shift
# amount 0..300 on 64 values is checked against the reference.
# Usage: python3 -I run_real.py <prestate.bin> <tools/opdiff dir> <cycle13 kona dir> <out.json> [fault ...]
import sys, os, struct, json, random, collections
pre, opdir, c13, outp = sys.argv[1:5]; faults = sys.argv[5:]
sys.path.insert(0, c13); sys.path.insert(1, opdir)
import mips64emu
from mips64emu import Emu, Fault, RET_MAGIC
import targeted, battery
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
assert not any((a << 12) >> 24 in (0x70, 0x71, 0x7e, 0x7f) for a in pages)
E = Emu.__new__(Emu); E.faults = set(faults); E.sym = {}; E.decode_cache = {}; E.steps = 0
E.mem = PagedMem(pages); BASEPAGES = E.mem.p
CAND = {'H1': 0x12006ad70, 'H2': 0x12006b1a8, 'H3': 0x12006b328}

def run(entry, shift, value):
    E.mem.p = dict(BASEPAGES)  # page table copy; scratch pages are fresh each run
    for pg in (INTERP >> 12, STACK >> 12, (SP >> 12) - 1, (SP >> 12) - 2): E.mem.p[pg] = bytearray(4096)
    E.wr(INTERP + 0x1c1, 1, 30)            # spec id well above the fork that enables shifts
    E.wr(INTERP + 0x28, 8, STACK); E.wr(INTERP + 0x30, 8, 2)
    E.put256(STACK, value); E.put256(STACK + 32, shift)
    R = [0] * 32; R[4] = INTERP; R[29] = SP; R[31] = RET_MAGIC; R[25] = entry
    E.run(R, entry, 100000)
    ln = E.rd(INTERP + 0x30, 8)
    return E.get256(STACK), ln

# 1. identify
probe = [(1, 1 << 200 | 5), (70, (1 << 255) | 12345), (130, MASK)]
ident = {}
for nm, ent in CAND.items():
    outs = [run(ent, s, v) for s, v in probe]
    for op in ('SHL', 'SHR', 'SAR'):
        if all(r[0] == battery.reference(op, s, v, 0, b'') and r[1] == 1 for r, (s, v) in zip(outs, probe)):
            ident[op] = nm
res_ident = dict(ident)
if faults: ident = {'SAR': 'H1', 'SHL': 'H2', 'SHR': 'H3'}  # mapping from the clean run; a planted fault may break the probes
print('identified', res_ident, flush=True)
# 2. vectors
VT = [t for t in targeted.vectors() if t[0] in ('SHL', 'SHR', 'SAR')]
VB = [t for t in battery.vectors() if t[0] in ('SHL', 'SHR', 'SAR')]
rnd = random.Random(14)
vals = [rnd.getrandbits(256) for _ in range(24)] + [rnd.getrandbits(256) | (1 << 255) for _ in range(24)] + \
       [0, 1, MASK, 1 << 255, (1 << 255) - 1, MASK >> 64, MASK >> 128, MASK >> 192, (MASK << 64) & MASK, (MASK << 128) & MASK,
        (MASK << 192) & MASK, 0x5555555555555555555555555555555555555555555555555555555555555555, 0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,
        (1 << 128) - 1 | (1 << 255), 1 << 64, 1 << 127]
VX = [(op, s, v, 0) for op in ('SHL', 'SHR', 'SAR') for s in range(0, 301) for v in vals]
res = {'prestate': '0x03e5a54835d39c1d83b198314473e1f111c3539c04f65c3e8a9b8ccebe3737c9', 'handlers': {k: hex(CAND[v]) for k, v in ident.items()},
       'faults': faults, 'sets': {}}
for name, V in (('targeted', VT), ('battery', VB), ('exhaustiveAmounts0to300', VX)):
    if faults: V = V[::10]
    bad = []; per = collections.Counter(); err = 0
    for op, s, v, _ in V:
        if op not in ident: continue
        try: got, ln = run(CAND[ident[op]], s, v)
        except Fault as e: err += 1; continue
        per[op] += 1
        if got != battery.reference(op, s, v, 0, b'') or ln != 1: bad.append([op, hex(s), hex(v), hex(got), ln])
    res['sets'][name] = {'ran': sum(per.values()), 'perOp': dict(per), 'mismatch': len(bad), 'emuFaults': err, 'first': bad[:5]}
    print(name, res['sets'][name], flush=True)
json.dump(res, open(outp, 'w'), indent=1)
