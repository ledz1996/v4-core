# Structural profile of build/PoolManager.json runtime for the Monad native size bound.
import json,sys,collections
b=json.load(open(sys.argv[1]));code=bytes.fromhex(b['runtime'].removeprefix('0x'))
n=len(code);i=0;ops=collections.Counter();jd=0;blocks=0;term=set([0x56,0x57,0x00,0xf3,0xfd,0xfe,0xff])
nostack=0;emit=0
while i<n:
    o=code[i]
    if 0x60<=o<=0x7f: ops['PUSH']+=1;i+=o-0x5e;continue
    if o==0x5f: ops['PUSH']+=1
    elif 0x80<=o<=0x9f: ops['DUPSWAP']+=1
    elif o==0x50: ops['POP']+=1
    elif o==0x5b: ops['JUMPDEST']+=1
    else: ops['OTHER']+=1
    if o in term: blocks+=1
    i+=1
tot=sum(ops.values())
bound=10*1024+32*n
print('bytes',n,'instructions',tot,dict(ops),'terminators',blocks)
print('bound',bound,'jump table',4*n,'room for text+rodata',bound-4*n)
print('room per instruction',round((bound-4*n)/tot,1),'per non stack-shuffle instruction',round((bound-4*n)/(ops['OTHER']+ops['JUMPDEST']),1))
