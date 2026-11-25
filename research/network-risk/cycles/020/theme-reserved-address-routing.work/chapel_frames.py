# L-887: on Chapel (Jenner active since 2026-10-29), call a live CAS20 token's balanceOf from a contract
# placed by state override using CALL, STATICCALL and DELEGATECALL, and transfer(dead,0) with CALL and STATICCALL.
import json,sys
sys.path.insert(0,'.')
from rpc import rpc
U=sys.argv[1] if len(sys.argv)>1 else 'https://bsc-testnet.bnbchain.org'
TOK='0xca52000000000000000001217954ab5467577565'
CALLER='0x00000000000000000000000000000000c0ffee21'
def caller_code(op):
    # copy calldata[32:] to mem 0, call TOK (address = calldata word 0) with it, return [success, rds, rd(<=64)]
    c=bytes([0x36,0x60,0x20,0x90,0x03])            # CALLDATASIZE PUSH1 32 SWAP1 SUB -> len
    c+=bytes([0x80,0x60,0x20,0x5f,0x37])          # DUP1 PUSH1 32 PUSH0 CALLDATACOPY (dest0, off32, len)
    # stack: len
    c+=bytes([0x60,0x40,0x61,0x01,0x00])          # retSize 64, retOff 0x100
    c+=bytes([0x91])                              # SWAP2 -> [0x100? ...] build: want outSize outOff inSize inOff (value) addr gas
    # simpler: rebuild explicitly
    c=bytes([0x36,0x60,0x20,0x90,0x03,0x80,0x60,0x20,0x5f,0x37])  # len on stack, mem[0:len]=payload
    c+=bytes([0x60,0x40])          # outSize 64           [len,64]
    c+=bytes([0x61,0x01,0x00])     # outOff 0x100         [len,64,0x100]
    c+=bytes([0x82])               # DUP3 inSize=len      [len,64,0x100,len]
    c+=bytes([0x5f])               # inOff 0
    if op==0xf1: c+=bytes([0x5f])  # value 0 for CALL
    c+=bytes([0x5f,0x35])          # PUSH0 CALLDATALOAD -> addr
    c+=bytes([0x5a,op])            # GAS op -> success
    c+=bytes([0x60,0xc0,0x52])     # mstore(0xc0, success)
    c+=bytes([0x3d,0x60,0xe0,0x52])# mstore(0xe0, rds)
    c+=bytes([0x60,0xa0,0x60,0xc0,0xf3]) # RETURN(0xc0, 0xa0)
    return '0x'+c.hex()
def pad(a): return a[2:].lower().rjust(64,'0')
out={'clientVersionBefore':rpc(U,'web3_clientVersion',[]),'tokenCode':rpc(U,'eth_getCode',[TOK,'latest'])}
calls={'balanceOf(caller)':'70a08231'+pad(CALLER),'transfer(dead,0)':'a9059cbb'+pad('0x000000000000000000000000000000000000dead')+'0'*64}
for name,op in (('CALL',0xf1),('STATICCALL',0xfa),('DELEGATECALL',0xf4)):
    for cn,cd in calls.items():
        j=rpc(U,'eth_call',[{'from':'0x00000000000000000000000000000000000a11ce','to':CALLER,'data':'0x'+pad(TOK)+cd,'gas':'0x2dc6c0'},'latest',{CALLER:{'code':caller_code(op)}}])
        r=j.get('result',j.get('error'))
        if isinstance(r,str):
            b=bytes.fromhex(r[2:]); r={'success':int.from_bytes(b[0:32],'big'),'rds':int.from_bytes(b[32:64],'big'),'rd':b[64:].hex()}
        out[name+' '+cn]=r; print(name,cn,r)
out['clientVersionAfter']=rpc(U,'web3_clientVersion',[])
print(out['clientVersionBefore'],out['clientVersionAfter'],str(out['tokenCode'])[:80])
json.dump(out,open('raw/chapel_frames_%s.json'%U.split('/')[2]+'','w'),indent=1)
