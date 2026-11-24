import json,sys; from lib import *
URL='https://mainnet.gateway.tenderly.co'; PM='0x000000000004444c5dc75cB358380D2e3dE08A90'
V1='0x3231Cb76718CDeF2155FC47b5286d82e6eDA273f'; V2='0x39b8B6385416f4cA36a20319F70D28621895279D'
T0='0x'+keccak256(b'Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)').hex()
head=int(rpc(URL,'eth_blockNumber',[])['result'],16)
def logs(topics,frm,to):
    return rpc(URL,'eth_getLogs',[{'address':PM,'topics':topics,'fromBlock':hex(frm),'toBlock':hex(to)}],timeout=90)
res=[]
for name,a in (('V1',V1),('V2',V2)):
    t='0x'+w(a)
    for pos in (2,3):
        topics=[T0,None,None,None]; topics[pos]=t
        r=logs(topics,21688329,head)
        if 'result' not in r:
            print('ERR',name,pos,json.dumps(r)[:300]); continue
        for l in r['result']:
            d=bytes.fromhex(l['data'][2:])
            res.append({'ver':name,'id':l['topics'][1],'c0':'0x'+l['topics'][2][26:],'c1':'0x'+l['topics'][3][26:],'fee':int.from_bytes(d[0:32],'big'),'ts':int.from_bytes(d[32:64],'big',signed=False),'hooks':'0x'+d[64+12:96].hex(),'block':int(l['blockNumber'],16),'tx':l['transactionHash']})
for x in res: print(x)
json.dump(res,open('raw_eure_pools.json','w'),indent=0)
