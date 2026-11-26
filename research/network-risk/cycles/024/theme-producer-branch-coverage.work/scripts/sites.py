"""Map PoolManager instructions to source lines with the solc source map of the build (cycle 12 srcmap.py)."""
import sys, collections
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/012/theme-bytecode-coverage.work')
import srcmap as S
from pyevm_cov import NAMES
OPS = {'MULMOD','ADDMOD','SAR','SIGNEXTEND','BYTE','SHL','SHR','SDIV','SMOD','DIV','MOD','EXP','JUMPI','SLT','SGT','LT','GT','MUL','ADD','SUB','KECCAK256','MCOPY','TLOAD','TSTORE'}
def sites():
    out = []
    for p in S.starts[:S.NCODE]:
        n = NAMES.get(S.code[p])
        if n in OPS:
            l = S.loc(p); out.append((p, n, l['file'], l.get('line'), l.get('snippet', '')))
    return out
if __name__ == '__main__':
    c = collections.Counter()
    for p, n, f, l, s in sites():
        if f.startswith('src/libraries') or f.startswith('src/types'):
            if n in ('MULMOD','ADDMOD','SAR','SIGNEXTEND','BYTE','SDIV','SMOD','EXP','JUMPI','DIV','MOD'): print(p, n, f, l, s[:70])
