#!/usr/bin/env python3
"""Dump the branchelim pass of every function and method of a holiman/uint256 source copy, compiled by the
installed go1.24.7 (not an affected compiler), and list every CondSelect and its users. A CondSelect whose
result is the address of a Store/Zero/Move and whose operands are LocalAddr of stack autos is the issue
81863 precondition; any CondSelect at all is listed so the reader can check.
Usage: u256dump.py <copy of uint256 dir> <outdir>"""
import os, re, subprocess, sys, glob, shutil
pkg, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
os.makedirs(out, exist_ok=True)
names = []
for f in sorted(glob.glob(pkg + '/*.go')):
    if f.endswith('_test.go'): continue
    for m in re.finditer(r'^func (?:\((\w+) (\*?)(\w+)\) )?(\w+)\(', open(f).read(), re.M):
        _, star, typ, fn = m.groups()
        names.append(('(*%s).%s' % (typ, fn)) if star else ('%s.%s' % (typ, fn) if typ else fn))
total = 0
for n in names:
    for f in glob.glob(pkg + '/*.dump'): os.remove(f)
    subprocess.run(['go', 'build', '-gcflags=-d=ssa/branchelim/dump=' + n, '-o', os.devnull, '.'], cwd=pkg,
                   capture_output=True, env=dict(os.environ, GOTOOLCHAIN='local', GOCACHE=os.path.join(out, 'gocache')))
    ds = glob.glob(pkg + '/*.dump')
    txt = ''
    for f in ds:
        txt += open(f).read(); shutil.move(f, os.path.join(out, os.path.basename(f)))
    vals = re.findall(r'\) (v\d+) = (\w+) <([^>]*)> ?(.*)', txt)
    cs = [(v, t, r.strip()) for v, op, t, r in vals if op == 'CondSelect']
    total += len(cs)
    defs = {v: (op, t, r) for v, op, t, r in vals}
    for v, t, r in cs:
        users = [(u, op) for u, op, _, a in vals if re.search(r'\b%s\b' % v, a)]
        ops = [defs.get(a, ('?',))[0] for a in r.split()[:2]]
        print('%-28s %s %s <%s> args=%s operand-ops=%s users=%s' % (n, 'dumped' if ds else 'NODUMP', v, t, r, ops, users))
    if not ds: print('%-28s NODUMP (inlined-only or not compiled)' % n)
print('functions', len(names), 'CondSelect total', total)
