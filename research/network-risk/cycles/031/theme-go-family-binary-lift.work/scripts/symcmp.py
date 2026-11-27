"""Compares pclntab function names of the Nitro binary with funcs and methods declared in source.
usage: python3 -I symcmp.py <pcln list> <src-vm> <src-u256> <out.json>"""
import json, re, sys
pc, svm, su, out = sys.argv[1:5]
import os
PFX = {os.environ.get('VMPFX', 'github.com/ethereum/go-ethereum/core/vm.'): 'vm', 'github.com/holiman/uint256.': 'u256'}
binn = {'vm': set(), 'u256': set()}; raw = {'vm': [], 'u256': []}
for l in open(pc):
    name = l.split()[0]
    for p, k in PFX.items():
        if name.startswith(p):
            n = name[len(p):]; raw[k].append(n)
            n = re.sub(r'(\.(func|deferwrap|gowrap)\d+)+$', '', n)
            n = re.sub(r'^init\.\d+$', 'init', n)
            if n.startswith('map.init'): n = 'init'
            binn[k].add(n)
def src(f):
    s = set(); v = []
    for l in open(f):
        kind, n, loc = l.split()
        if kind == 'func': s.add(n)
        elif kind == 'var' and n != '_': v.append(n)
    return s, v
res = {}
for k, f in (('vm', svm), ('u256', su)):
    s, v = src(f)
    def norm_has(n):
        if n in s: return True
        m = re.match(r'^\(\*(\w+)\)\.(\w+)$', n)   # pointer wrapper of a value method
        if m and f"{m.group(1)}.{m.group(2)}" in s: return True
        if n == 'init': return True
        return False
    bin_only = sorted(n for n in binn[k] if not norm_has(n))
    src_names = set(s)
    def in_bin(n):
        if n in binn[k]: return True
        m = re.match(r'^(\w+)\.(\w+)$', n)
        if m and f"(*{m.group(1)}).{m.group(2)}" in binn[k]: return True
        return False
    src_only = sorted(n for n in src_names if not in_bin(n))
    res[k] = {'binaryFunctions': len(raw[k]), 'binaryDistinct': len(binn[k]), 'sourceFuncs': len(s),
              'binaryOnly': bin_only, 'sourceOnly': src_only, 'sourcePackageVars': v}
json.dump(res, open(out, 'w'), indent=1)
for k in res:
    print(k, {x: res[k][x] for x in ('binaryFunctions', 'binaryDistinct', 'sourceFuncs')})
    print(' binaryOnly', res[k]['binaryOnly'])
    print(' sourceOnly', len(res[k]['sourceOnly']), res[k]['sourceOnly'] if k == 'u256' else '')
