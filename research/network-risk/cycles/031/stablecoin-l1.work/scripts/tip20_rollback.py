# Read-only check: does a TIP-20 transfer made inside a reverted frame roll back on Tempo?
# Installs a small harness as code at the PoolManager address through an eth_call state override.
import json, sys, urllib.request
OP = dict(STOP=0x00,ADD=0x01,EQ=0x14,SHL=0x1b,CALLDATALOAD=0x35,ADDRESS=0x30,MLOAD=0x51,MSTORE=0x52,
          JUMP=0x56,JUMPI=0x57,JUMPDEST=0x5b,GAS=0x5a,CALL=0xf1,STATICCALL=0xfa,RETURN=0xf3,REVERT=0xfd,POP=0x50,DUP1=0x80)
def asm(items):
    out=[]; labels={}; fix=[]
    for it in items:
        if isinstance(it,tuple) and it[0]=='L': labels[it[1]]=len(out); out.append(0x5b)
        elif isinstance(it,tuple) and it[0]=='J': out.append(0x61); fix.append((len(out),it[1])); out+= [0,0]
        elif isinstance(it,int): b=it.to_bytes(max(1,(it.bit_length()+7)//8),'big'); out.append(0x5f+len(b)); out+=b
        else: out.append(OP[it])
    for pos,l in fix: out[pos:pos+2]=labels[l].to_bytes(2,'big')
    return bytes(out)
TOKEN=0x20c0000000000000000000000000000000000000; B0B=0xb0b; AMT=1_000_000
def bal(addr_items, dst):
    return [0x70a08231<<224, 0x200, 'MSTORE'] + addr_items + [0x204,'MSTORE',
            0x20,0x300,0x24,0x200,TOKEN,'GAS','STATICCALL','POP', 0x300,'MLOAD', dst,'MSTORE']
code = [0,'CALLDATALOAD', 'DUP1', 3,'EQ', ('J','inner'),'JUMPI', 'DUP1', 4,'EQ', ('J','inner'),'JUMPI',
        # outer
       ] + bal(['ADDRESS'],0x00) + [
        2,'ADD', 0x400,'MSTORE', 0,0,0x20,0x400,0,'ADDRESS','GAS','CALL', 0x20,'MSTORE'] + bal(['ADDRESS'],0x40) + bal([B0B],0x60) + [
        0x80,0,'RETURN',
        ('L','inner'),
        0xa9059cbb<<224, 0x100,'MSTORE', B0B,0x104,'MSTORE', AMT,0x124,'MSTORE',
        0x20,0x500,0x44,0x100,0,TOKEN,'GAS','CALL', 0x520,'MSTORE',
        3,'EQ', ('J','rev'),'JUMPI', 'STOP', ('L','rev'), 0,0,'REVERT']
bc = asm(code)
PM='0x33620f62c5b9b2086dd6b62f4a297a9f30347029'
def call(mode):
    body={"jsonrpc":"2.0","id":mode,"method":"eth_call","params":[{"from":"0x00000000000000000000000000000000000a11ce","to":PM,"data":"0x"+mode.to_bytes(32,'big').hex(),"gas":"0x1c9c380"},"latest",{PM:{"code":"0x"+bc.hex()}}]}
    r=urllib.request.Request(sys.argv[1],json.dumps(body).encode(),{'content-type':'application/json'})
    return json.load(urllib.request.urlopen(r,timeout=30))
res={}
for m,name in [(1,'inner frame reverts'),(2,'inner frame returns')]:
    j=call(m); res[name]=j
    if 'result' in j:
        w=[int(j['result'][2+64*i:2+64*(i+1)],16) for i in range(4)]
        print(name, dict(pmBefore=w[0], innerSuccess=w[1], pmAfter=w[2], recipientAfter=w[3]))
    else: print(name, j)
json.dump({'harness':bc.hex(),'results':res}, open(sys.argv[2],'w'), indent=1)
