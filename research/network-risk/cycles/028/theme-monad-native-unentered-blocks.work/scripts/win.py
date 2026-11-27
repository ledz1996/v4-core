"""print the instructions in [a, a+n) with source: python3 win.py 0x15b8 24 ..."""
import sys, blocks as B
ARGS = list(sys.argv)
from dis import ins
sys.argv = ARGS
for i in range(1, len(sys.argv), 2):
    a = int(sys.argv[i], 16); n = int(sys.argv[i + 1])
    print('---', hex(a))
    for p in B.pcs:
        if a <= p < a + n: print(f'  {p:#06x} {ins(p):44s} {B.where(p)}')
