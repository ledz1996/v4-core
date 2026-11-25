"""Largest stack height the built PoolManager reaches in the reference interpreter, over the buildcheck.py cases
(measured on an instrumented in-memory copy of tools/opdiff/pyevm.py; the shared file is not changed).
usage: PM_BUILD=... python3 stackmax.py <out.json> <cases>"""
import sys, os, types
OP = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'tools', 'opdiff'))
sys.path.insert(0, OP)
src = open(os.path.join(OP, 'pyevm.py')).read()
pat = "cov.add(pc); ops[op] = ops.get(op, 0) + 1"
assert pat in src
src = src.replace(pat, pat + "\n            if len(st) > MAXST[0].get(code_addr, 0): MAXST[0][code_addr] = len(st)")
m = types.ModuleType('pyevm'); m.__file__ = os.path.join(OP, 'pyevm.py'); m.MAXST = [{}]
exec(compile(src, m.__file__, 'exec'), m.__dict__); sys.modules['pyevm'] = m
import runpy
sys.argv = ['buildcheck.py'] + sys.argv[1:]
runpy.run_path(os.path.join(OP, 'buildcheck.py'), run_name='__main__')
print('max stack height before an instruction, by code address:', {hex(a): v for a, v in m.MAXST[0].items()})
