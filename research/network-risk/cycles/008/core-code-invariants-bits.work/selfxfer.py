# Read-only: does a self transfer of an ERC-6909 claim on the deployed PoolManager leave the balance unchanged?
# Uses eth_simulateV1 (three calls in one simulated block, nothing is sent).
import json,sys,time
from width_probe import rpc,sel,W,NET
from keccak import keccak256
T0='0x'+keccak256(b'Transfer(address,address,address,uint256,uint256)').hex()
def find_holder(n,span=4000,tries=12):
    url=n['rpc']; pm=n['poolManager']
    head=int(rpc(url,'eth_blockNumber',[])['result'],16)
    to=head
    for _ in range(tries):
        fr=to-span
        r=rpc(url,'eth_getLogs',[{'address':pm,'topics':[T0],'fromBlock':hex(fr),'toBlock':hex(to)}])
        logs=r.get('result') if isinstance(r,dict) else None
        if logs is None: return None,str(r)[:200]
        for lg in reversed(logs):
            to_addr='0x'+lg['topics'][2][26:]; idw=lg['topics'][3]
            if int(to_addr,16)==0: continue
            b=rpc(url,'eth_call',[{'to':pm,'data':'0x'+sel('balanceOf(address,uint256)')+W(int(to_addr,16))+idw[2:]},'latest'])
            if 'result' in b and int(b['result'],16)>0: return (to_addr,idw,int(b['result'],16)),None
        to=fr
    return None,'no holder found in window'
def test(n):
    h,err=find_holder(n)
    if not h: return {'chainId':n['chainId'],'err':err}
    holder,idw,bal=h; pm=n['poolManager']; url=n['rpc']
    bo='0x'+sel('balanceOf(address,uint256)')+W(int(holder,16))+idw[2:]
    amt=bal
    tx='0x'+sel('transfer(address,uint256,uint256)')+W(int(holder,16))+idw[2:]+W(amt)
    tf='0x'+sel('transferFrom(address,address,uint256,uint256)')+W(int(holder,16))+W(int(holder,16))+idw[2:]+W(amt)
    calls=[{'from':holder,'to':pm,'data':bo},{'from':holder,'to':pm,'data':tx},{'from':holder,'to':pm,'data':bo},{'from':holder,'to':pm,'data':tf},{'from':holder,'to':pm,'data':bo},
           {'from':holder,'to':pm,'data':'0x'+sel('transfer(address,uint256,uint256)')+W(int(holder,16))+idw[2:]+W(amt+1)}]
    r=rpc(url,'eth_simulateV1',[{'blockStateCalls':[{'stateOverrides':{holder:{'balance':hex(10**20)}},'calls':calls}],'validation':False},'latest'])
    out={'chainId':n['chainId'],'holder':holder,'id':idw,'bal':bal}
    if 'result' not in r: out['err']=str(r)[:300]; return out
    cs=r['result'][0]['calls']
    out['calls']=[(c.get('status'),c.get('returnData','')[:74],(c.get('error') or {}).get('message','')[:40]) for c in cs]
    out['block']=int(r['result'][0]['number'],16)
    return out
if __name__=='__main__':
    ids=[int(x) for x in sys.argv[1:]] or [1]
    res=[]
    for n in NET:
        if n['chainId'] in ids:
            o=test(n); res.append(o); print(json.dumps(o))
    json.dump(res,open('selfxfer.out.json','w'),indent=1)
