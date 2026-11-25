import json,sys,time
from rpc import *
from keccak import keccak256
UPG='0x'+keccak256(b'Upgraded(address)').hex()
which=sys.argv[1]
if which=='portals':
    U='https://rpc.flashbots.net'; step=2000
    addrs=['0xbEb5Fc579115071764c7423A4f12eDde41f106Ed','0x49048044D57e1C92A77f79988d21Fa8fAF74E97e','0x0bd48f6B86a26D3a217d0Fa6FfE2B491B956A7a2','0x1a0ad011913A150f69f6A19DF447A0CfD9551054','0xd5ec14a83B7d95BE1E2Ac12523e2dEE12Cbeea6C','0x5d66C1782664115999C47c9fA5cd031f495D3e4F','0x88e529A6ccd302c948689Cd5156C83D4614FAE92','0xc5c5D157928BDBD2ACf6d0777626b6C75a9EAEDC','0x64057ad1ddac804d0d26a7275b193d9daca19993']
    span=int(sys.argv[2])
elif which=='eth':
    U='https://rpc.flashbots.net'; step=2000
    addrs=['0x4dbd4fc535ac27206064b68ffcf827b0a60bab3f','0x8315177ab297ba92a06054ce80a67ed4dbd7ed3a','0x1c479675ad559dc151f6ec7ed3fbf8cee79582b6','0x57bd336d579a51938619271a7cc137a46d0501b1',
           '0x1a07cc4bd17e0118bdb54d70990d2158abad7a2d','0xdf8755334ce7a73ccf6b581c02ea649ae3e864b3','0xc34f4907822d1cdc6ae3038be22e6f12dea35bd4','0xbd0d173eeb87d57a09521c24388a12789f33ba96']
    span=int(sys.argv[2])
else:
    U='https://rpc.hyperliquid.xyz/evm'; step=int(sys.argv[3]) if len(sys.argv)>3 else 1000
    addrs=['0xce59f8b65ad41c9dae4c07a0571a39824bd92cff','0x503d572157113faaad4dbed2647bb10b949216b6','0x37c92ba3796febe10a1bd2494a7e6e5357a3e1fb','0x7f3ff53aecb87261206ad3bdc27a88b6d8420fa6']
    span=int(sys.argv[2])
out={'endpoint':U,'client_start':rpc1(U,'web3_clientVersion',[])}
head=int(rpc1(U,'eth_blockNumber',[]),16); out['head']=head; out['from']=head-span
logs=[];gaps=[]
b=head-span
while b<=head:
    ok=False
    for k in range(6):
        r=rpc1(U,'eth_getLogs',[{'address':addrs,'topics':[UPG],'fromBlock':hex(b),'toBlock':hex(min(b+step-1,head))}])
        if isinstance(r,list): ok=True; break
        time.sleep(1+k)
    if ok: logs+=[{'block':int(x['blockNumber'],16),'addr':x['address'],'tx':x['transactionHash'],'impl':'0x'+x['topics'][1][-40:]} for x in r]
    else: gaps.append([b,str(r)[:150]])
    b+=step
out['logs']=logs; out['gaps']=gaps; out['client_end']=rpc1(U,'web3_clientVersion',[])
json.dump(out,open(f'../raw/upglogs_{which}.json','w'),indent=1)
print(json.dumps(out)[:3000])
