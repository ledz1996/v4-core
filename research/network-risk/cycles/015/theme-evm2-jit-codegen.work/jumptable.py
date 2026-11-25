"""Transcription of build_dynamic_jump_table (translate/mod.rs 2102-2172) checked on the
PoolManager runtime: every pc from 0 to max_pc + 64 and 2^64 - 1 must dispatch to the JUMPDEST at
that pc when it is a valid jump destination and to the invalid-jump block otherwise.
Usage: python3 jumptable.py <PoolManager.json> [--plant]"""
import sys, json
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools', 'opdiff'))
from pyevm import jumpdests
code = bytes.fromhex(json.load(open(sys.argv[1]))['runtime'].removeprefix('0x'))
plant = '--plant' in sys.argv
J = sorted(jumpdests(code))
max_pc = J[-1]
table = [[0, 0] for _ in range(max_pc // 32 + 1)]
targets = {}
for i, pc in enumerate(reversed(J)):
    table[pc // 32][1] |= 1 << (31 - pc % 32)
    targets[i] = pc
rank = 0
for pair in reversed(table):
    pair[0] = (rank - 1) & 0xffffffff
    rank += bin(pair[1]).count('1')
def i32(x): x &= 0xffffffff; return x - (1 << 32) if x >> 31 else x
bad = 0; n = 0
for pc in list(range(0, max_pc + 65)) + [(1 << 64) - 1, 1 << 40]:
    n += 1
    if not pc <= max_pc: got = None
    else:
        base, bitmap = table[pc >> 5]
        bits = (bitmap << ((pc & 31) if not plant else ((pc + 1) & 31))) & 0xffffffff
        if i32(bits) >= 0: got = None
        else: got = targets.get(i32(i32(base) + bin(bits).count('1')))
    want = pc if pc in set(J) else None
    if got != want: bad += 1
print(json.dumps({'validJumpdests': len(J), 'maxPc': max_pc, 'pcsTested': n, 'mismatches': bad, 'plant': plant}))
