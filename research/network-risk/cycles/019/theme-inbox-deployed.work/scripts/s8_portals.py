import json,os
from rpc import *
from keccak import keccak256
def sel(s): return '0x'+keccak256(s.encode()).hex()[:8]
IMPL='0x'+hex(int.from_bytes(keccak256(b'eip1967.proxy.implementation'),'big')-1)[2:]
ADMIN='0x'+hex(int.from_bytes(keccak256(b'eip1967.proxy.admin'),'big')-1)[2:]
P={10:('0xbEb5Fc579115071764c7423A4f12eDde41f106Ed','0x229047fed2591dbec1eF1118d64F7aF3dB9EB290'),8453:('0x49048044D57e1C92A77f79988d21Fa8fAF74E97e','0x73a79Fab69143498Ed3712e519A88a918e1f4072'),
130:('0x0bd48f6B86a26D3a217d0Fa6FfE2B491B956A7a2','0xc407398d063f942feBbcC6F80a156b47F3f1BDA6'),7777777:('0x1a0ad011913A150f69f6A19DF447A0CfD9551054','0xA3cAB0126d5F504B071b81a3e8A2BBBF17930d86'),
480:('0xd5ec14a83B7d95BE1E2Ac12523e2dEE12Cbeea6C','0x6ab0777fD0e609CE58F939a7F70Fe41F5Aa6300A'),57073:('0x5d66C1782664115999C47c9fA5cd031f495D3e4F','0x62C0a111929fA32ceC2F76aDba54C16aFb6E8364'),
1868:('0x88e529A6ccd302c948689Cd5156C83D4614FAE92','0x7A8Ed66B319911A0F3E7288BDdAB30d9c0C875c3'),42220:('0xc5c5D157928BDBD2ACf6d0777626b6C75a9EAEDC','0x89E31965D844a309231B1f17759Ccaf1b7c09861'),
196:('0x64057ad1ddac804d0d26a7275b193d9daca19993','0x5065809af286321a05fbf85713b5d5de7c8f0433')}
out={'client_start':rpc(ETH,'web3_clientVersion',[])}
for cid,(portal,sc) in P.items():
    d={'portal':portal,'systemConfig':sc}
    d['sc.optimismPortal()']=addr(call(ETH,sc,sel('optimismPortal()')))
    d['impl']=addr(rpc(ETH,'eth_getStorageAt',[portal,IMPL,'latest']))
    d['admin']=addr(rpc(ETH,'eth_getStorageAt',[portal,ADMIN,'latest']))
    d['adminOwner']=addr(call(ETH,d['admin'],sel('owner()')))
    v=call(ETH,portal,sel('version()'))
    try: d['version']=bytes.fromhex(v[2:])[64:64+int(v[66:130],16)].decode()
    except Exception: d['version']=v
    d['paused()']=call(ETH,portal,sel('paused()'))
    c=rpc(ETH,'eth_getCode',[d['impl'],'latest'])
    open(f'../raw/code/portal_{cid}_{d["impl"]}.hex','w').write(c)
    d['implCodeLen']=(len(c)-2)//2
    d['implCodeKeccak']='0x'+keccak256(bytes.fromhex(c[2:])).hex()
    out[cid]=d; print(cid,json.dumps(d))
out['client_end']=rpc(ETH,'web3_clientVersion',[])
json.dump(out,open('../raw/portals.json','w'),indent=1)
