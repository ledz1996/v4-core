"""Cycle 27: split the asmjit listings of the PoolManager (out/pm-asm-<ver>.txt, written by build/<ver>/asmdump) into
Monad basic blocks by the emitter's block comment ('//   0xNN:'), normalise label names and read-only data offsets,
and list the blocks whose emitted instructions differ between v0.16.5 and v0.16.7, with the EVM instructions of each
block (from the 0.16.7 per-instruction comments) and a classification by emitter change.
Usage: python3 asmblocks.py out/pm-asm-0.16.5.txt out/pm-asm-0.16.7.txt out/asm-blockdiff.json"""
import sys, re, json
def split(path):
    blocks, cur, order = {}, None, []
    for ln in open(path):
        ln = ln.rstrip('\n')
        m = re.match(r'^//   (0x[0-9a-f]+):', ln)
        if m:
            cur = int(m.group(1), 16); blocks[cur] = {'asm': [], 'evm': []}; order.append(cur); continue
        if cur is None: continue
        m2 = re.match(r'^//\s+(0x[0-9a-f]+): (.*)$', ln)
        if m2: blocks[cur]['evm'].append((int(m2.group(1), 16), m2.group(2))); continue
        m3 = re.match(r'^//\s+(\S.*)$', ln)
        if m3: blocks[cur]['evm'].append((None, m3.group(1))); continue
        blocks[cur]['asm'].append(ln)
    return blocks, order
def norm(lines):
    labs = {}
    out = []
    for l in lines:
        def lab(m):
            k = m.group(0)
            if k not in labs: labs[k] = f'L{len(labs)}'
            return labs[k]
        l = re.sub(r'\bL\d+\b', lab, l)
        l = re.sub(r'ROD\+\d+', 'ROD+x', l)
        l = re.sub(r'\[ROD\]', '[ROD+x]', l)
        out.append(l)
    return out
a, oa = split(sys.argv[1]); b, ob = split(sys.argv[2])
res = {'blocks165': len(oa), 'blocks167': len(ob), 'sameOffsets': oa == ob, 'differ': []}
for off in ob:
    if off not in a: res['differ'].append({'block': hex(off), 'why': 'missing in 0.16.5'}); continue
    na, nb = norm(a[off]['asm']), norm(b[off]['asm'])
    if na == nb: continue
    txt = '\n'.join(b[off]['asm'])
    tags = []
    if re.search(r'shr eax, 3', txt) and 'vpand' in txt: tags.append('shift_literal_by_non_literal')
    if 'vpinsrq' in txt and 'vinserti128' in txt and not ('vpinsrq' in '\n'.join(a[off]['asm'])): tags.append('mov_words_to_ymm')
    if 'vpextrb' in txt or re.search(r'mov byte ptr \[.*\], \w+b\b', txt): tags.append('mstore8_from_stack')
    if 'lzcnt' in txt: tags.append('clz')
    if len(nb) < len(na) and not tags: tags.append('shorter (memory check skipped?)')
    res['differ'].append({'block': hex(off), 'asm165': len(na), 'asm167': len(nb), 'tags': tags or ['other'],
                          'evm': [f'{hex(p) if p is not None else ""} {s}' for p, s in b[off]['evm']]})
from collections import Counter
res['tagCount'] = dict(Counter(t for d in res['differ'] for t in d.get('tags', [])))
json.dump(res, open(sys.argv[3], 'w'), indent=1)
print(res['blocks165'], res['blocks167'], res['sameOffsets'], 'differ', len(res['differ']), res['tagCount'])
