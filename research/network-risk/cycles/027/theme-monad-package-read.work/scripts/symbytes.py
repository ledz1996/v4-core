"""Compare the bytes of named symbols between an ELF file of the package and harness object files.

Reads ELF files as data with readelf/nm output and plain file reads. Nothing is executed.
usage: python3 -I symbytes.py <elf> <out.json> <regex> <obj> [obj ...]
For an object file the bytes are taken from the section the symbol lives in, without relocations applied;
relocated positions are listed from readelf -r and masked on both sides.
"""
import sys, re, subprocess, json, hashlib

def sections(path):
    out = subprocess.run(['readelf', '-S', '-W', path], capture_output=True, text=True).stdout
    secs = {}
    for m in re.finditer(r'\[\s*(\d+)\]\s+(\S+)\s+(\S+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)', out):
        secs[int(m.group(1))] = (m.group(2), int(m.group(4), 16), int(m.group(5), 16), int(m.group(6), 16))
    return secs

def symbols(path):
    out = subprocess.run(['readelf', '-s', '-W', path], capture_output=True, text=True).stdout
    syms = []
    for line in out.splitlines():
        f = line.split()
        if len(f) >= 8 and f[0].endswith(':') and f[6] not in ('UND', 'ABS') and f[6].isdigit():
            syms.append((f[7], int(f[1], 16), int(f[2], 0) if not f[2].startswith('0x') else int(f[2], 16), int(f[6])))
    return syms

def demangle(names):
    out = subprocess.run(['c++filt'], input='\n'.join(names), capture_output=True, text=True).stdout.splitlines()
    return dict(zip(names, out))

def relocs(path):
    out = subprocess.run(['readelf', '-r', '-W', path], capture_output=True, text=True).stdout
    rel = {}
    cur = None
    for line in out.splitlines():
        m = re.match(r"Relocation section '\.rela?(\S+)'", line)
        if m: cur = m.group(1); rel.setdefault(cur, []); continue
        f = line.split()
        if cur and f and re.match(r'^[0-9a-f]{8,}$', f[0]):
            typ = f[2] if len(f) > 2 else ''
            size = 4 if ('32' in typ or 'PC32' in typ or 'PLT32' in typ) else 8
            rel[cur].append((int(f[0], 16), size, ' '.join(f[4:])))
    return rel

def get(path, rx):
    data = open(path, 'rb').read()
    secs = sections(path); syms = symbols(path)
    dm = demangle([s[0] for s in syms])
    rel = relocs(path)
    found = {}
    for name, val, size, shn in syms:
        d = dm.get(name, name)
        if not re.search(rx, d) or size == 0: continue
        sname, addr, off, ssz = secs[shn]
        if sname in ('.bss', '.tbss'): continue
        start = off + (val - addr)
        b = bytearray(data[start:start + size])
        masked = []
        for (o, sz, tgt) in rel.get(sname, []):
            p = o - (val - addr) if addr == 0 else o - val
            if 0 <= p < size:
                for i in range(sz):
                    if p + i < size: b[p + i] = 0
                masked.append(p)
        found[d] = (bytes(b), masked)
    return found

if __name__ == '__main__':
    elf, out, rx = sys.argv[1], sys.argv[2], sys.argv[3]
    objs = sys.argv[4:]
    pk = get(elf, rx)
    hv = {}
    for o in objs:
        for k, v in get(o, rx).items(): hv.setdefault(k, v)
    res = []
    for k in sorted(set(pk) | set(hv)):
        a = pk.get(k); b = hv.get(k)
        r = {'symbol': k, 'inPackage': a is not None, 'inHarness': b is not None}
        if a and b:
            ab, am = a; bb, bm = b
            # mask positions relocated in the harness object on the package side too
            ab2 = bytearray(ab)
            for p in bm:
                for i in range(8 if p + 8 <= len(ab2) else 4):
                    if p + i < len(ab2): ab2[p + i] = 0
            bb2 = bytearray(bb)
            r.update({'size': [len(ab), len(bb)], 'sha256Package': hashlib.sha256(ab).hexdigest(),
                      'sha256Harness': hashlib.sha256(bb).hexdigest(), 'relocMasked': len(bm),
                      'equalRaw': ab == bb, 'equalMasked': bytes(ab2) == bytes(bb2)})
            if not r['equalMasked']:
                diff = [i for i in range(min(len(ab2), len(bb2))) if ab2[i] != bb2[i]]
                r['firstDiffs'] = diff[:20]
        res.append(r)
    json.dump(res, open(out, 'w'), indent=1)
    for r in res:
        print(r.get('equalMasked'), r.get('equalRaw'), r.get('size'), r['symbol'][:110])
