# Read-only eth_call probe of mega-evm frame-local limit semantics (no PoolManager interaction).
import json, sys, urllib.request
R='https://mainnet.megaeth.com/rpc'
def rpc(m,p):
    req=urllib.request.Request(R,json.dumps({'jsonrpc':'2.0','id':1,'method':m,'params':p}).encode(),{'content-type':'application/json','user-agent':'curl/8'})
    return json.load(urllib.request.urlopen(req,timeout=300))
# child: for i=N..1: sstore(i,1); stop      (N = calldata word 0); mode word1: 1 -> infinite loop instead
child=bytes.fromhex(
 '600035'      # PUSH1 0 CALLDATALOAD  -> N
 '5b'          # 3: JUMPDEST
 '80'          # DUP1
 '15'          # ISZERO
 '6014'        # PUSH1 0x14 (end)
 '57'          # JUMPI
 '6001' '81' '55'  # PUSH1 1 DUP2 SSTORE
 '6001' '90' '03'  # PUSH1 1 SWAP1 SUB
 '6003' '56'   # PUSH1 3 JUMP
 '5b' '00')    # 0x14: JUMPDEST STOP
assert child[0x14]==0x5b and child[3]==0x5b, child.hex()
C='0x'+'c0'*20
# parent: calldatacopy(0,0,32); success=call(gas,C,0,0,32,0,0); sstore(0xff, 7); mstore(0,success); mstore(32,rds); returndatacopy(64,0,rds); return(0,64+rds)
parent=bytes.fromhex('6020600060003760006000602060006000'+'73'+'c0'*20+'5af1'+'600760ff55'+'600052'+'3d602052'+'3d600060403e'+'3d6040016000f3')
P='0x'+'b0'*20
def run(n, gas=hex(9_000_000_000)):
    ov={C:{'code':'0x'+child.hex()},P:{'code':'0x'+parent.hex()}}
    r=rpc('eth_call',[{'from':'0x'+'a1'*20,'to':P,'data':'0x%064x'%n,'gas':gas},'latest',ov])
    return r
for n in [int(x) for x in sys.argv[1:]]:
    r=run(n); 
    if 'result' in r:
        o=bytes.fromhex(r['result'][2:]); print(n,'parent returned; child success=',int.from_bytes(o[:32],'big'),'rds=',int.from_bytes(o[32:64],'big'),'revertdata=',o[64:].hex())
    else: print(n,r)
# variant: parent DELEGATECALLs the child so the child's writes land in the parent's storage, then returns
# success, sload(N), sload(0xff written by parent after the call)
parent2=bytes.fromhex('602060006000376000600060206000'+'73'+'c0'*20+'5af4'+'600760ff55'+'600052'+'600035'+'54'+'602052'+'60ff54'+'604052'+'60606000f3')
def run2(n):
    ov={C:{'code':'0x'+child.hex()},P:{'code':'0x'+parent2.hex()}}
    r=rpc('eth_call',[{'from':'0x'+'a1'*20,'to':P,'data':'0x%064x'%n,'gas':hex(9_000_000_000)},'latest',ov])
    o=bytes.fromhex(r['result'][2:]); return [int.from_bytes(o[i:i+32],'big') for i in (0,32,64)]
if __name__=='__main__':
    for n in (900,979,990):
        print('delegatecall n=%d success,sload(n),sload(0xff)='%n, run2(n))
