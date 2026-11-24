import json,sys
sys.path.insert(0,'research/network-risk/tools/opdiff')
from pyevm import NAMES
b=json.load(open('research/network-risk/build/PoolManager.json'))
code=bytes.fromhex(b['runtime'].replace('0x',''))
ins=[];i=0
while i<len(code):
    op=code[i];k=op-0x5f if 0x60<=op<=0x7f else 0
    ins.append((i,NAMES.get(op,hex(op)),code[i+1:i+1+k].hex() if k else ''));i+=k+1
idx={p:n for n,(p,_,_) in enumerate(ins)}
def ctx(pc,a=12,bk=6):
    n=idx[pc];return ' | '.join(f'{p}:{o} {d}'.strip() for p,o,d in ins[max(0,n-a):n+bk])
if __name__=='__main__':
    for p,o,d in ins:
        if o=='MULMOD': print(ctx(p,14,4)); print()
