"""Transient storage variant of slotalias.py (L-602): the same probe with SSTORE/SLOAD replaced by
TSTORE/TLOAD, so a fold of transient slot keys would show as a nonzero read of another key.
Usage: python3 slotalias_transient.py <out.json> <chainId> [...]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slotalias as S
orig = S.code
def tcode():
    c = bytearray(orig())
    # opcode positions only (push data in this probe never holds 0x54 or 0x55)
    return bytes(0x5d if b == 0x55 else 0x5c if b == 0x54 else b for b in c)
S.code = tcode
if __name__ == '__main__':
    src = open(S.__file__).read().split("if __name__ == '__main__':", 1)[1]
    exec(compile('\n'.join(l[4:] if l.startswith('    ') else l for l in src.splitlines()), 'main', 'exec'), vars(S))
