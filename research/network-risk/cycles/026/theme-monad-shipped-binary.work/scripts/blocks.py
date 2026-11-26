# Split the PoolManager runtime into basic blocks with the rule of Monad's
# basic_blocks IR (block starts at JUMPDEST, ends after JUMP, JUMPI, STOP,
# RETURN, REVERT, SELFDESTRUCT, INVALID or an undefined opcode) and list the
# blocks in which an instruction with an effect outside the frame (CALL family,
# SSTORE, TSTORE, LOG) is followed by more instructions of the same block.
import json, sys
j = json.load(open(sys.argv[1]))
h = j.get('deployedBytecode', j.get('runtime'))
if isinstance(h, dict): h = h.get('object')
b = bytes.fromhex(h[2:] if h.startswith('0x') else h)
TERM = {0x56, 0x57, 0x00, 0xf3, 0xfd, 0xff, 0xfe}
SIDE = {0xf1: 'CALL', 0xf2: 'CALLCODE', 0xf4: 'DELEGATECALL', 0xfa: 'STATICCALL', 0x55: 'SSTORE', 0x5d: 'TSTORE',
        0xa0: 'LOG0', 0xa1: 'LOG1', 0xa2: 'LOG2', 0xa3: 'LOG3', 0xa4: 'LOG4', 0xf0: 'CREATE', 0xf5: 'CREATE2'}
VALID = set(range(0x00, 0x0c)) | set(range(0x10, 0x1e)) | {0x20} | set(range(0x30, 0x4b)) | set(range(0x50, 0x60)) | set(range(0x60, 0xa5)) | {0xf0, 0xf1, 0xf2, 0xf3, 0xf4, 0xf5, 0xfa, 0xfd, 0xfe, 0xff}
blocks = []; cur = None; i = 0
while i < len(b):
    op = b[i]
    if op == 0x5b or cur is None:
        if cur is not None and cur['ins']: blocks.append(cur)
        cur = {'start': i, 'ins': []}
    cur['ins'].append((i, op))
    n = op - 0x5f if 0x60 <= op <= 0x7f else 0
    i += 1 + n
    if op in TERM or op not in VALID:
        blocks.append(cur); cur = None
if cur and cur['ins']: blocks.append(cur)
out = []
for bl in blocks:
    ins = bl['ins']
    for k, (pc, op) in enumerate(ins):
        if op in SIDE and k < len(ins) - 1:
            out.append({'block': bl['start'], 'pc': pc, 'op': SIDE[op], 'after': len(ins) - 1 - k})
print(json.dumps({'blocks': len(blocks), 'sideEffectNotLast': len(out), 'blocksAffected': len({o['block'] for o in out}),
                  'byOp': {o: sum(1 for x in out if x['op'] == o) for o in sorted({x['op'] for x in out})}, 'list': out}, indent=0))
