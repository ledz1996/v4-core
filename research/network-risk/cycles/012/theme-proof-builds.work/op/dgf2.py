# Read respected game type impl, gameArgs, and the newest game proxy of that type with its prestate and vm.
import json,sys
sys.path.insert(0,sys.argv[1])
from rpc import call,sel,raw
d0=json.load(open(sys.argv[2]))
out={'ethBlock':int(raw('eth_blockNumber',[])['result'],16),'chains':{}}
def addr(x): return None if not x or len(x)<66 else '0x'+x[-40:]
def s(x):
    try:
        b=bytes.fromhex(x[2:]);n=int.from_bytes(b[32:64],'big');return b[64:64+n].decode()
    except Exception: return x
for cid,c in d0['chains'].items():
    dgf=c['dgf'];rgt=int(c['respectedGameType_asr'],16)
    r={'dgf':dgf,'respectedGameType':rgt,'dgfVersion':s(call(dgf,sel('version()')))}
    impl=addr(call(dgf,sel('gameImpls(uint32)')+format(rgt,'064x')))
    r['impl']=impl; r['implVersion']=s(call(impl,sel('version()')))
    r['gameArgs']=call(dgf,sel('gameArgs(uint32)')+format(rgt,'064x'))
    cnt=int(call(dgf,sel('gameCount()')),16); r['gameCount']=cnt
    # walk back to find newest game of respected type
    for i in range(cnt-1,max(cnt-60,-1),-1):
        g=call(dgf,sel('gameAtIndex(uint256)')+format(i,'064x'))
        b=bytes.fromhex(g[2:]); gt=int.from_bytes(b[0:32],'big'); proxy='0x'+b[64+12:96].hex()
        if gt==rgt:
            r['newestGame']={'index':i,'proxy':proxy,'timestamp':int.from_bytes(b[32:64],'big')}
            for f in ['absolutePrestate()','vm()','l2ChainId()','gameType()','status()','rootClaim()','l2BlockNumber()','l2SequenceNumber()','version()']:
                v=call(proxy,sel(f)); r['newestGame'][f]=s(v) if f=='version()' else v
            vm=addr(r['newestGame']['vm()'])
            if vm and int(vm,16):
                r['vm']=vm; r['vmVersion']=s(call(vm,sel('version()'))); r['oracle']=addr(call(vm,sel('oracle()')))
                r['vmCodeSize']=len(raw('eth_getCode',[vm,'latest'])['result'])//2-1
            break
    out['chains'][cid]=r
    print(cid,json.dumps(r,indent=0),flush=True)
json.dump(out,open(sys.argv[3],'w'),indent=1)
