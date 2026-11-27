"""Cycle 33. Read from the shipped monad 0.16.7 ELF (never executed): the negate_comparison lookup table CSWTCH.2401
at 0x810800 used by jumpi_keep/spill_fallthrough_stack, and the switch table of Emitter::conditional_jmp at
0x8107c0, and map each Comparison to the asmjit instruction id the table arm passes to _emitI.
usage: python3 -I cctables.py <out.json>"""
import sys, json, re, struct
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/029/theme-monad-gcc-literal-folds.work/scripts')
from emdrv import IMG, IDN
COMP = ['Below', 'AboveEqual', 'Above', 'BelowEqual', 'Less', 'GreaterEqual', 'Greater', 'LessEqual', 'Equal', 'NotEqual']
NEG = {'Below': 'AboveEqual', 'AboveEqual': 'Below', 'Above': 'BelowEqual', 'BelowEqual': 'Above', 'Less': 'GreaterEqual',
       'GreaterEqual': 'Less', 'Greater': 'LessEqual', 'LessEqual': 'Greater', 'Equal': 'NotEqual', 'NotEqual': 'Equal'}
JCC = {'Below': 'jb', 'AboveEqual': 'jae', 'Above': 'ja', 'BelowEqual': 'jbe', 'Less': 'jl', 'GreaterEqual': 'jge',
       'Greater': 'jg', 'LessEqual': 'jle', 'Equal': 'je', 'NotEqual': 'jne'}
def u32(a): return sum(IMG.byte(a + i) << (8 * i) for i in range(4))
def s32(a): v = u32(a); return v - (1 << 32) if v >> 31 else v
D = '/home/user/v4-core/research/network-risk/cycles/027/theme-monad-package-read.work/dl/dis/monad-0.16.7.s'
# conditional_jmp body text
txt = []; on = False
for l in open(D):
    if l.startswith('000000000036f430 <'): on = True; continue
    if on:
        if not l.strip(): break
        txt.append(l)
arms = {}
for i, l in enumerate(txt):
    m = re.match(r'\s+([0-9a-f]+):\s+mov\s+esi,0x([0-9a-f]+)', l)
    if m: arms[int(m.group(1), 16)] = int(m.group(2), 16)
out = {'negTable': [], 'condTable': [], 'ok': True}
for k, c in enumerate(COMP):
    n = u32(0x810800 + 4 * k)
    got = COMP[n] if n < 10 else hex(n)
    ok = got == NEG[c]; out['ok'] &= ok
    out['negTable'].append({'comp': c, 'raw': n, 'negated': got, 'ok': ok})
for k, c in enumerate(COMP):
    tgt = (0x8107c0 + s32(0x8107c0 + 4 * k)) & ((1 << 64) - 1)
    iid = arms.get(tgt)
    nm = IDN.get(hex(iid), '?').lower() if iid is not None else None
    ok = nm == JCC[c]; out['ok'] &= ok
    out['condTable'].append({'comp': c, 'target': hex(tgt), 'instId': hex(iid) if iid else None, 'mnemonic': nm, 'want': JCC[c], 'ok': ok})
json.dump(out, open(sys.argv[1], 'w'), indent=1)
for r in out['negTable']: print(r)
for r in out['condTable']: print(r)
print('ok', out['ok'])
