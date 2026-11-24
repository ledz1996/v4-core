import sys, json; sys.path.insert(0, __import__('os').path.dirname(__file__))
import srcmap as S
sys.path.insert(0, S.ROOT+'/research/network-risk/tools/opdiff')
from pyevm import NAMES
cov=set(json.load(open(sys.argv[3]))['cover']) if len(sys.argv)>3 else set()
a,b=int(sys.argv[1]),int(sys.argv[2]); code=S.code
for p in S.starts:
    if a<=p<=b:
        op=code[p]; m=op-0x5f if 0x60<=op<=0x7f else 0
        L=S.loc(p) if p<S.starts[S.NCODE] else {}
        print(('   ' if p in cov else '-- ')+f'{p}:{NAMES.get(op,hex(op))}'+(f' {code[p+1:p+1+m].hex()}' if m else ''), '\t', L.get('file','').replace('src/',''), L.get('line'), L.get('snippet','')[:50])
