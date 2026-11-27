"""Dump the disassembly of named functions of a cycle 31 target (read as data with objdump / llvm-objdump only)."""
import sys, os, subprocess
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/031/theme-go-family-binary-lift.work/scripts')
import targets, goshim as G
name, pat, out = sys.argv[1], sys.argv[2:-1], sys.argv[-1]
t = targets.get(name)
fns = G.fnlist(t['fns'])
sel = [n for n in fns if any(p in n for p in pat)]
txt = G.disasm(t['bin'], t['arch'], [fns[n] for n in sel])
open(out, 'w').write(txt)
print(len(sel), 'functions'); [print(' ', n, hex(fns[n][0])) for n in sel]
