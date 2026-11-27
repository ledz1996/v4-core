# Verifier spot check: independent small vector set, eth_call with code override only.
import sys, os, random, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'tools', 'opdiff'))
import evm
M=evm.M; MASK=evm.MASK
def ref(op,a,b,c):
    if op=='MULMOD': return 0 if c==0 else (a*b)%c
    if op=='ADDMOD': return 0 if c==0 else (a+b)%c
    if op=='SDIV': return evm.u(evm.ref_sdiv(a,b)) if True else 0
    if op=='SMOD': return evm.u(evm.ref_smod(a,b))
    if op=='SAR': return evm.ref_sar(a,b)
    if op=='SIGNEXTEND': return evm.ref_signextend(a,b)
    if op=='BYTE': return evm.ref_byte(a,b)
    if op=='SHR': return (b>>a) if a<256 else 0
    if op=='SHL': return ((b<<a)&MASK) if a<256 else 0
def prog(op, nargs):
    # loop over 96-byte records; push c,b,a so a is on top; result at mem[i/3]
    p=[('PUSH',0),('LABEL','loop'),'DUP1','CALLDATASIZE','GT','ISZERO',('REF','end'),'JUMPI']
    if nargs==3: p+=['DUP1',('PUSH',64),'ADD','CALLDATALOAD']
    p+=['DUP1' if nargs==2 else 'DUP2',('PUSH',32),'ADD','CALLDATALOAD']
    p+=['DUP2' if nargs==2 else 'DUP3','CALLDATALOAD',op]
    p+=['DUP2',('PUSH',3),'SWAP1','DIV','MSTORE',('PUSH',96),'ADD',('REF','loop'),'JUMP',('LABEL','end'),('PUSH',3),'SWAP1','DIV',('PUSH',0),'RETURN']
    return evm.assemble(p)
edges=[0,1,2,3,255,256,2**127,2**128-1,2**128,2**159,2**160-1,2**255-1,2**255,2**255+1,MASK-1,MASK,887272,MASK-887271,
       0xfffd8963efd1fc6a506488495d951d5263988d26,4295128739,MASK//3,(2**256-1)//(2**128+1)]
random.seed(34)
def vals(n):
    v=list(edges)
    while len(v)<n: v.append(random.getrandbits(random.choice([8,64,128,192,255,256])))
    return v
ops={'MULMOD':3,'ADDMOD':3,'SDIV':2,'SMOD':2,'SAR':2,'SIGNEXTEND':2,'BYTE':2,'SHR':2,'SHL':2}
out={}
for cid,url in [(42220,'https://forno.celo.org'),(196,'https://rpc.xlayer.tech')]:
    tot=0;mis=[]
    for op,n in ops.items():
        code=prog(op,n); V=vals(60)
        recs=[]
        for i in range(200):
            a=random.choice(V); b=random.choice(V); c=random.choice(V+[MASK,MASK,MASK])
            if op in ('SAR','SHR','SHL','BYTE','SIGNEXTEND') and random.random()<0.6: a=random.randrange(0,300)
            recs.append((a,b,c))
        data=b''.join(x.to_bytes(32,'big') for r in recs for x in r)
        res=evm.call_code(url,code,data,gas=30_000_000)
        for k,(a,b,c) in enumerate(recs):
            got=int.from_bytes(res[32*k:32*k+32],'big'); exp=ref(op,a,b,c); tot+=1
            if got!=exp: mis.append((op,hex(a),hex(b),hex(c),hex(got),hex(exp)))
    out[cid]={'vectors':tot,'mismatches':mis[:20],'mismatchCount':len(mis)}
    print(cid,tot,len(mis),mis[:3])
json.dump(out,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'spot.json'),'w'),indent=1)
