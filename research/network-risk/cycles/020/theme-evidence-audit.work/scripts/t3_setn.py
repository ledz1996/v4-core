# Task 3: jump destination analysis around PUSH2..PUSH16 data, the path through bitvec.setN (core/vm analysis, a >> 8 on a
# uint16, the C1 shape of Go issue 81868). Code = CALLDATALOAD(0) JUMP, then o bytes of 0x5b, PUSHn whose data is all 0x5b,
# then JUMPDEST, return 1. A target inside the push data must fail; every 0x5b outside it must return 1.
import json, sys, time
from rpch import rpcb
NETS_ALL={1:'https://ethereum-rpc.publicnode.com',137:'https://polygon-bor-rpc.publicnode.com',56:'https://bsc-dataseed1.bnbchain.org',43114:'https://api.avax.network/ext/bc/C/rpc'}
NETS={c:NETS_ALL[c] for c in map(int,sys.argv[1:])} if sys.argv[1:] else NETS_ALL
STUB='0x00000000000000000000000000000000000e2020'
head=bytes([0x5f,0x35,0x56])  # PUSH0 CALLDATALOAD JUMP
tail=bytes([0x5b,0x60,0x01,0x5f,0x52,0x60,0x20,0x5f,0xf3])
cases=[]
for n in range(2,17):
    for o in range(0,8):
        code=head+bytes([0x5b]*o)+bytes([0x5f+n])+bytes([0x5b]*n)+tail
        start=len(head); pushpc=start+o
        for t in range(start, pushpc+n+2):
            inside = pushpc < t <= pushpc+n
            ok_expected = (not inside) and code[t]==0x5b
            if t==pushpc: continue  # the PUSH opcode itself is not 0x5b
            cases.append((n,o,t,code,ok_expected))
out={'cases':len(cases),'results':{}}
for cid,u in NETS.items():
    bad=[]; done=0; cv=[]
    STEP=int(__import__('os').environ.get('STEP','40'))
    for i in range(0,len(cases),STEP):
        ch=cases[i:i+STEP]
        calls=[('web3_clientVersion',[])]+[('eth_call',[{'to':STUB,'data':'0x'+t.to_bytes(32,'big').hex(),'gas':'0x100000'},'latest',{STUB:{'code':'0x'+c.hex()}}]) for (n,o,t,c,e) in ch]+[('web3_clientVersion',[])]
        for k in range(4):
            r=rpcb(u,calls)
            if isinstance(r,list): break
            time.sleep(2)
        if not isinstance(r,list): bad.append(['batch error',i,str(r)[:200]]); continue
        cv.append([r[0],r[-1]])
        for (n,o,t,c,e),x in zip(ch,r[1:-1]):
            got_ok = isinstance(x,str) and int(x,16)==1
            if got_ok!=e: bad.append({'n':n,'o':o,'target':t,'expectedSuccess':e,'answer':str(x)[:120]})
            done+=1
    out['results'][cid]={'rpc':u,'ran':done,'mismatch':bad,'clients':sorted({str(a)[:120] for p in cv for a in p})}
    print(cid,done,len(bad),out['results'][cid]['clients'],bad[:2])
json.dump(out,open('../out/t3_setn-%s.json'%('-'.join(map(str,NETS))),'w'),indent=1)
