"""Inventory of PoolManager runtime instructions with an opcode the shape census counts, mapped to src/ by the solc source map
(cycles/012/theme-bytecode-coverage.work/srcmap.py). Usage: inv.py <out json>"""
import sys, json, collections
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/012/theme-bytecode-coverage.work')
import srcmap
OPS = {2:'MUL',4:'DIV',5:'SDIV',6:'MOD',7:'SMOD',8:'ADDMOD',9:'MULMOD',10:'EXP',11:'SIGNEXTEND',18:'SLT',19:'SGT',26:'BYTE',27:'SHL',28:'SHR',29:'SAR',0x20:'KECCAK256',0x55:'SSTORE',0x57:'JUMPI',0x5c:'TLOAD',0x5d:'TSTORE',0x5e:'MCOPY'}
inv = []
for pc in srcmap.starts:
    if srcmap.PC2I[pc] >= srcmap.NCODE: break
    op = srcmap.code[pc]
    if op in OPS: inv.append({'pc': pc, 'op': OPS[op], 'opn': op, 'src': srcmap.loc(pc)})
json.dump(inv, open(sys.argv[1], 'w'), indent=0)
print(len(inv), collections.Counter(x['op'] for x in inv))
