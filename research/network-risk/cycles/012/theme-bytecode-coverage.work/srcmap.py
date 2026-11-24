"""Map each instruction of the built runtime to a source file and line through the solc source map."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
B = json.load(open(os.path.join(HERE, 'build-srcmap.json')))
code = bytes.fromhex(B['runtime'])
starts = []; i = 0
while i < len(code):
    starts.append(i); op = code[i]; i += op - 0x5e if 0x60 <= op <= 0x7f else 1
ent = []; s = l = f = 0; j = '-'
for e in B['sourceMap'].split(';'):
    p = e.split(':')
    if len(p) > 0 and p[0] != '': s = int(p[0])
    if len(p) > 1 and p[1] != '': l = int(p[1])
    if len(p) > 2 and p[2] != '': f = int(p[2])
    if len(p) > 3 and p[3] != '': j = p[3]
    ent.append((s, l, f, j))
assert len(ent) <= len(starts); NCODE = len(ent)  # the rest is the compiler trailer
srcs = {}
def text(fid):
    if fid not in srcs:
        name = B['sourceIds'].get(str(fid))
        if name is None: srcs[fid] = None
        else:
            pth = os.path.join(ROOT, name if not name.startswith('solmate') else 'lib/solmate/' + name[len('solmate/'):])
            srcs[fid] = (name, open(pth, 'rb').read())
    return srcs[fid]
PC2I = {p: k for k, p in enumerate(starts)}
def loc(pc):
    if PC2I[pc] >= len(ent): return {'file': 'trailer', 'line': None, 'snippet': 'compiler version trailer (data)', 'jump': '-'}
    s, l, f, j = ent[PC2I[pc]]
    t = text(f)
    if t is None or f < 0: return {'file': 'generated' if f >= 0 else 'none', 'line': None, 'snippet': '', 'jump': j}
    name, b = t; line = b[:s].count(b'\n') + 1; endline = b[:s + l].count(b'\n') + 1
    snip = b[s:s + min(l, 140)].decode(errors='replace').replace('\n', ' ')
    return {'file': name, 'line': line, 'endLine': endline, 'snippet': ' '.join(snip.split()), 'jump': j}
