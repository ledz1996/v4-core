"""Cut the emitter's assembly log (pm.asm) into basic blocks and write, for each
target source region, the EVM instructions and the x86 code emitted for every
block that holds an instruction of the region."""
import json, re, sys, os
sys.path.insert(0, os.path.abspath('../../012/theme-bytecode-coverage.work'))
import srcmap
import covmap
lines = open('pm.asm').read().split('\n')
blocks = {}; cur = None
for l in lines:
    m = re.match(r'^//   0x([0-9a-f]+):$', l)
    if m:
        cur = int(m.group(1), 16); blocks[cur] = []
    if cur is not None:
        blocks[cur].append(l)
starts = sorted(blocks)
import bisect
def block_of(pc):
    i = bisect.bisect_right(starts, pc) - 1
    return starts[i] if i >= 0 else None
hits = set()
for f in sys.argv[1:]:
    hits |= {int(x) for x in open(f).read().split()}
summary = {}
for name, (fn, a, b) in covmap.REG.items():
    pcs = [p for p in srcmap.starts if p in srcmap.PC2I and srcmap.PC2I[p] < srcmap.NCODE and (lambda L: L['file'] == fn and L['line'] and a <= L['line'] <= b)(srcmap.loc(p))]
    bs = sorted({block_of(p) for p in pcs})
    with open('blocks/%s.asm' % re.sub(r'[^A-Za-z0-9]', '_', name), 'w') as f:
        for s in bs:
            f.write('\n'.join(blocks[s]) + '\n')
    x86 = sum(1 for s in bs for l in blocks[s] if l and not l.startswith('//') and not l.endswith(':'))
    ops = {}
    for s in bs:
        for l in blocks[s]:
            m = re.match(r'^//       0x[0-9a-f]+: (\w+)', l)
            if m: ops[m.group(1)] = ops.get(m.group(1), 0) + 1
    summary[name] = {'sourceRegion': '%s:%d-%d' % (fn, a, b), 'blocks': len(bs), 'blockOffsets': bs,
                     'blocksExecutedInHarness': sum(1 for s in bs if s in hits or any(p in hits for p in pcs if block_of(p) == s)),
                     'evmInstructions': sum(ops.values()), 'x86Instructions': x86, 'opcodes': ops}
    print(name, summary[name]['blocks'], summary[name]['blocksExecutedInHarness'], summary[name]['evmInstructions'], x86)
json.dump(summary, open('blocks/summary.json', 'w'), indent=1)
