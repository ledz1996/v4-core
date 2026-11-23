# Read-only: does the fee controller of each network accept collect((address,uint256)[]) from an arbitrary account, and where do the fees go.
import json
from walk import NETS, rpc, EOA
from keccak import sel
def w(x): return (x%(1<<256)).to_bytes(32,'big').hex()
S=sel('collect((address,uint256)[])'); print('selector',S)
out={}
for n in NETS:
    c=n['protocolFeeController']
    if int(c,16)==0: continue
    pm=n['poolManager']
    jar=rpc(n['rpc'],'eth_call',[{'to':c,'data':'0x'+sel('TOKEN_JAR()')},'latest']).get('result')
    pmr=rpc(n['rpc'],'eth_call',[{'to':c,'data':'0x'+sel('POOL_MANAGER()')},'latest']).get('result')
    acc=rpc(n['rpc'],'eth_call',[{'to':pm,'data':'0x'+sel('protocolFeesAccrued(address)')+w(0)},'latest']).get('result')
    data='0x'+S+w(0x20)+w(1)+w(0)+w(0)
    r=rpc(n['rpc'],'eth_call',[{'from':EOA,'to':c,'data':data},'latest',{EOA:{'balance':hex(10**18)}}])
    res='ok '+r['result'][:74] if 'result' in r else 'err '+json.dumps(r['error'])[:160]
    # trace balances: use a second call through state diff is not available everywhere, so read jar balance only
    out[n['chainId']]={'controller':c,'TOKEN_JAR':jar,'POOL_MANAGER':pmr,'nativeFeesAccrued':int(acc,16) if acc else None,'collect_from_any_account':res}
    print(n['chainId'],n['name'],out[n['chainId']])
json.dump(out,open('raw/collect.json','w'),indent=1)
