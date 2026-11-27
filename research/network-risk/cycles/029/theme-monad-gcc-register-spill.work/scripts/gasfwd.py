"""Cycle 29 Task 3 (L-1170). Gas that a CALL and a STATICCALL forward, interpreter against native code, in the
cycle 27 fixed harness (clang build of the v0.16.7 emitter, MonadTraits<MONAD_TEN>), on callees that return GAS.
The caller makes the call shapes of src/types/Currency.sol:48 (CALL gas() with value), :73 (CALL gas() no value),
src/libraries/Hooks.sol:134 (CALL gas()) and Currency.sol:94 (STATICCALL gas()), plus literal gas words at the
edges of the 63/64 rule and the int64 clamp, and stores every success flag, returned GAS word and its own GAS.
Seed: random.Random(29029). Usage: python3 -I gasfwd.py <outdir>"""
import sys, os, subprocess, random, re, json
HX = '/home/user/v4-core/research/network-risk/cycles/027/theme-monad-engine-agreement.work/build/0.16.7/hxf'
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
C, E1, E2, EOA = 0xc0 << 152 | 1, 0xe0 << 152 | 1, 0xe0 << 152 | 2, 0xaa << 152 | 7
def push(v):
    if v == 0: return b'\x5f'
    b = v.to_bytes((v.bit_length() + 7) // 8, 'big'); return bytes([0x5f + len(b)]) + b
# E1: GAS at the start of its only block.  E2: GAS in the middle of a longer block, then more work in the same block.
e1 = bytes.fromhex('5a5f5260205ff3')
e2 = bytes.fromhex('6001600201505a600160020150600160020150') + bytes.fromhex('5f5260205ff3')
LIT = [0, 1, 2299, 2300, 2301, 10000, 99999, 100000, (1 << 63) - 1, 1 << 63, 1 << 64, (1 << 64) + 5, 1 << 255, (1 << 256) - 1]
code = b''; slot = 0
def st(): global code, slot; code += push(slot) + b'\x55'; slot += 1   # SSTORE(slot, top)
def call(op, gas, tgt, val):
    global code
    code += push(32) + push(0) + push(0) + push(0)
    if op == 0xf1: code += push(val)
    code += push(tgt) + (b'\x5a' if gas is None else push(gas)) + bytes([op])
    st(); code += push(0) + b'\x51'; st(); code += push(0) + push(0) + b'\x52'
for tgt in (E1, E2):
    code += b'\x5a'; st()
    call(0xf1, None, tgt, 1)   # Currency.sol:48 shape
    call(0xf1, None, tgt, 0)   # Currency.sol:73 and Hooks.sol:134 shape
    call(0xfa, None, tgt, 0)   # Currency.sol:94 shape
    for g in LIT:
        call(0xf1, g, tgt, 0); call(0xfa, g, tgt, 0); call(0xf1, g, tgt, 1)
code += b'\x00'
world = f'code {C:040x} {code.hex()}\ncode {E1:040x} {e1.hex()}\ncode {E2:040x} {e2.hex()}\nbal {C:040x} {10**6:064x}\n'
rnd = random.Random(29029)
levels = [21000 + x for x in (30000, 60000, 100000, 200000, 400000, 800000, 1600000, 3000000, 30000000, 150000000)]
levels += sorted(rnd.randrange(40000, 3000000) for _ in range(150))
scen = ''.join(f'SCEN g{g}\nTX {EOA:040x} {C:040x} 00 {g} 00\n' for g in levels)
open(os.path.join(out, 'world.txt'), 'w').write(world); open(os.path.join(out, 'scen.txt'), 'w').write(scen)
p = subprocess.run([HX, os.path.join(out, 'world.txt'), os.path.join(out, 'scen.txt'), '-v'], capture_output=True, text=True)
open(os.path.join(out, 'hx-stdout.txt'), 'w').write(p.stdout + '\n#stderr\n' + p.stderr[-4000:])
same = re.findall(r'^(SAME|DIFF) (\S+)', p.stdout, re.M)
st_ = re.findall(r'tx 0 status=(\w+) gasleft=(\d+)', p.stdout)
print('rc', p.returncode, 'scenarios', len(same), 'DIFF', [n for s, n in same if s == 'DIFF'], 'slots', slot, 'codelen', len(code))
print(p.stdout.splitlines()[-1] if p.stdout else p.stderr[-500:])
json.dump({'seed': 29029, 'levels': levels, 'slots': slot, 'results': same, 'status_counts': {k: sum(1 for s, _ in st_ if s == k) for k in set(s for s, _ in st_)}}, open(os.path.join(out, 'summary.json'), 'w'))
