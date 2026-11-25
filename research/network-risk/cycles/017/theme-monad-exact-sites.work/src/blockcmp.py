# Compare the enclosing basic blocks of the five sites between the deployed code and the prologue code, with
# label numbers, block numbers and read-only data offsets replaced by the 8 bytes stored at that offset.
import re, sys, json
def load(p):
    L = open(p).read().split('\n'); db = [l for l in L if l.startswith('.db')]
    rod = bytes(int(x, 16) for x in re.findall(r'0x([0-9A-Fa-f]{2})', db[-1])) if db else b''
    return [l for l in L if not l.startswith('.db')], rod
def blocks(L, lab):
    i = [k for k, l in enumerate(L) if l.startswith(lab + ':')][0]; out = []
    for l in L[i:]:
        out.append(l)
        if len(out) > 1 and re.match(r'^B[0-9a-f]+:', l): break
    return out
def norm(L, rod):
    out = []
    for l in L:
        l = re.sub(r'\bL\d+', 'L#', l); l = re.sub(r'JumpI \d+', 'JumpI #', l)
        l = l.replace('[ROD]', '[ROD+0]')
        wd = 4 if 'dword ptr [ROD' in l else (32 if ('ymm' in l and 'vmovd' not in l and 'vpmov' not in l) else 8)
        l = re.sub(r'ROD\+(\d+)', lambda m: 'ROD<' + rod[int(m.group(1)):int(m.group(1)) + wd].hex() + '>', l)
        out.append(l)
    return out
res = {}
for v in ('167', '165'):
    a, ra = load('asm/plain%s.asm' % v); b, rb = load('asm/prol%s.asm' % v)
    for lab in ('B5703', 'B5810', 'B3c94', 'B40d7'):
        x = blocks(a, lab); y = blocks(b, lab)
        res['%s %s' % (v, lab)] = {'lines': len(x), 'raw': x == y, 'normalised': norm(x, ra) == norm(y, rb)}
        print(v, lab, res['%s %s' % (v, lab)])
json.dump(res, open('asm/blockcheck.json', 'w'), indent=1)
