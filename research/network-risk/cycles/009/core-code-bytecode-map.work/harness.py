"""Run one internal (Yul) function of the built runtime in the reference interpreter of
tools/opdiff/pyevm.py, with a chosen stack, and return its results. The interpreter
source is loaded and patched in memory only (start pc and stack, final stack on STOP)."""
import sys, json
OPD = '/home/user/v4-core/research/network-risk/tools/opdiff'
sys.path.insert(0, OPD)
import evm  # noqa: reference semantics used by pyevm
src = open(OPD + '/pyevm.py').read()
a = "st = []; mem = bytearray(); pc = 0; rd = b''"
assert a in src
src = src.replace(a, "st = self.__dict__.pop('init_stack', []); mem = bytearray(); pc = self.__dict__.pop('init_pc', 0); rd = b''")
b = "elif op == 0x00: return True, b''"
assert b in src
src = src.replace(b, "elif op == 0x00: self.final_stack = list(st); return True, b''")
mod = {'__name__': 'pyevm_h'}; exec(compile(src, 'pyevm_patched', 'exec'), mod)
World = mod['World']; Halt = mod['Halt']
B = json.load(open(__import__('os').path.dirname(__file__) + '/full.json'))
CODE = bytes.fromhex(B['runtime'])
RET = len(CODE)
HCODE = CODE + b'\x5b\x00'           # JUMPDEST; STOP appended after the metadata
EP = {k: v['entryPoint'] for k, v in B['functionDebugData'].items() if v.get('entryPoint') is not None}
PM = 0x1000
def run(fn, args, storage=None, order='top_first', max_steps=2_000_000):
    """args in Yul parameter order; returns (ok, list of return values in Yul order) or (False, reason)."""
    w = World({PM: HCODE}); w.max_steps = max_steps
    if storage: w.storage.update({(PM, k): v for k, v in storage.items()})
    st = [RET] + (list(reversed(args)) if order == 'top_first' else list(args))
    w.init_stack = st; w.init_pc = EP[fn]
    ok, ret = w.run(PM, PM, 0, 0, b'', False, 0) if True else None
    if not ok: return False, ret
    fs = w.final_stack
    return True, fs, w
