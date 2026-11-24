# Read-only: for OP Mainnet, Unichain, Ink read on Ethereum the portal's AnchorStateRegistry, its respectedGameType,
# the factory's implementation and gameArgs for that type, and absolutePrestate() of the newest game of that type.
import json,sys
sys.path.insert(0,sys.argv[1])
from rpc import call,sel,raw
C={'10':'0xbEb5Fc579115071764c7423A4f12eDde41f106Ed','130':'0x0bd48f6B86a26D3a217d0Fa6FfE2B491B956A7a2','57073':'0x5d66C1782664115999C47c9fA5cd031f495D3e4F'}
blk=int(raw('eth_blockNumber',[])['result'],16); B=hex(blk)
def a(x): return '0x'+x[-40:]
def s(x):
    try:
        b=bytes.fromhex(x[2:]);n=int.from_bytes(b[32:64],'big');return b[64:64+n].decode()
    except Exception: return x
out={'ethBlock':blk,'chains':{}}
for cid,portal in C.items():
    r={'portal':portal}
    asr=a(call(portal,sel('anchorStateRegistry()'),block=B)); r['asr']=asr
    rgt=int(call(asr,sel('respectedGameType()'),block=B),16); r['respectedGameType']=rgt
    dgf=a(call(asr,sel('disputeGameFactory()'),block=B)); r['dgf']=dgf
    impl=a(call(dgf,sel('gameImpls(uint32)')+format(rgt,'064x'),block=B)); r['impl']=impl
    r['implVersion']=s(call(impl,sel('version()'),block=B))
    r['gameArgs']=call(dgf,sel('gameArgs(uint32)')+format(rgt,'064x'),block=B)
    cnt=int(call(dgf,sel('gameCount()'),block=B),16); r['gameCount']=cnt
    for i in range(cnt-1,max(cnt-80,-1),-1):
        b=bytes.fromhex(call(dgf,sel('gameAtIndex(uint256)')+format(i,'064x'),block=B)[2:])
        if int.from_bytes(b[0:32],'big')==rgt:
            p='0x'+b[76:96].hex()
            r['newestGame']={'index':i,'proxy':p,'timestamp':int.from_bytes(b[32:64],'big'),'absolutePrestate':call(p,sel('absolutePrestate()'),block=B)}
            break
    out['chains'][cid]=r; print(cid,json.dumps(r),flush=True)
json.dump(out,open(sys.argv[2],'w'),indent=1)
