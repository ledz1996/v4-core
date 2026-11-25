#!/usr/bin/env python3
"""Build, for one client tree, a small package with that tree's core/vm/stack.go and the verbatim text of its
arithmetic, comparison and bitwise opcode handlers (opAdd .. opSAR), stub EVM/ScopeContext types, and the
matching uint256 source; compile it with the installed go1.24.7 (not an affected compiler) with the
branchelim pass dumped for every handler, and list every CondSelect with the values that use it.
Usage: harness.py <tree> <uint256 dir> <outdir>"""
import os, re, shutil, subprocess, sys, glob
tree, u256, out = sys.argv[1:4]
out = os.path.abspath(out)
shutil.rmtree(out, ignore_errors=True); os.makedirs(out + '/h'); os.makedirs(out + '/uint256')
for f in glob.glob(u256 + '/*.go'):
    if not f.endswith('_test.go'): shutil.copy(f, out + '/uint256/')
open(out + '/go.mod', 'w').write('module harness\n\ngo 1.24\n\nrequire github.com/holiman/uint256 v0.0.0\n\nreplace github.com/holiman/uint256 => ./uint256\n')
open(out + '/uint256/go.mod', 'w').write('module github.com/holiman/uint256\n\ngo 1.19\n')
st = open(tree + '/core/vm/stack.go').read()
st = re.sub(r'package vm', 'package h', st)
open(out + '/h/stack.go', 'w').write(st)
ins = open(tree + '/core/vm/instructions.go').read()
a = ins.index('func opAdd('); b = ins.index('func opKeccak256(')
body = ins[a:b]
names = re.findall(r'^func (op\w+)\(', body, re.M)
hdr = '''package h

import (
	"math"
	"github.com/holiman/uint256"
)

var _ uint64 = math.MaxUint64
var _ uint256.Int

type EVM struct{}
type EVMInterpreter struct{}
type ScopeContext struct{ Stack *Stack }
'''
open(out + '/h/ins.go', 'w').write(hdr + body)
res = {}
for n in names:
    d = out + '/dump-' + n; os.makedirs(d)
    r = subprocess.run(['go', 'build', '-gcflags=harness/h=-d=ssa/branchelim/dump=' + n, '-o', os.devnull, './h'],
                       cwd=out, capture_output=True, text=True, env=dict(os.environ, GOTOOLCHAIN='local', GOFLAGS='-mod=mod', GOCACHE=os.path.join(out, 'gocache')))
    if r.returncode:
        print('BUILD FAIL', n, r.stderr[-600:]); sys.exit(1)
    for f in glob.glob(out + '/h/*branchelim*.dump') + glob.glob(out + '/*branchelim*.dump'):
        shutil.move(f, d)
    txt = ''.join(open(f).read() for f in glob.glob(d + '/*.dump'))
    vals = re.findall(r'\) (v\d+) = (\w+) <([^>]*)> ?(.*)', txt)
    cs = [(v, t, rest) for v, op, t, rest in vals if op == 'CondSelect']
    res[n] = []
    for v, t, rest in cs:
        users = [(u, op) for u, op, _, args in vals if re.search(r'\b%s\b' % v, args)]
        res[n].append((v, t, rest.strip(), users))
for n in names:
    print(n, 'CondSelect:', len(res[n]), res[n] if res[n] else '')
