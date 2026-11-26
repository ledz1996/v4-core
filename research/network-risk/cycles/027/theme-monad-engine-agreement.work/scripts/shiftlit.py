"""Cycle 27 (Task 4): SHL, SHR and SAR of a literal value by a non-literal shift, the case that v0.16.7's emitter
compiles with the new shift_literal_by_non_literal (emitter.cpp:5253-5326 at v0.16.7) and v0.16.5 through
mov_literal_to_avx_reg + shift_avx_reg_by_non_literal. One contract per batch of literals; the shift comes from
CALLDATALOAD directly, through AND with 0xffff..ff (a general register), and through MSTORE/MLOAD. Each transaction
carries one shift word. Both engines of the fixed harness at both tags against Python integers. Seed 2727.
Usage: python3 shiftlit.py <outdir>"""
import sys, os, random, subprocess, re, json
W27 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
M = (1 << 256) - 1
rnd = random.Random(2727)
lits = [0, 1, 2, 0xff, 1 << 255, M, M >> 1, (1 << 255) | 1, 0x8000000000000000, 1 << 64, (1 << 128) - 1, 0xa0 << 248]
# the literals the PoolManager shifts by a variable amount: BitMath.sol:22, BitMath.sol:40-42, TickBitmap.sol:73,110 (1), :97 (max), block 0x40d7 (0xffffffff << 224)
lits += [0x8421084210842108cc6318c6db6d54be, 0x8040405543005266443200005020610674053026020000107506200176117077, 0xffffffff << 224]
lits += [rnd.getrandbits(256) for _ in range(8)] + [rnd.getrandbits(256) | (1 << 255) for _ in range(4)]
shifts = list(range(0, 301)) + [511, 512, 1 << 64, (1 << 64) + 1, (1 << 64) + 7, 1 << 128, 1 << 255, M, (1 << 200) + 3, 256 + (1 << 32), (1 << 32) + 1]
OPS = {'SHL': 0x1b, 'SHR': 0x1c, 'SAR': 0x1d}
def ref(op, s, v):
    if op == 'SHL': return (v << s) & M if s < 256 else 0
    if op == 'SHR': return v >> s if s < 256 else 0
    sv = v - (1 << 256) if v >> 255 else v
    return (sv >> min(s, 256)) & M
def push(n, w): b = n.to_bytes(w, 'big'); return bytes([0x5f + w]) + b
def build(lits):
    c = bytearray(); slot = 0; layout = []
    c += push(0, 1) + bytes([0x35]) + push(0x10000, 3) + bytes([0x52])  # mstore(0x10000, calldataload(0))
    for form in ('cd', 'and', 'mload'):
        for L in lits:
            for op, code in OPS.items():
                c += push(L, 32)
                if form == 'cd': c += push(0, 1) + bytes([0x35])
                elif form == 'and': c += push(0, 1) + bytes([0x35]) + push(M, 32) + bytes([0x16])
                else: c += push(0x10000, 3) + bytes([0x51])
                c += bytes([code]) + push(slot * 32, 2) + bytes([0x52]); layout.append((form, L, op)); slot += 1
    c += push(slot * 32, 2) + push(0, 1) + bytes([0xf3])
    return bytes(c), layout
code, layout = build(lits)
A = 0xc0de0000000000000000000000000000000000c1; EOA = 0xa11ce
open(os.path.join(out, 'w.txt'), 'w').write(f'code {A:040x} {code.hex()}\n')
with open(os.path.join(out, 's.txt'), 'w') as f:
    for s in shifts: f.write(f'SCEN s{s:x}\nTX {EOA:040x} {A:040x} 00 30000000 {s:064x}\n')
summary = {'seed': 2727, 'literals': len(lits), 'shifts': len(shifts), 'resultsPerTx': len(layout), 'codeBytes': len(code)}
bad = []
for ver in ('0.16.5', '0.16.7'):
    p = subprocess.run([os.path.join(W27, 'build', ver, 'hxf'), os.path.join(out, 'w.txt'), os.path.join(out, 's.txt'), '-v'], capture_output=True, text=True)
    open(os.path.join(out, f'out-{ver}.txt'), 'w').write(p.stdout)
    blocks = re.split(r'(?m)^(?=SAME |DIFF )', p.stdout); n = eq = same = 0
    for blk in blocks:
        m = re.match(r'(SAME|DIFF) s([0-9a-f]+)', blk)
        if not m: continue
        s = int(m.group(2), 16); same += m.group(1) == 'SAME'
        outs = re.findall(r'tx 0 status=(\w+) gasleft=\d+ out=([0-9a-f]*)', blk)
        for eng, (st, o) in zip(('interp', 'native'), outs):
            words = [int(o[i:i + 64], 16) for i in range(0, len(o), 64)]
            for (form, L, op), wv in zip(layout, words):
                n += 1
                if wv == ref(op, s, L): eq += 1
                else: bad.append({'ver': ver, 'engine': eng, 'shift': hex(s), 'form': form, 'lit': hex(L), 'op': op, 'got': hex(wv), 'want': hex(ref(op, s, L))})
            if st != 'success' or len(words) != len(layout): bad.append({'ver': ver, 'engine': eng, 'shift': hex(s), 'status': st, 'words': len(words)})
    summary[ver] = {'scenarios': len(blocks) - 1, 'SAME': same, 'words': n, 'equalPython': eq}
summary['mismatches'] = bad[:200]; summary['mismatchCount'] = len(bad)
json.dump(summary, open(os.path.join(out, 'summary.json'), 'w'), indent=1)
print({k: v for k, v in summary.items() if k != 'mismatches'})
