"""For every IR block, the external functions (dispatcher entries) whose static walk reaches it, and the internal
functions (targets of PUSH2 X; JUMP with a return address pushed earlier) whose static walk reaches it."""
import json, sys, re, blocks as B, cfg
cf = sys.argv[1]
offs = B.block_offsets(cf); sp = B.block_spans(offs)
meth = json.load(open(B.os.path.join(B.NR, 'build', 'PoolManager.json')))['methodIdentifiers']
bysel = {int(v, 16): k for k, v in meth.items()}
ent = {}
# selector dispatch: PUSH4 sel ... EQ/ GT ... PUSH2 tgt JUMPI ; also PUSH3 for 0x00fdd58e
for i, p in enumerate(B.pcs):
    o = B.code[p]
    if o in (0x62, 0x63):
        v = int.from_bytes(B.code[p + 1:p + 1 + o - 0x5f], 'big')
        if v in bysel and v not in [x for x in ent]:
            # find the next PUSH2 X JUMPI within 4 instructions after an EQ
            for q in B.pcs[i + 1:i + 6]:
                if B.code[q] == 0x14:
                    for r in B.pcs[B.pcs.index(q) + 1:B.pcs.index(q) + 3]:
                        if B.code[r] == 0x61 and B.code[r + 3] == 0x57: ent[v] = int.from_bytes(B.code[r + 1:r + 3], 'big')
reach = {}
for v, e in ent.items():
    bl, _ = cfg.func(sp, e)
    for b in bl: reach.setdefault(b, []).append(bysel[v])
if __name__ == '__main__':
    print(len(ent), 'of', len(bysel), 'selectors found')
    for v in bysel:
        if v not in ent: print('missing', bysel[v])
    json.dump({'entries': {bysel[v]: hex(e) for v, e in ent.items()}, 'reach': {hex(b): f for b, f in reach.items()}},
              open(B.os.path.join(B.WORK, 'out', 'owners.json'), 'w'), indent=0)
