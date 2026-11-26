import sys
sys.path.insert(0, '/home/user/v4-core/research/network-risk/cycles/012/theme-bytecode-coverage.work')
import srcmap as S
from pyevm_cov import NAMES
code=S.code
def dis(a,b):
    for p in S.starts[:S.NCODE]:
        if a<=p<=b:
            op=code[p]; n=op-0x5f if 0x60<=op<=0x7f else 0; l=S.loc(p)
            print(p, NAMES.get(op,hex(op)), ('0x'+code[p+1:p+1+n].hex()) if n else '', '   ', l['file'].split('/')[-1], l.get('line'))
if __name__=='__main__': dis(int(sys.argv[1]),int(sys.argv[2]))
