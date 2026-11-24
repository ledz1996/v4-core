# For each OP Stack chain read portal -> DGF, respected game type, gameImpls(0,1,...) and their prestate, vm, vm.oracle.
import json,sys
sys.path.insert(0,sys.argv[1])
from rpc import call,sel,raw
chains={10:('0xbEb5Fc579115071764c7423A4f12eDde41f106Ed',),8453:('0x49048044D57e1C92A77f79988d21Fa8fAF74E97e',),130:('0x0bd48f6B86a26D3a217d0Fa6FfE2B491B956A7a2',),57073:('0x5d66C1782664115999C47c9fA5cd031f495D3e4F',),1868:('0x88e529A6ccd302c948689Cd5156C83D4614FAE92',),7777777:('0x1a0ad011913A150f69f6A19DF447A0CfD9551054',),480:('0xd5ec14a83B7d95BE1E2Ac12523e2dEE12Cbeea6C',)}
blk=raw('eth_blockNumber',[])['result']
out={'ethBlock':int(blk,16),'chains':{}}
def addr(x): return None if not x or len(x)<66 else '0x'+x[-40:]
for cid,(portal,) in chains.items():
    d={'portal':portal}
    d['version']=call(portal,sel('version()'))
    d['dgf']=addr(call(portal,sel('disputeGameFactory()')))
    d['respectedGameType_portal']=call(portal,sel('respectedGameType()'))
    asr=addr(call(portal,sel('anchorStateRegistry()')))
    d['anchorStateRegistry']=asr
    if asr: d['respectedGameType_asr']=call(asr,sel('respectedGameType()'))
    d['games']={}
    for gt in [0,1,2,3,4,5,6,8,254,255,1337]:
        impl=addr(call(d['dgf'],sel('gameImpls(uint32)')+format(gt,'064x')))
        if not impl or int(impl,16)==0: continue
        g={'impl':impl}
        g['version']=call(impl,sel('version()'))
        g['absolutePrestate']=call(impl,sel('absolutePrestate()'))
        vm=addr(call(impl,sel('vm()')))
        g['vm']=vm
        if vm:
            g['vmVersion']=call(vm,sel('version()'))
            g['oracle']=addr(call(vm,sel('oracle()')))
        g['l2ChainId']=call(impl,sel('l2ChainId()'))
        g['gameType']=call(impl,sel('gameType()'))
        d['games'][gt]=g
    out['chains'][cid]=d
    print(cid,json.dumps(d,indent=0),flush=True)
json.dump(out,open(sys.argv[2],'w'),indent=1)
