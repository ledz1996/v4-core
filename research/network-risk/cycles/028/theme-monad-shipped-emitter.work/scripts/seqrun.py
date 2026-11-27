"""Cycle 28, Task 2 (second piece). Run the inline sequences that the v0.16.7 emitter writes for the two MULMOD sites
with a power-of-two literal modulus (pc 0x576a = 22378, modulus 2^128; pc 0x586f = 22639, modulus 2^96) in the x86
model (x86emu.py of cycle 27), taken from the clang harness listing pm-asm-0.16.7.txt, and compare the result words
with (a * b) % 2^k in Python. Operands: products of the pool-math edge words (every 2^j, 2^j - 1, 2^j + 1 for j < 256,
the PoolManager's literals, the Q96 and Q128 neighbourhoods, uint128 / uint160 extremes) and random words, seed 2829.
Planted faults: one instruction per sequence.
usage: python3 -I seqrun.py <pm-asm> <x86emu dir> <PoolManager.json> <out.json> [pairs]"""
import sys, os, re, json, random
ASM, EMU, PMJ, OUTF = sys.argv[1:5]; NPAIR = int(sys.argv[5]) if len(sys.argv) > 5 else 100000
sys.path.insert(0, EMU)
from x86emu import CPU, Prog, Stop
M = (1 << 256) - 1; M64 = (1 << 64) - 1
lines = open(ASM).read().splitlines()
def seq(pc):
    out = []; on = False
    for ln in lines:
        m = re.match(r'^//\s+0x([0-9a-f]+): (\w+)', ln)
        if m:
            if on: break
            on = int(m.group(1), 16) == pc and m.group(2) == 'MULMOD'; continue
        if on and not ln.startswith('//'): out.append(ln)
    return out
R32 = {'r%dd' % i for i in range(8, 16)} | {'eax', 'ecx', 'edx', 'ebx', 'esi', 'edi'}
def translate(ins):
    """asmjit text -> objdump intel text that x86emu reads. asmjit prints a 32-bit memory load as 'qword ptr'
    after a 32-bit register (e.g. mov r8d, qword ptr [rbp-88]); the operand size is that of the register."""
    out = []
    for i, s in enumerate(ins):
        mn, _, rest = s.partition(' ')
        ops = [o.strip() for o in rest.split(',')]
        if len(ops) == 2 and ops[0] in R32 and 'ptr' in ops[1]: ops[1] = ops[1].replace('qword ptr', 'DWORD PTR')
        ops = [o.replace('qword ptr', 'QWORD PTR') for o in ops]
        ops = [re.sub(r'([+-])(\d+)\]', lambda m: '%s0x%x]' % (m.group(1), int(m.group(2))), o) for o in ops]
        out.append('  %x:\t%s %s' % (0x1000 + 4 * i, mn, ','.join(ops)))
    out.append('  %x:\tret' % (0x1000 + 4 * len(ins)))
    return '\n'.join(out) + '\n'
SITES = {0x576a: 128, 0x586f: 96}
RBP = 0x7ffff0100000
def runseq(p, end, a, b):
    c = CPU(p); c.r['rbp'] = RBP; c.r['rsp'] = 0x7ffff0080000
    for i in range(4):
        c.write(RBP - 128 + 8 * i, 8, (a >> (64 * i)) & M64); c.write(RBP - 96 + 8 * i, 8, (b >> (64 * i)) & M64)
    for k in ('r8', 'r9', 'r10', 'r11'): c.r[k] = 0xdeadbeefdeadbeef
    pc = 0x1000
    while pc != end: pc = c.step(pc)
    return c.r['r10'] | c.r['r11'] << 64 | c.r['r8'] << 128 | c.r['r9'] << 192
code = bytes.fromhex(json.load(open(PMJ))['runtime'].removeprefix('0x'))
lits = set(); i = 0
while i < len(code):
    op = code[i]
    if 0x60 <= op <= 0x7f: n = op - 0x5f; lits.add(int.from_bytes(code[i + 1:i + 1 + n], 'big')); i += 1 + n
    else: i += 1
edge = set(lits)
for j in range(256): edge |= {1 << j, (1 << j) - 1, ((1 << j) + 1) & M}
for q in (96, 128, 160, 192):
    for d in range(-3, 4): edge.add(((1 << q) + d) & M)
edge = sorted(edge)
rnd = random.Random(2829)
pairs = [(x, y) for x in edge[::3] for y in edge[::7]]
rnd.shuffle(pairs); pairs = pairs[:NPAIR // 2]
pairs += [(rnd.getrandbits(rnd.choice((64, 96, 128, 160, 192, 256))), rnd.getrandbits(rnd.choice((64, 96, 128, 160, 192, 256)))) for _ in range(NPAIR // 2)]
res = {'seed': 2829, 'pairsPerSite': len(pairs), 'sites': {}}
for pc, k in SITES.items():
    ins = seq(pc); txt = translate(ins); end = 0x1000 + 4 * len(ins)
    p = Prog(txt); bad = []
    for a, b in pairs:
        try: got = runseq(p, end, a, b)
        except Stop as e: got = str(e)
        if got != (a * b) % (1 << k): bad.append({'a': hex(a), 'b': hex(b), 'got': hex(got) if isinstance(got, int) else got, 'want': hex((a * b) % (1 << k))})
    # planted fault: drop the cross term a0*b1 (the 'add r11..., r8...' line)
    j = max(i for i, s in enumerate(ins) if s.startswith('add r11'))
    pf = Prog(translate(ins[:j] + ['nop'] + ins[j + 1:])); fb = 0
    for a, b in pairs[:2000]:
        if runseq(pf, end, a, b) != (a * b) % (1 << k): fb += 1
    res['sites']['0x%x' % pc] = {'pc': pc, 'modulusLog2': k, 'instructions': ins, 'cases': len(pairs), 'mismatches': len(bad), 'records': bad,
                                 'plant': {'removed': ins[j], 'cases': 2000, 'mismatches': fb}}
    print(hex(pc), k, len(ins), 'mismatches', len(bad), 'plant', fb)
json.dump(res, open(OUTF, 'w'), indent=1)
