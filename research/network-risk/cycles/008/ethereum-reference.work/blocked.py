import json,sys,time; from lib import *
URLS=['https://eth.drpc.org','https://mainnet.gateway.tenderly.co']
PM='0x000000000004444c5dc75cB358380D2e3dE08A90'; RECIP='0x3db67d11b5ab579acf2d6b1ed5e9012e685900f6'; OTHER='0x5b89b6fea024655c9d60e77fd841a8f0a19e8c91'
TOK={'yUSD':'0x19ebd191f7a24ece672ba13a302212b5ef7f35cb','yETH':'0x8464f6ecae1ea58ec816c13f964030eab8ec123a','xSolvBTC':'0xd9d920aa40f578ab794426f5c90f6c731d159def'}
def call(p,blk):
    for i in range(6):
        for U in URLS:
            r=rpc(U,'eth_call',[p,hex(blk)],timeout=40)
            if 'result' in r: return (True,r['result'])
            m=json.dumps(r.get('error'))
            if 'revert' in m.lower(): return (False,m)
        time.sleep(1.5)
    raise Exception('rpc '+m)
def blocked(tok,blk):
    ok,_=call({'from':PM,'to':tok,'data':'0x'+cd('transfer(address,uint256)',RECIP,0)},blk)
    return not ok
head=int(rpc(URLS[1],'eth_blockNumber',[])['result'],16)
out={}
for n,t in TOK.items():
    code_at=lambda b: rpc(URLS[1],'eth_getCode',[t,hex(b)]).get('result','0x')
    lo=21688329; hi=head
    # token may not exist at lo: transfer to no code returns ok (not blocked)
    print(n,'blocked at head',blocked(t,hi),'blocked at PM deploy',blocked(t,lo),'code at lo',len(code_at(lo))//2-1,flush=True)
    while hi-lo>1:
        mid=(lo+hi)//2
        if blocked(t,mid): hi=mid
        else: lo=mid
    # control at hi: a transfer of 0 between two other accounts
    c_ok,_=call({'from':OTHER,'to':t,'data':'0x'+cd('transfer(address,uint256)',RECIP,0)},hi)
    blk=rpc(URLS[1],'eth_getBlockByNumber',[hex(hi),False])['result']
    out[n]={'token':t,'firstBlockedBlock':hi,'timestamp':int(blk['timestamp'],16),'controlOtherSenderOk':c_ok,'txs':blk['transactions']}
    print(n,'first blocked block',hi,'ts',int(blk['timestamp'],16),'control ok',c_ok,'txs in block',len(blk['transactions']),flush=True)
json.dump(out,open('raw_blocked.json','w'),indent=0)
